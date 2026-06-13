# ════════════════════════════════════════════════════════════════════════════
# LAUNCHER — M5StickC Plus / UIFlow 2
# Navigation : A = suivant | B = précédent | A long = ouvrir | B long = menu
# ════════════════════════════════════════════════════════════════════════════

import M5, os, time, json
from M5 import *

# ── Constantes ────────────────────────────────────────────────────────────────
W, H       = 135, 240
C_BG       = 0x111111
C_ACCENT   = 0x00BFFF
C_TEXT     = 0xFFFFFF
C_MUTED    = 0x888888
C_HEADER   = 0x222222
C_MENU_SEL = 0x005577
APPS_DIR   = "apps"
ITEM_H     = 44
HEADER_H   = 30
VISIBLE    = (H - HEADER_H) // ITEM_H

F12 = Widgets.FONTS.DejaVu12
F18 = Widgets.FONTS.DejaVu18

# ── Scan des apps ─────────────────────────────────────────────────────────────
def scan_apps():
    apps = []
    try:
        entries = os.listdir(APPS_DIR)
    except OSError:
        return apps
    for entry in sorted(entries):
        meta_path = APPS_DIR + "/" + entry + "/meta.json"
        app_path  = APPS_DIR + "/" + entry + "/app.py"
        try:
            os.stat(app_path)
            with open(meta_path) as f:
                meta = json.load(f)
            apps.append({
                "id":      entry,
                "name":    meta.get("name", entry),
                "version": meta.get("version", 0),
                "path":    app_path,
            })
        except (OSError, ValueError):
            pass
    return apps

# ── UI liste ──────────────────────────────────────────────────────────────────
_lbl_header = None
_lbl_names  = []
_lbl_vers   = []

def _build_ui(apps, selected):
    global _lbl_header, _lbl_names, _lbl_vers
    Lcd.fillScreen(C_BG)
    Lcd.fillRect(0, 0, W, HEADER_H, C_HEADER)
    _lbl_header = Widgets.Label(
        "APPS {}/{}".format(selected + 1, max(len(apps), 1)),
        6, 6, 1.0, C_TEXT, C_HEADER, F18
    )
    _lbl_names = []
    _lbl_vers  = []
    for i in range(VISIBLE):
        y  = HEADER_H + i * ITEM_H
        ln = Widgets.Label("", 10, y + 6,  1.0, C_TEXT,  C_BG, F18)
        lv = Widgets.Label("", 10, y + 26, 1.0, C_MUTED, C_BG, F12)
        _lbl_names.append(ln)
        _lbl_vers.append(lv)

