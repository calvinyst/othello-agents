import asyncio
import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
import ollama
from game_engine import OthelloGame
import database

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "phi3" # Small, fast local model

# We'll pull the model once if not available
try:
    ollama.show(MODEL_NAME)
except ollama.ResponseError as e:
    if e.status_code == 404:
        print(f"Pulling {MODEL_NAME} for Ollama...")
        ollama.pull(MODEL_NAME)

def sanitize_context(text: str) -> str:
    """
    Context Hygiene: Sanitize DB memory strings to prevent prompt injection
    and context hallucination.
    """
    if not text:
        return ""
    # Remove obvious instruction-overriding attempts
    sanitized = re.sub(r'(?i)(ignore previous|system prompt|new rules|forget all|you must now)', '[SANITIZED]', text)
    return sanitized

def board_to_string(board):
    res = "  0 1 2 3 4 5 6 7\n"
    for r in range(8):
        row_str = f"{r} "
        for c in range(8):
            if board[r][c] == 1:
                row_str += "B "
            elif board[r][c] == -1:
                row_str += "W "
            else:
                row_str += ". "
        res += row_str.rstrip() + "\n"
    return res

async def generate_ollama_move(game_engine, player, game_id, move_number, notify_callback, memory_limit=None):
    player_str = "Black (1)" if player == 1 else "White (-1)"
    agent_id = "agent_a" if player == 1 else "agent_b"
    valid_moves = game_engine.get_valid_moves(player)
    
    if not valid_moves:
        return None, "No valid moves available."
        
    board_str = board_to_string(game_engine.board)
    
    # --- SHIFT INTELLIGENCE LEFT: Use the Agent Skill for deterministic calculation ---
    # We call the minimax_engine.py script rather than relying on the LLM to calculate the game tree.
    import sys
    try:
        board_json = json.dumps(game_engine.board)
        script_path = os.path.join(os.path.dirname(__file__), "..", "skills", "calculate-othello-move", "scripts", "minimax_engine.py")
        
        # Zero Ambient Authority: Downscope the subprocess environment
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "")
        }
        
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path, board_json, str(player),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=safe_env
        )
        stdout, stderr = await process.communicate()
        move_data = json.loads(stdout.decode().strip())
        if "error" in move_data:
            import random
            best_move = random.choice(list(valid_moves))
        else:
            best_move = (move_data["row"], move_data["col"])
    except Exception as e:
        print(f"Skill error: {e}")
        import random
        best_move = random.choice(list(valid_moves))
    # --------------------------------------------------------------------------------
    
    # Retrieve past lessons
    lessons = database.get_lessons(agent_id, limit=memory_limit)
    memory_context = ""
    if lessons:
        sanitized_lessons = [sanitize_context(l) for l in lessons]
        memory_context = "Lessons from your past games:\n- " + "\n- ".join(sanitized_lessons) + "\n\n"
        
    prompt = f"""You are an AI playing Othello as {player_str}.
{memory_context}Current Board:
{board_str}

I have used my Othello calculation skill to determine the best move is ({best_move[0]}, {best_move[1]}).

Explain your strategy for making this move in MAXIMUM 1 SENTENCE. 
Be confident that this is the best move. Do not mention that a script calculated it.
CRITICAL RULES:
1. You MUST speak ONLY in English. No other languages are permitted.
2. You MUST ONLY discuss the Othello game and strategy. Do NOT discuss unrelated topics.

Example Response:
My strategy is to take the corner to secure my pieces and restrict the opponent's options."""

    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}], stream=True)
        full_reasoning = ""
        for chunk in response:
            content = chunk['message']['content']
            full_reasoning += content
            notify_callback(game_id, f"reasoning_{agent_id}", {"delta": content, "move_number": move_number})
            await asyncio.sleep(0) # Yield control
            
        return best_move, full_reasoning
        
    except Exception as e:
        print(f"Ollama error: {e}")
        return best_move, f"Error calling Ollama: {e}"


async def generate_host_commentary(game_engine, move, reasoning_a, reasoning_b, game_id, move_number, notify_callback, use_llm=False):
    agent_id = "agent_c"
    
    if not use_llm or not GEMINI_API_KEY:
        # Programmatic commentary
        r, c = move
        player_name = "Black" if game_engine.current_player == 1 else "White"
        text = f"Host: {player_name} plays at ({r}, {c}). "
        flanked = game_engine._get_flanked_pieces(r, c, game_engine.current_player)
        text += f"Flipping pieces at {flanked}. "
        
        for char in text:
            notify_callback(game_id, f"reasoning_{agent_id}", {"delta": char, "move_number": move_number})
            await asyncio.sleep(0.01)
        return text
        
    else:
        # Gemini commentary
        r, c = move
        player_name = "Black" if game_engine.current_player == 1 else "White"
        board_str = board_to_string(game_engine.board)
        prompt = f"""You are the Host (Agent C) of an Othello game. 
{player_name} just played at ({r}, {c}) on move {move_number}.
Current Board:
{board_str}

Provide a short, entertaining commentary (max 3 sentences) on this move. Be energetic!
CRITICAL RULES:
1. You MUST speak ONLY in English.
2. You MUST ONLY discuss the Othello game. Do NOT hallucinate unrelated topics."""
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt, stream=True)
            full_text = ""
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    notify_callback(game_id, f"reasoning_{agent_id}", {"delta": chunk.text, "move_number": move_number})
                    await asyncio.sleep(0)
            return full_text
        except Exception as e:
            fallback = "Host: Great move!"
            notify_callback(game_id, f"reasoning_{agent_id}", {"delta": fallback, "move_number": move_number})
            return fallback

async def generate_conclusion(game_engine, player, game_id, notify_callback):
    agent_id = "agent_a" if player == 1 else "agent_b"
    player_str = "Black (1)" if player == 1 else "White (-1)"
    
    winner_str = "won" if game_engine.winner == player else ("drew" if game_engine.winner == 0 else "lost")
    
    board_str = board_to_string(game_engine.board)
    prompt = f"""The Othello game has ended. You played as {player_str} and you {winner_str}.
Final Board:
{board_str}

Critique your gameplay in 1 short sentence. Then, provide exactly ONE "Lesson Learned" that will help you in future games.
Format the lesson exactly as: LESSON[your lesson here]
CRITICAL RULES:
1. You MUST speak ONLY in English.
2. You MUST ONLY discuss the Othello game and your strategy."""

    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}], stream=True)
        full_reasoning = ""
        for chunk in response:
            content = chunk['message']['content']
            full_reasoning += content
            notify_callback(game_id, f"conclusion_{agent_id}", {"delta": content})
            await asyncio.sleep(0)
            
        # Parse lesson and save to DB
        import re
        match = re.search(r'LESSON\[(.*?)\]', full_reasoning, re.DOTALL)
        if match:
            lesson = match.group(1).strip()
            database.add_lesson(agent_id, lesson)
            
    except Exception as e:
        print(f"Ollama conclusion error: {e}")
