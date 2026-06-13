# ════════════════════════════════════════════════════════════════════════════
#  RUNNER — M5StickC Plus / UIFlow 2  v10
# ════════════════════════════════════════════════════════════════════════════

import M5, time
from M5 import *
from libs.app_base import AppBase
from machine import PWM, Pin

Widgets.setRotation(3)
W, H = 240, 135

C_SKY_TOP  = 0x020818
C_SKY_MID  = 0x041230
C_SKY_BOT  = 0x061A48
C_CLOUD    = 0x0A1F50
C_CLOUD_LT = 0x0D2860
C_BUILD    = 0x2A2A2A
C_BUILD_LT = 0x383838
C_ROOF_TOP = 0xBBBBBB
C_ROOF     = 0x444444
C_LONG_PLT = 0x555555
C_LONG_TOP = 0xFFAA00
C_GROUND   = 0x111111
C_SKIN     = 0xFFCC88
C_SUIT     = 0xCC3300
C_HAIR     = 0x221100
C_SHOE     = 0x333333
C_EYE_P    = 0x000000
C_MON_BODY = 0x00FF44
C_MON_DARK = 0x008822
C_MON_EYE  = 0xFF0000
C_ACCENT   = 0xFF6600
C_DEAD     = 0xFF2200
C_HUD      = 0xDDDDDD
C_STREAK   = 0x0A2060

PLAYER_W      = 10
PLAYER_H      = 16
PLAYER_X      = 38
GRAVITY       = 0.45
JUMP_V        = -3.96
JUMP_BOOST    = -0.20
JUMP_HOLD_MAX = 12
MAX_JUMPS     = 2
GROUND_H      = 8
MON_W         = 10
MON_H         = 12
BLDG_H_MIN    = 25
BLDG_H_MAX    = 80
LONG_H        = 14
MIN_GAP       = 36
MAX_GAP       = 68

# ── Buzzer ────────────────────────────────────────────────────────────────────
_buzz = None
def _buzz_on(f):
    global _buzz
    try:
        if _buzz is None: _buzz = PWM(Pin(2), freq=max(1,f), duty=512)
        else: _buzz.freq(max(1,f)); _buzz.duty(512)
    except: pass
def _buzz_off():
    try:
        if _buzz: _buzz.duty(0)
    except: pass

_MELODY = [
    (110,60),(0,10),(110,60),(0,10),(165,120),(0,20),
    (110,60),(0,10),(110,60),(0,10),(147,90),(0,15),(138,90),(0,30),
    (123,60),(0,10),(123,60),(0,10),(185,120),(0,20),
    (123,60),(0,10),(123,60),(0,10),(174,90),(0,15),(165,90),(0,30),
    (147,50),(0,10),(165,50),(0,10),(185,50),(0,10),(196,50),(0,10),
    (220,80),(0,15),(220,80),(0,15),(220,80),(0,15),(0,30),
    (220,70),(0,10),(220,70),(0,10),(330,100),(0,15),
    (294,70),(0,10),(294,70),(0,10),(440,100),(0,15),
    (262,70),(0,10),(262,70),(0,10),(392,100),(0,15),
    (247,140),(0,30),
    (659,60),(0,10),(622,60),(0,10),(587,60),(0,10),(523,60),(0,10),
    (494,80),(0,15),(440,80),(0,15),(415,80),(0,15),(392,120),(0,25),
    (440,60),(0,10),(494,60),(0,10),(523,80),(0,15),
    (587,60),(0,10),(622,60),(0,10),(659,120),(0,25),
    (880,40),(0,8),(784,40),(0,8),(698,40),(0,8),(659,40),(0,8),
    (622,40),(0,8),(587,40),(0,8),(523,40),(0,8),(494,80),(0,20),
    (523,40),(0,8),(587,40),(0,8),(659,40),(0,8),(698,40),(0,8),
    (784,40),(0,8),(880,40),(0,8),(988,80),(0,20),
    (110,60),(0,10),(110,60),(0,10),(165,120),(0,20),
    (123,60),(0,10),(123,60),(0,10),(185,120),(0,20),
    (147,60),(0,10),(165,60),(0,10),(185,60),(0,10),(220,180),(0,40),
    (0,80),
]
_mi=0; _mn=0; _mon=False
def music_start():
    global _mi,_mn,_mon; _mi=0; _mn=time.ticks_ms(); _mon=True
