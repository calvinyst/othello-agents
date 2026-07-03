class OthelloGame:
    def __init__(self):
        self.board = [[0 for _ in range(8)] for _ in range(8)]
        # 1 for Black, -1 for White
        self.board[3][3] = -1
        self.board[4][4] = -1
        self.board[3][4] = 1
        self.board[4][3] = 1
        self.current_player = 1
        self.game_over = False
        self.winner = 0

    def get_state(self):
        return {
            "board": self.board,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "black_score": sum(row.count(1) for row in self.board),
            "white_score": sum(row.count(-1) for row in self.board)
        }

    def _get_flanked_pieces(self, r, c, player):
        if self.board[r][c] != 0:
            return []
        
        flanked = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            temp_flanked = []
            while 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == -player:
                temp_flanked.append((nr, nc))
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == player and temp_flanked:
                flanked.extend(temp_flanked)
                
        return flanked

    def get_valid_moves(self, player):
        valid_moves = []
        for r in range(8):
            for c in range(8):
                if self._get_flanked_pieces(r, c, player):
                    valid_moves.append((r, c))
        return valid_moves

    def make_move(self, r, c):
        if self.game_over:
            return False, "Game is over"
            
        flanked = self._get_flanked_pieces(r, c, self.current_player)
        if not flanked:
            return False, "Invalid move"
            
        self.board[r][c] = self.current_player
        for fr, fc in flanked:
            self.board[fr][fc] = self.current_player
            
        # Switch player
        self.current_player = -self.current_player
        
        # Check if next player has valid moves
        if not self.get_valid_moves(self.current_player):
            # If not, switch back
            self.current_player = -self.current_player
            # Check if game over
            if not self.get_valid_moves(self.current_player):
                self.game_over = True
                self._calculate_winner()
                
        return True, "Move successful"

    def _calculate_winner(self):
        black_score = sum(row.count(1) for row in self.board)
        white_score = sum(row.count(-1) for row in self.board)
        if black_score > white_score:
            self.winner = 1
        elif white_score > black_score:
            self.winner = -1
        else:
            self.winner = 0 # Tie
