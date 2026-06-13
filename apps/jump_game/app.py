# ════════════════════════════════════════════════════════════════════════════
#  JUMP GAME — M5StickC Plus / UIFlow 2
#  Btn A      = sauter
#  Btn B long = retour launcher
# ════════════════════════════════════════════════════════════════════════════

import M5, time
from M5 import *
from libs.app_base import AppBase

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG     = 0x661111
C_GROUND = 0x4CAF50
C_PLAYER = 0x00BFFF
C_WHITE  = 0xFFFFFF
C_YELLOW = 0xFFD700
C_MUTED  = 0x888888

# ── Constantes ────────────────────────────────────────────────────────────────
W, H        = 135, 240
GROUND_Y    = H - 25
GROUND_H    = 25
PW, PH      = 14, 20
PX          = W // 2 - PW // 2
GRAVITY     = 1.4
JUMP_FORCE  = -15.0

# ── Init ──────────────────────────────────────────────────────────────────────
M5.begin()
Lcd.fillScreen(C_BG)
Lcd.fillRect(0, GROUND_Y, W, GROUND_H, C_GROUND)

lbl_score = Widgets.Label("Score: 0", 4, 2, 0.9, C_WHITE, C_BG, Widgets.FONTS.DejaVu12)
lbl_hint  = Widgets.Label("B long=quitter", 4, H - 14, 0.85, C_MUTED, C_BG, Widgets.FONTS.DejaVu12)

# ── État ──────────────────────────────────────────────────────────────────────
app         = AppBase()
player_y    = float(GROUND_Y - PH)
player_vy   = 0.0
is_grounded = True
score       = 0
frame_cnt   = 0
prev_y      = player_y

# ── Boucle ────────────────────────────────────────────────────────────────────
while app.update():
    M5.update()
    t0 = time.ticks_ms()

    # Saut
    if BtnA.wasPressed() and is_grounded:
        player_vy   = JUMP_FORCE
        is_grounded = False

    # Physique
    prev_y     = player_y
    player_vy += GRAVITY
    player_y  += player_vy
    limit = float(GROUND_Y - PH)
    if player_y >= limit:
        player_y    = limit
        player_vy   = 0.0
        is_grounded = True
    else:
        is_grounded = False

    # Rendu : efface ancienne pos, redessine sol + joueur
    Lcd.fillRect(PX, int(prev_y), PW, PH, C_BG)
    Lcd.fillRect(0, GROUND_Y, W, GROUND_H, C_GROUND)
    Lcd.fillRect(PX, int(player_y), PW, PH, C_PLAYER)
    # Yeux
    Lcd.fillRect(PX + 2, int(player_y) + 4, 3, 3, C_WHITE)
    Lcd.fillRect(PX + 9, int(player_y) + 4, 3, 3, C_WHITE)

    # Score
    frame_cnt += 1
    if frame_cnt % 10 == 0:
        score += 1
        lbl_score.setText("Score: " + str(score))

    # ~30 FPS
    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    wait = 33 - elapsed
    if wait > 0:
        time.sleep_ms(wait)
