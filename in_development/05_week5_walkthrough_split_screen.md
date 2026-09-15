# Week 5, Optional Extra Walkthrough — Split-Screen, No Menu, No AI

**Not part of the required path.** This is a smaller, standalone stepping
stone into split-screen: two human players race each other head-to-head on
the same course, with no menu and no AI racers at all. It's a gentler first
step into split-screen than Part 2's full menu-plus-multiplayer version, or
a quick aside for a fast finisher. Build it directly from Week 4's finished
game — it does not need Week 5 Parts 1-3 at all.

## Starting Code for the Optional Extra

Start from the Week 4, Part 2 checkpoint (`04_week4_part2.py`).
```python
import random

### CONSTANTS
NUM_RIVALS = 4
LANE_COUNT = NUM_RIVALS + 1
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

RIVAL_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange"]

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3
FREEZE_FRAMES = 2 * FPS

### TRACK
CENTER = WIDTH // 2
TRACK = [
    (300, CENTER),
    (300, CENTER - 150),
    (250, CENTER - 150),
    (350, CENTER + 160),
    (250, CENTER + 160),
    (300, CENTER),
    (250, CENTER - 120),
    (350, CENTER + 120),
    (300, CENTER),
    (300, CENTER - 140),
    (250, CENTER - 140),
    (350, CENTER + 150),
    (350, CENTER),
]
FINISH_DISTANCE = sum(length for length, _ in TRACK)

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### GAME STATE
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
rivals = []
game_state = "waiting"
race_results = []
player_place = None
countdown_timer = 0
freeze_timer = 0
player_start_lane = 0.0


### TRACK MATH
def _segment_at(dist):
    start_center = CENTER
    covered = 0
    for length, end_center in TRACK:
        if dist < covered + length:
            fraction = (dist - covered) / length
            return start_center, end_center, fraction
        covered += length
        start_center = end_center
    return start_center, start_center, 1.0


def center_x_at_distance(dist):
    start_center, end_center, fraction = _segment_at(dist)
    return start_center + (end_center - start_center) * fraction


def is_turn_at(dist):
    start_center, end_center, _ = _segment_at(dist)
    return start_center != end_center


def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)


def row_at(dist):
    return PLAYER_ROW - (dist - distance_traveled)


### ROAD
def road_center_x(y):
    return center_x_at_distance(dist_at(y))


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
    return road_left(y) + lane * ROAD_WIDTH


### RACE SETUP
def new_race():
    global player_speed, distance_traveled, rivals, game_state, player_start_lane
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "waiting"
    race_results = []
    player_place = None

    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_start_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_start_lane, PLAYER_ROW), PLAYER_ROW)

    rival_colors = random.sample(RIVAL_COLORS, k=len(grid) - 1)
    rivals = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
            "state": "racing",
            "freeze_timer": 0,
        }
        for lane_i, color in zip(grid[1:], rival_colors)
    ]
    for r in rivals:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)


new_race()


### DRAW
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
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)

    finish_y = row_at(FINISH_DISTANCE)
    if -20 < finish_y < HEIGHT:
        left = road_center_x(finish_y) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    for r in rivals:
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()
    if game_state != "frozen" or (freeze_timer // 6) % 2 == 0:
        player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} / {FINISH_DISTANCE} m",
                     topleft=(10, 40), fontsize=30, color="white")

    if game_state == "frozen":
        screen.draw.text("CRASHED! Recovering...", midtop=(WIDTH // 2, 10),
                         fontsize=32, color=(255, 90, 60))
    elif game_state == "racing" and is_turn_at(distance_traveled):
        screen.draw.text("TURN - stay on the road!", midtop=(WIDTH // 2, 10),
                         fontsize=32, color=(255, 220, 120))

    if game_state == "waiting":
        _banner("READY TO RACE?", "Press SPACE to start")
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")


def _draw_countdown():
    elapsed = COUNTDOWN_FRAMES - countdown_timer
    counting_frames = len(COUNTDOWN_NUMBERS) * FPS
    if elapsed < counting_frames:
        number = COUNTDOWN_NUMBERS[elapsed // FPS]
        _banner(str(number), "Get ready...")
    else:
        _banner("GO!", "")


def _ordinal(n):
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


### UPDATE
def update():
    global player_speed, distance_traveled, game_state, player_place
    global countdown_timer, freeze_timer

    if game_state == "waiting":
        if keyboard.space:
            game_state = "countdown"
            countdown_timer = COUNTDOWN_FRAMES
        return

    if game_state == "countdown":
        countdown_timer -= 1
        if countdown_timer <= 0:
            game_state = "racing"
        return

    if game_state == "won":
        if keyboard.space:
            new_race()
        return

    if game_state == "frozen":
        freeze_timer -= 1
        if freeze_timer <= 0:
            game_state = "racing"
    else:
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

    for r in rivals:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            y = row_at(r["distance"])
            r["actor"].pos = (lane_to_x(r["lane"], y), y)
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)

    if game_state == "racing":
        for r in rivals:
            if player.colliderect(r["actor"]):
                game_state = "frozen"
                freeze_timer = FREEZE_FRAMES
                player_speed = 0.0
                r["state"] = "frozen"
                r["freeze_timer"] = FREEZE_FRAMES
                player.x = lane_to_x(player_start_lane, PLAYER_ROW)
                r["actor"].x = lane_to_x(r["lane"], row_at(r["distance"]))
                break

        if distance_traveled >= FINISH_DISTANCE:
            player_place = len(race_results) + 1
            game_state = "won"
```
*Expected State: this runs exactly as the Week 4, Part 2 checkpoint always
has — one human player, four AI rivals, a countdown, a single window. Split
screen hasn't been touched yet.*

