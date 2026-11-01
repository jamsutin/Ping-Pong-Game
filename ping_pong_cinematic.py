# Ping-Pong-Game
# Game klasik ping pong yang dibuat lebih modern mengikuti zaman dengan hasil ide ide 100% dari saya sendiri dan  dibantu claude ai sebagai ai pembantu saat coding (Tugas Sekolah By Frs)

# -*- coding: utf-8 -*-
"""
PING PONG - CINEMATIC SKILL EDITION  (By Fredd)
===============================================

Cara menjalankan:
    py -m pip install pygame        (atau: py -m pip install pygame-ce)
    py ping_pong_cinematic.py

Kontrol:
    Menu     : TAB ganti halaman (PERTANDINGAN / KARAKTER), UP/DOWN pilih baris,
               LEFT/RIGHT ubah pilihan, ketik untuk mengisi NAMA, ENTER mulai
    1 PEMAIN : UP/DOWN atau W/S gerakkan paddle (sisi kanan), SPACE = pakai skill,
               P atau ESC = pause
    2 PEMAIN : Pemain 1 (kiri)  W = atas, S = bawah, D = pakai skill
               Pemain 2 (kanan) P = atas, L = bawah, K = pakai skill
               ESC = pause (P dipakai Pemain 2)
    M : mute / unmute      F11 : fullscreen
    Game over: ENTER main lagi, ESC kembali ke menu

Pemenang adalah yang pertama mencapai 5 poin.

MYSTERY BOX muncul di garis vertikal tempat paddle bergerak (tiap sisi punya
timer sendiri, 8-10 detik). Sentuh dengan paddle untuk mengambil skill acak:
    1. LIGHTNING SHOT : pukulan berikutnya jadi tembakan petir super cepat
    2. ZA WARUDO      : memperlambat gerakan lawan + musik melambat & terdistorsi
    3. KAGEBUNSIN     : klon paddle yang bergerak terbalik
    4. NANO SHIELD    : 3 detik tidak bisa kebobolan
    5. FISH THROW     : lempar ikan, lawan yang kena stun 1 detik
    6. LIGHT SPEED    : speed 2x selama 8 detik + jejak cahaya
    7. BLACK HOLE     : (langka) lawan terhapus, ronde ini pasti menang

MODE 2 PEMAIN (satu keyboard, saling melawan): pilih MODE di menu. Semua skill, map,
skin, aksesoris, dan nama berlaku untuk kedua pemain.

MAP dengan event unik (pilih di menu):
    JALAN RAYA        : kendaraan melintas tiap 15 dtk, tertabrak = STUN 2,5 dtk
    GUNUNG VOLCANO    : lava menyembur tiap 10 dtk, terkena = LAMBAT 0,5x selama 4 dtk
    PASAR TRADISIONAL : barang dilempar tiap 15 dtk, terkena = TAK BISA PAKAI SKILL 8 dtk
    LAB KIMIA         : botol racikan tiap 12 dtk, terkena = PUSING (kontrol terbalik)
    MEDAN PERANG      : peluru tank tiap 15 dtk + bom kecil, terkena = BLEEDING

Pengaturan (nama, skin, map, dll) disimpan di ping_pong_settings.json.

Catatan: semua suara (SFX + BGM) dibuat otomatis lewat kode, jadi TIDAK
butuh file audio / numpy / library tambahan selain pygame.
"""

import colorsys
import io
import json
import math
import os
import random
import sys
from array import array
from collections import deque

import pygame

# Modul `wave` tidak ada di CPython WebAssembly milik Pygbag. Hanya dipakai
# untuk membangun suara sintetis di desktop (di browser audio dinonaktifkan),
# jadi import-nya dibuat opsional agar game tetap bisa di-import di browser.
try:
    import wave
except ImportError:  # pragma: no cover - hanya terjadi di runtime browser
    wave = None

# ============================================================
#  KONFIGURASI
# ============================================================
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
WIN_SCORE = 5

PADDLE_W, PADDLE_H = 20, 110
PADDLE_MARGIN = 30
BALL_SIZE = 30
BALL_R = BALL_SIZE // 2

BALL_START_SPEED = 7.5
BALL_MAX_SPEED = 16.0
BALL_SPEED_STEP = 0.5

PLAYER_MAX_SPEED = 9.0

SERVE_STEP = 50                 # frame per angka hitung mundur (3-2-1)
SERVE_FRAMES = SERVE_STEP * 3

# --- skill ---
BOX_SIZE = 48
BOX_LIFE = 720                  # 12 detik kalau tidak diambil
BOX_MIN, BOX_MAX = 480, 600     # 8 - 10 detik

LIGHTNING_SPEED = 21.0
TIME_FRAMES = 270               # 4.5 detik
TIME_SLOW = 0.40                # lawan jadi 40% kecepatan (tidak melumpuhkan total)
CLONE_FRAMES = 480              # 8 detik
SHIELD_FRAMES = 180             # 3 detik
LIGHT_FRAMES = 480              # 8 detik
LIGHT_MULT = 2.0
STUN_FRAMES = 60                # 1 detik
FISH_SPEED = 9.0
FISH_LIFE = 420
BH_THROW = 55
BH_SUCK = 100
BH_HOLD = 100
BH_MAX_R = 150.0

SKILLS = {
    "lightning": {"name": "LIGHTNING SHOT", "text": "LIGHTNING SHOT!",
                  "color": (140, 215, 255), "weight": 1.0},
    "time":      {"name": "ZA WARUDO", "text": "ZA WARUDOOO!!",
                  "color": (255, 225, 110), "weight": 1.0},
    "clone":     {"name": "KAGEBUNSIN", "text": "KAGEBUNSIN!",
                  "color": (225, 225, 240), "weight": 1.0},
    "shield":    {"name": "NANO SHIELD", "text": "NANO SHIELD!",
                  "color": (70, 170, 255), "weight": 1.0},
    "fish":      {"name": "FISH THROW", "text": "WLEEEEE!",
                  "color": (255, 150, 90), "weight": 1.0},
    "light":     {"name": "LIGHT SPEED", "text": "LIGHT SPEED!",
                  "color": (255, 235, 60), "weight": 1.0},
    "blackhole": {"name": "BLACK HOLE", "text": "BLACK HOLE!",
                  "color": (160, 60, 255), "weight": 0.1},      # langka 0.1 : 1
}
SKILL_KEYS = list(SKILLS.keys())
SKILL_WEIGHTS = [SKILLS[k]["weight"] for k in SKILL_KEYS]

# --- map & event ---
ROAD_STUN_FRAMES = 150          # tertabrak kendaraan = stun 2,5 detik
LAVA_WARN = 60                  # peringatan sebelum lava menyembur
LAVA_HOLD = 70
LAVA_SLOW_FRAMES = 240          # kena lava = lambat 4 detik
LAVA_MULT = 0.5
LOCK_FRAMES = 480               # kena lemparan pasar = tak bisa pakai skill 8 detik
DIZZY_FRAMES = 360              # kena botol kimia = kontrol terbalik 6 detik
BLEED_STUN = 90                 # bleeding: stun 1,5 detik ...
BLEED_FRAMES = 240              # ... + lambat 0,7x selama 4 detik
BLEED_MULT = 0.7
ROAD_LANES = (346, 454)
MARKET_ITEMS = ("pisang", "ayam", "sayur", "jeruk", "ikan")
ITEM_COLORS = {"pisang": (250, 215, 50), "ayam": (240, 235, 225), "sayur": (110, 190, 80),
               "jeruk": (255, 150, 30), "ikan": (150, 190, 230)}
CHEM_COLORS = {"chem0": (90, 255, 140), "chem1": (190, 90, 255), "chem2": (80, 220, 255)}

MAPS = [
    {"id": "arena", "name": "NEON ARENA", "accent": None, "interval": 0,
     "desc": "Arena klasik tanpa event - fokus ke permainan dan skill"},
    {"id": "highway", "name": "JALAN RAYA", "accent": (255, 200, 60), "interval": 15,
     "desc": "Tiap 15 dtk truk/mobil melintas di tengah - tertabrak = STUN 2,5 dtk"},
    {"id": "volcano", "name": "GUNUNG VOLCANO", "accent": (255, 120, 30), "interval": 10,
     "desc": "Tiap 10 dtk lava menyembur dari bawah - terkena = LAMBAT 0,5x selama 4 dtk"},
    {"id": "market", "name": "PASAR TRADISIONAL", "accent": (255, 170, 70), "interval": 15,
     "desc": "Tiap 15 dtk barang pasar dilempar - terkena = TAK BISA PAKAI SKILL 8 dtk"},
    {"id": "lab", "name": "LAB KIMIA", "accent": (70, 255, 170), "interval": 12,
     "desc": "Tiap 12 dtk botol racikan dilempar - terkena = PUSING (kontrol terbalik)"},
    {"id": "war", "name": "MEDAN PERANG", "accent": (210, 200, 120), "interval": 15,
     "desc": "Tiap 15 dtk peluru tank jatuh + bom kecil - terkena = BLEEDING"},
]

# Karakter: tokoh domain publik / folklor + karakter orisinal (bebas hak cipta)
CHARACTERS = [
    {"id": "wukong", "name": "WUKONG", "body": (240, 170, 40)},
    {"id": "holmes", "name": "HOLMES", "body": (160, 120, 80)},
    {"id": "dracula", "name": "DRACULA", "body": (200, 40, 70)},
    {"id": "franken", "name": "FRANKEN", "body": (110, 190, 100)},
    {"id": "alice", "name": "ALICE", "body": (90, 160, 255)},
    {"id": "zorro", "name": "ZORRO", "body": (150, 150, 175)},
    {"id": "ninja", "name": "NINJA", "body": (230, 50, 60)},
    {"id": "robot", "name": "ROBOT", "body": (80, 220, 255)},
    {"id": "pirate", "name": "PIRATE", "body": (220, 90, 50)},
    {"id": "astronaut", "name": "ASTRONAUT", "body": (225, 232, 250)},
    {"id": "wizard", "name": "WIZARD", "body": (150, 90, 230)},
    {"id": "knight", "name": "KNIGHT", "body": (185, 195, 212)},
]
HEAD_ACCS = [("none", "TANPA"), ("helm", "HELM"), ("crown", "MAHKOTA RAJA"),
             ("wizard", "TOPI SIHIR"), ("chef", "TOPI KOKI"), ("phones", "HEADSET")]
CHEST_ACCS = [("none", "TANPA"), ("jersey", "JERSEY"), ("armor", "ARMOR"),
              ("medal", "MEDALI"), ("cape", "JUBAH")]
HAND_ACCS = [("none", "TANPA"), ("shield", "TAMENG"), ("sword", "PEDANG"), ("stick", "STICK GAME"),
             ("burger", "BURGER"), ("pizza", "PIZZA"), ("trophy", "PIALA"), ("wand", "TONGKAT")]
PLAIN_LOOK = (None, "none", "none", "none")

# Kontrol (bisa diubah di sini). "skill_label" hanya teks yang tampil di layar.
CONTROLS_1P = {"up": (pygame.K_UP, pygame.K_w), "down": (pygame.K_DOWN, pygame.K_s),
               "skill": (pygame.K_SPACE,), "skill_label": "SPACE"}
CONTROLS_P1 = {"up": (pygame.K_w,), "down": (pygame.K_s,),
               "skill": (pygame.K_d,), "skill_label": "D"}
CONTROLS_P2 = {"up": (pygame.K_p,), "down": (pygame.K_l,),
               "skill": (pygame.K_k,), "skill_label": "K"}


def _settings_path():
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base = os.getcwd()
    return os.path.join(base, "ping_pong_settings.json")


SETTINGS_PATH = _settings_path()

# Level kesulitan CPU (semuanya BISA dikalahkan)
#   speed   : kecepatan maksimum paddle CPU
#   react   : jeda (frame) CPU memperbarui target -> makin besar makin telat
#   error   : seberapa meleset bidikan CPU (piksel)
#   mistake : peluang CPU salah baca bola dengan meleset jauh
DIFFICULTIES = [
    {"name": "MUDAH",  "speed": 4.6, "react": 14, "error": 70, "mistake": 0.15},
    {"name": "NORMAL", "speed": 6.2, "react": 8,  "error": 45, "mistake": 0.08},
    {"name": "SULIT",  "speed": 7.6, "react": 4,  "error": 25, "mistake": 0.03},
]

# Skin: warna paddle player, paddle CPU, gaya bola, dan tema background
SKINS = [
    {"name": "NEON", "player": (0, 225, 255), "cpu": (255, 60, 200),
     "ball": (255, 255, 255), "ball_glow": (120, 200, 255),
     "bg_top": (6, 8, 28), "bg_bottom": (24, 6, 42), "ball_style": "orb"},
    {"name": "INFERNO", "player": (255, 170, 30), "cpu": (255, 50, 50),
     "ball": (255, 240, 160), "ball_glow": (255, 120, 20),
     "bg_top": (26, 4, 4), "bg_bottom": (50, 14, 4), "ball_style": "fire"},
    {"name": "TOXIC", "player": (90, 255, 120), "cpu": (180, 90, 255),
     "ball": (230, 255, 200), "ball_glow": (120, 255, 60),
     "bg_top": (2, 18, 10), "bg_bottom": (12, 8, 32), "ball_style": "ring"},
    {"name": "GOLD", "player": (255, 215, 90), "cpu": (110, 170, 255),
     "ball": (255, 255, 255), "ball_glow": (255, 220, 120),
     "bg_top": (14, 14, 26), "bg_bottom": (34, 26, 10), "ball_style": "orb"},
]

MUSIC_LEVELS = {"menu": 0.35, "play": 0.42, "pause": 0.12, "gameover": 0.25}

WHITE = (255, 255, 255)


# ============================================================
#  FUNGSI BANTU
# ============================================================
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def scale_color(c, k):
    return (clamp(int(c[0] * k), 0, 255),
            clamp(int(c[1] * k), 0, 255),
            clamp(int(c[2] * k), 0, 255))


def hsv_color(h, s=0.6, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def clone_color(c):
    """Warna klon: satu tone dengan aslinya tapi lebih redup & sedikit pudar."""
    return scale_color(mix(c, (128, 128, 128), 0.22), 0.58)


_font_cache = {}


def get_font(size):
    size = max(8, int(size))
    f = _font_cache.get(size)
    if f is None:
        f = pygame.font.Font(None, size)
        _font_cache[size] = f
    return f


_glow_cache = {}


def _build_glow(radius, color):
    d = radius * 2
    surf = pygame.Surface((d, d))
    surf.fill((0, 0, 0))
    for r in range(radius, 0, -2):
        k = (1.0 - r / radius) ** 2
        pygame.draw.circle(surf, scale_color(color, k), (radius, radius), r)
    return surf


def get_glow(radius, color):
    """Bola cahaya (gradasi radial) untuk efek glow, dipakai dengan blend ADD."""
    key = (radius, color)
    surf = _glow_cache.get(key)
    if surf is None:
        surf = _build_glow(radius, color)
        _glow_cache[key] = surf
    return surf


def draw_glow(target, pos, radius, color, strength=1.0):
    strength = round(clamp(strength, 0.0, 1.0) * 4) / 4.0
    if strength <= 0:
        return
    radius = max(10, int(round(radius / 10.0)) * 10)
    glow = get_glow(radius, scale_color(color, strength))
    target.blit(glow, (int(pos[0]) - radius, int(pos[1]) - radius),
                special_flags=pygame.BLEND_RGB_ADD)


def draw_text(surf, text, size, color, center, glow=None, scale=1.0, alpha=255):
    font = get_font(size)
    img = font.render(text, True, color)
    if scale != 1.0:
        img = pygame.transform.rotozoom(img, 0, scale)
    rect = img.get_rect(center=(int(center[0]), int(center[1])))
    if glow is not None:
        base = font.render(text, True, glow)
        for k in (1.16, 1.08):
            g = pygame.transform.rotozoom(base, 0, scale * k)
            g.set_alpha(min(alpha, 70))
            surf.blit(g, g.get_rect(center=rect.center))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, rect)
    return rect


