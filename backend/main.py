import asyncio
import json
import time
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from game_engine import OthelloGame
import database
from agents import generate_ollama_move, generate_host_commentary, generate_conclusion

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory active games
active_games = {} # game_id -> OthelloGame
game_queues = {} # game_id -> [asyncio.Queue]

def notify_game(game_id, event_type, data):
    if game_id in game_queues:
        for q in game_queues[game_id]:
            q.put_nowait({"type": event_type, "data": data})

class GameCreateReq(BaseModel):
    mode: str # 'agent_vs_agent' or 'human_vs_agent'
    min_move_time: int
    agent_c_type: str # 'programmatic' or 'llm'
    memory_limit: int = -1

@app.post("/api/game")
def start_game(req: GameCreateReq):
    game_id = database.create_game(req.mode, req.min_move_time)
    game = OthelloGame()
    active_games[game_id] = {
        "engine": game,
        "mode": req.mode,
        "min_move_time": req.min_move_time,
        "agent_c_type": req.agent_c_type,
        "memory_limit": req.memory_limit,
        "move_count": 0
    }
    return {"game_id": game_id, "state": game.get_state()}

@app.post("/api/game/{game_id}/abort")
def abort_game(game_id: int):
    if game_id in active_games:
        database.update_game_status(game_id, "ABORTED")
        del active_games[game_id]
        notify_game(game_id, "game_aborted", {})
    return {"status": "success"}

async def run_conclusions(engine, game_id):
    await asyncio.sleep(1)
    await generate_conclusion(engine, 1, game_id, notify_game)
    await generate_conclusion(engine, -1, game_id, notify_game)

@app.get("/api/game/{game_id}/stream")
async def stream_game(game_id: int):
    q = asyncio.Queue()
    if game_id not in game_queues:
        game_queues[game_id] = []
    game_queues[game_id].append(q)
    
    async def event_generator():
        try:
            while True:
                msg = await q.get()
                yield {"event": msg["type"], "data": json.dumps(msg["data"])}
        except asyncio.CancelledError:
            if q in game_queues.get(game_id, []):
                game_queues[game_id].remove(q)
            
    return EventSourceResponse(event_generator())

async def process_agent_turn(game_id: int):
    if game_id not in active_games:
        return
        
    game_info = active_games[game_id]
    engine = game_info["engine"]
    min_time = game_info["min_move_time"]
    memory_limit = game_info["memory_limit"]
    if memory_limit == -1:
        memory_limit = None
    
    start_time = time.time()
    
    # Check if game is over
    if engine.game_over:
        database.update_game_status(game_id, "COMPLETED", engine.winner)
        notify_game(game_id, "game_over", engine.get_state())
        if game_info["mode"] != "human_v_human":
            asyncio.create_task(run_conclusions(engine, game_id))
        return

    player = engine.current_player
    current_move_number = game_info["move_count"] + 1
    
    # Ask agent A or B for move
    move, reasoning = await generate_ollama_move(engine, player, game_id, current_move_number, notify_game, memory_limit=memory_limit)
    
    if not move:
        # Pass turn
        engine.current_player = -engine.current_player
        if not engine.get_valid_moves(engine.current_player):
            engine.game_over = True
            engine._calculate_winner()
            database.update_game_status(game_id, "COMPLETED", engine.winner)
            notify_game(game_id, "board_update", engine.get_state())
            notify_game(game_id, "game_over", engine.get_state())
            
            # Run conclusions if game is over
            if game_info["mode"] != "human_v_human":
                asyncio.create_task(run_conclusions(engine, game_id))
            
            return

    r, c = move
    
    # Host Commentary
    use_llm_host = (game_info["agent_c_type"] == "llm")
    host_reasoning = await generate_host_commentary(engine, move, reasoning, "", game_id, current_move_number, notify_game, use_llm_host)
    
    # Make move
    engine.make_move(r, c)
    game_info["move_count"] += 1
    
    # Save move
    database.add_move(
        game_id, game_info["move_count"], player, r, c, 
        agent_a_reasoning=reasoning if player == 1 else "",
        agent_b_reasoning=reasoning if player == -1 else "",
        agent_c_reasoning=host_reasoning
    )
    
    elapsed = time.time() - start_time
    if elapsed < min_time:
        await asyncio.sleep(min_time - elapsed)
        
    # Broadcast new state
    state = engine.get_state()
    state["move_number"] = game_info["move_count"]
    state["last_player"] = player
    notify_game(game_id, "board_update", state)
    
    # If agent vs agent, trigger next turn automatically if game not over
    if not engine.game_over and game_info["mode"] == "agent_vs_agent":
        asyncio.create_task(process_agent_turn(game_id))
    elif engine.game_over:
        database.update_game_status(game_id, "COMPLETED", engine.winner)
        notify_game(game_id, "game_over", engine.get_state())
        if game_info["mode"] != "human_v_human":
            asyncio.create_task(run_conclusions(engine, game_id))

@app.post("/api/game/{game_id}/trigger_agent")
async def trigger_agent(game_id: int, background_tasks: BackgroundTasks):
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    background_tasks.add_task(process_agent_turn, game_id)
    return {"status": "started"}

class MoveReq(BaseModel):
    r: int
    c: int

@app.post("/api/game/{game_id}/move")
async def make_human_move(game_id: int, req: MoveReq, background_tasks: BackgroundTasks):
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
        
    game_info = active_games[game_id]
    engine = game_info["engine"]
    
    if engine.game_over:
        return {"status": "error", "message": "Game is over"}
        
    player = engine.current_player
    success, msg = engine.make_move(req.r, req.c)
    
    if not success:
        return {"status": "error", "message": msg}
        
    game_info["move_count"] += 1
    current_move_number = game_info["move_count"]
    
    # Host Commentary for human move
    use_llm_host = (game_info["agent_c_type"] == "llm")
    host_reasoning = await generate_host_commentary(engine, (req.r, req.c), "Human Move", "", game_id, current_move_number, notify_game, use_llm_host)
    
    # Save move to DB
    database.add_move(
        game_id, game_info["move_count"], player, req.r, req.c,
        agent_a_reasoning="", agent_b_reasoning="", agent_c_reasoning=host_reasoning
    )
    
    state = engine.get_state()
    state["move_number"] = game_info["move_count"]
    state["last_player"] = player
    notify_game(game_id, "board_update", state)
    
    if not engine.game_over and game_info["mode"] == "human_vs_agent":
        # Agent's turn
        background_tasks.add_task(process_agent_turn, game_id)
        
    elif engine.game_over:
        database.update_game_status(game_id, "COMPLETED", engine.winner)
        notify_game(game_id, "game_over", engine.get_state())
        if game_info["mode"] != "human_v_human":
            asyncio.create_task(run_conclusions(engine, game_id))
        
    return {"status": "success", "state": engine.get_state()}
