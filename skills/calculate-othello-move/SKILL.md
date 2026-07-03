---
name: calculate-othello-move
description: |
  Calculates the optimal next move for an Othello (Reversi) agent using a deterministic algorithm.
  Use this skill when the agent needs to decide which coordinate to play next on the Othello board.
  Do NOT use this for checking game rules or validating moves (use the MCP server for that).
version: 1.0.0
license: MIT
allowed-tools: Read Bash Execute
metadata:
  author: @calvinyst
---
# Calculate Othello Move

## When to use
- When it is your turn to play in an Othello game.
- When you have the current board state and need to output the best `(row, col)` move.

## When NOT to use
- When the game is over.
- When you are just checking if a move is valid (the MCP server does this).

## Workflow
1. Get the current board state as a 2D array and your player color (1 for Black, -1 for White).
2. Use the provided Python script `scripts/minimax_engine.py` to calculate the best move.
3. Pass the `board` and `player` as arguments to the script.
4. Output the exact `(row, col)` returned by the script.

## Shifting Intelligence Left
Do not attempt to calculate the game tree or evaluate the board yourself. Large Language Models degrade rapidly when performing deep game tree searches in context. We shift this deterministic logic into `minimax_engine.py` to preserve token budget and ensure optimal play.
