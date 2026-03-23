"""Cow agents — three archetypes with rule-based autonomous movement.

Key behavioural changes vs. the first version:

* **Momentum** — VELOCITY_DAMPING raised to 0.985 so cows drift and arc
  instead of jittering.
* **Smooth wander** — angle drift capped at WANDER_DRIFT rad/tick (0.12)
  for natural meandering.
* **Social alarm** — when a neighbor has a fence warning, herd-follow cows
  copy its deflected velocity.  This is how one cow's turn cascades into a
  group redirection.
* **Normalised cohesion** — pull toward group centre is direction-only so
  it doesn't scale with distance (prevents runaway attraction).
* **Destination pull removed** — the fence_system now handles reward
  attraction via a continuous field, so cows no longer need a separate
  destination force.
"""

import math
import random
from config import (
    ARCHETYPE_LINEAR, ARCHETYPE_HERD, ARCHETYPE_ARISTOTLE,
    ARCHETYPE_DISTRIBUTION,
    COW_RADIUS, MAX_SPEED, VELOCITY_DAMPING,
    WANDER_STRENGTH, WANDER_DRIFT, FOOD_SEEK_STRENGTH,
    SEPARATION_STRENGTH, ALIGNMENT_STRENGTH, COHESION_STRENGTH,
    SOCIAL_ALARM_STRENGTH, SOCIAL_ALARM_DIST,
    BOUNDARY_STRENGTH,
    SEPARATION_DIST, ALIGNMENT_DIST, COHESION_DIST,
    HUNGER_INCREASE, HUNGER_DECREASE_FACTOR, MAX_HUNGER,
    GRASS_CONSUME_RATE, STRESS_DECAY, STRESS_FROM_HUNGER,
    MEMORY_CAPACITY, MEMORY_DECAY, MEMORY_AVOID_DIST, MEMORY_AVOID_STRENGTH,
    MAX_LEARNING, COW_TRAIL_LEN,
)


