# main.py
import pygame
import random
import os
import sys
import config
from config import CELL_SIZE, VISIBLE_ROWS
from game import Game

# ================= 资源路径兼容 (用于 PyInstaller 单文件打包) =================
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ================= 初始化 =================
pygame.init()
pygame.mixer.init() # 初始化音频模块

# ---- 新增：加载背景音乐 ----
bgm_path = get_resource_path("bgm.mp3")
if os.path.exists(bgm_path):
    pygame.mixer.music.load(bgm_path)
    pygame.mixer.music.set_volume(0.3) # 建议音量调低到0.3，不要盖过方块落下的音效
    pygame.mixer.music.play(-1)        # 参数 -1 代表无限循环播放
else:
    print("未找到背景音乐文件 bgm.mp3")

SIDEBAR_W = 260
WIDTH = config.COLS * CELL_SIZE
HEIGHT = VISIBLE_ROWS * CELL_SIZE
SCROLLBAR_W = 12
TOTAL_WIDTH = SIDEBAR_W + WIDTH + SCROLLBAR_W
screen = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT))
pygame.display.set_caption("重力沉压 · 俄罗斯方块 (列宾式)")
clock = pygame.time.Clock()

# ================= 字体加载 =================
def load_font(font_size, bold=False):
    font_names = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc"]
    for name in font_names:
        path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", name)
        if os.path.exists(path):
            f = pygame.font.Font(path, font_size)
            f.set_bold(bold)
            return f
    return pygame.font.Font(None, font_size + 4)

font_title = load_font(20, bold=True)
font_bold = load_font(15, bold=True)
font_text = load_font(14)
font_small = load_font(12)

# ================= 音效加载 =================
def load_sound(filename, volume):
    path = get_resource_path(filename)
    if os.path.exists(path):
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        return snd
    print(f"未找到音效文件: {path}")
    return None

snd_history = load_sound("warm_clumsy_pop.wav", 0.7)
snd_move = load_sound("move.wav", 0.3) # 进一步降低音量
snd_land = load_sound("land.wav", 0.6)

# 【新增】开辟专属声道，防止声音重叠
move_channel = pygame.mixer.Channel(1)

def play_history(): 
    if snd_history: snd_history.play()
    
def play_move(): 
    # 【修改】每次播放移动音前，强制掐断上一次未播完的移动音
    if snd_move: 
        move_channel.stop()
        move_channel.play(snd_move)
        
def play_land(): 
    if snd_land: snd_land.play()
# ================= 实例化游戏 =================
game = Game(on_history_created=play_history, on_move=play_move, on_land=play_land)

# ================= 噪点背景层 =================
noise_layer = pygame.Surface((TOTAL_WIDTH, HEIGHT), pygame.SRCALPHA)
for _ in range(15000):
    x = random.randint(0, TOTAL_WIDTH-1)
    y = random.randint(0, HEIGHT-1)
    color = (0, 0, 0, random.randint(5, 15)) if random.random() > 0.5 else (255, 255, 255, random.randint(5, 15))
    pygame.draw.circle(noise_layer, color, (x, y), random.choice([1, 1, 2]))

scroll_offset = 0
auto_follow = True

# ================= 滑动条系统 =================
SLIDERS = {
    'GRAVITY':       {'min': 0.1, 'max': 5.0,  'y': 100, 'label': '重力 G'},
    'MATERIAL_MULT': {'min': 0.1, 'max': 5.0,  'y': 150, 'label': '材料硬度 M'},
    'LINK_COEF':     {'min': 0.5, 'max': 20.0, 'y': 200, 'label': '历史链接 C'},
}
dragging_param = None

def update_param_from_mouse(x, key):
    cfg = SLIDERS[key]
    ratio = max(0.0, min(1.0, (x - 15) / 200))
    val = cfg['min'] + ratio * (cfg['max'] - cfg['min'])
    setattr(config, key, round(val, 2))

# ================= 视口转换 =================
def clamp_scroll(offset):
    if game.grid.num_rows <= VISIBLE_ROWS: return 0
    return max(0, min(offset, game.grid.num_rows - VISIBLE_ROWS))

def update_auto_follow():
    global scroll_offset
    if auto_follow:
        scroll_offset = clamp_scroll(game.grid.num_rows - VISIBLE_ROWS)