## Step 1: A Two-Player-Wide Road, and a Stacked Window

Simplify the tuning knobs first — there's no `LANE_COUNT` formula here, just
room for exactly two cars:

```python
LANE_WIDTH = 110
ROAD_WIDTH = LANE_WIDTH * 2      # just enough room for two cars to pass
SHOULDER_WIDTH = 55
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.12
BRAKE = 0.35
COAST = 0.04
ROUGH_BRAKE = 0.40

DASH_PERIOD = 60
DASH_LENGTH = 30

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
```

Then add the stacked-band setup:
```python
# ---------------------------------------------------------------------------
# STACKED BANDS
# ---------------------------------------------------------------------------
# The window is twice as tall as a normal single-player window, split into
# two equal bands. BAND_HEIGHT is how tall EACH player's private view is.
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2

# Where each player's own car sits, measured from the TOP OF THEIR OWN BAND
# (not the top of the whole window) - this is what makes the same drawing
# code work for both players even though their bands are in different
# places on screen.
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120

CENTER = WIDTH // 2
```
Add one colour for the bar between the two bands:
```python
DIVIDER = (20, 20, 20)     # the bar between the two bands
```

Keep your existing `TRACK` (the multi-turn lap from Week 4, Part 2)
unchanged — this file races the same course, just with two players on it
instead of one.

*Expected State: no visible change and nothing runnable yet. The window's
dimensions and the new constants exist, but `draw()` and `update()` still
reference the old single-player globals.*

**The Geometry:** `BAND_HEIGHT` is how tall one player's own view is; the
whole window is just two of them stacked, so `HEIGHT = BAND_HEIGHT * 2`.
`PLAYER_ROW_LOCAL` is measured from the top of a *band*, not the top of the
window — that's what lets the same number mean "480 pixels into my own
view" for both Player 1 (band starts at screen row 0) and Player 2 (band
starts at screen row 400). Nothing here computes an actual screen `y` yet;
that happens later, once drawing code adds a band's own `band_top` to a
local row.

## Step 2: Every Road Formula Takes a `player`

Just like the road-curving functions (`_segment_at`, `center_x_at_distance`,
`is_turn_at`), which stay exactly as they were, the *positional* formulas
that used to read a single global now take a `player` dictionary instead:

