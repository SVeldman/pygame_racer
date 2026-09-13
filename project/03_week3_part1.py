"""Week 3, Part 1 - A whole pack of rivals, a starting grid, and a finish line.

WHAT'S NEW SINCE WEEK 2
-------------------------
Last week you met ONE rival, stored in a single dictionary. This week we
scale that up to `NUM_RIVALS` rivals, stored in a LIST of dictionaries - the
same idea, just more of them. Once we have several cars, a few more pieces
fall into place naturally:

  * a real STARTING GRID - every car (you included) lines up at distance 0,
    each in its own lane, instead of the rival just appearing somewhere
    ahead of you
  * a FINISH LINE at `FINISH_DISTANCE` - the race actually ends
  * PLACEMENT - since every car's distance is tracked independently, we can
    tell who crossed the finish line first, second, third...

Crashing still just ends the run for now ("CRASHED! Press SPACE to try
again") - turning that into something gentler is next week's lesson.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 05_week3_part1.py
"""

import random

# ---------------------------------------------------------------------------
# TUNING "KNOBS"
# ---------------------------------------------------------------------------
NUM_RIVALS = 3
LANE_COUNT = NUM_RIVALS + 1              # one lane per rival, plus one for you
LANE_WIDTH = 110
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
SHOULDER_WIDTH = 55
PLAYER_ROW = 480
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.12
BRAKE = 0.35
COAST = 0.04
ROUGH_BRAKE = 0.40

DASH_PERIOD = 60
DASH_LENGTH = 30

FINISH_DISTANCE = 3000
RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

# Because LANE_COUNT depends on NUM_RIVALS, and WIDTH depends on LANE_COUNT,
# turning this into a 6-rival race next semester is a one-line change - every
# other number in this file recalculates itself.
GRASS_MARGIN = 200
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
rivals = []                     # filled in by new_race(), below
game_state = "racing"           # "racing" | "crashed" | "won"
race_results = []               # rivals, in the order they crossed the line
player_place = None             # your finish position, once you cross


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
    """lane 0.0 = left edge of the road, 1.0 = right edge, at screen row y."""
    return road_left(y) + lane * ROAD_WIDTH


def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)


def row_at(dist):
    return PLAYER_ROW - (dist - distance_traveled)


def new_race():
    """Line every car up at the start (distance 0), each in its own lane."""
    global player_speed, distance_traveled, rivals, game_state
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    race_results = []
    player_place = None

    # ------------------------------------------------------------------
    # THE STARTING GRID
    # ------------------------------------------------------------------
    # We have exactly enough lanes for every car (LANE_COUNT = NUM_RIVALS +
    # 1). `grid` is just the list of lane numbers [0, 1, 2, ...LANE_COUNT-1];
    # shuffling it and handing out lanes in that shuffled order means every
    # car gets its OWN lane, nobody overlaps, and the starting order is
    # different every race.
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_lane, PLAYER_ROW), PLAYER_ROW)

    rivals = [
        {
            "actor": Actor(random.choice(RIVAL_COLORS)),
            "distance": 0,                         # everyone starts together
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
        }
        for lane_i in grid[1:]
    ]
    # Actors don't get positioned until update() runs the movement loop
    # below - but draw() might run BEFORE the first update(). Position them
    # here too, so the very first frame already shows everyone lined up
    # correctly instead of wherever Actor() happened to default to.
    for r in rivals:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)


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
        # One dashed line per lane BOUNDARY (there are LANE_COUNT - 1 of
        # them) - with 4 lanes that's 3 lines splitting the road into 4.
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)

    # The finish line only needs to be drawn once it's close enough to be
    # visible on screen - row_at() tells us exactly where that is.
    finish_y = row_at(FINISH_DISTANCE)
    if -20 < finish_y < HEIGHT:
        left = road_center_x(finish_y) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    for r in rivals:
        r["actor"].draw()
    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} / {FINISH_DISTANCE} m",
                     topleft=(10, 40), fontsize=30, color="white")

    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")


def _ordinal(n):
    """Turns 1 into '1ST', 2 into '2ND', 3 into '3RD', 4 into '4TH', and so
    on (11-20 are all 'TH', which is why they're special-cased first)."""
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"


def _banner(title, subtitle):
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=60, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=30, color="white")


def update():
    global player_speed, distance_traveled, game_state, player_place

    if game_state != "racing":
        if keyboard.space:
            new_race()
        return

    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
    player.x = max(20, min(WIDTH - 20, player.x))

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

    # Move every rival and note anyone who's just crossed the line. Because
    # this is a normal `for` loop over a LIST, adding a 4th, 5th, or 20th
    # rival to NUM_RIVALS needs no other changes anywhere in this function.
    for r in rivals:
        r["distance"] += r["base_speed"]
        y = row_at(r["distance"])
        r["actor"].pos = (lane_to_x(r["lane"], y), y)

        if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
            r["finished"] = True
            race_results.append(r)

    for r in rivals:
        if player.colliderect(r["actor"]):
            game_state = "crashed"

    # Your place is simply "how many rivals got there before you, plus one
    # for yourself" - race_results only contains rivals that finished
    # BEFORE this moment, because we check it before appending you to
    # anything.
    if distance_traveled >= FINISH_DISTANCE:
        player_place = len(race_results) + 1
        game_state = "won"