def grid_to_screen_y(row):
    vi = row - scroll_offset
    if vi < 0 or vi >= VISIBLE_ROWS: return None
    return (VISIBLE_ROWS - 1 - vi) * CELL_SIZE

# ================= 应力计算 =================
def compute_floating_history_info():
    threshold = config.historical_link_threshold()
    info = {}
    for r in range(1, game.grid.num_rows):
        if not all(game.grid.is_cell_historical(r, c) for c in range(config.COLS)): continue
        if game.grid.bedrock[r]: continue
        max_n = 0
        can = False
        for c in range(config.COLS):
            n = 0
            for rr in range(r + 1, game.grid.num_rows):
                if game.grid.is_cell_empty(rr, c): break
                if game.grid.is_cell_historical(rr, c): break
                n += 1
            max_n = max(max_n, n)
            if not can and game.grid.is_cell_empty(r - 1, c):
                if n * config.GRAVITY >= threshold:
                    can = True
        ratio = min(1.0, max_n * config.GRAVITY / threshold) if threshold > 0 else 0.0
        info[r] = (ratio, can, max_n, threshold)
    return info

def stress_color(ratio, can_dissolve):
    if can_dissolve: return config.COLOR_ACCENT
    r = 180
    g = int(140 - 80 * ratio)
    b = int(60 - 40 * ratio)
    return (r, max(0, g), max(0, b))

# ================= 渲染 =================
def draw_sidebar(info):
    pygame.draw.rect(screen, config.COLOR_SIDEBAR, (0, 0, SIDEBAR_W, HEIGHT))
    pygame.draw.line(screen, config.COLOR_TEXT, (SIDEBAR_W - 4, 0), (SIDEBAR_W - 4, HEIGHT), 2)
    pygame.draw.line(screen, config.COLOR_TEXT, (SIDEBAR_W - 1, 0), (SIDEBAR_W - 1, HEIGHT), 1)
    
    y = 15
    screen.blit(font_title.render("GRAVITAS MECHANICA", True, config.COLOR_TEXT), (15, y))
    y += 30
    pygame.draw.line(screen, config.COLOR_TEXT, (15, y), (SIDEBAR_W - 20, y), 1)
    y += 15

    screen.blit(font_bold.render("【 物理参量调校 】", True, config.COLOR_TEXT), (15, y))
    for key, cfg in SLIDERS.items():
        val = getattr(config, key)
        screen.blit(font_text.render(f"{cfg['label']} : {val:.2f}", True, config.COLOR_TEXT), (15, cfg['y']))
        slider_y = cfg['y'] + 20
        pygame.draw.rect(screen, (200, 190, 170), (15, slider_y, 200, 6))
        ratio = max(0.0, min(1.0, (val - cfg['min']) / (cfg['max'] - cfg['min'])))
        knob_x = 15 + ratio * 200
        pygame.draw.circle(screen, config.COLOR_TEXT, (int(knob_x), slider_y + 3), 6)
        pygame.draw.circle(screen, (100, 90, 80), (int(knob_x), slider_y + 3), 4)
    
    y = 240
    screen.blit(font_small.render("拖拽滑块 / 按键盘 1~6 微调", True, (100, 90, 80)), (15, y))
    y += 30

    screen.blit(font_bold.render("【 操作指南 】", True, config.COLOR_TEXT), (15, y)); y += 24
    for t in ["← →  位移 / ↑  旋转", "空格 瞬间坠落", "滚轮 观测上下", "F    恢复视角跟随"]:
        screen.blit(font_text.render(t, True, (70, 60, 50)), (15, y)); y += 20

    y += 15
    screen.blit(font_bold.render("【 悬浮历史行应力 】", True, config.COLOR_TEXT), (15, y)); y += 24
    pygame.draw.line(screen, (150, 140, 120), (15, y), (SIDEBAR_W - 20, y), 1)
    y += 10
    
    for r, (ratio, can, n_above, thresh) in sorted(info.items(), reverse=True):
        color = stress_color(ratio, can)
        bar_w = int(120 * ratio)
        pygame.draw.rect(screen, (200, 190, 170), (100, y+2, 120, 10))
        pygame.draw.rect(screen, color, (100, y+2, bar_w, 10))
        txt = font_small.render(f"层{r:02d}: {n_above:02d}/{thresh:.1f}", True, color)
        screen.blit(txt, (15, y))
        if can: screen.blit(font_small.render(" 塌", True, config.COLOR_ACCENT), (225, y))
        y += 22
        if y > HEIGHT - 20: break