```python
# ---------------------------------------------------------------------------
# PER-PLAYER HELPERS
# ---------------------------------------------------------------------------
# Every function below takes a `player` dict as an argument, instead of
# reading global variables - that's what lets us call the exact same code
# for Player 1 and Player 2. Compare these to dist_at()/row_at()/
# road_center_x() from earlier weeks: same formulas, just with
# `player["distance"]` where there used to be a single `distance_traveled`.
def dist_at(y_local, player):
    return player["distance"] + (PLAYER_ROW_LOCAL - y_local)


def row_at(dist, player):
    return PLAYER_ROW_LOCAL - (dist - player["distance"])


def road_center_x(y_local, player):
    return center_x_at_distance(dist_at(y_local, player))


def road_left(y_local, player):
    return road_center_x(y_local, player) - ROAD_WIDTH // 2


def road_right(y_local, player):
    return road_center_x(y_local, player) + ROAD_WIDTH // 2


def on_road(x, y_local, player):
    return road_left(y_local, player) <= x <= road_right(y_local, player)


def on_shoulder(x, y_local, player):
    if on_road(x, y_local, player):
        return False
    return (road_left(y_local, player) - SHOULDER_WIDTH
            <= x <= road_right(y_local, player) + SHOULDER_WIDTH)
```
*Expected State: still nothing runnable. These functions now require a
`player` argument, but nothing in the file calls them that way yet — that
gets wired up in Step 3.*

**Teaching Note:** this refactor is mostly mechanical. Every one of these
functions already existed in some form since Week 1 or Week 2 — the only
change is reading `player["distance"]` where there used to be one shared
`distance_traveled`, and taking `y_local` (a row *within a band*) instead of
an absolute screen row. There's no `lane_to_x()` in this file at all, unlike
the AI-populated Week 5 files — with no rivals to place in lanes, each
player steers their own `x` position directly, the same way Week 1 always
did.

## Step 3: A Dictionary Per Player

```python
def make_player(label, car_image, band_top, key_left, key_right, key_up, key_down):
    """Build one player's state dict. `key_left`/etc. are the NAMES pgzero
    uses for that key (e.g. "left" for the left arrow, "a" for the A key) -
    we look them up on `keyboard` with getattr() every frame, in update()."""
    return {
        "label": label,
        "actor": Actor(car_image, (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "keys": (key_left, key_right, key_up, key_down),
    }


game_state = "waiting"          # "waiting" | "countdown" | "racing" | "won"
countdown_timer = 0
winner_label = None

players = [
    make_player("P1", "car_red", 0, "left", "right", "up", "down"),
    make_player("P2", "car_blue", BAND_HEIGHT, "a", "d", "w", "s"),
]


def new_race():
    global game_state, winner_label
    game_state = "waiting"
    winner_label = None
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["actor"].pos = (WIDTH // 2, player["band_top"] + PLAYER_ROW_LOCAL)


new_race()
```
*Expected State: still not runnable on its own. `game_state`, `players`,
and `new_race()` all exist now, but `draw()` and `update()` haven't been
rewritten to use them — the Mid-Session Checkpoint below borrows that code
early to get back to something playable.*

**Teaching Note:** everything that used to be a handful of global variables
(`player_speed`, `distance_traveled`, ...) now lives inside a dictionary
instead — one dict per player. That's the same trick already used for
rivals since Week 2: bundle related values together. This file just applies
it to the human players too, so the exact same drawing and steering code
can run once for Player 1 and once for Player 2, instead of being
duplicated by hand.

**Classroom Prompt (For Fast Finishers):** `make_player()` doesn't hard-code
"there are only two players" anywhere — it just takes whatever `band_top`
you hand it. What else would need to change to support a three-player,
three-band race? (Mostly `BAND_HEIGHT`/`HEIGHT` math and a third entry in
`players` — the per-player functions from Step 2 already generalize.)

## Mid-Session Checkpoint: Two Players, Two Bands, No Explanation Yet

Steps 1-3 replace the whole data model (one player + rivals → a `players`
list, no rivals at all) in one move, which leaves nothing runnable in
between — `draw()` and `update()` still expect the old globals. This
checkpoint borrows `draw()`/`draw_player_band()` from Step 4 and
`update_player()`/`update()` from Step 5 early, to get back to something
playable at this halfway point. Steps 4 and 5 below walk through this exact
code, with the explanation. At this stage, the full Python script should
look something like this:

