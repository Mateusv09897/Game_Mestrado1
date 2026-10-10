"""Pesquisadoras em Ação — exploração individual curta e educativa (v2).

Controles: WASD/setas movimentam | Shift corre | E interage | 1-4 escolhem personagem
           P pausa | M música | N efeitos sonoros | F11 tela cheia | Esc volta
"""
from __future__ import annotations

import array
import glob
import json
import math
import os
import random
import sys
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT, FPS = 1280, 720, 60
BASE = os.path.dirname(os.path.abspath(__file__))
SPRITES_DIR = os.path.join(BASE, "assets", "sprites")
BACKGROUNDS_DIR = os.path.join(BASE, "assets", "backgrounds")
MUSIC_DIR = os.path.join(BASE, "assets", "music")
SAVE_PATH = os.path.join(BASE, "progress.json")

WHITE, INK = (247, 250, 247), (17, 38, 42)
GREEN, LEAF, RIVER, SKY = (24, 111, 74), (103, 184, 105), (55, 157, 190), (176, 225, 238)
GOLD, CORAL, PURPLE, PANEL = (247, 190, 67), (232, 99, 88), (118, 84, 154), (8, 42, 47, 232)
MUTED, CARD, CARD_HOVER = (215, 238, 223), (42, 82, 83), (62, 110, 108)

ARROW_KEYS = {pygame.K_LEFT: "left", pygame.K_a: "left", pygame.K_RIGHT: "right", pygame.K_d: "right",
              pygame.K_UP: "up", pygame.K_w: "up", pygame.K_DOWN: "down", pygame.K_s: "down"}
ARROW_COLORS = {"left": (96, 190, 235), "down": (247, 190, 67), "up": (122, 204, 110), "right": (232, 99, 88)}
NOTE_FREQ = {"left": 262, "down": 330, "up": 392, "right": 523}
ACTION_OWNER = {"water": 0, "dance": 1, "map_ana": 2, "map_francisca": 3}
MISSION_SECONDS = 180.0


@dataclass(frozen=True)
class Researcher:
    name: str; key: str; color: tuple[int, int, int]; area: str; place: str; goal: str
    points: tuple[tuple[str, str], ...]; question: str; answers: tuple[str, str, str]; correct: int


RESEARCHERS = (
    Researcher("Lucilene", "lucilene", LEAF, "Botânica e educação", "Horta comunitária", "Encontre três elementos de uma horta que também é laboratório vivo.",
               (("Sementes", "Toda pesquisa começa com uma pergunta e cuidado."), ("Água", "A observação do ambiente orienta o cultivo."), ("Caderno", "Registrar dados transforma experiência em conhecimento.")),
               "Por que uma horta pode ser um laboratório vivo?", ("Porque permite observar, registrar e aprender com a natureza.", "Porque substitui todas as aulas.", "Porque plantas não precisam de cuidado."), 0),
    Researcher("Deuzilene", "deuzilene", PURPLE, "Educação, arte e tecnologia", "Pátio de aprendizagem", "Reúna três pistas que conectam ensino, arte e conhecimentos diversos.",
               (("Leitura", "Ensinar os vizinhos desde cedo revelou uma vocação."), ("Código", "A formação técnica pode abrir novos caminhos."), ("Ritmo", "Arte e educação também fazem ciência em movimento.")),
               "O que torna uma trajetória formativa mais potente?", ("Juntar saberes, pessoas e oportunidades.", "Seguir apenas um caminho sem dialogar.", "Evitar aprender coisas novas."), 0),
    Researcher("Ana Cláudia", "ana_claudia", GOLD, "Memória, história e formação", "Arquivo de memórias", "Encontre documentos que ajudam a contar histórias da educação profissional.",
               (("Documento", "Memórias e fontes ajudam a compreender o presente."), ("Mapa", "Redesenhar a rota também é uma escolha de estudo."), ("Livro", "A formação docente liga histórias, pessoas e território.")),
               "Quando um caminho planejado não está disponível, o que pode ajudar?", ("Redesenhar a rota sem abandonar o desejo de aprender.", "Desistir de estudar.", "Esperar sem agir."), 0),
    Researcher("Francisca", "maria_francisca", CORAL, "Linguagem, extensão e equidade", "Mapa da inclusão", "Ative cinco pontos que aproximam linguagem, formação e inclusão.",
               (("Linguagem", "Palavras, escuta e leitura ampliam a participação."), ("Extensão", "Conhecimento ganha força no diálogo com a comunidade."), ("Formação", "Formar professores é multiplicar possibilidades."), ("Equidade", "Educação acolhe diferenças e enfrenta desigualdades."), ("Inclusão", "Cada pessoa deve ter espaço, voz e oportunidade.")),
               "Como a formação pode ajudar a transformar desigualdades?", ("Fortalecendo estudo, voz e inclusão.", "Aceitando barreiras como definitivas.", "Esperando sem agir."), 0),
)

MINI_PAIRS = {
    "lucilene": (("SEMENTES", "PLANTAR"), ("ÁGUA", "CULTIVAR"), ("CADERNO", "REGISTRAR")),
    "ana_claudia": (("DOCUMENTO", "CONSULTAR FONTE"), ("MAPA", "REDESENHAR ROTA"), ("LIVRO", "COMPARTILHAR")),
    "maria_francisca": (("LINGUAGEM", "ESCUTAR"), ("EXTENSÃO", "DIALOGAR"), ("EQUIDADE", "ACOLHER")),
}


# ----------------------------------------------------------------------------
# Utilidades de desenho (fontes, textos e painéis com cache — rápido e leve)
# ----------------------------------------------------------------------------
def clamp(v, lo, hi): return max(lo, min(hi, v))
def lerp(a, b, t): return a + (b - a) * t
def ease_out(t): return 1 - (1 - clamp(t, 0, 1)) ** 3


_FONTS: dict = {}
_TEXT: dict = {}
_PANELS: dict = {}
_GLOWS: dict = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _FONTS: _FONTS[key] = pygame.font.SysFont("arial,dejavusans,freesans,liberationsans", size, bold=bold)
    return _FONTS[key]


def wrap(content, size, bold, max_width):
    if not max_width: return [content]
    f, lines, current = font(size, bold), [], ""
    for word in content.split():
        candidate = f"{current} {word}".strip()
        if not current or f.size(candidate)[0] <= max_width: current = candidate
        else: lines.append(current); current = word
    if current: lines.append(current)
    return lines or [""]


