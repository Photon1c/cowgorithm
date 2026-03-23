"""Environment — pasture zones, grass resources, and spatial queries."""

import pygame
from config import (
    ZONES, GRASS_MAX, GRASS_REGEN_RATE, GRASS_CONSUME_RATE,
    MILK_ZONE_CLR, MEAT_ZONE_CLR, NEUTRAL_ZONE_CLR, RESTRICTED_ZONE_CLR,
)


class Zone:
    def __init__(self, name, rect_tuple, zone_type, grass_quality, base_color):
        self.name = name
        self.rect = pygame.Rect(rect_tuple)
        self.zone_type = zone_type          # "milk" | "meat" | "neutral" | "restricted"
        self.grass_quality = grass_quality   # 0‒1 governs regen speed & ceiling
        self.grass_value = grass_quality * GRASS_MAX
        self.base_color = base_color
        self.is_destination = False

    def regenerate(self, dt=1.0):
        cap = self.grass_quality * GRASS_MAX
        self.grass_value = min(cap, self.grass_value + GRASS_REGEN_RATE * self.grass_quality * dt)

    def consume(self, amount):
        taken = min(self.grass_value, amount)
        self.grass_value -= taken
        return taken

    def contains(self, pos):
        return self.rect.collidepoint(int(pos[0]), int(pos[1]))

    def center(self):
        return (self.rect.centerx, self.rect.centery)

    def get_color(self):
        """Current color modulated by remaining grass."""
        f = self.grass_value / GRASS_MAX if GRASS_MAX else 0
        r = int(self.base_color[0] * (0.40 + 0.60 * f))
        g = int(self.base_color[1] * (0.45 + 0.55 * f))
        b = int(self.base_color[2] * (0.40 + 0.60 * f))
        return (min(255, r), min(255, g), min(255, b))


class Environment:
    def __init__(self):
        self.zones: list[Zone] = []
        self.pasture_bounds = pygame.Rect(10, 10, 830, 730)
        self._build_zones()

    def _build_zones(self):
        self.zones.append(Zone("Milk Pasture",  ZONES["milk"],             "milk",       0.90, MILK_ZONE_CLR))
        self.zones.append(Zone("Meat Pasture",  ZONES["meat"],             "meat",       0.70, MEAT_ZONE_CLR))
        self.zones.append(Zone("Neutral Area",  ZONES["neutral"],          "neutral",    0.50, NEUTRAL_ZONE_CLR))
        self.zones.append(Zone("Restricted L",  ZONES["restricted_left"],  "restricted", 0.15, RESTRICTED_ZONE_CLR))
        self.zones.append(Zone("Restricted R",  ZONES["restricted_right"], "restricted", 0.15, RESTRICTED_ZONE_CLR))

    def get_zone_at(self, pos):
        for z in self.zones:
            if z.contains(pos):
                return z
        return None

    def get_zones_by_type(self, zone_type):
        return [z for z in self.zones if z.zone_type == zone_type]

    def update(self, dt=1.0):
        for z in self.zones:
            z.regenerate(dt)
