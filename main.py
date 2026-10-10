"""Pesquisadoras em Jogo — exploração individual curta e educativa.
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
        pygame.init(); pygame.display.set_caption("Pesquisadoras em Jogo — IFAM")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas, self.clock = pygame.Surface((WIDTH, HEIGHT)), pygame.time.Clock()
        self.running, self.fullscreen, self.state = True, False, "title"
        self.selection, self.active, self.player = 0, None, pygame.Vector2(150, 560)
        self.collected, self.notice, self.notice_time, self.question_answer = set(), "", 0.0, None
        self.seconds, self.frame_time, self.anim_frame, self.completed = 180.0, 0.0, 0, set()
        self.animations = self.load_animations()

    def load_animations(self):
        animations = {}
        for researcher in RESEARCHERS:
            animations[researcher.key] = {}
            for action in ("idle", "walk_left", "walk_right"):
                paths = sorted(glob.glob(os.path.join(SPRITES_DIR, researcher.key, action, "*.png")))
                animations[researcher.key][action] = [pygame.transform.scale(pygame.image.load(path).convert_alpha(), (128, 128)) for path in paths]
        return animations

    @property
    def researcher(self): return RESEARCHERS[self.active]

    def start_mission(self, index):
        self.active, self.state, self.player = index, "play", pygame.Vector2(150, 560)
        self.collected, self.question_answer, self.notice, self.seconds, self.anim_frame = set(), None, "", 180.0, 0

    def hotspot_positions(self):
        return [(265, 355), (460, 250), (640, 420), (825, 260), (1035, 365)] if len(self.researcher.points) == 5 else [(290, 355), (650, 270), (1015, 385)]

    def show_notice(self, message): self.notice, self.notice_time = message, 5.0

    def interact(self):
        for index, (position, item) in enumerate(zip(self.hotspot_positions(), self.researcher.points)):
            if index not in self.collected and self.player.distance_to(position) < 80:
                self.collected.add(index); self.show_notice(f"{item[0]}: {item[1]}"); return
        if len(self.collected) == len(self.researcher.points): self.state = "question"
        else: self.show_notice("Aproxime-se de um ponto brilhante e aperte E.")

    def update(self, dt):
        if self.notice_time: self.notice_time = max(0, self.notice_time - dt)
        if self.state != "play": return
        self.seconds = max(0, self.seconds - dt)
        if not self.seconds: self.state = "timeout"; return
        k = pygame.key.get_pressed(); direction = pygame.Vector2(int(k[pygame.K_d] or k[pygame.K_RIGHT]) - int(k[pygame.K_a] or k[pygame.K_LEFT]), int(k[pygame.K_s] or k[pygame.K_DOWN]) - int(k[pygame.K_w] or k[pygame.K_UP]))
        if direction.length_squared():
            self.player += direction.normalize() * 260 * dt; self.player.x = max(65, min(WIDTH - 65, self.player.x)); self.player.y = max(190, min(HEIGHT - 95, self.player.y))
            self.frame_time += dt
            if self.frame_time >= .12: self.anim_frame, self.frame_time = self.anim_frame + 1, 0

    def handle_event(self, event):
        if event.type == pygame.QUIT: self.running = False
        if event.type == pygame.VIDEORESIZE and not self.fullscreen: self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        if event.type != pygame.KEYDOWN: return
        if event.key == pygame.K_F11:
            self.fullscreen = not self.fullscreen; self.screen = pygame.display.set_mode((0, 0) if self.fullscreen else (WIDTH, HEIGHT), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE); return
        if event.key == pygame.K_ESCAPE:
            if self.state in ("play", "question", "timeout", "result"): self.state = "select"
            else: self.running = False
            return
        if self.state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE): self.state = "select"
        elif self.state == "select":
            if event.key in (pygame.K_LEFT, pygame.K_a): self.selection = (self.selection - 1) % 4
            elif event.key in (pygame.K_RIGHT, pygame.K_d): self.selection = (self.selection + 1) % 4
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4): self.selection = event.key - pygame.K_1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): self.start_mission(self.selection)
        elif self.state == "play" and event.key == pygame.K_e: self.interact()
        elif self.state == "question" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.question_answer, self.state = event.key - pygame.K_1, "result"
            if self.question_answer == self.researcher.correct: self.completed.add(self.active)
        elif self.state in ("result", "timeout") and event.key in (pygame.K_RETURN, pygame.K_SPACE): self.state = "select"

    def background(self):
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
            image = frames[self.anim_frame % len(frames)]
            if scale != 1: image = pygame.transform.smoothscale(image, (int(128 * scale), int(128 * scale)))
            self.canvas.blit(image, image.get_rect(midbottom=(x, y)))

    def footer(self, label):
        panel(self.canvas, pygame.Rect(245, 674, 790, 32), (2, 30, 33, 225), 10); text(self.canvas, label, 14, WHITE, 640, 682, center=True, bold=True)

    def draw_title(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); veil.fill((4, 29, 35, 125)); self.canvas.blit(veil, (0, 0)); panel(self.canvas, pygame.Rect(135, 122, 1010, 450), PANEL, 30)
        text(self.canvas, "PESQUISADORAS", 62, WHITE, 640, 175, center=True, bold=True); text(self.canvas, "EM JOGO", 62, GOLD, 640, 245, center=True, bold=True)
        text(self.canvas, "Explore o campus, encontre pistas e faça ciência acontecer.", 25, WHITE, 640, 338, center=True); text(self.canvas, "Cada missão dura até 3 minutos e tem um desafio de conhecimento no final.", 19, (214, 235, 221), 640, 385, center=True)
        for i, researcher in enumerate(RESEARCHERS): self.avatar(285 + i * 235, 505, researcher, scale=.78)
        self.footer("ENTER: ESCOLHER UMA PESQUISADORA")

    def draw_select(self):
        panel(self.canvas, pygame.Rect(72, 92, 1136, 535), PANEL, 26); text(self.canvas, "ESCOLHA SUA MISSÃO", 34, WHITE, 640, 130, center=True, bold=True); text(self.canvas, "Todas podem ser jogadas em qualquer ordem.", 18, (215, 238, 223), 640, 177, center=True)
        for i, r in enumerate(RESEARCHERS):
            x, selected = 115 + i * 275, i == self.selection; panel(self.canvas, pygame.Rect(x, 232, 240, 290), r.color if selected else (38, 76, 77), 20); self.avatar(x + 120, 353, r, scale=.88)
            text(self.canvas, r.name.upper(), 20, INK if selected else WHITE, x + 120, 390, center=True, bold=True); text(self.canvas, r.area, 15, INK if selected else (220, 239, 219), x + 120, 426, center=True, max_width=195); text(self.canvas, "✓ CONCLUÍDA" if i in self.completed else "3 MINUTOS", 14, INK if selected else GOLD, x + 120, 487, center=True, bold=True)
        self.footer("← → ou 1–4: ESCOLHER  |  ENTER: INICIAR")

    def draw_hud(self):
        panel(self.canvas, pygame.Rect(20, 18, 1240, 58), PANEL, 16); text(self.canvas, "PESQUISADORAS EM JOGO", 23, WHITE, 42, 33, bold=True); text(self.canvas, self.researcher.name.upper(), 19, self.researcher.color, 540, 35, bold=True)
        minutes, seconds = divmod(int(math.ceil(self.seconds)), 60); text(self.canvas, f"TEMPO  {minutes}:{seconds:02d}", 21, GOLD, 1065, 33, bold=True)

    def draw_play(self):
        self.draw_hud(); text(self.canvas, self.researcher.place.upper(), 26, WHITE, 640, 100, center=True, bold=True); text(self.canvas, self.researcher.goal, 18, INK, 640, 138, center=True, max_width=860)
        for index, (pos, point) in enumerate(zip(self.hotspot_positions(), self.researcher.points)):
            if index not in self.collected:
                pygame.draw.circle(self.canvas, (255, 244, 173), pos, int(28 + 5 * math.sin(pygame.time.get_ticks() / 160 + index))); pygame.draw.circle(self.canvas, self.researcher.color, pos, 20); text(self.canvas, point[0], 16, WHITE, pos[0], pos[1] - 50, center=True, bold=True)
        k = pygame.key.get_pressed(); self.avatar(int(self.player.x), int(self.player.y), self.researcher, walking=int(k[pygame.K_d] or k[pygame.K_RIGHT]) - int(k[pygame.K_a] or k[pygame.K_LEFT]))
        panel(self.canvas, pygame.Rect(28, 650, 330, 42), (3, 35, 38, 224), 12); text(self.canvas, f"PISTAS {len(self.collected)}/{len(self.researcher.points)}", 16, WHITE, 47, 662, bold=True); self.footer("WASD / SETAS: MOVER  |  E: INTERAGIR")
        if self.notice_time: panel(self.canvas, pygame.Rect(210, 534, 860, 86), (250, 248, 231), 16); text(self.canvas, self.notice, 18, INK, 640, 551, center=True, max_width=790)
        if len(self.collected) == len(self.researcher.points): text(self.canvas, "PISTAS REUNIDAS — APERTE E PARA O DESAFIO", 17, GOLD, 640, 615, center=True, bold=True)

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
        self.background()
        if self.state == "title": self.draw_title()
        elif self.state == "select": self.draw_select()
        elif self.state == "play": self.draw_play()
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
