# grid.py
from config import INITIAL_ROWS, COLS

HISTORICAL = -1

class Grid:
    def __init__(self):
        self.num_rows = INITIAL_ROWS
        self.num_cols = COLS
        self.grid = [[0] * self.num_cols for _ in range(self.num_rows)]
        self.material_grid = [[0] * self.num_cols for _ in range(self.num_rows)]
        self.bedrock = [False] * self.num_rows
        self.new_historical_rows = []

    def expand_top(self, n=1):
        for _ in range(n):
            self.grid.append([0] * self.num_cols)
            self.material_grid.append([0] * self.num_cols)
            self.bedrock.append(False)
        self.num_rows += n

    def ensure_top_free(self, required=4):
        while self.num_rows < required:
            self.expand_top(required - self.num_rows)
        while True:
            start = self.num_rows - required
            if all(self.grid[r][c] == 0
                   for r in range(start, self.num_rows)
                   for c in range(self.num_cols)):
                return
            self.expand_top(1)

    def lock_block(self, block):
        for r, c in block.get_cell_positions():
            self.grid[r][c] = block.id
            self.material_grid[r][c] = block.id

    def is_cell_empty(self, row, col):
        return self.grid[row][col] == 0

    def is_cell_historical(self, row, col):
        return self.grid[row][col] == HISTORICAL

    def clear_full_rows(self):
        cleared = 0
        self.new_historical_rows = []
        for row in range(self.num_rows):
            if all(self.grid[row][c] not in (0, HISTORICAL)
                   for c in range(self.num_cols)):
                for c in range(self.num_cols):
                    self.grid[row][c] = HISTORICAL
                cleared += 1
                self.new_historical_rows.append(row)
        if cleared:
            self.refresh_bedrock()
        return cleared

    def refresh_bedrock(self):
        self.bedrock = [False] * self.num_rows
        row = 0
        while row < self.num_rows and all(
                self.grid[row][c] == HISTORICAL for c in range(self.num_cols)):
            self.bedrock[row] = True
            row += 1
