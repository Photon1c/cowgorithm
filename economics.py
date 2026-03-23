"""Economics module — simplified milk / meat production tracking."""

from config import (
    MILK_BASE_RATE, MEAT_BASE_RATE,
    MILK_STRESS_PENALTY, MEAT_STRESS_PENALTY,
    DAY_TICKS,
)


class Economics:
    def __init__(self):
        self.total_milk = 0.0
        self.total_meat = 0.0
        self.day = 0
        self.tick_in_day = 0

    def update(self, cows, environment, dt=1.0):
        self.tick_in_day += 1
        if self.tick_in_day >= DAY_TICKS:
            self.tick_in_day = 0
            self.day += 1

        for cow in cows:
            zone = environment.get_zone_at(cow.pos)
            if zone is None:
                continue

            stress_milk = max(0.0, 1.0 - cow.stress * MILK_STRESS_PENALTY)
            stress_meat = max(0.0, 1.0 - cow.stress * MEAT_STRESS_PENALTY)
            hunger_f = max(0.15, 1.0 - cow.hunger * 0.5)

            zone_milk_q = {"milk": 1.0, "meat": 0.30, "neutral": 0.40, "restricted": 0.10}.get(zone.zone_type, 0.2)
            zone_meat_q = {"meat": 1.0, "milk": 0.25, "neutral": 0.35, "restricted": 0.10}.get(zone.zone_type, 0.2)

            milk = MILK_BASE_RATE * cow.milk_bias * zone_milk_q * stress_milk * hunger_f * dt
            meat = MEAT_BASE_RATE * cow.meat_bias * zone_meat_q * stress_meat * hunger_f * dt

            cow.total_milk += milk
            cow.total_meat += meat
            self.total_milk += milk
            self.total_meat += meat

    def get_stats(self, cows):
        n = max(1, len(cows))
        total_t = sum(c.ticks_total for c in cows)
        if total_t > 0:
            pct_milk = sum(c.ticks_in_milk for c in cows) / total_t * 100
            pct_meat = sum(c.ticks_in_meat for c in cows) / total_t * 100
        else:
            pct_milk = 0.0
            pct_meat = 0.0
        return {
            "day":              self.day,
            "total_milk":       self.total_milk,
            "total_meat":       self.total_meat,
            "pct_time_milk":    pct_milk,
            "pct_time_meat":    pct_meat,
            "avg_stress":       sum(c.stress for c in cows) / n,
            "avg_learning":     sum(c.learning for c in cows) / n,
            "avg_hunger":       sum(c.hunger for c in cows) / n,
            "total_beeps":      sum(c.beeps for c in cows),
            "total_vibrations": sum(c.vibrations for c in cows),
            "total_pulses":     sum(c.pulses for c in cows),
            "pulses_per_cow":   sum(c.pulses for c in cows) / n,
        }
