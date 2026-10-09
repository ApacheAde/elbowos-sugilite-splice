#!/usr/bin/env python3
"""Sugilite Splice — neon helix colour-fuse arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/SUGILITE_SPLICE_ElbowOS.mp4")
TITLE, HANDLE = "SUGILITE SPLICE", "x.com/ElbowOS"
PLUM, INK = (18, 6, 36), (8, 2, 18)
VIOLET, ORCHID = (176, 86, 255), (255, 78, 188)
LIME, CYAN, GOLD, CORAL = (190, 255, 70), (70, 236, 255), (255, 214, 78), (255, 96, 72)
PAL = [ORCHID, LIME, CYAN, GOLD, CORAL]
GATE_Y, BAND = 1180, 130

def hex_pts(x, y, r, ang):
    return [(x + r * math.cos(ang + i * math.pi / 3), y + r * math.sin(ang + i * math.pi / 3)) for i in range(6)]

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not RECORD else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font = pygame.font.SysFont("dejavusans", 72, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 42, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 32, bold=True)
        self.bg = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            pygame.draw.line(self.bg, (int(22 - 12 * t), int(6 + 8 * t), int(40 + 18 * t)), (0, y), (W, y))
        self.reset()

    def reset(self):
        random.seed(7 if RECORD or not PLAY else None)
        self.t = 0
        self.score = 0
        self.streak = 0
        self.gems = []
        self.sparks = []
        self.blooms = []
        self.pid = 0
        self.spawn_at = 8
        self.flash = 0
        self.miss = 0
        self.pop = 0

    def spawn(self):
        match = random.random() < 0.72
        a = random.randrange(5)
        b = a if match else (a + random.randint(1, 4)) % 5
        self.pid += 1
        y = 250 + random.randint(-20, 20)
        self.gems.append({"x": 300, "y": y, "c": a, "p": self.pid, "s": random.random() * 6, "alive": True})
        self.gems.append({"x": 780, "y": y + random.choice([0, 0, 36]), "c": b, "p": self.pid, "s": random.random() * 6, "alive": True})
        self.spawn_at = self.t + random.randint(28, 42)

    def in_gate(self, g):
        return abs(g["y"] - GATE_Y) <= BAND and g["alive"]

    def try_splice(self):
        left = [g for g in self.gems if g["x"] < 540 and self.in_gate(g)]
        right = [g for g in self.gems if g["x"] > 540 and self.in_gate(g)]
        if not left or not right:
            return False
        L, R = min(left, key=lambda g: abs(g["y"] - GATE_Y)), min(right, key=lambda g: abs(g["y"] - GATE_Y))
        if L["c"] == R["c"]:
            L["alive"] = R["alive"] = False
            self.streak += 1
            self.score += 120 + 40 * min(self.streak, 8)
            self.flash, self.pop = 10, 18
            col = PAL[L["c"]]
            self.blooms.append([540, GATE_Y, 20, col])
            for i in range(22):
                ang = i / 22 * math.tau
                self.sparks.append([540, GATE_Y, math.cos(ang) * random.uniform(4, 11), math.sin(ang) * random.uniform(4, 11), col, 22])
            return True
        self.streak = 0
        self.miss = 8
        return False

    def update(self, auto=False):
        self.t += 1
        if self.t >= self.spawn_at:
            self.spawn()
        for g in self.gems:
            g["y"] += 7.4 + min(self.t, 300) * 0.004
            g["s"] += 0.09
        if auto:
            if any(self.in_gate(g) for g in self.gems if g["x"] < 540) and any(self.in_gate(g) for g in self.gems if g["x"] > 540):
                self.try_splice()
        self.gems = [g for g in self.gems if g["alive"] and g["y"] < H + 80]
        for g in list(self.gems):
            if g["y"] > GATE_Y + BAND + 40 and g["alive"]:
                mate = [m for m in self.gems if m["p"] == g["p"] and m is not g]
                if mate and mate[0]["y"] > GATE_Y + BAND:
                    self.streak = 0
        nxt = []
        for s in self.sparks:
            s[0] += s[2]; s[1] += s[3]; s[3] += 0.12; s[5] -= 1
            if s[5] > 0:
                nxt.append(s)
        self.sparks = nxt
        self.blooms = [[b[0], b[1], b[2] + 16, b[3]] for b in self.blooms if b[2] < 420]
        self.flash = max(0, self.flash - 1)
        self.miss = max(0, self.miss - 1)
        self.pop = max(0, self.pop - 1)

    def draw_gem(self, surf, g):
        col = PAL[g["c"]]
        pulse = 1 + 0.06 * math.sin(self.t * 0.3 + g["s"])
        r = 46 * pulse
        glow = pygame.Surface((160, 160), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, 70), (80, 80), 62)
        surf.blit(glow, (g["x"] - 80, g["y"] - 80))
        pts = hex_pts(g["x"], g["y"], r, g["s"])
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, (255, 255, 255), pts, 3)
        pygame.draw.polygon(surf, (255, 255, 255), hex_pts(g["x"], g["y"], r * 0.42, g["s"]), 0)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        for i in range(28):
            y = (i * 78 + self.t * 3) % (H + 80) - 40
            pygame.draw.line(surf, (40, 18, 68), (140, y), (940, y), 1)
        phase = self.t * 0.08
        for i in range(46):
            y = 220 + i * 34
            x1 = 540 + math.sin(phase + i * 0.38) * 150
            x2 = 540 + math.sin(phase + i * 0.38 + math.pi) * 150
            pygame.draw.circle(surf, VIOLET, (int(x1), y), 5)
            pygame.draw.circle(surf, ORCHID, (int(x2), y), 5)
        band = pygame.Surface((W, BAND * 2), pygame.SRCALPHA)
        band.fill((176, 86, 255, 28 + (12 if self.flash else 0)))
        surf.blit(band, (0, GATE_Y - BAND))
        pygame.draw.line(surf, CYAN if self.flash else VIOLET, (120, GATE_Y), (960, GATE_Y), 6)
        pygame.draw.circle(surf, GOLD, (540, GATE_Y), 18 + (6 if self.flash else 0))
        pygame.draw.circle(surf, INK, (540, GATE_Y), 8)
        for g in self.gems:
            self.draw_gem(surf, g)
        for b in self.blooms:
            pygame.draw.circle(surf, b[3], (int(b[0]), int(b[1])), int(b[2]), 4)
        for s in self.sparks:
            pygame.draw.circle(surf, s[4], (int(s[0]), int(s[1])), max(2, s[5] // 5))
        if self.miss:
            pygame.draw.rect(surf, CORAL, (0, 0, W, H), 10)
        banner = pygame.Surface((W, 210), pygame.SRCALPHA)
        banner.fill((8, 2, 18, 170))
        surf.blit(banner, (0, 0))
        title = self.font.render(TITLE, True, ORCHID)
        surf.blit(title, title.get_rect(center=(W // 2, 78)))
        sc = self.mid.render(f"SCORE  {self.score:05d}", True, GOLD if self.pop else CYAN)
        surf.blit(sc, sc.get_rect(center=(W // 2, 150)))
        st = self.small.render(f"STREAK  {self.streak}", True, LIME)
        surf.blit(st, st.get_rect(center=(W // 2, 198)))
        foot = pygame.Surface((W, 120), pygame.SRCALPHA)
        foot.fill((8, 2, 18, 180))
        surf.blit(foot, (0, H - 120))
        h = self.mid.render(HANDLE, True, (230, 210, 255))
        surf.blit(h, h.get_rect(center=(W // 2, H - 72)))
        hint = self.small.render("SPACE  SPLICE", True, VIOLET)
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 28)))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                        self.try_splice()
                    elif ev.key == pygame.K_r:
                        self.reset()
                    elif ev.key == pygame.K_ESCAPE:
                        running = False
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    self.try_splice()
            self.update(False)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               "-preset", "veryfast", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(FPS * SECS):
                self.update(True)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