def text(surface, content, size, color, x, y, *, center=False, bold=False, max_width=None, shadow=False):
    lines = wrap(content, size, bold, max_width)
    for index, line in enumerate(lines):
        key = (line, size, color, bold)
        image = _TEXT.get(key)
        if image is None:
            if len(_TEXT) > 700: _TEXT.clear()
            image = _TEXT[key] = font(size, bold).render(line, True, color)
        ly = y + index * (size + 6)
        rect = image.get_rect(center=(x, ly + size // 2 + 2)) if center else image.get_rect(topleft=(x, ly))
        if shadow:
            dark = _TEXT.get((line, size, (0, 0, 0), bold)) or _TEXT.setdefault((line, size, (0, 0, 0), bold), font(size, bold).render(line, True, (0, 0, 0)))
            surface.blit(dark, rect.move(2, 2))
        surface.blit(image, rect)
    return len(lines) * (size + 6)


def panel(surface, rect, color=PANEL, radius=18, border=None):
    rect = pygame.Rect(rect)
    key = (rect.size, color, radius, border)
    image = _PANELS.get(key)
    if image is None:
        if len(_PANELS) > 300: _PANELS.clear()
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(image, color, image.get_rect(), border_radius=radius)
        if border: pygame.draw.rect(image, border, image.get_rect(), 2, border_radius=radius)
        _PANELS[key] = image
    surface.blit(image, rect.topleft)


def glow(surface, center, radius, color, alpha=110):
    key = (radius, color, alpha)
    image = _GLOWS.get(key)
    if image is None:
        image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            pygame.draw.circle(image, (*color, int(alpha * (1 - r / radius) ** 1.5) + 4), (radius, radius), r)
        _GLOWS[key] = image
    surface.blit(image, (center[0] - radius, center[1] - radius))


def draw_arrow(surface, direction, cx, cy, size, color, outline=None):
    angle = math.radians({"right": 0, "down": 90, "left": 180, "up": 270}[direction])
    c, s = math.cos(angle), math.sin(angle)
    base = [(-1, -.42), (0, -.42), (0, -1), (1, 0), (0, 1), (0, .42), (-1, .42)]
    points = [(cx + (x * c - y * s) * size / 2, cy + (x * s + y * c) * size / 2) for x, y in base]
    pygame.draw.polygon(surface, color, points)
    if outline: pygame.draw.polygon(surface, outline, points, 3)


def draw_star(surface, cx, cy, r, color, outline=None):
    points = [(cx + math.cos(math.radians(-90 + i * 36)) * (r if i % 2 == 0 else r * .45),
               cy + math.sin(math.radians(-90 + i * 36)) * (r if i % 2 == 0 else r * .45)) for i in range(10)]
    pygame.draw.polygon(surface, color, points)
    if outline: pygame.draw.polygon(surface, outline, points, 2)


def draw_check(surface, cx, cy, size, color, width=4):
    pygame.draw.lines(surface, color, False, [(cx - size * .5, cy), (cx - size * .12, cy + size * .4), (cx + size * .55, cy - size * .4)], width)


def draw_cross(surface, cx, cy, size, color, width=4):
    pygame.draw.line(surface, color, (cx - size / 2, cy - size / 2), (cx + size / 2, cy + size / 2), width)
    pygame.draw.line(surface, color, (cx - size / 2, cy + size / 2), (cx + size / 2, cy - size / 2), width)


def draw_keycap(surface, x, y, label, size=30):
    rect = pygame.Rect(0, 0, size, size); rect.center = (x, y)
    pygame.draw.rect(surface, (22, 50, 52), rect.move(0, 3), border_radius=7)
    pygame.draw.rect(surface, WHITE, rect, border_radius=7)
    text(surface, label, int(size * .6), INK, x, y - size * .32, center=True, bold=True)


def draw_note_icon(surface, x, y, color, on=True):
    pygame.draw.ellipse(surface, color, (x - 7, y + 2, 11, 8)); pygame.draw.line(surface, color, (x + 3, y + 5), (x + 3, y - 9), 2)
    pygame.draw.line(surface, color, (x + 3, y - 9), (x + 9, y - 5), 2)
    if not on: draw_cross(surface, x + 2, y, 22, CORAL, 3)


def draw_speaker_icon(surface, x, y, color, on=True):
    pygame.draw.rect(surface, color, (x - 9, y - 4, 6, 8)); pygame.draw.polygon(surface, color, [(x - 3, y - 4), (x + 4, y - 9), (x + 4, y + 9), (x - 3, y + 4)])
    if on: pygame.draw.arc(surface, color, (x + 1, y - 7, 12, 14), -1.0, 1.0, 2)
    else: draw_cross(surface, x + 8, y, 12, CORAL, 3)


# ----------------------------------------------------------------------------
# Efeitos sonoros sintetizados (nenhum arquivo extra necessário)
# ----------------------------------------------------------------------------
def synth(events, length, rate, channels, master=.33):
    n = int(length * rate); mix = [0.0] * n
    for freq, start, dur, wave, vol, slide in events:
        i0, count, phase, noise = int(start * rate), int(dur * rate), 0.0, 0.0
        for i in range(count):
            j = i0 + i
            if j >= n: break
            phase += 2 * math.pi * (freq + slide * i / count) / rate
            if wave == "sine": v = math.sin(phase)
            elif wave == "square": v = .5 if math.sin(phase) > 0 else -.5
            elif wave == "tri": v = 2 / math.pi * math.asin(math.sin(phase))
            else: noise = noise * .86 + random.uniform(-1, 1) * .14; v = noise * 3
            mix[j] += v * min(1, i / (rate * .004)) * (1 - i / count) ** 1.6 * vol
    data = array.array("h")
    for v in mix:
        sample = int(clamp(v * master, -1, 1) * 32767)
        for _ in range(channels): data.append(sample)
    return pygame.mixer.Sound(buffer=data.tobytes())


class Sfx:
    def __init__(self):
        self.ok, self.enabled, self.sounds = False, True, {}
        init = pygame.mixer.get_init()
        if not init or init[1] != -16: return
        try:
            self.build(init[0], init[2]); self.ok = True
        except Exception:  # sem áudio: o jogo segue normalmente
            self.sounds = {}

    def build(self, rate, ch):
        def mk(name, events, length, master=.33): self.sounds[name] = synth(events, length, rate, ch, master)
        mk("collect", [(660, 0, .12, "sine", 1, 0), (880, .08, .12, "sine", 1, 0), (1175, .16, .22, "sine", 1, 0)], .45)
        mk("bonus", [(1320, 0, .09, "tri", 1, 0), (1760, .07, .16, "tri", 1, 0)], .3)
        mk("click", [(520, 0, .06, "tri", 1, 0)], .1)
        mk("match", [(700, 0, .1, "sine", 1, 0), (990, .08, .18, "sine", 1, 0)], .3)
        mk("error", [(210, 0, .22, "square", .8, -90)], .28, .25)
        mk("water", [(0, 0, .45, "noise", .9, 0)], .5, .3)
        mk("tick", [(1000, 0, .05, "sine", 1, 0)], .08, .25)
        mk("beat", [(180, 0, .07, "sine", 1, 0)], .1, .35)
        mk("perfect", [(880, 0, .1, "sine", 1, 0), (1320, 0, .14, "sine", .7, 0)], .2)
        mk("good", [(660, 0, .12, "sine", 1, 0)], .16)
        mk("miss", [(140, 0, .16, "tri", 1, -40)], .2)
        mk("timeout", [(440, 0, .2, "tri", 1, 0), (330, .2, .2, "tri", 1, 0), (220, .4, .4, "tri", 1, 0)], .85)
        mk("win", [(523, 0, .14, "tri", 1, 0), (659, .14, .14, "tri", 1, 0), (784, .28, .14, "tri", 1, 0), (1047, .42, .6, "tri", 1, 0), (784, .42, .6, "sine", .5, 0)], 1.1)
        for i in range(3): mk(f"star{i}", [(740 + i * 220, 0, .25, "sine", 1, 0), (1480 + i * 440, 0, .2, "sine", .4, 0)], .3)
        for name, freq in NOTE_FREQ.items(): mk(f"n_{name}", [(freq, 0, .22, "tri", 1, 0), (freq * 2, 0, .15, "sine", .3, 0)], .28)

    def play(self, name, volume=1.0):
        if self.ok and self.enabled and name in self.sounds:
            self.sounds[name].set_volume(volume); self.sounds[name].play()


# ----------------------------------------------------------------------------
# Partículas
# ----------------------------------------------------------------------------
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "age", "color", "size", "grav", "kind", "rot", "spin")

    def __init__(self, x, y, vx, vy, life, color, size, grav, kind):
        self.x, self.y, self.vx, self.vy, self.life, self.age = x, y, vx, vy, life, 0.0
        self.color, self.size, self.grav, self.kind = color, size, grav, kind
        self.rot, self.spin = random.uniform(0, 6.28), random.uniform(-9, 9)


class Particles:
    def __init__(self): self.items: list[Particle] = []

    def clear(self): self.items.clear()

    def burst(self, x, y, count, colors, *, speed=(60, 260), life=(.5, 1.1), size=(3, 7), grav=320, kind="spark"):
        for _ in range(count):
            a, s = random.uniform(0, math.tau), random.uniform(*speed)
            self.items.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(*life), random.choice(colors), random.uniform(*size), grav, kind))

    def add(self, x, y, vx, vy, life, color, size, grav, kind):
        self.items.append(Particle(x, y, vx, vy, life, color, size, grav, kind))

    def update(self, dt):
        for p in self.items:
            p.age += dt; p.vy += p.grav * dt
            if p.kind in ("confetti", "leaf", "note"): p.vx += math.sin(p.age * 5 + p.rot) * 60 * dt
            p.x += p.vx * dt; p.y += p.vy * dt
        self.items = [p for p in self.items if p.age < p.life and p.y < HEIGHT + 40]
        if len(self.items) > 500: self.items = self.items[-500:]

    def draw(self, surface):
        for p in self.items:
            k = 1 - p.age / p.life; x, y = int(p.x), int(p.y)
            if p.kind == "confetti":
                angle, w, h = p.rot + p.age * p.spin, p.size, p.size * .55
                c, s = math.cos(angle), math.sin(angle)
                pygame.draw.polygon(surface, p.color, [(x + c * dx - s * dy, y + s * dx + c * dy) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))])
            elif p.kind == "leaf": pygame.draw.ellipse(surface, p.color, (x - p.size, y - p.size // 2, p.size * 2, max(3, p.size)))
            elif p.kind == "note":
                pygame.draw.circle(surface, p.color, (x, y), int(p.size * .8)); pygame.draw.line(surface, p.color, (x + p.size * .7, y), (x + p.size * .7, y - p.size * 2.2), 2)
            elif p.kind == "dust": pygame.draw.circle(surface, p.color, (x, y), max(1, int(p.size * k)))
            else:
                pygame.draw.circle(surface, p.color, (x, y), max(1, int(p.size * k)))
                if p.size > 4 and k > .4: pygame.draw.circle(surface, WHITE, (x, y), max(1, int(p.size * k * .4)))


# ----------------------------------------------------------------------------
# Jogo
# ----------------------------------------------------------------------------
class Game:
    def __init__(self):
        # Inicialização explícita evita que a trilha fique silenciosa em alguns PCs Windows.
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init(); pygame.display.set_caption("Pesquisadoras em Ação — IFAM")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas, self.clock = pygame.Surface((WIDTH, HEIGHT)), pygame.time.Clock()
        self.running, self.fullscreen, self.state, self.next_state = True, False, "title", None
        self.fade, self.time, self.shake, self.show_help = 255.0, 0.0, 0.0, False
        self.mouse, self.selection, self.active = pygame.Vector2(-1, -1), 0, 0
        self.card_lift, self.schedule_list, self.reset_armed = [0.0] * 4, [], 0.0
        self.particles, self.sfx = Particles(), Sfx()
        self.animations, self.backgrounds = self.load_animations(), self.load_backgrounds()
        self.action_sprites, self.scaled_cache = self.load_action_sprites(), {}
        self.action_name, self.action_time, self.pending_minigame = None, 0.0, False
        self.music_loaded, self.music_paused, self.music_error = False, False, ""
        self.notice, self.notice_time, self.popups = "", 0.0, []
        self.progress = self.load_progress()
        self.motes = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(0, 6.28), random.uniform(8, 22)] for _ in range(26)]
        self.tint = pygame.Surface((WIDTH, HEIGHT)); self.tint.fill((255, 165, 80))
        self.vignette = self.make_vignette(); self.fallback_sky = self.make_sky(); self.fallback_fg = self.make_fallback_fg()
        self.reset_mission_state()
        self.load_music()

    # ------------------------------------------------------------- carregamento
    def load_animations(self):
        animations = {}
        for researcher in RESEARCHERS:
            animations[researcher.key] = {}
            for action in ("idle", "walk_left", "walk_right"):
                paths = sorted(glob.glob(os.path.join(SPRITES_DIR, researcher.key, action, "*.png")))
                animations[researcher.key][action] = [pygame.transform.scale(pygame.image.load(p).convert_alpha(), (128, 128)) for p in paths]
        return animations

    def load_backgrounds(self):
        backgrounds = {}
        for key, filename in (("facade", "ifam_cmc_fachada_8bit.jpg"), ("aerial", "ifam_cmc_aereo_8bit.jpg")):
            path = os.path.join(BACKGROUNDS_DIR, filename)
            if os.path.exists(path):
                backgrounds[key] = pygame.transform.smoothscale(pygame.image.load(path).convert(), (WIDTH, HEIGHT))  # escala uma única vez
        return backgrounds

    def load_action_sprites(self):
        """Ações fornecidas pela equipe: usadas como feedback real de cada missão."""
        names = {"water": ("lucilene", "lucilene_water_01.png"), "dance": ("deuzilene", "deuzilene_dance_01.png"),
                 "map_ana": ("ana_claudia", "ana_claudia_map_01.png"), "map_francisca": ("maria_francisca", "maria_francisca_map_01.png")}
        actions = {}
        for key, (researcher, filename) in names.items():
            path = os.path.join(SPRITES_DIR, researcher, filename)
            if os.path.exists(path): actions[key] = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (128, 128))
        return actions

    def load_music(self):
        """Carrega a trilha e mantém um status para o controle M."""
        self.music_loaded, self.music_error = False, ""
        for filename in ("trilha.wav", "trilha.mp3", "trilha.wav"):
            path = os.path.join(MUSIC_DIR, filename)
            if os.path.exists(path):
                try:
                    if not pygame.mixer.get_init(): pygame.mixer.init(44100, -16, 2, 1024)
                    pygame.mixer.music.load(path); pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1, fade_ms=700)
                    self.music_loaded, self.music_paused = True, False
                except pygame.error as error: self.music_error = str(error)
                return

    def toggle_music(self):
        if not self.music_loaded:
            self.load_music(); self.show_notice("Trilha iniciada." if self.music_loaded else "Não foi possível iniciar a trilha."); return
        if self.music_paused: pygame.mixer.music.unpause(); self.music_paused = False; self.show_notice("Trilha ativada.")
        else: pygame.mixer.music.pause(); self.music_paused = True; self.show_notice("Trilha pausada.")

    def load_progress(self):
        try:
            with open(SAVE_PATH, encoding="utf-8") as handle: data = json.load(handle)
            return {k: v for k, v in data.get("best", {}).items() if isinstance(v, dict)}
        except (OSError, ValueError, AttributeError): return {}

    def save_progress(self):
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as handle: json.dump({"best": self.progress}, handle, ensure_ascii=False, indent=1)
        except OSError: pass  # pasta somente leitura: o jogo continua sem salvar

    @property
    def completed(self): return {i for i, r in enumerate(RESEARCHERS) if r.key in self.progress}

    def best(self, index): return self.progress.get(RESEARCHERS[index].key, {"score": 0, "stars": 0})

    @property
    def researcher(self): return RESEARCHERS[self.active]

    # ------------------------------------------------------------- cenário de reserva
    def make_sky(self):
        sky = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = min(1.0, y / 420); pygame.draw.line(sky, (int(lerp(120, 205, t)), int(lerp(190, 233, t)), int(lerp(235, 240, t))), (0, y), (WIDTH, y))
        pygame.draw.circle(sky, (255, 239, 181), (1090, 105), 58)
        return sky

    def make_fallback_fg(self):
        fg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(fg, (83, 151, 99), [(0, 330), (210, 205), (460, 350), (710, 210), (970, 345), (1280, 220), (1280, 520), (0, 520)])
        pygame.draw.rect(fg, (92, 151, 92), (0, 485, WIDTH, 235)); pygame.draw.rect(fg, (207, 178, 117), (0, 555, WIDTH, 165))
        pygame.draw.rect(fg, (238, 241, 229), (435, 180, 410, 220), border_radius=8); pygame.draw.rect(fg, GREEN, (420, 160, 440, 34), border_radius=5)
        text(fg, "IFAM", 23, WHITE, 640, 165, center=True, bold=True)
        for x in range(465, 810, 66):
            for y in (225, 285, 345): pygame.draw.rect(fg, (80, 139, 150), (x, y, 35, 28), border_radius=4)
        for x in range(90, 1220, 135): pygame.draw.circle(fg, LEAF, (x, 486), 32); pygame.draw.rect(fg, (83, 92, 54), (x - 4, 490, 8, 57))
        return fg

    def make_vignette(self):
        small = pygame.Surface((64, 36), pygame.SRCALPHA)
        for x in range(64):
            for y in range(36):
                d = math.hypot((x - 31.5) / 32, (y - 17.5) / 18)
                small.set_at((x, y), (0, 8, 12, int(clamp((d - .62) * 210, 0, 120))))
        return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))

    # ------------------------------------------------------------- estado da missão
    def reset_mission_state(self):
        self.player, self.vel, self.facing, self.anim_frame, self.frame_time = pygame.Vector2(150, 560), pygame.Vector2(), 1, 0, 0.0
        self.collected, self.collect_time, self.bonus, self.bonus_got = set(), {}, [], 0
        self.seconds, self.errors, self.last_sec = MISSION_SECONDS, 0, 999
        self.tally = {"Pistas": 0, "Curiosidades": 0, "Minidesafio": 0, "Tempo restante": 0, "Precisão": 0}
        self.mini_selected, self.mini_matched, self.mini_order, self.mini_streak, self.mini_flash = None, set(), [0, 1, 2], 0, {}
        self.rh_notes, self.rh_time, self.rh_hits, self.rh_combo, self.rh_max, self.rh_last_beat, self.rh_end = [], 0.0, 0, 0, 0, -1, False
        self.q_order, self.q_wrong, self.q_shake, self.q_done = [0, 1, 2], set(), {}, False
        self.stars, self.final_score, self.result_t, self.result_new_best = 1, 0, 0.0, False
        self.dust_timer, self.flavor_timer, self.mission_t = 0.0, 0.0, 0.0
        self.action_name, self.action_time, self.pending_minigame = None, 0.0, False

    @property
    def score(self): return sum(self.tally.values())

    def add_score(self, category, points, x=None, y=None):
        self.tally[category] += points
        if x is not None: self.popups.append([f"+{points}", x, y, 1.1, GOLD, 24])

    def start_mission(self, index):
        self.active = index; self.reset_mission_state(); self.particles.clear(); self.popups.clear()
        self.bonus = self.make_bonus(); self.notice_time = 0.0
        self.go("play")

    def make_bonus(self):
        spots, tries = [], 0
        hot = self.hotspot_positions()
        while len(spots) < 5 and tries < 400:
            tries += 1; p = (random.randint(110, WIDTH - 110), random.randint(235, HEIGHT - 120))
            if all(math.dist(p, h) > 110 for h in hot) and all(math.dist(p, s) > 170 for s in spots) and math.dist(p, (150, 560)) > 160: spots.append(p)
        return [{"pos": p, "got": False, "phase": random.uniform(0, 6)} for p in spots]

    def hotspot_positions(self):
        return [(265, 355), (460, 250), (640, 420), (825, 260), (1035, 365)] if len(self.researcher.points) == 5 else [(290, 355), (650, 270), (1015, 385)]

    def mini_pairs(self): return MINI_PAIRS.get(self.researcher.key, ())

    def show_notice(self, message, duration=4.5): self.notice, self.notice_time = message, duration

    def play_action(self, name, duration=.8): self.action_name, self.action_time = name, duration

    def after(self, delay, fn): self.schedule_list.append([delay, fn])

    # ------------------------------------------------------------- transições
    def go(self, state):
        if self.next_state is None: self.next_state = state; self.schedule_list.clear()  # descarta ações agendadas da tela anterior

    def enter(self, state):
        if state in ("select", "title"): self.particles.clear(); self.popups.clear()
        if state == "minigame":
            if self.researcher.key == "deuzilene": self.start_rhythm()
            else:
                n = len(self.mini_pairs()); self.mini_order = random.sample(range(n), n)
                self.mini_selected, self.mini_matched, self.mini_streak, self.mini_flash = None, set(), 0, {}
                self.show_notice("Clique (ou digite o número) de uma pista e depois da ação que a completa.", 6)
        elif state == "question":
            self.q_order = random.sample(range(3), 3); self.q_wrong, self.q_shake, self.q_done = set(), {}, False
        elif state == "result":
            self.result_t = 0.0; self.particles.clear()
            for _ in range(130 if len(self.completed) == 4 else 80):
                self.particles.add(random.uniform(0, WIDTH), random.uniform(-200, -10), random.uniform(-40, 40), random.uniform(60, 190), random.uniform(3.5, 6),
                                   random.choice((GOLD, CORAL, LEAF, RIVER, PURPLE, WHITE)), random.uniform(5, 9), 40, "confetti")
            self.sfx.play("win")
        elif state == "timeout": self.sfx.play("timeout")

    # ------------------------------------------------------------- interação
    def nearest_hotspot(self):
        candidates = [(i, pygame.Vector2(pos), item) for i, (pos, item) in enumerate(zip(self.hotspot_positions(), self.researcher.points)) if i not in self.collected]
        return min(candidates, key=lambda c: self.player.distance_to(c[1])) if candidates else None

    def interact(self):
        for index, (position, item) in enumerate(zip(self.hotspot_positions(), self.researcher.points)):
            if index not in self.collected and self.player.distance_to(position) < 85:
                self.collected.add(index); self.collect_time[index] = self.time; self.show_notice(f"{item[0]}: {item[1]}", 6)
                self.add_score("Pistas", 100, position[0], position[1] - 50)
                self.particles.burst(position[0], position[1], 26, (GOLD, WHITE, (255, 239, 117)), speed=(80, 280), size=(3, 8))
                self.sfx.play("collect")
                if self.researcher.key == "lucilene":
                    self.play_action("water", 1.1); self.sfx.play("water", .6)
                    self.particles.burst(position[0], position[1] + 10, 18, (RIVER, (170, 225, 245)), speed=(40, 160), grav=500, size=(2, 5))
                return
        if len(self.collected) == len(self.researcher.points):
            map_action = {"ana_claudia": "map_ana", "maria_francisca": "map_francisca"}.get(self.researcher.key)
            if map_action:
                self.show_notice("Agora consulte o mapa para definir a próxima rota."); self.play_action(map_action, 1.25); self.pending_minigame = True
            else: self.go("minigame")
        else: self.show_notice("Aproxime-se de um ponto brilhante e aperte E.")

    # ---- minidesafio de associação
    def left_rect(self, i): return pygame.Rect(135, 238 + i * 105, 335, 74)
    def right_rect(self, slot): return pygame.Rect(810, 238 + slot * 105, 335, 74)

    def select_clue(self, index):
        if index in self.mini_matched: return
        self.mini_selected = index; self.sfx.play("click"); self.show_notice(f"{self.mini_pairs()[index][0].title()} selecionada. Agora escolha a ação.")

    def try_match(self, slot):
        pairs, source = self.mini_pairs(), self.mini_order[slot]
        if source in self.mini_matched: return
        if self.mini_selected is None: self.show_notice("Primeiro selecione uma pista à esquerda."); self.sfx.play("click"); return
        rect = self.right_rect(slot)
        if self.mini_selected == source:
            self.mini_matched.add(source); self.mini_selected, self.mini_streak = None, 0
            self.show_notice("Boa associação!"); self.sfx.play("match"); self.add_score("Minidesafio", 100, rect.centerx, rect.top)
            self.particles.burst(rect.centerx, rect.centery, 22, (LEAF, GOLD, WHITE), speed=(60, 240))
            if len(self.mini_matched) == len(pairs): self.after(1.0, lambda: self.go("question")); self.show_notice("Todas as pistas conectadas!")
        else:
            self.errors += 1; self.mini_streak += 1; self.shake = .25; self.mini_flash[slot] = .5; self.sfx.play("error")
            self.show_notice("Tente outra ação: pense no que essa pista permite fazer.")

    def matching_click(self, mouse):
        for index in range(len(self.mini_pairs())):
            if self.left_rect(index).collidepoint(mouse): self.select_clue(index); return
        for slot in range(len(self.mini_pairs())):
            if self.right_rect(slot).collidepoint(mouse): self.try_match(slot); return

    # ---- minidesafio de ritmo (Deuzilene)
    def start_rhythm(self):
        keys, last = [], None
        for _ in range(12):
            choice = random.choice([k for k in ("left", "down", "up", "right") if k != last]); keys.append(choice); last = choice
        self.rh_notes = [{"t": 2.4 + i * .66, "key": k, "state": None} for i, k in enumerate(keys)]
        self.rh_time, self.rh_hits, self.rh_combo, self.rh_max, self.rh_last_beat, self.rh_end = 0.0, 0, 0, 0, -1, False
        self.show_notice("Aperte a seta certa quando a nota chegar ao círculo!", 5)

    def rhythm_input(self, key):
        direction = ARROW_KEYS.get(key)
        if not direction or self.rh_end: return
        near = [n for n in self.rh_notes if n["state"] is None and abs(n["t"] - self.rh_time) <= .32]
        if not near: return
        note = min(near, key=lambda n: abs(n["t"] - self.rh_time)); delta = abs(note["t"] - self.rh_time)
        hit_x = 420
        if note["key"] == direction:
            grade = "PERFEITO!" if delta < .1 else "BOA!"
            note["state"] = "perfect" if delta < .1 else "good"
            self.rh_hits += 1; self.rh_combo += 1; self.rh_max = max(self.rh_max, self.rh_combo)
            self.add_score("Minidesafio", (20 if delta < .1 else 10) + min(self.rh_combo, 8)); self.sfx.play(f"n_{direction}")
            self.sfx.play("perfect" if delta < .1 else "good", .5)
            self.particles.burst(hit_x, 345, 14 if delta < .1 else 8, (ARROW_COLORS[direction], WHITE, GOLD), speed=(80, 260))
            self.popups.append([grade, hit_x + 40, 270, .55, GOLD if delta < .1 else WHITE, 22])
        else:
            note["state"] = "miss"; self.rh_combo = 0; self.sfx.play("miss"); self.shake = .15
            self.popups.append(["ERROU", hit_x + 40, 270, .7, CORAL, 22])

    def update_rhythm(self, dt):
        self.rh_time += dt
        first = self.rh_notes[0]["t"]
        beat = int(self.rh_time / .66)
        if beat != self.rh_last_beat:
            self.rh_last_beat = beat
            if self.rh_time < first - .3: self.sfx.play("beat", .8)
        for n in self.rh_notes:
            if n["state"] is None and self.rh_time > n["t"] + .32: n["state"] = "miss"; self.rh_combo = 0
        if not self.rh_end and all(n["state"] for n in self.rh_notes) and self.rh_time > self.rh_notes[-1]["t"] + .5:
            self.rh_end = True
            if self.rh_hits >= 8:
                self.show_notice(f"Ritmo concluído! {self.rh_hits}/12 notas."); self.sfx.play("match"); self.after(1.4, lambda: self.go("question"))
            else:
                self.errors += 1; self.show_notice(f"{self.rh_hits}/12 — precisamos de 8. Vamos de novo!"); self.after(1.6, self.start_rhythm)

    # ---- pergunta final
    def option_rect(self, i): return pygame.Rect(205, 330 + i * 78, 870, 58)

    def answer_question(self, shown_index):
        if self.q_done or shown_index in self.q_wrong: return
        original = self.q_order[shown_index]
        if original == self.researcher.correct:
            self.q_done = True; self.finish_mission()
            self.particles.burst(self.option_rect(shown_index).centerx, self.option_rect(shown_index).centery, 40, (LEAF, GOLD, WHITE), speed=(80, 320))
            self.sfx.play("match"); self.after(.9, lambda: self.go("result"))
        else:
            self.q_wrong.add(shown_index); self.q_shake[shown_index] = .5; self.errors += 1; self.shake = .25; self.sfx.play("error")

    def finish_mission(self):
        self.add_score("Tempo restante", int(self.seconds) * 3)
        self.add_score("Precisão", max(0, 300 - self.errors * 75))
        self.stars = 1 + (self.errors <= 2) + (self.seconds >= 30 and self.bonus_got >= 3)
        self.final_score = self.score
        old = self.progress.get(self.researcher.key, {"score": 0, "stars": 0})
        self.result_new_best = self.final_score > old["score"]
        self.progress[self.researcher.key] = {"score": max(old["score"], self.final_score), "stars": max(old["stars"], self.stars)}
        self.save_progress()

    # ------------------------------------------------------------- atualização
    def update(self, dt):
        self.time += dt; self.mission_t += dt
        if self.next_state is not None:
            self.fade = min(255, self.fade + 1500 * dt)
            if self.fade >= 255:
                self.state, self.next_state = self.next_state, None; self.enter(self.state)
        elif self.fade > 0: self.fade = max(0, self.fade - 1100 * dt)
        self.shake = max(0, self.shake - dt)
        self.reset_armed = max(0, self.reset_armed - dt)
        if self.notice_time: self.notice_time = max(0, self.notice_time - dt)
        if self.state == "pause": return
        for item in self.schedule_list: item[0] -= dt
        due = [i for i in self.schedule_list if i[0] <= 0]; self.schedule_list = [i for i in self.schedule_list if i[0] > 0]
        for _, fn in due:
            if self.next_state is None: fn()
        self.particles.update(dt)
        for p in self.popups: p[3] -= dt; p[2] -= 38 * dt
        self.popups = [p for p in self.popups if p[3] > 0]
        for i in range(4): self.card_lift[i] = lerp(self.card_lift[i], 1.0 if (self.state == "select" and i == self.selection) else 0.0, min(1, 12 * dt))
        for t in list(self.mini_flash): self.mini_flash[t] -= dt; self.mini_flash = {k: v for k, v in self.mini_flash.items() if v > 0}
        for t in list(self.q_shake): self.q_shake[t] = max(0, self.q_shake[t] - dt)
        if self.state == "play": self.update_play(dt)
        elif self.state == "minigame" and self.researcher.key == "deuzilene": self.update_rhythm(dt)
        elif self.state == "result": self.update_result(dt)
        elif self.state == "title" and random.random() < .25: self.particles.add(random.uniform(150, 1130), 580, random.uniform(-20, 20), -random.uniform(40, 90), 1.6, GOLD, 4, -10, "spark")

    def update_result(self, dt):
        before = self.result_t; self.result_t += dt
        for i in range(self.stars):
            at = 1.2 + i * .45
            if before < at <= self.result_t:
                self.sfx.play(f"star{i}"); self.particles.burst(640 + (i - 1) * 100, 262, 18, (GOLD, WHITE), speed=(60, 220), grav=120)

    def update_play(self, dt):
        self.seconds = max(0, self.seconds - dt)
        sec = int(math.ceil(self.seconds))
        if 0 < sec <= 10 and sec != self.last_sec: self.sfx.play("tick", .7)
        self.last_sec = sec
        if self.seconds <= 0: self.go("timeout"); return
        self.flavor(dt)
        if self.action_time:
            self.action_time = max(0, self.action_time - dt)
            if not self.action_time:
                self.action_name = None
                if self.pending_minigame: self.pending_minigame = False; self.go("minigame")
            return
        k = pygame.key.get_pressed()
        direction = pygame.Vector2(int(k[pygame.K_d] or k[pygame.K_RIGHT]) - int(k[pygame.K_a] or k[pygame.K_LEFT]), int(k[pygame.K_s] or k[pygame.K_DOWN]) - int(k[pygame.K_w] or k[pygame.K_UP]))
        speed = 360 if (k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]) else 250
        target = direction.normalize() * speed if direction.length_squared() else pygame.Vector2()
        self.vel += (target - self.vel) * min(1, 11 * dt)
        if self.vel.length() < 4: self.vel.update(0, 0)
        self.player += self.vel * dt
        self.player.x, self.player.y = clamp(self.player.x, 65, WIDTH - 65), clamp(self.player.y, 190, HEIGHT - 95)
        if abs(direction.x) > .1: self.facing = 1 if direction.x > 0 else -1
        if self.vel.length() > 30:
            self.frame_time += dt * (self.vel.length() / 250)
            if self.frame_time >= .12: self.anim_frame, self.frame_time = self.anim_frame + 1, 0
            self.dust_timer -= dt
            if self.dust_timer <= 0:
                self.dust_timer = .11; self.particles.add(self.player.x + random.uniform(-10, 10), self.player.y - 4, random.uniform(-14, 14), -random.uniform(8, 30), .45, (226, 205, 150), 5, 0, "dust")
        for b in self.bonus:
            if not b["got"] and math.dist(b["pos"], (self.player.x, self.player.y - 40)) < 52:
                b["got"] = True; self.bonus_got += 1; self.add_score("Curiosidades", 50, b["pos"][0], b["pos"][1] - 20); self.sfx.play("bonus")
                self.particles.burst(b["pos"][0], b["pos"][1], 20, (GOLD, WHITE, (255, 239, 117)), speed=(80, 260))

    def flavor(self, dt):
        """Detalhes de cada pesquisadora: folhas para Lucilene, notas para Deuzilene."""
        self.flavor_timer -= dt
        if self.flavor_timer > 0: return
        key = self.researcher.key
        if key == "lucilene": self.flavor_timer = .45; self.particles.add(random.uniform(0, WIDTH), 120, random.uniform(-20, 20), random.uniform(30, 60), 6, random.choice(((120, 190, 90), (90, 160, 80))), 6, 8, "leaf")
        elif key == "deuzilene": self.flavor_timer = .8; self.particles.add(random.uniform(80, WIDTH - 80), HEIGHT - 110, random.uniform(-15, 15), -random.uniform(50, 80), 3, random.choice((PURPLE, GOLD, (200, 160, 240))), 6, -8, "note")
        else: self.flavor_timer = 1.2

    # ------------------------------------------------------------- entrada
    def view_rect(self):
        sw, sh = self.screen.get_size(); s = min(sw / WIDTH, sh / HEIGHT)
        w, h = int(WIDTH * s), int(HEIGHT * s)
        return pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)

    def canvas_mouse(self, position):
        vr = self.view_rect()
        return pygame.Vector2((position[0] - vr.x) * WIDTH / max(1, vr.w), (position[1] - vr.y) * HEIGHT / max(1, vr.h))

    def card_rect(self, index): return pygame.Rect(115 + index * 275, 232, 240, 290)

    def handle_event(self, event):
        if event.type == pygame.QUIT: self.running = False; return
        if event.type in (pygame.VIDEORESIZE, getattr(pygame, "WINDOWSIZECHANGED", -1)): self.screen = pygame.display.get_surface(); return
        if event.type == getattr(pygame, "WINDOWFOCUSLOST", -1) and self.state == "play": self.state = "pause"; return
        if self.next_state is not None: return
        if event.type == pygame.MOUSEMOTION:
            self.mouse = self.canvas_mouse(event.pos)
            if self.state == "select":
                for i in range(len(RESEARCHERS)):
                    if self.card_rect(i).collidepoint(self.mouse): self.selection = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self.on_click(self.canvas_mouse(event.pos))
        elif event.type == pygame.KEYDOWN: self.on_key(event)

    def on_click(self, mouse):
        if self.show_help: self.show_help = False; return
        if self.state == "title": self.sfx.play("click"); self.go("select")
        elif self.state == "select":
            for i in range(len(RESEARCHERS)):
                if self.card_rect(i).collidepoint(mouse): self.sfx.play("click"); self.start_mission(i); return
        elif self.state == "play":
            for index, position in enumerate(self.hotspot_positions()):
                if index not in self.collected and mouse.distance_to(position) < 55:
                    if self.player.distance_to(position) < 110: self.interact()
                    else: self.show_notice("Caminhe até este elemento e aperte E para investigá-lo.")
                    return
        elif self.state == "pause": self.state = "play"
        elif self.state == "minigame" and self.researcher.key != "deuzilene": self.matching_click(mouse)
        elif self.state == "question":
            for i in range(3):
                if self.option_rect(i).collidepoint(mouse): self.answer_question(i); return
        elif self.state in ("result", "timeout"): self.go("select")

    def on_key(self, event):
        key = event.key
        if key == pygame.K_F11:
            self.fullscreen = not self.fullscreen
            self.screen = pygame.display.set_mode((0, 0) if self.fullscreen else (WIDTH, HEIGHT), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE); return
        if key == pygame.K_m: self.toggle_music(); return
        if key == pygame.K_n:
            self.sfx.enabled = not self.sfx.enabled; self.show_notice("Efeitos sonoros ligados." if self.sfx.enabled else "Efeitos sonoros desligados."); self.sfx.play("click"); return
        if self.show_help:
            self.show_help = False; return
        if key == pygame.K_ESCAPE:
            if self.state in ("play", "minigame", "question", "timeout", "result", "pause"): self.go("select")
            elif self.state == "select": self.go("title")
            else: self.running = False
            return
        if key == pygame.K_p and self.state in ("play", "pause"): self.state = "pause" if self.state == "play" else "play"; return
        if key in (pygame.K_h, pygame.K_F1) and self.state in ("title", "select"): self.show_help = True; return
        if self.state == "title" and key in (pygame.K_RETURN, pygame.K_SPACE): self.sfx.play("click"); self.go("select")
        elif self.state == "pause" and key in (pygame.K_RETURN, pygame.K_SPACE): self.state = "play"
        elif self.state == "select":
            if key in (pygame.K_LEFT, pygame.K_a): self.selection = (self.selection - 1) % 4; self.sfx.play("click", .5)
            elif key in (pygame.K_RIGHT, pygame.K_d): self.selection = (self.selection + 1) % 4; self.sfx.play("click", .5)
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4): self.selection = key - pygame.K_1; self.sfx.play("click", .5)
            elif key in (pygame.K_RETURN, pygame.K_SPACE): self.sfx.play("click"); self.start_mission(self.selection)
            elif key == pygame.K_F9:
                if self.reset_armed: self.progress = {}; self.save_progress(); self.reset_armed = 0; self.show_notice("Progresso zerado.")
                else: self.reset_armed = 3.0; self.show_notice("Aperte F9 de novo para zerar estrelas e pontos.", 3)
        elif self.state == "play" and key == pygame.K_e: self.interact()
        elif self.state == "minigame":
            if self.researcher.key == "deuzilene": self.rhythm_input(key)
            elif pygame.K_1 <= key <= pygame.K_3 and key - pygame.K_1 < len(self.mini_pairs()):
                (self.select_clue if self.mini_selected is None else self.try_match)(key - pygame.K_1)
            elif key == pygame.K_BACKSPACE: self.mini_selected = None
        elif self.state == "question" and key in (pygame.K_1, pygame.K_2, pygame.K_3): self.answer_question(key - pygame.K_1)
        elif self.state in ("result", "timeout"):
            if key in (pygame.K_RETURN, pygame.K_SPACE): self.go("select")
            elif key == pygame.K_r: self.start_mission(self.active)

    # ------------------------------------------------------------- desenho: personagens
    def scaled(self, image, scale):
        if scale == 1: return image
        key = (id(image), scale)
        if key not in self.scaled_cache: self.scaled_cache[key] = pygame.transform.smoothscale(image, (int(128 * scale), int(128 * scale)))
        return self.scaled_cache[key]

    def shadow(self, x, y, width):
        s = pygame.Surface((width, width // 3), pygame.SRCALPHA); pygame.draw.ellipse(s, (0, 0, 0, 70), s.get_rect())
        self.canvas.blit(s, s.get_rect(center=(x, y - 2)))

    def placeholder(self, x, y, researcher, scale, bob=0):
        """Bonequinha de reserva — usada apenas quando os sprites oficiais não estão na pasta."""
        s = scale; y = y - bob
        pygame.draw.rect(self.canvas, researcher.color, (x - 24 * s, y - 62 * s, 48 * s, 56 * s), border_radius=int(14 * s))
        pygame.draw.rect(self.canvas, INK, (x - 24 * s, y - 62 * s, 48 * s, 56 * s), 3, border_radius=int(14 * s))
        pygame.draw.circle(self.canvas, (236, 196, 156), (int(x), int(y - 82 * s)), int(22 * s))
        pygame.draw.arc(self.canvas, (60, 40, 35), (x - 24 * s, y - 108 * s, 48 * s, 40 * s), 0, math.pi, int(10 * s))
        for dx in (-8, 8): pygame.draw.circle(self.canvas, INK, (int(x + dx * s), int(y - 80 * s)), max(2, int(3 * s)))
        text(self.canvas, researcher.name[0], int(26 * s), INK, x, y - 52 * s, center=True, bold=True)

    def avatar(self, x, y, researcher, *, scale=1, walking=0, bob=0):
        frames = self.animations[researcher.key].get("walk_right" if walking > 0 else "walk_left") if walking else self.animations[researcher.key]["idle"]
        self.shadow(x, y, int(70 * scale))
        if not frames: self.placeholder(x, y, researcher, scale, bob); return
        # O primeiro idle é o retrato frontal aprovado: parados, sempre usamos ele.
        image = frames[self.anim_frame % len(frames)] if walking else frames[0]
        image = self.scaled(image, scale)
        self.canvas.blit(image, image.get_rect(midbottom=(x, y - bob)))

    def action_avatar(self, x, y, name, *, scale=1, bob=0):
        image = self.action_sprites.get(name)
        self.shadow(x, y, int(70 * scale))
        if image: image = self.scaled(image, scale); self.canvas.blit(image, image.get_rect(midbottom=(x, y - bob)))
        else: self.placeholder(x, y, RESEARCHERS[ACTION_OWNER[name]], scale, bob)

    def draw_grown_plant(self, position, grow=1.0):
        x, y = position; g = ease_out(grow)
        pygame.draw.ellipse(self.canvas, (110, 72, 40), (x - 24, y + 13, 48, 12))
        pygame.draw.rect(self.canvas, (58, 112, 57), (x - 3, y + 18 - 24 * g, 6, 24 * g))
        if g > .35:
            q = (g - .35) / .65
            pygame.draw.ellipse(self.canvas, LEAF, (x - 20 * q, y - 10 * q, 21 * q, 13 * q)); pygame.draw.ellipse(self.canvas, LEAF, (x - 1, y - 17 * q, 21 * q, 14 * q))
        if g > .9: pygame.draw.circle(self.canvas, GOLD, (x + 4, y - 18), 6)

    def bubble(self, x, top, content, *, width=330, tail_up=False):
        lines = wrap(content, 15, False, width - 28); height = max(44, 22 + len(lines) * 21)
        x = clamp(x, width // 2 + 14, WIDTH - width // 2 - 14); top = int(top)
        panel(self.canvas, pygame.Rect(x - width // 2, top, width, height), (250, 249, 236), 13)
        if tail_up: pygame.draw.polygon(self.canvas, (250, 249, 236), [(x - 16, top), (x + 6, top), (x - 4, top - 14)])
        else: pygame.draw.polygon(self.canvas, (250, 249, 236), [(x - 16, top + height), (x + 6, top + height), (x - 4, top + height + 14)])
        text(self.canvas, content, 15, INK, x, top + 10, center=True, max_width=width - 28)

    def draw_hotspot(self, position, label, index):
        x, y = position; pulse = math.sin(self.time * 6 + index); bob = int(math.sin(self.time * 3 + index) * 4)
        glow(self.canvas, (x, y + bob), 62, (255, 230, 110), 130)
        pygame.draw.circle(self.canvas, (255, 239, 117), (x, y + bob), int(40 + pulse * 4), 3)
        panel(self.canvas, pygame.Rect(x - 26, y - 26 + bob, 52, 52), (26, 80, 70), 13); self.draw_item_icon(x, y + bob, label)
        panel(self.canvas, pygame.Rect(x - 70, y - 66 + bob, 140, 28), (3, 39, 42, 230), 9)
        text(self.canvas, label.upper(), 14, WHITE, x, y - 62 + bob, center=True, bold=True)

    def draw_item_icon(self, x, y, label):
        """Pequenos objetos pixelados desenhados no próprio jogo, sem asset extra."""
        name = label.lower(); c = self.canvas
        if name == "sementes":
            for dx, dy in ((-8, 5), (2, -4), (9, 8)): pygame.draw.ellipse(c, (120, 72, 35), (x + dx - 5, y + dy - 4, 10, 8))
        elif name == "água": pygame.draw.polygon(c, RIVER, [(x, y - 16), (x - 12, y + 8), (x, y + 17), (x + 12, y + 8)])
        elif name in ("caderno", "livro", "documento", "leitura"):
            pygame.draw.rect(c, (245, 239, 192), (x - 13, y - 15, 26, 31), border_radius=3)
            pygame.draw.line(c, self.researcher.color, (x - 8, y - 6), (x + 8, y - 6), 2); pygame.draw.line(c, self.researcher.color, (x - 8, y + 2), (x + 8, y + 2), 2)
        elif name == "mapa":
            pygame.draw.polygon(c, (231, 216, 161), [(x - 16, y - 12), (x - 4, y - 16), (x + 5, y - 10), (x + 16, y - 14), (x + 13, y + 14), (x + 2, y + 10), (x - 8, y + 15), (x - 16, y + 10)])
            pygame.draw.line(c, RIVER, (x - 4, y - 13), (x - 8, y + 12), 2); pygame.draw.line(c, RIVER, (x + 5, y - 10), (x + 2, y + 10), 2)
        elif name in ("código", "linguagem"):
            panel(c, pygame.Rect(x - 17, y - 12, 34, 24), (103, 184, 105), 6); text(c, "</>" if name == "código" else "...", 13, INK, x, y - 9, center=True, bold=True)
        elif name == "ritmo": draw_note_icon(c, x - 2, y - 2, GOLD)
        elif name == "extensão":
            pygame.draw.circle(c, GOLD, (x - 8, y - 3), 6); pygame.draw.circle(c, GOLD, (x + 8, y - 3), 6); pygame.draw.line(c, GOLD, (x - 2, y + 8), (x + 2, y + 8), 4)
        elif name == "inclusão":
            for dx in (-10, 0, 10): pygame.draw.circle(c, (WHITE, GOLD, CORAL)[(dx + 10) // 10], (x + dx, y - 4), 6)
            pygame.draw.arc(c, WHITE, (x - 15, y - 2, 30, 18), math.pi, math.tau, 3)
        elif name == "equidade":
            pygame.draw.line(c, GOLD, (x - 15, y + 12), (x + 15, y + 12), 3); pygame.draw.line(c, GOLD, (x, y - 14), (x, y + 12), 3)
            pygame.draw.line(c, GOLD, (x - 14, y - 8), (x + 14, y - 8), 3); pygame.draw.circle(c, WHITE, (x - 14, y - 2), 5); pygame.draw.circle(c, WHITE, (x + 14, y - 2), 5)
        elif name == "formação":
            pygame.draw.polygon(c, WHITE, [(x, y - 14), (x - 18, y - 4), (x, y + 6), (x + 18, y - 4)]); pygame.draw.rect(c, WHITE, (x - 9, y + 3, 18, 9))
        else:
            pygame.draw.circle(c, self.researcher.color, (x, y), 18); text(c, "!", 24, WHITE, x, y - 13, center=True, bold=True)

    def footer(self, label):
        panel(self.canvas, pygame.Rect(215, 674, 850, 32), (2, 30, 33, 225), 10); text(self.canvas, label, 14, WHITE, 640, 681, center=True, bold=True)

    def draw_motes(self):
        for m in self.motes:
            x = m[0] + math.sin(self.time * .6 + m[2]) * 20; y = (m[1] - self.time * m[3]) % (HEIGHT - 80) + 70
            alpha = 40 + int(30 * (.5 + .5 * math.sin(self.time * 2 + m[2]))) // 10 * 10
            glow(self.canvas, (x, y), 9, (255, 240, 150), alpha)

    # ------------------------------------------------------------- desenho: telas
    def background(self, mode="facade"):
        source = self.backgrounds.get(mode)
        if source: self.canvas.blit(source, (0, 0)); return
        self.canvas.blit(self.fallback_sky, (0, 0))
        for i in range(5):
            cx = (i * 330 + self.time * (10 + i * 3)) % (WIDTH + 300) - 150; cy = 70 + (i * 53) % 110
            for dx, dy, r in ((0, 0, 34), (34, 8, 28), (-34, 10, 26), (8, -14, 26)): pygame.draw.circle(self.canvas, (250, 252, 252), (int(cx + dx), cy + dy), r)
        self.canvas.blit(self.fallback_fg, (0, 0))

    def draw_title(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); veil.fill((4, 29, 35, 125)); self.canvas.blit(veil, (0, 0))
        panel(self.canvas, pygame.Rect(135, 112, 1010, 490), PANEL, 30)
        bob = math.sin(self.time * 2) * 4
        text(self.canvas, "PESQUISADORAS", 62, WHITE, 640, 168 + bob, center=True, bold=True, shadow=True); text(self.canvas, "EM AÇÃO", 62, GOLD, 640, 238 - bob, center=True, bold=True, shadow=True)
        text(self.canvas, "Explore o campus, encontre pistas e faça ciência acontecer.", 25, WHITE, 640, 330, center=True)
        text(self.canvas, "Cada missão dura até 3 minutos, tem minidesafio, estrelas de curiosidade e uma pergunta no final.", 18, (214, 235, 221), 640, 374, center=True)
        for i, researcher in enumerate(RESEARCHERS):
            self.avatar(285 + i * 235, 575, researcher, scale=.78, bob=abs(math.sin(self.time * 2.4 + i * 1.3)) * 10)
        total = sum(self.best(i)["stars"] for i in range(4))
        if total:
            for s in range(12): draw_star(self.canvas, 640 - 11 * 14 + s * 28, 462, 9, GOLD if s < total else (60, 96, 96))
        blink = 200 + int(55 * math.sin(self.time * 4)); text(self.canvas, "APERTE ENTER OU CLIQUE PARA COMEÇAR", 20, (blink, blink, 150), 640, 418, center=True, bold=True)
        self.footer("ENTER: COMEÇAR  |  H: COMO JOGAR  |  M: MÚSICA  |  N: EFEITOS  |  F11: TELA CHEIA")

    def draw_select(self):
        panel(self.canvas, pygame.Rect(72, 92, 1136, 535), PANEL, 26); text(self.canvas, "ESCOLHA SUA MISSÃO", 34, WHITE, 640, 128, center=True, bold=True)
        total = sum(self.best(i)["stars"] for i in range(4)); score = sum(self.best(i)["score"] for i in range(4))
        text(self.canvas, f"Todas podem ser jogadas em qualquer ordem.   Estrelas: {total}/12   Pontos: {score}", 18, MUTED, 640, 176, center=True)
        for i, r in enumerate(RESEARCHERS):
            rect = self.card_rect(i).move(0, int(-14 * self.card_lift[i])); selected = i == self.selection
            if selected: glow(self.canvas, rect.center, 190, r.color, 70)
            panel(self.canvas, rect, r.color if selected else CARD, 20, WHITE if selected else None)
            self.avatar(rect.centerx, rect.y + 121, r, scale=.88, bob=abs(math.sin(self.time * 5)) * 8 * self.card_lift[i])
            ink = INK if selected else WHITE
            text(self.canvas, r.name.upper(), 20, ink, rect.centerx, rect.y + 158, center=True, bold=True)
            text(self.canvas, r.area, 15, INK if selected else (220, 239, 219), rect.centerx, rect.y + 192, center=True, max_width=195)
            best = self.best(i)
            for s in range(3): draw_star(self.canvas, rect.centerx - 34 + s * 34, rect.y + 246, 13, GOLD if s < best["stars"] else (95, 125, 120), INK if selected else None)
            text(self.canvas, f"MELHOR: {best['score']}" if best["score"] else "3 MINUTOS", 14, ink if selected else GOLD, rect.centerx, rect.y + 272, center=True, bold=True)
        text(self.canvas, "Dica: pegue as estrelas de curiosidade, erre pouco e termine rápido para ganhar 3 estrelas.", 18, GOLD, 640, 566, center=True)
        self.footer("CLIQUE EM UMA PESQUISADORA  |  SETAS + ENTER  |  H: AJUDA  |  F9 (2X): ZERAR PROGRESSO  |  ESC: VOLTAR")

    def draw_hud(self, show_stats=True):
        panel(self.canvas, pygame.Rect(20, 14, 1240, 62), PANEL, 16)
        text(self.canvas, "PESQUISADORAS EM AÇÃO", 18, MUTED, 42, 22, bold=True); text(self.canvas, self.researcher.name.upper(), 22, self.researcher.color, 42, 42, bold=True)
        if not show_stats: return
        text(self.canvas, f"PONTOS  {self.score}", 21, WHITE, 330, 30, bold=True)
        draw_star(self.canvas, 560, 45, 13, GOLD); text(self.canvas, f"{self.bonus_got}/{len(self.bonus)}", 20, GOLD, 582, 34, bold=True)
        text(self.canvas, f"PISTAS {len(self.collected)}/{len(self.researcher.points)}", 20, WHITE, 690, 34, bold=True)
        draw_note_icon(self.canvas, 880, 44, LEAF if self.music_loaded and not self.music_paused else CORAL, self.music_loaded and not self.music_paused)
        draw_speaker_icon(self.canvas, 930, 45, LEAF if self.sfx.enabled and self.sfx.ok else CORAL, self.sfx.enabled and self.sfx.ok)
        minutes, secs = divmod(int(math.ceil(self.seconds)), 60); low = self.seconds < 30
        color = CORAL if low and int(self.time * 3) % 2 == 0 else (GOLD if self.seconds >= 30 else WHITE)
        text(self.canvas, f"TEMPO  {minutes}:{secs:02d}", 22, color, 1000, 24, bold=True)
        ratio = self.seconds / MISSION_SECONDS
        pygame.draw.rect(self.canvas, (30, 62, 64), (1000, 56, 232, 8), border_radius=4)
        pygame.draw.rect(self.canvas, LEAF if ratio > .33 else (GOLD if ratio > .15 else CORAL), (1000, 56, int(232 * ratio), 8), border_radius=4)

    def draw_play(self):
        self.tint.set_alpha(int(70 * (1 - self.seconds / MISSION_SECONDS))); self.canvas.blit(self.tint, (0, 0))
        self.draw_motes()
        positions = self.hotspot_positions()
        # banner da missão
        if self.mission_t < 12 or len(self.collected) == 0:
            panel(self.canvas, pygame.Rect(180, 84, 920, 73), (3, 39, 42, 218), 14)
            text(self.canvas, self.researcher.place.upper(), 24, WHITE, 640, 92, center=True, bold=True); text(self.canvas, self.researcher.goal, 16, (223, 242, 224), 640, 124, center=True, max_width=850)
        for index, (pos, point) in enumerate(zip(positions, self.researcher.points)):
            if index not in self.collected: self.draw_hotspot(pos, point[0], index)
            elif self.researcher.key == "lucilene": self.draw_grown_plant(pos, (self.time - self.collect_time.get(index, 0)) / 1.3)
            else:
                glow(self.canvas, pos, 34, LEAF, 90); pygame.draw.circle(self.canvas, LEAF, pos, 16); draw_check(self.canvas, pos[0], pos[1], 16, INK, 3)
        for b in self.bonus:
            if not b["got"]:
                x, y = b["pos"]; y += int(math.sin(self.time * 3 + b["phase"]) * 5)
                glow(self.canvas, (x, y), 30, GOLD, 100); draw_star(self.canvas, x, y, 13 + math.sin(self.time * 6 + b["phase"]) * 2, GOLD, WHITE)
        moving = self.vel.length() > 30 and not self.action_time
        walking = (self.facing if moving else 0); bob = abs(math.sin(self.time * 12)) * 4 if moving else 0
        px, py = int(self.player.x), int(self.player.y)
        if self.action_time and self.action_name: self.action_avatar(px, py, self.action_name, bob=abs(math.sin(self.time * 14)) * 5)
        else: self.avatar(px, py, self.researcher, walking=walking, bob=bob)
        # seta de orientação
        closest = self.nearest_hotspot()
        if closest and self.player.distance_to(closest[1]) > 190 and not self.action_time:
            d = (closest[1] - pygame.Vector2(px, py - 60)).normalize(); c = pygame.Vector2(px, py - 60) + d * (92 + math.sin(self.time * 6) * 5)
            ang = math.atan2(d.y, d.x); pts = [(c.x + math.cos(ang) * 13, c.y + math.sin(ang) * 13), (c.x + math.cos(ang + 2.5) * 11, c.y + math.sin(ang + 2.5) * 11), (c.x + math.cos(ang - 2.5) * 11, c.y + math.sin(ang - 2.5) * 11)]
            pygame.draw.polygon(self.canvas, GOLD, pts); pygame.draw.polygon(self.canvas, WHITE, pts, 2)
        if closest and self.player.distance_to(closest[1]) < 85: draw_keycap(self.canvas, int(closest[1].x), int(closest[1].y) + 62, "E")
        self.particles.draw(self.canvas)
        self.canvas.blit(self.vignette, (0, 0))
        self.draw_hud()
        full = len(self.collected) == len(self.researcher.points)
        message = self.notice if self.notice_time else (f"Vamos investigar {closest[2][0]}. Aperte E!" if closest and self.player.distance_to(closest[1]) < 155 else ("Siga os marcadores com ! amarelo — e pegue as estrelas!" if not self.collected else ""))
        if message:
            h = max(44, 22 + len(wrap(message, 15, False, 392)) * 21); top = py - 150 - h
            if top < 165: self.bubble(px, py + 20, message, width=420, tail_up=True)
            else: self.bubble(px, top, message, width=420)
        if full and not self.action_time:
            pulse = 17 + int(2 * math.sin(self.time * 6)); text(self.canvas, "PISTAS REUNIDAS — APERTE E PARA O MINIDESAFIO", pulse, GOLD, 640, 622, center=True, bold=True, shadow=True)
        self.footer("WASD / SETAS: MOVER  |  SHIFT: CORRER  |  E: AGIR  |  P: PAUSA  |  M: MÚSICA  |  CLIQUE: SELECIONAR")

    def draw_matching_minigame(self):
        pairs = self.mini_pairs(); panel(self.canvas, pygame.Rect(70, 82, 1140, 555), PANEL, 26)
        text(self.canvas, "MINIDESAFIO: CONECTE AS PISTAS", 31, GOLD, 640, 104, center=True, bold=True)
        text(self.canvas, "Clique (ou digite o número) de uma pista e depois da ação que completa a investigação.", 18, WHITE, 640, 150, center=True)
        text(self.canvas, "PISTAS", 18, MUTED, 300, 200, center=True, bold=True); text(self.canvas, "AÇÕES", 18, MUTED, 975, 200, center=True, bold=True)
        for slot, source in enumerate(self.mini_order):   # linhas das conexões feitas
            if source in self.mini_matched: pygame.draw.line(self.canvas, LEAF, self.left_rect(source).midright, self.right_rect(slot).midleft, 6)
        action = {"lucilene": "water", "ana_claudia": "map_ana", "maria_francisca": "map_francisca"}.get(self.researcher.key)
        if action: self.action_avatar(640, 450, action, scale=.92, bob=abs(math.sin(self.time * 3)) * 4)
        for i, (source, _) in enumerate(pairs):
            rect = self.left_rect(i); selected, done = self.mini_selected == i, i in self.mini_matched; hover = rect.collidepoint(self.mouse) and not done
            panel(self.canvas, rect, LEAF if done else (GOLD if selected else (CARD_HOVER if hover else CARD)), 16, WHITE if selected else None)
            pygame.draw.circle(self.canvas, INK if (done or selected) else (30, 60, 61), (rect.x + 38, rect.centery), 19)
            if done: draw_check(self.canvas, rect.x + 38, rect.centery, 18, LEAF, 4)
            else: text(self.canvas, str(i + 1), 22, GOLD, rect.x + 38, rect.centery - 13, center=True, bold=True)
            text(self.canvas, source, 20, INK if (done or selected) else WHITE, rect.x + 72, rect.centery - 12, bold=True)
        hint_slot = None
        if self.mini_streak >= 2 and self.mini_selected is not None: hint_slot = self.mini_order.index(self.mini_selected)
        for slot, source in enumerate(self.mini_order):
            rect = self.right_rect(slot); done = source in self.mini_matched; wrong = slot in self.mini_flash
            hover = rect.collidepoint(self.mouse) and not done and self.mini_selected is not None
            color = LEAF if done else (CORAL if wrong else (CARD_HOVER if hover else CARD))
            panel(self.canvas, rect, color, 16, GOLD if (slot == hint_slot and int(self.time * 3) % 2 == 0) else None)
            pygame.draw.circle(self.canvas, INK if (done or wrong) else (30, 60, 61), (rect.x + 36, rect.centery), 19)
            if done: draw_check(self.canvas, rect.x + 36, rect.centery, 18, LEAF, 4)
            elif wrong: draw_cross(self.canvas, rect.x + 36, rect.centery, 14, CORAL, 4)
            else: text(self.canvas, str(slot + 1), 22, GOLD, rect.x + 36, rect.centery - 13, center=True, bold=True)
            text(self.canvas, pairs[source][1], 19, INK if (done or wrong) else WHITE, rect.x + 70, rect.centery - 11, bold=True)
        if self.notice_time: self.bubble(640, 548, self.notice, width=560)
        self.footer("CLIQUE OU DIGITE 1-3 (PISTA E DEPOIS AÇÃO)  |  BACKSPACE: DESFAZER  |  ESC: MISSÕES")

    def draw_rhythm_minigame(self):
        hit_x, lane_y, speed = 420, 345, 300
        panel(self.canvas, pygame.Rect(110, 110, 1060, 500), PANEL, 28)
        text(self.canvas, "MINIDESAFIO: RITMO E CÓDIGO", 33, GOLD, 640, 134, center=True, bold=True)
        text(self.canvas, "Quando a seta chegar ao círculo, aperte a mesma seta (ou WASD). Acerte 8 de 12!", 19, WHITE, 640, 182, center=True)
        beat = (self.rh_time % .66) / .66
        self.action_avatar(235, 520, "dance", scale=.9, bob=abs(math.sin(self.rh_time * math.tau / .66)) * 14)
        panel(self.canvas, pygame.Rect(330, lane_y - 55, 800, 110), (20, 52, 56), 20, (80, 130, 125))
        glow(self.canvas, (hit_x, lane_y), 70, (255, 235, 140), int(60 + 70 * (1 - beat)))
        pygame.draw.circle(self.canvas, WHITE, (hit_x, lane_y), 46, 4); pygame.draw.circle(self.canvas, GOLD, (hit_x, lane_y), int(52 + 6 * (1 - beat)), 2)
        for n in self.rh_notes:
            x = hit_x + (n["t"] - self.rh_time) * speed
            if x > 1115 or x < 335: continue
            if n["state"] in ("perfect", "good"): continue
            miss = n["state"] == "miss"
            draw_arrow(self.canvas, n["key"], x, lane_y, 58, (90, 100, 100) if miss else ARROW_COLORS[n["key"]], WHITE if not miss else None)
        for i, d in enumerate(("left", "down", "up", "right")):   # legenda
            draw_arrow(self.canvas, d, 590 + i * 90, 440, 40, ARROW_COLORS[d], WHITE)
        text(self.canvas, "ACERTOS", 18, MUTED, 590, 472, bold=True); text(self.canvas, f"{self.rh_hits}/12", 28, GOLD, 590, 496, bold=True)
        text(self.canvas, "COMBO", 18, MUTED, 830, 472, bold=True); text(self.canvas, f"x{self.rh_combo}", 28, GOLD, 830, 496, bold=True)
        if self.rh_time < self.rh_notes[0]["t"] - .2: text(self.canvas, "PREPARE-SE...", 22, WHITE, 640, 245, center=True, bold=True)
        if self.notice_time: self.bubble(640, 548, self.notice, width=520)
        self.footer("USE AS SETAS (OU WASD)  |  ESC: VOLTAR ÀS MISSÕES")

    def draw_minigame(self):
        self.draw_motes()
        if self.researcher.key == "deuzilene": self.draw_rhythm_minigame()
        else: self.draw_matching_minigame()

    def draw_question(self):
        self.draw_hud(False); panel(self.canvas, pygame.Rect(130, 118, 1020, 495), PANEL, 25)
        text(self.canvas, "DESAFIO DE CONHECIMENTO", 20, GOLD, 640, 150, center=True, bold=True)
        text(self.canvas, self.researcher.question, 31, WHITE, 640, 192, center=True, bold=True, max_width=850)
        for i in range(3):
            rect = self.option_rect(i); original = self.q_order[i]; wrong = i in self.q_wrong; right = self.q_done and original == self.researcher.correct
            hover = rect.collidepoint(self.mouse) and not wrong and not self.q_done
            dx = int(math.sin(self.time * 70) * 9 * self.q_shake.get(i, 0) * 2)
            rect = rect.move(dx, 0)
            panel(self.canvas, rect, LEAF if right else ((120, 55, 55) if wrong else (CARD_HOVER if hover else CARD)), 13, WHITE if hover else None)
            pygame.draw.circle(self.canvas, (24, 52, 54), (rect.x + 34, rect.centery), 18)
            if right: draw_check(self.canvas, rect.x + 34, rect.centery, 16, LEAF, 4)
            elif wrong: draw_cross(self.canvas, rect.x + 34, rect.centery, 14, CORAL, 4)
            else: text(self.canvas, str(i + 1), 20, GOLD, rect.x + 34, rect.centery - 11, center=True, bold=True)
            text(self.canvas, self.researcher.answers[original], 18, INK if right else (WHITE if not wrong else (230, 190, 190)), rect.x + 66, rect.centery - 11, max_width=780)
        if self.q_wrong and not self.q_done:
            text(self.canvas, "Quase! Releia as pistas e pense em aprender e agir juntos. Tente outra opção.", 18, (255, 215, 180), 640, 572, center=True, bold=True)
        self.footer("1, 2 OU 3: RESPONDER  |  CLIQUE NA RESPOSTA")

    def draw_result(self):
        panel(self.canvas, pygame.Rect(170, 112, 940, 508), PANEL, 28)
        pop = ease_out(self.result_t / .5)
        text(self.canvas, "MISSÃO CONCLUÍDA!", int(30 + 11 * pop), GOLD, 640, 140, center=True, bold=True)
        for i in range(3):
            got = i < self.stars and self.result_t > 1.2 + i * .45
            r = 32 + (8 * ease_out((self.result_t - 1.2 - i * .45) / .3) if got else 0)
            draw_star(self.canvas, 540 + i * 100, 262, r, GOLD if got else (66, 98, 98), WHITE if got else None)
        labels = [(k, v) for k, v in self.tally.items()]
        for i, (label, value) in enumerate(labels):
            if self.result_t < .4 + i * .25: break
            y = 318 + i * 31
            text(self.canvas, label, 20, MUTED, 400, y); text(self.canvas, f"+{value}", 20, WHITE, 880, y, bold=True)
            pygame.draw.line(self.canvas, (60, 100, 100), (400, y + 28), (880, y + 28), 1)
        if self.result_t > 1.9:
            text(self.canvas, f"TOTAL  {self.final_score}", 30, GOLD, 640, 478, center=True, bold=True)
            if self.result_new_best: text(self.canvas, "NOVO RECORDE!", 18, LEAF, 640, 518, center=True, bold=True)
        if self.result_t > 2.3:
            if len(self.completed) == 4: text(self.canvas, "Você conheceu as quatro pesquisadoras. Parabéns, missões completas!", 18, WHITE, 640, 546, center=True, bold=True)
            else: text(self.canvas, "Você conectou pesquisa, trajetória e território. Uma nova missão está disponível.", 18, WHITE, 640, 546, center=True)
            text(self.canvas, "“Às vezes precisamos recuar, mas desistir nunca.”", 18, (210, 238, 215), 640, 578, center=True)
        self.footer("ENTER: VOLTAR ÀS MISSÕES  |  R: JOGAR DE NOVO PARA GANHAR MAIS ESTRELAS")

    def draw_timeout(self):
        panel(self.canvas, pygame.Rect(190, 190, 900, 320), PANEL, 28)
        text(self.canvas, "O TEMPO DESTA MISSÃO TERMINOU", 32, GOLD, 640, 236, center=True, bold=True)
        text(self.canvas, "Sem problema: cada pesquisadora pode ser explorada novamente. Agora você já sabe onde estão as pistas.", 21, WHITE, 640, 312, center=True, max_width=710)
        text(self.canvas, f"Pistas encontradas: {len(self.collected)}/{len(self.researcher.points)}   Estrelas de curiosidade: {self.bonus_got}/{len(self.bonus)}", 18, MUTED, 640, 424, center=True)
        self.footer("R: TENTAR DE NOVO  |  ENTER: VOLTAR ÀS MISSÕES")

    def draw_overlay_panel(self, title, lines):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); veil.fill((3, 20, 24, 170)); self.canvas.blit(veil, (0, 0))
        panel(self.canvas, pygame.Rect(300, 120, 680, 480), PANEL, 28, (80, 130, 125)); text(self.canvas, title, 36, GOLD, 640, 150, center=True, bold=True)
        for i, (keys, desc) in enumerate(lines):
            y = 222 + i * 40; text(self.canvas, keys, 19, WHITE, 345, y, bold=True); text(self.canvas, desc, 19, MUTED, 650, y)

    CONTROLS = (("WASD / SETAS", "Mover (Shift corre)"), ("E", "Investigar pista / abrir minidesafio"), ("1, 2, 3 (ou clique)", "Escolher respostas e associações"),
                ("SETAS (ou WASD)", "Ritmo da Deuzilene"), ("P", "Pausar"), ("M / N", "Música / efeitos sonoros"), ("F11", "Tela cheia"), ("ESC", "Voltar"))

    def draw(self):
        self.background("aerial" if self.state == "title" else "facade")
        if self.state == "title": self.draw_motes(); self.draw_title()
        elif self.state == "select": self.draw_motes(); self.draw_select()
        elif self.state in ("play", "pause"): self.draw_play()
        elif self.state == "minigame": self.draw_minigame()
        elif self.state == "question": self.draw_question()
        elif self.state == "result": self.draw_result()
        elif self.state == "timeout": self.draw_timeout()
        if self.state not in ("play", "pause"): self.particles.draw(self.canvas)
        if self.state in ("select", "title") and self.notice_time: self.bubble(640, 20, self.notice, width=420, tail_up=False)
        if self.state == "pause": self.draw_overlay_panel("PAUSA", self.CONTROLS); text(self.canvas, "P ou ENTER: continuar   |   ESC: voltar às missões", 18, WHITE, 640, 556, center=True, bold=True)
        if self.show_help: self.draw_overlay_panel("COMO JOGAR", self.CONTROLS); text(self.canvas, "Aperte qualquer tecla para fechar", 18, WHITE, 640, 556, center=True, bold=True)
        for txt, x, y, life, color, size in self.popups: text(self.canvas, txt, size, color, x, y, center=True, bold=True, shadow=True)
        if self.fade > 0:
            veil = pygame.Surface((WIDTH, HEIGHT)); veil.set_alpha(int(self.fade)); self.canvas.blit(veil, (0, 0))
        self.present()

    def present(self):
        vr = self.view_rect(); self.screen.fill((0, 0, 0))
        offset = (random.randint(-5, 5), random.randint(-4, 4)) if self.shake > 0 else (0, 0)
        image = self.canvas if vr.size == (WIDTH, HEIGHT) else pygame.transform.smoothscale(self.canvas, vr.size)
        self.screen.blit(image, vr.move(offset)); pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, .05)
            for event in pygame.event.get(): self.handle_event(event)
            self.update(dt); self.draw()
        pygame.quit()


def smoke_test():
    game = Game()
    for index in range(4):
        game.start_mission(index); game.fade, game.state, game.next_state = 0, "play", None
        for state in ("play", "minigame", "question", "result", "timeout"):
            game.state = state; game.enter(state); game.update(.016); game.draw()
    pygame.quit(); print("Pygame pronto: sprites e quatro missões carregados.")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv: smoke_test()
    else: Game().run()
