"""Halter-style virtual fence — continuous influence field + escalating events.

The fence system produces TWO layers of force:

1. **Continuous aversion field** — a smooth, long-range repulsion that begins
   at FENCE_FIELD_RADIUS and grows quadratically toward the forbidden zone
   boundary.  A tangential component deflects cows *along* the boundary
   instead of straight back, which is what creates corridor-following.

2. **Discrete event escalation** — beep / vibration / pulse overlaid at
   shorter thresholds.  These add burst force, stress, and learning but are
   NOT the primary steering mechanism.

A **reward attraction field** pulls cows toward destination zones with a
linear falloff, independent of fence strictness so the two forces can be
tuned separately.
"""

import math
from config import (
    FENCE_FIELD_RADIUS, FENCE_FIELD_STRENGTH, FENCE_TANGENT_FACTOR,
    FENCE_BEEP_DIST, FENCE_VIBRATE_DIST, FENCE_PULSE_DIST,
    FENCE_AVOID_STRENGTH,
    REWARD_FIELD_RADIUS, REWARD_FIELD_STRENGTH, REWARD_INTERIOR_STRENGTH,
    DEFAULT_STRICTNESS, MIN_STRICTNESS, MAX_STRICTNESS,
    LEARNING_RATE_BEEP, LEARNING_RATE_VIBRATE, LEARNING_RATE_PULSE,
    MAX_LEARNING,
    STRESS_FROM_VIBRATE, STRESS_FROM_PULSE,
)