class Cow:
    def __init__(self, cow_id, pos, archetype):
        self.id = cow_id
        self.pos = list(pos)
        self.vel = [random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)]
        self.archetype = archetype

        self.hunger = random.uniform(0.10, 0.35)
        self.stress = 0.0
        self.learning = 0.0

        self.milk_bias = random.uniform(0.30, 0.70)
        self.meat_bias = 1.0 - self.milk_bias

        self.herd_follow = 0.5
        self.fence_sensitivity = 1.0
        self.max_speed = MAX_SPEED
        self.wander_angle = random.uniform(0, math.tau)

        self.beeps = 0
        self.vibrations = 0
        self.pulses = 0
        self.current_warning = 0
        self.boundary_violations = 0

        self.total_milk = 0.0
        self.total_meat = 0.0

        self.memory: list[tuple[float, float, float]] = []
        self.trail: list[tuple[float, float]] = []

        self.wander_mult = 1.0
        self.reward_mult = 1.0
        self.alignment_mult = 1.0
        self.alarm_mult = 1.0

        self.ticks_in_milk = 0
        self.ticks_in_meat = 0
        self.ticks_total = 0

        self._apply_archetype()

    # ------------------------------------------------------------------
    def _apply_archetype(self):
        if self.archetype == ARCHETYPE_LINEAR:
            self.herd_follow = random.uniform(0.10, 0.30)
            self.fence_sensitivity = random.uniform(0.60, 1.00)
            self.max_speed = MAX_SPEED * random.uniform(0.90, 1.10)
            self.wander_mult = 1.4
            self.reward_mult = 1.3
        elif self.archetype == ARCHETYPE_HERD:
            self.herd_follow = random.uniform(0.70, 1.00)
            self.fence_sensitivity = random.uniform(0.80, 1.20)
            self.max_speed = MAX_SPEED * random.uniform(0.85, 1.05)
            self.wander_mult = 0.5
            self.reward_mult = 0.7
            self.alignment_mult = 1.5
            self.alarm_mult = 1.5
        elif self.archetype == ARCHETYPE_ARISTOTLE:
            self.herd_follow = random.uniform(0.30, 0.60)
            self.fence_sensitivity = random.uniform(1.20, 1.80)
            self.max_speed = MAX_SPEED * random.uniform(0.80, 1.00)
            self.wander_mult = 0.7

    # ------------------------------------------------------------------
    def update(self, environment, all_cows, fence_force, dt=1.0):
        fx, fy = 0.0, 0.0

        wx, wy = self._wander()
        fx += wx; fy += wy

        gx, gy = self._food_seek(environment)
        fx += gx; fy += gy

        hx, hy = self._herd(all_cows)
        fx += hx; fy += hy

        fx += fence_force[0]
        fy += fence_force[1]

        if self.archetype == ARCHETYPE_ARISTOTLE and self.memory:
            mx, my = self._memory_avoid()
            fx += mx; fy += my

        bx, by = self._boundary(environment.pasture_bounds)
        fx += bx; fy += by

        self.vel[0] = (self.vel[0] + fx * dt) * VELOCITY_DAMPING
        self.vel[1] = (self.vel[1] + fy * dt) * VELOCITY_DAMPING
        speed = math.hypot(self.vel[0], self.vel[1])
        if speed > self.max_speed:
            self.vel[0] *= self.max_speed / speed
            self.vel[1] *= self.max_speed / speed

        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt

        bounds = environment.pasture_bounds
        self.pos[0] = max(bounds.left + COW_RADIUS, min(bounds.right - COW_RADIUS, self.pos[0]))
        self.pos[1] = max(bounds.top + COW_RADIUS, min(bounds.bottom - COW_RADIUS, self.pos[1]))

        self.trail.append((self.pos[0], self.pos[1]))
        if len(self.trail) > COW_TRAIL_LEN:
            self.trail.pop(0)

        self._metabolize(environment, dt)

        if self.archetype == ARCHETYPE_ARISTOTLE:
            self.memory = [(x, y, s * MEMORY_DECAY) for x, y, s in self.memory if s > 0.05]

    # ------------------------------------------------------------------
    def add_memory(self, pos):
        if self.archetype != ARCHETYPE_ARISTOTLE:
            return
        if len(self.memory) >= MEMORY_CAPACITY:
            self.memory.pop(0)
        self.memory.append((pos[0], pos[1], 1.0))

    # ------------------------------------------------------------------
    # Force components
    # ------------------------------------------------------------------
    def _wander(self):
        self.wander_angle += random.uniform(-WANDER_DRIFT, WANDER_DRIFT)
        s = WANDER_STRENGTH * self.wander_mult
        return (math.cos(self.wander_angle) * s,
                math.sin(self.wander_angle) * s)

    def _food_seek(self, env):
        if self.hunger < 0.20:
            return (0.0, 0.0)
        best_zone, best_score = None, -1.0
        for z in env.zones:
            if z.zone_type == "restricted":
                continue
            dx = z.center()[0] - self.pos[0]
            dy = z.center()[1] - self.pos[1]
            d = math.hypot(dx, dy)
            score = z.grass_value / (d + 60)
            if score > best_score:
                best_score = score
                best_zone = z
        if best_zone is None:
            return (0.0, 0.0)
        dx = best_zone.center()[0] - self.pos[0]
        dy = best_zone.center()[1] - self.pos[1]
        d = math.hypot(dx, dy)
        if d < 1:
            return (0.0, 0.0)
        s = FOOD_SEEK_STRENGTH * min(self.hunger, 1.0)
        return (dx / d * s, dy / d * s)

    def _herd(self, all_cows):
        if self.herd_follow < 0.05:
            return (0.0, 0.0)

        sx, sy, sc = 0.0, 0.0, 0
        ax, ay, ac = 0.0, 0.0, 0
        cx, cy, cc = 0.0, 0.0, 0
        al_vx, al_vy, al_c = 0.0, 0.0, 0      # social alarm accumulators

        for o in all_cows:
            if o.id == self.id:
                continue
            dx = o.pos[0] - self.pos[0]
            dy = o.pos[1] - self.pos[1]
            d = math.hypot(dx, dy)
            if d < 1:
                continue

            if d < SEPARATION_DIST:
                sx -= dx / d; sy -= dy / d; sc += 1
            if d < ALIGNMENT_DIST:
                ax += o.vel[0]; ay += o.vel[1]; ac += 1
            if d < COHESION_DIST:
                cx += o.pos[0]; cy += o.pos[1]; cc += 1

            if o.current_warning > 0 and d < SOCIAL_ALARM_DIST:
                w = 1.0 - d / SOCIAL_ALARM_DIST
                al_vx += o.vel[0] * w
                al_vy += o.vel[1] * w
                al_c += 1

        fx, fy = 0.0, 0.0

        if sc:
            fx += sx / sc * SEPARATION_STRENGTH
            fy += sy / sc * SEPARATION_STRENGTH

        if ac:
            fx += (ax / ac - self.vel[0]) * ALIGNMENT_STRENGTH * self.herd_follow * self.alignment_mult
            fy += (ay / ac - self.vel[1]) * ALIGNMENT_STRENGTH * self.herd_follow * self.alignment_mult

        if cc:
            cmx = cx / cc - self.pos[0]
            cmy = cy / cc - self.pos[1]
            cd = math.hypot(cmx, cmy)
            if cd > 1:
                fx += cmx / cd * COHESION_STRENGTH * self.herd_follow
                fy += cmy / cd * COHESION_STRENGTH * self.herd_follow

        if al_c and self.herd_follow > 0.1:
            al_vx /= al_c
            al_vy /= al_c
            fx += (al_vx - self.vel[0]) * SOCIAL_ALARM_STRENGTH * self.herd_follow * self.alarm_mult
            fy += (al_vy - self.vel[1]) * SOCIAL_ALARM_STRENGTH * self.herd_follow * self.alarm_mult

        return (fx, fy)

    def _memory_avoid(self):
        fx, fy = 0.0, 0.0
        for mx, my, strength in self.memory:
            dx = self.pos[0] - mx
            dy = self.pos[1] - my
            d = math.hypot(dx, dy)
            if 1 < d < MEMORY_AVOID_DIST:
                f = strength * MEMORY_AVOID_STRENGTH * (1.0 - d / MEMORY_AVOID_DIST)
                fx += dx / d * f
                fy += dy / d * f
        return (fx, fy)

    def _boundary(self, bounds):
        fx, fy = 0.0, 0.0
        margin = 30
        if self.pos[0] < bounds.left + margin:
            fx += BOUNDARY_STRENGTH * (1.0 - (self.pos[0] - bounds.left) / margin)
        if self.pos[0] > bounds.right - margin:
            fx -= BOUNDARY_STRENGTH * (1.0 - (bounds.right - self.pos[0]) / margin)
        if self.pos[1] < bounds.top + margin:
            fy += BOUNDARY_STRENGTH * (1.0 - (self.pos[1] - bounds.top) / margin)
        if self.pos[1] > bounds.bottom - margin:
            fy -= BOUNDARY_STRENGTH * (1.0 - (bounds.bottom - self.pos[1]) / margin)
        return (fx, fy)

    # ------------------------------------------------------------------
    def _metabolize(self, env, dt):
        zone = env.get_zone_at(self.pos)
        self.ticks_total += 1
        if zone:
            if zone.zone_type == "milk":
                self.ticks_in_milk += 1
            elif zone.zone_type == "meat":
                self.ticks_in_meat += 1
        if zone and zone.grass_value > 5:
            eaten = zone.consume(GRASS_CONSUME_RATE * dt)
            self.hunger = max(0.0, self.hunger - eaten * HUNGER_DECREASE_FACTOR)
        else:
            self.hunger = min(MAX_HUNGER, self.hunger + HUNGER_INCREASE * dt)

        if self.current_warning == 0:
            self.stress = max(0.0, self.stress - STRESS_DECAY * dt)
        if self.hunger > 0.7:
            self.stress = min(1.0, self.stress + STRESS_FROM_HUNGER * dt)


# ======================================================================
def create_herd(environment):
    """Spawn the initial herd — biased toward the neutral zone."""
    neutral = environment.get_zones_by_type("neutral")
    milk = environment.get_zones_by_type("milk")
    meat = environment.get_zones_by_type("meat")
    cows = []
    cid = 0
    for archetype, count in ARCHETYPE_DISTRIBUTION.items():
        for _ in range(count):
            r = random.random()
            pool = neutral if r < 0.60 else (milk if r < 0.80 else meat)
            z = random.choice(pool)
            x = random.uniform(z.rect.left + 15, z.rect.right - 15)
            y = random.uniform(z.rect.top + 15, z.rect.bottom - 15)
            cows.append(Cow(cid, (x, y), archetype))
            cid += 1
    return cows
