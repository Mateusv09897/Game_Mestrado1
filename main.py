"""Pesquisadoras em Ação — exploração individual curta e educativa.
Controles: WASD/setas movimentam | E interage | 1-4 escolhem personagem.
"""
from __future__ import annotations

import glob
import math
import os
import sys
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT, FPS = 1280, 720, 60
WHITE, INK = (247, 250, 247), (17, 38, 42)
GREEN, LEAF, RIVER, SKY = (24, 111, 74), (103, 184, 105), (55, 157, 190), (176, 225, 238)
GOLD, CORAL, PURPLE, PANEL = (247, 190, 67), (232, 99, 88), (118, 84, 154), (8, 42, 47, 232)
SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", "sprites")
BACKGROUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")


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


def text(surface, content, size, color, x, y, *, center=False, bold=False, max_width=None):
    font = pygame.font.SysFont("arial", size, bold=bold)
    words, lines, current = content.split(), [], ""
    if max_width:
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or font.size(candidate)[0] <= max_width: current = candidate
            else: lines.append(current); current = word
        if current: lines.append(current)
    else: lines = [content]
    for index, line in enumerate(lines):
        image = font.render(line, True, color)
        rect = image.get_rect(center=(x, y + index * (size + 6))) if center else image.get_rect(topleft=(x, y + index * (size + 6)))
        surface.blit(image, rect)
    return len(lines) * (size + 6)


def panel(surface, rect, color=PANEL, radius=18):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


