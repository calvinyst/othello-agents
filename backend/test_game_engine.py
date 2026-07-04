import pytest
from game_engine import OthelloGame

def test_initial_board_state():
    game = OthelloGame()
    assert game.board[3][3] == -1
    assert game.board[4][4] == -1
    assert game.board[3][4] == 1
    assert game.board[4][3] == 1
    assert game.current_player == 1
    assert game.winner == 0

def test_valid_moves_initial():
    game = OthelloGame()
    # Black (1) should have 4 valid moves initially
    valid_moves = game.get_valid_moves(1)
    assert len(valid_moves) == 4
    assert (2, 3) in valid_moves
    assert (3, 2) in valid_moves
    assert (4, 5) in valid_moves
    assert (5, 4) in valid_moves

def test_make_move():
    game = OthelloGame()
    # Black plays (2, 3)
    success, msg = game.make_move(2, 3)
    assert success is True
    # Check if piece was placed
    assert game.board[2][3] == 1
    # Check if opponent piece was flipped
    assert game.board[3][3] == 1
    # Check if turn changed to White (-1)
    assert game.current_player == -1

def test_invalid_move():
    game = OthelloGame()
    # (0, 0) is an invalid opening move
    success, msg = game.make_move(0, 0)
    assert success is False
    assert game.board[0][0] == 0
    # Turn should not change
    assert game.current_player == 1