```python
### CONSTANTS
LANE_WIDTH = 110
ROAD_WIDTH = LANE_WIDTH * 2
SHOULDER_WIDTH = 55
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.12
BRAKE = 0.35
COAST = 0.04
ROUGH_BRAKE = 0.40

DASH_PERIOD = 60
DASH_LENGTH = 30

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN

### STACKED BANDS
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2

PLAYER_ROW_LOCAL = BAND_HEIGHT - 120

CENTER = WIDTH // 2

DIVIDER = (20, 20, 20)

### TRACK
TRACK = [
    (300, CENTER),
    (300, CENTER - 150),
    (250, CENTER - 150),
    (350, CENTER + 160),
    (250, CENTER + 160),
    (300, CENTER),
    (250, CENTER - 120),
    (350, CENTER + 120),
    (300, CENTER),
    (300, CENTER - 140),
    (250, CENTER - 140),
    (350, CENTER + 150),
    (350, CENTER),
]
FINISH_DISTANCE = sum(length for length, _ in TRACK)

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)


### TRACK MATH
def _segment_at(dist):
    start_center = CENTER
    covered = 0
    for length, end_center in TRACK:
        if dist < covered + length:
            fraction = (dist - covered) / length
            return start_center, end_center, fraction
        covered += length
        start_center = end_center
    return start_center, start_center, 1.0


def center_x_at_distance(dist):
    start_center, end_center, fraction = _segment_at(dist)
    return start_center + (end_center - start_center) * fraction


def is_turn_at(dist):
    start_center, end_center, _ = _segment_at(dist)
    return start_center != end_center


### PER-PLAYER HELPERS
def dist_at(y_local, player):
    return player["distance"] + (PLAYER_ROW_LOCAL - y_local)


def row_at(dist, player):
    return PLAYER_ROW_LOCAL - (dist - player["distance"])


def road_center_x(y_local, player):
    return center_x_at_distance(dist_at(y_local, player))


def road_left(y_local, player):
    return road_center_x(y_local, player) - ROAD_WIDTH // 2


def road_right(y_local, player):
    return road_center_x(y_local, player) + ROAD_WIDTH // 2


def on_road(x, y_local, player):
    return road_left(y_local, player) <= x <= road_right(y_local, player)


def on_shoulder(x, y_local, player):
    if on_road(x, y_local, player):
        return False
    return (road_left(y_local, player) - SHOULDER_WIDTH
            <= x <= road_right(y_local, player) + SHOULDER_WIDTH)


### PLAYERS
def make_player(label, car_image, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor(car_image, (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "keys": (key_left, key_right, key_up, key_down),
    }


game_state = "waiting"
countdown_timer = 0
winner_label = None

players = [
    make_player("P1", "car_red", 0, "left", "right", "up", "down"),
    make_player("P2", "car_blue", BAND_HEIGHT, "a", "d", "w", "s"),
]


def new_race():
    global game_state, winner_label
    game_state = "waiting"
    winner_label = None
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["actor"].pos = (WIDTH // 2, player["band_top"] + PLAYER_ROW_LOCAL)


new_race()


### DRAW
def draw():
    screen.fill(DIVIDER)

    for player in players:
        draw_player_band(player)

    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, BAND_HEIGHT - 2, WIDTH, 4), DIVIDER)

    if game_state == "waiting":
        _banner("READY TO RACE?", "P1: Arrow keys   P2: W A S D   -   SPACE to start")
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        _banner(f"{winner_label} WINS!", "Press SPACE to race again")


def draw_player_band(player):
    """Draw one player's entire world - road, car, HUD - clipped to their
    own band so it can never draw over the other player's half."""
    band_top = player["band_top"]

    screen.surface.set_clip(Rect(0, band_top, WIDTH, BAND_HEIGHT))

    screen.draw.filled_rect(Rect(0, band_top, WIDTH, BAND_HEIGHT), GRASS)

    strip_height = 10
    for top_local in range(0, BAND_HEIGHT, strip_height):
        y_local = top_local + strip_height // 2
        top = band_top + top_local
        center_x = road_center_x(y_local, player)
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
        if dist_at(y_local, player) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    finish_y_local = row_at(FINISH_DISTANCE, player)
    if -20 < finish_y_local < BAND_HEIGHT:
        finish_y = band_top + finish_y_local
        left = road_center_x(finish_y_local, player) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    player["actor"].draw()

    screen.draw.text(f"{player['label']}  Speed: {player['speed']:0.1f}",
                     topleft=(10, band_top + 10), fontsize=26, color="white")
    screen.draw.text(f"{int(player['distance'])} / {FINISH_DISTANCE} m",
                     topleft=(10, band_top + 36), fontsize=22, color="white")


def _draw_countdown():
    elapsed = COUNTDOWN_FRAMES - countdown_timer
    counting_frames = len(COUNTDOWN_NUMBERS) * FPS
    if elapsed < counting_frames:
        number = COUNTDOWN_NUMBERS[elapsed // FPS]
        _banner(str(number), "Get ready...")
    else:
        _banner("GO!", "")


def _banner(title, subtitle):
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=54, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=24, color="white")


### UPDATE
def update_player(player):
    """Move one player. Note this reads player["keys"] with getattr()
    instead of hard-coding `keyboard.left` - that's the one line that lets
    Player 1 and Player 2 share this same function with different keys."""
    key_left, key_right, key_up, key_down = player["keys"]

    if getattr(keyboard, key_left):
        player["actor"].x -= 5
    if getattr(keyboard, key_right):
        player["actor"].x += 5
    player["actor"].x = max(20, min(WIDTH - 20, player["actor"].x))

    if getattr(keyboard, key_up):
        player["speed"] += ACCEL
    elif getattr(keyboard, key_down):
        player["speed"] -= BRAKE
    else:
        player["speed"] -= COAST

    x = player["actor"].x
    if on_shoulder(x, PLAYER_ROW_LOCAL, player):
        if player["speed"] > SHOULDER_MAX_SPEED:
            player["speed"] -= ROUGH_BRAKE
    elif not on_road(x, PLAYER_ROW_LOCAL, player):
        if player["speed"] > ROUGH_MAX_SPEED:
            player["speed"] -= ROUGH_BRAKE

    player["speed"] = max(0.0, min(MAX_SPEED, player["speed"]))
    player["distance"] += player["speed"]


def update():
    global game_state, countdown_timer, winner_label

    if game_state == "waiting":
        if keyboard.space:
            game_state = "countdown"
            countdown_timer = COUNTDOWN_FRAMES
        return

    if game_state == "countdown":
        countdown_timer -= 1
        if countdown_timer <= 0:
            game_state = "racing"
        return

    if game_state == "won":
        if keyboard.space:
            new_race()
        return

    for player in players:
        update_player(player)

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            winner_label = player["label"]
            game_state = "won"
            break
```
*Expected State: two full bands stacked in one window, both players
driving the same course independently — Player 1 on arrow keys in the top
half, Player 2 on WASD in the bottom half. This already plays like the
finished file.*

