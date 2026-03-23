"""
Cow Airlines Simulation — cow_airlines_sim.py
==============================================
A top-down 2D herd simulation demonstrating Halter-style virtual fencing.
Weak local nudges (beep → vibration → pulse) produce emergent global herd
structure over time.  Three cow archetypes respond differently to fence
signals and social cues.  An economics layer tracks how routing and stress
affect milk vs. meat production.

Architecture
------------
  config.py        – constants and tuning knobs
  environment.py   – pasture zones, grass resources
  cow.py           – cow agents, archetypes, flocking
  fence_system.py  – virtual fencing with escalation + learning
  economics.py     – milk / meat index tracking
  ui.py            – Pygame rendering (pasture + side panel)
  cow_airlines_sim.py  – this file; main loop

Controls
--------
  SPACE   pause / resume
  R       reset simulation
  F       toggle fence overlays
  V       toggle influence-field gradient
  G       toggle destination zone markers
  T       toggle cow trails
  +/-     raise / lower fence strictness
  1       switch to milk-optimised routing
  2       switch to meat-optimised routing
  3       neutral routing (restricted zones only)
"""

import sys
import pygame
from config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT, STRICTNESS_STEP
from environment import Environment
from cow import create_herd
from fence_system import FenceSystem
from economics import Economics
from ui import Renderer


class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cow Airlines — Virtual Fence Herd Simulation")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.paused = False
        self.running = True
        self.show_trails = True
        self._reset()

    def _reset(self):
        self.environment = Environment()
        self.cows = create_herd(self.environment)
        self.fence_system = FenceSystem(self.environment)
        self.economics = Economics()

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            self._handle_events()
            if not self.paused:
                self._tick()
            self._render()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------
    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                self._on_key(ev.key)

    def _on_key(self, key):
        if key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self._reset()
        elif key == pygame.K_f:
            self.fence_system.show_fences = not self.fence_system.show_fences
        elif key == pygame.K_g:
            self.fence_system.show_destinations = not self.fence_system.show_destinations
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.fence_system.adjust_strictness(STRICTNESS_STEP)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.fence_system.adjust_strictness(-STRICTNESS_STEP)
        elif key == pygame.K_v:
            self.fence_system.show_fields = not self.fence_system.show_fields
        elif key == pygame.K_t:
            self.show_trails = not self.show_trails
        elif key == pygame.K_1:
            self.fence_system.set_routing("milk")
        elif key == pygame.K_2:
            self.fence_system.set_routing("meat")
        elif key == pygame.K_3:
            self.fence_system.set_routing("neutral")

    # ------------------------------------------------------------------
    def _tick(self):
        self.environment.update()
        for cow in self.cows:
            fence_f = self.fence_system.process_cow(cow)
            cow.update(self.environment, self.cows, fence_f)
        self.economics.update(self.cows, self.environment)

    def _render(self):
        self.renderer.draw(self.environment, self.cows, self.fence_system,
                           self.economics, self.show_trails)
        if self.paused:
            self.renderer.draw_paused()
        pygame.display.flip()


# ======================================================================
if __name__ == "__main__":
    Simulation().run()
