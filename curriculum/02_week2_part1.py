"""Week 2, Part 1 - The road scrolls.

WHAT'S NEW SINCE WEEK 1
-------------------------
Up to now the car has been able to move left and right, but never
"forward" - Week 1 had no sense of how far you'd travelled. Now we track
`distance_traveled`, and use it to make the dashed centre line stream down
the screen, creating the illusion that you're driving forward even though
the car itself stays put on PLAYER_ROW. UP and DOWN now control the throttle
and brake directly, instead of speed building up automatically the way it
did last week.

There's no rival yet, and nothing to crash into - that's next lesson, once
we have a `distance_traveled` for ourselves to compare someone else's
against.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 02_week2_part1.py
"""

WIDTH = 800
HEIGHT = 600

# --- Tuning "knobs" -------------------------------------------------------
ROAD_WIDTH = 220
SHOULDER_WIDTH = 55
PLAYER_ROW = 480
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7    # speed the shoulder drags you down to
ROUGH_MAX_SPEED = MAX_SPEED * 0.4       # speed the rough drags you down to
ACCEL = 0.12              # UP key
BRAKE = 0.35              # DOWN key
COAST = 0.04              # slow-down when no key is held
ROUGH_BRAKE = 0.40        # extra slow-down off the tarmac (shoulder or rough)

DASH_PERIOD = 60          # distance from the start of one dash to the next
DASH_LENGTH = 30          # how long each dash is

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


# ---------------------------------------------------------------------------
# THE SCROLLING TRICK
# ---------------------------------------------------------------------------
# `distance_traveled` is how far along the course you've driven so far. It
# only ever goes up (by `player_speed` every frame). We never move the
# ROAD - we only ever move the NUMBER - and then use dist_at() to translate
# "a distance along the course" into "a row on screen" wherever we need to
# draw something at that distance.
def dist_at(y):
    """What track distance is being drawn at screen row y, right now?"""
    return distance_traveled + (PLAYER_ROW - y)


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
        # Nothing here actually moves; we just re-decide where to paint each
        # dash, every single frame.
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
                     fontsize=30, color="white")
    if on_shoulder(player.x, PLAYER_ROW):
        screen.draw.text("ON THE SHOULDER", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 220, 120))
    elif not on_road(player.x, PLAYER_ROW):
        screen.draw.text("ON THE ROUGH!", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 90, 60))


def update():
    global player_speed, distance_traveled

    # steering
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
    player.x = max(20, min(WIDTH - 20, player.x))

    # throttle / brake / coast - this replaces last week's auto-accelerate.
    # Holding UP builds speed, DOWN sheds it fast, and letting go bleeds it
    # off slowly (COAST) instead of holding steady - a real car doesn't
    # coast at a constant speed forever either.
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

    # This is the only place distance_traveled changes - it only ever grows,
    # by however fast you're currently going. Everything scrolling on
    # screen is downstream of this one line.
    distance_traveled += player_speed
