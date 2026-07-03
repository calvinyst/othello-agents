import asyncio
from main import run_conclusions, active_games, game_queues, notify_game
from game_engine import OthelloGame

async def test():
    engine = OthelloGame()
    active_games[1] = {'engine': engine, 'mode': 'agent_vs_agent'}
    q = asyncio.Queue()
    game_queues[1] = [q]
    
    # Run conclusion in background
    task = asyncio.create_task(run_conclusions(engine, 1))
    
    while True:
        try:
            msg = await asyncio.wait_for(q.get(), timeout=2.0)
            print("BROADCAST:", msg)
        except asyncio.TimeoutError:
            if task.done():
                break
            
    if task.exception():
        print("EXCEPTION:", task.exception())

asyncio.run(test())
