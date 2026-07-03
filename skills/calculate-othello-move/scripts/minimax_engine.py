import sys
import json
import ast

def get_valid_moves(board, player):
    valid_moves = []
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, r, c, player):
                valid_moves.append((r, c))
    return valid_moves

def is_valid_move(board, r, c, player):
    if board[r][c] != 0:
        return False
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in directions:
        if check_direction(board, r, c, dr, dc, player):
            return True
    return False

def check_direction(board, r, c, dr, dc, player):
    nr, nc = r + dr, c + dc
    if not (0 <= nr < 8 and 0 <= nc < 8):
        return False
    if board[nr][nc] == player or board[nr][nc] == 0:
        return False
    nr += dr
    nc += dc
    while 0 <= nr < 8 and 0 <= nc < 8:
        if board[nr][nc] == 0:
            return False
        if board[nr][nc] == player:
            return True
        nr += dr
        nc += dc
    return False

def make_simulated_move(board, r, c, player):
    new_board = [row[:] for row in board]
    new_board[r][c] = player
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in directions:
        if check_direction(new_board, r, c, dr, dc, player):
            nr, nc = r + dr, c + dc
            while new_board[nr][nc] != player:
                new_board[nr][nc] = player
                nr += dr
                nc += dc
    return new_board

def evaluate_board(board, player):
    # Simple evaluation: piece difference + corner weight
    score = 0
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                score += 1
                if (r, c) in corners:
                    score += 10
            elif board[r][c] == -player:
                score -= 1
                if (r, c) in corners:
                    score -= 10
    return score

def minimax(board, depth, alpha, beta, maximizing_player, current_player):
    valid_moves = get_valid_moves(board, current_player)
    
    if depth == 0 or len(valid_moves) == 0:
        # Check if the other player can move
        other_moves = get_valid_moves(board, -current_player)
        if len(valid_moves) == 0 and len(other_moves) == 0:
            # Game over
            return evaluate_board(board, maximizing_player)
        elif len(valid_moves) == 0:
            # Pass turn
            return minimax(board, depth - 1, alpha, beta, maximizing_player, -current_player)
        else:
            return evaluate_board(board, maximizing_player)
            
    if current_player == maximizing_player:
        max_eval = float('-inf')
        for move in valid_moves:
            new_board = make_simulated_move(board, move[0], move[1], current_player)
            eval = minimax(new_board, depth - 1, alpha, beta, maximizing_player, -current_player)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in valid_moves:
            new_board = make_simulated_move(board, move[0], move[1], current_player)
            eval = minimax(new_board, depth - 1, alpha, beta, maximizing_player, -current_player)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_best_move(board, player, depth=2):
    valid_moves = get_valid_moves(board, player)
    if not valid_moves:
        return None
        
    best_move = None
    best_value = float('-inf')
    
    for move in valid_moves:
        new_board = make_simulated_move(board, move[0], move[1], player)
        move_value = minimax(new_board, depth - 1, float('-inf'), float('inf'), player, -player)
        if move_value > best_value:
            best_value = move_value
            best_move = move
            
    return best_move

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python minimax_engine.py '<board_json>' <player>")
        sys.exit(1)
        
    board_str = sys.argv[1]
    player = int(sys.argv[2])
    
    # Safely parse the 2D array
    board = ast.literal_eval(board_str)
    
    best_move = get_best_move(board, player)
    if best_move:
        print(json.dumps({"row": best_move[0], "col": best_move[1]}))
    else:
        print(json.dumps({"error": "No valid moves available"}))