def music_stop():
    global _mon; _mon=False; _buzz_off()
def music_update():
    global _mi,_mn
    if not _mon: return
    if time.ticks_diff(time.ticks_ms(),_mn)<0: return
    f,d=_MELODY[_mi]
    _buzz_on(f) if f else _buzz_off()
    _mn=time.ticks_ms()+d; _mi=(_mi+1)%len(_MELODY)
def play_death_music():
    music_stop()
    for f,d in [(523,120),(466,120),(415,120),(370,180),(0,80),(330,120),(294,120),(262,300)]:
        _buzz_on(f) if f else _buzz_off(); time.sleep_ms(d)
    _buzz_off()
def snd_jump():      _buzz_off(); _buzz_on(900); time.sleep_ms(40)
def snd_milestone(): _buzz_off(); _buzz_on(1200); time.sleep_ms(50)

# ── PRNG ──────────────────────────────────────────────────────────────────────
_seed = time.ticks_ms()
def _rand(mn,mx):
    global _seed
    _seed=(_seed*1103515245+12345)&0x7FFFFFFF
    return mn+(_seed%(mx-mn))

# ── Streaks ───────────────────────────────────────────────────────────────────
_streaks=[]
def init_streaks():
    global _streaks
    _streaks=[{"x":float(_rand(0,W)),"y":_rand(15,H-GROUND_H-5),"w":_rand(20,50)} for _ in range(5)]

def update_streaks(speed):
    for s in _streaks:
        sx=int(s["x"]); sw=s["w"]
        if 0<=sx<W: restore_bg(sx, s["y"], min(sw,W-sx), 1)
        s["x"]-=speed*2.2
        if s["x"]+sw<0:
            s["x"]=float(W+_rand(0,30))
            s["y"]=_rand(15,H-GROUND_H-5)
            s["w"]=_rand(20,50)
        sx=int(s["x"])
        on_bldg=False
        for p in _cur_plats:
            if int(p["x"])<=sx<int(p["x"])+p["w"] and p["top_y"]<=s["y"]:
                on_bldg=True; break
        if not on_bldg and 0<=sx<W:
            Lcd.fillRect(sx, s["y"], min(s["w"],W-sx), 1, C_STREAK)

# ── Décor ─────────────────────────────────────────────────────────────────────
_clouds=[]
def gen_bg_data():
    global _clouds; _clouds=[]
    for _ in range(6):
        _clouds.append((_rand(0,W-30),_rand(4,36),_rand(28,62),_rand(8,16)))

def draw_static_bg():
    t=H//3
    Lcd.fillRect(0,0,  W,t,     C_SKY_TOP)
    Lcd.fillRect(0,t,  W,t,     C_SKY_MID)
    Lcd.fillRect(0,2*t,W,H-2*t, C_SKY_BOT)
    for cx,cy,cw,ch in _clouds:
        Lcd.fillRect(cx,   cy+2, cw,   ch-4, C_CLOUD)
        Lcd.fillRect(cx+3, cy,   cw-6, ch,   C_CLOUD)
        Lcd.fillRect(cx+1, cy+1, cw-2, 2,    C_CLOUD_LT)
    Lcd.fillRect(0, H-GROUND_H, W, GROUND_H, C_GROUND)