class FenceSystem:
    def __init__(self, environment):
        self.env = environment
        self.routing_mode = "neutral"
        self.strictness = DEFAULT_STRICTNESS
        self.show_fences = True
        self.show_destinations = True
        self.show_fields = False

        self.total_beeps = 0
        self.total_vibrations = 0
        self.total_pulses = 0

    # ------------------------------------------------------------------
    def set_routing(self, mode):
        self.routing_mode = mode
        for z in self.env.zones:
            z.is_destination = False
        target = {"milk": "milk", "meat": "meat"}.get(mode)
        if target:
            for z in self.env.get_zones_by_type(target):
                z.is_destination = True

    def get_forbidden_zones(self):
        if self.routing_mode == "milk":
            return [z for z in self.env.zones if z.zone_type in ("meat", "restricted")]
        if self.routing_mode == "meat":
            return [z for z in self.env.zones if z.zone_type in ("milk", "restricted")]
        return [z for z in self.env.zones if z.zone_type == "restricted"]

    def get_destination_zones(self):
        return [z for z in self.env.zones if z.is_destination]

    # ------------------------------------------------------------------
    def process_cow(self, cow):
        """Return combined routing force [fx, fy] for *cow*.

        Combines continuous aversion field, tangential sliding, discrete
        event escalation, and reward attraction.
        """
        force = [0.0, 0.0]
        max_warn = 0

        dest_zones = self.get_destination_zones()
        tang_bias = [0.0, 0.0]
        if dest_zones:
            dz = dest_zones[0]
            dx = dz.center()[0] - cow.pos[0]
            dy = dz.center()[1] - cow.pos[1]
            d = math.hypot(dx, dy)
            if d > 1:
                tang_bias = [dx / d, dy / d]

        # --- aversion: continuous field + discrete events ---------------
        for zone in self.get_forbidden_zones():
            dist, nx, ny = self._dist_and_normal(cow.pos, zone.rect)
            w = self._aversion(cow, dist, nx, ny, force, tang_bias)
            max_warn = max(max_warn, w)

        # --- reward attraction ------------------------------------------
        for zone in dest_zones:
            self._reward(cow, zone, force)

        self._apply_stats(cow, max_warn)
        return force

    # ------------------------------------------------------------------
    # Aversion: field + tangent + events
    # ------------------------------------------------------------------
    def _aversion(self, cow, dist, nx, ny, force, tang_bias):
        """Append aversion forces to *force* in-place; return warning level."""
        field_radius = FENCE_FIELD_RADIUS * self.strictness
        warn = 0

        # -- continuous influence field (t^1.5 falloff) --
        if dist < field_radius:
            t = max(0.0, 1.0 - dist / field_radius) if dist > 0 else 1.0
            eff = cow.fence_sensitivity * self.strictness * (1.0 + cow.learning * 0.8)
            mag = FENCE_FIELD_STRENGTH * t ** 1.5 * eff

            # normal push (away from zone)
            force[0] += nx * mag
            force[1] += ny * mag

            # tangential sliding (along boundary, in the direction of travel)
            ts = mag * FENCE_TANGENT_FACTOR
            vn = cow.vel[0] * nx + cow.vel[1] * ny
            tvx = cow.vel[0] - vn * nx
            tvy = cow.vel[1] - vn * ny
            tm = math.hypot(tvx, tvy)
            if tm > 0.01:
                force[0] += tvx / tm * ts
                force[1] += tvy / tm * ts
            elif tang_bias[0] != 0.0 or tang_bias[1] != 0.0:
                bp = tang_bias[0] * (-ny) + tang_bias[1] * nx
                if abs(bp) > 0.01:
                    sign = 1.0 if bp > 0 else -1.0
                    force[0] += (-ny) * sign * ts * 0.5
                    force[1] += nx * sign * ts * 0.5

        # -- discrete event escalation --
        eff_ev = cow.fence_sensitivity * self.strictness * (1.0 + cow.learning * 1.5)
        sb = FENCE_BEEP_DIST * self.strictness
        sv = FENCE_VIBRATE_DIST * self.strictness
        sp = FENCE_PULSE_DIST * self.strictness

        if dist <= 0:
            warn = 3
            s = FENCE_AVOID_STRENGTH * 1.6 * eff_ev
            force[0] += nx * s
            force[1] += ny * s
            cow.boundary_violations += 1
            cow.add_memory(cow.pos)
        elif dist < sp:
            warn = 3
            t = 1.0 - dist / sp
            s = FENCE_AVOID_STRENGTH * (1.0 + 0.5 * t) * eff_ev
            force[0] += nx * s
            force[1] += ny * s
            cow.add_memory(cow.pos)
        elif dist < sv:
            warn = 2
            t = 1.0 - (dist - sp) / (sv - sp)
            s = FENCE_AVOID_STRENGTH * (0.4 + 0.4 * t) * eff_ev
            force[0] += nx * s
            force[1] += ny * s
        elif dist < sb:
            warn = 1
            t = 1.0 - (dist - sv) / (sb - sv)
            s = FENCE_AVOID_STRENGTH * 0.2 * t * eff_ev
            force[0] += nx * s
            force[1] += ny * s

        return warn

    # ------------------------------------------------------------------
    # Reward attraction
    # ------------------------------------------------------------------
    def _reward(self, cow, zone, force):
        rm = cow.reward_mult
        dist, nx, ny = self._dist_and_normal(cow.pos, zone.rect)
        if dist <= 0:
            cx, cy = zone.center()
            dx = cx - cow.pos[0]
            dy = cy - cow.pos[1]
            d = math.hypot(dx, dy)
            if d > 1:
                force[0] += dx / d * REWARD_INTERIOR_STRENGTH * rm
                force[1] += dy / d * REWARD_INTERIOR_STRENGTH * rm
        elif dist < REWARD_FIELD_RADIUS:
            t = 1.0 - dist / REWARD_FIELD_RADIUS
            s = REWARD_FIELD_STRENGTH * t * (1.0 + cow.learning * 0.5) * rm
            force[0] -= nx * s
            force[1] -= ny * s

    # ------------------------------------------------------------------
    # Stats / learning
    # ------------------------------------------------------------------
    def _apply_stats(self, cow, level):
        if level >= 1:
            cow.beeps += 1
            self.total_beeps += 1
            cow.learning = min(MAX_LEARNING, cow.learning + LEARNING_RATE_BEEP)
        if level >= 2:
            cow.vibrations += 1
            self.total_vibrations += 1
            cow.stress = min(1.0, cow.stress + STRESS_FROM_VIBRATE)
            cow.learning = min(MAX_LEARNING, cow.learning + LEARNING_RATE_VIBRATE)
        if level >= 3:
            cow.pulses += 1
            self.total_pulses += 1
            cow.stress = min(1.0, cow.stress + STRESS_FROM_PULSE)
            cow.learning = min(MAX_LEARNING, cow.learning + LEARNING_RATE_PULSE)
        cow.current_warning = level

    # ------------------------------------------------------------------
    @staticmethod
    def _dist_and_normal(pos, rect):
        """Signed distance from *pos* to nearest edge of *rect*.

        Returns ``(dist, nx, ny)`` where the normal points *away* from the
        rect.  Negative *dist* means the point is inside.
        """
        cx, cy = pos
        if rect.collidepoint(int(cx), int(cy)):
            dl = cx - rect.left
            dr = rect.right - cx
            dt_ = cy - rect.top
            db = rect.bottom - cy
            m = min(dl, dr, dt_, db)
            if m == dl:
                return -m, -1.0, 0.0
            if m == dr:
                return -m, 1.0, 0.0
            if m == dt_:
                return -m, 0.0, -1.0
            return -m, 0.0, 1.0

        nearest_x = max(rect.left, min(cx, rect.right))
        nearest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - nearest_x
        dy = cy - nearest_y
        d = math.hypot(dx, dy)
        if d < 0.001:
            return 0.0, 1.0, 0.0
        return d, dx / d, dy / d

    # ------------------------------------------------------------------
    def adjust_strictness(self, delta):
        self.strictness = max(MIN_STRICTNESS, min(MAX_STRICTNESS, self.strictness + delta))

    def get_containment(self, cows):
        """% of cows NOT in any forbidden zone."""
        forbidden = self.get_forbidden_zones()
        bad = sum(1 for c in cows if any(z.contains(c.pos) for z in forbidden))
        return (1.0 - bad / max(1, len(cows))) * 100

    def get_in_target(self, cows):
        """% of cows currently inside a destination zone."""
        dests = self.get_destination_zones()
        if not dests:
            return 0.0
        good = sum(1 for c in cows if any(z.contains(c.pos) for z in dests))
        return good / max(1, len(cows)) * 100