def _render_list(apps, selected):
    if not apps:
        Lcd.fillScreen(C_BG)
        Widgets.Label("Aucune app", 14, 105, 1.0, C_MUTED, C_BG, F18)
        return
    scroll = max(0, min(selected - VISIBLE // 2, len(apps) - VISIBLE))
    scroll = max(0, scroll)
    if _lbl_header:
        _lbl_header.setText("APPS {}/{}".format(selected + 1, len(apps)))
    for i in range(VISIBLE):
        idx    = scroll + i
        y      = HEADER_H + i * ITEM_H
        is_sel = (idx == selected)
        if idx < len(apps):
            bg = C_ACCENT if is_sel else C_BG
            fg = 0x111111 if is_sel else C_TEXT
            mv = 0x003355 if is_sel else C_MUTED
            Lcd.fillRect(0, y, W, ITEM_H - 1, bg)
            _lbl_names[i].setColor(fg, bg)
            _lbl_vers[i].setColor(mv, bg)
            _lbl_names[i].setText(apps[idx]["name"])
            _lbl_vers[i].setText("v" + str(apps[idx]["version"]))
        else:
            Lcd.fillRect(0, y, W, ITEM_H - 1, C_BG)
            _lbl_names[i].setText("")
            _lbl_vers[i].setText("")
        Lcd.fillRect(0, y + ITEM_H - 1, W, 1, 0x333333)

# ── Menu OTA (B long) ─────────────────────────────────────────────────────────
MENU_ITEMS = ["Verifier MAJ", "Annuler"]

def _draw_menu(sel):
    Lcd.fillScreen(C_BG)
    Lcd.fillRect(0, 0, W, HEADER_H, C_HEADER)
    Widgets.Label("OPTIONS", 6, 6, 1.0, C_TEXT, C_HEADER, F18)
    for i, label in enumerate(MENU_ITEMS):
        y  = 44 + i * 52
        bg = C_MENU_SEL if i == sel else C_BG
        fg = C_ACCENT   if i == sel else C_TEXT
        Lcd.fillRect(4, y, W - 8, 42, bg)
        Widgets.Label(label, 10, y + 12, 1.0, fg, bg, F18)
    Lcd.fillRect(0, H - 28, W, 28, 0x1A1A1A)
    Widgets.Label("A=ok  B=nav", 10, H - 22, 1.0, C_MUTED, 0x1A1A1A, F18)

def run_menu():
    sel = 0
    _draw_menu(sel)
    while BtnB.isPressed():
        M5.update()
        time.sleep_ms(20)

    updated = False
    while True:
        M5.update()

        if BtnB.wasPressed():
            sel = (sel + 1) % len(MENU_ITEMS)
            _draw_menu(sel)

        if BtnA.wasPressed():
            if sel == 0:
                from libs.ota import check_and_update
                updated = check_and_update()
                while True:
                    M5.update()
                    if BtnA.wasPressed():
                        break
                    time.sleep_ms(20)
            break

        time.sleep_ms(30)

    return updated

# ── Écran d'erreur ────────────────────────────────────────────────────────────
def show_error(e):
    Lcd.fillScreen(0x220000)
    Lcd.fillRect(0, 0, W, 30, 0x880000)
    Widgets.Label("ERREUR APP", 10, 6, 1.0, 0xFFAAAA, 0x880000, F18)
    msg   = type(e).__name__ + ": " + str(e)
    CHARS = 14
    lines = []
    while msg:
        lines.append(msg[:CHARS])
        msg = msg[CHARS:]
        if len(lines) >= 6:
            break
    for i, line in enumerate(lines):
        Widgets.Label(line, 6, 38 + i * 26, 1.0, 0xFFFFFF, 0x220000, F18)
    Lcd.fillRect(0, H - 28, W, 28, 0x330000)
    Widgets.Label("Btn A = retour", 6, H - 22, 1.0, 0xFFAAAA, 0x330000, F18)
    while True:
        M5.update()
        if BtnA.wasPressed():
            break
        time.sleep_ms(20)

# ── Lancement d'une app ───────────────────────────────────────────────────────
def launch_app(app):
    Lcd.fillScreen(C_BG)
    try:
        with open(app["path"]) as f:
            code = f.read()
        exec(code, {"__name__": app["id"]})
    except Exception as e:
        show_error(e)

# ── Boucle principale ─────────────────────────────────────────────────────────
def run_launcher():
    # ── Protection boot_option ────────────────────────────────────────────
    try:
        import esp32
        nvs = esp32.NVS("uiflow")
        if nvs.get_u8("boot_option") != 2:
            nvs.set_u8("boot_option", 2)
            nvs.commit()
    except:
        pass
    # ─────────────────────────────────────────────────────────────────────

    M5.begin()
    apps     = scan_apps()
    selected = 0

    _build_ui(apps, selected)
    _render_list(apps, selected)

    b_hold_start = None

    while True:
        M5.update()

        if BtnB.wasPressed():
            if apps:
                selected = (selected - 1) % len(apps)
                _render_list(apps, selected)
            b_hold_start = None

        if BtnB.isPressed():
            if b_hold_start is None:
                b_hold_start = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), b_hold_start) > 700:
                b_hold_start = None
                updated = run_menu()
                apps    = scan_apps()
                if selected >= len(apps):
                    selected = max(0, len(apps) - 1)
                _build_ui(apps, selected)
                _render_list(apps, selected)
        else:
            b_hold_start = None

        if BtnA.wasPressed():
            if apps:
                selected = (selected + 1) % len(apps)
                _render_list(apps, selected)

        if BtnA.isHolding():
            if apps:
                time.sleep_ms(500)
                if BtnA.isHolding():
                    launch_app(apps[selected])
                    apps = scan_apps()
                    _build_ui(apps, selected)
                    _render_list(apps, selected)

        time.sleep_ms(30)

run_launcher()