def restore_bg(rx,ry,rw,rh):
    rx=max(0,rx); ry=max(0,ry)
    rw=min(rw,W-rx); rh=min(rh,H-ry)
    if rw<=0 or rh<=0: return
    t=H//3
    for sy,ey,c in [(0,t,C_SKY_TOP),(t,2*t,C_SKY_MID),(2*t,H,C_SKY_BOT)]:
        oy=max(sy,ry); oy2=min(ey,ry+rh)
        if oy2>oy: Lcd.fillRect(rx,oy,rw,oy2-oy,c)
    for cx,cy,cw,ch in _clouds:
        if cx<rx+rw and cx+cw>rx:
            ix0=max(cx,rx); ix1=min(cx+cw,rx+rw)
            iy0=max(cy-1,ry); iy1=min(cy+ch+1,ry+rh)
            if ix1>ix0 and iy1>iy0:
                Lcd.fillRect(ix0,iy0,ix1-ix0,iy1-iy0,C_CLOUD)
    if ry+rh>H-GROUND_H:
        sy2=max(ry,H-GROUND_H)
        Lcd.fillRect(rx,sy2,rw,H-sy2,C_GROUND)

# ── Immeubles ─────────────────────────────────────────────────────────────────
def _draw_bldg_segment(p, base_px, sx0, sx1):
    """Redessine le fond de la plateforme entre sx0 et sx1 (coordonnées écran clippées)."""
    if sx1 <= sx0: return
    w  = sx1 - sx0
    ty = p["top_y"]
    if p.get("long"):
        Lcd.fillRect(sx0, ty,        w, LONG_H,       C_LONG_PLT)
        Lcd.fillRect(sx0, ty,        w, 2,            C_LONG_TOP)
        Lcd.fillRect(sx0, ty+LONG_H, w, H-ty-LONG_H,  C_BUILD)
    else:
        Lcd.fillRect(sx0, ty,   w, 1, C_ROOF_TOP)
        Lcd.fillRect(sx0, ty+1, w, 1, C_ROOF)
        bh = H - ty - 2
        if bh > 0:
            le = max(sx0, base_px)  # colonne du bord gauche sombre
            if le < sx1:
                Lcd.fillRect(le, ty+2, 1, bh, C_BUILD)
                if sx1 > le+1: Lcd.fillRect(le+1, ty+2, sx1-(le+1), bh, C_BUILD_LT)
                if sx0 < le:   Lcd.fillRect(sx0,  ty+2, le-sx0,     bh, C_BUILD_LT)
            else:
                Lcd.fillRect(sx0, ty+2, w, bh, C_BUILD_LT)

def draw_building(p):
    px=int(p["x"]); bw=p["w"]
    x0=max(0,px); x1=min(W,px+bw)
    if x1<=x0: return
    _draw_bldg_segment(p, px, x0, x1)
    # Monstres
    all_mon=[]
    if p["mon_x"]>=0: all_mon.append(p["mon_x"])
    all_mon+=p.get("mon_extras",[])
    for emx in all_mon:
        mx=px+emx
        if mx+MON_W>0 and mx<W:
            draw_monster(mx, p["top_y"]-MON_H)

def erase_building(p):
    prev = int(p["prev_x"])
    cur  = int(p["x"])
    bw   = p["w"]
    ty   = p["top_y"]
    top  = ty - MON_H - 1
    htot = H - top

    # Tranche gauche disparaissant
    ex0 = max(0, prev); ex1 = max(0, cur)
    if ex1 > ex0: restore_bg(ex0, top, ex1-ex0, htot)

    # Tranche droite éventuelle
    rx0 = min(W, prev+bw); rx1 = min(W, cur+bw)
    if rx0 > rx1: restore_bg(rx1, top, rx0-rx1, htot)

    # Efface l'ancienne position de chaque monstre et redessine la plateforme dessous
    all_mon=[]
    if p["mon_x"]>=0: all_mon.append(p["mon_x"])
    all_mon+=p.get("mon_extras",[])
    for emx in all_mon:
        mx0 = max(0, prev+emx)
        mx1 = min(W, prev+emx+MON_W)
        if mx1 > mx0:
            restore_bg(mx0, ty-MON_H, mx1-mx0, MON_H+2)
            _draw_bldg_segment(p, prev, mx0, mx1)