Steps 4 and 5 don't add any new behavior — they walk through the two
tricks that make this checkpoint work (`set_clip()` for the split,
`getattr()` for per-player keys), one piece at a time. Read them as
commentary on the code above, not as new code to type.

## Step 4: Two Bands, One Window

```python
def draw():
    # A neutral background behind everything (mostly hidden once both bands
    # are drawn, but avoids a flash of the wrong colour at the very edges).
    screen.fill(DIVIDER)

    for player in players:
        draw_player_band(player)

    # Draw the thin divider bar LAST, without any clip applied, so it always
    # shows up on top of both bands.
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, BAND_HEIGHT - 2, WIDTH, 4), DIVIDER)

    if game_state == "waiting":
        _banner("READY TO RACE?", "P1: Arrow keys   P2: W A S D   -   SPACE to start")
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        _banner(f"{winner_label} WINS!", "Press SPACE to race again")


def draw_player_band(player):
    band_top = player["band_top"]

    # Everything from here down is clipped to a WIDTH x BAND_HEIGHT
    # rectangle starting at this player's band_top. Any shape or text we
    # draw that would land outside that rectangle is simply not shown.
    screen.surface.set_clip(Rect(0, band_top, WIDTH, BAND_HEIGHT))

    screen.draw.filled_rect(Rect(0, band_top, WIDTH, BAND_HEIGHT), GRASS)

    strip_height = 10
    for top_local in range(0, BAND_HEIGHT, strip_height):
        y_local = top_local + strip_height // 2
        top = band_top + top_local          # actual screen y for this strip
        center_x = road_center_x(y_local, player)
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
        if dist_at(y_local, player) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    finish_y_local = row_at(FINISH_DISTANCE, player)
    if -20 < finish_y_local < BAND_HEIGHT:
        finish_y = band_top + finish_y_local
        left = road_center_x(finish_y_local, player) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    player["actor"].draw()

    screen.draw.text(f"{player['label']}  Speed: {player['speed']:0.1f}",
                     topleft=(10, band_top + 10), fontsize=26, color="white")
    screen.draw.text(f"{int(player['distance'])} / {FINISH_DISTANCE} m",
                     topleft=(10, band_top + 36), fontsize=22, color="white")
```
*Expected State: identical on-screen behavior to the checkpoint above —
this step doesn't change what the game does, only explains the `draw()`
code that's already running.*

