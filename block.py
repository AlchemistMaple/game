# block.py
SHAPES = {
    1: [[1, 1, 1, 1]],
    2: [[1, 1], [1, 1]],
    3: [[0, 1, 0], [1, 1, 1]],
    4: [[1, 0, 0], [1, 1, 1]],
    5: [[0, 0, 1], [1, 1, 1]],
    6: [[0, 1, 1], [1, 1, 0]],
    7: [[1, 1, 0], [0, 1, 1]],
}

class Block:
    def __init__(self, block_id, y, x):
        self.id = block_id
        self.shape = [row[:] for row in SHAPES[block_id]]
        self.y = y    # 方块顶部在 grid 中的行号（row 越大越靠上）
        self.x = x

    def get_cell_positions(self):
        """局部坐标 local_row=0 是 shape 顶部，映射到 grid_row = y - local_row。"""
        out = []
        for lr, row in enumerate(self.shape):
            for lc, v in enumerate(row):
                if v:
                    out.append((self.y - lr, self.x + lc))
        return out

    def is_valid(self, grid):
        for r, c in self.get_cell_positions():
            if c < 0 or c >= grid.num_cols:
                return False
            if r < 0 or r >= grid.num_rows:
                return False
            if grid.grid[r][c] != 0:
                return False
        return True

    def move(self, dy, dx, grid):
        self.y += dy
        self.x += dx
        if not self.is_valid(grid):
            self.y -= dy
            self.x -= dx
            return False
        return True

    def rotate(self, grid):
        old = self.shape
        self.shape = [list(r) for r in zip(*old[::-1])]
        if not self.is_valid(grid):
            self.shape = old
            return False
        return True