def make_background(skin):
    """Background HD: gradasi + nebula + grid halus + vignette (dibuat sekali)."""
    surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    for y in range(SCREEN_H):
        pygame.draw.line(surf, mix(skin["bg_top"], skin["bg_bottom"], y / SCREEN_H),
                         (0, y), (SCREEN_W, y))
    # nebula lembut
    for nx, ny, nr, ncol in ((260, 220, 300, scale_color(skin["cpu"], 0.16)),
                             (1020, 560, 300, scale_color(skin["player"], 0.16)),
                             (640, 400, 200, scale_color(mix(skin["cpu"], skin["player"], 0.5), 0.09))):
        blob = _build_glow(nr, ncol)
        surf.blit(blob, (nx - nr, ny - nr), special_flags=pygame.BLEND_RGB_ADD)
    grid = mix(skin["bg_bottom"], skin["player"], 0.10)
    for x in range(0, SCREEN_W, 80):
        pygame.draw.line(surf, grid, (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, 80):
        pygame.draw.line(surf, grid, (0, y), (SCREEN_W, y))
    vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for i in range(40):
        a = int(150 * (1 - i / 40) ** 2)
        pygame.draw.rect(vig, (0, 0, 0, a),
                         pygame.Rect(i * 4, i * 3, SCREEN_W - i * 8, SCREEN_H - i * 6), 5)
    surf.blit(vig, (0, 0))
    return surf


# ============================================================
#  SPRITE HD (digambar 4x lalu di-smoothscale -> tepi halus)
# ============================================================
_sprite_cache = {}
PAD = 10
BALL_SPR = BALL_SIZE + 24


def get_paddle_sprite(color, level=0):
    key = ("pad", color, level)
    spr = _sprite_cache.get(key)
    if spr is None:
        S = 4
        w, h = (PADDLE_W + 2 * PAD) * S, (PADDLE_H + 2 * PAD) * S
        big = pygame.Surface((w, h), pygame.SRCALPHA)
        c = mix(color, WHITE, level * 0.23)
        body = pygame.Rect(PAD * S, PAD * S, PADDLE_W * S, PADDLE_H * S)
        pygame.draw.rect(big, scale_color(c, 0.30) + (255,), body, border_radius=9 * S)
        inner = body.inflate(-6 * S, -6 * S)
        pygame.draw.rect(big, scale_color(c, 0.85) + (255,), inner, border_radius=6 * S)
        band = pygame.Rect(inner.x + 2 * S, inner.y + 6 * S, 4 * S, inner.height - 12 * S)
        pygame.draw.rect(big, mix(c, WHITE, 0.55) + (255,), band, border_radius=2 * S)
        core = pygame.Rect(inner.centerx + S, inner.y + 5 * S, 2 * S, inner.height - 10 * S)
        pygame.draw.rect(big, mix(c, WHITE, 0.85) + (255,), core, border_radius=S)
        spr = pygame.transform.smoothscale(big, (w // S, h // S))
        _sprite_cache[key] = spr
    return spr


def get_ball_sprite(skin):
    key = ("ball", skin["name"])
    spr = _sprite_cache.get(key)
    if spr is None:
        S = 4
        size = BALL_SPR * S
        c = size // 2
        R = BALL_R * S
        big = pygame.Surface((size, size), pygame.SRCALPHA)
        glow, core = skin["ball_glow"], skin["ball"]
        style = skin["ball_style"]
        if style == "fire":
            for col, rad in (((150, 30, 5), R + 2 * S), ((230, 90, 15), R - S),
                             ((255, 170, 40), R - 5 * S), (core, R - 10 * S)):
                pygame.draw.circle(big, col + (255,), (c, c), rad)
        elif style == "ring":
            pygame.draw.circle(big, scale_color(glow, 0.35) + (255,), (c, c), R)
            pygame.draw.circle(big, glow + (255,), (c, c), R, 4 * S)
            pygame.draw.circle(big, core + (255,), (c, c), R - 9 * S)
        else:
            edge = mix(glow, (0, 0, 0), 0.4)
            for i in range(R, 0, -2):
                t = i / R
                pygame.draw.circle(big, mix(core, edge, t ** 1.5) + (255,), (c, c), i)
            pygame.draw.circle(big, WHITE + (255,), (c - R // 3, c - R // 3), R // 4)
        spr = pygame.transform.smoothscale(big, (BALL_SPR, BALL_SPR))
        _sprite_cache[key] = spr
    return spr


def get_fish_sprite():
    spr = _sprite_cache.get("fish")
    if spr is None:
        S = 4
        w, h = 64 * S, 36 * S
        big = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(big, (255, 110, 40, 255),
                            [(42 * S, 18 * S), (62 * S, 4 * S), (57 * S, 18 * S), (62 * S, 32 * S)])
        pygame.draw.polygon(big, (255, 120, 50, 255),
                            [(20 * S, 8 * S), (30 * S, 0 * S), (36 * S, 9 * S)])
        pygame.draw.ellipse(big, (255, 150, 60, 255), pygame.Rect(4 * S, 6 * S, 44 * S, 24 * S))
        pygame.draw.ellipse(big, (255, 205, 130, 255), pygame.Rect(10 * S, 17 * S, 32 * S, 11 * S))
        for sx in (24, 30, 36):
            pygame.draw.line(big, (255, 95, 35, 255), (sx * S, 9 * S), (sx * S, 16 * S), S)
        pygame.draw.circle(big, WHITE + (255,), (14 * S, 15 * S), 4 * S)
        pygame.draw.circle(big, (20, 20, 30, 255), (13 * S, 15 * S), 2 * S)
        spr = pygame.transform.smoothscale(big, (w // S, h // S))
        _sprite_cache["fish"] = spr
    return spr


# ============================================================
#  KARAKTER, AKSESORIS & ITEM (digambar 4x lalu di-smoothscale)
# ============================================================
SS = 4                      # faktor supersampling
MX, MT = 50, 40             # margin komposit paddle (kiri/kanan, atas)
COMP_W, COMP_H = PADDLE_W + 2 * MX, PADDLE_H + MT + 10


class Canvas4:
    """Kanvas supersampling: semua koordinat dalam satuan 'normal'."""

    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.surf = pygame.Surface((self.w * SS, self.h * SS), pygame.SRCALPHA)

    @staticmethod
    def _col(col):
        return (int(col[0]), int(col[1]), int(col[2]), int(col[3]) if len(col) > 3 else 255)

    def circle(self, col, c, r, width=0):
        pygame.draw.circle(self.surf, self._col(col), (int(c[0] * SS), int(c[1] * SS)),
                           max(1, int(r * SS)), max(0, int(width * SS)))

    def rect(self, col, box, radius=0, width=0):
        r = pygame.Rect(int(box[0] * SS), int(box[1] * SS),
                        max(1, int(box[2] * SS)), max(1, int(box[3] * SS)))
        pygame.draw.rect(self.surf, self._col(col), r, max(0, int(width * SS)),
                         border_radius=max(0, int(radius * SS)))

    def ellipse(self, col, box, width=0):
        r = pygame.Rect(int(box[0] * SS), int(box[1] * SS),
                        max(1, int(box[2] * SS)), max(1, int(box[3] * SS)))
        pygame.draw.ellipse(self.surf, self._col(col), r, max(0, int(width * SS)))

    def poly(self, col, pts, width=0):
        pygame.draw.polygon(self.surf, self._col(col),
                            [(int(x * SS), int(y * SS)) for x, y in pts], max(0, int(width * SS)))

    def line(self, col, p1, p2, width=1):
        pygame.draw.line(self.surf, self._col(col), (int(p1[0] * SS), int(p1[1] * SS)),
                         (int(p2[0] * SS), int(p2[1] * SS)), max(1, int(width * SS)))

    def out(self):
        return pygame.transform.smoothscale(self.surf, (self.w, self.h))


def _eyes(c, cx, cy, pupil=(20, 20, 30)):
    for ex in (cx + 4, cx + 10):
        c.circle(WHITE, (ex, cy - 2), 3.2)
        c.circle(pupil, (ex + 1, cy - 2), 1.7)


def _face(c, cx, cy, tone=(255, 214, 170), r=14.0):
    c.circle(tone, (cx, cy), r)
    _eyes(c, cx, cy)
    c.line((120, 60, 50), (cx + 4, cy + 6), (cx + 10, cy + 6), 1.5)


def draw_character_head(c, cid, cx, cy):
    """Kepala karakter (menghadap kanan; di-flip untuk sisi player)."""
    if cid == "wukong":
        c.circle((200, 130, 35), (cx, cy), 15.5)
        _face(c, cx, cy + 1, (255, 205, 140), 12.5)
        c.rect((255, 215, 60), (cx - 14, cy - 9, 28, 4), radius=2)
        c.line((255, 110, 60), (cx - 3, cy - 9), (cx - 12, cy - 31), 2)
        c.line((255, 110, 60), (cx + 3, cy - 9), (cx - 1, cy - 33), 2)
        c.circle((255, 215, 60), (cx - 12, cy - 31), 2.2)
        c.circle((255, 215, 60), (cx - 1, cy - 33), 2.2)
    elif cid == "holmes":
        _face(c, cx, cy)
        c.ellipse((150, 110, 70), (cx - 15, cy - 19, 30, 15))
        c.rect((120, 85, 55), (cx - 16, cy - 9, 32, 3.5), radius=1.5)
        c.poly((120, 85, 55), [(cx + 4, cy - 10), (cx + 21, cy - 9), (cx + 16, cy - 5)])
        c.line((90, 60, 40), (cx + 8, cy + 7), (cx + 18, cy + 9), 2.5)
        c.circle((70, 45, 30), (cx + 19, cy + 6.5), 3.2)
    elif cid == "dracula":
        c.poly((170, 40, 60), [(cx - 19, cy + 2), (cx - 9, cy + 19), (cx + 9, cy + 19),
                               (cx + 19, cy + 2), (cx + 12, cy + 12), (cx - 12, cy + 12)])
        _face(c, cx, cy, (226, 226, 240))
        c.poly((20, 20, 30), [(cx - 14, cy - 2), (cx - 13, cy - 14), (cx, cy - 17), (cx + 13, cy - 14),
                              (cx + 14, cy - 2), (cx + 6, cy - 9), (cx + 1, cy - 4), (cx - 6, cy - 9)])
        c.circle((225, 40, 40), (cx + 5, cy - 2), 1.7)
        c.circle((225, 40, 40), (cx + 11, cy - 2), 1.7)
        c.poly(WHITE, [(cx + 4, cy + 6), (cx + 6.5, cy + 6), (cx + 5, cy + 10.5)])
        c.poly(WHITE, [(cx + 8.5, cy + 6), (cx + 11, cy + 6), (cx + 10, cy + 10.5)])
    elif cid == "franken":
        _face(c, cx, cy, (150, 205, 120))
        c.rect((40, 40, 50), (cx - 14, cy - 17, 28, 9), radius=2)
        c.rect((130, 130, 145), (cx - 19, cy - 3, 6, 4), radius=1)
        c.rect((130, 130, 145), (cx + 13, cy - 3, 6, 4), radius=1)
        c.line((60, 90, 50), (cx - 8, cy - 8), (cx + 9, cy - 8), 1.5)
        for sx in (-5, 0, 5):
            c.line((60, 90, 50), (cx + sx, cy - 10), (cx + sx, cy - 6), 1)
        c.line((60, 90, 50), (cx + 2, cy - 5), (cx + 13, cy - 5), 2)
    elif cid == "alice":
        c.circle((250, 215, 90), (cx - 2, cy + 1), 16)
        _face(c, cx, cy)
        c.poly((250, 215, 90), [(cx - 13, cy - 1), (cx - 12, cy - 12), (cx, cy - 15), (cx + 10, cy - 9),
                                (cx + 2, cy - 7), (cx - 6, cy - 4)])
        c.poly((90, 160, 255), [(cx - 2, cy - 15), (cx - 12, cy - 22), (cx - 12, cy - 9)])
        c.poly((90, 160, 255), [(cx - 2, cy - 15), (cx + 8, cy - 22), (cx + 8, cy - 9)])
        c.circle((60, 120, 220), (cx - 2, cy - 15), 2.5)
    elif cid == "zorro":
        _face(c, cx, cy)
        c.rect((15, 15, 20), (cx - 13, cy - 6, 28, 8), radius=3)
        _eyes(c, cx, cy)
        c.line((30, 20, 20), (cx + 4, cy + 4), (cx + 12, cy + 4), 1.5)
        c.ellipse((20, 20, 25), (cx - 20, cy - 15, 40, 7))
        c.ellipse((20, 20, 25), (cx - 11, cy - 27, 22, 16))
    elif cid == "ninja":
        c.circle((35, 35, 45), (cx, cy), 15)
        c.rect((255, 214, 170), (cx - 12, cy - 6, 26, 9), radius=3)
        _eyes(c, cx, cy)
        c.rect((200, 30, 40), (cx - 15, cy - 12, 30, 4))
        c.poly((200, 30, 40), [(cx - 15, cy - 11), (cx - 31, cy - 5), (cx - 27, cy - 13)])
        c.poly((200, 30, 40), [(cx - 15, cy - 9), (cx - 29, cy + 3), (cx - 31, cy - 5)])
    elif cid == "robot":
        c.line((150, 160, 175), (cx, cy - 13), (cx, cy - 22), 2)
        c.circle((235, 60, 60), (cx, cy - 23), 2.8)
        c.rect((165, 175, 190), (cx - 14, cy - 13, 28, 26), radius=5)
        c.rect((105, 115, 135), (cx - 14, cy - 13, 28, 26), radius=5, width=1.5)
        c.rect((25, 35, 50), (cx - 10, cy - 8, 26, 10), radius=3)
        c.circle((80, 230, 255), (cx + 4, cy - 3), 2.6)
        c.circle((80, 230, 255), (cx + 11, cy - 3), 2.6)
        for k in range(3):
            c.line((105, 115, 135), (cx - 2 + k * 5, cy + 6), (cx - 2 + k * 5, cy + 10), 1.2)
    elif cid == "pirate":
        _face(c, cx, cy, (240, 190, 140))
        c.circle((15, 15, 20), (cx + 10, cy - 2), 3.8)
        c.line((15, 15, 20), (cx - 13, cy - 8), (cx + 12, cy), 1.2)
        c.poly((200, 40, 40), [(cx - 15, cy - 3), (cx - 13, cy - 14), (cx, cy - 19), (cx + 13, cy - 14),
                               (cx + 15, cy - 3), (cx, cy - 9)])
        c.poly((200, 40, 40), [(cx - 14, cy - 8), (cx - 28, cy - 4), (cx - 25, cy - 12)])
        for dx, dy in ((-7, -12), (0, -15), (7, -12)):
            c.circle(WHITE, (cx + dx, cy + dy), 1.4)
    elif cid == "astronaut":
        c.circle((235, 238, 248), (cx, cy), 16)
        c.ellipse((30, 45, 95), (cx - 8, cy - 10, 24, 20))
        c.ellipse((120, 170, 255), (cx + 1, cy - 8, 11, 5))
        c.circle((235, 70, 60), (cx - 11, cy + 8), 2)
    elif cid == "wizard":
        _face(c, cx, cy)
        c.poly((240, 240, 245), [(cx - 11, cy + 3), (cx + 13, cy + 3), (cx + 5, cy + 22), (cx - 3, cy + 17)])
        c.poly((90, 60, 170), [(cx - 16, cy - 8), (cx + 16, cy - 8), (cx + 2, cy - 38)])
        c.ellipse((70, 45, 140), (cx - 20, cy - 12, 40, 8))
        c.circle((255, 230, 90), (cx + 1, cy - 20), 2.6)
    elif cid == "knight":
        c.circle((175, 185, 200), (cx, cy), 15.5)
        c.rect((30, 30, 40), (cx - 1, cy - 4, 16, 5), radius=1.5)
        c.line((120, 130, 145), (cx + 7, cy - 14), (cx + 7, cy + 13), 1.2)
        c.poly((210, 40, 50), [(cx - 6, cy - 14), (cx - 22, cy - 26), (cx - 18, cy - 12), (cx + 4, cy - 18)])
        c.circle((120, 130, 145), (cx - 8, cy + 4), 1.5)


def _arc_pts(cx, cy, r, n=12):
    return [(cx + r * math.cos(math.pi + i * math.pi / n), cy + r * math.sin(math.pi + i * math.pi / n))
            for i in range(n + 1)]


def draw_head_acc(c, kind, hx, hy):
    if kind == "helm":
        pts = _arc_pts(hx, hy - 2, 17)
        c.poly((150, 160, 178), pts)
        c.poly((205, 215, 230), pts, width=1.2)
        c.rect((205, 215, 230), (hx - 17, hy - 4, 34, 3), radius=1)
        c.rect((150, 160, 178), (hx + 9, hy - 3, 5, 9), radius=1)
        c.rect((200, 60, 60), (hx - 1, hy - 19, 2.5, 8))
    elif kind == "crown":
        c.poly((255, 205, 40), [(hx - 12, hy - 20), (hx - 12, hy - 32), (hx - 6, hy - 25), (hx, hy - 35),
                                (hx + 6, hy - 25), (hx + 12, hy - 32), (hx + 12, hy - 20)])
        c.rect((240, 175, 30), (hx - 12, hy - 22, 24, 5), radius=1)
        c.circle((225, 50, 70), (hx, hy - 19.5), 1.8)
        c.circle((60, 130, 255), (hx - 7, hy - 19.5), 1.6)
        c.circle((60, 130, 255), (hx + 7, hy - 19.5), 1.6)
        for px, py in ((-12, -32), (0, -35), (12, -32)):
            c.circle((255, 245, 200), (hx + px, hy + py), 2)
    elif kind == "wizard":
        c.poly((60, 90, 200), [(hx - 14, hy - 12), (hx + 14, hy - 12), (hx + 1, hy - 40)])
        c.ellipse((45, 70, 170), (hx - 19, hy - 16, 38, 8))
        c.circle((255, 230, 90), (hx + 1, hy - 24), 2.4)
    elif kind == "chef":
        for ox, oy, r in ((-8, -24, 7), (0, -28, 8), (8, -24, 7)):
            c.circle((250, 250, 250), (hx + ox, hy + oy), r)
        c.rect((250, 250, 250), (hx - 12, hy - 22, 24, 9), radius=2)
        c.rect((205, 205, 218), (hx - 12, hy - 15, 24, 2.5))
    elif kind == "phones":
        pts = _arc_pts(hx, hy - 1, 16)
        for i in range(len(pts) - 1):
            c.line((50, 50, 72), pts[i], pts[i + 1], 3)
        c.rect((60, 60, 92), (hx - 20, hy - 6, 7, 13), radius=3)
        c.rect((60, 60, 92), (hx + 13, hy - 6, 7, 13), radius=3)
        c.rect((0, 230, 255), (hx - 18, hy - 3, 3, 7), radius=1)
        c.rect((0, 230, 255), (hx + 15, hy - 3, 3, 7), radius=1)


def draw_chest_acc(c, kind, cx, cy, back=False):
    if kind == "cape":
        if back:
            c.poly((200, 30, 50), [(cx - 6, cy - 22), (cx - 34, cy + 48), (cx - 8, cy + 40), (cx + 6, cy - 14)])
            c.poly((140, 20, 40), [(cx - 6, cy - 22), (cx - 34, cy + 48), (cx - 22, cy + 44), (cx - 4, cy - 18)])
        return
    if back:
        return
    if kind == "jersey":
        c.poly((220, 50, 50), [(cx - 16, cy - 16), (cx - 8, cy - 20), (cx + 8, cy - 20), (cx + 16, cy - 16),
                               (cx + 16, cy - 4), (cx + 11, cy - 2), (cx + 11, cy + 18), (cx - 11, cy + 18),
                               (cx - 11, cy - 2), (cx - 16, cy - 4)])
        c.rect(WHITE, (cx - 11, cy - 6, 22, 3))
        c.rect(WHITE, (cx - 11, cy, 22, 3))
        c.circle(WHITE, (cx, cy + 12), 3.5)
        c.poly((250, 210, 50), [(cx - 5, cy - 20), (cx, cy - 15), (cx + 5, cy - 20)])
    elif kind == "armor":
        c.rect((165, 175, 192), (cx - 13, cy - 17, 26, 36), radius=7)
        c.rect((215, 225, 240), (cx - 13, cy - 17, 26, 36), radius=7, width=1.5)
        c.line((110, 120, 140), (cx, cy - 15), (cx, cy + 17), 1.5)
        c.line((110, 120, 140), (cx - 11, cy + 1), (cx + 11, cy + 1), 1.5)
        for px, py in ((-8, -12), (8, -12), (-8, 12), (8, 12)):
            c.circle((235, 240, 250), (cx + px, cy + py), 1.4)
    elif kind == "medal":
        c.poly((60, 90, 220), [(cx - 9, cy - 20), (cx - 3, cy - 20), (cx + 4, cy - 2), (cx - 2, cy - 2)])
        c.poly((220, 50, 50), [(cx + 9, cy - 20), (cx + 3, cy - 20), (cx - 4, cy - 2), (cx + 2, cy - 2)])
        c.circle((255, 205, 40), (cx, cy + 4), 8)
        c.circle((200, 150, 20), (cx, cy + 4), 8, width=1.5)
        c.circle((255, 240, 150), (cx - 2, cy + 2), 2)


def draw_hand_acc(c, kind, fx, fy):
    if kind == "shield":
        pts = [(fx, fy - 20), (fx + 24, fy - 16), (fx + 22, fy + 6), (fx + 11, fy + 24), (fx + 1, fy + 8)]
        c.poly((70, 110, 200), pts)
        c.poly((240, 200, 60), pts, width=2)
        c.line((240, 200, 60), (fx + 12, fy - 18), (fx + 12, fy + 20), 2)
        c.line((240, 200, 60), (fx + 2, fy - 4), (fx + 22, fy - 4), 2)
    elif kind == "sword":
        c.poly((220, 228, 240), [(fx + 6, fy + 18), (fx + 6, fy - 34), (fx + 10, fy - 42),
                                 (fx + 14, fy - 34), (fx + 14, fy + 18)])
        c.line((160, 170, 190), (fx + 10, fy - 36), (fx + 10, fy + 16), 1.2)
        c.rect((240, 190, 40), (fx, fy + 16, 20, 5), radius=2)
        c.rect((120, 70, 40), (fx + 8, fy + 21, 4, 12), radius=1)
        c.circle((240, 190, 40), (fx + 10, fy + 35), 3)
    elif kind == "stick":
        c.rect((50, 50, 66), (fx + 1, fy + 4, 24, 14), radius=4)
        c.line((150, 155, 170), (fx + 10, fy + 5), (fx + 10, fy - 12), 3.5)
        c.circle((235, 60, 70), (fx + 10, fy - 14), 6)
        c.circle((90, 220, 120), (fx + 18, fy + 10), 2.5)
        c.circle((250, 210, 70), (fx + 22, fy + 8), 2.5)
    elif kind == "burger":
        c.ellipse((225, 165, 80), (fx, fy - 14, 28, 15))
        c.rect((90, 190, 70), (fx - 1, fy, 30, 4), radius=2)
        c.rect((240, 200, 60), (fx + 2, fy + 3, 24, 2))
        c.rect((110, 60, 40), (fx, fy + 5, 28, 6), radius=3)
        c.ellipse((225, 165, 80), (fx, fy + 10, 28, 9))
        for sx in (6, 13, 20):
            c.circle((250, 235, 190), (fx + sx, fy - 8), 1)
    elif kind == "pizza":
        c.poly((250, 200, 80), [(fx + 14, fy + 26), (fx, fy - 12), (fx + 28, fy - 12)])
        c.poly((205, 130, 50), [(fx, fy - 12), (fx + 28, fy - 12), (fx + 27, fy - 17), (fx + 1, fy - 17)])
        for px, py, r in ((9, -6, 3), (19, -5, 3), (14, 6, 3), (14, -1, 2)):
            c.circle((200, 50, 50), (fx + px, fy + py), r)
    elif kind == "trophy":
        c.poly((255, 205, 40), [(fx + 2, fy - 18), (fx + 24, fy - 18), (fx + 20, fy - 2),
                                (fx + 14, fy + 2), (fx + 12, fy + 2), (fx + 6, fy - 2)])
        c.circle((255, 205, 40), (fx + 1, fy - 12), 5, width=2)
        c.circle((255, 205, 40), (fx + 25, fy - 12), 5, width=2)
        c.rect((240, 175, 30), (fx + 11, fy + 2, 4, 10))
        c.rect((200, 140, 30), (fx + 5, fy + 12, 16, 5), radius=1.5)
        c.line((255, 245, 190), (fx + 7, fy - 15), (fx + 8, fy - 6), 1.5)
    elif kind == "wand":
        c.line((120, 80, 50), (fx + 4, fy + 24), (fx + 22, fy - 14), 3.5)
        c.circle((255, 230, 90), (fx + 23, fy - 16), 4.5)
        for k in range(8):
            a = k * math.pi / 4
            c.line((255, 245, 170), (fx + 23 + math.cos(a) * 5, fy - 16 + math.sin(a) * 5),
                   (fx + 23 + math.cos(a) * 9, fy - 16 + math.sin(a) * 9), 1.2)


def _draw_paddle_body(c, ox, oy, color):
    c.rect(scale_color(color, 0.30), (ox, oy, PADDLE_W, PADDLE_H), radius=9)
    c.rect(scale_color(color, 0.85), (ox + 3, oy + 3, PADDLE_W - 6, PADDLE_H - 6), radius=6)
    c.rect(mix(color, WHITE, 0.55), (ox + 5, oy + 9, 4, PADDLE_H - 18), radius=2)
    c.rect(mix(color, WHITE, 0.85), (ox + PADDLE_W / 2 + 1, oy + 8, 2, PADDLE_H - 16), radius=1)


def build_composite(look, color):
    """Paddle + kepala karakter + aksesoris (kepala/dada/tangan), menghadap kanan."""
    cid, head, chest, hand = look
    c = Canvas4(COMP_W, COMP_H)
    hx, hy = MX + PADDLE_W / 2, MT + 16
    chest_y = MT + PADDLE_H / 2 + 4
    draw_chest_acc(c, chest, hx, chest_y, back=True)
    _draw_paddle_body(c, MX, MT, color)
    if chest != "none":
        draw_chest_acc(c, chest, hx, chest_y, back=False)
    if cid is not None:
        draw_character_head(c, cid, hx, hy)
    if head != "none":
        draw_head_acc(c, head, hx, hy)
    if hand != "none":
        draw_hand_acc(c, hand, MX + PADDLE_W + 2, MT + PADDLE_H / 2 + 6)
    return c.out()


_comp_cache = {}


def get_paddle_composite(look, color, flip, variant=0):
    """variant: 0 normal, 1 meredup (debuff), 2 klon."""
    key = (look, color, flip, variant)
    spr = _comp_cache.get(key)
    if spr is None:
        raw_key = (look, color, "raw")
        raw = _comp_cache.get(raw_key)
        if raw is None:
            raw = build_composite(look, color)
            _comp_cache[raw_key] = raw
        spr = pygame.transform.flip(raw, True, False) if flip else raw
        if variant:
            spr = spr.copy()
            if variant == 1:
                spr.fill((150, 160, 190), special_flags=pygame.BLEND_RGB_MULT)
            else:
                spr.fill((140, 140, 150), special_flags=pygame.BLEND_RGB_MULT)
                spr.set_alpha(200)
        _comp_cache[key] = spr
    return spr


def get_item_sprite(kind):
    """Sprite barang lemparan (pasar tradisional) & botol kimia."""
    spr = _sprite_cache.get(("item", kind))
    if spr is not None:
        return spr
    c = Canvas4(48, 48)
    if kind == "pisang":
        angs = [0.25 * math.pi + i * 0.5 * math.pi / 10 for i in range(11)]
        outer = [(24 + 20 * math.cos(a), 10 + 20 * math.sin(a)) for a in angs]
        inner = [(24 + 13 * math.cos(a), 6 + 13 * math.sin(a)) for a in reversed(angs)]
        c.poly((250, 215, 50), outer + inner)
        c.circle((90, 60, 20), outer[0], 2.5)
        c.circle((90, 60, 20), outer[-1], 2.5)
    elif kind == "ayam":
        c.poly((250, 245, 235), [(8, 28), (0, 18), (4, 36)])
        c.ellipse((250, 245, 235), (6, 18, 32, 22))
        c.ellipse((225, 215, 200), (12, 24, 16, 10))
        c.circle((250, 245, 235), (36, 16), 7)
        c.poly((255, 160, 40), [(41, 14), (47, 17), (41, 20)])
        for kx in (33, 37):
            c.circle((225, 50, 50), (kx, 8), 3)
        c.circle((20, 20, 30), (38, 15), 1.5)
        c.line((255, 160, 40), (20, 40), (18, 47), 2)
        c.line((255, 160, 40), (28, 40), (28, 47), 2)
    elif kind == "sayur":
        c.circle((110, 190, 80), (24, 25), 18)
        c.circle((150, 215, 110), (24, 25), 12)
        c.circle((70, 140, 50), (24, 25), 18, width=1.5)
        c.circle((70, 140, 50), (24, 25), 7, width=1.5)
        c.line((70, 140, 50), (24, 8), (24, 42), 1.5)
        c.line((70, 140, 50), (8, 25), (40, 25), 1.5)
    elif kind == "jeruk":
        c.circle((255, 150, 30), (24, 27), 17)
        c.circle((255, 190, 90), (18, 21), 5)
        c.poly((70, 160, 60), [(24, 11), (34, 5), (32, 14)])
        c.line((110, 70, 30), (24, 12), (24, 8), 2)
    elif kind == "ikan":
        c.poly((120, 160, 205), [(36, 24), (47, 13), (47, 35)])
        c.ellipse((150, 190, 230), (4, 14, 36, 20))
        c.ellipse((200, 225, 245), (8, 24, 26, 8))
        c.circle(WHITE, (13, 22), 3)
        c.circle((20, 20, 30), (12, 22), 1.5)
        for sx in (20, 26, 32):
            c.line((110, 150, 195), (sx, 17), (sx, 30), 1.2)
    else:   # botol kimia
        col = CHEM_COLORS.get(kind, (90, 255, 140))
        c.rect((170, 210, 215), (20, 4, 8, 16))
        c.rect((130, 90, 50), (19, 1, 10, 5), radius=1)
        c.circle((170, 210, 215), (24, 31), 15)
        c.circle(col, (24, 33), 12)
        c.circle(WHITE, (19, 28), 3)
        c.circle((170, 210, 215), (24, 31), 15, width=1.5)
    spr = c.out()
    _sprite_cache[("item", kind)] = spr
    return spr


# ============================================================
#  BACKGROUND MAP
# ============================================================
def _gradient(surf, top, bottom, y0, y1):
    n = max(1, y1 - y0)
    for y in range(y0, y1):
        pygame.draw.line(surf, mix(top, bottom, (y - y0) / n), (0, y), (SCREEN_W, y))


def _vignette(surf, strength=150):
    vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for i in range(40):
        a = int(strength * (1 - i / 40) ** 2)
        pygame.draw.rect(vig, (0, 0, 0, a),
                         pygame.Rect(i * 4, i * 3, SCREEN_W - i * 8, SCREEN_H - i * 6), 5)
    surf.blit(vig, (0, 0))


def _add_glow(surf, x, y, r, color):
    surf.blit(get_glow(r, color), (int(x) - r, int(y) - r), special_flags=pygame.BLEND_RGB_ADD)


def build_bg_highway():
    rng = random.Random(7)
    surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    _gradient(surf, (8, 10, 34), (40, 22, 62), 0, 292)
    _gradient(surf, (26, 24, 40), (12, 12, 22), 292, SCREEN_H)
    x = 0
    while x < SCREEN_W:
        w = rng.randint(60, 130)
        h = rng.randint(70, 210)
        pygame.draw.rect(surf, (14, 16, 34), (x, 262 - h, w, h))
        for wy in range(262 - h + 10, 250, 18):
            for wx in range(x + 8, x + w - 10, 16):
                if rng.random() < 0.38:
                    pygame.draw.rect(surf, (255, 214, 120), (wx, wy, 7, 9))
        x += w + rng.randint(0, 14)
    pygame.draw.rect(surf, (62, 64, 80), (0, 262, SCREEN_W, 30))
    pygame.draw.rect(surf, (96, 98, 118), (0, 288, SCREEN_W, 4))
    pygame.draw.rect(surf, (36, 38, 48), (0, 292, SCREEN_W, 216))
    for xx in range(0, SCREEN_W, 100):
        pygame.draw.rect(surf, (230, 230, 235), (xx, 396, 56, 8))
    pygame.draw.rect(surf, (230, 190, 40), (0, 296, SCREEN_W, 3))
    pygame.draw.rect(surf, (230, 190, 40), (0, 501, SCREEN_W, 3))
    pygame.draw.rect(surf, (96, 98, 118), (0, 508, SCREEN_W, 4))
    pygame.draw.rect(surf, (62, 64, 80), (0, 512, SCREEN_W, 30))
    for lx in range(160, SCREEN_W, 320):
        pygame.draw.rect(surf, (50, 52, 66), (lx - 3, 200, 6, 62))
        pygame.draw.rect(surf, (50, 52, 66), (lx - 3, 200, 28, 5))
        _add_glow(surf, lx + 20, 206, 70, (90, 70, 30))
        _add_glow(surf, lx, 400, 90, (50, 42, 18))
    for _ in range(30):
        _add_glow(surf, rng.randint(0, SCREEN_W), rng.randint(560, 790), 40,
                  rng.choice(((40, 20, 60), (60, 40, 20), (20, 40, 60))))
    _vignette(surf)
    return surf


def build_bg_volcano():
    rng = random.Random(11)
    surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    _gradient(surf, (22, 4, 8), (120, 34, 10), 0, SCREEN_H)
    _add_glow(surf, 640, 250, 300, (110, 30, 10))
    pygame.draw.polygon(surf, (24, 12, 14), [(-50, 800), (200, 430), (330, 520), (470, 360), (600, 800)])
    pygame.draw.polygon(surf, (24, 12, 14), [(700, 800), (860, 400), (1000, 480), (1120, 380), (1330, 800)])
    pygame.draw.polygon(surf, (32, 14, 16), [(260, 800), (560, 250), (610, 220), (690, 220), (740, 250), (1030, 800)])
    pygame.draw.ellipse(surf, (255, 150, 40), (600, 212, 100, 16))
    for sx, ex in ((630, 520), (650, 600), (670, 780), (660, 880)):
        pts = [(sx, 224)]
        x, y = float(sx), 224
        while y < 640:
            y += rng.randint(30, 60)
            x += (ex - sx) * 0.12 + rng.randint(-12, 12)
            pts.append((int(x), y))
        pygame.draw.lines(surf, (255, 120, 30), False, pts, 5)
        pygame.draw.lines(surf, (255, 200, 80), False, pts, 2)
    _add_glow(surf, 650, 215, 160, (200, 80, 20))
    pygame.draw.rect(surf, (28, 12, 10), (0, 700, SCREEN_W, 100))
    for _ in range(26):
        x, y = rng.randint(0, SCREEN_W), rng.randint(710, 790)
        pts = [(x, y)]
        for _k in range(4):
            x += rng.randint(-40, 40)
            y += rng.randint(-14, 14)
            pts.append((x, y))
        pygame.draw.lines(surf, (255, 110, 30), False, pts, 2)
    _add_glow(surf, 640, 800, 380, (140, 40, 10))
    _vignette(surf, 170)
    return surf


def build_bg_market():
    rng = random.Random(5)
    surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    _gradient(surf, (40, 20, 44), (104, 56, 38), 0, SCREEN_H)
    pygame.draw.rect(surf, (66, 38, 40), (0, 0, SCREEN_W, 252))
    for y in range(0, 252, 24):
        pygame.draw.line(surf, (54, 30, 32), (0, y), (SCREEN_W, y))
    cols = ((220, 60, 60), (240, 200, 80), (60, 160, 90), (70, 120, 210), (230, 130, 50))
    fruit = ((230, 60, 60), (250, 210, 50), (120, 200, 70), (255, 150, 30), (170, 70, 170))
    for i, x in enumerate(range(0, SCREEN_W, 170)):
        c1 = cols[i % len(cols)]
        for k in range(5):
            col = c1 if k % 2 == 0 else (240, 232, 215)
            pygame.draw.polygon(surf, col, [(x + k * 34, 100), (x + (k + 1) * 34, 100),
                                            (x + (k + 1) * 34 + 4, 158), (x + k * 34 + 4, 158)])
            pygame.draw.circle(surf, col, (x + k * 34 + 21, 158), 17)
        pygame.draw.rect(surf, (88, 54, 34), (x + 6, 158, 6, 94))
        pygame.draw.rect(surf, (88, 54, 34), (x + 158, 158, 6, 94))
        pygame.draw.rect(surf, (112, 72, 42), (x + 10, 226, 150, 26), border_radius=4)
        for k in range(7):
            pygame.draw.circle(surf, rng.choice(fruit), (x + 22 + k * 21, 222 + rng.randint(-3, 3)), 10)
    pts = [(xx, 58 + int(22 * math.sin(xx * 0.012))) for xx in range(0, SCREEN_W + 1, 20)]
    pygame.draw.lines(surf, (30, 20, 20), False, pts, 2)
    for xx in range(30, SCREEN_W, 70):
        yy = 58 + int(22 * math.sin(xx * 0.012))
        pygame.draw.circle(surf, (255, 232, 150), (xx, yy + 6), 5)
        _add_glow(surf, xx, yy + 8, 40, (110, 80, 28))
    _gradient(surf, (112, 80, 54), (80, 54, 38), 262, SCREEN_H)
    for y in range(262, SCREEN_H, 64):
        pygame.draw.line(surf, (70, 48, 34), (0, y), (SCREEN_W, y))
    for r, y in enumerate(range(262, SCREEN_H, 64)):
        for x in range((r % 2) * 40, SCREEN_W, 80):
            pygame.draw.line(surf, (70, 48, 34), (x, y), (x, y + 64))
    _vignette(surf)
    return surf


def build_bg_lab():
    rng = random.Random(3)
    surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    _gradient(surf, (6, 24, 30), (12, 46, 50), 0, SCREEN_H)
    for x in range(0, SCREEN_W, 80):
        pygame.draw.line(surf, (22, 62, 66), (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, 80):
        pygame.draw.line(surf, (22, 62, 66), (0, y), (SCREEN_W, y))
    liquids = ((90, 255, 140), (190, 90, 255), (80, 220, 255), (255, 200, 60), (255, 90, 120))
    for i in range(4):
        x0 = 70 + i * 300
        pygame.draw.rect(surf, (70, 100, 106), (x0, 150, 240, 8))
        pygame.draw.rect(surf, (40, 60, 64), (x0 + 10, 158, 6, 40))
        pygame.draw.rect(surf, (40, 60, 64), (x0 + 224, 158, 6, 40))
        for k in range(4):
            bx = x0 + 32 + k * 58
            col = liquids[(i + k) % len(liquids)]
            pygame.draw.rect(surf, (150, 190, 196), (bx - 5, 104, 10, 22))
            pygame.draw.circle(surf, (150, 190, 196), (bx, 138), 18, 2)
            pygame.draw.circle(surf, scale_color(col, 0.55), (bx, 140), 14)
            _add_glow(surf, bx, 140, 40, scale_color(col, 0.35))
    for tx in (170, 1110):
        pygame.draw.rect(surf, (20, 70, 66), (tx - 22, 260, 44, 360), border_radius=20)
        pygame.draw.rect(surf, (120, 200, 200), (tx - 22, 260, 44, 360), 3, border_radius=20)
        pygame.draw.rect(surf, (40, 200, 120), (tx - 18, 400, 36, 216), border_radius=16)
        _add_glow(surf, tx, 500, 110, (20, 90, 50))
    for mx in (520, 700):
        pygame.draw.rect(surf, (10, 20, 24), (mx, 30, 130, 70), border_radius=6)
        pygame.draw.rect(surf, (90, 140, 150), (mx, 30, 130, 70), 3, border_radius=6)
        pts = [(mx + 8 + i * 12, 70 + rng.randint(-18, 18)) for i in range(10)]
        pygame.draw.lines(surf, (80, 255, 160), False, pts, 2)
    pygame.draw.rect(surf, (20, 22, 24), (0, 772, SCREEN_W, 28))
    for x in range(-40, SCREEN_W, 60):
        pygame.draw.polygon(surf, (230, 200, 30), [(x, 772), (x + 30, 772), (x + 60, 800), (x + 30, 800)])
    _add_glow(surf, 640, 420, 360, (10, 50, 40))
    _vignette(surf)
    return surf


def build_bg_war():
    rng = random.Random(9)
    surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    _gradient(surf, (34, 30, 36), (92, 62, 42), 0, 620)
    x = 0
    while x < SCREEN_W:
        w = rng.randint(50, 120)
        h = rng.randint(80, 260)
        base = 620
        pts = [(x, base), (x, base - h), (x + w * 0.3, base - h + rng.randint(0, 40)),
               (x + w * 0.6, base - h - rng.randint(0, 20)), (x + w, base - h + rng.randint(10, 60)),
               (x + w, base)]
        pygame.draw.polygon(surf, (22, 18, 24), [(int(a), int(b)) for a, b in pts])
        for _ in range(3):
            if rng.random() < 0.5:
                pygame.draw.rect(surf, (255, 150, 60),
                                 (x + rng.randint(6, max(7, w - 14)), base - rng.randint(20, h - 10), 6, 8))
        x += w
    for fxp in (180, 520, 900, 1130):
        _add_glow(surf, fxp, 470, 100, (170, 70, 20))
        pygame.draw.polygon(surf, (255, 140, 40), [(fxp - 10, 520), (fxp + 10, 520), (fxp + 2, 470)])
        pygame.draw.polygon(surf, (255, 210, 90), [(fxp - 4, 520), (fxp + 4, 520), (fxp, 495)])
    _gradient(surf, (74, 54, 38), (44, 32, 24), 620, SCREEN_H)
    for _ in range(8):
        cx, cy = rng.randint(80, 1200), rng.randint(650, 780)
        pygame.draw.ellipse(surf, (34, 24, 18), (cx - 60, cy - 14, 120, 28))
    for sx in (0, SCREEN_W - 150):
        for row in range(3):
            for k in range(3 - row):
                pygame.draw.rect(surf, (150, 130, 88), (sx + k * 50 + row * 25, 700 - row * 26, 48, 24),
                                 border_radius=10)
    pts = [(i, 690 + (14 if (i // 22) % 2 == 0 else -14)) for i in range(0, SCREEN_W + 1, 22)]
    pygame.draw.lines(surf, (130, 130, 140), False, pts, 2)
    _vignette(surf, 170)
    return surf


MAP_BUILDERS = {"highway": build_bg_highway, "volcano": build_bg_volcano, "market": build_bg_market,
                "lab": build_bg_lab, "war": build_bg_war}


# ============================================================
#  PETIR & IKON SKILL
# ============================================================
def bolt_points(x1, y1, x2, y2, segments=7, jitter=18):
    pts = [(x1, y1)]
    dx = (x2 - x1) / segments
    dy = (y2 - y1) / segments
    for i in range(1, segments):
        pts.append((x1 + dx * i + random.uniform(-jitter, jitter),
                    y1 + dy * i + random.uniform(-jitter, jitter)))
    pts.append((x2, y2))
    return pts


def draw_bolt(surf, pts, color, width=3):
    ip = [(int(x), int(y)) for x, y in pts]
    pygame.draw.lines(surf, scale_color(color, 0.45), False, ip, width + 5)
    pygame.draw.lines(surf, color, False, ip, width)
    pygame.draw.lines(surf, WHITE, False, ip, max(1, width - 2))


def draw_skill_icon(surf, kind, cx, cy, size, color):
    s = size / 2.0

    def P(x, y):
        return (int(cx + x * s), int(cy + y * s))

    icx, icy = int(cx), int(cy)
    if kind == "lightning":
        pts = [P(0.15, -1.0), P(-0.55, 0.1), P(-0.05, 0.1), P(-0.25, 1.0), P(0.6, -0.25), P(0.1, -0.25)]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, WHITE, pts, 2)
    elif kind == "time":
        pygame.draw.circle(surf, color, (icx, icy), max(2, int(s)), 3)
        pygame.draw.line(surf, color, P(0, 0), P(0, -0.65), 3)
        pygame.draw.line(surf, color, P(0, 0), P(0.45, 0.2), 3)
        for i in range(12):
            a = i * math.pi / 6
            pygame.draw.line(surf, color, P(math.sin(a) * 0.8, -math.cos(a) * 0.8),
                             P(math.sin(a) * 0.95, -math.cos(a) * 0.95), 2)
    elif kind == "clone":
        for dx, col in ((-0.35, scale_color(color, 0.55)), (0.35, color)):
            r = pygame.Rect(0, 0, max(2, int(s * 0.5)), max(2, int(s * 1.6)))
            r.center = (int(cx + dx * s), icy)
            pygame.draw.rect(surf, col, r, border_radius=4)
    elif kind == "shield":
        pts = [P(0, -1.0), P(0.85, -0.65), P(0.7, 0.3), P(0, 1.0), P(-0.7, 0.3), P(-0.85, -0.65)]
        pygame.draw.polygon(surf, scale_color(color, 0.45), pts)
        pygame.draw.polygon(surf, color, pts, 3)
        pygame.draw.line(surf, WHITE, P(0, -0.55), P(0, 0.55), 2)
    elif kind == "fish":
        body = pygame.Rect(0, 0, max(2, int(s * 1.4)), max(2, int(s * 0.9)))
        body.center = P(-0.1, 0)
        pygame.draw.ellipse(surf, color, body)
        pygame.draw.polygon(surf, scale_color(color, 0.8), [P(0.5, 0), P(1.0, -0.45), P(1.0, 0.45)])
        pygame.draw.circle(surf, (20, 20, 30), P(-0.5, -0.1), 2)
    elif kind == "light":
        pygame.draw.circle(surf, color, (icx, icy), max(2, int(s * 0.45)))
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surf, color, P(math.cos(a) * 0.65, math.sin(a) * 0.65),
                             P(math.cos(a) * 1.0, math.sin(a) * 1.0), 3)
    elif kind == "blackhole":
        pygame.draw.circle(surf, (8, 0, 18), (icx, icy), max(2, int(s * 0.6)))
        pygame.draw.circle(surf, color, (icx, icy), max(2, int(s * 0.85)), 3)
        pygame.draw.circle(surf, WHITE, (icx, icy), max(2, int(s * 0.62)), 1)


# ============================================================
#  SINTESIS SUARA (tanpa file audio, tanpa numpy)
# ============================================================
SAMPLE_RATE = 22050
_TWO_PI = 2.0 * math.pi


def synth_tone(freq, dur, vol=0.5, wave_type="sine", decay=4.0, sweep_to=None, attack=0.004,
               vib_rate=0.0, vib_depth=0.0):
    n = max(1, int(SAMPLE_RATE * dur))
    att_n = max(1, int(SAMPLE_RATE * attack))
    rel_n = max(1, int(SAMPLE_RATE * 0.01))
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        k = i / n
        f = freq if sweep_to is None else freq + (sweep_to - freq) * k
        if vib_depth:
            f *= 1.0 + vib_depth * math.sin(_TWO_PI * vib_rate * i / SAMPLE_RATE)
        phase += f / SAMPLE_RATE
        ph = phase % 1.0
        if wave_type == "sine":
            s = math.sin(_TWO_PI * ph)
        elif wave_type == "square":
            s = 1.0 if ph < 0.5 else -1.0
        elif wave_type == "saw":
            s = 2.0 * ph - 1.0
        else:  # triangle
            s = 4.0 * abs(ph - 0.5) - 1.0
        env = math.exp(-decay * k)
        if i < att_n:
            env *= i / att_n
        if n - i < rel_n:
            env *= (n - i) / rel_n
        out[i] = s * env * vol
    return out


def synth_noise(dur, vol=0.5, decay=6.0, smooth=1.0):
    n = max(1, int(SAMPLE_RATE * dur))
    out = [0.0] * n
    y = 0.0
    for i in range(n):
        x = random.uniform(-1.0, 1.0)
        y += (x - y) * smooth
        out[i] = y * math.exp(-decay * i / n) * vol
    return out


def mix_layers(layers):
    """layers = [(samples, start_detik), ...] -> satu list sample."""
    total = max(int(start * SAMPLE_RATE) + len(s) for s, start in layers)
    buf = [0.0] * total
    for samples, start in layers:
        off = int(start * SAMPLE_RATE)
        for j, v in enumerate(samples):
            buf[off + j] += v
    return buf


def make_sound(buf, peak_target=0.9, normalize=False):
    peak = max(max(buf), -min(buf))
    if peak <= 1e-9:
        scale = 1.0
    elif normalize:
        scale = peak_target / peak
    else:
        scale = min(1.0, peak_target / peak)
    pcm = array("h", (int(clamp(v * scale, -1.0, 1.0) * 32767) for v in buf))
    if sys.byteorder == "big":
        pcm.byteswap()
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())
    bio.seek(0)
    return pygame.mixer.Sound(file=bio)


def midi_freq(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def build_sfx():
    sfx = {}

    def snd(layers):
        return make_sound(mix_layers(layers))

    # ---------- dasar ----------
    hits = []
    for mult in (1.0, 1.12, 1.26):
        hits.append(snd([
            (synth_tone(190 * mult, 0.28, 0.9, "sine", decay=5.0, sweep_to=45 * mult), 0.0),
            (synth_noise(0.09, 0.55, decay=7.0, smooth=0.5), 0.0),
            (synth_tone(520 * mult, 0.16, 0.22, "saw", decay=6.0, sweep_to=980 * mult), 0.0),
        ]))
    sfx["hit"] = hits
    sfx["wall"] = [snd([
        (synth_tone(760, 0.07, 0.40, "tri", decay=4.0, sweep_to=520), 0.0),
        (synth_noise(0.03, 0.15, decay=8.0, smooth=0.6), 0.0),
    ])]

    layers = [(synth_tone(140, 0.55, 0.9, "sine", decay=4.0, sweep_to=40), 0.0),
              (synth_noise(0.30, 0.30, decay=5.0, smooth=0.3), 0.0)]
    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        layers.append((synth_tone(f, 0.25, 0.28, "saw", decay=3.0), 0.07 * i))
    sfx["score_player"] = [snd(layers)]

    sfx["score_cpu"] = [snd([
        (synth_tone(330, 0.70, 0.40, "saw", decay=3.0, sweep_to=90), 0.0),
        (synth_tone(80, 0.60, 0.90, "sine", decay=3.0, sweep_to=35), 0.0),
        (synth_tone(220, 0.50, 0.25, "tri", decay=3.0, sweep_to=110), 0.15),
    ])]

    sfx["count"] = [snd([(synth_tone(660, 0.12, 0.35, "square", decay=3.0), 0.0)])]
    sfx["go"] = [snd([
        (synth_tone(990, 0.25, 0.35, "square", decay=3.0), 0.0),
        (synth_tone(200, 0.30, 0.25, "saw", decay=2.0, sweep_to=1400), 0.0),
        (synth_noise(0.25, 0.30, decay=3.0, smooth=0.2), 0.0),
    ])]

    layers = [(synth_tone(140, 0.8, 0.9, "sine", decay=3.0, sweep_to=40), 0.55)]
    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        layers.append((synth_tone(f, 0.20, 0.30, "saw", decay=2.0), 0.12 * i))
    for f in (523.25, 659.25, 783.99, 1046.5):
        layers.append((synth_tone(f, 1.2, 0.20, "saw", decay=2.2), 0.55))
    sfx["win"] = [snd(layers)]

    layers = [(synth_tone(55, 1.2, 0.5, "sine", decay=2.0), 0.0)]
    for i, f in enumerate((440.0, 349.23, 329.63, 220.0)):
        layers.append((synth_tone(f, 0.35, 0.30, "saw", decay=2.0), 0.25 * i))
    sfx["lose"] = [snd(layers)]

    sfx["move"] = [snd([(synth_tone(880, 0.05, 0.25, "square", decay=3.0), 0.0)])]
    sfx["ok"] = [snd([
        (synth_tone(660, 0.06, 0.30, "square", decay=3.0), 0.0),
        (synth_tone(990, 0.10, 0.30, "square", decay=3.0), 0.06),
    ])]
    sfx["pause"] = [snd([(synth_tone(500, 0.10, 0.30, "tri", decay=3.0, sweep_to=300), 0.0)])]

    # ---------- mystery box ----------
    sfx["box"] = [snd([
        (synth_tone(1200, 0.14, 0.22, "sine", decay=3.0, sweep_to=2000), 0.0),
        (synth_tone(1600, 0.14, 0.18, "sine", decay=3.0, sweep_to=2600), 0.07),
    ])]
    layers = [(synth_tone(f, 0.14, 0.28, "square", decay=3.0), 0.06 * i)
              for i, f in enumerate((660, 880, 1100, 1480))]
    layers.append((synth_tone(1480, 0.30, 0.25, "sine", decay=2.5, sweep_to=2200), 0.24))
    sfx["pickup"] = [snd(layers)]
    sfx["rare"] = [snd([
        (synth_tone(90, 0.9, 0.7, "sine", decay=2.0, sweep_to=220), 0.0),
        (synth_tone(220, 0.7, 0.3, "saw", decay=2.0, sweep_to=880), 0.0),
        (synth_tone(1760, 0.6, 0.25, "sine", decay=2.5), 0.5),
    ])]

    # ---------- lightning ----------
    layers = [(synth_noise(0.03, 0.6, decay=4.0, smooth=0.7), 0.04 * i) for i in range(6)]
    layers.append((synth_tone(200, 0.30, 0.25, "saw", decay=3.0, sweep_to=1800), 0.0))
    sfx["zap"] = [snd(layers)]
    sfx["thunder"] = [snd([
        (synth_noise(0.05, 1.0, decay=2.0, smooth=1.0), 0.0),
        (synth_noise(0.90, 0.8, decay=3.0, smooth=0.12), 0.02),
        (synth_tone(70, 0.8, 0.9, "sine", decay=3.0, sweep_to=35), 0.02),
        (synth_tone(200, 0.25, 0.3, "saw", decay=4.0, sweep_to=1800), 0.0),
    ])]

    # ---------- time ----------
    layers = [(synth_noise(0.5, 0.6, decay=5.0, smooth=0.2)[::-1], 0.0),
              (synth_tone(110, 2.0, 0.7, "sine", decay=1.6), 0.5),
              (synth_tone(220, 1.6, 0.3, "sine", decay=2.0), 0.5),
              (synth_tone(331, 1.2, 0.15, "sine", decay=2.5), 0.5),
              (synth_tone(553, 1.0, 0.1, "sine", decay=3.0), 0.5)]
    for i in range(6):
        layers.append((synth_tone(1800 if i % 2 == 0 else 1500, 0.015, 0.35, "square", decay=1.0),
                       0.5 + 0.3 * i))
    sfx["zawarudo"] = [snd(layers)]
    sfx["time_end"] = [snd([
        (synth_tone(900, 0.4, 0.3, "sine", decay=2.0, sweep_to=200), 0.0),
        (synth_noise(0.4, 0.3, decay=4.0, smooth=0.3)[::-1], 0.0),
    ])]

    # ---------- clone ----------
    sfx["poof"] = [snd([
        (synth_noise(0.35, 0.55, decay=4.0, smooth=0.3), 0.0),
        (synth_tone(300, 0.25, 0.3, "sine", decay=4.0, sweep_to=100), 0.0),
        (synth_tone(1500, 0.15, 0.12, "sine", decay=3.0), 0.05),
    ])]

    # ---------- shield ----------
    sfx["shield_on"] = [snd([
        (synth_tone(500, 0.5, 0.3, "sine", decay=1.5, sweep_to=1500), 0.0),
        (synth_tone(1000, 0.4, 0.2, "tri", decay=2.0, sweep_to=2000), 0.0),
        (synth_tone(1800, 0.4, 0.2, "sine", decay=3.0), 0.3),
    ])]
    sfx["shield_hit"] = [snd([
        (synth_tone(1400, 0.4, 0.5, "sine", decay=4.0), 0.0),
        (synth_tone(2100, 0.3, 0.3, "sine", decay=5.0), 0.0),
        (synth_noise(0.03, 0.3, decay=8.0, smooth=0.7), 0.0),
    ])]
    sfx["shield_off"] = [snd([(synth_tone(1200, 0.3, 0.3, "sine", decay=3.0, sweep_to=400), 0.0)])]

    # ---------- fish ----------
    sfx["wlee"] = [snd([
        (synth_tone(600, 0.55, 0.4, "tri", decay=1.2, sweep_to=1500, vib_rate=14, vib_depth=0.07), 0.0),
        (synth_tone(300, 0.50, 0.15, "square", decay=1.5, sweep_to=750, vib_rate=14, vib_depth=0.07), 0.0),
    ])]
    layers = [(synth_tone(900 + (i % 2) * 200, 0.08, 0.28, "tri", decay=2.5, vib_rate=25, vib_depth=0.1),
               0.1 * i) for i in range(7)]
    sfx["laugh"] = [snd(layers)]
    sfx["fish_hit"] = [snd([
        (synth_noise(0.06, 0.7, decay=6.0, smooth=0.5), 0.0),
        (synth_tone(220, 0.25, 0.6, "sine", decay=4.0, sweep_to=80), 0.0),
        (synth_tone(400, 0.35, 0.3, "tri", decay=2.0, sweep_to=900, vib_rate=18, vib_depth=0.08), 0.05),
    ])]

    # ---------- light ----------
    sfx["light"] = [snd([
        (synth_noise(0.35, 0.5, decay=4.0, smooth=0.8), 0.0),
        (synth_tone(600, 0.4, 0.35, "sine", decay=2.0, sweep_to=2400), 0.0),
        (synth_tone(2400, 0.5, 0.25, "sine", decay=3.0), 0.2),
    ])]

    # ---------- black hole ----------
    sfx["bh_throw"] = [snd([
        (synth_tone(200, 0.7, 0.5, "saw", decay=1.5, sweep_to=60), 0.0),
        (synth_noise(0.7, 0.4, decay=2.0, smooth=0.15), 0.0),
    ])]
    sfx["bh_suck"] = [snd([
        (synth_tone(55, 2.6, 0.8, "sine", decay=0.5, sweep_to=28), 0.0),
        (synth_noise(2.4, 0.5, decay=3.0, smooth=0.06)[::-1], 0.0),
        (synth_tone(120, 2.4, 0.2, "saw", decay=1.0, sweep_to=40), 0.0),
    ])]
    sfx["bh_erase"] = [snd([
        (synth_tone(60, 1.6, 1.0, "sine", decay=1.8, sweep_to=25), 0.0),
        (synth_tone(110, 1.2, 0.2, "saw", decay=2.0), 0.0),
        (synth_tone(117, 1.2, 0.2, "saw", decay=2.0), 0.0),
        (synth_noise(0.4, 0.5, decay=4.0, smooth=0.2), 0.0),
    ])]

    # ---------- map & event ----------
    sfx["horn"] = [snd([
        (synth_tone(196, 0.6, 0.35, "saw", decay=0.8), 0.0),
        (synth_tone(247, 0.6, 0.30, "saw", decay=0.8), 0.0),
        (synth_tone(196, 0.5, 0.35, "saw", decay=0.8), 0.8),
        (synth_tone(247, 0.5, 0.30, "saw", decay=0.8), 0.8),
    ])]
    sfx["vroom"] = [snd([
        (synth_noise(0.9, 0.5, decay=1.5, smooth=0.12), 0.0),
        (synth_tone(70, 0.9, 0.5, "saw", decay=1.0, sweep_to=140), 0.0),
    ])]
    sfx["crash"] = [snd([
        (synth_noise(0.35, 0.9, decay=4.0, smooth=0.6), 0.0),
        (synth_tone(120, 0.4, 0.8, "sine", decay=4.0, sweep_to=35), 0.0),
        (synth_tone(800, 0.2, 0.3, "square", decay=5.0, sweep_to=300), 0.0),
    ])]
    sfx["rumble"] = [snd([
        (synth_noise(1.0, 0.5, decay=1.0, smooth=0.05), 0.0),
        (synth_tone(48, 1.0, 0.7, "sine", decay=1.0, sweep_to=36), 0.0),
    ])]
    sfx["erupt"] = [snd([
        (synth_noise(0.8, 0.8, decay=2.5, smooth=0.25), 0.0),
        (synth_tone(110, 0.8, 0.8, "sine", decay=2.5, sweep_to=40), 0.0),
    ])]
    sfx["sizzle"] = [snd([
        (synth_noise(0.5, 0.45, decay=3.0, smooth=0.9), 0.0),
        (synth_tone(300, 0.4, 0.2, "saw", decay=3.0, sweep_to=120), 0.0),
    ])]
    sfx["throw"] = [snd([
        (synth_noise(0.3, 0.35, decay=3.0, smooth=0.2)[::-1], 0.0),
        (synth_tone(300, 0.3, 0.2, "tri", decay=2.0, sweep_to=700), 0.0),
    ])]
    sfx["splat"] = [snd([
        (synth_noise(0.15, 0.6, decay=5.0, smooth=0.5), 0.0),
        (synth_tone(220, 0.2, 0.5, "sine", decay=4.0, sweep_to=80), 0.0),
    ])]
    sfx["glass"] = [snd([
        (synth_noise(0.05, 0.7, decay=3.0, smooth=1.0), 0.0),
        (synth_noise(0.05, 0.6, decay=3.0, smooth=1.0), 0.05),
        (synth_noise(0.08, 0.5, decay=3.0, smooth=1.0), 0.1),
        (synth_tone(2400, 0.2, 0.25, "sine", decay=5.0), 0.0),
        (synth_tone(3100, 0.2, 0.2, "sine", decay=5.0), 0.04),
        (synth_noise(0.6, 0.3, decay=2.0, smooth=0.9), 0.1),
    ])]
    sfx["whistle"] = [snd([(synth_tone(1800, 0.7, 0.3, "sine", decay=0.5, sweep_to=500), 0.0)])]
    sfx["boom"] = [snd([
        (synth_tone(100, 1.1, 1.0, "sine", decay=2.0, sweep_to=25), 0.0),
        (synth_noise(0.7, 0.9, decay=3.0, smooth=0.15), 0.0),
    ])]
    sfx["pop"] = [snd([
        (synth_noise(0.1, 0.6, decay=5.0, smooth=0.5), 0.0),
        (synth_tone(300, 0.1, 0.4, "sine", decay=4.0, sweep_to=100), 0.0),
    ])]
    sfx["bleed"] = [snd([
        (synth_tone(300, 0.5, 0.35, "saw", decay=2.0, sweep_to=90), 0.0),
        (synth_tone(317, 0.5, 0.30, "saw", decay=2.0, sweep_to=95), 0.0),
        (synth_noise(0.2, 0.4, decay=5.0, smooth=0.4), 0.0),
    ])]
    sfx["locked"] = [snd([
        (synth_tone(220, 0.08, 0.3, "square", decay=3.0), 0.0),
        (synth_tone(180, 0.12, 0.3, "square", decay=3.0), 0.1),
    ])]
    sfx["hiss"] = [snd([(synth_noise(0.6, 0.3, decay=2.0, smooth=0.9), 0.0)])]

    for lst in sfx.values():
        for s in lst:
            s.set_volume(0.85)
    return sfx


def slow_down_buffer(buf, factor=0.62):
    """Versi BGM melambat + terdistorsi + teredam untuk efek ZA WARUDO."""
    n = len(buf)
    out_n = int(n / factor)
    out = [0.0] * out_n
    last = n - 2
    for j in range(out_n):
        pos = j * factor
        i = int(pos)
        if i > last:
            i = last
        fr = pos - i
        out[j] = buf[i] + (buf[i + 1] - buf[i]) * fr
    y = 0.0
    for j in range(out_n):
        x = math.tanh(out[j] * 2.4)       # distorsi
        y += (x - y) * 0.35               # peredam (low-pass)
        out[j] = y
    return out


def build_bgm():
    """BGM synthwave 128 BPM, 8 bar, A-minor (Am F C G Am F G E) - loop.
    Mengembalikan (bgm_normal, bgm_melambat)."""
    bpm = 128
    step = 60.0 / bpm / 4.0               # durasi 1/16 nada (detik)
    step_n = step * SAMPLE_RATE
    progression = [
        (45, [69, 72, 76]),   # Am
        (41, [65, 69, 72]),   # F
        (48, [72, 76, 79]),   # C
        (43, [67, 71, 74]),   # G
        (45, [69, 72, 76]),   # Am
        (41, [65, 69, 72]),   # F
        (43, [67, 71, 74]),   # G
        (40, [68, 71, 76]),   # E
    ]
    total_n = int(len(progression) * 16 * step_n) + SAMPLE_RATE // 2
    buf = [0.0] * total_n
    cache = {}

    def cached(key, factory):
        s = cache.get(key)
        if s is None:
            s = factory()
            cache[key] = s
        return s

    def add(samples, step_index, vol):
        start = int(step_index * step_n)
        end = min(total_n, start + len(samples))
        if end <= start:
            return
        seg = buf[start:end]
        buf[start:end] = [a + b * vol for a, b in zip(seg, samples)]

    kick = mix_layers([
        (synth_tone(160, 0.22, 1.0, "sine", decay=5.0, sweep_to=42), 0.0),
        (synth_noise(0.01, 0.4, decay=3.0), 0.0),
    ])
    snare = mix_layers([
        (synth_noise(0.18, 0.9, decay=6.0, smooth=0.55), 0.0),
        (synth_tone(210, 0.10, 0.5, "tri", decay=6.0), 0.0),
    ])
    hat = synth_noise(0.05, 0.6, decay=9.0, smooth=1.0)
    bar_dur = 16 * step

    for bar, (root, tones) in enumerate(progression):
        base = bar * 16
        for s in range(16):
            idx = base + s
            if s % 4 == 0:
                add(kick, idx, 0.55)
            if s in (4, 12):
                add(snare, idx, 0.30)
            if s % 4 == 2:
                add(hat, idx, 0.16)
            elif s % 2 == 0:
                add(hat, idx, 0.07)
            if s % 2 == 0:
                m = root + (12 if s in (6, 14) else 0)
                add(cached(("bass", m), lambda m=m: synth_tone(
                    midi_freq(m), step * 2.0, 1.0, "saw", decay=2.5, attack=0.003)), idx, 0.20)
            m = tones[(0, 1, 2, 1)[s % 4]] + (12 if s >= 8 else 0)
            add(cached(("arp", m), lambda m=m: synth_tone(
                midi_freq(m), step * 1.8, 1.0, "square", decay=4.0)), idx, 0.07)
        for m in (tones[1], tones[2]):
            add(cached(("pad", m), lambda m=m: synth_tone(
                midi_freq(m - 12), bar_dur, 1.0, "saw", decay=0.6, attack=0.3)), base, 0.045)

    normal = make_sound(buf, peak_target=0.8, normalize=True)
    slow = make_sound(slow_down_buffer(buf), peak_target=0.8, normalize=True)
    return normal, slow


class Audio:
    """Pembungkus suara; kalau audio gagal, game tetap jalan tanpa suara."""

    def __init__(self):
        self.ok = False
        self.muted = False
        self.sfx = {}
        self.bgm = None
        self.bgm_slow = None
        self.bgm_ch = None
        self.level = 0.35
        # Audio sintetis tetap aktif pada desktop, tetapi dinonaktifkan di browser.
        # Ini menghindari inisialisasi mixer dan pembuatan BGM/SFX yang berat di WASM.
        if globals().get("WEB_MODE", False):
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(24)
            pygame.mixer.set_reserved(1)       # channel 0 khusus BGM
            self.bgm_ch = pygame.mixer.Channel(0)
            self.ok = True
        except Exception as e:  # noqa: BLE001
            print("Audio tidak aktif:", e)

    def build(self):
        if not self.ok:
            return
        try:
            self.sfx = build_sfx()
            pygame.event.pump()
            self.bgm, self.bgm_slow = build_bgm()
        except Exception as e:  # noqa: BLE001
            print("Gagal membuat suara, game berjalan tanpa audio:", e)
            self.ok = False

    def play(self, name):
        if not self.ok or self.muted:
            return
        snds = self.sfx.get(name)
        if snds:
            random.choice(snds).play()

    def start_music(self):
        if self.ok and self.bgm is not None:
            self.bgm_ch.play(self.bgm, loops=-1)
            self.apply_level()

    def set_slow(self, flag):
        """Ganti BGM ke versi melambat/terdistorsi (ZA WARUDO) atau normal."""
        if not self.ok or self.bgm is None or self.bgm_ch is None:
            return
        snd = self.bgm_slow if (flag and self.bgm_slow is not None) else self.bgm
        self.bgm_ch.play(snd, loops=-1)
        self.apply_level()

    def set_music_level(self, v):
        self.level = v
        self.apply_level()

    def apply_level(self):
        if self.ok and self.bgm_ch is not None:
            self.bgm_ch.set_volume(0.0 if self.muted else self.level)

    def toggle_mute(self):
        self.muted = not self.muted
        self.apply_level()


# ============================================================
#  PARTIKEL
# ============================================================
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "drag", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, drag=0.94, gravity=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.drag, self.gravity = color, size, drag, gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.drag
        self.vy = self.vy * self.drag + self.gravity
        self.life -= 1

    def draw(self, surf):
        f = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * (0.4 + 0.6 * f)))
        pygame.draw.circle(surf, scale_color(self.color, f), (int(self.x), int(self.y)), r)


# ============================================================
#  SISI PEMAIN (player / cpu)
# ============================================================
class Side:
    def __init__(self, name):
        self.name = name
        self.is_player = (name == "player")
        self.fwd = -1 if self.is_player else 1        # arah menuju lawan
        self.rect = pygame.Rect(0, 0, PADDLE_W, PADDLE_H)
        self.clone_rect = pygame.Rect(0, 0, PADDLE_W, PADDLE_H)
        self.hist = deque(maxlen=8)
        self.light_hist = deque(maxlen=14)
        self.ai_delay = 0
        self.color = (255, 255, 255)
        self.display_name = name.upper()
        self.look = PLAIN_LOOK
        self.ctrl = None            # None = dikendalikan AI
        self.reset_match()

    def reset_match(self):
        self.cy = SCREEN_H / 2
        self.vel = 0.0
        self.score = 0
        self.glow = 0
        self.pulse = 0
        self.slot = None
        self.box = None
        self.box_timer = random.randint(BOX_MIN, BOX_MAX)
        self.ai_delay = 0
        self.hist.clear()
        self.light_hist.clear()
        self.clear_effects()
        self.sync()

    def clear_effects(self):
        self.stun_t = 0
        self.slow_t = 0
        self.clone_t = 0
        self.shield_t = 0
        self.light_t = 0
        self.time_t = 0
        self.dark_t = 0
        self.lava_t = 0
        self.lock_t = 0
        self.dizzy_t = 0
        self.bleed_t = 0
        self.armed = False
        self.light_hist.clear()

    def sync(self):
        if self.is_player:
            self.rect.midright = (SCREEN_W - PADDLE_MARGIN, int(self.cy))
        else:
            self.rect.midleft = (PADDLE_MARGIN, int(self.cy))
        self.clone_rect.x = self.rect.x
        self.clone_rect.centery = int(SCREEN_H - self.cy)   # gerak terbalik dari paddle utama

    def paddles(self):
        return [self.rect, self.clone_rect] if self.clone_t > 0 else [self.rect]

    def speed_mult(self):
        if self.stun_t > 0:
            return 0.0
        m = 1.0
        if self.slow_t > 0:
            m *= TIME_SLOW
        if self.light_t > 0:
            m *= LIGHT_MULT
        if self.lava_t > 0:
            m *= LAVA_MULT
        if self.bleed_t > 0:
            m *= BLEED_MULT
        return m


def spiral_pos(p0, center, k):
    """Posisi benda yang tersedot lubang hitam (memutar sambil mendekat)."""
    dx = p0[0] - center[0]
    dy = p0[1] - center[1]
    dist = math.hypot(dx, dy)
    ang = math.atan2(dy, dx) + k * 7.0
    r = dist * (1.0 - k)
    return (center[0] + math.cos(ang) * r, center[1] + math.sin(ang) * r)


# ============================================================
#  GAME
# ============================================================
class Game:
    def __init__(self):
        # SCALED butuh renderer SDL (WebGL) dan dapat gagal di browser dengan
        # "failed to create renderer". Di browser, Pygbag sudah menskalakan
        # canvas lewat CSS, jadi cukup mode software biasa.
        if globals().get("WEB_MODE", False):
            flags = 0
        else:
            flags = getattr(pygame, "SCALED", 0)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption("Ping Pong Game By Fredd")
        self.clock = pygame.time.Clock()

        self.canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
        self.fx = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
        self.flash_surf = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
        self.dim = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
        self.dim.fill((0, 0, 0))
        self.dim.set_alpha(150)
        self.bloom_ok = True

        self.draw_loading("MEMUAT SUARA & MUSIK...")
        self.audio = Audio()
        self.audio.build()
        self.stars = [[random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H),
                       random.uniform(0.2, 1.0), random.randint(1, 3),
                       random.uniform(0, 6.28)] for _ in range(80)]

        self.t = 0
        self.state = "menu"
        self.skin_idx = 0
        self.diff_idx = 1
        self.skills_on = True
        self.mode = 0                      # 0 = 1 pemain (vs AI), 1 = 2 pemain (versus)
        self.map_idx = 0
        self.cskin_idx = 0
        self.prof = [{"name": "PLAYER 1", "skin": 0, "head": 0, "chest": 0, "hand": 0},
                     {"name": "PLAYER 2", "skin": 0, "head": 0, "chest": 0, "hand": 0}]
        self.menu_page = 0
        self.menu_row = 0
        self.bg_cache = {}
        self.thumb_cache = {}
        self.hazards = []
        self.hz_new = []
        self.map_timer = 0
        self.comp_ok = True
        self.load_settings()

        self.player = Side("player")
        self.cpu = Side("cpu")
        self.sides = (self.cpu, self.player)

        self.particles = []
        self.rings = []
        self.texts = []
        self.speed_lines = []
        self.fish = []
        self.delayed = []
        self.bh = None
        self.ball_electric = None
        self.bgm_slow = False
        self.flash_alpha = 0.0
        self.flash_color = WHITE
        self.shake = 0.0
        self.hitstop = 0

        self.reset_match()
        self.audio.set_music_level(MUSIC_LEVELS["menu"])
        self.audio.start_music()

    # ---------------------------------------------------------
    #  Setup pertandingan
    # ---------------------------------------------------------
    def draw_loading(self, text):
        self.screen.fill((0, 0, 0))
        draw_text(self.screen, text, 56, WHITE, (SCREEN_W // 2, SCREEN_H // 2))
        pygame.display.flip()
        pygame.event.pump()

    def other(self, side):
        return self.cpu if side is self.player else self.player

    def reset_match(self):
        self.player.reset_match()
        self.cpu.reset_match()
        self.setup_sides()
        self.map_timer = MAPS[self.map_idx]["interval"] * FPS
        self.ball_trail = deque(maxlen=16)
        self.ball_rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.cpu_target = SCREEN_H / 2
        self.cpu_error = 0.0
        self.cpu_react = 0
        self.winner = None
        self.particles.clear()
        self.rings.clear()
        self.texts.clear()
        self.speed_lines.clear()
        self.hitstop = 0
        self.rally = 0
        self.start_serve(random.choice((-1, 1)))

    def clear_round_effects(self):
        for s in self.sides:
            s.clear_effects()
        self.hazards = []
        self.hz_new = []
        self.fish = []
        self.delayed = []
        self.bh = None
        self.ball_electric = None

    def start_serve(self, direction):
        """direction: +1 bola menuju player (kanan), -1 menuju CPU (kiri)."""
        self.clear_round_effects()
        self.ball_x = SCREEN_W / 2
        self.ball_y = SCREEN_H / 2
        self.ball_speed = BALL_START_SPEED
        self.bvx = 0.0
        self.bvy = 0.0
        self.serve_dir = direction
        self.serve_timer = SERVE_FRAMES
        self.last_count = None
        self.rally = 0
        self.ball_trail.clear()
        self.ball_rect.center = (int(self.ball_x), int(self.ball_y))
        self.new_cpu_error()

    def launch_ball(self):
        angle = random.uniform(-0.45, 0.45)
        self.bvx = self.serve_dir * math.cos(angle) * self.ball_speed
        self.bvy = math.sin(angle) * self.ball_speed
        self.cpu_react = 0
        self.audio.play("go")
        self.add_text("GO!", SCREEN_W / 2, SCREEN_H / 2 - 140, WHITE, 100, 40)
        self.add_flash(70, WHITE)
        self.burst(self.ball_x, self.ball_y, SKINS[self.skin_idx]["ball_glow"], 24, speed=7)

    def new_cpu_error(self):
        d = DIFFICULTIES[self.diff_idx]
        err = random.uniform(-d["error"], d["error"])
        # makin panjang reli, makin besar peluang CPU salah (CPU bisa "capek")
        chance = d["mistake"] + 0.03 * max(0, self.rally - 6)
        if random.random() < chance:
            err += random.choice((-1, 1)) * random.uniform(90, 160)
        self.cpu_error = err

    def start_match(self):
        self.audio.play("ok")
        self.reset_match()
        self.state = "play"
        self.audio.set_music_level(MUSIC_LEVELS["play"])

    def go_menu(self):
        self.clear_round_effects()
        self.state = "menu"
        self.audio.set_music_level(MUSIC_LEVELS["menu"])

    def quit(self):
        pygame.quit()
        sys.exit()

    # ---------------------------------------------------------
    #  Efek
    # ---------------------------------------------------------
    def burst(self, x, y, color, count, speed=6.0, life=(20, 40), size=(2, 5),
              gravity=0.0, angle=None, spread=math.pi):
        for _ in range(count):
            a = random.uniform(0, math.tau) if angle is None else angle + random.uniform(-spread, spread)
            s = random.uniform(speed * 0.3, speed)
            self.particles.append(Particle(
                x, y, math.cos(a) * s, math.sin(a) * s, random.randint(life[0], life[1]),
                color, random.uniform(size[0], size[1]), 0.94, gravity))

    def smoke(self, x, y, count=22):
        """Awan tipis (tidak menutupi permainan): redup & transparan-ish."""
        self.burst(x, y, (110, 110, 125), count, speed=2.6, life=(40, 70), size=(10, 22))

    def add_ring(self, x, y, color, grow=6.0, life=22):
        self.rings.append([x, y, 8.0, grow, color, life, life])

    def add_text(self, text, x, y, color, size=70, life=50):
        self.texts.append({"text": text, "x": x, "y": y, "color": color,
                           "size": size, "life": life, "max": life})

    def add_flash(self, alpha, color):
        self.flash_alpha = max(self.flash_alpha, alpha)
        self.flash_color = color

    def later(self, frames, fn):
        self.delayed.append([frames, fn])

    # ---------------------------------------------------------
    #  Input
    # ---------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key
            if key == pygame.K_F11:
                try:
                    pygame.display.toggle_fullscreen()
                except Exception:  # noqa: BLE001
                    pass
                continue
            if self.state == "menu":
                self.menu_key(event)
                continue
            if key == pygame.K_m:
                self.audio.toggle_mute()
                continue
            # 2 pemain: tombol P dipakai Pemain 2, jadi pause hanya lewat ESC
            pause_keys = (pygame.K_p, pygame.K_ESCAPE) if self.mode == 0 else (pygame.K_ESCAPE,)
            if self.state == "play":
                if key in pause_keys:
                    self.state = "pause"
                    self.audio.play("pause")
                    self.audio.set_music_level(MUSIC_LEVELS["pause"])
                else:
                    for s in self.sides:
                        if s.ctrl is not None and key in s.ctrl["skill"]:
                            self.use_skill(s)
            elif self.state == "pause":
                if key in pause_keys:
                    self.state = "play"
                    self.audio.play("pause")
                    self.audio.set_music_level(MUSIC_LEVELS["play"])
                elif key == pygame.K_q:
                    self.go_menu()
            elif self.state == "gameover":
                if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.begin_match()
                elif key == pygame.K_ESCAPE:
                    self.go_menu()

    def menu_key(self, event):
        key = event.key
        editing = self.editing_name()
        n_rows = self.page_rows()
        if key == pygame.K_TAB:
            self.menu_page = (self.menu_page + 1) % 3
            self.menu_row = 0
            self.audio.play("move")
        elif key == pygame.K_UP or (not editing and key == pygame.K_w):
            self.menu_row = (self.menu_row - 1) % n_rows
            self.audio.play("move")
        elif key == pygame.K_DOWN or (not editing and key == pygame.K_s):
            self.menu_row = (self.menu_row + 1) % n_rows
            self.audio.play("move")
        elif key in (pygame.K_LEFT, pygame.K_RIGHT) or (not editing and key in (pygame.K_a, pygame.K_d)):
            self.menu_change(-1 if key in (pygame.K_LEFT, pygame.K_a) else 1)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.begin_match()
        elif key == pygame.K_ESCAPE:
            self.quit()
        elif editing and key == pygame.K_BACKSPACE:
            p = self.prof[self.menu_page - 1]
            p["name"] = p["name"][:-1]
        elif editing:
            p = self.prof[self.menu_page - 1]
            ch = getattr(event, "unicode", "") or ""
            if ch and ch.isprintable() and len(p["name"]) < 12 and (ch.isalnum() or ch in " -_."):
                p["name"] += ch.upper()
        elif key == pygame.K_m:
            self.audio.toggle_mute()
        elif key == pygame.K_SPACE:
            self.begin_match()

    # ---------------------------------------------------------
    #  Update
    # ---------------------------------------------------------
    def update(self):
        self.t += 1
        for s in self.stars:
            s[0] -= s[2] * 0.6
            if s[0] < 0:
                s[0] = SCREEN_W
                s[1] = random.uniform(0, SCREEN_H)

        if self.state == "play":
            if self.hitstop > 0:
                self.hitstop -= 1
            else:
                self.update_logic()
        elif self.state == "gameover":
            self.spawn_confetti()

        if self.state != "pause":
            self.update_fx()
        self.update_bgm_mode()

    def update_bgm_mode(self):
        want = self.player.time_t > 0 or self.cpu.time_t > 0
        if want != self.bgm_slow:
            self.bgm_slow = want
            self.audio.set_slow(want)

    def update_logic(self):
        if self.bh is not None:
            self.update_blackhole()
            return
        if self.cpu.ctrl is not None:
            self.update_human(self.cpu)
        else:
            self.update_cpu()
        self.update_human(self.player)
        self.update_boxes()
        self.update_map()
        self.tick_effects()
        self.update_cpu_skill_ai()
        if self.bh is not None:
            return
        self.update_fish()
        if self.serve_timer > 0:
            self.serve_timer -= 1
            number = -(-self.serve_timer // SERVE_STEP)      # ceil
            if number > 0 and number != self.last_count:
                self.last_count = number
                self.audio.play("count")
            if self.serve_timer == 0:
                self.launch_ball()
            return
        self.update_ball()

    def move_side(self, s, desired, accel):
        if s.stun_t > 0:
            s.vel = 0.0
        else:
            s.vel += (desired - s.vel) * accel
            if abs(s.vel) < 0.05:
                s.vel = 0.0
        s.cy += s.vel
        half = PADDLE_H / 2
        if s.cy < half:
            s.cy = half
            s.vel = 0.0
        elif s.cy > SCREEN_H - half:
            s.cy = SCREEN_H - half
            s.vel = 0.0
        s.sync()
        s.hist.append(s.rect.topleft)
        if s.light_t > 0:
            s.light_hist.append(s.rect.topleft)
        elif s.light_hist:
            s.light_hist.clear()

    def update_human(self, s):
        """Gerakkan paddle pemain manusia sesuai kontrol sisinya (s.ctrl)."""
        keys = pygame.key.get_pressed()
        ctrl = s.ctrl
        target = 0.0
        if any(keys[k] for k in ctrl["up"]):
            target -= 1.0
        if any(keys[k] for k in ctrl["down"]):
            target += 1.0
        if s.dizzy_t > 0:
            target = -target                          # pusing: kontrol terbalik
        self.move_side(s, target * PLAYER_MAX_SPEED * s.speed_mult(), 0.35)

    def update_cpu(self):
        """AI sederhana & BISA dikalahkan: bereaksi telat, bidikan meleset,
        kecepatan terbatas, dan sesekali salah baca bola."""
        s = self.cpu
        d = DIFFICULTIES[self.diff_idx]
        chasing = self.serve_timer == 0 and self.bvx < 0
        if chasing:
            self.cpu_react -= 1
            if self.cpu_react <= 0:
                self.cpu_target = self.ball_y + self.cpu_error
                self.cpu_react = d["react"]
            top_speed = d["speed"]
        elif s.box is not None:
            self.cpu_target = s.box["y"]               # bola menjauh -> ambil mystery box
            top_speed = d["speed"] * 0.8
        else:
            self.cpu_target = SCREEN_H / 2             # bola menjauh -> kembali ke tengah
            top_speed = d["speed"] * 0.5
        top_speed *= s.speed_mult()
        diff = self.cpu_target - s.cy
        desired = 0.0
        if abs(diff) > 6:
            desired = clamp(diff * 0.25, -top_speed, top_speed)
        if s.dizzy_t > 0:
            desired = -desired
        self.move_side(s, desired, 0.3)

    # ---------------------------------------------------------
    #  Mystery box & skill
    # ---------------------------------------------------------
    def update_boxes(self):
        if not self.skills_on:
            return
        for s in self.sides:
            if s.box_timer > 0:
                s.box_timer -= 1
            if s.box is None:
                if s.box_timer <= 0 and s.slot is None:
                    self.spawn_box(s)
                continue
            b = s.box
            b["life"] -= 1
            b["age"] += 1
            brect = pygame.Rect(0, 0, BOX_SIZE, BOX_SIZE)
            brect.center = (s.rect.centerx, int(b["y"]))
            picked = False
            for p in s.paddles():
                if p.colliderect(brect):
                    picked = True
                    break
            if picked:
                self.pickup(s)
            elif b["life"] <= 0:
                s.box = None
                s.box_timer = random.randint(BOX_MIN, BOX_MAX)

    def spawn_box(self, s):
        s.box = {"y": random.uniform(100, SCREEN_H - 100), "life": BOX_LIFE, "age": 0}
        self.burst(s.rect.centerx, s.box["y"], hsv_color(random.random()), 14, speed=4.0,
                   life=(14, 26), size=(2, 4))
        self.audio.play("box")

    def pickup(self, s):
        b = s.box
        s.box = None
        s.box_timer = random.randint(BOX_MIN, BOX_MAX)
        kind = random.choices(SKILL_KEYS, weights=SKILL_WEIGHTS, k=1)[0]
        s.slot = kind
        info = SKILLS[kind]
        color = info["color"]
        self.burst(s.rect.centerx, b["y"], color, 34, speed=7.0, life=(18, 36), size=(2, 5))
        self.add_ring(s.rect.centerx, b["y"], color, grow=7.0, life=22)
        self.add_text(info["name"], s.rect.centerx + s.fwd * 190, b["y"], color, 44, 55)
        self.audio.play("pickup")
        if kind == "blackhole":
            self.add_text("RARE SKILL!!", SCREEN_W / 2, 330, (255, 215, 90), 84, 80)
            self.add_flash(110, (150, 60, 255))
            self.audio.play("rare")
        if s.ctrl is None:
            s.ai_delay = random.randint(50, 140)

    def tick_effects(self):
        for s in self.sides:
            cx, cy = s.rect.center
            if s.stun_t > 0:
                s.stun_t -= 1
            if s.slow_t > 0:
                s.slow_t -= 1
            if s.lava_t > 0:
                s.lava_t -= 1
            if s.lock_t > 0:
                s.lock_t -= 1
            if s.dizzy_t > 0:
                s.dizzy_t -= 1
            if s.bleed_t > 0:
                s.bleed_t -= 1
                if self.t % 5 == 0:
                    self.burst(cx, cy + random.uniform(-40, 40), (200, 20, 40), 1, speed=1.0,
                               life=(20, 34), size=(2, 4), gravity=0.2)
            if s.time_t > 0:
                s.time_t -= 1
                if s.time_t == 0:
                    self.audio.play("time_end")
                elif self.t % 4 == 0:
                    self.burst(cx + random.uniform(-30, 30), cy + random.uniform(-60, 60),
                               (255, 225, 120), 1, speed=2.0, life=(14, 26), size=(2, 4))
            if s.clone_t > 0:
                s.clone_t -= 1
                if s.clone_t == 0:
                    self.smoke(s.clone_rect.centerx, s.clone_rect.centery, 14)
                    self.audio.play("poof")
                elif self.t % 18 == 0:
                    self.burst(s.clone_rect.centerx, s.clone_rect.centery + random.uniform(-50, 50),
                               (130, 130, 145), 1, speed=1.0, life=(30, 50), size=(8, 14))
            if s.shield_t > 0:
                s.shield_t -= 1
                if s.shield_t == 0:
                    self.audio.play("shield_off")
            if s.light_t > 0:
                s.light_t -= 1
                if abs(s.vel) > 1.0:
                    self.burst(cx, cy + random.uniform(-50, 50), (255, 235, 90), 2, speed=3.0,
                               life=(12, 24), size=(2, 4))
            if s.armed and self.t % 4 == 0:
                self.burst(cx + random.uniform(-14, 14), cy + random.uniform(-55, 55),
                           (150, 220, 255), 1, speed=3.0, life=(8, 16), size=(2, 3))

    def update_cpu_skill_ai(self):
        s = self.cpu
        if s.ctrl is not None:
            return                                    # sisi kiri dipegang pemain manusia
        if s.slot is None or self.serve_timer > 0 or s.lock_t > 0:
            return
        if s.ai_delay > 0:
            s.ai_delay -= 1
            return
        if s.slot in ("lightning", "clone", "shield", "light") and self.bvx >= 0:
            return                                    # tunggu bola mengarah ke CPU
        self.use_skill(s)

    def use_skill(self, s):
        if self.state != "play" or self.bh is not None or self.serve_timer > 0:
            return False
        if s.lock_t > 0 and s.slot is not None:
            if s.ctrl is not None:
                self.add_text("SKILL TERKUNCI!", SCREEN_W / 2 - (s.fwd * 130 if self.mode == 1 else 0), 290,
                              (255, 110, 110), 80, 45)
                self.audio.play("locked")
            return False
        kind = s.slot
        if kind is None:
            return False
        o = self.other(s)
        info = SKILLS[kind]
        s.slot = None
        if s.box_timer < 180:
            s.box_timer = 180
        color = info["color"]
        self.add_text(info["text"], SCREEN_W / 2 - (s.fwd * 130 if self.mode == 1 else 0), 290, color, 96, 75)
        cx, cy = s.rect.center
        if kind == "lightning":
            s.armed = True
            self.audio.play("zap")
            self.add_flash(90, color)
            for _ in range(3):
                a = random.uniform(0, math.tau)
                draw_pts = bolt_points(cx, cy, cx + math.cos(a) * 80, cy + math.sin(a) * 80, 5, 12)
                self.burst(draw_pts[-1][0], draw_pts[-1][1], color, 6, speed=4.0, life=(10, 20))
        elif kind == "time":
            s.time_t = TIME_FRAMES
            o.slow_t = TIME_FRAMES
            self.audio.play("zawarudo")
            self.add_flash(130, (255, 225, 110))
            self.shake = max(self.shake, 10.0)
            self.add_ring(cx, cy, color, grow=18.0, life=40)
            self.add_ring(cx, cy, WHITE, grow=26.0, life=34)
            self.add_ring(SCREEN_W / 2, SCREEN_H / 2, color, grow=30.0, life=46)
            self.burst(cx, cy, color, 36, speed=8.0, life=(20, 40))
        elif kind == "clone":
            s.clone_t = CLONE_FRAMES
            s.sync()
            self.audio.play("poof")
            self.smoke(cx, cy)
            self.smoke(s.clone_rect.centerx, s.clone_rect.centery)
        elif kind == "shield":
            s.shield_t = SHIELD_FRAMES
            self.audio.play("shield_on")
            self.add_ring(cx, cy, color, grow=9.0, life=30)
            self.add_flash(70, color)
            self.burst(cx, cy, color, 24, speed=6.0, life=(16, 30))
        elif kind == "fish":
            self.fish.append({"owner": s, "x": float(cx + s.fwd * 30), "y": float(s.cy),
                              "vx": s.fwd * FISH_SPEED, "vy": 0.0, "life": FISH_LIFE, "t": 0})
            self.audio.play("wlee")
            self.later(18, lambda: self.audio.play("laugh"))
            self.later(18, lambda: self.add_text("HIHIHIHIHI!", SCREEN_W / 2, 380,
                                                 (255, 200, 120), 70, 60))
        elif kind == "light":
            s.light_t = LIGHT_FRAMES
            self.audio.play("light")
            self.add_flash(140, (255, 240, 120))
            self.add_ring(cx, cy, color, grow=14.0, life=30)
            self.burst(cx, cy, color, 40, speed=9.0, life=(16, 34))
        elif kind == "blackhole":
            self.start_blackhole(s, o)
        return True

    def start_blackhole(self, s, o):
        self.fish = []
        self.ball_electric = None
        x0 = s.rect.centerx + s.fwd * 40
        self.bh = {"user": s, "victim": o, "t": 0, "x": float(x0), "y": float(s.cy),
                   "x0": float(x0), "y0": float(s.cy),
                   "xv": float(o.rect.centerx), "yv": float(o.cy), "r": 6.0, "suck": 0.0,
                   "ball0": (self.ball_x, self.ball_y),
                   "v_pos": [(p.centerx, p.centery, p is not o.rect) for p in o.paddles()]}
        s.dark_t = BH_THROW + BH_SUCK + BH_HOLD
        self.audio.play("bh_throw")
        self.add_flash(120, (90, 20, 170))
        self.shake = max(self.shake, 8.0)

    def update_blackhole(self):
        bh = self.bh
        bh["t"] += 1
        t = bh["t"]
        user = bh["user"]
        if user.dark_t > 0:
            user.dark_t -= 1
        ucx, ucy = user.rect.center
        if t % 2 == 0:
            self.burst(ucx + random.uniform(-40, 40), ucy + random.uniform(-70, 70), (120, 40, 210),
                       2, speed=1.6, life=(18, 34), size=(4, 9))
        if t <= BH_THROW:
            k = t / BH_THROW
            e = k * k * (3 - 2 * k)
            bh["x"] = bh["x0"] + (bh["xv"] - bh["x0"]) * e
            bh["y"] = bh["y0"] + (bh["yv"] - bh["y0"]) * e
            bh["r"] = 6.0 + 16.0 * e
            self.burst(bh["x"], bh["y"], (170, 80, 255), 2, speed=2.0, life=(10, 18), size=(2, 4))
        elif t <= BH_THROW + BH_SUCK:
            k = (t - BH_THROW) / BH_SUCK
            bh["x"], bh["y"] = bh["xv"], bh["yv"]
            bh["r"] = 22.0 + (BH_MAX_R - 22.0) * (k ** 0.8)
            bh["suck"] = k * k
            if t == BH_THROW + 1:
                self.audio.play("bh_suck")
            for _ in range(3):
                a = random.uniform(0, math.tau)
                d = bh["r"] * random.uniform(1.4, 2.2)
                px = bh["x"] + math.cos(a) * d
                py = bh["y"] + math.sin(a) * d
                self.particles.append(Particle(
                    px, py, -math.cos(a) * d * 0.07 - math.sin(a) * 2.0,
                    -math.sin(a) * d * 0.07 + math.cos(a) * 2.0, 22, (190, 110, 255),
                    random.uniform(2, 4), 0.97, 0.0))
            self.shake = max(self.shake, 3.0 + 7.0 * k)
        else:
            j = t - (BH_THROW + BH_SUCK)
            bh["suck"] = 1.0
            if j == 1:
                self.add_text("YOUR EXISTENCE IS ERASED", SCREEN_W / 2, SCREEN_H / 2 + 170,
                              (255, 80, 160), 84, 120)
                self.audio.play("bh_erase")
                self.add_flash(180, (120, 40, 220))
                self.shake = 22.0
            shrink_start = BH_HOLD - 30
            if j > shrink_start:
                bh["r"] = BH_MAX_R * max(0.0, 1.0 - (j - shrink_start) / 30.0)
            else:
                bh["r"] = BH_MAX_R * (1.0 + 0.03 * math.sin(self.t * 0.5))
            if j >= BH_HOLD:
                pos = (bh["xv"], bh["yv"])
                self.bh = None
                self.score_point(user.name, at=pos)

    # ---------------------------------------------------------
    #  Ikan
    # ---------------------------------------------------------
    def fish_redirect(self, f, wall):
        if wall == "top":
            ang = random.uniform(0.15 * math.pi, 0.85 * math.pi)
        elif wall == "bottom":
            ang = random.uniform(-0.85 * math.pi, -0.15 * math.pi)
        elif wall == "left":
            ang = random.uniform(-0.4 * math.pi, 0.4 * math.pi)
        else:
            ang = random.uniform(0.6 * math.pi, 1.4 * math.pi)
        f["vx"] = math.cos(ang) * FISH_SPEED
        f["vy"] = math.sin(ang) * FISH_SPEED
        self.burst(f["x"], f["y"], (255, 190, 120), 6, speed=3.0, life=(10, 18))
        self.audio.play("wall")

    def update_fish(self):
        keep = []
        for f in self.fish:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            f["life"] -= 1
            f["t"] += 1
            if f["y"] < 18:
                f["y"] = 18.0
                self.fish_redirect(f, "top")
            elif f["y"] > SCREEN_H - 18:
                f["y"] = SCREEN_H - 18.0
                self.fish_redirect(f, "bottom")
            if f["x"] < 20:
                f["x"] = 20.0
                self.fish_redirect(f, "left")
            elif f["x"] > SCREEN_W - 20:
                f["x"] = SCREEN_W - 20.0
                self.fish_redirect(f, "right")
            victim = self.other(f["owner"])
            frect = pygame.Rect(0, 0, 52, 30)
            frect.center = (int(f["x"]), int(f["y"]))
            hit = False
            for p in victim.paddles():
                if frect.colliderect(p):
                    hit = True
                    break
            if hit:
                self.fish_hit(f, victim)
                continue
            if f["life"] <= 0:
                self.burst(f["x"], f["y"], (255, 190, 120), 14, speed=4.0, life=(12, 24))
                continue
            keep.append(f)
            if f["t"] % 3 == 0:
                self.burst(f["x"], f["y"], (255, 170, 90), 1, speed=1.0, life=(12, 20), size=(2, 4))
        self.fish = keep

    def fish_hit(self, f, victim):
        if victim.shield_t > 0:
            self.burst(f["x"], f["y"], SKILLS["shield"]["color"], 20, speed=6.0, life=(12, 26))
            self.add_ring(f["x"], f["y"], SKILLS["shield"]["color"], grow=6.0, life=18)
            self.audio.play("shield_hit")
            self.add_text("BLOCKED!", f["x"], f["y"] - 40, SKILLS["shield"]["color"], 56, 40)
            return
        victim.stun_t = STUN_FRAMES
        victim.vel = 0.0
        self.audio.play("fish_hit")
        self.later(6, lambda: self.audio.play("laugh"))
        self.burst(f["x"], f["y"], (255, 210, 120), 26, speed=7.0, life=(16, 32))
        self.add_ring(f["x"], f["y"], (255, 190, 90), grow=7.0, life=22)
        self.add_text("STUN!", f["x"], f["y"] - 50, (255, 230, 120), 64, 50)
        self.add_flash(60, (255, 200, 120))
        self.shake = max(self.shake, 8.0)

    # ---------------------------------------------------------
    #  Bola
    # ---------------------------------------------------------
    def update_ball(self):
        skin = SKINS[self.skin_idx]
        self.ball_x += self.bvx
        self.ball_y += self.bvy
        self.ball_trail.append((self.ball_x, self.ball_y))

        # pantulan dinding atas / bawah
        if self.ball_y - BALL_R <= 0:
            self.ball_y = BALL_R
            self.bvy = abs(self.bvy)
            self.wall_fx(0)
        elif self.ball_y + BALL_R >= SCREEN_H:
            self.ball_y = SCREEN_H - BALL_R
            self.bvy = -abs(self.bvy)
            self.wall_fx(SCREEN_H)

        self.ball_rect.center = (int(self.ball_x), int(self.ball_y))

        # tabrakan paddle (bola harus masih di depan paddle); paddle klon ikut menangkis
        hit_done = False
        for s in (self.player, self.cpu):
            if hit_done:
                break
            incoming = (self.bvx > 0) if s.is_player else (self.bvx < 0)
            if not incoming:
                continue
            for p in s.paddles():
                in_front = (self.ball_x <= p.centerx) if s.is_player else (self.ball_x >= p.centerx)
                if in_front and self.ball_rect.colliderect(p):
                    self.paddle_hit(s, p)
                    hit_done = True
                    break

        # efek di belakang bola
        if self.ball_electric is not None:
            self.burst(self.ball_x, self.ball_y, (180, 230, 255), 2, speed=4.0, life=(8, 16), size=(2, 4))
        elif skin["ball_style"] == "fire":
            self.burst(self.ball_x, self.ball_y, (255, random.randint(80, 170), 20), 2,
                       speed=2.0, life=(10, 18), size=(3, 6), angle=math.atan2(-self.bvy, -self.bvx),
                       spread=0.6)
        elif random.random() < 0.35:
            self.burst(self.ball_x, self.ball_y, skin["ball_glow"], 1, speed=1.5,
                       life=(10, 20), size=(2, 4))

        # garis kecepatan saat bola ngebut
        if self.ball_speed > 11 and random.random() < (self.ball_speed - 10) * 0.08:
            self.speed_lines.append([random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H),
                                     random.uniform(80, 220), random.uniform(18, 30)])

        # skor (NANO SHIELD memantulkan bola, tidak bisa kebobolan)
        if self.ball_x + BALL_R >= SCREEN_W:
            if self.player.shield_t > 0:
                self.shield_reflect(self.player)
            else:
                self.score_point("cpu")
        elif self.ball_x - BALL_R <= 0:
            if self.cpu.shield_t > 0:
                self.shield_reflect(self.cpu)
            else:
                self.score_point("player")

    def shield_reflect(self, s):
        color = SKILLS["shield"]["color"]
        self.ball_x = SCREEN_W - BALL_R - 2 if s.is_player else BALL_R + 2
        self.bvx = s.fwd * abs(self.bvx)
        self.ball_electric = None
        ex = SCREEN_W - 6 if s.is_player else 6
        self.add_ring(ex, self.ball_y, color, grow=9.0, life=26)
        self.burst(ex, self.ball_y, color, 24, speed=8.0, life=(14, 28),
                   angle=math.pi if s.is_player else 0.0, spread=1.2)
        self.add_flash(70, color)
        self.shake = max(self.shake, 8.0)
        self.audio.play("shield_hit")
        self.add_text("BLOCKED!", SCREEN_W / 2, SCREEN_H / 2 + 120, color, 64, 36)

    def wall_fx(self, wall_y):
        skin = SKINS[self.skin_idx]
        self.audio.play("wall")
        self.burst(self.ball_x, wall_y, skin["ball_glow"], 8, speed=4.0,
                   life=(10, 22), angle=math.pi / 2 if wall_y == 0 else -math.pi / 2, spread=1.0)
        self.shake = max(self.shake, 2.0)

    def paddle_hit(self, s, paddle):
        color = s.color
        offset = clamp((self.ball_y - paddle.centery) / (PADDLE_H / 2 + BALL_R), -1.0, 1.0)
        shot = s.armed
        if shot:
            s.armed = False
            self.ball_speed = LIGHTNING_SPEED
            self.ball_electric = s.name
        else:
            self.ball_speed = min(BALL_MAX_SPEED, self.ball_speed + BALL_SPEED_STEP)
            self.ball_electric = None
        self.rally += 1
        vy = math.sin(offset * 1.0) * self.ball_speed + s.vel * 0.35
        if shot:
            vy *= 0.5                                    # tembakan petir lebih lurus
        limit = self.ball_speed * 0.88
        vy = clamp(vy, -limit, limit)
        vx = math.sqrt(max(0.0, self.ball_speed ** 2 - vy ** 2))
        if s.is_player:
            self.ball_x = paddle.left - BALL_R
            contact_x = paddle.left
            ang = math.pi
        else:
            self.ball_x = paddle.right + BALL_R
            contact_x = paddle.right
            ang = 0.0
        if s.ctrl is not None:
            self.new_cpu_error()                         # AI membidik ulang setelah pukulan manusia
        self.bvx = s.fwd * vx
        self.bvy = vy
        s.glow = 15
        self.ball_rect.center = (int(self.ball_x), int(self.ball_y))

        if shot:
            bolt = SKILLS["lightning"]["color"]
            self.audio.play("thunder")
            self.burst(contact_x, self.ball_y, bolt, 40, speed=11.0, life=(14, 30), angle=ang, spread=1.3)
            self.add_ring(contact_x, self.ball_y, bolt, grow=12.0, life=26)
            self.add_ring(contact_x, self.ball_y, WHITE, grow=18.0, life=20)
            self.add_flash(170, (200, 235, 255))
            self.shake = max(self.shake, 16.0)
            self.hitstop = 5
            self.add_text("ZAP!!", self.ball_x, self.ball_y - 70, bolt, 80, 40)
            return

        self.audio.play("hit")
        self.burst(contact_x, self.ball_y, color, 16, speed=8.0, life=(14, 30), angle=ang, spread=1.1)
        self.burst(contact_x, self.ball_y, WHITE, 6, speed=5.0, life=(8, 16), size=(1, 3),
                   angle=ang, spread=0.8)
        self.add_ring(contact_x, self.ball_y, color, grow=5.0, life=18)
        self.add_flash(30 + int(self.ball_speed * 3), mix(color, WHITE, 0.5))
        self.shake = max(self.shake, 4.0 + self.ball_speed * 0.5)
        self.hitstop = 2
        if abs(offset) > 0.85 and self.ball_speed > 10:
            self.add_text("SMASH!", self.ball_x, self.ball_y - 60, color, 64, 36)
            self.shake = max(self.shake, 12.0)
            self.hitstop = 4

    def score_point(self, scorer, at=None):
        s = self.player if scorer == "player" else self.cpu
        color = s.color
        s.score += 1
        s.pulse = 24
        if at is not None:
            x, y = at
        else:
            x = 12 if scorer == "player" else SCREEN_W - 12
            y = self.ball_y
        self.audio.play("score_player" if s.ctrl is not None else "score_cpu")
        label = "POIN %s!" % s.display_name
        # ledakan di tepi layar tempat bola keluar
        self.burst(x, y, color, 70, speed=11.0, life=(25, 55), size=(2, 6))
        self.burst(x, y, WHITE, 24, speed=8.0, life=(15, 30), size=(1, 3))
        self.add_ring(x, y, color, grow=14.0, life=34)
        self.add_ring(x, y, WHITE, grow=9.0, life=26)
        self.add_flash(150, color)
        self.shake = 18.0
        self.hitstop = 8
        self.add_text(label, SCREEN_W / 2, SCREEN_H / 2, color, 96, 60)

        if s.score >= WIN_SCORE:
            self.end_match(scorer)
        else:
            self.start_serve(-1 if scorer == "player" else 1)

    def end_match(self, winner):
        self.clear_round_effects()
        self.winner = winner
        self.state = "gameover"
        self.serve_timer = 0
        self.bvx = self.bvy = 0.0
        self.audio.play("win" if (self.player if winner == "player" else self.cpu).ctrl is not None else "lose")
        self.audio.set_music_level(MUSIC_LEVELS["gameover"])
        color = (self.player if winner == "player" else self.cpu).color
        self.add_flash(200, color)
        for _ in range(4):
            self.burst(random.uniform(200, SCREEN_W - 200), random.uniform(150, 450),
                       random.choice((color, WHITE)), 40, speed=9.0, life=(30, 70), gravity=0.08)

    def spawn_confetti(self):
        if self.t % 2:
            return
        skin = SKINS[self.skin_idx]
        winner_side = self.player if self.winner == "player" else self.cpu
        palette = (winner_side.color, WHITE, skin["ball_glow"])
        for _ in range(3):
            self.particles.append(Particle(
                random.uniform(0, SCREEN_W), -10, random.uniform(-1.5, 1.5), random.uniform(2, 5),
                140, random.choice(palette), random.uniform(3, 6), 0.99, 0.06))

    def update_fx(self):
        self.spawn_ambient()
        for d in self.delayed:
            d[0] -= 1
        due = [d for d in self.delayed if d[0] <= 0]
        self.delayed = [d for d in self.delayed if d[0] > 0]
        for d in due:
            d[1]()

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        if len(self.particles) > 1600:
            self.particles = self.particles[-1600:]

        for r in self.rings:
            r[2] += r[3]
            r[5] -= 1
        self.rings = [r for r in self.rings if r[5] > 0]

        for tx in self.texts:
            tx["life"] -= 1
            tx["y"] -= 0.6
        self.texts = [tx for tx in self.texts if tx["life"] > 0]

        for sl in self.speed_lines:
            sl[0] += sl[3] * (-1 if self.bvx > 0 else 1)
        self.speed_lines = [sl for sl in self.speed_lines
                            if -300 < sl[0] < SCREEN_W + 300]

        self.flash_alpha *= 0.82
        if self.flash_alpha < 3:
            self.flash_alpha = 0.0
        self.shake *= 0.85
        if self.shake < 0.5:
            self.shake = 0.0
        for s in self.sides:
            if s.glow > 0:
                s.glow -= 1
            if s.pulse > 0:
                s.pulse -= 1

    # ---------------------------------------------------------
    #  Pengaturan, karakter, menu & map
    # ---------------------------------------------------------
    @staticmethod
    def clean_name(name):
        return "".join(ch for ch in name.upper() if ch.isalnum() or ch in " -_.")[:12]

    def load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:  # noqa: BLE001
            return
        if not isinstance(data, dict):
            return

        def pick(key, size, cur):
            v = data.get(key, cur)
            return v if (isinstance(v, int) and not isinstance(v, bool) and 0 <= v < size) else cur

        self.mode = pick("mode", 2, self.mode)
        self.map_idx = pick("map", len(MAPS), self.map_idx)
        self.skin_idx = pick("theme", len(SKINS), self.skin_idx)
        self.diff_idx = pick("diff", len(DIFFICULTIES), self.diff_idx)
        self.cskin_idx = pick("cskin", len(CHARACTERS) + 2, self.cskin_idx)
        if isinstance(data.get("skills"), bool):
            self.skills_on = data["skills"]
        for i, suf in ((0, ""), (1, "2")):          # pemain 1 memakai kunci lama (kompatibel)
            p = self.prof[i]
            p["skin"] = pick("pskin" + suf, len(CHARACTERS) + 1, p["skin"])
            p["head"] = pick("head" + suf, len(HEAD_ACCS), p["head"])
            p["chest"] = pick("chest" + suf, len(CHEST_ACCS), p["chest"])
            p["hand"] = pick("hand" + suf, len(HAND_ACCS), p["hand"])
            name = data.get("name" + suf)
            if isinstance(name, str):
                p["name"] = self.clean_name(name) or p["name"]

    def save_settings(self):
        data = {"mode": self.mode, "map": self.map_idx, "theme": self.skin_idx, "diff": self.diff_idx,
                "skills": self.skills_on, "cskin": self.cskin_idx}
        for i, suf in ((0, ""), (1, "2")):
            p = self.prof[i]
            data["name" + suf] = p["name"]
            data["pskin" + suf] = p["skin"]
            data["head" + suf] = p["head"]
            data["chest" + suf] = p["chest"]
            data["hand" + suf] = p["hand"]
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:  # noqa: BLE001
            pass

    def setup_sides(self):
        """Tentukan kontrol, nama, warna, dan tampilan (skin + aksesoris) kedua sisi.
        Sisi kiri = self.cpu (AI atau Pemain 1), sisi kanan = self.player (Pemain 2 / kamu)."""
        theme = SKINS[self.skin_idx]
        left, right = self.cpu, self.player
        p1, p2 = self.prof

        def char_of(idx):
            return CHARACTERS[idx - 1] if idx > 0 else None

        def look_of(ch, p):
            return (ch["id"] if ch else None, HEAD_ACCS[p["head"]][0], CHEST_ACCS[p["chest"]][0],
                    HAND_ACCS[p["hand"]][0])

        if self.mode == 1:                                   # 2 pemain: P1 kiri (W/S), P2 kanan (P/L)
            lch, rch = char_of(p1["skin"]), char_of(p2["skin"])
            left.ctrl, right.ctrl = CONTROLS_P1, CONTROLS_P2
            left.display_name = self.clean_name(p1["name"]).strip() or "PLAYER 1"
            right.display_name = self.clean_name(p2["name"]).strip() or "PLAYER 2"
            left.look = look_of(lch, p1)
            right.look = look_of(rch, p2)
        else:                                                # 1 pemain: kamu di kanan, AI di kiri
            rch = char_of(p1["skin"])
            if self.cskin_idx == 0:
                lch = None
            elif self.cskin_idx == 1:
                pool = [ch for ch in CHARACTERS if ch is not rch] or CHARACTERS
                lch = random.choice(pool)
            else:
                lch = CHARACTERS[self.cskin_idx - 2]
            left.ctrl, right.ctrl = None, CONTROLS_1P
            left.display_name = lch["name"] if lch else "AI"
            right.display_name = self.clean_name(p1["name"]).strip() or "PLAYER"
            right.look = look_of(rch, p1)
            if lch:
                left.look = (lch["id"],
                             random.choice(HEAD_ACCS)[0] if random.random() < 0.6 else "none",
                             random.choice(CHEST_ACCS)[0] if random.random() < 0.5 else "none",
                             random.choice(HAND_ACCS)[0] if random.random() < 0.7 else "none")
            else:
                left.look = PLAIN_LOOK
        left.color = lch["body"] if lch else theme["cpu"]
        right.color = rch["body"] if rch else theme["player"]
        if sum(abs(a - b) for a, b in zip(left.color, right.color)) < 90:
            left.color = mix(left.color, (255, 60, 60), 0.45)   # bedakan warna kalau terlalu mirip

    def preview_info(self):
        """(look, warna, flip, judul, subjudul) untuk panel pratinjau di menu."""
        theme = SKINS[self.skin_idx]
        if self.menu_page == 2 and self.mode == 0:
            if self.cskin_idx >= 2:
                ch = CHARACTERS[self.cskin_idx - 2]
                return ((ch["id"], "none", "none", "none"), ch["body"], False, ch["name"],
                        "Aksesoris CPU diacak tiap main")
            return PLAIN_LOOK, theme["cpu"], False, "ACAK" if self.cskin_idx == 1 else "AI", \
                "Lawan dikendalikan komputer"
        idx = 0 if self.menu_page != 2 else 1
        p = self.prof[idx]
        ch = CHARACTERS[p["skin"] - 1] if p["skin"] > 0 else None
        left = (self.mode == 1 and idx == 0)
        color = ch["body"] if ch else (theme["cpu"] if left else theme["player"])
        look = (ch["id"] if ch else None, HEAD_ACCS[p["head"]][0], CHEST_ACCS[p["chest"]][0],
                HAND_ACCS[p["hand"]][0])
        if self.mode == 1:
            sub = "Sisi KIRI  -  W / S + D" if left else "Sisi KANAN  -  P / L + K"
        else:
            sub = "Sisi KANAN  -  UP/DOWN + SPACE"
        default = "PLAYER 2" if idx == 1 else ("PLAYER 1" if self.mode == 1 else "PLAYER")
        return look, color, (not left), self.clean_name(p["name"]).strip() or default, sub

    def cpu_skin_label(self):
        if self.cskin_idx == 0:
            return "AI (TANPA SKIN)"
        if self.cskin_idx == 1:
            return "ACAK"
        return CHARACTERS[self.cskin_idx - 2]["name"]

    def get_bg(self):
        mid = MAPS[self.map_idx]["id"]
        key = (mid, self.skin_idx if mid == "arena" else 0)
        bg = self.bg_cache.get(key)
        if bg is None:
            bg = make_background(SKINS[self.skin_idx]) if mid == "arena" else MAP_BUILDERS[mid]()
            self.bg_cache[key] = bg
        return bg

    def get_thumb(self):
        key = (self.map_idx, self.skin_idx if MAPS[self.map_idx]["id"] == "arena" else 0)
        th = self.thumb_cache.get(key)
        if th is None:
            th = pygame.transform.smoothscale(self.get_bg(), (340, 213))
            self.thumb_cache[key] = th
        return th

    def map_accent(self):
        acc = MAPS[self.map_idx]["accent"]
        if acc is not None:
            return acc
        skin = SKINS[self.skin_idx]
        return mix(skin["player"], skin["cpu"], 0.5)

    def begin_match(self):
        for i, default in ((0, "PLAYER 1"), (1, "PLAYER 2")):
            p = self.prof[i]
            p["name"] = self.clean_name(p["name"]).strip() or default
        self.save_settings()
        self.start_match()

    def editing_name(self):
        if self.menu_page == 1:
            return self.menu_row == 0
        if self.menu_page == 2:
            return self.mode == 1 and self.menu_row == 0
        return False

    def page_rows(self):
        if self.menu_page == 2 and self.mode == 0:
            return 1
        return 5

    def menu_change(self, d):
        if self.menu_page == 0:
            r = self.menu_row
            if r == 0:
                self.mode = 1 - self.mode
            elif r == 1:
                self.map_idx = (self.map_idx + d) % len(MAPS)
            elif r == 2:
                self.skin_idx = (self.skin_idx + d) % len(SKINS)
            elif r == 3:
                if self.mode == 1:
                    return                                # level AI tidak berlaku di 2 pemain
                self.diff_idx = (self.diff_idx + d) % len(DIFFICULTIES)
            else:
                self.skills_on = not self.skills_on
        elif self.menu_page == 2 and self.mode == 0:
            self.cskin_idx = (self.cskin_idx + d) % (len(CHARACTERS) + 2)
        else:
            p = self.prof[self.menu_page - 1]
            r = self.menu_row
            if r == 1:
                p["skin"] = (p["skin"] + d) % (len(CHARACTERS) + 1)
            elif r == 2:
                p["head"] = (p["head"] + d) % len(HEAD_ACCS)
            elif r == 3:
                p["chest"] = (p["chest"] + d) % len(CHEST_ACCS)
            elif r == 4:
                p["hand"] = (p["hand"] + d) % len(HAND_ACCS)
            else:
                return
        self.audio.play("move")

    # ---------------------------------------------------------
    #  Event map
    # ---------------------------------------------------------
    def update_map(self):
        m = MAPS[self.map_idx]
        if m["id"] == "arena" or self.serve_timer > 0:
            return
        self.map_timer -= 1
        if self.map_timer <= 0:
            self.map_timer = m["interval"] * FPS
            self.trigger_event(m["id"])
        self.hz_new = []
        keep = []
        for h in self.hazards:
            if getattr(self, "_hz_" + h["type"])(h):
                keep.append(h)
        self.hazards = keep + self.hz_new
        self.hz_new = []

    def trigger_event(self, mid):
        accent = MAPS[self.map_idx]["accent"] or WHITE
        if mid == "highway":
            kind = random.choice(("truck", "car"))
            direction = random.choice((-1, 1))
            w, h = (260, 78) if kind == "truck" else (150, 58)
            self.hazards.append({
                "type": "vehicle", "kind": kind, "dir": direction, "w": w, "h": h,
                "x": float(-w if direction > 0 else SCREEN_W + w), "y": float(random.choice(ROAD_LANES)),
                "speed": 20.0 if kind == "truck" else 26.0, "warn": 70, "hit": set(),
                "color": random.choice(((200, 50, 40), (60, 120, 210), (230, 190, 50),
                                        (70, 170, 90), (180, 180, 190)))})
            self.add_text("AWAS! KENDARAAN MELINTAS!", SCREEN_W / 2, 250, accent, 64, 70)
            self.audio.play("horn")
        elif mid == "volcano":
            sides = random.choice(((self.cpu, self.player), (self.cpu,), (self.player,)))
            for s in sides:
                self.hazards.append({"type": "lava", "x": float(s.rect.centerx), "side": s, "t": 0,
                                     "h": random.uniform(260, 480), "cur": 0.0, "decor": False})
            for _ in range(2):
                self.hazards.append({"type": "lava", "x": random.uniform(260, SCREEN_W - 260), "side": None,
                                     "t": random.randint(-20, 0), "h": random.uniform(120, 260),
                                     "cur": 0.0, "decor": True})
            self.add_text("LAVA MENYEMBUR!", SCREEN_W / 2, 250, accent, 70, 70)
        elif mid == "market":
            self.add_text("AWAS! LEMPARAN PASAR!", SCREEN_W / 2, 250, accent, 64, 70)
            for i in range(3):
                self.throw_item(random.choice(MARKET_ITEMS), random.choice(self.sides), i * 16)
        elif mid == "lab":
            self.add_text("AWAS! BOTOL RACIKAN!", SCREEN_W / 2, 250, accent, 64, 70)
            self.throw_item("chem%d" % random.randint(0, 2), random.choice(self.sides), 0)
        elif mid == "war":
            x = random.choice(self.sides).rect.centerx if random.random() < 0.3 \
                else random.uniform(120, SCREEN_W - 120)
            self.hazards.append({"type": "shell", "x": float(x), "y": -80.0, "vy": 12.0})
            self.add_text("SERANGAN TANK!", SCREEN_W / 2, 250, accent, 70, 70)
            self.audio.play("whistle")

    # --- kendaraan ---
    def _hz_vehicle(self, v):
        if v["warn"] > 0:
            v["warn"] -= 1
            if v["warn"] == 0:
                self.audio.play("vroom")
            return True
        v["x"] += v["dir"] * v["speed"]
        rect = pygame.Rect(0, 0, v["w"], v["h"])
        rect.center = (int(v["x"]), int(v["y"]))
        for s in self.sides:
            if s.name in v["hit"]:
                continue
            for p in s.paddles():
                if rect.colliderect(p):
                    v["hit"].add(s.name)
                    self.hit_stun(s, ROAD_STUN_FRAMES, "TERTABRAK!", (255, 200, 60))
                    break
        if (v["dir"] > 0 and v["x"] > SCREEN_W + v["w"]) or (v["dir"] < 0 and v["x"] < -v["w"]):
            return False
        return True

    # --- lava ---
    def _hz_lava(self, lv):
        lv["t"] += 1
        t = lv["t"]
        if t < 0:
            return True
        x = lv["x"]
        if t == 1:
            self.audio.play("rumble")
        if t < LAVA_WARN:
            lv["cur"] = 0.0
            if t % 5 == 0:
                self.burst(x + random.uniform(-30, 30), SCREEN_H - 6, (255, 120, 30), 2, speed=3.0,
                           life=(10, 20), angle=-math.pi / 2, spread=0.8)
            return True
        u = t - LAVA_WARN
        rise, fall = 22, 26
        hh = lv["h"]
        if u < rise:
            h = hh * (u / rise) ** 0.6
        elif u < rise + LAVA_HOLD:
            h = hh
        elif u < rise + LAVA_HOLD + fall:
            h = hh * (1.0 - (u - rise - LAVA_HOLD) / fall)
        else:
            return False
        lv["cur"] = h
        if u == 1:
            self.audio.play("erupt")
            self.shake = max(self.shake, 10.0)
            self.add_flash(70, (255, 120, 30))
        if h > 12 and t % 2 == 0:
            self.burst(x + random.uniform(-35, 35), SCREEN_H - h, (255, random.randint(110, 200), 30), 2,
                       speed=5.0, life=(14, 30), size=(2, 4), angle=-math.pi / 2, spread=0.9)
        s = lv["side"]
        if s is not None and h > 8:
            lrect = pygame.Rect(int(x - 45), int(SCREEN_H - h), 90, int(h) + 1)
            for p in s.paddles():
                if lrect.colliderect(p):
                    self.apply_lava(s)
                    break
        return True

    # --- lemparan pasar / botol kimia ---
    def throw_item(self, kind, victim, delay):
        def go():
            sx = random.uniform(260, SCREEN_W - 260)
            T = random.randint(55, 70)
            ty = clamp(victim.cy + victim.vel * T * 0.5, 70, SCREEN_H - 70)
            self.hazards.append({"type": "thrown", "kind": kind, "sx": sx, "sy": 70.0,
                                 "tx": float(victim.rect.centerx), "ty": float(ty), "t": 0, "T": T,
                                 "arc": random.choice((-120.0, 120.0)), "x": sx, "y": 70.0,
                                 "rot": 0.0, "spin": random.uniform(-14.0, 14.0)})
            self.audio.play("throw")
        if delay <= 0:
            go()
        else:
            self.later(delay, go)

    def _hz_thrown(self, h):
        h["t"] += 1
        u = min(1.0, h["t"] / h["T"])
        h["x"] = h["sx"] + (h["tx"] - h["sx"]) * u
        h["y"] = h["sy"] + (h["ty"] - h["sy"]) * u - h["arc"] * 4.0 * u * (1.0 - u)
        h["rot"] += h["spin"]
        rect = pygame.Rect(0, 0, 38, 38)
        rect.center = (int(h["x"]), int(h["y"]))
        if h["t"] > 8:
            for s in self.sides:
                for p in s.paddles():
                    if rect.colliderect(p):
                        self.thrown_hit(h, s)
                        return False
        if u >= 1.0:
            self.splat(h["x"], h["y"], h["kind"])
            return False
        return True

    def splat(self, x, y, kind):
        col = ITEM_COLORS.get(kind) or CHEM_COLORS.get(kind, WHITE)
        self.burst(x, y, col, 18, speed=5.0, life=(14, 30))
        self.add_ring(x, y, col, grow=5.0, life=16)
        self.audio.play("glass" if kind.startswith("chem") else "splat")

    def thrown_hit(self, h, s):
        kind = h["kind"]
        cx, cy = s.rect.center
        col = ITEM_COLORS.get(kind) or CHEM_COLORS.get(kind, WHITE)
        if kind.startswith("chem"):
            s.dizzy_t = DIZZY_FRAMES
            self.burst(cx, cy, col, 30, speed=4.0, life=(40, 70), size=(8, 16))
            self.add_text("PUSING! KONTROL TERBALIK", cx + s.fwd * 260, cy - 60, col, 50, 80)
            self.audio.play("glass")
        else:
            s.lock_t = LOCK_FRAMES
            self.burst(cx, cy, col, 26, speed=6.0, life=(14, 30))
            self.add_text("SKILL TERKUNCI 8 DTK!", cx + s.fwd * 260, cy - 60, col, 50, 80)
            self.audio.play("splat")
        self.add_ring(cx, cy, col, grow=8.0, life=22)
        self.add_flash(70, col)
        self.shake = max(self.shake, 8.0)

    # --- peluru tank & bom kecil ---
    def _hz_shell(self, sh):
        sh["vy"] += 0.28
        sh["y"] += sh["vy"]
        if self.t % 2 == 0:
            self.burst(sh["x"], sh["y"] - 40, (255, 150, 40), 1, speed=1.5, life=(10, 18), size=(3, 5))
        rect = pygame.Rect(0, 0, 26, 66)
        rect.center = (int(sh["x"]), int(sh["y"]))
        for s in self.sides:
            for p in s.paddles():
                if rect.colliderect(p):
                    self.shell_explode(sh["x"], sh["y"], s)
                    return False
        if sh["y"] >= SCREEN_H - 24:
            self.shell_explode(sh["x"], SCREEN_H - 24, None)
            return False
        return True

    def shell_explode(self, x, y, direct):
        self.audio.play("boom")
        self.burst(x, y, (255, 160, 50), 60, speed=12.0, life=(20, 50), size=(3, 7))
        self.burst(x, y, (255, 240, 180), 20, speed=8.0, life=(10, 24), size=(2, 4))
        self.add_ring(x, y, (255, 170, 60), grow=14.0, life=30)
        self.add_ring(x, y, WHITE, grow=9.0, life=22)
        self.add_flash(120, (255, 190, 90))
        self.shake = max(self.shake, 18.0)
        for _ in range(8):
            ang = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
            spd = random.uniform(7.0, 13.0)
            self.hz_new.append({"type": "bomb", "x": float(x), "y": float(y - 10),
                                "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd, "life": 300})
        if direct is not None:
            self.apply_bleed(direct)

    def pop_bomb(self, b):
        self.burst(b["x"], b["y"], (255, 170, 60), 14, speed=6.0, life=(10, 24))
        self.add_ring(b["x"], b["y"], (255, 170, 60), grow=5.0, life=14)
        self.audio.play("pop")

    def _hz_bomb(self, b):
        b["life"] -= 1
        b["vy"] += 0.35
        b["x"] += b["vx"]
        b["y"] += b["vy"]
        r = 9
        if b["y"] > SCREEN_H - r:
            b["y"] = float(SCREEN_H - r)
            b["vy"] = -abs(b["vy"]) * 0.72
            if b["vy"] > -4.0:
                b["vy"] = -random.uniform(5.0, 10.0)
            b["vx"] = clamp(b["vx"] + random.uniform(-2.5, 2.5), -9.0, 9.0)
            self.burst(b["x"], SCREEN_H - 4, (180, 150, 110), 4, speed=2.5, life=(10, 18))
        elif b["y"] < r:
            b["y"] = float(r)
            b["vy"] = abs(b["vy"])
        if b["x"] < r:
            b["x"] = float(r)
            b["vx"] = abs(b["vx"]) + random.uniform(0, 1.5)
        elif b["x"] > SCREEN_W - r:
            b["x"] = float(SCREEN_W - r)
            b["vx"] = -abs(b["vx"]) - random.uniform(0, 1.5)
        rect = pygame.Rect(0, 0, 2 * r, 2 * r)
        rect.center = (int(b["x"]), int(b["y"]))
        for s in self.sides:
            for p in s.paddles():
                if rect.colliderect(p):
                    self.pop_bomb(b)
                    self.apply_bleed(s)
                    return False
        if b["life"] <= 0:
            self.pop_bomb(b)
            return False
        return True

    # --- efek status dari event map ---
    def hit_stun(self, s, frames, text, color):
        s.stun_t = max(s.stun_t, frames)
        s.vel = 0.0
        cx, cy = s.rect.center
        self.burst(cx, cy, color, 30, speed=8.0, life=(14, 30))
        self.add_ring(cx, cy, color, grow=9.0, life=24)
        self.add_flash(110, color)
        self.shake = max(self.shake, 14.0)
        self.add_text(text, cx + s.fwd * 170, cy - 60, color, 60, 55)
        self.audio.play("crash")

    def apply_lava(self, s):
        if s.lava_t <= 0:
            cx, cy = s.rect.center
            self.burst(cx, cy, (255, 130, 30), 24, speed=6.0, life=(14, 30))
            self.add_text("LAVA! LAMBAT 0,5x", cx + s.fwd * 190, cy - 60, (255, 140, 40), 52, 60)
            self.audio.play("sizzle")
        s.lava_t = LAVA_SLOW_FRAMES

    def strip_skills(self, s):
        """Bleeding: skill yang dimiliki maupun yang sedang aktif hilang."""
        o = self.other(s)
        s.slot = None
        s.armed = False
        s.clone_t = 0
        s.shield_t = 0
        s.light_t = 0
        s.light_hist.clear()
        if s.time_t > 0:
            s.time_t = 0
            o.slow_t = 0

    def apply_bleed(self, s):
        self.strip_skills(s)
        s.stun_t = max(s.stun_t, BLEED_STUN)
        s.bleed_t = BLEED_FRAMES
        s.vel = 0.0
        cx, cy = s.rect.center
        self.burst(cx, cy, (230, 30, 50), 36, speed=7.0, life=(20, 44), size=(2, 5), gravity=0.2)
        self.add_ring(cx, cy, (230, 30, 50), grow=8.0, life=24)
        self.add_flash(100, (200, 20, 40))
        self.shake = max(self.shake, 12.0)
        self.add_text("BLEEDING!", cx + s.fwd * 170, cy - 60, (255, 70, 90), 60, 60)
        self.audio.play("bleed")

    def spawn_ambient(self):
        mid = MAPS[self.map_idx]["id"]
        if mid == "volcano" and random.random() < 0.4:
            self.particles.append(Particle(random.uniform(0, SCREEN_W), SCREEN_H + 5, random.uniform(-0.6, 0.6),
                                           -random.uniform(1.0, 2.6), 140, (255, random.randint(90, 160), 30),
                                           random.uniform(1.5, 3.2), 0.995, -0.004))
        elif mid == "war" and random.random() < 0.25:
            self.particles.append(Particle(random.uniform(0, SCREEN_W), -5, random.uniform(-1.2, 0.2),
                                           random.uniform(0.6, 1.6), 200, (110, 100, 95),
                                           random.uniform(1.5, 3.0), 0.998, 0.0))
        elif mid == "lab" and random.random() < 0.3:
            self.particles.append(Particle(random.choice((170, 1110)) + random.uniform(-14, 14), 600,
                                           random.uniform(-0.2, 0.2), -random.uniform(0.8, 1.6), 120,
                                           (80, 255, 170), random.uniform(2.0, 4.0), 0.999, 0.0))
        elif mid == "market" and random.random() < 0.2:
            self.particles.append(Particle(random.uniform(0, SCREEN_W), random.uniform(40, 250),
                                           random.uniform(-0.3, 0.3), random.uniform(0.1, 0.5), 80,
                                           (255, 220, 130), random.uniform(1.5, 2.5), 0.99, 0.0))

    # ---------------------------------------------------------
    #  Gambar
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    #  Gambar: hazard map, dekorasi, halaman menu
    # ---------------------------------------------------------
    def draw_hazards(self, cv, fx):
        for h in self.hazards:
            getattr(self, "_draw_" + h["type"])(cv, fx, h)

    def _draw_vehicle(self, cv, fx, v):
        x, y, d = v["x"], v["y"], v["dir"]
        col = v["color"]
        if v["warn"] > 0:
            pulse = 0.5 + 0.5 * math.sin(self.t * 0.5)
            pygame.draw.rect(fx, scale_color((200, 20, 20), 0.35 * pulse), pygame.Rect(0, int(y - 54), SCREEN_W, 108))
            ex = 60 if d > 0 else SCREEN_W - 60
            draw_text(cv, "!", 120, (255, 80, 60), (ex, y), glow=(255, 60, 40))
            return

        def box(color, dx, dy, w, h, radius=0):
            left = x + dx if d > 0 else x - dx - w
            pygame.draw.rect(cv, color, pygame.Rect(int(left), int(y + dy), int(w), int(h)), border_radius=radius)

        def wheel(dx, dy):
            wx = int(x + d * dx)
            pygame.draw.circle(cv, (18, 18, 22), (wx, int(y + dy)), 15)
            pygame.draw.circle(cv, (150, 150, 160), (wx, int(y + dy)), 7)

        if v["kind"] == "truck":
            box((200, 200, 210), -130, -39, 170, 70, 4)
            box((120, 120, 135), -130, -39, 170, 8, 2)
            box(col, 45, -26, 80, 57, 8)
            box((150, 210, 240), 88, -20, 30, 20, 3)
            wheel(-90, 38)
            wheel(-40, 38)
            wheel(85, 38)
            head = x + d * 126
        else:
            box(col, -75, -10, 150, 34, 8)
            box(scale_color(col, 0.75), -30, -32, 78, 26, 8)
            box((150, 210, 240), -22, -28, 25, 18, 3)
            box((150, 210, 240), 8, -28, 30, 18, 3)
            wheel(-42, 26)
            wheel(45, 26)
            head = x + d * 74
        draw_glow(fx, (head, y + 10), 90, (255, 230, 150), 0.75)
        pygame.draw.polygon(fx, (70, 62, 34), [(head, y + 4), (head + d * 220, y - 46), (head + d * 220, y + 64)])

    def _draw_lava(self, cv, fx, lv):
        if lv["t"] < 0:
            return
        x = int(lv["x"])
        hot = (255, 120, 30)
        if lv["t"] < LAVA_WARN:
            pulse = 0.5 + 0.5 * math.sin(self.t * 0.6)
            draw_glow(fx, (x, SCREEN_H - 6), 90, hot, 0.5 + 0.5 * pulse)
            for k in range(-2, 3):
                pygame.draw.line(fx, scale_color(hot, 0.5 + 0.5 * pulse), (x + k * 14, SCREEN_H),
                                 (x + k * 14 + 6, SCREEN_H - 22 - abs(k) * 3), 3)
            if not lv["decor"]:
                draw_text(cv, "!", 90, (255, 150, 50), (x + (60 if x < SCREEN_W / 2 else -60), SCREEN_H - 70),
                          glow=hot)
            return
        h = int(lv["cur"])
        if h < 4:
            return
        w = 70 if lv["decor"] else 90
        top = SCREEN_H - h
        pygame.draw.rect(cv, (200, 60, 15), pygame.Rect(x - w // 2, top, w, h))
        pygame.draw.rect(cv, (255, 130, 30), pygame.Rect(x - w // 2 + 8, top, w - 16, h))
        pygame.draw.rect(cv, (255, 215, 90), pygame.Rect(x - w // 4, top, w // 2, h))
        for i in range(5):
            bx = x - w // 2 + i * w // 4
            by = top + int(math.sin(self.t * 0.3 + i * 1.7) * 5)
            pygame.draw.circle(cv, (255, 150, 40), (bx, by), 14)
        draw_glow(fx, (x, top + 40), 120, hot, 0.75)
        draw_glow(fx, (x, SCREEN_H - 20), 140, hot, 0.5)

    def _draw_thrown(self, cv, fx, h):
        spr = get_item_sprite(h["kind"])
        img = pygame.transform.rotozoom(spr, h["rot"], 1.0)
        cv.blit(img, img.get_rect(center=(int(h["x"]), int(h["y"]))))
        col = ITEM_COLORS.get(h["kind"]) or CHEM_COLORS.get(h["kind"], WHITE)
        draw_glow(fx, (h["x"], h["y"]), 40, col, 0.5)
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.5)
        pygame.draw.circle(fx, scale_color((200, 40, 40), 0.4 + 0.4 * pulse), (int(h["tx"]), int(h["ty"])), 30, 2)

    def _draw_shell(self, cv, fx, sh):
        x, y = int(sh["x"]), int(sh["y"])
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.5)
        pygame.draw.circle(fx, scale_color((200, 40, 30), 0.4 + 0.4 * pulse), (x, SCREEN_H - 14), 34 + int(6 * pulse), 3)
        pygame.draw.line(fx, (50, 14, 10), (x, 0), (x, SCREEN_H), 1)
        pygame.draw.polygon(cv, (120, 125, 115), [(x - 9, y - 34), (x + 9, y - 34), (x + 9, y + 16),
                                                  (x, y + 34), (x - 9, y + 16)])
        pygame.draw.rect(cv, (200, 160, 60), pygame.Rect(x - 9, y - 6, 18, 6))
        draw_glow(fx, (x, y - 40), 50, (255, 150, 40), 0.75)
        pygame.draw.polygon(fx, (255, 140, 30), [(x - 7, y - 34), (x + 7, y - 34), (x, y - 70)])

    def _draw_bomb(self, cv, fx, b):
        x, y = int(b["x"]), int(b["y"])
        pygame.draw.circle(cv, (40, 42, 40), (x, y), 9)
        pygame.draw.circle(cv, (90, 94, 90), (x, y), 9, 2)
        blink = (self.t // 6) % 2 == 0
        pygame.draw.circle(cv, (255, 60, 40) if blink else (120, 20, 15), (x + 2, y - 2), 3)
        if blink:
            draw_glow(fx, (x, y), 30, (255, 80, 40), 0.5)

    def draw_map_decor(self, cv, fx):
        mid = MAPS[self.map_idx]["id"]
        t = self.t
        if mid == "highway":
            for lx in range(160, SCREEN_W, 320):
                draw_glow(fx, (lx + 20, 206), 70, (255, 210, 110), 0.5 + 0.25 * math.sin(t * 0.07 + lx))
        elif mid == "volcano":
            draw_glow(fx, (SCREEN_W // 2, SCREEN_H), 300, (140, 40, 10), 0.5 + 0.25 * math.sin(t * 0.05))
            draw_glow(fx, (650, 215), 130, (200, 80, 20), 0.5 + 0.25 * math.sin(t * 0.09))
        elif mid == "market":
            for i, xx in enumerate(range(30, SCREEN_W, 70)):
                yy = 58 + int(22 * math.sin(xx * 0.012))
                draw_glow(fx, (xx, yy + 8), 40, (255, 200, 110), 0.5 + 0.25 * math.sin(t * 0.1 + i))
        elif mid == "lab":
            for tx in (170, 1110):
                draw_glow(fx, (tx, 500), 110, (40, 200, 120), 0.4 + 0.2 * math.sin(t * 0.08 + tx))
        elif mid == "war":
            for k, ax in enumerate((240, 1040)):
                ang = math.sin(t * 0.012 + k * 2.0) * 0.5
                tip = ax + math.tan(ang) * (SCREEN_H + 100)
                pygame.draw.polygon(fx, (30, 30, 22), [(ax - 12, SCREEN_H - 20), (ax + 12, SCREEN_H - 20),
                                                       (int(tip + 90), -100), (int(tip - 90), -100)])

    def draw_menu_match(self, cv, acc):
        m = MAPS[self.map_idx]
        thumb = self.get_thumb()
        r = thumb.get_rect(center=(SCREEN_W // 2, 372))
        pygame.draw.rect(cv, acc, r.inflate(10, 10), 3, border_radius=10)
        cv.blit(thumb, r)
        draw_text(cv, m["name"], 36, WHITE, (SCREEN_W // 2, 498), glow=acc)
        draw_text(cv, m["desc"], 22, (210, 210, 225), (SCREEN_W // 2, 526))
        mode_txt = "2 PEMAIN (VERSUS)" if self.mode == 1 else "1 PEMAIN (VS AI)"
        level_txt = "-  (hanya 1 pemain)" if self.mode == 1 else DIFFICULTIES[self.diff_idx]["name"]
        rows = (("MODE", mode_txt), ("MAP", m["name"]), ("TEMA / BOLA", SKINS[self.skin_idx]["name"]),
                ("LEVEL", level_txt), ("SKILL", "ON" if self.skills_on else "OFF"))
        for i, (label, value) in enumerate(rows):
            sel = (i == self.menu_row)
            text = "<   %s :  %s   >" % (label, value) if sel else "%s :  %s" % (label, value)
            draw_text(cv, text, 34, WHITE if sel else (130, 130, 150), (SCREEN_W // 2, 565 + i * 40),
                      glow=acc if sel else None)
        if self.mode == 1:
            ctrl_txt = "P1 (kiri): W / S + D skill     |     P2 (kanan): P / L + K skill     |     ESC = Pause"
        else:
            ctrl_txt = "UP / DOWN atau W / S + SPACE skill     |     P / ESC = Pause"
        draw_text(cv, ctrl_txt, 24, (190, 190, 210), (SCREEN_W // 2, 757))

    def draw_menu_char(self, cv, acc):
        if self.menu_page == 2 and self.mode == 0:
            rows = (("SKIN CPU", self.cpu_skin_label()),)
        else:
            p = self.prof[self.menu_page - 1]
            blink = (self.t // 25) % 2 == 0 and self.menu_row == 0
            pname = "TANPA SKIN" if p["skin"] == 0 else CHARACTERS[p["skin"] - 1]["name"]
            rows = (("NAMA", p["name"] + ("_" if blink else " ")), ("SKIN", pname),
                    ("KEPALA", HEAD_ACCS[p["head"]][1]), ("DADA", CHEST_ACCS[p["chest"]][1]),
                    ("TANGAN", HAND_ACCS[p["hand"]][1]))
        for i, (label, value) in enumerate(rows):
            sel = (i == self.menu_row)
            if label == "NAMA":
                text = "%s :  %s" % (label, value)
            else:
                text = "<   %s :  %s   >" % (label, value) if sel else "%s :  %s" % (label, value)
            draw_text(cv, text, 38, WHITE if sel else (130, 130, 150), (400, 330 + i * 62),
                      glow=acc if sel else None)
        if self.editing_name():
            draw_text(cv, "Ketik nama (maks 12 karakter)  -  BACKSPACE untuk menghapus", 24, (150, 150, 175),
                      (400, 720))
        panel = pygame.Rect(0, 0, 380, 470)
        panel.center = (1000, 520)
        pygame.draw.rect(cv, (14, 14, 26), panel, border_radius=16)
        pygame.draw.rect(cv, acc, panel, 3, border_radius=16)
        look, color, flip, title, sub = self.preview_info()
        try:
            spr = get_paddle_composite(look, color, flip, 0)
            big = pygame.transform.rotozoom(spr, 0, 2.4)
            cv.blit(big, big.get_rect(center=(panel.centerx, panel.centery + 14)))
        except Exception:  # noqa: BLE001
            pass
        draw_text(cv, title, 40, WHITE, (panel.centerx, panel.top + 34), glow=color)
        draw_text(cv, sub, 24, (190, 190, 210), (panel.centerx, panel.bottom - 24))

    def draw_stars(self, cv):
        for x, y, spd, size, ph in self.stars:
            v = int(90 + 70 * math.sin(self.t * 0.05 + ph))
            pygame.draw.rect(cv, (v, v, v), (int(x), int(y), size, size))

    def draw_center_line(self, cv, skin):
        col = scale_color(mix(skin["player"], skin["cpu"], 0.5), 0.45 + 0.15 * math.sin(self.t * 0.08))
        for y in range(10, SCREEN_H, 40):
            pygame.draw.line(cv, col, (SCREEN_W // 2, y), (SCREEN_W // 2, y + 20), 4)
        pygame.draw.circle(cv, col, (SCREEN_W // 2, SCREEN_H // 2), 110, 2)
        pygame.draw.circle(cv, col, (SCREEN_W // 2, SCREEN_H // 2), 8)

    def draw_arena(self, cv, fx, skin):
        # garis lintasan paddle (tempat mystery box muncul)
        for s in self.sides:
            x = s.rect.centerx
            col = scale_color(s.color, 0.22)
            pygame.draw.line(cv, col, (x, 0), (x, SCREEN_H), 2)
            for y in range(0, SCREEN_H, 40):
                pygame.draw.line(cv, col, (x - 6, y), (x + 6, y), 1)
        # tepi neon
        edge = scale_color(self.map_accent(), 0.75)
        for y in (3, SCREEN_H - 4):
            pygame.draw.line(fx, edge, (0, y), (SCREEN_W, y), 4)
        for x0, sx in ((0, 1), (SCREEN_W - 1, -1)):
            for y0, sy in ((0, 1), (SCREEN_H - 1, -1)):
                pygame.draw.line(fx, edge, (x0, y0), (x0 + sx * 70, y0), 5)
                pygame.draw.line(fx, edge, (x0, y0), (x0, y0 + sy * 70), 5)

    def draw_ball_trail(self, fx, trail, color):
        n = len(trail)
        prev = None
        for i, (x, y) in enumerate(trail):
            f = (i + 1) / n
            r = max(2, int(BALL_R * (0.35 + 0.65 * f)))
            col = scale_color(color, 0.35 * f)
            pos = (int(x), int(y))
            if prev is not None:
                pygame.draw.line(fx, col, prev, pos, r * 2)
            pygame.draw.circle(fx, col, pos, r)
            prev = pos

    def draw_paddle_trail(self, fx, hist, color):
        n = len(hist)
        if n < 2 or hist[0] == hist[-1]:
            return
        for i, (x, y) in enumerate(hist):
            f = (i + 1) / n
            pygame.draw.rect(fx, scale_color(color, 0.20 * f),
                             pygame.Rect(x, y, PADDLE_W, PADDLE_H), border_radius=8)

    def draw_paddle(self, cv, fx, rect, color, glow_t=0, dim=0.0, glow_scale=1.0,
                    look=None, flip=False, clone=False):
        level = min(3, glow_t // 4)
        orig = color
        if clone:
            color = clone_color(color)
        base = color if dim <= 0 else mix(color, (110, 115, 135), dim)
        cx = rect.centerx
        gr = 55 + (glow_t // 5) * 10
        flash = glow_t / 15.0
        for gy in (rect.top + 14, rect.centery, rect.bottom - 14):
            draw_glow(fx, (cx, gy), gr, base, (0.6 + flash * 0.4) * glow_scale)
        pygame.draw.rect(fx, scale_color(base, 0.30 * glow_scale), rect, border_radius=8)
        if look is not None and look != PLAIN_LOOK and self.comp_ok:
            try:
                variant = 2 if clone else (1 if dim > 0 else 0)
                spr = get_paddle_composite(look, orig, flip, variant)
                cv.blit(spr, (rect.x - MX, rect.y - MT))
                return
            except Exception as e:  # noqa: BLE001
                self.comp_ok = False
                print("Skin karakter dimatikan karena error:", e)
        cv.blit(get_paddle_sprite(base, level), (rect.x - PAD, rect.y - PAD))

    def draw_sucked(self, cv, spr, p0, center, k, spin=1.0):
        if k >= 0.97:
            return
        px, py = spiral_pos(p0, center, k)
        img = pygame.transform.rotozoom(spr, -math.degrees(k * 7.0 * spin), max(0.05, 1.0 - k))
        cv.blit(img, img.get_rect(center=(int(px), int(py))))

    def draw_side_paddles(self, cv, fx, s, skin):
        color = s.color
        if self.bh is not None and self.bh["victim"] is s:
            hole = (self.bh["x"], self.bh["y"])
            k = self.bh["suck"]
            for cx, cy, is_clone in self.bh["v_pos"]:
                c = clone_color(color) if is_clone else color
                self.draw_sucked(cv, get_paddle_sprite(c, 0), (cx, cy), hole, k)
            return
        dim = 0.0
        if s.slow_t > 0:
            dim = 0.35
        if s.stun_t > 0 and (self.t // 4) % 2 == 0:
            dim = 0.6
        self.draw_paddle(cv, fx, s.rect, color, s.glow, dim, 1.0, s.look, s.is_player, False)
        if s.clone_t > 0:
            blink = s.clone_t < 60 and (s.clone_t // 5) % 2 == 0
            if not blink:
                self.draw_paddle(cv, fx, s.clone_rect, color, s.glow, dim, 0.6, s.look, s.is_player, True)

    def render_ball(self, cv, fx, skin, x, y):
        ix, iy = int(x), int(y)
        glow = skin["ball_glow"]
        if self.ball_electric is not None:
            glow = SKILLS["lightning"]["color"]
        pulse = 0.8 + 0.2 * math.sin(self.t * 0.2)
        draw_glow(fx, (ix, iy), 70, glow, pulse)
        draw_glow(fx, (ix, iy), 34, skin["ball"], 0.7)
        style = skin["ball_style"]
        spr = get_ball_sprite(skin)
        if style == "fire":
            img = pygame.transform.rotozoom(spr, (self.t * 4) % 360, 1.0 + 0.05 * math.sin(self.t * 0.5))
        else:
            img = spr
        cv.blit(img, img.get_rect(center=(ix, iy)))
        if style == "ring":
            for k in range(3):
                a = self.t * 0.12 + k * 2.094
                pygame.draw.circle(cv, skin["ball"],
                                   (int(ix + math.cos(a) * (BALL_R + 8)),
                                    int(iy + math.sin(a) * (BALL_R + 8))), 3)

    def draw_box(self, cv, fx, s):
        b = s.box
        x = s.rect.centerx
        y = b["y"] + 4 * math.sin(self.t * 0.1 + (0 if s.is_player else 2))
        if b["life"] < 150 and (b["life"] // 6) % 2 == 0:
            return                                        # berkedip sebelum hilang
        col = hsv_color(self.t * 0.012 + (0.0 if s.is_player else 0.5))
        pop = min(1.0, 0.25 + b["age"] / 14.0)
        size = max(8, int(BOX_SIZE * (0.92 + 0.08 * math.sin(self.t * 0.2)) * pop))
        r = pygame.Rect(0, 0, size, size)
        r.center = (int(x), int(y))
        draw_glow(fx, (x, y), 60, col, 0.75)
        pygame.draw.rect(cv, scale_color(col, 0.22), r, border_radius=10)
        pygame.draw.rect(cv, col, r, 3, border_radius=10)
        draw_text(cv, "?", int(size * 0.95), WHITE, r.center)
        for k in range(3):
            a = self.t * 0.08 + k * 2.094
            pygame.draw.circle(fx, col, (int(x + math.cos(a) * (size * 0.8)),
                                         int(y + math.sin(a) * (size * 0.8))), 3)

    def draw_shield(self, cv, fx, s):
        cx, cy = s.rect.center
        col = SKILLS["shield"]["color"]
        frac = s.shield_t / SHIELD_FRAMES
        if frac < 0.25 and (s.shield_t // 5) % 2 == 0:
            return
        pulse = 0.8 + 0.2 * math.sin(self.t * 0.2)
        R = 100
        pygame.draw.circle(fx, scale_color(col, 0.16 * pulse), (cx, cy), R)
        pygame.draw.circle(fx, scale_color(col, 0.65 * pulse), (cx, cy), R, 4)
        pygame.draw.circle(fx, scale_color(col, 0.30), (cx, cy), R - 10, 1)
        for i in range(18):                               # titik nano berputar
            a = i * math.tau / 18 + self.t * 0.03
            pygame.draw.circle(fx, scale_color(col, 0.9),
                               (int(cx + math.cos(a) * R), int(cy + math.sin(a) * R)), 3)
        # sarang tawon (honeycomb)
        hex_r = 22
        rot = self.t * 0.01
        centers = [(0.0, 0.0)] + [(math.cos(rot + k * math.pi / 3) * 38,
                                   math.sin(rot + k * math.pi / 3) * 38) for k in range(6)]
        for hx, hy in centers:
            pts = [(int(cx + hx + math.cos(rot + k * math.pi / 3) * hex_r),
                    int(cy + hy + math.sin(rot + k * math.pi / 3) * hex_r)) for k in range(6)]
            pygame.draw.polygon(fx, scale_color(col, 0.38 * pulse), pts, 1)
        # dinding energi di garis gawang
        wx = SCREEN_W - 5 if s.is_player else 5
        pygame.draw.line(fx, scale_color(col, 0.55 * pulse), (wx, 0), (wx, SCREEN_H), 8)
        pygame.draw.line(fx, scale_color(col, 0.9), (wx, 0), (wx, SCREEN_H), 2)
        draw_skill_icon(cv, "shield", cx, s.rect.top - 40, 34, col)

    def draw_light_trail(self, fx, s):
        hist = s.light_hist
        n = len(hist)
        for i, (x, y) in enumerate(hist):
            f = (i + 1) / n
            pygame.draw.rect(fx, scale_color((255, 225, 50), 0.5 * f),
                             pygame.Rect(x - 6, y - 2, PADDLE_W + 12, PADDLE_H + 4), border_radius=10)
        cx, cy = s.rect.center
        draw_glow(fx, (cx, cy), 120, (255, 220, 40), 0.75)
        for _ in range(3):
            ang = random.uniform(-0.4, 0.4) + (0.0 if random.random() < 0.5 else math.pi)
            ln = random.uniform(40, 150)
            y1 = cy + random.uniform(-45, 45)
            pygame.draw.line(fx, (255, 235, 120), (int(cx), int(y1)),
                             (int(cx + math.cos(ang) * ln), int(y1 + math.sin(ang) * ln * 0.2)), 2)

    def draw_time_aura(self, fx, s):
        gold = SKILLS["time"]["color"]
        rect = s.rect
        cx, cy = rect.center
        pulse = 0.75 + 0.25 * math.sin(self.t * 0.15)
        for gy in (rect.top + 10, cy, rect.bottom - 10):
            draw_glow(fx, (cx, gy), 90, gold, pulse)
        sweep = (self.t * 4) % (PADDLE_H + 60) - 30
        y = rect.top + sweep
        fx.set_clip(rect.inflate(10, 10))
        pygame.draw.line(fx, (255, 255, 230), (rect.left - 8, int(y + 14)), (rect.right + 8, int(y - 14)), 4)
        fx.set_clip(None)
        r = 64 + 4 * math.sin(self.t * 0.1)
        pygame.draw.circle(fx, scale_color(gold, 0.6), (cx, cy), int(r), 2)
        for i in range(12):
            a = i * math.pi / 6 + self.t * 0.01
            pygame.draw.line(fx, scale_color(gold, 0.8),
                             (int(cx + math.cos(a) * (r - 6)), int(cy + math.sin(a) * (r - 6))),
                             (int(cx + math.cos(a) * (r + 6)), int(cy + math.sin(a) * (r + 6))), 2)
        ha = -self.t * 0.05
        pygame.draw.line(fx, gold, (cx, cy), (int(cx + math.cos(ha) * (r - 10)), int(cy + math.sin(ha) * (r - 10))), 3)

    def draw_dark_aura(self, fx, s):
        cx, cy = s.rect.center
        purple = (110, 30, 200)
        pulse = 0.7 + 0.3 * math.sin(self.t * 0.2)
        for gy in (s.rect.top + 10, cy, s.rect.bottom - 10):
            draw_glow(fx, (cx, gy), 130, purple, pulse)
        for i in range(3):
            a0 = self.t * 0.09 + i * 2.094
            rr = pygame.Rect(0, 0, 150, 150)
            rr.center = (cx, cy)
            pygame.draw.arc(fx, (150, 70, 255), rr, a0, a0 + 1.2, 3)

    def draw_armed_aura(self, fx, s):
        cx, cy = s.rect.center
        col = SKILLS["lightning"]["color"]
        draw_glow(fx, (cx, cy), 100, col, 0.5)
        for _ in range(3):
            ang = random.uniform(0, math.tau)
            sx = cx + random.uniform(-8, 8)
            sy = cy + random.uniform(-50, 50)
            ln = random.uniform(40, 90)
            draw_bolt(fx, bolt_points(sx, sy, sx + math.cos(ang) * ln, sy + math.sin(ang) * ln, 5, 10), col, 3)

    def draw_electric_ball(self, fx):
        bx, by = self.ball_x, self.ball_y
        col = SKILLS["lightning"]["color"]
        draw_glow(fx, (bx, by), 90, col, 0.9)
        for _ in range(4):
            ang = random.uniform(0, math.tau)
            ln = random.uniform(30, 70)
            draw_bolt(fx, bolt_points(bx, by, bx + math.cos(ang) * ln, by + math.sin(ang) * ln, 5, 9), col, 3)
        if len(self.ball_trail) > 6:
            px, py = self.ball_trail[0]
            draw_bolt(fx, bolt_points(bx, by, px, py, 8, 16), col, 2)

    def draw_side_fx(self, cv, fx, s):
        if s.light_t > 0:
            self.draw_light_trail(fx, s)
        if s.time_t > 0:
            self.draw_time_aura(fx, s)
        if s.armed:
            self.draw_armed_aura(fx, s)
        if s.shield_t > 0:
            self.draw_shield(cv, fx, s)
        if self.bh is not None and self.bh["user"] is s:
            self.draw_dark_aura(fx, s)
        cx, cy = s.rect.center
        if s.slow_t > 0:                                  # debuff: gerakan melambat
            pygame.draw.circle(fx, (70, 80, 110), (cx, cy), 60, 2)
        if s.lava_t > 0:                                  # debuff: lava
            pygame.draw.circle(fx, (150, 60, 10), (cx, cy), 64, 3)
            draw_glow(fx, (cx, cy), 80, (255, 110, 30), 0.5)
        if s.bleed_t > 0:
            draw_glow(fx, (cx, cy), 80, (200, 20, 40), 0.5)
        if s.stun_t > 0:                                  # bintang pusing
            for i in range(3):
                a = self.t * 0.15 + i * 2.094
                pygame.draw.circle(cv, (255, 235, 120),
                                   (int(cx + math.cos(a) * 28), int(s.rect.top - 20 + math.sin(a) * 8)), 5)
        if s.dizzy_t > 0:                                 # pusing: spiral hijau
            pts = []
            for i in range(30):
                a = i * 0.45 + self.t * 0.2
                rr = 3 + i * 0.8
                pts.append((int(cx + math.cos(a) * rr), int(s.rect.top - 30 + math.sin(a) * rr * 0.6)))
            pygame.draw.lines(cv, (120, 255, 160), False, pts, 2)
        if s.lock_t > 0:                                  # skill terkunci: gembok
            lx, ly = cx, s.rect.top - 34
            pygame.draw.circle(cv, (190, 190, 205), (lx, ly - 4), 8, 3)
            pygame.draw.rect(cv, (190, 190, 205), pygame.Rect(lx - 10, ly, 20, 15), border_radius=3)
            pygame.draw.circle(cv, (60, 60, 75), (lx, ly + 7), 2)

    def draw_fish(self, cv, fx):
        spr = get_fish_sprite()
        for f in self.fish:
            draw_glow(fx, (f["x"], f["y"]), 50, (255, 150, 80), 0.5)
            base = pygame.transform.flip(spr, False, True) if f["vx"] < 0 else spr
            img = pygame.transform.rotozoom(base, -math.degrees(math.atan2(f["vy"], f["vx"])), 1.0)
            cv.blit(img, img.get_rect(center=(int(f["x"]), int(f["y"]))))

    def draw_blackhole_fx(self, fx):
        bh = self.bh
        r = bh["r"]
        if r < 2:
            return
        ix, iy = int(bh["x"]), int(bh["y"])
        for col, mul, w in (((120, 40, 220), 1.5, 6), ((255, 140, 40), 1.25, 4), ((200, 100, 255), 1.05, 3)):
            pygame.draw.circle(fx, scale_color(col, 0.55), (ix, iy), max(2, int(r * mul)), w)
        for i in range(4):
            a0 = self.t * 0.12 * (1 if i % 2 else -1) + i * 1.57
            rr = pygame.Rect(0, 0, max(4, int(r * 2.6)), max(4, int(r * 2.6)))
            rr.center = (ix, iy)
            pygame.draw.arc(fx, (150, 90, 230), rr, a0, a0 + 1.0, 4)
        draw_glow(fx, (ix, iy), min(int(r * 2.2), 200), (110, 40, 200), 0.5)

    def draw_blackhole_core(self, cv):
        bh = self.bh
        r = int(bh["r"])
        if r < 2:
            return
        ix, iy = int(bh["x"]), int(bh["y"])
        pygame.draw.circle(cv, (2, 0, 6), (ix, iy), r)
        pygame.draw.circle(cv, (230, 200, 255), (ix, iy), r, 2)

    def effect_chips(self, s):
        chips = []
        if s.armed:
            chips.append(("ZAP", SKILLS["lightning"]["color"], 1.0))
        if s.time_t > 0:
            chips.append(("TIME", SKILLS["time"]["color"], s.time_t / TIME_FRAMES))
        if s.clone_t > 0:
            chips.append(("CLONE", SKILLS["clone"]["color"], s.clone_t / CLONE_FRAMES))
        if s.shield_t > 0:
            chips.append(("SHIELD", SKILLS["shield"]["color"], s.shield_t / SHIELD_FRAMES))
        if s.light_t > 0:
            chips.append(("LIGHT", SKILLS["light"]["color"], s.light_t / LIGHT_FRAMES))
        if s.slow_t > 0:
            chips.append(("SLOW", (150, 150, 175), s.slow_t / TIME_FRAMES))
        if s.stun_t > 0:
            chips.append(("STUN", (255, 90, 90), s.stun_t / STUN_FRAMES))
        if s.lava_t > 0:
            chips.append(("LAVA", (255, 130, 40), s.lava_t / LAVA_SLOW_FRAMES))
        if s.lock_t > 0:
            chips.append(("KUNCI", (200, 90, 90), s.lock_t / LOCK_FRAMES))
        if s.dizzy_t > 0:
            chips.append(("PUSING", (120, 255, 160), s.dizzy_t / DIZZY_FRAMES))
        if s.bleed_t > 0:
            chips.append(("BLEED", (230, 30, 50), s.bleed_t / BLEED_FRAMES))
        return chips

    def draw_hud(self, cv, skin):
        for s, x in ((self.cpu, SCREEN_W * 0.25), (self.player, SCREEN_W * 0.75)):
            color = s.color
            scale = 1.0 + 0.6 * (s.pulse / 24.0)
            draw_text(cv, str(s.score), 130, color, (x, 95), glow=color, scale=scale)
            draw_text(cv, s.display_name, 34, scale_color(color, 0.85), (x, 28))
            for i in range(WIN_SCORE):
                px = int(x - (WIN_SCORE - 1) * 13 + i * 26)
                if i < s.score:
                    pygame.draw.circle(cv, color, (px, 165), 7)
                else:
                    pygame.draw.circle(cv, (70, 70, 85), (px, 165), 6, 1)

            # slot skill
            if self.skills_on:
                sx = int(x + (170 if s.is_player else -170))
                r = pygame.Rect(0, 0, 76, 76)
                r.center = (sx, 95)
                pygame.draw.rect(cv, (16, 16, 28), r, border_radius=12)
                if s.slot is not None:
                    info = SKILLS[s.slot]
                    pulse = 0.7 + 0.3 * math.sin(self.t * 0.15)
                    pygame.draw.rect(cv, scale_color(info["color"], pulse), r, 3, border_radius=12)
                    draw_skill_icon(cv, s.slot, sx, 95, 44, info["color"])
                    draw_text(cv, info["name"], 22, info["color"], (sx, 150))
                    if s.ctrl is not None:
                        draw_text(cv, "[%s]" % s.ctrl["skill_label"], 22, WHITE, (sx, 170))
                else:
                    pygame.draw.rect(cv, (60, 60, 78), r, 2, border_radius=12)
                    draw_text(cv, "?", 44, (70, 70, 90), (sx, 95))

            chips = self.effect_chips(s)
            w = 84
            total = len(chips) * (w + 6) - 6
            for i, (label, col, frac) in enumerate(chips):
                cxx = x - total / 2 + i * (w + 6) + w / 2
                cr = pygame.Rect(0, 0, w, 26)
                cr.center = (int(cxx), 205)
                pygame.draw.rect(cv, (16, 16, 28), cr, border_radius=6)
                pygame.draw.rect(cv, scale_color(col, 0.45),
                                 pygame.Rect(cr.x, cr.y, max(2, int(w * clamp(frac, 0.0, 1.0))), cr.height),
                                 border_radius=6)
                pygame.draw.rect(cv, col, cr, 1, border_radius=6)
                draw_text(cv, label, 22, WHITE, cr.center)

    def apply_bloom(self, cv, fx):
        if not self.bloom_ok:
            return
        try:
            small = pygame.transform.smoothscale(fx, (SCREEN_W // 4, SCREEN_H // 4))
            big = pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))
            cv.blit(big, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        except Exception:  # noqa: BLE001
            self.bloom_ok = False

    def draw_game(self):
        cv, fx = self.canvas, self.fx
        skin = SKINS[self.skin_idx]
        m = MAPS[self.map_idx]
        arena = m["id"] == "arena"
        cv.blit(self.get_bg(), (0, 0))
        if arena:
            self.draw_stars(cv)
            self.draw_center_line(cv, skin)

        fx.fill((0, 0, 0))
        self.draw_arena(cv, fx, skin)
        self.draw_map_decor(cv, fx)
        for s in self.sides:
            if s.box is not None:
                self.draw_box(cv, fx, s)
        for x, y, ln, _spd in self.speed_lines:
            direction = -1 if self.bvx > 0 else 1
            pygame.draw.line(fx, scale_color(skin["ball_glow"], 0.35),
                             (int(x), int(y)), (int(x + direction * -ln), int(y)), 2)
        electric = self.ball_electric is not None
        if self.state != "gameover" and self.bh is None:
            self.draw_ball_trail(fx, self.ball_trail,
                                 SKILLS["lightning"]["color"] if electric else skin["ball_glow"])
        self.draw_paddle_trail(fx, self.cpu.hist, self.cpu.color)
        self.draw_paddle_trail(fx, self.player.hist, self.player.color)
        for s in self.sides:
            self.draw_side_fx(cv, fx, s)
        for p in self.particles:
            p.draw(fx)
        for x, y, r, _g, color, life, max_life in self.rings:
            f = life / max_life
            pygame.draw.circle(fx, scale_color(color, f), (int(x), int(y)), int(r), max(1, int(6 * f)))
        if self.bh is not None:
            self.draw_blackhole_fx(fx)

        self.draw_hud(cv, skin)
        for s in self.sides:
            self.draw_side_paddles(cv, fx, s, skin)
        self.draw_fish(cv, fx)
        if self.state != "gameover":
            if self.bh is not None:
                hole = (self.bh["x"], self.bh["y"])
                self.draw_sucked(cv, get_ball_sprite(skin), self.bh["ball0"], hole, self.bh["suck"], 0.6)
            else:
                self.render_ball(cv, fx, skin, self.ball_x, self.ball_y)
                if electric:
                    self.draw_electric_ball(fx)
        self.draw_hazards(cv, fx)
        cv.blit(fx, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.apply_bloom(cv, fx)
        if self.bh is not None:
            self.draw_blackhole_core(cv)

        for tx in self.texts:
            f = tx["life"] / tx["max"]
            draw_text(cv, tx["text"], tx["size"], tx["color"], (tx["x"], tx["y"]),
                      glow=tx["color"], scale=1.0 + (1.0 - f) * 0.5,
                      alpha=int(255 * min(1.0, f * 1.6)))

        if not arena and self.state == "play" and self.serve_timer == 0:
            secs = -(-self.map_timer // FPS)
            draw_text(cv, "%s  -  EVENT %d DTK" % (m["name"], max(0, secs)), 24, self.map_accent(),
                      (SCREEN_W // 2, SCREEN_H - 22))

        if self.mode == 1 and self.serve_timer > 0 and self.state in ("play", "pause"):
            draw_text(cv, "P1:  W / S  gerak   -   D  skill", 28, self.cpu.color, (SCREEN_W * 0.25, SCREEN_H - 70))
            draw_text(cv, "P2:  P / L  gerak   -   K  skill", 28, self.player.color, (SCREEN_W * 0.75, SCREEN_H - 70))
        if self.serve_timer > 0 and self.state in ("play", "pause"):
            number = -(-self.serve_timer // SERVE_STEP)
            k = (self.serve_timer % SERVE_STEP) / SERVE_STEP
            draw_text(cv, str(number), 220, WHITE, (SCREEN_W / 2, SCREEN_H / 2 - 150),
                      glow=skin["ball_glow"], scale=0.8 + 0.8 * k,
                      alpha=int(255 * (0.35 + 0.65 * k)))

    def draw_menu(self):
        cv = self.canvas
        m = MAPS[self.map_idx]
        cv.blit(self.get_bg(), (0, 0))
        if m["id"] == "arena":
            self.draw_stars(cv)
        cv.blit(self.dim, (0, 0))
        acc = self.map_accent()
        draw_text(cv, "PING PONG", 150, WHITE, (SCREEN_W // 2, 95), glow=acc,
                  scale=1.0 + 0.03 * math.sin(self.t * 0.06))
        draw_text(cv, "CINEMATIC SKILL EDITION  -  By Fredd", 30, mix(acc, WHITE, 0.4), (SCREEN_W // 2, 165))
        labels = ("PERTANDINGAN", "PEMAIN 1" if self.mode == 1 else "KARAKTER",
                  "PEMAIN 2" if self.mode == 1 else "LAWAN")
        for i, label in enumerate(labels):
            active = (i == self.menu_page)
            tx = SCREEN_W // 2 + (i - 1) * 330
            draw_text(cv, label, 36, WHITE if active else (120, 120, 140), (tx, 222),
                      glow=acc if active else None)
            if active:
                pygame.draw.line(cv, acc, (tx - 100, 244), (tx + 100, 244), 3)
        if self.menu_page == 0:
            self.draw_menu_match(cv, acc)
        else:
            self.draw_menu_char(cv, acc)
        draw_text(cv, "ENTER = Mulai   |   TAB = Ganti halaman   |   UP/DOWN + LEFT/RIGHT = Pilih   |   M = Suara",
                  24, (150, 150, 175), (SCREEN_W // 2, 783))

    def draw_overlay_pause(self, cv):
        cv.blit(self.dim, (0, 0))
        acc = self.map_accent()
        m = MAPS[self.map_idx]
        draw_text(cv, "PAUSE", 150, WHITE, (SCREEN_W // 2, 250), glow=acc)
        resume = "ESC = Lanjut      Q = Menu" if self.mode == 1 else "P / ESC = Lanjut      Q = Menu"
        draw_text(cv, resume, 40, (200, 200, 220), (SCREEN_W // 2, 350))
        draw_text(cv, "MAP: %s" % m["name"], 36, acc, (SCREEN_W // 2, 440))
        draw_text(cv, m["desc"], 26, (210, 210, 225), (SCREEN_W // 2, 480))
        for i, kind in enumerate(SKILL_KEYS):
            ix = SCREEN_W // 2 + (i - 3) * 150
            info = SKILLS[kind]
            draw_skill_icon(cv, kind, ix, 575, 40, info["color"])
            draw_text(cv, info["name"], 20, info["color"], (ix, 615))
        if self.mode == 1:
            tip = "Ambil MYSTERY BOX di garis gerak paddle  -  P1 skill: D   |   P2 skill: K"
        else:
            tip = "Ambil MYSTERY BOX di garis gerak paddle, tekan SPACE untuk memakai skill"
        draw_text(cv, tip, 26, (170, 170, 190), (SCREEN_W // 2, 680))

    def draw_overlay_gameover(self, cv):
        cv.blit(self.dim, (0, 0))
        side = self.player if self.winner == "player" else self.cpu
        color = side.color
        title = "%s MENANG!" % side.display_name
        size = min(130, int(1100 / (0.46 * len(title))))
        draw_text(cv, title, size, color, (SCREEN_W // 2, 300), glow=color,
                  scale=1.0 + 0.04 * math.sin(self.t * 0.1))
        draw_text(cv, "%s  %d  :  %d  %s" % (self.cpu.display_name, self.cpu.score, self.player.score,
                                              self.player.display_name), 70, WHITE, (SCREEN_W // 2, 430))
        draw_text(cv, "ENTER = Main lagi      ESC = Menu", 40, (200, 200, 220), (SCREEN_W // 2, 540))

    def draw(self):
        cv = self.canvas
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()
            if self.state == "pause":
                self.draw_overlay_pause(cv)
            elif self.state == "gameover":
                self.draw_overlay_gameover(cv)

        if self.flash_alpha > 0:
            self.flash_surf.fill(self.flash_color)
            self.flash_surf.set_alpha(int(clamp(self.flash_alpha, 0, 255)))
            cv.blit(self.flash_surf, (0, 0))

        ox = oy = 0
        if self.shake > 0:
            ox = int(random.uniform(-self.shake, self.shake))
            oy = int(random.uniform(-self.shake, self.shake))
        self.screen.fill((0, 0, 0))
        self.screen.blit(cv, (ox, oy))

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)


def main():
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
    pygame.init()
    Game().run()


if __name__ == "__main__":
    main()