**The Geometry:** `screen.surface.set_clip(rect)` tells Pygame Zero "only
actually paint pixels inside this rectangle — ignore anything drawn outside
it." Player 1's whole world (road, car, HUD) draws completely normally,
just with the clip rectangle limited to the TOP half of the window;
`draw_player_band()` itself doesn't know or care that it's being clipped.
The same function then runs again for Player 2, clipped to the BOTTOM half
instead. Two calls to one function, two different clip rectangles, and the
result reads as two independent split screens. `set_clip(None)` turns
clipping back off — needed for anything meant to span the whole window,
like the divider bar or a banner.

**Classroom Demo:** comment out the `screen.surface.set_clip(None)` call
at the top of `_banner()` and trigger the "READY TO RACE?" banner while a
band's clip rectangle is still active. Half the banner text gets clipped
away — a fast, concrete demonstration of what "ignore anything drawn
outside this rectangle" actually means.

Countdown and banner helpers are otherwise unchanged in shape from earlier
weeks — the one new detail is that `_banner()` must call
`screen.surface.set_clip(None)` itself, so a banner always spans the full
window even if the last thing drawn was clipped to one band.

## Step 5: Moving Both Players

```python
def update_player(player):
    key_left, key_right, key_up, key_down = player["keys"]

    if getattr(keyboard, key_left):
        player["actor"].x -= 5
    if getattr(keyboard, key_right):
        player["actor"].x += 5
    player["actor"].x = max(20, min(WIDTH - 20, player["actor"].x))

    if getattr(keyboard, key_up):
        player["speed"] += ACCEL
    elif getattr(keyboard, key_down):
        player["speed"] -= BRAKE
    else:
        player["speed"] -= COAST

    x = player["actor"].x
    if on_shoulder(x, PLAYER_ROW_LOCAL, player):
        if player["speed"] > SHOULDER_MAX_SPEED:
            player["speed"] -= ROUGH_BRAKE
    elif not on_road(x, PLAYER_ROW_LOCAL, player):
        if player["speed"] > ROUGH_MAX_SPEED:
            player["speed"] -= ROUGH_BRAKE

    player["speed"] = max(0.0, min(MAX_SPEED, player["speed"]))
    player["distance"] += player["speed"]


def update():
    global game_state, countdown_timer, winner_label

    if game_state == "waiting":
        if keyboard.space:
            game_state = "countdown"
            countdown_timer = COUNTDOWN_FRAMES
        return

    if game_state == "countdown":
        countdown_timer -= 1
        if countdown_timer <= 0:
            game_state = "racing"
        return

    if game_state == "won":
        if keyboard.space:
            new_race()
        return

    # "racing": move both players with the exact same function - this is
    # the payoff of putting each player's state in its own dict instead of
    # its own set of separate global variables.
    for player in players:
        update_player(player)

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            winner_label = player["label"]
            game_state = "won"
            break   # whoever we find first crossing the line this frame wins
```
*Expected State: identical on-screen behavior to the checkpoint above —
this step explains the `update()` code already running, it doesn't change
anything.*

