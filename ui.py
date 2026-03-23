"""UI renderer — Pygame drawing for pasture, cows, fields, and stat panel."""

import math
import pygame
from config import (
    SCREEN_HEIGHT, PASTURE_WIDTH, PANEL_WIDTH,
    BG_COLOR, PANEL_BG, PANEL_TEXT, PANEL_ACCENT,
    FENCE_ACTIVE_COLOR, BEEP_CLR, VIBRATE_CLR, PULSE_CLR,
    ZONE_BORDER_CLR, GRASS_MAX,
    COW_RADIUS, ARCHETYPE_COLORS, ARCHETYPE_NAMES,
    FENCE_FIELD_RADIUS, REWARD_FIELD_RADIUS,
)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        fname = "consolas"
        self.f_sm  = pygame.font.SysFont(fname, 13)
        self.f_md  = pygame.font.SysFont(fname, 15)
        self.f_lg  = pygame.font.SysFont(fname, 20)
        self.f_ttl = pygame.font.SysFont(fname, 24, bold=True)

        self._field_cache = None
        self._field_key = None

    # ==================================================================
    def draw(self, environment, cows, fence_sys, econ, show_trails=True):
        self.screen.fill(BG_COLOR)
        self._draw_zones(environment)
        if fence_sys.show_fields:
            self._draw_fields(fence_sys)
        if fence_sys.show_fences:
            self._draw_fences(fence_sys)
        if fence_sys.show_destinations:
            self._draw_destinations(fence_sys)
        if show_trails:
            self._draw_trails(cows)
        self._draw_cows(cows)
        self._draw_panel(cows, fence_sys, econ)

    # ==================================================================
    # Pasture elements
    # ==================================================================
    def _draw_zones(self, env):
        for z in env.zones:
            pygame.draw.rect(self.screen, z.get_color(), z.rect)
            pygame.draw.rect(self.screen, ZONE_BORDER_CLR, z.rect, 1)
            lbl = self.f_sm.render(z.name, True, (200, 200, 200))
            self.screen.blit(lbl, (z.rect.x + 5, z.rect.y + 5))
            bw = min(60, z.rect.width - 10)
            bx, by = z.rect.x + 5, z.rect.y + 22
            pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, bw, 4))
            fill = int(bw * z.grass_value / GRASS_MAX)
            gc = (50, 200, 50) if z.grass_value > 40 else (200, 200, 50)
            pygame.draw.rect(self.screen, gc, (bx, by, fill, 4))

    # ------------------------------------------------------------------
    def _draw_fields(self, fs):
        """Render cached influence-field gradient overlay."""
        key = (fs.routing_mode, round(fs.strictness, 2))
        if self._field_key != key:
            self._rebuild_field_cache(fs)
            self._field_key = key
        if self._field_cache:
            self.screen.blit(self._field_cache, (0, 0))

    def _rebuild_field_cache(self, fs):
        surf = pygame.Surface((PASTURE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bands = 4
        for z in fs.get_forbidden_zones():
            fr = FENCE_FIELD_RADIUS * fs.strictness
            for i in range(bands):
                expand = int(fr * (bands - i) / bands)
                alpha = 5 + i * 6
                exp = z.rect.inflate(expand * 2, expand * 2)
                exp = exp.clip(pygame.Rect(0, 0, PASTURE_WIDTH, SCREEN_HEIGHT))
                if exp.width > 0 and exp.height > 0:
                    band = pygame.Surface((exp.width, exp.height), pygame.SRCALPHA)
                    band.fill((255, 50, 50, alpha))
                    surf.blit(band, exp.topleft)
        for z in fs.get_destination_zones():
            for i in range(bands):
                expand = int(REWARD_FIELD_RADIUS * (bands - i) / bands)
                alpha = 3 + i * 4
                exp = z.rect.inflate(expand * 2, expand * 2)
                exp = exp.clip(pygame.Rect(0, 0, PASTURE_WIDTH, SCREEN_HEIGHT))
                if exp.width > 0 and exp.height > 0:
                    band = pygame.Surface((exp.width, exp.height), pygame.SRCALPHA)
                    band.fill((50, 140, 255, alpha))
                    surf.blit(band, exp.topleft)
        self._field_cache = surf

    # ------------------------------------------------------------------
    def _draw_fences(self, fs):
        for z in fs.get_forbidden_zones():
            pygame.draw.rect(self.screen, FENCE_ACTIVE_COLOR, z.rect, 2)
            mx, my = z.rect.center
            sz = 8
            pygame.draw.line(self.screen, FENCE_ACTIVE_COLOR,
                             (mx - sz, my - sz), (mx + sz, my + sz), 2)
            pygame.draw.line(self.screen, FENCE_ACTIVE_COLOR,
                             (mx - sz, my + sz), (mx + sz, my - sz), 2)

    def _draw_destinations(self, fs):
        for z in fs.get_destination_zones():
            pygame.draw.rect(self.screen, PANEL_ACCENT, z.rect, 3)
            cx, cy = z.rect.center
            pts = [(cx, cy - 14), (cx + 11, cy), (cx, cy + 14), (cx - 11, cy)]
            pygame.draw.polygon(self.screen, PANEL_ACCENT, pts, 2)

    # ==================================================================
    def _draw_trails(self, cows):
        for c in cows:
            if len(c.trail) < 2:
                continue
            col = ARCHETYPE_COLORS[c.archetype]
            trail_col = (col[0] * 2 // 5, col[1] * 2 // 5, col[2] * 2 // 5)
            pts = [(int(p[0]), int(p[1])) for p in c.trail]
            pygame.draw.lines(self.screen, trail_col, False, pts, 1)

    # ==================================================================
    def _draw_cows(self, cows):
        for c in cows:
            x, y = int(c.pos[0]), int(c.pos[1])
            col = ARCHETYPE_COLORS[c.archetype]

            if c.current_warning >= 3:
                pygame.draw.circle(self.screen, PULSE_CLR, (x, y), COW_RADIUS + 5, 2)
            elif c.current_warning >= 2:
                pygame.draw.circle(self.screen, VIBRATE_CLR, (x, y), COW_RADIUS + 4, 2)
            elif c.current_warning >= 1:
                pygame.draw.circle(self.screen, BEEP_CLR, (x, y), COW_RADIUS + 3, 1)

            pygame.draw.circle(self.screen, col, (x, y), COW_RADIUS)
            dark = (max(0, col[0] - 60), max(0, col[1] - 60), max(0, col[2] - 60))
            pygame.draw.circle(self.screen, dark, (x, y), COW_RADIUS, 1)

            spd = math.hypot(c.vel[0], c.vel[1])
            if spd > 0.1:
                ex = x + int(c.vel[0] / spd * (COW_RADIUS + 3))
                ey = y + int(c.vel[1] / spd * (COW_RADIUS + 3))
                pygame.draw.line(self.screen, dark, (x, y), (ex, ey), 2)

    # ==================================================================
    # Side panel
    # ==================================================================
    def _draw_panel(self, cows, fs, econ):
        px = PASTURE_WIDTH
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, (55, 55, 75), (px, 0), (px, SCREEN_HEIGHT), 2)

        x = px + 15
        y = 12

        y = self._title_block(x, y)
        y = self._divider(x, y)
        y = self._routing_block(x, y, fs)
        y = self._divider(x, y)

        stats = econ.get_stats(cows)
        containment = fs.get_containment(cows)
        in_target = fs.get_in_target(cows)
        y = self._metrics_block(x, y, stats, containment, in_target)
        y = self._divider(x, y)
        y = self._economics_block(x, y, stats)
        y = self._divider(x, y)
        y = self._fence_stats_block(x, y, stats)
        y = self._divider(x, y)
        y = self._legend_block(x, y, cows)
        y = self._divider(x, y)
        self._controls_block(x, y)

    # --- sub-blocks ---------------------------------------------------
    def _title_block(self, x, y):
        self._text(self.f_ttl, "COW AIRLINES", x, y, PANEL_ACCENT); y += 28
        self._text(self.f_sm, "Virtual Fence Herd Sim", x, y, (150, 150, 170)); y += 22
        return y

    def _routing_block(self, x, y, fs):
        mc = {"neutral": (180, 180, 180), "milk": (100, 210, 100), "meat": (210, 165, 80)}
        self._text(self.f_md, f"Routing: {fs.routing_mode.upper()}", x, y,
                   mc.get(fs.routing_mode, PANEL_TEXT)); y += 20
        self._text(self.f_sm, f"Strictness: {fs.strictness:.1f}x", x, y); y += 18
        return y

    def _metrics_block(self, x, y, stats, containment, in_target):
        self._text(self.f_md, "HERD METRICS", x, y, PANEL_ACCENT); y += 20
        self._stat("Day", str(stats["day"]), x, y); y += 16
        cc = (100, 220, 100) if containment > 80 else (220, 100, 100)
        self._stat("Containment", f"{containment:.0f}%", x, y, cc); y += 16
        tc = (100, 200, 255) if in_target > 50 else (170, 170, 170)
        self._stat("In Target", f"{in_target:.0f}%", x, y, tc); y += 16
        sc = (220, 100, 100) if stats["avg_stress"] > 0.5 else (100, 220, 100)
        self._stat("Avg Stress", f"{stats['avg_stress']:.3f}", x, y, sc); y += 16
        self._stat("Avg Learning", f"{stats['avg_learning']:.3f}", x, y); y += 16
        self._stat("Avg Hunger", f"{stats['avg_hunger']:.2f}", x, y); y += 18
        return y

    def _economics_block(self, x, y, stats):
        self._text(self.f_md, "ECONOMICS", x, y, PANEL_ACCENT); y += 20
        self._stat("Milk Index", f"{stats['total_milk']:.1f}", x, y, (200, 230, 255)); y += 16
        self._stat("Meat Index", f"{stats['total_meat']:.1f}", x, y, (255, 200, 150)); y += 16
        self._stat("Milk Time", f"{stats['pct_time_milk']:.0f}%", x, y, (180, 210, 240)); y += 16
        self._stat("Meat Time", f"{stats['pct_time_meat']:.0f}%", x, y, (240, 190, 140)); y += 18
        return y

    def _fence_stats_block(self, x, y, stats):
        self._text(self.f_md, "FENCE EVENTS", x, y, PANEL_ACCENT); y += 20
        self._stat("Beeps", str(stats["total_beeps"]), x, y, BEEP_CLR); y += 16
        self._stat("Vibrations", str(stats["total_vibrations"]), x, y, VIBRATE_CLR); y += 16
        self._stat("Pulses", str(stats["total_pulses"]), x, y, PULSE_CLR); y += 16
        self._stat("Pulses/Cow", f"{stats['pulses_per_cow']:.1f}", x, y); y += 18
        return y

    def _legend_block(self, x, y, cows):
        self._text(self.f_md, "COW TYPES", x, y, PANEL_ACCENT); y += 20
        for arch, col in ARCHETYPE_COLORS.items():
            pygame.draw.circle(self.screen, col, (x + 6, y + 6), 5)
            n = sum(1 for c in cows if c.archetype == arch)
            self._text(self.f_sm, f"{ARCHETYPE_NAMES[arch]} ({n})", x + 18, y)
            y += 16
        y += 8
        return y

    def _controls_block(self, x, y):
        self._text(self.f_md, "CONTROLS", x, y, PANEL_ACCENT); y += 20
        for key, act in (
            ("SPACE", "Pause / Resume"),
            ("R",     "Reset"),
            ("F",     "Toggle Fences"),
            ("V",     "Toggle Fields"),
            ("G",     "Toggle Destinations"),
            ("T",     "Toggle Trails"),
            ("+/-",   "Fence Strictness"),
            ("1",     "Milk Routing"),
            ("2",     "Meat Routing"),
            ("3",     "Neutral Routing"),
        ):
            self._text(self.f_sm, f"[{key}]", x, y, (180, 180, 220))
            self._text(self.f_sm, act, x + 55, y, (140, 140, 150))
            y += 15
        return y

    # --- helpers ------------------------------------------------------
    def _divider(self, x, y):
        pygame.draw.line(self.screen, (55, 55, 75),
                         (x, y), (PASTURE_WIDTH + PANEL_WIDTH - 15, y))
        return y + 10

    def _text(self, font, txt, x, y, color=PANEL_TEXT):
        self.screen.blit(font.render(txt, True, color), (x, y))

    def _stat(self, label, value, x, y, vcol=None):
        self._text(self.f_sm, f"{label}:", x, y, (140, 140, 160))
        self._text(self.f_sm, value, x + 120, y, vcol or (200, 200, 200))

    # ==================================================================
    def draw_paused(self):
        ov = pygame.Surface((PASTURE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100))
        self.screen.blit(ov, (0, 0))
        txt = self.f_ttl.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=(PASTURE_WIDTH // 2, SCREEN_HEIGHT // 2)))
