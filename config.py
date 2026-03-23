"""Configuration constants for Cow Airlines Simulation."""

# --- Display ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 750
PASTURE_WIDTH = 850
PANEL_WIDTH = SCREEN_WIDTH - PASTURE_WIDTH
FPS = 60

# --- Colors ---
BG_COLOR = (25, 35, 20)
PANEL_BG = (28, 28, 38)
PANEL_TEXT = (220, 220, 220)
PANEL_ACCENT = (100, 170, 230)
FENCE_ACTIVE_COLOR = (255, 70, 70)
BEEP_CLR = (255, 255, 100)
VIBRATE_CLR = (255, 180, 50)
PULSE_CLR = (255, 50, 50)
ZONE_BORDER_CLR = (130, 130, 130)

# Zone base colors (modulated by grass level at runtime)
MILK_ZONE_CLR = (40, 135, 40)
MEAT_ZONE_CLR = (145, 125, 42)
NEUTRAL_ZONE_CLR = (70, 120, 55)
RESTRICTED_ZONE_CLR = (90, 50, 50)

# --- Cow archetypes ---
ARCHETYPE_LINEAR = "linear"
ARCHETYPE_HERD = "herd"
ARCHETYPE_ARISTOTLE = "aristotle"

ARCHETYPE_COLORS = {
    ARCHETYPE_LINEAR: (215, 215, 215),
    ARCHETYPE_HERD: (195, 145, 80),
    ARCHETYPE_ARISTOTLE: (105, 115, 225),
}
ARCHETYPE_NAMES = {
    ARCHETYPE_LINEAR: "Linear",
    ARCHETYPE_HERD: "Herd",
    ARCHETYPE_ARISTOTLE: "Aristotle",
}

# --- Herd composition ---
NUM_COWS = 30
ARCHETYPE_DISTRIBUTION = {
    ARCHETYPE_LINEAR: 10,
    ARCHETYPE_HERD: 12,
    ARCHETYPE_ARISTOTLE: 8,
}

# =====================================================================
# MOVEMENT / PHYSICS  (tune these to change how cows feel)
# =====================================================================
COW_RADIUS = 7
MAX_SPEED = 1.8
VELOCITY_DAMPING = 0.988           # higher → more momentum / inertia
WANDER_STRENGTH = 0.10             # magnitude of random wander force
WANDER_DRIFT = 0.09                # max wander-angle change per tick (rad)
FOOD_SEEK_STRENGTH = 0.25
BOUNDARY_STRENGTH = 2.0

# =====================================================================
# HERD BEHAVIOR  (tune for flocking tightness and social copying)
# =====================================================================
SEPARATION_STRENGTH = 0.40
ALIGNMENT_STRENGTH = 0.25          # how strongly cows match neighbor velocity
COHESION_STRENGTH = 0.15           # pull toward herd centre (direction-normalised)
SOCIAL_ALARM_STRENGTH = 0.30       # copy velocity of warned neighbours
SOCIAL_ALARM_DIST = 90             # radius for alarm propagation

# Neighbor perception radii
SEPARATION_DIST = 25
ALIGNMENT_DIST = 70
COHESION_DIST = 100

# =====================================================================
# CONTINUOUS FENCE AVERSION FIELD
# =====================================================================
FENCE_FIELD_RADIUS = 150           # soft aversion starts this far from boundary
FENCE_FIELD_STRENGTH = 0.28        # base magnitude (t^1.5 falloff, wider+gentler)
FENCE_TANGENT_FACTOR = 0.40        # fraction redirected along boundary → corridor sliding

# Discrete escalation thresholds (beep / vibration / pulse)
FENCE_BEEP_DIST = 55
FENCE_VIBRATE_DIST = 35
FENCE_PULSE_DIST = 18
FENCE_AVOID_STRENGTH = 0.80        # event-burst force magnitude

DEFAULT_STRICTNESS = 1.0
STRICTNESS_STEP = 0.1
MIN_STRICTNESS = 0.2
MAX_STRICTNESS = 3.0

# =====================================================================
# REWARD ATTRACTION FIELD  (destination zones)
# =====================================================================
REWARD_FIELD_RADIUS = 350           # pull range from destination zone edge
REWARD_FIELD_STRENGTH = 0.15        # visible drift bias (still emergent, not a shove)
REWARD_INTERIOR_STRENGTH = 0.04     # keep cows settled once inside destination

# =====================================================================
# LEARNING
# =====================================================================
LEARNING_RATE_BEEP = 0.001
LEARNING_RATE_VIBRATE = 0.003
LEARNING_RATE_PULSE = 0.010
MAX_LEARNING = 1.0

# =====================================================================
# STRESS
# =====================================================================
STRESS_FROM_VIBRATE = 0.008
STRESS_FROM_PULSE = 0.040
STRESS_DECAY = 0.0008
STRESS_FROM_HUNGER = 0.0003

# --- Hunger / grass ---
HUNGER_INCREASE = 0.0015
HUNGER_DECREASE_FACTOR = 0.01
MAX_HUNGER = 1.0
GRASS_MAX = 100.0
GRASS_REGEN_RATE = 0.03
GRASS_CONSUME_RATE = 0.15

# --- Economics ---
MILK_BASE_RATE = 0.012
MEAT_BASE_RATE = 0.008
MILK_STRESS_PENALTY = 0.6
MEAT_STRESS_PENALTY = 0.35

# --- Simulation timing ---
DAY_TICKS = 3600  # at 60 FPS → 1 sim-day = 60 real seconds

# --- Aristotle memory ---
MEMORY_CAPACITY = 15
MEMORY_DECAY = 0.995
MEMORY_AVOID_DIST = 100
MEMORY_AVOID_STRENGTH = 0.55

# --- Cow trail (visual only) ---
COW_TRAIL_LEN = 60

# --- Zone rectangles (x, y, w, h) ---
ZONES = {
    "milk":             (20,  20,  385, 320),
    "meat":             (435, 20,  395, 320),
    "neutral":          (120, 390, 600, 330),
    "restricted_left":  (20,  390,  80, 330),
    "restricted_right": (740, 390,  80, 330),
}
