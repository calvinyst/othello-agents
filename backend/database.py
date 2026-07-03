import sqlite3
import json
import os
from datetime import datetime

DB_FILE = "othello.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TEXT,
        end_time TEXT,
        status TEXT,
        mode TEXT,
        winner INTEGER,
        min_move_time INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER,
        move_number INTEGER,
        player INTEGER,
        r INTEGER,
        c INTEGER,
        agent_a_reasoning TEXT,
        agent_b_reasoning TEXT,
        agent_c_reasoning TEXT,
        timestamp TEXT,
        FOREIGN KEY(game_id) REFERENCES games(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        lesson TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def create_game(mode, min_move_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO games (start_time, status, mode, min_move_time) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "IN_PROGRESS", mode, min_move_time)
    )
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return game_id

def update_game_status(game_id, status, winner=0):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE games SET end_time = ?, status = ?, winner = ? WHERE id = ?",
        (datetime.now().isoformat(), status, winner, game_id)
    )
    conn.commit()
    conn.close()

def get_moves(game_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT move_number, player, r, c, timestamp FROM moves WHERE game_id = ? ORDER BY move_number", (game_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"move_number": r[0], "player": r[1], "row": r[2], "col": r[3], "timestamp": r[4]} for r in rows]

def add_lesson(agent_id, lesson):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO agent_lessons (agent_id, lesson) VALUES (?, ?)", (agent_id, lesson))
    conn.commit()
    conn.close()

def get_lessons(agent_id, limit=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if limit is not None and limit > 0:
        cursor.execute("SELECT lesson FROM agent_lessons WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?", (agent_id, limit))
    else:
        cursor.execute("SELECT lesson FROM agent_lessons WHERE agent_id = ? ORDER BY created_at ASC", (agent_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_move(game_id, move_number, player, r, c, agent_a_reasoning="", agent_b_reasoning="", agent_c_reasoning=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO moves (game_id, move_number, player, r, c, 
        agent_a_reasoning, agent_b_reasoning, agent_c_reasoning, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (game_id, move_number, player, r, c, agent_a_reasoning, agent_b_reasoning, agent_c_reasoning, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
