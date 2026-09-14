"""Week 2, Part 2 - You meet your first rival.

WHAT'S NEW SINCE PART 1
-------------------------
Part 1 already has the road scrolling, throttle/brake, and
`distance_traveled`. Now that WE have a distance for ourselves, we can give
another car its OWN distance and use the GAP between the two distances to
decide where to draw it on screen. This is the single most important trick
in the whole game, so read the comment above `row_at()` carefully.

Along the way, a couple of smaller things change too:
  * `WIDTH` is now CALCULATED from how many rivals there are, instead of a
    fixed number - see the comment above it.
  * `LANE_COUNT` shows up for the first time, giving the rival its own lane
    to drive in, separate from yours.
  * running into the rival now actually does something - it ends your run,
    with SPACE to try again.

There's no finish line yet, and no "winning" - that arrives next week, once
we also have more than one rival. For now the goal is simpler: drive around
without hitting the other car.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 02_week2_part2.py
"""

import random

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
NUM_RIVALS = 1                           # just one other car this week
LANE_COUNT = NUM_RIVALS + 1              # one lane for the rival, one for you
LANE_WIDTH = 110                         # width of a single lane
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT     # total width of the tarmac
SHOULDER_WIDTH = 55
PLAYER_ROW = 480
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.12              # UP key
BRAKE = 0.35              # DOWN key
COAST = 0.04              # slow-down when no key is held
ROUGH_BRAKE = 0.40        # extra slow-down off the tarmac (shoulder or rough)

DASH_PERIOD = 60          # distance from the start of one dash to the next
DASH_LENGTH = 30          # how long each dash is

RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

# ---------------------------------------------------------------------------
# WINDOW SIZE - NOW COMPUTED, NOT HARD-CODED
# ---------------------------------------------------------------------------
# Instead of picking a WIDTH by hand, we calculate one that's just wide
# enough for the road plus a little grass on each side. This matters a lot
# starting next week, when NUM_RIVALS grows and the road needs more lanes -
# changing ONE number (NUM_RIVALS) will automatically resize the window to
# fit, instead of us having to guess a new WIDTH by hand every time.
GRASS_MARGIN = 200        # how much grass to leave visible on each side
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600

# --- Colours -----------------------------------------------------------------
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

# ---------------------------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------------------------
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
game_state = "racing"          # "racing" | "crashed"


def road_center_x(y):
    return WIDTH // 2


def road_left(y):
    return road_center_x(y) - ROAD_WIDTH // 2


def road_right(y):
    return road_center_x(y) + ROAD_WIDTH // 2


def on_road(x, y):
    return road_left(y) <= x <= road_right(y)


def on_shoulder(x, y):
    if on_road(x, y):
        return False
    return road_left(y) - SHOULDER_WIDTH <= x <= road_right(y) + SHOULDER_WIDTH


def lane_to_x(lane, y):
    """Turn a lane FRACTION (0.0 = left edge of road, 1.0 = right edge) into
    an actual X pixel position, at screen row y."""
    return road_left(y) + lane * ROAD_WIDTH


# ---------------------------------------------------------------------------
# THE SCROLLING TRICK
# ---------------------------------------------------------------------------
# `distance_traveled` is how far along the course you've driven so far. It
# only ever goes up (by `player_speed` every frame). We never move the
# ROAD - we only ever move the NUMBER - and then use these two functions
# to translate between "a distance along the course" and "a row on screen":
def dist_at(y):
    """What track distance is being drawn at screen row y, right now?"""
    return distance_traveled + (PLAYER_ROW - y)


def row_at(dist):
    """The exact opposite question: which screen row is track distance
    `dist` drawn at, right now? This is `dist_at` solved backwards, and
    it's exactly what we need to answer "where on screen is the rival?" -
    the rival doesn't have a row, it has a DISTANCE, and row_at converts
    that into a row for us every frame.
    """
    return PLAYER_ROW - (dist - distance_traveled)


def new_race():
    """Reset everything back to the start."""
    global player_speed, distance_traveled, rival, game_state
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    player.pos = (lane_to_x(0.75, PLAYER_ROW), PLAYER_ROW)
    rival = {
        "actor": Actor(random.choice(RIVAL_COLORS)),
        "distance": 0,           # the rival starts even with you, not ahead
        "lane": 0.25,               # pick a lane that isn't where you start
        "base_speed": 6.5,          # the rival's own, constant, forward speed
    }


new_race()


def draw():
    screen.fill(GRASS)

    strip_height = 10
    for top in range(0, HEIGHT, strip_height):
        y = top + strip_height // 2
        center_x = road_center_x(y)
        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2 - SHOULDER_WIDTH, top,
                 SHOULDER_WIDTH, strip_height),
            GRAVEL,
        )
        screen.draw.filled_rect(
            Rect(center_x + ROAD_WIDTH // 2, top, SHOULDER_WIDTH, strip_height),
            GRAVEL,
        )
        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2, top, ROAD_WIDTH, strip_height),
            TARMAC,
        )
        # The centre line is drawn wherever the current track DISTANCE lands
        # inside a "dash" - as distance_traveled grows, every dash appears to
        # slide down the screen, which is the whole scrolling illusion.
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    rival["actor"].draw()
    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
                     fontsize=30, color="white")

    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")


def _banner(title, subtitle):
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=60, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=30, color="white")


def update():
    global player_speed, distance_traveled, game_state

    if game_state != "racing":
        if keyboard.space:
            new_race()
        return

    # steering
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
    player.x = max(20, min(WIDTH - 20, player.x))

    # throttle / brake / coast - this replaces last week's auto-accelerate
    if keyboard.up:
        player_speed += ACCEL
    elif keyboard.down:
        player_speed -= BRAKE
    else:
        player_speed -= COAST

    if on_shoulder(player.x, PLAYER_ROW):
        if player_speed > SHOULDER_MAX_SPEED:
            player_speed -= ROUGH_BRAKE
    elif not on_road(player.x, PLAYER_ROW):
        if player_speed > ROUGH_MAX_SPEED:
            player_speed -= ROUGH_BRAKE
    player_speed = max(0.0, min(MAX_SPEED, player_speed))

    distance_traveled += player_speed

    # ---------------------------------------------------------------------
    # RELATIVE SPEED - THE CORE TRICK
    # ---------------------------------------------------------------------
    # The rival has its OWN distance, which grows by its OWN base_speed -
    # completely independently of yours. Every frame we work out where that
    # puts it on screen right now with row_at(), and place its Actor there.
    #
    #   * If you're driving FASTER than the rival's base_speed, the GAP
    #     between your distance and its distance shrinks every frame, which
    #     means row_at() returns a bigger row number (further down the
    #     screen) - the rival appears to drift toward you and then past you.
    #   * If you're SLOWER, the gap grows, row_at() returns a smaller row
    #     number, and the rival pulls away up the screen.
    #
    # This is the whole trick behind every car in this game "racing" you -
    # nothing is being steered by an AI, it's just two independent numbers
    # (your distance and the rival's) being compared every frame.
    rival["distance"] += rival["base_speed"]
    rival_y = row_at(rival["distance"])
    rival["actor"].pos = (lane_to_x(rival["lane"], rival_y), rival_y)

    if player.colliderect(rival["actor"]):
        game_state = "crashed"
