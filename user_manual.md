# 📖 Autonomous Othello Arena: User Manual

Welcome to the **Autonomous Othello Arena**! This application is a fully-featured, production-ready Othello (Reversi) web app that brings advanced Agentic Engineering to life. This manual provides a detailed overview of the core features and how to interact with the system.

---

## 🚀 Getting Started

### Launching the Game
When you first open the application, you will be greeted by the Configuration Panel.
1. **Select Game Mode**:
   - **Agent vs Agent**: Sit back and watch two AI models battle it out.
   - **Human vs Agent (Black/White)**: Play against the AI yourself.
2. **Select Host Type (Agent C)**:
   - **Programmatic**: A fast, deterministic rules engine that simply announces the moves and flipped pieces.
   - **Gemini AI**: A creative Host powered by Google Gemini that provides colorful, energetic commentary on the state of the game.
3. **Move Pacing**: Set the minimum move time (in seconds) to ensure the AI doesn't play too fast for you to read their reasoning.
4. **Memory Limit**: Decide how many past "Lessons Learned" the agents are allowed to remember from previous games.

---

## ✨ Core Features & Mechanics

### 1. Real-Time Generative UI (SSE Streaming)
The heart of the arena is the real-time commentary and reasoning streams. As the agents "think", you will see their thought processes streamed to your screen character-by-character via Server-Sent Events (SSE). 

You can toggle the visibility of each agent's reasoning stream:
- **Agent A (Black) Panel**: Reveals Black's strategic reasoning for their move.
- **Agent B (White) Panel**: Reveals White's strategic reasoning.
- **Agent C (Host) Panel**: Displays the live color-commentary of the match.

### 2. "Shifting Intelligence Left" (Agent Skills)
A unique architectural feature of this system is that the LLMs are **not** calculating the Othello game tree. 

When it is an AI's turn to move, the backend invokes a deterministic **Minimax Engine** asynchronously. This script mathematically calculates the absolute best move. Once calculated, this optimal move is fed to the LLM, whose only job is to generate high-quality strategic reasoning explaining *why* that move is brilliant. This guarantees 100% flawless gameplay while maintaining rich, creative commentary.

### 3. Strict On-Topic Discipline
LLMs have a tendency to hallucinate or drift off-topic during long sequences (e.g., unexpectedly speaking in Russian or discussing unrelated concepts). Our agents are bound by **CRITICAL RULES** in their system prompts that strictly forbid non-English languages and force them to exclusively discuss Othello strategy.

### 4. Post-Game Analysis & Time Travel
When a match concludes:
- **Critique & Lessons Learned**: The AI agents will analyze their performance. The winner will brag about their strategy, and the loser will formulate a "Lesson Learned".
- **Persistent Memory**: These lessons are saved to a lightweight SQLite database and are injected into the agents' prompts in future games (if the memory limit allows).
- **Time Travel**: While reviewing the match, you can use the interactive log to step backward through the game, viewing the exact board state and reasoning streams from any specific turn.

---

## 🛠️ Technical Architecture Overview

For developers interested in the underlying system:
- **The Orchestrator**: A FastAPI backend manages the canonical truth of the game board, ensuring agents cannot cheat or hallucinate invalid moves.
- **Asynchronous Microservices**: Deep Minimax calculations are executed as non-blocking async subprocesses, ensuring the FastAPI event loop remains responsive and SSE streams never hang.
- **A2A Protocol**: The system avoids chaotic free-form chat. Agent interactions are strictly orchestrated turn-by-turn.
- **Zero-Cost Local Inference**: The core gameplay agents can run entirely on local hardware using Ollama (e.g., `phi3` or `llama3`), allowing for infinite matches with zero API costs.

Enjoy the Arena!