def draw_block_shape(x, y, color, is_historical=False):
    pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
    if is_historical:
        for i in range(0, CELL_SIZE, 6):
            pygame.draw.line(screen, (40, 35, 30), (x + i, y), (x + i - 10, y + CELL_SIZE), 1)
        pygame.draw.rect(screen, (40, 35, 30), (x, y, CELL_SIZE, CELL_SIZE), 1)
    else:
        light_color = tuple(min(255, c + 30) for c in color)
        dark_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.line(screen, light_color, (x+1, y+1), (x+CELL_SIZE-2, y+1), 2)
        pygame.draw.line(screen, light_color, (x+1, y+1), (x+1, y+CELL_SIZE-2), 2)
        pygame.draw.line(screen, dark_color, (x+CELL_SIZE-1, y+1), (x+CELL_SIZE-1, y+CELL_SIZE-1), 2)
        pygame.draw.line(screen, dark_color, (x+1, y+CELL_SIZE-1), (x+CELL_SIZE-1, y+CELL_SIZE-1), 2)

def draw_board():
    for c in range(config.COLS + 1):
        x = SIDEBAR_W + c * CELL_SIZE
        pygame.draw.line(screen, config.COLOR_GRID, (x, 0), (x, HEIGHT), 1)
    for r in range(VISIBLE_ROWS + 1):
        y = r * CELL_SIZE
        pygame.draw.line(screen, config.COLOR_GRID, (SIDEBAR_W, y), (SIDEBAR_W + WIDTH, y), 1)
    for r in range(game.grid.num_rows):
        for c in range(config.COLS):
            v = game.grid.grid[r][c]
            if v != 0:
                y = grid_to_screen_y(r)
                if y is not None:
                    draw_block_shape(SIDEBAR_W + c * CELL_SIZE, y, config.COLORS.get(v, (100, 100, 100)), v == -1)

def draw_current_block():
    if not game.current: return
    for r, c in game.current.get_cell_positions():
        y = grid_to_screen_y(r)
        if y is not None:
            draw_block_shape(SIDEBAR_W + c * CELL_SIZE, y, config.COLORS.get(game.current.id, (100, 100, 100)))

def draw_history_highlight(info):
    for r, (ratio, can, _, _) in info.items():
        y = grid_to_screen_y(r)
        if y is None: continue
        line_surf = pygame.Surface((WIDTH, 3), pygame.SRCALPHA)
        c = stress_color(ratio, can)
        line_surf.fill((c[0], c[1], c[2], 180))
        screen.blit(line_surf, (SIDEBAR_W, y))

