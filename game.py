# game.py
import random
import config
from grid import Grid
from block import Block
from deformation import DeformationEngine

class Game:
    def __init__(self, on_history_created=None, on_move=None, on_land=None):
        self.grid = Grid()
        self.deform = DeformationEngine(self.grid)
        self.current = None
        self.game_over = False
        
        # 音效回调
        self.on_history_created = on_history_created
        self.on_move = on_move
        self.on_land = on_land
        
        self.spawn()

    def spawn(self):
        self.grid.ensure_top_free(4)
        block_id = random.randint(1, 7)
        start_x = config.COLS // 2 - 2
        self.current = Block(block_id, y=self.grid.num_rows - 1, x=start_x)
        if not self.current.is_valid(self.grid):
            self.game_over = True

    def move(self, dy, dx, play_sound=True):
        if self.current:
            success = self.current.move(dy, dx, self.grid)
            # 如果是左右移动，或者手动下落，触发移动音效
            if success and play_sound and self.on_move:
                self.on_move()
            return success
        return False

    def rotate(self):
        if self.current:
            success = self.current.rotate(self.grid)
            if success and self.on_move:
                self.on_move()
            return success
        return False

    def hard_drop(self):
        if not self.current: return
        # 硬降时不触发连续的移动音效，直接触底
        while self.current.move(-1, 0, self.grid):
            pass
        self.lock()

    def lock(self):
        if not self.current: return
        
        # 记录下落前的历史行数量
        prev_hist = sum(1 for r in range(self.grid.num_rows) 
                        if all(self.grid.grid[r][c] == -1 for c in range(config.COLS)))
        
        self.grid.lock_block(self.current)
        self.current = None
        
        # 触发落地音效
        if self.on_land:
            self.on_land()
        
        # 运行形变引擎
        self.deform.run()
        
        # 记录下落后的历史行数量
        curr_hist = sum(1 for r in range(self.grid.num_rows) 
                        if all(self.grid.grid[r][c] == -1 for c in range(config.COLS)))
        
        # 如果历史行变多了，触发崩塌音效
        if curr_hist > prev_hist:
            if self.on_history_created:
                self.on_history_created()
                
        self.spawn()
