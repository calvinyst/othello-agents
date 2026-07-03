# Othello Agents: A Full-Stack Multi-Agent Capstone Project

**Submission for AI Agents: Intensive Vibe Coding Capstone Project | Kaggle**  
**Author:** @calvinyst  

## Project Overview

Welcome to the **Othello Agents** Capstone! This project is a fully-featured, production-ready Othello (Reversi) web application that brings the theoretical concepts of Agentic Engineering to life.

Rather than relying on simple console scripts or monolithic prompt engineering, this application implements a robust **FastAPI backend** and a dynamic **Vanilla JS frontend**, perfectly mapped to the core paradigms from the course whitepapers (*Agent Tools & Interoperability* and *Agent Skills*).

You can play Human vs. AI, or sit back and watch AI vs. AI matches with live, real-time commentary streamed directly to your browser.

---

## Architectural Alignment with Course Concepts

### 1. Agent-to-Agent (A2A) Protocol: The Orchestrator Backend
*See: `backend/main.py`*
To solve the "GOTO Problem" and avoid the "Monolithic Ceiling", the system relies on a multi-agent architecture. The FastAPI server (`main.py`) acts as the central **Orchestrator**. It manages the game loop and uses the conceptual A2A protocol to discover, initialize, and communicate with three distinct agents:
- **Agent A (Black)**: Plays the game.
- **Agent B (White)**: Plays the game.
- **Agent C (Host)**: Provides dynamic, energetic color commentary on the moves.

### 2. Agent Skills: Shifting Intelligence Left
*See: `skills/calculate-othello-move/` and `backend/agents.py`*
A major pitfall of early agent design is forcing LLMs to evaluate deep game trees, which leads to immediate context rot and hallucinated (invalid) moves.
- **The Solution:** We implemented the `calculate-othello-move` Agent Skill. 
- **Shifting Intelligence Left:** When Agent A or B needs to move, the backend explicitly delegates the game tree calculation to a deterministic Python script (`skills/calculate-othello-move/scripts/minimax_engine.py`). 
- The LLM's prompt is then updated *with* the optimal move, and it generates the strategic reasoning behind it. This keeps the active token budget extremely low and ensures 100% flawless play, matching the "Write Software, Not Rules" recommendation perfectly!

### 3. Decoupled Tooling & State
*See: `backend/game_engine.py`*
Following the principle of "Consumption over Creation", the core game logic is entirely decoupled from the agents. The `OthelloGame` class acts as the single source of truth (serving a similar role to a Model Context Protocol server), exposing rigid tools like `get_valid_moves` and `make_move`. The agents cannot break the rules or cheat.

### 4. Interactive UI & Streaming
*See: `frontend/index.html`*
We solve the "Communication Gap" by mapping the internal JSON state of the orchestrator to a beautiful, interactive web UI. While not strictly an A2UI payload sent to a console, the architecture achieves the exact same goal: the backend generates the game state, and the decoupled frontend renders it natively into an interactive board and live-updating chat streams via Server-Sent Events (SSE).

---

## Getting Started

### Prerequisites
- Python 3.9+
- Ollama installed locally (for local AI inference)
- [Gemini API Key](https://aistudio.google.com/) (optional, for Host commentary)

### 1. Start the Backend (The Orchestrator)
1. Navigate to the `backend/` directory.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### 2. Start the Frontend (The UI)
1. Open a new terminal.
2. Navigate to the `frontend/` directory.
3. Start a simple web server:
   ```bash
   python -m http.server 8080
   ```
4. Open your browser and go to `http://localhost:8080`.

*Enjoy the game!*