**The Concept:** `key_left` is a *string* (`"left"` or `"a"`), and Python
has no built-in way to write `keyboard.key_left` and have it look up the
attribute *named by that string's value* — that syntax would look for a
literal attribute called `key_left`, which doesn't exist. `getattr(object,
name)` is the tool for exactly this: "fetch the attribute of `object` whose
name is this string." It's the one line that lets `update_player()` serve
two players with two different keyboards' worth of keys.

**Classroom Prompt (For Fast Finishers):** `update_player()` already reads
its keys from `player["keys"]` instead of assuming arrow-keys-vs-WASD. What
would it take to let a player remap their own keys from the "waiting"
screen, before the countdown starts? (Nothing here would need to change —
only the call site that builds each player with `make_player()` would pass
different key names.)

## Checkpoint: Final Code for the Optional Extra

The full script should now match `05_week5_split_screen.py` — two human
players, stacked, racing the same course, no AI.

```python
### CONSTANTS
LANE_WIDTH = 110
ROAD_WIDTH = LANE_WIDTH * 2
SHOULDER_WIDTH = 55
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.12
BRAKE = 0.35
COAST = 0.04
ROUGH_BRAKE = 0.40

DASH_PERIOD = 60
DASH_LENGTH = 30

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN

### STACKED BANDS
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2

PLAYER_ROW_LOCAL = BAND_HEIGHT - 120

### TRACK
CENTER = WIDTH // 2
TRACK = [
    (300, CENTER),
    (300, CENTER - 150),
    (250, CENTER - 150),
    (350, CENTER + 160),
    (250, CENTER + 160),
    (300, CENTER),
    (250, CENTER - 120),
    (350, CENTER + 120),
    (300, CENTER),
    (300, CENTER - 140),
    (250, CENTER - 140),
    (350, CENTER + 150),
    (350, CENTER),
]
FINISH_DISTANCE = sum(length for length, _ in TRACK)

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)
DIVIDER = (20, 20, 20)


### TRACK MATH
def _segment_at(dist):
    start_center = CENTER
    covered = 0
    for length, end_center in TRACK:
        if dist < covered + length:
            fraction = (dist - covered) / length
            return start_center, end_center, fraction
        covered += length
        start_center = end_center
    return start_center, start_center, 1.0


def center_x_at_distance(dist):
    start_center, end_center, fraction = _segment_at(dist)
    return start_center + (end_center - start_center) * fraction


def is_turn_at(dist):
    start_center, end_center, _ = _segment_at(dist)
    return start_center != end_center


### ROAD
def dist_at(y_local, player):
    return player["distance"] + (PLAYER_ROW_LOCAL - y_local)


def row_at(dist, player):
    return PLAYER_ROW_LOCAL - (dist - player["distance"])


def road_center_x(y_local, player):
    return center_x_at_distance(dist_at(y_local, player))


def road_left(y_local, player):
    return road_center_x(y_local, player) - ROAD_WIDTH // 2


def road_right(y_local, player):
    return road_center_x(y_local, player) + ROAD_WIDTH // 2


def on_road(x, y_local, player):
    return road_left(y_local, player) <= x <= road_right(y_local, player)


def on_shoulder(x, y_local, player):
    if on_road(x, y_local, player):
        return False
    return (road_left(y_local, player) - SHOULDER_WIDTH
            <= x <= road_right(y_local, player) + SHOULDER_WIDTH)


