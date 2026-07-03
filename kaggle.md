# Autonomous Othello Arena: A Multi-Agent System Ecosystem
**Subtitle**: Shifting Intelligence Left in Agent Architectures for Real-Time Competitive Gaming

**Track Selection**: Freestyle Track

---

## 1. Executive Summary

The **Autonomous Othello Arena** is a multi-agent system designed to explore advanced agent architectures, specifically focusing on the principles of **Agent-to-Agent (A2A) Orchestration**, **Agent-to-UI (A2UI)**, and **"Shifting Intelligence Left"** through localized Agent Skills. 

In this system, autonomous AI agents—powered by Google Gemini and Ollama models—compete in real-time games of Othello (Reversi). A dedicated Orchestrator (the "Host") manages the game state, enforces rules, and provides dynamic programmatic commentary via Server-Sent Events (SSE). The system demonstrates how a carefully constructed architecture can decouple deterministic logic from Large Language Models (LLMs), yielding highly performant, predictable, and engaging agent interactions.

---

## 2. Core Architectural Pillars

### A. Agent-to-Agent (A2A) Orchestration
The foundation of the arena relies on a robust orchestration layer. Rather than having agents loosely chat with one another to decide game state, the system employs a rigid structural protocol. 
*   **The Orchestrator**: A FastMCP-inspired backend manages the canonical truth of the game board. It prompts Agent A (Black) and Agent B (White) strictly in turn-based sequence.
*   **Structured Outputs**: Agents are compelled to return highly structured JSON schemas representing their next move coordinates. 
*   **The Host Agent**: A third observer agent acts as the referee and color-commentator, ensuring that the A2A interactions are seamlessly translated into a digestible format.

### B. Shifting Intelligence Left: The Agent Skills Pattern
A critical failing in early agent design is relying on LLMs for deterministic calculations (e.g., asking an LLM to "calculate the best Minimax move"). We implemented the **"Shift Intelligence Left"** methodology to solve this.

*   **Agent Skills**: The system includes a standard `calculate-othello-move` Agent Skill. This skill contains a `SKILL.md` instruction file and a `minimax_engine.py` deterministic script.
*   **Tool Execution**: When an agent must make a move, the LLM is bypassed for the computational heavy lifting. Instead, the backend invokes the localized Python script asynchronously (`asyncio.create_subprocess_exec`) to calculate the mathematically optimal move.
*   **The Role of the LLM**: Freed from playing the game poorly, the LLM is instead fed the optimal move and asked to generate high-quality, strategic reasoning and color commentary about *why* the move was made. This creates a perfect symbiosis of deterministic accuracy and generative creativity.

### C. Agent-to-UI (A2UI) Generative Interfaces
To visualize the A2A interactions, we implemented real-time generative UI components. 
*   **SSE Streaming**: The backend streams the LLMs' strategic reasoning and the Host's commentary character-by-character to the frontend via Server-Sent Events.
*   **Interactive Review**: As the game progresses, the system logs board states and reasoning chunks. The UI parses this data to offer a "Time Travel" feature, allowing users to scrub through past rounds, view auxiliary mini-boards comparing turn states, and read the agents' post-match conclusions.

---

## 3. Analysis & Key Learnings

Building the Autonomous Othello Arena provided several profound insights into production-ready agent deployment:

1.  **The Perils of Blocking I/O**: During development, we encountered a severe issue where a deep Minimax calculation (Depth 4) took over 60 seconds. Because it was originally invoked via a synchronous `subprocess.run`, it blocked the entire FastAPI event loop, causing the SSE streams to hang. Transitioning to `asyncio` and reducing the search depth proved that **agent tools must be treated as asynchronous microservices**, lest they stall the orchestrator.
2.  **State Synchronization**: Keeping the generative UI in perfect lockstep with the backend game engine required meticulous state management. By ensuring the Orchestrator was the single source of truth, we eliminated race conditions where an agent might hallucinate a move on a previously occupied square.
3.  **Strict Prompting Against Hallucinations**: We quickly discovered that LLMs tend to diverge off-topic during games (e.g., unexpectedly speaking in Russian or discussing unrelated concepts). By establishing strict "CRITICAL RULES" within the system prompts (forbidding non-English languages and forcing alignment strictly to Othello strategy), we achieved highly disciplined, on-topic commentary streams without sacrificing the agents' energetic personas.
4.  **The Power of Constrained Prompts**: Giving the agents system prompts that strictly decoupled their "thought process" from their "action output" allowed us to capture rich, engaging dialogue without polluting the JSON payloads required for game progression.

---

## 4. Required Assets

### A. Media Gallery
*   **Cover Image**: ![Autonomous Othello Arena UI](https://github.com/calvinyst/othello-agents/raw/master/cover_image.png)
*   **Video Demonstration**: [Watch the Autonomous Othello Arena Demo](https://youtu.be/yPpt-kA0Xdk)

### B. Public Project Link

**GitHub Repository:** [https://github.com/calvinyst/othello-agents](https://github.com/calvinyst/othello-agents)

**Setup Instructions:**
1. Clone the repository: `git clone https://github.com/calvinyst/othello-agents.git`
2. Navigate to the backend directory and set up your environment variables (rename `.env.example` to `.env` and add your API keys).
3. Create a virtual environment and install dependencies: `pip install -r requirements.txt` (ensure `fastapi`, `uvicorn`, `google-genai`, etc., are installed).
4. Run the backend server: `uvicorn main:app --reload`
5. In a separate terminal, navigate to the `frontend` directory.
6. Run the frontend server: `python -m http.server 8080`
7. Open `http://localhost:8080` in your web browser to access the Autonomous Othello Arena!
