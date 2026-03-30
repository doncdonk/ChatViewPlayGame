"""
リバーシ（オセロ）ロジック
"""

EMPTY = 0
BLACK = 1  # 配信者
WHITE = 2  # チャット

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]


class Reversi:
    def __init__(self):
        self.board = [[EMPTY]*8 for _ in range(8)]
        self.board[3][3] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.board[4][4] = WHITE
        self.turn        = BLACK   # 配信者先手
        self.game_over   = False
        self.winner      = None    # BLACK / WHITE / "draw"
        self.last_move   = None    # (row, col)

    # ── 合法手 ──────────────────────────────────
    def legal_moves(self, color=None):
        if color is None:
            color = self.turn
        moves = []
        for r in range(8):
            for c in range(8):
                if self._is_legal(r, c, color):
                    moves.append((r, c))
        return moves

    def _is_legal(self, row, col, color):
        if self.board[row][col] != EMPTY:
            return False
        opp = WHITE if color == BLACK else BLACK
        for dr, dc in DIRS:
            r, c = row+dr, col+dc
            found_opp = False
            while 0 <= r < 8 and 0 <= c < 8:
                if self.board[r][c] == opp:
                    found_opp = True
                elif self.board[r][c] == color:
                    if found_opp:
                        return True
                    break
                else:
                    break
                r += dr; c += dc
        return False

    # ── 石を置く ─────────────────────────────────
    def place(self, row, col):
        """置く → 反転 → ターン交代 → 終了判定。True=成功"""
        if self.game_over:
            return False
        if not self._is_legal(row, col, self.turn):
            return False
        color = self.turn
        opp   = WHITE if color == BLACK else BLACK
        self.board[row][col] = color
        self.last_move = (row, col)
        # 反転
        for dr, dc in DIRS:
            to_flip = []
            r, c = row+dr, col+dc
            while 0 <= r < 8 and 0 <= c < 8:
                if self.board[r][c] == opp:
                    to_flip.append((r, c))
                elif self.board[r][c] == color:
                    for fr, fc in to_flip:
                        self.board[fr][fc] = color
                    break
                else:
                    break
                r += dr; c += dc
        # ターン交代
        self.turn = opp
        # パス・終了判定
        self._check_turn()
        return True

    def _check_turn(self):
        if self.legal_moves(self.turn):
            return
        # 次の手番が打てない → パス or 終了
        opp = WHITE if self.turn == BLACK else BLACK
        if self.legal_moves(opp):
            # パス（相手に戻す）
            self.turn = opp
        else:
            # 両者打てない → 終了
            self.game_over = True
            b = sum(self.board[r][c] == BLACK for r in range(8) for c in range(8))
            w = sum(self.board[r][c] == WHITE for r in range(8) for c in range(8))
            if b > w:
                self.winner = BLACK
            elif w > b:
                self.winner = WHITE
            else:
                self.winner = "draw"

    # ── カウント ─────────────────────────────────
    def count(self, color):
        return sum(self.board[r][c] == color for r in range(8) for c in range(8))

    def is_passed(self):
        """現在のターンがパスかどうか（legal_movesが空）"""
        return not self.legal_moves(self.turn)