# ── Monstre ───────────────────────────────────────────────────────────────────
_MON=[
    (1,0,2,3,C_MON_BODY),(7,0,2,3,C_MON_BODY),
    (0,3,10,7,C_MON_BODY),(2,6,6,3,C_MON_DARK),
    (2,4,2,2,C_MON_EYE),(6,4,2,2,C_MON_EYE),
    (3,4,1,1,0x000000),(7,4,1,1,0x000000),
    (3,8,4,2,C_MON_DARK),(4,8,2,1,0xFFFFFF),
    (1,10,2,3,C_MON_BODY),(4,10,2,2,C_MON_BODY),(7,10,2,3,C_MON_BODY),
]
def draw_monster(mx,my):
    for dx,dy,w,h,c in _MON:
        nx=mx+dx
        if my+dy>=0 and 0<=nx<W: Lcd.fillRect(nx,my+dy,w,h,c)

# ── Joueur ────────────────────────────────────────────────────────────────────
_BASE=[(2,0,6,6,C_SKIN),(3,0,4,1,C_HAIR),(5,2,1,1,C_EYE_P),(1,6,8,5,C_SUIT)]
_RA  =[(1,11,3,3,C_SUIT),(6,11,3,3,C_SUIT),(1,13,2,3,C_SHOE),(7,13,2,3,C_SHOE)]
_RB  =[(3,11,4,5,C_SUIT),(3,14,2,3,C_SHOE),(5,14,2,3,C_SHOE)]
_JMP =[(2,11,3,3,C_SUIT),(5,11,3,3,C_SUIT),(1,12,3,2,C_SHOE),(6,12,3,2,C_SHOE)]

def erase_player(py):
    restore_bg(PLAYER_X-2, int(py)-2, PLAYER_W+4, PLAYER_H+4)
    for p in _cur_plats:
        px2=int(p["x"]); bw=p["w"]; ty=p["top_y"]
        ox=max(PLAYER_X-2,px2); ox2=min(PLAYER_X+PLAYER_W+2,px2+bw)
        if ox2<=ox: continue
        _draw_bldg_segment(p, px2, ox, ox2)
        # Redessine monstres dans la zone
        all_mon=[]
        if p["mon_x"]>=0: all_mon.append(p["mon_x"])
        all_mon+=p.get("mon_extras",[])
        for emx in all_mon:
            mx=px2+emx; my=ty-MON_H
            if mx+MON_W>PLAYER_X-2 and mx<PLAYER_X+PLAYER_W+2:
                draw_monster(mx,my)

def draw_player(py, af, jumping, sq):
    iy=int(py)
    legs=_JMP if jumping else (_RA if af%2==0 else _RB)
    if sq>0:
        off_x=-1; extra_w=2; off_y=2; extra_h=-2
    elif jumping:
        off_x=1; extra_w=-2; off_y=-1; extra_h=1
    else:
        off_x=0; extra_w=0; off_y=0; extra_h=0
    for dx,dy,w,h,c in _BASE+legs:
        nx=PLAYER_X+dx+off_x; ny=iy+dy+off_y
        nw=max(1,w+extra_w); nh=max(1,h+extra_h)
        if 0<=nx<W and 0<=ny<H: Lcd.fillRect(nx,ny,nw,nh,c)

# ── Plateformes ───────────────────────────────────────────────────────────────
_cur_plats=[]

def new_platform(x, speed):
    if _rand(0,4)==0:
        w=_rand(200,480)
        n_mon=_rand(1,3)
        mon_list=[]
        for i in range(n_mon):
            slot=(w-20)//(n_mon+1)*(i+1)+10
            mon_list.append(max(6,min(slot,w-MON_W-6)))
        ty=H-LONG_H-GROUND_H-_rand(5,25)
        return {"x":float(x),"w":w,"top_y":ty,
                "prev_x":float(x),"mon_x":mon_list[0],
                "mon_extras":mon_list[1:],"long":True}
    else:
        w=_rand(38,85)
        ty=_rand(H-BLDG_H_MAX,H-BLDG_H_MIN)
        return {"x":float(x),"w":w,"top_y":ty,
                "prev_x":float(x),"mon_x":-1,"mon_extras":[],"long":False}