### PLAYERS
def make_player(label, car_image, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor(car_image, (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "keys": (key_left, key_right, key_up, key_down),
    }


game_state = "waiting"
countdown_timer = 0
winner_label = None

players = [
    make_player("P1", "car_red", 0, "left", "right", "up", "down"),
    make_player("P2", "car_blue", BAND_HEIGHT, "a", "d", "w", "s"),
]


### RACE SETUP
def new_race():
    global game_state, winner_label
    game_state = "waiting"
    winner_label = None
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["actor"].pos = (WIDTH // 2, player["band_top"] + PLAYER_ROW_LOCAL)


new_race()


### DRAW
def draw():
    screen.fill(DIVIDER)

    for player in players:
        draw_player_band(player)

    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, BAND_HEIGHT - 2, WIDTH, 4), DIVIDER)

    if game_state == "waiting":
        _banner("READY TO RACE?", "P1: Arrow keys   P2: W A S D   -   SPACE to start")
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        _banner(f"{winner_label} WINS!", "Press SPACE to race again")


def draw_player_band(player):
    band_top = player["band_top"]

    screen.surface.set_clip(Rect(0, band_top, WIDTH, BAND_HEIGHT))

    screen.draw.filled_rect(Rect(0, band_top, WIDTH, BAND_HEIGHT), GRASS)

    strip_height = 10
    for top_local in range(0, BAND_HEIGHT, strip_height):
        y_local = top_local + strip_height // 2
        top = band_top + top_local
        center_x = road_center_x(y_local, player)
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
        if dist_at(y_local, player) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    finish_y_local = row_at(FINISH_DISTANCE, player)
    if -20 < finish_y_local < BAND_HEIGHT:
        finish_y = band_top + finish_y_local
        left = road_center_x(finish_y_local, player) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    player["actor"].draw()

    screen.draw.text(f"{player['label']}  Speed: {player['speed']:0.1f}",
                     topleft=(10, band_top + 10), fontsize=26, color="white")
    screen.draw.text(f"{int(player['distance'])} / {FINISH_DISTANCE} m",
                     topleft=(10, band_top + 36), fontsize=22, color="white")


def _draw_countdown():
    elapsed = COUNTDOWN_FRAMES - countdown_timer
    counting_frames = len(COUNTDOWN_NUMBERS) * FPS
    if elapsed < counting_frames:
        number = COUNTDOWN_NUMBERS[elapsed // FPS]
        _banner(str(number), "Get ready...")
    else:
        _banner("GO!", "")


def _banner(title, subtitle):
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=54, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=24, color="white")


### UPDATE
def update_player(player):
    key_left, key_right, key_up, key_down = player["keys"]

    if getattr(keyboard, key_left):
        player["actor"].x -= 5
    if getattr(keyboard, key_right):
        player["actor"].x += 5
    player["actor"].x = max(20, min(WIDTH - 20, player["actor"].x))

    if getattr(keyboard, key_up):
        player["speed"] += ACCEL
    elif getattr(keyboard, key_down):
        player["speed"] -= BRAKE
    else:
        player["speed"] -= COAST

    x = player["actor"].x
    if on_shoulder(x, PLAYER_ROW_LOCAL, player):
        if player["speed"] > SHOULDER_MAX_SPEED:
            player["speed"] -= ROUGH_BRAKE
    elif not on_road(x, PLAYER_ROW_LOCAL, player):
        if player["speed"] > ROUGH_MAX_SPEED:
            player["speed"] -= ROUGH_BRAKE

    player["speed"] = max(0.0, min(MAX_SPEED, player["speed"]))
    player["distance"] += player["speed"]


def update():
    global game_state, countdown_timer, winner_label

    if game_state == "waiting":
        if keyboard.space:
            game_state = "countdown"
            countdown_timer = COUNTDOWN_FRAMES
        return

    if game_state == "countdown":
        countdown_timer -= 1
        if countdown_timer <= 0:
            game_state = "racing"
        return

    if game_state == "won":
        if keyboard.space:
            new_race()
        return

    for player in players:
        update_player(player)

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            winner_label = player["label"]
            game_state = "won"
            break
```
*Expected State: the finished file — two stacked bands, two independent
human-controlled cars, one shared course, no AI and no menu.*

**Watch for:** there are no AI rivals and no collisions between the two
players in this file — both players race their own private copy of the
track and can't affect each other at all. Both are intentional gaps and
natural "extend this yourself" prompts for a student who finishes early:
try adding a shared set of AI rivals (Part 2's approach), or make the two
players able to bump into each other.
