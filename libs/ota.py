# ════════════════════════════════════════════════════════════════════════════
# OTA — Mise à jour Over-The-Air depuis GitHub
# Placer dans /flash/libs/ota.py
# ════════════════════════════════════════════════════════════════════════════

import json, os, time
import requests
from M5 import Lcd, Widgets

# ── Configuration ─────────────────────────────────────────────────────────────
GITHUB_RAW   = "https://raw.githubusercontent.com/PaulTestDev/m5stick-apps/main"
MANIFEST_URL = GITHUB_RAW + "/manifest.json"
APPS_DIR     = "/flash/apps"

# ── Couleurs ──────────────────────────────────────────────────────────────────
W, H     = 135, 240
C_BG     = 0x111111
C_ACCENT = 0x00BFFF
C_TEXT   = 0xFFFFFF
C_MUTED  = 0x888888
C_OK     = 0x00CC66
C_ERR    = 0xFF4444
C_HEADER = 0x222222

F12 = Widgets.FONTS.DejaVu12
F18 = Widgets.FONTS.DejaVu18

# ── Affichage ─────────────────────────────────────────────────────────────────
def _header(title):
    Lcd.fillScreen(C_BG)
    Lcd.fillRect(0, 0, W, 28, C_HEADER)
    Widgets.Label(title, 6, 5, 1.0, C_TEXT, C_HEADER, F18)

def _line(text, y, color=None):
    if color is None:
        color = C_TEXT
    Widgets.Label(text, 6, y, 1.0, color, C_BG, F18)

def _status(text, color=None):
    if color is None:
        color = C_MUTED
    Lcd.fillRect(0, H - 26, W, 26, 0x1A1A1A)
    Widgets.Label(text, 6, H - 21, 1.0, color, 0x1A1A1A, F18)

# ── Réseau avec suivi de redirection ─────────────────────────────────────────
def _http_get(url, timeout=15):
    """GET avec suivi manuel des redirections (301/302/307)."""
    for _ in range(5):  # max 5 redirections
        r = requests.get(url, timeout=timeout)
        if r.status_code in (301, 302, 307, 308):
            url = r.headers.get("Location", url)
            r.close()
            continue
        return r
    raise Exception("Trop de redirections")

def _get_json(url):
    r = _http_get(url)
    if r.status_code != 200:
        r.close()
        raise Exception("HTTP " + str(r.status_code))
    data = r.json()
    r.close()
    return data

def _download_file(url, dest_path):
    r = _http_get(url)
    if r.status_code != 200:
        r.close()
        raise Exception("HTTP " + str(r.status_code))
    folder = dest_path.rsplit("/", 1)[0]
    try:
        os.mkdir(folder)
    except OSError:
        pass
    tmp_path = dest_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(r.content)
    r.close()
    try:
        os.remove(dest_path)
    except OSError:
        pass
    os.rename(tmp_path, dest_path)

# ── Logique principale ────────────────────────────────────────────────────────
def _get_local_version(app_id):
    try:
        with open(APPS_DIR + "/" + app_id + "/meta.json") as f:
            meta = json.load(f)
        return meta.get("version", 0)
    except (OSError, ValueError):
        return -1

def check_and_update():
    _header("MAJ OTA")
    _line("Connexion...", 40, C_MUTED)

    try:
        _status("Recup. manifest...")
        manifest = _get_json(MANIFEST_URL)
    except Exception as e:
        _header("MAJ OTA")
        _line("Erreur reseau", 50, C_ERR)
        _line(str(e)[:16], 76, C_ERR)
        _status("Btn A = retour")
        return False

    remote_apps = manifest.get("apps", {})

    to_update = []
    for app_id, info in remote_apps.items():
        local_v  = _get_local_version(app_id)
        remote_v = info.get("version", 1)
        if remote_v > local_v:
            to_update.append((app_id, info, local_v, remote_v))

    if not to_update:
        _header("MAJ OTA")
        _line("Tout est", 60, C_OK)
        _line("a jour !", 86, C_OK)
        _line(str(len(remote_apps)) + " app(s) OK", 116, C_MUTED)
        _status("Btn A = retour")
        return False

    _header("MAJ OTA")
    _line(str(len(to_update)) + " MAJ dispo", 36, C_ACCENT)

    updated = 0
    y = 64
    for app_id, info, local_v, remote_v in to_update:
        label = app_id[:10]
        _line(label + "...", y, C_MUTED)
        try:
            url_app  = GITHUB_RAW + "/apps/" + app_id + "/app.py"
            dest_app = APPS_DIR + "/" + app_id + "/app.py"
            _download_file(url_app, dest_app)

            url_meta  = GITHUB_RAW + "/apps/" + app_id + "/meta.json"
            dest_meta = APPS_DIR + "/" + app_id + "/meta.json"
            _download_file(url_meta, dest_meta)

            _line(label + " v" + str(remote_v), y, C_OK)
            updated += 1
        except Exception:
            _line(label + " ERR", y, C_ERR)

        y += 26
        if y > H - 40:
            y = 64

    _status(str(updated) + "/" + str(len(to_update)) + " OK  A=ret", C_OK)
    return updated > 0
