# deformation.py
import config
from grid import HISTORICAL

class DeformationEngine:
    def __init__(self, grid):
        self.grid = grid

    def run(self):
        deforms = dissolves = cleared_total = 0
        ignore_rows = set() 
        while True:
            event = self._scan_once_lowest_first(ignore_rows)
            if event == "collapse":
                deforms += 1
            elif event == "dissolve":
                dissolves += 1
            
            cleared = self.grid.clear_full_rows()
            cleared_total += cleared
            if cleared > 0:
                ignore_rows.update(self.grid.new_historical_rows)
                
            if event is None and cleared == 0:
                break
        return deforms, dissolves, cleared_total

    def _scan_once_lowest_first(self, ignore_rows):
        for row in range(0, self.grid.num_rows):
            for col in range(0, self.grid.num_cols):
                if not self.grid.is_cell_empty(row, col):
                    continue
                if self._try_dissolve_historical(row, col, ignore_rows):
                    return "dissolve"
                source = self._find_nearest_occupied_above(row, col)
                if source is None:
                    continue
                src_row, src_material = source
                n = self._count_continuous_nonempty_above(row, col)
                # 动态读取全局 config.GRAVITY
                if n * config.GRAVITY >= config.deformation_threshold(src_material):
                    self._collapse(src_row, col, row, col)
                    return "collapse"
        return None

    def _try_dissolve_historical(self, empty_row, col, ignore_rows):
        for r in range(empty_row + 1, self.grid.num_rows):
            if self.grid.is_cell_empty(r, col):
                return False
            if not self.grid.is_cell_historical(r, col):
                return False
            if self.grid.bedrock[r]:
                return False
            if r in ignore_rows:
                return False
            n_above = self._count_continuous_normal_above(r, col)
            # 动态读取历史行崩溃阈值
            if n_above * config.GRAVITY >= config.historical_link_threshold():
                self._dissolve_historical_row(r)
                return True
            return False
        return False

    def _find_nearest_occupied_above(self, empty_row, col):
        for r in range(empty_row + 1, self.grid.num_rows):
            if self.grid.is_cell_empty(r, col):
                return None
            if self.grid.is_cell_historical(r, col):
                return None
            return r, self.grid.material_grid[r][col]
        return None

    def _count_continuous_nonempty_above(self, empty_row, col):
        count = 0
        for r in range(empty_row + 1, self.grid.num_rows):
            if self.grid.is_cell_empty(r, col):
                break
            count += 1
        return count

    def _count_continuous_normal_above(self, historical_row, col):
        count = 0
        for r in range(historical_row + 1, self.grid.num_rows):
            if self.grid.is_cell_empty(r, col):
                break
            if self.grid.is_cell_historical(r, col):
                break
            count += 1
        return count

    def _collapse(self, src_row, src_col, dst_row, dst_col):
        assert dst_row < src_row
        material = self.grid.material_grid[src_row][src_col]
        self.grid.grid[src_row][src_col] = 0
        self.grid.material_grid[src_row][src_col] = 0
        self.grid.grid[dst_row][dst_col] = material
        self.grid.material_grid[dst_row][dst_col] = material

    def _dissolve_historical_row(self, row):
        for c in range(self.grid.num_cols):
            if self.grid.grid[row][c] == HISTORICAL:
                self.grid.grid[row][c] = self.grid.material_grid[row][c]
        self.grid.refresh_bedrock()
