# config.py
GRAVITY = 1.0
MATERIAL_MULT = 1.0
LINK_COEF = 3.0

BASE_THRESHOLD = 1.0
MATERIAL_K = {1: 1.0, 2: 1.5, 3: 2.5, 4: 1.0, 5: 1.5, 6: 2.5, 7: 1.0}

INITIAL_ROWS = 20
COLS = 15             # 增加到15列
CELL_SIZE = 30
VISIBLE_ROWS = 20

# 列宾式古典配色 (做旧纸张、炭黑、暗赭、砖红、松绿)
COLOR_BG = (225, 215, 195)        # 羊皮纸底色
COLOR_GRID = (205, 195, 175)      # 纸张网格线
COLOR_SIDEBAR = (215, 205, 185)   # 侧边栏底色
COLOR_TEXT = (45, 40, 35)         # 炭黑文字
COLOR_ACCENT = (130, 40, 30)      # 朱砂红（用于崩溃警告）

COLORS = {
    1: (60, 85, 90),      # 暗青灰
    2: (180, 145, 80),    # 黄土/赭石
    3: (90, 70, 110),     # 暗紫罗兰
    4: (150, 80, 60),     # 焦茶
    5: (60, 80, 65),      # 松绿
    6: (160, 120, 90),    # 肉色/土红
    7: (50, 45, 40),      # 炭黑
    -1: (100, 90, 80),    # 历史沉淀行
}

def deformation_threshold(material_id):
    k = MATERIAL_K.get(material_id, 99.0)
    return k * MATERIAL_MULT * BASE_THRESHOLD

def historical_link_threshold():
    return LINK_COEF * BASE_THRESHOLD