def draw_scrollbar_with_marks(info):
    total = game.grid.num_rows
    pygame.draw.rect(screen, (200, 190, 170), (SIDEBAR_W + WIDTH, 0, SCROLLBAR_W, HEIGHT))
    pygame.draw.line(screen, config.COLOR_TEXT, (SIDEBAR_W + WIDTH, 0), (SIDEBAR_W + WIDTH, HEIGHT), 1)
    pygame.draw.line(screen, config.COLOR_TEXT, (SIDEBAR_W + WIDTH + SCROLLBAR_W -1, 0), (SIDEBAR_W + WIDTH + SCROLLBAR_W -1, HEIGHT), 1)
    if total <= VISIBLE_ROWS: return
    span = total - VISIBLE_ROWS
    bar_h = max(20, HEIGHT * VISIBLE_ROWS // total)
    bar_y = int((HEIGHT - bar_h) * (1 - scroll_offset / span))
    pygame.draw.rect(screen, (120, 110, 100), (SIDEBAR_W + WIDTH + 2, bar_y, SCROLLBAR_W - 4, bar_h))
    for r, (ratio, can, _, _) in info.items():
        pos_y = int((HEIGHT - 1) * (1 - r / (total - 1))) if total > 1 else 0
        pygame.draw.rect(screen, stress_color(ratio, can), (SIDEBAR_W + WIDTH + 1, pos_y, SCROLLBAR_W - 2, 2))

def draw_block_direction_indicator():
    if not game.current: return
    cells = game.current.get_cell_positions()
    if not cells: return
    rows = [r for r, _ in cells]
    min_r, max_r = min(rows), max(rows)
    top_visible = scroll_offset + VISIBLE_ROWS - 1

    if min_r < scroll_offset:
        dist = scroll_offset - min_r
        s = pygame.Surface((WIDTH, 26), pygame.SRCALPHA)
        s.fill((225, 215, 195, 200))
        screen.blit(s, (SIDEBAR_W, HEIGHT - 26))
        pygame.draw.polygon(screen, config.COLOR_TEXT, [(SIDEBAR_W + 16, HEIGHT - 20), (SIDEBAR_W + 28, HEIGHT - 20), (SIDEBAR_W + 22, HEIGHT - 8)])
        screen.blit(font_text.render(f"▼ 下方 {dist} 层", True, config.COLOR_TEXT), (SIDEBAR_W + 36, HEIGHT - 22))

    if max_r > top_visible:
        dist = max_r - top_visible
        s = pygame.Surface((WIDTH, 26), pygame.SRCALPHA)
        s.fill((225, 215, 195, 200))
        screen.blit(s, (SIDEBAR_W, 0))
        pygame.draw.polygon(screen, config.COLOR_TEXT, [(SIDEBAR_W + 16, 8), (SIDEBAR_W + 28, 8), (SIDEBAR_W + 22, 20)])
        screen.blit(font_text.render(f"▲ 上方 {dist} 层", True, config.COLOR_TEXT), (SIDEBAR_W + 36, 4))

# ================= 主循环 =================
fall_timer = 0

while not game.game_over:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); raise SystemExit
        
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if e.pos[0] < SIDEBAR_W:
                for key, cfg in SLIDERS.items():
                    if cfg['y'] <= e.pos[1] <= cfg['y'] + 30:
                        dragging_param = key
                        update_param_from_mouse(e.pos[0], key)
                        break
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            dragging_param = None
        if e.type == pygame.MOUSEMOTION and dragging_param:
            update_param_from_mouse(e.pos[0], dragging_param)

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_1: config.GRAVITY = max(0.1, round(config.GRAVITY - 0.1, 1))
            if e.key == pygame.K_2: config.GRAVITY = min(5.0, round(config.GRAVITY + 0.1, 1))
            if e.key == pygame.K_3: config.MATERIAL_MULT = max(0.1, round(config.MATERIAL_MULT - 0.1, 1))
            if e.key == pygame.K_4: config.MATERIAL_MULT = min(5.0, round(config.MATERIAL_MULT + 0.1, 1))
            if e.key == pygame.K_5: config.LINK_COEF = max(0.5, round(config.LINK_COEF - 0.5, 1))
            if e.key == pygame.K_6: config.LINK_COEF = min(20.0, round(config.LINK_COEF + 0.5, 1))

            if e.key == pygame.K_LEFT:   game.move(0, -1)
            if e.key == pygame.K_RIGHT:  game.move(0, 1)
            if e.key == pygame.K_UP:     game.rotate()
            if e.key == pygame.K_SPACE:  game.hard_drop()
            if e.key == pygame.K_PAGEUP:
                auto_follow = False
                scroll_offset = clamp_scroll(scroll_offset + VISIBLE_ROWS // 2)
            if e.key == pygame.K_PAGEDOWN:
                auto_follow = False
                scroll_offset = clamp_scroll(scroll_offset - VISIBLE_ROWS // 2)
            if e.key == pygame.K_HOME:
                auto_follow = False
                scroll_offset = 0
            if e.key == pygame.K_END:
                auto_follow = False
                scroll_offset = clamp_scroll(game.grid.num_rows - VISIBLE_ROWS)
            if e.key == pygame.K_f:
                auto_follow = True
                
        if e.type == pygame.MOUSEWHEEL:
            auto_follow = False
            scroll_offset = clamp_scroll(scroll_offset + e.y * 2)

    fall_timer += dt
    if fall_timer > 500:
        fall_timer = 0
        # 自动下落时也触发微小的移动音效
        if not game.move(-1, 0):
            game.lock()
            update_auto_follow()

    update_auto_follow()
    info = compute_floating_history_info()

    screen.fill(config.COLOR_BG)
    draw_sidebar(info)
    draw_board()
    draw_current_block()
    draw_history_highlight(info)
    draw_block_direction_indicator()
    draw_scrollbar_with_marks(info)
    screen.blit(noise_layer, (0, 0))
    pygame.display.flip()