class Game:
    def __init__(self):
        pygame.init(); pygame.display.set_caption("Pesquisadoras em Ação — IFAM")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas, self.clock = pygame.Surface((WIDTH, HEIGHT)), pygame.time.Clock()
        self.running, self.fullscreen, self.state = True, False, "title"
        self.selection, self.active, self.player = 0, None, pygame.Vector2(150, 560)
        self.collected, self.notice, self.notice_time, self.question_answer = set(), "", 0.0, None
        self.seconds, self.frame_time, self.anim_frame, self.completed = 180.0, 0.0, 0, set()
        self.mini_selected, self.mini_matched, self.mini_progress = None, set(), 0
        self.rhythm_sequence = (pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_UP, pygame.K_RIGHT, pygame.K_LEFT)
        self.animations, self.backgrounds = self.load_animations(), self.load_backgrounds()
        self.action_sprites, self.action_name, self.action_time = self.load_action_sprites(), None, 0.0
        self.load_music()

    def load_animations(self):
        animations = {}
        for researcher in RESEARCHERS:
            animations[researcher.key] = {}
            for action in ("idle", "walk_left", "walk_right"):
                paths = sorted(glob.glob(os.path.join(SPRITES_DIR, researcher.key, action, "*.png")))
                animations[researcher.key][action] = [pygame.transform.scale(pygame.image.load(path).convert_alpha(), (128, 128)) for path in paths]
        return animations

    def load_backgrounds(self):
        backgrounds = {}
        for key, filename in (("facade", "ifam_cmc_fachada_8bit.jpg"), ("aerial", "ifam_cmc_aereo_8bit.jpg")):
            path = os.path.join(BACKGROUNDS_DIR, filename)
            if os.path.exists(path):
                backgrounds[key] = pygame.image.load(path).convert()
        return backgrounds

    def load_action_sprites(self):
        """Ações fornecidas pela equipe: usadas como feedback real de cada missão."""
        names = {
            "water": ("lucilene", "lucilene_water_01.png"),
            "dance": ("deuzilene", "deuzilene_dance_01.png"),
            "map_ana": ("ana_claudia", "ana_claudia_map_01.png"),
            "map_francisca": ("maria_francisca", "maria_francisca_map_01.png"),
        }
        actions = {}
        for key, (researcher, filename) in names.items():
            path = os.path.join(SPRITES_DIR, researcher, filename)
            if os.path.exists(path): actions[key] = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (128, 128))
        return actions

    def load_music(self):
        """Toca uma trilha opcional quando o arquivo for adicionado ao projeto."""
        for filename in ("trilha.ogg", "trilha.mp3", "trilha.wav"):
            path = os.path.join(os.path.dirname(__file__), "assets", "music", filename)
            if os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.32)
                    pygame.mixer.music.play(-1)
                except pygame.error:
                    pass
                return

    @property
    def researcher(self): return RESEARCHERS[self.active]

    def start_mission(self, index):
        self.active, self.state, self.player = index, "play", pygame.Vector2(150, 560)
        self.collected, self.question_answer, self.notice, self.notice_time, self.seconds, self.anim_frame = set(), None, "", 0.0, 180.0, 0
        self.mini_selected, self.mini_matched, self.mini_progress = None, set(), 0
        self.action_name, self.action_time = None, 0.0

    def hotspot_positions(self):
        return [(265, 355), (460, 250), (640, 420), (825, 260), (1035, 365)] if len(self.researcher.points) == 5 else [(290, 355), (650, 270), (1015, 385)]

    def show_notice(self, message): self.notice, self.notice_time = message, 5.0

    def play_action(self, name, duration=.8):
        self.action_name, self.action_time = name, duration

    def canvas_mouse(self, position):
        screen_w, screen_h = self.screen.get_size()
        return pygame.Vector2(position[0] * WIDTH / screen_w, position[1] * HEIGHT / screen_h)

    def card_rect(self, index):
        return pygame.Rect(115 + index * 275, 232, 240, 290)

    def nearest_hotspot(self):
        candidates = [(index, pygame.Vector2(position), item) for index, (position, item) in enumerate(zip(self.hotspot_positions(), self.researcher.points)) if index not in self.collected]
        return min(candidates, key=lambda candidate: self.player.distance_to(candidate[1])) if candidates else None

    def answer_question(self, index):
        self.question_answer, self.state = index, "result"
        if index == self.researcher.correct: self.completed.add(self.active)

    def interact(self):
        for index, (position, item) in enumerate(zip(self.hotspot_positions(), self.researcher.points)):
            if index not in self.collected and self.player.distance_to(position) < 80:
                self.collected.add(index); self.show_notice(f"{item[0]}: {item[1]}")
                if self.researcher.key == "lucilene": self.play_action("water", 1.1)
                return
        if len(self.collected) == len(self.researcher.points): self.state = "minigame"
        else: self.show_notice("Aproxime-se de um ponto brilhante e aperte E.")

    def mini_pairs(self):
        """Pares para os minidesafios de associação, após a exploração."""
        pairs = {
            "lucilene": (("SEMENTES", "PLANTAR"), ("ÁGUA", "CULTIVAR"), ("CADERNO", "REGISTRAR")),
            "ana_claudia": (("DOCUMENTO", "CONSULTAR FONTE"), ("MAPA", "REDESENHAR ROTA"), ("LIVRO", "COMPARTILHAR")),
            "maria_francisca": (("LINGUAGEM", "ESCUTAR"), ("EXTENSÃO", "DIALOGAR"), ("EQUIDADE", "ACOLHER")),
        }
        return pairs.get(self.researcher.key, ())

    def matching_click(self, mouse):
        pairs = self.mini_pairs()
        for index in range(len(pairs)):
            if pygame.Rect(135, 238 + index * 105, 335, 74).collidepoint(mouse):
                if index not in self.mini_matched:
                    self.mini_selected = index; self.show_notice(f"{pairs[index][0].title()} selecionado. Agora escolha a ação.")
                return
        target_order = (2, 0, 1)
        for slot, source_index in enumerate(target_order):
            if pygame.Rect(810, 238 + slot * 105, 335, 74).collidepoint(mouse):
                if self.mini_selected is None:
                    self.show_notice("Primeiro selecione um item à esquerda.")
                elif self.mini_selected == source_index:
                    self.mini_matched.add(source_index); self.mini_selected = None
                    self.show_notice("Boa associação!")
                    if len(self.mini_matched) == len(pairs): self.state = "question"
                else:
                    self.show_notice("Tente outra ação: pense no que essa pista permite fazer.")
                return

    def rhythm_input(self, key):
        if key not in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN): return
        if key == self.rhythm_sequence[self.mini_progress]:
            self.mini_progress += 1
            self.show_notice("No ritmo certo!")
            if self.mini_progress == len(self.rhythm_sequence): self.state = "question"
        else:
            self.mini_progress = 0; self.show_notice("Ops! A sequência recomeçou. Observe as setas.")

    def update(self, dt):
        if self.notice_time: self.notice_time = max(0, self.notice_time - dt)
        if self.state != "play": return
        self.seconds = max(0, self.seconds - dt)
        if not self.seconds: self.state = "timeout"; return
        if self.action_time:
            self.action_time = max(0, self.action_time - dt)
            if not self.action_time: self.action_name = None
            return
        k = pygame.key.get_pressed(); direction = pygame.Vector2(int(k[pygame.K_d] or k[pygame.K_RIGHT]) - int(k[pygame.K_a] or k[pygame.K_LEFT]), int(k[pygame.K_s] or k[pygame.K_DOWN]) - int(k[pygame.K_w] or k[pygame.K_UP]))
        if direction.length_squared():
            self.player += direction.normalize() * 260 * dt; self.player.x = max(65, min(WIDTH - 65, self.player.x)); self.player.y = max(190, min(HEIGHT - 95, self.player.y))
            self.frame_time += dt
            if self.frame_time >= .12: self.anim_frame, self.frame_time = self.anim_frame + 1, 0

    def handle_event(self, event):
        if event.type == pygame.QUIT: self.running = False
        if event.type == pygame.VIDEORESIZE and not self.fullscreen: self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        if event.type == pygame.MOUSEMOTION and self.state == "select":
            mouse = self.canvas_mouse(event.pos)
            for index in range(len(RESEARCHERS)):
                if self.card_rect(index).collidepoint(mouse): self.selection = index
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.canvas_mouse(event.pos)
            if self.state == "title": self.state = "select"; return
            if self.state == "select":
                for index in range(len(RESEARCHERS)):
                    if self.card_rect(index).collidepoint(mouse): self.start_mission(index); return
            if self.state == "play":
                for index, position in enumerate(self.hotspot_positions()):
                    if index not in self.collected and mouse.distance_to(position) < 55:
                        if self.player.distance_to(position) < 100: self.interact()
                        else: self.show_notice("Caminhe até este elemento e aperte E para investigá-lo.")
                        return
            if self.state == "minigame" and self.researcher.key != "deuzilene":
                self.matching_click(mouse); return
            if self.state == "question":
                for index in range(3):
                    if pygame.Rect(205, 330 + index * 78, 870, 58).collidepoint(mouse): self.answer_question(index); return
            if self.state in ("result", "timeout"): self.state = "select"; return
        if event.type != pygame.KEYDOWN: return
        if event.key == pygame.K_F11:
            self.fullscreen = not self.fullscreen; self.screen = pygame.display.set_mode((0, 0) if self.fullscreen else (WIDTH, HEIGHT), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE); return
        if event.key == pygame.K_ESCAPE:
            if self.state in ("play", "minigame", "question", "timeout", "result"): self.state = "select"
            else: self.running = False
            return
        if self.state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE): self.state = "select"
        elif self.state == "select":
            if event.key in (pygame.K_LEFT, pygame.K_a): self.selection = (self.selection - 1) % 4
            elif event.key in (pygame.K_RIGHT, pygame.K_d): self.selection = (self.selection + 1) % 4
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4): self.selection = event.key - pygame.K_1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): self.start_mission(self.selection)
        elif self.state == "play" and event.key == pygame.K_e: self.interact()
        elif self.state == "minigame" and self.researcher.key == "deuzilene": self.rhythm_input(event.key)
        elif self.state == "question" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.answer_question(event.key - pygame.K_1)
        elif self.state in ("result", "timeout") and event.key in (pygame.K_RETURN, pygame.K_SPACE): self.state = "select"

    def background(self, mode="facade"):
        source = self.backgrounds.get(mode)
        if source:
            self.canvas.blit(pygame.transform.smoothscale(source, (WIDTH, HEIGHT)), (0, 0))
            return
        self.canvas.fill(SKY); pygame.draw.circle(self.canvas, (255, 239, 181), (1090, 105), 58)
        pygame.draw.polygon(self.canvas, (83, 151, 99), [(0, 330), (210, 205), (460, 350), (710, 210), (970, 345), (1280, 220), (1280, 520), (0, 520)])
        pygame.draw.rect(self.canvas, (92, 151, 92), (0, 485, WIDTH, 235)); pygame.draw.rect(self.canvas, (207, 178, 117), (0, 555, WIDTH, 165))
        panel(self.canvas, pygame.Rect(435, 180, 410, 220), (238, 241, 229), 8); pygame.draw.rect(self.canvas, GREEN, (420, 160, 440, 34), border_radius=5); text(self.canvas, "IFAM", 23, WHITE, 640, 165, center=True, bold=True)
        for x in range(465, 810, 66):
            for y in (225, 285, 345): pygame.draw.rect(self.canvas, (80, 139, 150), (x, y, 35, 28), border_radius=4)
        for x in range(90, 1220, 135): pygame.draw.circle(self.canvas, LEAF, (x, 486), 32); pygame.draw.rect(self.canvas, (83, 92, 54), (x - 4, 490, 8, 57))

    def avatar(self, x, y, researcher, *, scale=1, walking=0):
        action = "idle" if not walking else ("walk_right" if walking > 0 else "walk_left")
        frames = self.animations[researcher.key].get(action) or self.animations[researcher.key]["idle"]
        if frames:
            # O primeiro idle é o retrato frontal aprovado. Não reutilizamos um
            # quadro lateral/traseiro depois da caminhada, que escondia olhos/cabelo.
            image = frames[0] if not walking else frames[self.anim_frame % len(frames)]
            if scale != 1: image = pygame.transform.smoothscale(image, (int(128 * scale), int(128 * scale)))
            self.canvas.blit(image, image.get_rect(midbottom=(x, y)))

    def action_avatar(self, x, y, name, *, scale=1):
        image = self.action_sprites.get(name)
        if image:
            if scale != 1: image = pygame.transform.smoothscale(image, (int(128 * scale), int(128 * scale)))
            self.canvas.blit(image, image.get_rect(midbottom=(x, y)))

    def draw_grown_plant(self, position):
        x, y = position
        pygame.draw.ellipse(self.canvas, (110, 72, 40), (x - 24, y + 13, 48, 12))
        pygame.draw.rect(self.canvas, (58, 112, 57), (x - 3, y - 6, 6, 24))
        pygame.draw.ellipse(self.canvas, LEAF, (x - 20, y - 10, 21, 13))
        pygame.draw.ellipse(self.canvas, LEAF, (x - 1, y - 17, 21, 14))
        pygame.draw.circle(self.canvas, (247, 190, 67), (x + 4, y - 18), 6)

    def bubble(self, x, y, content, *, width=330):
        x = max(width // 2 + 14, min(WIDTH - width // 2 - 14, x))
        panel(self.canvas, pygame.Rect(x - width // 2, y, width, 66), (250, 249, 236), 13)
        pygame.draw.polygon(self.canvas, (250, 249, 236), [(x - 16, y + 66), (x + 6, y + 66), (x - 4, y + 80)])
        text(self.canvas, content, 15, INK, x, y + 12, center=True, max_width=width - 28)

    def draw_hotspot(self, position, label, index):
        x, y = position; pulse = int(5 * math.sin(pygame.time.get_ticks() / 160 + index))
        pygame.draw.circle(self.canvas, (255, 239, 117), (x, y), 37 + pulse)
        panel(self.canvas, pygame.Rect(x - 26, y - 26, 52, 52), (26, 80, 70), 13)
        self.draw_item_icon(x, y, label)
        panel(self.canvas, pygame.Rect(x - 70, y - 63, 140, 28), (3, 39, 42, 230), 9)
        text(self.canvas, label.upper(), 14, WHITE, x, y - 58, center=True, bold=True)

    def draw_item_icon(self, x, y, label):
        """Pequenos objetos pixelados desenhados no próprio jogo, sem asset extra."""
        name = label.lower()
        if name == "sementes":
            for dx, dy in ((-8, 5), (2, -4), (9, 8)): pygame.draw.ellipse(self.canvas, (120, 72, 35), (x + dx - 5, y + dy - 4, 10, 8))
        elif name == "água":
            pygame.draw.polygon(self.canvas, RIVER, [(x, y - 16), (x - 12, y + 8), (x, y + 17), (x + 12, y + 8)])
        elif name in ("caderno", "livro", "documento"):
            pygame.draw.rect(self.canvas, (245, 239, 192), (x - 13, y - 15, 26, 31), border_radius=3)
            pygame.draw.line(self.canvas, self.researcher.color, (x - 8, y - 6), (x + 8, y - 6), 2)
            pygame.draw.line(self.canvas, self.researcher.color, (x - 8, y + 2), (x + 8, y + 2), 2)
        elif name == "mapa":
            pygame.draw.polygon(self.canvas, (231, 216, 161), [(x - 16, y - 12), (x - 4, y - 16), (x + 5, y - 10), (x + 16, y - 14), (x + 13, y + 14), (x + 2, y + 10), (x - 8, y + 15), (x - 16, y + 10)])
            pygame.draw.line(self.canvas, RIVER, (x - 4, y - 13), (x - 8, y + 12), 2)
            pygame.draw.line(self.canvas, RIVER, (x + 5, y - 10), (x + 2, y + 10), 2)
        elif name in ("código", "linguagem"):
            panel(self.canvas, pygame.Rect(x - 17, y - 12, 34, 24), (103, 184, 105), 6)
            text(self.canvas, "</>" if name == "código" else "…", 13, INK, x, y - 8, center=True, bold=True)
        elif name == "ritmo":
            text(self.canvas, "♪", 34, GOLD, x, y - 20, center=True, bold=True)
        elif name == "extensão":
            pygame.draw.circle(self.canvas, GOLD, (x - 8, y - 3), 6); pygame.draw.circle(self.canvas, GOLD, (x + 8, y - 3), 6)
            pygame.draw.line(self.canvas, GOLD, (x - 2, y + 8), (x + 2, y + 8), 4)
        else:
            pygame.draw.circle(self.canvas, self.researcher.color, (x, y), 18)
            text(self.canvas, "!", 24, WHITE, x, y - 14, center=True, bold=True)

    def footer(self, label):
        panel(self.canvas, pygame.Rect(245, 674, 790, 32), (2, 30, 33, 225), 10); text(self.canvas, label, 14, WHITE, 640, 682, center=True, bold=True)

    def draw_matching_minigame(self):
        pairs, target_order = self.mini_pairs(), (2, 0, 1)
        panel(self.canvas, pygame.Rect(70, 82, 1140, 555), PANEL, 26)
        text(self.canvas, "MINIDESAFIO: CONECTE AS PISTAS", 31, GOLD, 640, 116, center=True, bold=True)
        text(self.canvas, "Clique em uma pista e depois na ação que completa a investigação.", 18, WHITE, 640, 161, center=True)
        text(self.canvas, "PISTAS", 18, (215, 238, 223), 300, 205, center=True, bold=True); text(self.canvas, "AÇÕES", 18, (215, 238, 223), 975, 205, center=True, bold=True)
        action_name = {"lucilene": "water", "ana_claudia": "map_ana", "maria_francisca": "map_francisca"}.get(self.researcher.key)
        if action_name: self.action_avatar(640, 432, action_name, scale=.92)
        for index, (source, _) in enumerate(pairs):
            y = 238 + index * 105; selected = self.mini_selected == index; done = index in self.mini_matched
            color = LEAF if done else (self.researcher.color if selected else (42, 82, 83))
            panel(self.canvas, pygame.Rect(135, y, 335, 74), color, 16)
            text(self.canvas, "✓" if done else source[:1], 28, INK if (done or selected) else GOLD, 165, y + 19, bold=True)
            text(self.canvas, source, 20, INK if (done or selected) else WHITE, 210, y + 25, bold=True)
        for slot, source_index in enumerate(target_order):
            y = 238 + slot * 105; done = source_index in self.mini_matched
            panel(self.canvas, pygame.Rect(810, y, 335, 74), LEAF if done else (42, 82, 83), 16)
            text(self.canvas, "✓" if done else "→", 25, INK if done else GOLD, 840, y + 20, bold=True)
            text(self.canvas, pairs[source_index][1], 19, INK if done else WHITE, 883, y + 26, bold=True)
        if self.notice_time: self.bubble(640, 530, self.notice, width=500)
        self.footer("CLIQUE EM UMA PISTA E NA AÇÃO CORRESPONDENTE  |  ESC: VOLTAR ÀS MISSÕES")

    def draw_rhythm_minigame(self):
        arrows = {pygame.K_LEFT: "←", pygame.K_RIGHT: "→", pygame.K_UP: "↑", pygame.K_DOWN: "↓"}
        panel(self.canvas, pygame.Rect(110, 120, 1060, 470), PANEL, 28)
        text(self.canvas, "MINIDESAFIO: RITMO E CÓDIGO", 33, GOLD, 640, 165, center=True, bold=True)
        self.action_avatar(210, 255, "dance", scale=.72)
        text(self.canvas, "Repita a sequência usando as setas. Cada acerto faz a investigação avançar.", 19, WHITE, 640, 212, center=True)
        start_x = 365
        for index, key in enumerate(self.rhythm_sequence):
            x = start_x + index * 110; active = index == self.mini_progress; done = index < self.mini_progress
            panel(self.canvas, pygame.Rect(x, 300, 78, 78), LEAF if done else (self.researcher.color if active else (42, 82, 83)), 16)
            text(self.canvas, "✓" if done else arrows[key], 39, INK if (done or active) else WHITE, x + 39, 315, center=True, bold=True)
        text(self.canvas, f"SEQUÊNCIA {self.mini_progress}/{len(self.rhythm_sequence)}", 21, (215, 238, 223), 640, 432, center=True, bold=True)
        if self.notice_time: self.bubble(640, 472, self.notice, width=510)
        self.footer("USE AS SETAS DO TECLADO  |  ESC: VOLTAR ÀS MISSÕES")

    def draw_minigame(self):
        if self.researcher.key == "deuzilene": self.draw_rhythm_minigame()
        else: self.draw_matching_minigame()

    def draw_title(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); veil.fill((4, 29, 35, 125)); self.canvas.blit(veil, (0, 0)); panel(self.canvas, pygame.Rect(135, 122, 1010, 450), PANEL, 30)
        text(self.canvas, "PESQUISADORAS", 62, WHITE, 640, 175, center=True, bold=True); text(self.canvas, "EM AÇÃO", 62, GOLD, 640, 245, center=True, bold=True)
        text(self.canvas, "Explore o campus, encontre pistas e faça ciência acontecer.", 25, WHITE, 640, 338, center=True); text(self.canvas, "Cada missão dura até 3 minutos e tem um desafio de conhecimento no final.", 19, (214, 235, 221), 640, 385, center=True)
        for i, researcher in enumerate(RESEARCHERS): self.avatar(285 + i * 235, 505, researcher, scale=.78)
        self.footer("CLIQUE OU ENTER: ESCOLHER UMA PESQUISADORA")

    def draw_select(self):
        panel(self.canvas, pygame.Rect(72, 92, 1136, 535), PANEL, 26); text(self.canvas, "ESCOLHA SUA MISSÃO", 34, WHITE, 640, 130, center=True, bold=True); text(self.canvas, "Todas podem ser jogadas em qualquer ordem.", 18, (215, 238, 223), 640, 177, center=True)
        for i, r in enumerate(RESEARCHERS):
            x, selected = 115 + i * 275, i == self.selection; panel(self.canvas, pygame.Rect(x, 232, 240, 290), r.color if selected else (38, 76, 77), 20); self.avatar(x + 120, 353, r, scale=.88)
            text(self.canvas, r.name.upper(), 20, INK if selected else WHITE, x + 120, 390, center=True, bold=True); text(self.canvas, r.area, 15, INK if selected else (220, 239, 219), x + 120, 426, center=True, max_width=195); text(self.canvas, "✓ CONCLUÍDA" if i in self.completed else "3 MINUTOS", 14, INK if selected else GOLD, x + 120, 487, center=True, bold=True)
        self.footer("CLIQUE EM UMA PESQUISADORA  |  OU USE ← → E ENTER")

    def draw_hud(self):
        panel(self.canvas, pygame.Rect(20, 18, 1240, 58), PANEL, 16); text(self.canvas, "PESQUISADORAS EM AÇÃO", 23, WHITE, 42, 33, bold=True); text(self.canvas, self.researcher.name.upper(), 19, self.researcher.color, 540, 35, bold=True)
        minutes, seconds = divmod(int(math.ceil(self.seconds)), 60); text(self.canvas, f"TEMPO  {minutes}:{seconds:02d}", 21, GOLD, 1065, 33, bold=True)

    def draw_play(self):
        self.draw_hud(); panel(self.canvas, pygame.Rect(180, 84, 920, 73), (3, 39, 42, 218), 14)
        text(self.canvas, self.researcher.place.upper(), 24, WHITE, 640, 94, center=True, bold=True); text(self.canvas, self.researcher.goal, 16, (223, 242, 224), 640, 126, center=True, max_width=850)
        for index, (pos, point) in enumerate(zip(self.hotspot_positions(), self.researcher.points)):
            if index not in self.collected: self.draw_hotspot(pos, point[0], index)
        if self.researcher.key == "lucilene":
            for index in self.collected: self.draw_grown_plant(self.hotspot_positions()[index])
        k = pygame.key.get_pressed()
        if self.action_time and self.action_name: self.action_avatar(int(self.player.x), int(self.player.y), self.action_name)
        else: self.avatar(int(self.player.x), int(self.player.y), self.researcher, walking=int(k[pygame.K_d] or k[pygame.K_RIGHT]) - int(k[pygame.K_a] or k[pygame.K_LEFT]))
        panel(self.canvas, pygame.Rect(28, 650, 330, 42), (3, 35, 38, 224), 12); text(self.canvas, f"PISTAS {len(self.collected)}/{len(self.researcher.points)}", 16, WHITE, 47, 662, bold=True); self.footer("WASD / SETAS: MOVER  |  E: INVESTIGAR  |  CLIQUE: SELECIONAR")
        closest = self.nearest_hotspot()
        if self.notice_time: self.bubble(int(self.player.x), int(self.player.y) - 175, self.notice, width=420)
        elif closest and self.player.distance_to(closest[1]) < 155: self.bubble(int(self.player.x), int(self.player.y) - 175, f"Vamos investigar {closest[2][0]}. Aperte E!", width=330)
        elif not self.collected: self.bubble(int(self.player.x), int(self.player.y) - 175, "Siga os marcadores com ! amarelo.", width=300)
        if len(self.collected) == len(self.researcher.points): text(self.canvas, "PISTAS REUNIDAS — APERTE E PARA O MINIDESAFIO", 17, GOLD, 640, 615, center=True, bold=True)

    def draw_question(self):
        self.draw_hud(); panel(self.canvas, pygame.Rect(130, 118, 1020, 495), PANEL, 25); text(self.canvas, "DESAFIO DE CONHECIMENTO", 20, GOLD, 640, 155, center=True, bold=True); text(self.canvas, self.researcher.question, 31, WHITE, 640, 200, center=True, bold=True, max_width=850)
        for i, answer in enumerate(self.researcher.answers):
            y = 330 + i * 78; panel(self.canvas, pygame.Rect(205, y, 870, 58), (43, 83, 84), 13); text(self.canvas, str(i + 1), 20, GOLD, 235, y + 16, bold=True); text(self.canvas, answer, 18, WHITE, 280, y + 17, max_width=760)
        self.footer("1, 2 OU 3: RESPONDER")

    def draw_result(self):
        right = self.question_answer == self.researcher.correct; panel(self.canvas, pygame.Rect(180, 180, 920, 340), PANEL, 28); text(self.canvas, "MISSÃO CONCLUÍDA!" if right else "QUASE LÁ!", 39, GOLD if right else CORAL, 640, 230, center=True, bold=True)
        message = "Você conectou pesquisa, trajetória e território. Uma nova missão está disponível." if right else "A ideia principal é: aprender e agir juntos amplia as possibilidades. Tente esta missão novamente quando quiser."; text(self.canvas, message, 22, WHITE, 640, 318, center=True, max_width=700); text(self.canvas, "“Às vezes precisamos recuar, mas desistir nunca.”", 19, (210, 238, 215), 640, 410, center=True); self.footer("ENTER: VOLTAR ÀS MISSÕES")

    def draw_timeout(self):
        panel(self.canvas, pygame.Rect(190, 200, 900, 300), PANEL, 28); text(self.canvas, "O TEMPO DESTA MISSÃO TERMINOU", 32, GOLD, 640, 254, center=True, bold=True); text(self.canvas, "Sem problema: cada pesquisadora pode ser explorada novamente. Agora você já sabe onde estão as pistas.", 21, WHITE, 640, 330, center=True, max_width=710); self.footer("ENTER: VOLTAR ÀS MISSÕES")

    def draw(self):
        self.background("aerial" if self.state == "title" else "facade")
        if self.state == "title": self.draw_title()
        elif self.state == "select": self.draw_select()
        elif self.state == "play": self.draw_play()
        elif self.state == "minigame": self.draw_minigame()
        elif self.state == "question": self.draw_question()
        elif self.state == "result": self.draw_result()
        elif self.state == "timeout": self.draw_timeout()
        self.screen.blit(pygame.transform.smoothscale(self.canvas, self.screen.get_size()), (0, 0)); pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get(): self.handle_event(event)
            self.update(dt); self.draw()
        pygame.quit()


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        pygame.init(); Game(); pygame.quit(); print("Pygame pronto: sprites e quatro missões carregados.")
    else: Game().run()
