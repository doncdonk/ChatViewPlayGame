"""
マインスイーパーのロジック
"""
import random
import time


class Minesweeper:
    def __init__(self, cols, rows, mines):
        self.cols  = cols
        self.rows  = rows
        self.mines = mines
        self.board = [[{"mine":False,"open":False,"flag":False,"number":0}
                       for _ in range(cols)] for _ in range(rows)]
        self.game_over  = False
        self.cleared    = False
        self.first_move = True
        self.start_time = None

    def _place_mines(self, safe_col, safe_row):
        forbidden = set()
        for dc in range(-1, 2):
            for dr in range(-1, 2):
                nc, nr = safe_col+dc, safe_row+dr
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    forbidden.add((nc, nr))
        candidates = [(c,r) for r in range(self.rows) for c in range(self.cols)
                      if (c,r) not in forbidden]
        for c, r in random.sample(candidates, min(self.mines, len(candidates))):
            self.board[r][c]["mine"] = True
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c]["mine"]:
                    cnt = sum(
                        1 for dc in range(-1,2) for dr in range(-1,2)
                        if 0 <= c+dc < self.cols and 0 <= r+dr < self.rows
                        and self.board[r+dr][c+dc]["mine"]
                    )
                    self.board[r][c]["number"] = cnt

    def open_cell(self, col, row):
        if self.game_over or self.cleared: return False
        if not (0 <= col < self.cols and 0 <= row < self.rows): return False
        cell = self.board[row][col]
        if cell["open"] or cell["flag"]: return False
        if self.first_move:
            self._place_mines(col, row)
            self.first_move = False
            self.start_time = time.time()
        if cell["mine"]:
            cell["open"] = True
            self.game_over = True
            self._reveal_mines()
            return True
        self._flood(col, row)
        self._check_clear()
        return False

    def _flood(self, col, row):
        q = [(col, row)]
        while q:
            c, r = q.pop()
            cell = self.board[r][c]
            if cell["open"] or cell["flag"] or cell["mine"]: continue
            cell["open"] = True
            if cell["number"] == 0:
                for dc in range(-1,2):
                    for dr in range(-1,2):
                        nc, nr = c+dc, r+dr
                        if 0 <= nc < self.cols and 0 <= nr < self.rows:
                            q.append((nc, nr))

    def _reveal_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c]["mine"]:
                    self.board[r][c]["open"] = True

    def _check_clear(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c]["mine"] and not self.board[r][c]["open"]:
                    return
        self.cleared = True

    def toggle_flag(self, col, row):
        if self.game_over or self.cleared: return
        if not (0 <= col < self.cols and 0 <= row < self.rows): return
        cell = self.board[row][col]
        if not cell["open"]:
            cell["flag"] = not cell["flag"]

    def get_cell(self, col, row):
        return self.board[row][col]

    def count_flags(self):
        return sum(self.board[r][c]["flag"]
                   for r in range(self.rows) for c in range(self.cols))