def init_platforms():
    p0={"x":0.0,"w":150,"top_y":H-55,"prev_x":0.0,
        "mon_x":-1,"mon_extras":[],"long":False}
    plats=[p0]; x=150+MIN_GAP
    while x<W+40:
        p=new_platform(x,3.5); plats.append(p); x=p["x"]+p["w"]+_rand(MIN_GAP,MAX_GAP)
    return plats

# ── HUD ───────────────────────────────────────────────────────────────────────
M5.begin(); Lcd.fillScreen(C_SKY_TOP)
lbl_score=Widgets.Label("0",    4,  2,1.0,C_HUD,   C_SKY_TOP,Widgets.FONTS.DejaVu18)
lbl_speed=Widgets.Label("x3.5",178, 2,1.0,C_ACCENT,C_SKY_TOP,Widgets.FONTS.DejaVu18)
def update_hud(s,sp):
    lbl_score.setText(str(s)); lbl_speed.setText("x{:.1f}".format(sp))

def show_title(best):
    _cur_plats.clear(); gen_bg_data(); draw_static_bg()
    Widgets.Label("RUNNER",          62, 10,2.0,C_ACCENT, C_SKY_TOP,Widgets.FONTS.DejaVu18)
    Widgets.Label("A court=p.saut",  44, 50,1.0,C_HUD,    C_SKY_TOP,Widgets.FONTS.DejaVu18)
    Widgets.Label("A long =g.saut",  44, 70,1.0,C_HUD,    C_SKY_TOP,Widgets.FONTS.DejaVu18)
    Widgets.Label("Best: "+str(best),68, 90,1.0,C_ACCENT, C_SKY_TOP,Widgets.FONTS.DejaVu18)
    Widgets.Label("-- Appuie A --",  54,112,1.0,0x8899AA,  C_SKY_TOP,Widgets.FONTS.DejaVu18)

def show_gameover(score,best):
    Lcd.fillScreen(0x080010)
    Widgets.Label("GAME OVER",         54, 12,2.0,C_DEAD,   0x080010,Widgets.FONTS.DejaVu18)
    Widgets.Label("Score: "+str(score),54, 52,1.0,C_HUD,    0x080010,Widgets.FONTS.DejaVu18)
    Widgets.Label("Best : "+str(best), 54, 72,1.0,C_ACCENT, 0x080010,Widgets.FONTS.DejaVu18)
    Widgets.Label("-- Appuie A --",    54,102,1.0,0x8899AA,  0x080010,Widgets.FONTS.DejaVu18)

# ── Boucle principale ─────────────────────────────────────────────────────────
app=AppBase(); best=0
show_title(best)
while app.running:
    M5.update(); app.update()
    if BtnA.wasPressed(): break
    time.sleep_ms(20)

