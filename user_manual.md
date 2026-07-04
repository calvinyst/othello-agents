# 📖 Autonomous Othello Arena: User Manual

Welcome to the **Autonomous Othello Arena**! This application offers a rich, interactive environment where you can play Othello against AI, or sit back and watch autonomous agents battle it out while providing live commentary on their strategies.

This manual outlines the various features available to you within the application.

---

## 🎮 Setting Up a Match

When you launch the application, you'll see a Configuration Panel on the left side of the screen. Here you can customize the rules of engagement before clicking **Start Game**:

### 1. Game Modes
- **Agent vs Agent**: Watch two AI models play against each other completely autonomously.
- **Human vs Agent (Black)**: You play as Black (going first) against the AI.
- **Human vs Agent (White)**: You play as White (going second) against the AI.

### 2. The Game Host
The "Host" acts as a live color-commentator for your game. You can choose their personality:
- **Programmatic**: A fast, straightforward referee that simply announces the moves (e.g., "Black plays at D3, flipping 1 piece").
- **Gemini AI**: A creative, conversational Host powered by Google Gemini that provides energetic, television-style commentary on the state of the match.

### 3. Move Pacing (Minimum Move Time)
To ensure the AI doesn't play so quickly that you miss their reasoning, you can set a **Minimum Move Time**. For example, setting this to 5 seconds forces the AI to wait at least 5 seconds between turns, giving you plenty of time to read their live thoughts and commentary.

### 4. Agent Memory
Our agents learn from their past mistakes! You can set a **Memory Limit** (e.g., 3). This tells the AI players to remember their top 3 "Lessons Learned" from previous games in the database and apply them to the current match.

---

## 🧠 Live Commentary & Reasoning Streams

As the game progresses, you don't just see the pieces flip—you get to see exactly *what* the AI is thinking. 

### Stream Panels
On the right side of the screen, there are three dedicated text panels:
- **Agent A (Black)**: Reveals Black's strategic reasoning for their move.
- **Agent B (White)**: Reveals White's strategic reasoning.
- **Agent C (Host)**: Displays the live commentary.

### Toggle Visibility
You have full control over what you want to see. Above the stream panels, you will find toggles to turn each individual stream ON or OFF. 
- Want a quiet game? Turn them all off.
- Want to only hear the Host? Leave Agent C on. 
- Want full transparency? Turn on all three streams to see the inner workings of every agent simultaneously.

---

## ⏪ Post-Game: Review and Time Travel

The application automatically records the full history of every game into a local database. When a match ends (or if you hit the **Abort Game** button), a set of powerful review tools becomes available:

### 1. Lessons Learned
At the end of a match, the AI agents will analyze their performance. The winner will brag about their strategy, and the loser will formulate a "Lesson Learned". These lessons are displayed prominently on the screen and are permanently saved to the database to make the agents smarter in the future.

### 2. The Time Machine (Round-by-Round View)
Want to analyze a crucial turning point in the match? Below the main board, you will find a complete history log of every single move made during the game.
- **Interactive Log**: Clicking on any move in the history log will instantly update the main game board to show you *exactly* what the board looked like at that specific moment in time.
- **Historical Thoughts**: Not only does the board travel back in time, but the stream panels will also update to show you exactly what the Agents and the Host were saying during that specific turn!

### 3. Persistent History
Every move, thought, and board state is stored in a lightweight SQLite file database. This means your game records are fully preserved between sessions.

---

## 🛡️ Enterprise-Grade Agent Security

The Autonomous Othello Arena is built not just for entertainment, but as a robust demonstration of Secure Agentic Engineering.
- **Context Hygiene**: The memories the agents draw from are strictly sanitized behind the scenes to prevent malicious prompt injections.
- **Sandboxed Execution**: When agents compute moves, the engine utilizes "Zero Ambient Authority", mathematically rejecting illegal actions and confining the agent's logic to a restricted runtime environment.