while app.running:
    gen_bg_data()
    plats=init_platforms()
    _cur_plats.clear()
    for p in plats: _cur_plats.append(p)
    init_streaks()
    speed=3.5
    player_y=float(plats[0]["top_y"]-PLAYER_H)
    player_vy=0.0; jumps_left=MAX_JUMPS
    score=0; frame_cnt=0; prev_ms=0; alive=True
    prev_py=player_y; jump_held=False; jump_frames=0
    was_holding=False; anim_frame=0; anim_tick=0
    is_jumping=False; _squash=0

    draw_static_bg()
    for p in plats: draw_building(p)
    draw_player(player_y,0,False,0)
    update_hud(score,speed)
    music_start()

    while alive and app.running:
        M5.update(); app.update()
        t0=time.ticks_ms(); music_update()

        btn_down=BtnA.isPressed()
        if btn_down and not was_holding and jumps_left>0:
            player_vy=JUMP_V; jumps_left-=1
            jump_held=True; jump_frames=JUMP_HOLD_MAX
            is_jumping=True; snd_jump()
        if btn_down and jump_held and jump_frames>0 and player_vy<0:
            player_vy+=JUMP_BOOST; jump_frames-=1
        elif not btn_down:
            jump_held=False; jump_frames=0
        was_holding=btn_down

        player_vy+=GRAVITY; player_y+=player_vy

        for p in plats:
            p["prev_x"]=p["x"]; p["x"]-=speed

        # Supprime immeubles sortis — efface la zone résiduelle d'abord
        while plats and plats[0]["x"]+plats[0]["w"]<0:
            old=plats.pop(0)
            ex1=max(0, int(old["prev_x"])+old["w"])
            if ex1>0:
                restore_bg(0, old["top_y"]-MON_H-1, ex1, H-(old["top_y"]-MON_H-1))
            if old in _cur_plats: _cur_plats.remove(old)

        last_x=plats[-1]["x"]+plats[-1]["w"] if plats else W
        while last_x<W+80:
            p=new_platform(last_x+_rand(MIN_GAP,MAX_GAP), speed)
            plats.append(p); _cur_plats.append(p)
            last_x=p["x"]+p["w"]

        for p in plats:
            if int(p["prev_x"])!=int(p["x"]):
                erase_building(p); draw_building(p)

        update_streaks(speed)

        # Collisions plateformes
        feet=player_y+PLAYER_H
        for p in plats:
            px2=int(p["x"]); pw=p["w"]; ty=p["top_y"]
            if (PLAYER_X+PLAYER_W>px2 and PLAYER_X<px2+pw and
                    feet>=ty and feet<=ty+max(abs(player_vy),1)+2 and
                    player_vy>=0):
                if _squash==0: _squash=4
                player_y=float(ty-PLAYER_H); player_vy=0.0
                jump_held=False; is_jumping=False; jumps_left=MAX_JUMPS
                all_mon=[]
                if p["mon_x"]>=0: all_mon.append(p["mon_x"])
                all_mon+=p.get("mon_extras",[])
                for emx in all_mon:
                    if PLAYER_X+PLAYER_W>px2+emx and PLAYER_X<px2+emx+MON_W:
                        alive=False
                break

        if alive:
            for p in plats:
                px2=int(p["x"]); ty=p["top_y"]; oy=ty-MON_H
                all_mon=[]
                if p["mon_x"]>=0: all_mon.append(p["mon_x"])
                all_mon+=p.get("mon_extras",[])
                for emx in all_mon:
                    ox=px2+emx
                    if (PLAYER_X+PLAYER_W>ox and PLAYER_X<ox+MON_W and
                            int(player_y)+PLAYER_H>oy and int(player_y)<ty):
                        alive=False; break
                if not alive: break

        if player_y>H+20: alive=False
        if not alive: break

        if _squash>0: _squash-=1

        erase_player(prev_py)
        anim_tick+=1
        if anim_tick>=5: anim_tick=0; anim_frame+=1
        draw_player(player_y, anim_frame, is_jumping, _squash)
        prev_py=player_y

        frame_cnt+=1
        if frame_cnt%3==0: score+=1
        ms=score//50
        if ms>prev_ms:
            prev_ms=ms; speed=min(3.5+ms*0.4,9.0); snd_milestone()

        update_hud(score,speed)
        elapsed=time.ticks_diff(time.ticks_ms(),t0)
        wait=33-elapsed
        if wait>0: time.sleep_ms(wait)

    if not app.running: break
    play_death_music()
    if score>best: best=score
    show_gameover(score,best)
    while app.running:
        M5.update(); app.update()
        if BtnA.wasPressed(): break
        time.sleep_ms(20)

Widgets.setRotation(0)
