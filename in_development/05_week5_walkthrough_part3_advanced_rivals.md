# Week 5, Part 3 Walkthrough — Advanced Rivals: Lane Changes and Rival-vs-Rival Crashes

Every AI racer has sat in one lane for the whole race, ever since Week 3 —
`r["lane"]` was set once, on the starting grid, and never touched again.
This session makes that value drift: each racer holds its lane for a random
few seconds, then eases smoothly over to a newly-picked one, and repeats.
**Nothing about drawing or player-vs-racer collision needs to change** —
`lane_to_x`, `draw_player_band`, and the collision check all already read
`r["lane"]` fresh every frame, so making that value change over time flows
straight through code that already exists. The one genuinely new mechanic:
racers can now meet each other.

## Starting Code for Week 5, Part 3

Start from the Week 5, Part 2 checkpoint (`05_week5_part2_multiplayer.py`).
```python
import random

### MENU OPTIONS

CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RACERS = 5

LENGTH_OPTIONS = [
    ("Short", 3900),
    ("Medium", 7800),
    ("Long", 15600),
]
DIFFICULTY_OPTIONS = [
    ("Easy", (4.0, 6.0)),
    ("Normal", (5.0, 8.5)),
    ("Hard", (7.0, 10.0)),
]
MENU_FIELDS = ["P1 Car", "P2 Car", "Racers", "Length", "Difficulty"]

selected_field = 0
p1_car_index = 0
p2_car_index = 1
num_racers = 4
length_index = 1
difficulty_index = 1

### CONSTANTS

LANE_WIDTH = 110
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
FREEZE_FRAMES = 2 * FPS
PLAYER_COLLISION_DISTANCE = 80

### COLOURS (cars)

RACER_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange",
                "car_pink", "car_silver", "car_white"]

### WINDOW SIZE

_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120
CENTER = WIDTH // 2

### TRACK

ONE_LAP = [
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
TRACK = ONE_LAP * 4

### COLOURS

GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)
DIVIDER = (20, 20, 20)

### CURRENTLY APPLIED SETTINGS

NUM_RACERS = num_racers
LANE_COUNT = NUM_RACERS
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]

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

def dist_at(y_local, player):
    return player["distance"] + (PLAYER_ROW_LOCAL - y_local)

def row_at(dist, player):
    return PLAYER_ROW_LOCAL - (dist - player["distance"])

### ROAD

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

def lane_to_x(lane, y_local, player):
    return road_left(y_local, player) + lane * ROAD_WIDTH

def _player_lane(player):
    return (player["actor"].x - road_left(PLAYER_ROW_LOCAL, player)) / ROAD_WIDTH

### PLAYERS AND RACERS

def make_player(label, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor("car_red", (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "state": "racing",
        "freeze_timer": 0,
        "place": None,
        "start_lane": 0.0,
        "keys": (key_left, key_right, key_up, key_down),
    }

game_state = "waiting"
countdown_timer = 0

players = [
    make_player("P1", 0, "left", "right", "up", "down"),
    make_player("P2", BAND_HEIGHT, "a", "d", "w", "s"),
]

racers = []

race_results = []

### RACE SETUP

def _apply_menu_choices():
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    players[0]["actor"].image = CAR_CHOICES[p1_car_index]
    players[1]["actor"].image = CAR_CHOICES[p2_car_index]

def _new_grid():
    global racers
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)

    for i, player in enumerate(players):
        player["start_lane"] = (grid[i] + 0.5) / LANE_COUNT
        player["actor"].x = lane_to_x(player["start_lane"], PLAYER_ROW_LOCAL, player)

    used_colors = {player["actor"].image for player in players}
    available_colors = [c for c in RACER_COLORS if c not in used_colors]
    ai_lanes = grid[len(players):]
    racer_colors = random.sample(available_colors, k=len(ai_lanes))

    racers = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
            "state": "racing",
            "freeze_timer": 0,
        }
        for lane_i, color in zip(ai_lanes, racer_colors)
    ]
    for r in racers:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW_LOCAL, players[0]),
                          players[0]["band_top"] + PLAYER_ROW_LOCAL)

def new_race():
    global game_state, race_results
    game_state = "waiting"
    race_results = []
    _new_grid()
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["state"] = "racing"
        player["freeze_timer"] = 0
        player["place"] = None
        player["actor"].y = player["band_top"] + PLAYER_ROW_LOCAL

_apply_menu_choices()
new_race()

### MENU

def on_key_down(key):
    global selected_field, p1_car_index, p2_car_index
    global num_racers, length_index, difficulty_index
    global game_state, countdown_timer

    if game_state != "waiting":
        return

    if key == keys.UP:
        selected_field = (selected_field - 1) % len(MENU_FIELDS)
    elif key == keys.DOWN:
        selected_field = (selected_field + 1) % len(MENU_FIELDS)
    elif key in (keys.LEFT, keys.RIGHT):
        direction = -1 if key == keys.LEFT else 1
        field = MENU_FIELDS[selected_field]
        if field == "P1 Car":
            p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
            if p1_car_index == p2_car_index:
                p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
        elif field == "P2 Car":
            p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
            if p2_car_index == p1_car_index:
                p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
        elif field == "Racers":
            num_racers = max(2, min(MAX_RACERS, num_racers + direction))
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        _apply_menu_choices()
        new_race()
    elif key == keys.SPACE:
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES

### DRAW

def draw():
    screen.fill(DIVIDER)
    for player in players:
        draw_player_band(player)

    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, BAND_HEIGHT - 2, WIDTH, 4), DIVIDER)

    if game_state == "waiting":
        _draw_menu()
    elif game_state == "countdown":
        _draw_countdown()

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
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)

    finish_y_local = row_at(FINISH_DISTANCE, player)
    if -20 < finish_y_local < BAND_HEIGHT:
        finish_y = band_top + finish_y_local
        left = road_center_x(finish_y_local, player) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    for r in racers:
        y_local = row_at(r["distance"], player)
        r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                          player["band_top"] + y_local)
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()

    for other in players:
        if other is player:
            continue
        other_y_local = row_at(other["distance"], player)
        saved_pos = other["actor"].pos
        other["actor"].pos = (lane_to_x(_player_lane(other), other_y_local, player),
                              player["band_top"] + other_y_local)
        if other["state"] != "frozen" or (other["freeze_timer"] // 6) % 2 == 0:
            other["actor"].draw()
        other["actor"].pos = saved_pos

    if player["state"] != "frozen" or (player["freeze_timer"] // 6) % 2 == 0:
        player["actor"].draw()

    screen.draw.text(f"{player['label']}  Speed: {player['speed']:0.1f}",
                     topleft=(10, band_top + 10), fontsize=26, color="white")
    screen.draw.text(f"{int(player['distance'])} / {FINISH_DISTANCE} m",
                     topleft=(10, band_top + 36), fontsize=22, color="white")
    if player["state"] == "frozen":
        screen.draw.text("CRASHED! Recovering...",
                         midtop=(WIDTH // 2, band_top + 10),
                         fontsize=24, color=(255, 90, 60))
    elif player["state"] == "finished":
        title = "YOU WIN!" if player["place"] == 1 else f"YOU FINISHED {_ordinal(player['place'])}!"
        subtitle = ("Press SPACE to race again" if game_state == "won"
                    else "Waiting for the other player...")
        screen.draw.filled_rect(Rect(0, band_top + BAND_HEIGHT // 2 - 50, WIDTH, 100),
                                (0, 0, 0))
        screen.draw.text(title, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 - 15),
                         fontsize=40, color="white")
        screen.draw.text(subtitle, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 + 20),
                         fontsize=20, color="white")

def _draw_menu():
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 160, WIDTH, 320), (0, 0, 0))
    screen.draw.text("READY TO RACE?", center=(WIDTH // 2, HEIGHT // 2 - 130),
                     fontsize=40, color="white")

    values = [
        CAR_CHOICES[p1_car_index].replace("car_", "").title(),
        CAR_CHOICES[p2_car_index].replace("car_", "").title(),
        str(num_racers),
        LENGTH_OPTIONS[length_index][0],
        DIFFICULTY_OPTIONS[difficulty_index][0],
    ]
    line_y = HEIGHT // 2 - 85
    for i, field in enumerate(MENU_FIELDS):
        is_selected = (i == selected_field)
        arrow = "> " if is_selected else "   "
        color = (255, 220, 120) if is_selected else "white"
        text = f"{arrow}{field}: {'< ' if is_selected else ''}{values[i]}{' >' if is_selected else ''}"
        screen.draw.text(text, center=(WIDTH // 2, line_y), fontsize=26, color=color)
        line_y += 30

    screen.draw.text("UP/DOWN choose a setting, LEFT/RIGHT change it, SPACE to start",
                     center=(WIDTH // 2, line_y + 10), fontsize=20, color="white")
    screen.draw.text("P1: Arrow keys      P2: W A S D",
                     center=(WIDTH // 2, line_y + 34), fontsize=20, color="white")

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

def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"

### UPDATE

def update_player(player):
    if player["state"] == "finished":
        return
    if player["state"] == "frozen":
        player["freeze_timer"] -= 1
        if player["freeze_timer"] <= 0:
            player["state"] = "racing"
    else:
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

    if player["state"] == "racing":
        for r in racers:
            y_local = row_at(r["distance"], player)
            r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                              player["band_top"] + y_local)
            if player["actor"].colliderect(r["actor"]):
                player["state"] = "frozen"
                player["freeze_timer"] = FREEZE_FRAMES
                player["speed"] = 0.0
                r["state"] = "frozen"
                r["freeze_timer"] = FREEZE_FRAMES
                player["actor"].x = lane_to_x(player["start_lane"],
                                               PLAYER_ROW_LOCAL, player)
                break

def update_racers():
    for r in racers:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)

def _check_player_collision():
    p1, p2 = players
    if p1["state"] != "racing" or p2["state"] != "racing":
        return
    lane_gap = 0.5 / LANE_COUNT
    same_lane = abs(_player_lane(p1) - _player_lane(p2)) < lane_gap
    same_spot = abs(p1["distance"] - p2["distance"]) < PLAYER_COLLISION_DISTANCE
    if same_lane and same_spot:
        for p in players:
            p["state"] = "frozen"
            p["freeze_timer"] = FREEZE_FRAMES
            p["speed"] = 0.0
            p["actor"].x = lane_to_x(p["start_lane"], PLAYER_ROW_LOCAL, p)

def update():
    global game_state, countdown_timer

    if game_state == "waiting":
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

    update_racers()
    for player in players:
        update_player(player)
    _check_player_collision()

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            player["state"] = "finished"
            player["place"] = len(race_results) + 1
            race_results.append(player)

    if all(player["finished"] for player in players):
        game_state = "won"
```
*Expected State: the same two-band split-screen race as the end of Part 2 —
both players driving, AI racers holding fixed lanes for the whole race, and
player-vs-racer collisions already working.*

## Step 1: New Tuning Knobs

Add these near the other tuning constants:

```python
# --- Lane-changing rivals ----------------------------------------------------
LANE_CHANGE_MIN_HOLD = FPS * 2   # hold a lane for at least 2 seconds...
LANE_CHANGE_MAX_HOLD = FPS * 5   # ...and at most 5, before picking a new one
LANE_EASE_SPEED = 0.02           # fraction of the road crossed per frame
                                  # while easing toward a new lane

# --- Rival-vs-rival crashes --------------------------------------------------
RIVAL_COLLISION_DISTANCE = 80    # "same spot" = within roughly a car length
RIVAL_CRASH_CHANCE = 0.25        # otherwise they swerve to avoid it
```
*Expected State: no visible change — these are just new constants, nothing
reads them yet.*

**Teaching Note:** a random range instead of one fixed hold time keeps the
racers out of lockstep. If every racer switched lanes on exactly the same
schedule, the whole field would drift together and read as robotic. Drawing
an independent random hold time (2 to 5 seconds) for each racer is what makes
the lane changes look staggered instead of synchronized.

## Step 2: Give Each Racer a Target to Ease Toward

In `_new_grid()`, add two new fields to each racer dictionary:

```python
    racers = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "target_lane": (lane_i + 0.5) / LANE_COUNT,   # eased toward, see
                                                            # update_racers()
            "lane_change_timer": random.randint(LANE_CHANGE_MIN_HOLD,
                                                 LANE_CHANGE_MAX_HOLD),
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
            "state": "racing",       # "racing" | "frozen" - mirrors a player's own
            "freeze_timer": 0,
        }
        for lane_i, color in zip(ai_lanes, racer_colors)
    ]
```
*Expected State: no visible change — every racer still just sits in its
starting lane, same as before.*

**The Concept:** `"lane"` and `"target_lane"` split "where a racer is" from
"where it's heading." Everything that already reads a racer's position —
drawing, the player-vs-racer collision check — keeps reading `"lane"`,
unchanged. `"target_lane"` only matters to the easing logic added in Step 3.
Starting the two equal means a racer begins the race mid-hold, not
mid-lane-change: it sits still for one full `lane_change_timer` countdown
before its first move.

## Step 3: Easing Toward a Moving Target

Update `update_racers()` — after the existing "hold `if r["state"] ==
"racing"`" block that advances `distance` and checks for finishing, add the
lane-change logic (still inside that same `if`):

```python
            # Hold the current lane for a while, then ease over to a new
            # one - a lane change is just "pick a new target, then nudge
            # `lane` a little closer to it every frame until they match."
            r["lane_change_timer"] -= 1
            if r["lane_change_timer"] <= 0:
                r["target_lane"] = (random.randrange(LANE_COUNT) + 0.5) / LANE_COUNT
                r["lane_change_timer"] = random.randint(LANE_CHANGE_MIN_HOLD,
                                                          LANE_CHANGE_MAX_HOLD)
            if r["lane"] < r["target_lane"]:
                r["lane"] = min(r["target_lane"], r["lane"] + LANE_EASE_SPEED)
            elif r["lane"] > r["target_lane"]:
                r["lane"] = max(r["target_lane"], r["lane"] - LANE_EASE_SPEED)
```
*Expected State: every AI racer now drifts smoothly between lanes over the
course of the race, instead of holding one lane the whole time.*

**Math Concept:** "ease toward a target" nudges a value a fixed amount per
frame — it doesn't jump straight to the destination.
- Below the target: nudge up by `LANE_EASE_SPEED`.
- Above the target: nudge down by the same amount.
- `min(target, lane + step)` and `max(target, lane - step)` stop the nudge
  from overshooting. Without them, a racer at `lane = 0.39` easing toward
  `target_lane = 0.40` could jump past it to `0.41` and oscillate around the
  target forever instead of settling on it.

This is the same shape as `player_speed` climbing toward `MAX_SPEED` back in
Week 1 — a value nudged toward a ceiling, one step per frame. The only thing
that changed is the ceiling can now move.

## Mid-Session Checkpoint: Racers Drift Between Lanes, but Never Meet

At this stage, the full Python script should look something like this:

```python
import random

### MENU OPTIONS

CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RACERS = 5

LENGTH_OPTIONS = [
    ("Short", 3900),
    ("Medium", 7800),
    ("Long", 15600),
]
DIFFICULTY_OPTIONS = [
    ("Easy", (4.0, 6.0)),
    ("Normal", (5.0, 8.5)),
    ("Hard", (7.0, 10.0)),
]
MENU_FIELDS = ["P1 Car", "P2 Car", "Racers", "Length", "Difficulty"]

selected_field = 0
p1_car_index = 0
p2_car_index = 1
num_racers = 4
length_index = 1
difficulty_index = 1

### CONSTANTS

LANE_WIDTH = 110
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
FREEZE_FRAMES = 2 * FPS
PLAYER_COLLISION_DISTANCE = 80

### COLOURS (cars)

RACER_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange",
                "car_pink", "car_silver", "car_white"]

### LANE-CHANGING RIVALS

LANE_CHANGE_MIN_HOLD = FPS * 2
LANE_CHANGE_MAX_HOLD = FPS * 5
LANE_EASE_SPEED = 0.02

### WINDOW SIZE

_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120
CENTER = WIDTH // 2

### TRACK

ONE_LAP = [
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
TRACK = ONE_LAP * 4

### COLOURS

GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)
DIVIDER = (20, 20, 20)

### CURRENTLY APPLIED SETTINGS

NUM_RACERS = num_racers
LANE_COUNT = NUM_RACERS
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]

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

def dist_at(y_local, player):
    return player["distance"] + (PLAYER_ROW_LOCAL - y_local)

def row_at(dist, player):
    return PLAYER_ROW_LOCAL - (dist - player["distance"])

### ROAD

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

def lane_to_x(lane, y_local, player):
    return road_left(y_local, player) + lane * ROAD_WIDTH

def _player_lane(player):
    return (player["actor"].x - road_left(PLAYER_ROW_LOCAL, player)) / ROAD_WIDTH

### PLAYERS AND RACERS

def make_player(label, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor("car_red", (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "state": "racing",
        "freeze_timer": 0,
        "place": None,
        "start_lane": 0.0,
        "keys": (key_left, key_right, key_up, key_down),
    }

game_state = "waiting"
countdown_timer = 0

players = [
    make_player("P1", 0, "left", "right", "up", "down"),
    make_player("P2", BAND_HEIGHT, "a", "d", "w", "s"),
]

racers = []

race_results = []

### RACE SETUP

def _apply_menu_choices():
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    players[0]["actor"].image = CAR_CHOICES[p1_car_index]
    players[1]["actor"].image = CAR_CHOICES[p2_car_index]

def _new_grid():
    global racers
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)

    for i, player in enumerate(players):
        player["start_lane"] = (grid[i] + 0.5) / LANE_COUNT
        player["actor"].x = lane_to_x(player["start_lane"], PLAYER_ROW_LOCAL, player)

    used_colors = {player["actor"].image for player in players}
    available_colors = [c for c in RACER_COLORS if c not in used_colors]
    ai_lanes = grid[len(players):]
    racer_colors = random.sample(available_colors, k=len(ai_lanes))

    racers = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "target_lane": (lane_i + 0.5) / LANE_COUNT,
            "lane_change_timer": random.randint(LANE_CHANGE_MIN_HOLD,
                                                 LANE_CHANGE_MAX_HOLD),
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
            "state": "racing",
            "freeze_timer": 0,
        }
        for lane_i, color in zip(ai_lanes, racer_colors)
    ]
    for r in racers:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW_LOCAL, players[0]),
                          players[0]["band_top"] + PLAYER_ROW_LOCAL)

def new_race():
    global game_state, race_results
    game_state = "waiting"
    race_results = []
    _new_grid()
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["state"] = "racing"
        player["freeze_timer"] = 0
        player["place"] = None
        player["actor"].y = player["band_top"] + PLAYER_ROW_LOCAL

_apply_menu_choices()
new_race()

### MENU

def on_key_down(key):
    global selected_field, p1_car_index, p2_car_index
    global num_racers, length_index, difficulty_index
    global game_state, countdown_timer

    if game_state != "waiting":
        return

    if key == keys.UP:
        selected_field = (selected_field - 1) % len(MENU_FIELDS)
    elif key == keys.DOWN:
        selected_field = (selected_field + 1) % len(MENU_FIELDS)
    elif key in (keys.LEFT, keys.RIGHT):
        direction = -1 if key == keys.LEFT else 1
        field = MENU_FIELDS[selected_field]
        if field == "P1 Car":
            p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
            if p1_car_index == p2_car_index:
                p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
        elif field == "P2 Car":
            p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
            if p2_car_index == p1_car_index:
                p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
        elif field == "Racers":
            num_racers = max(2, min(MAX_RACERS, num_racers + direction))
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        _apply_menu_choices()
        new_race()
    elif key == keys.SPACE:
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES

### DRAW

def draw():
    screen.fill(DIVIDER)
    for player in players:
        draw_player_band(player)

    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, BAND_HEIGHT - 2, WIDTH, 4), DIVIDER)

    if game_state == "waiting":
        _draw_menu()
    elif game_state == "countdown":
        _draw_countdown()

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
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)

    finish_y_local = row_at(FINISH_DISTANCE, player)
    if -20 < finish_y_local < BAND_HEIGHT:
        finish_y = band_top + finish_y_local
        left = road_center_x(finish_y_local, player) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    for r in racers:
        y_local = row_at(r["distance"], player)
        r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                          player["band_top"] + y_local)
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()

    for other in players:
        if other is player:
            continue
        other_y_local = row_at(other["distance"], player)
        saved_pos = other["actor"].pos
        other["actor"].pos = (lane_to_x(_player_lane(other), other_y_local, player),
                              player["band_top"] + other_y_local)
        if other["state"] != "frozen" or (other["freeze_timer"] // 6) % 2 == 0:
            other["actor"].draw()
        other["actor"].pos = saved_pos

    if player["state"] != "frozen" or (player["freeze_timer"] // 6) % 2 == 0:
        player["actor"].draw()

    screen.draw.text(f"{player['label']}  Speed: {player['speed']:0.1f}",
                     topleft=(10, band_top + 10), fontsize=26, color="white")
    screen.draw.text(f"{int(player['distance'])} / {FINISH_DISTANCE} m",
                     topleft=(10, band_top + 36), fontsize=22, color="white")
    if player["state"] == "frozen":
        screen.draw.text("CRASHED! Recovering...",
                         midtop=(WIDTH // 2, band_top + 10),
                         fontsize=24, color=(255, 90, 60))
    elif player["state"] == "finished":
        title = "YOU WIN!" if player["place"] == 1 else f"YOU FINISHED {_ordinal(player['place'])}!"
        subtitle = ("Press SPACE to race again" if game_state == "won"
                    else "Waiting for the other player...")
        screen.draw.filled_rect(Rect(0, band_top + BAND_HEIGHT // 2 - 50, WIDTH, 100),
                                (0, 0, 0))
        screen.draw.text(title, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 - 15),
                         fontsize=40, color="white")
        screen.draw.text(subtitle, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 + 20),
                         fontsize=20, color="white")

def _draw_menu():
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 160, WIDTH, 320), (0, 0, 0))
    screen.draw.text("READY TO RACE?", center=(WIDTH // 2, HEIGHT // 2 - 130),
                     fontsize=40, color="white")

    values = [
        CAR_CHOICES[p1_car_index].replace("car_", "").title(),
        CAR_CHOICES[p2_car_index].replace("car_", "").title(),
        str(num_racers),
        LENGTH_OPTIONS[length_index][0],
        DIFFICULTY_OPTIONS[difficulty_index][0],
    ]
    line_y = HEIGHT // 2 - 85
    for i, field in enumerate(MENU_FIELDS):
        is_selected = (i == selected_field)
        arrow = "> " if is_selected else "   "
        color = (255, 220, 120) if is_selected else "white"
        text = f"{arrow}{field}: {'< ' if is_selected else ''}{values[i]}{' >' if is_selected else ''}"
        screen.draw.text(text, center=(WIDTH // 2, line_y), fontsize=26, color=color)
        line_y += 30

    screen.draw.text("UP/DOWN choose a setting, LEFT/RIGHT change it, SPACE to start",
                     center=(WIDTH // 2, line_y + 10), fontsize=20, color="white")
    screen.draw.text("P1: Arrow keys      P2: W A S D",
                     center=(WIDTH // 2, line_y + 34), fontsize=20, color="white")

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

def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"

### UPDATE

def update_player(player):
    if player["state"] == "finished":
        return
    if player["state"] == "frozen":
        player["freeze_timer"] -= 1
        if player["freeze_timer"] <= 0:
            player["state"] = "racing"
    else:
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

    if player["state"] == "racing":
        for r in racers:
            y_local = row_at(r["distance"], player)
            r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                              player["band_top"] + y_local)
            if player["actor"].colliderect(r["actor"]):
                player["state"] = "frozen"
                player["freeze_timer"] = FREEZE_FRAMES
                player["speed"] = 0.0
                r["state"] = "frozen"
                r["freeze_timer"] = FREEZE_FRAMES
                player["actor"].x = lane_to_x(player["start_lane"],
                                               PLAYER_ROW_LOCAL, player)
                break

def update_racers():
    for r in racers:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)

            r["lane_change_timer"] -= 1
            if r["lane_change_timer"] <= 0:
                r["target_lane"] = (random.randrange(LANE_COUNT) + 0.5) / LANE_COUNT
                r["lane_change_timer"] = random.randint(LANE_CHANGE_MIN_HOLD,
                                                          LANE_CHANGE_MAX_HOLD)
            if r["lane"] < r["target_lane"]:
                r["lane"] = min(r["target_lane"], r["lane"] + LANE_EASE_SPEED)
            elif r["lane"] > r["target_lane"]:
                r["lane"] = max(r["target_lane"], r["lane"] - LANE_EASE_SPEED)


def _check_player_collision():
    p1, p2 = players
    if p1["state"] != "racing" or p2["state"] != "racing":
        return
    lane_gap = 0.5 / LANE_COUNT
    same_lane = abs(_player_lane(p1) - _player_lane(p2)) < lane_gap
    same_spot = abs(p1["distance"] - p2["distance"]) < PLAYER_COLLISION_DISTANCE
    if same_lane and same_spot:
        for p in players:
            p["state"] = "frozen"
            p["freeze_timer"] = FREEZE_FRAMES
            p["speed"] = 0.0
            p["actor"].x = lane_to_x(p["start_lane"], PLAYER_ROW_LOCAL, p)

def update():
    global game_state, countdown_timer

    if game_state == "waiting":
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

    update_racers()
    for player in players:
        update_player(player)
    _check_player_collision()

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            player["state"] = "finished"
            player["place"] = len(race_results) + 1
            race_results.append(player)

    if all(player["finished"] for player in players):
        game_state = "won"
```
*Expected State: every AI racer visibly drifts between lanes over time. Two
racers can end up sharing a lane and overlapping — nothing happens when they
do, since `check_racer_collisions()` doesn't exist until Step 4.*

Lane-changing and rival-vs-rival crashes are genuinely separate mechanics.
This checkpoint sits right at the seam between them: the drift is fully
working before collisions between racers enter the picture at all.

## Step 4: Racers Noticing Each Other

Add this new function, right after `update_racers()`:

```python
def check_racer_collisions():
    """Now that racers can change lanes, two of them can actually meet.
    This works in absolute track-space (lane + distance), not any one
    player's projected screen pixels - racers only have ONE real position,
    shared by both bands, so that's the space to compare them in.

    A racer that's currently frozen already isn't going anywhere, so it's
    not a NEW collision risk - only racers that are actively moving/lane-
    changing are checked against each other here. (A racer driving through
    an already-stopped one is a known gap - a good "extend this yourself"
    exercise.)"""
    racing = [r for r in racers if r["state"] == "racing"]
    lane_gap = 0.5 / LANE_COUNT
    for i, r1 in enumerate(racing):
        for r2 in racing[i + 1:]:
            same_lane = abs(r1["lane"] - r2["lane"]) < lane_gap
            same_spot = abs(r1["distance"] - r2["distance"]) < RIVAL_COLLISION_DISTANCE
            if same_lane and same_spot:
                if random.random() < RIVAL_CRASH_CHANCE:
                    # Crash! Exactly the same freeze/blink mechanic a
                    # player-vs-racer collision already uses.
                    r1["state"] = "frozen"
                    r1["freeze_timer"] = FREEZE_FRAMES
                    r2["state"] = "frozen"
                    r2["freeze_timer"] = FREEZE_FRAMES
                else:
                    # Swerve to avoid it - re-roll both lane changes right
                    # now instead of finishing the one that's about to
                    # collide.
                    r1["lane_change_timer"] = 0
                    r2["lane_change_timer"] = 0
```
*Expected State: no visible change yet — `check_racer_collisions()` exists
but nothing calls it.*

**Teaching Note:** a racer's screen position depends on which player's band
is looking at it — that's Part 2's whole projection trick. But two racers
either occupy the same real spot on the track or they don't, independent of
who's watching. Comparing `lane` and `distance` directly — not anything
derived from `row_at()` or `lane_to_x()` — checks them in the one space
where "did they meet" actually means something.

**Math Concept:** two details make this pairwise check work.
- `racing[i + 1:]` — everything *after* `r1` in the list — is the standard
  "compare every pair once" pattern. A plain `for r1 in racing: for r2 in
  racing:` would compare every racer to itself (always "the same spot,"
  meaningless) and check every pair twice, once as `(r1, r2)` and again as
  `(r2, r1)`.
- `lane_gap = 0.5 / LANE_COUNT` is half a lane's width, expressed as a
  fraction of the whole road (`1 / LANE_COUNT`). That threshold gets
  tighter automatically on a wider-laned road and looser on a narrower one
  — no magic number like `0.05` to retune if `LANE_COUNT` changes.

**Teaching Note:** a collision here isn't automatic. `random.random() <
RIVAL_CRASH_CHANCE` rolls a fresh number between `0.0` and `1.0` every time
two racers meet, and only crashes if it lands below `0.25`. The other 75% of
the time, both racers abandon their current lane change instead —
`lane_change_timer = 0` forces `update_racers()` to pick a fresh target next
frame — and swerve away. The 25% figure is a judgment call, not a law of
physics.

**Classroom Demo:** set `RIVAL_CRASH_CHANCE` to `1.0` or `0.0` and rerun. At
`1.0` every rival meeting ends in a pile-up; at `0.0` racers always thread
past each other. Neither extreme is "correct" — it's a knob for how chaotic
the race should feel.

Now that `check_racer_collisions()` exists, wire it in. Add one line at the
very end of `update_racers()`, after its loop:
```python
    check_racer_collisions()
```
This is what actually turns the check above into visible behavior — two
racers sharing a lane can now crash or swerve instead of quietly
overlapping.

## Checkpoint: Final Code for Week 5, Part 3

The full script should now match `05_week5_part3_advanced_rivals.py` — AI
racers that drift between lanes over time, and can crash into (or swerve
around) each other, using exactly the same freeze/blink mechanic a
player-vs-racer crash already had.

```python
import random

### MENU OPTIONS

CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RACERS = 5

LENGTH_OPTIONS = [
    ("Short", 3900),
    ("Medium", 7800),
    ("Long", 15600),
]
DIFFICULTY_OPTIONS = [
    ("Easy", (4.0, 6.0)),
    ("Normal", (5.0, 8.5)),
    ("Hard", (7.0, 10.0)),
]
MENU_FIELDS = ["P1 Car", "P2 Car", "Racers", "Length", "Difficulty"]

selected_field = 0
p1_car_index = 0
p2_car_index = 1
num_racers = 4
length_index = 1
difficulty_index = 1

### CONSTANTS

LANE_WIDTH = 110
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
FREEZE_FRAMES = 2 * FPS
PLAYER_COLLISION_DISTANCE = 80

### COLOURS (cars)

RACER_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange",
                "car_pink", "car_silver", "car_white"]

### LANE-CHANGING RIVALS

LANE_CHANGE_MIN_HOLD = FPS * 2
LANE_CHANGE_MAX_HOLD = FPS * 5
LANE_EASE_SPEED = 0.02

### RIVAL-VS-RIVAL CRASHES

RIVAL_COLLISION_DISTANCE = 80
RIVAL_CRASH_CHANCE = 0.25

### WINDOW SIZE

_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120
CENTER = WIDTH // 2

### TRACK

ONE_LAP = [
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
TRACK = ONE_LAP * 4

### COLOURS

GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)
DIVIDER = (20, 20, 20)

### CURRENTLY APPLIED SETTINGS

NUM_RACERS = num_racers
LANE_COUNT = NUM_RACERS
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]

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

def dist_at(y_local, player):
    return player["distance"] + (PLAYER_ROW_LOCAL - y_local)

def row_at(dist, player):
    return PLAYER_ROW_LOCAL - (dist - player["distance"])

### ROAD

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

def lane_to_x(lane, y_local, player):
    return road_left(y_local, player) + lane * ROAD_WIDTH

def _player_lane(player):
    return (player["actor"].x - road_left(PLAYER_ROW_LOCAL, player)) / ROAD_WIDTH

### PLAYERS AND RACERS

def make_player(label, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor("car_red", (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "state": "racing",
        "freeze_timer": 0,
        "place": None,
        "start_lane": 0.0,
        "keys": (key_left, key_right, key_up, key_down),
    }

game_state = "waiting"
countdown_timer = 0

players = [
    make_player("P1", 0, "left", "right", "up", "down"),
    make_player("P2", BAND_HEIGHT, "a", "d", "w", "s"),
]

racers = []

race_results = []

### RACE SETUP

def _apply_menu_choices():
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    players[0]["actor"].image = CAR_CHOICES[p1_car_index]
    players[1]["actor"].image = CAR_CHOICES[p2_car_index]

def _new_grid():
    global racers
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)

    for i, player in enumerate(players):
        player["start_lane"] = (grid[i] + 0.5) / LANE_COUNT
        player["actor"].x = lane_to_x(player["start_lane"], PLAYER_ROW_LOCAL, player)

    used_colors = {player["actor"].image for player in players}
    available_colors = [c for c in RACER_COLORS if c not in used_colors]
    ai_lanes = grid[len(players):]
    racer_colors = random.sample(available_colors, k=len(ai_lanes))

    racers = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "target_lane": (lane_i + 0.5) / LANE_COUNT,
            "lane_change_timer": random.randint(LANE_CHANGE_MIN_HOLD,
                                                 LANE_CHANGE_MAX_HOLD),
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
            "state": "racing",
            "freeze_timer": 0,
        }
        for lane_i, color in zip(ai_lanes, racer_colors)
    ]
    for r in racers:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW_LOCAL, players[0]),
                          players[0]["band_top"] + PLAYER_ROW_LOCAL)

def new_race():
    global game_state, race_results
    game_state = "waiting"
    race_results = []
    _new_grid()
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["state"] = "racing"
        player["freeze_timer"] = 0
        player["place"] = None
        player["actor"].y = player["band_top"] + PLAYER_ROW_LOCAL

_apply_menu_choices()
new_race()

### MENU

def on_key_down(key):
    global selected_field, p1_car_index, p2_car_index
    global num_racers, length_index, difficulty_index
    global game_state, countdown_timer

    if game_state != "waiting":
        return

    if key == keys.UP:
        selected_field = (selected_field - 1) % len(MENU_FIELDS)
    elif key == keys.DOWN:
        selected_field = (selected_field + 1) % len(MENU_FIELDS)
    elif key in (keys.LEFT, keys.RIGHT):
        direction = -1 if key == keys.LEFT else 1
        field = MENU_FIELDS[selected_field]
        if field == "P1 Car":
            p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
            if p1_car_index == p2_car_index:
                p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
        elif field == "P2 Car":
            p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
            if p2_car_index == p1_car_index:
                p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
        elif field == "Racers":
            num_racers = max(2, min(MAX_RACERS, num_racers + direction))
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        _apply_menu_choices()
        new_race()
    elif key == keys.SPACE:
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES

### DRAW

def draw():
    screen.fill(DIVIDER)
    for player in players:
        draw_player_band(player)

    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, BAND_HEIGHT - 2, WIDTH, 4), DIVIDER)

    if game_state == "waiting":
        _draw_menu()
    elif game_state == "countdown":
        _draw_countdown()

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
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)

    finish_y_local = row_at(FINISH_DISTANCE, player)
    if -20 < finish_y_local < BAND_HEIGHT:
        finish_y = band_top + finish_y_local
        left = road_center_x(finish_y_local, player) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    for r in racers:
        y_local = row_at(r["distance"], player)
        r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                          player["band_top"] + y_local)
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()

    for other in players:
        if other is player:
            continue
        other_y_local = row_at(other["distance"], player)
        saved_pos = other["actor"].pos
        other["actor"].pos = (lane_to_x(_player_lane(other), other_y_local, player),
                              player["band_top"] + other_y_local)
        if other["state"] != "frozen" or (other["freeze_timer"] // 6) % 2 == 0:
            other["actor"].draw()
        other["actor"].pos = saved_pos

    if player["state"] != "frozen" or (player["freeze_timer"] // 6) % 2 == 0:
        player["actor"].draw()

    screen.draw.text(f"{player['label']}  Speed: {player['speed']:0.1f}",
                     topleft=(10, band_top + 10), fontsize=26, color="white")
    screen.draw.text(f"{int(player['distance'])} / {FINISH_DISTANCE} m",
                     topleft=(10, band_top + 36), fontsize=22, color="white")
    if player["state"] == "frozen":
        screen.draw.text("CRASHED! Recovering...",
                         midtop=(WIDTH // 2, band_top + 10),
                         fontsize=24, color=(255, 90, 60))
    elif player["state"] == "finished":
        title = "YOU WIN!" if player["place"] == 1 else f"YOU FINISHED {_ordinal(player['place'])}!"
        subtitle = ("Press SPACE to race again" if game_state == "won"
                    else "Waiting for the other player...")
        screen.draw.filled_rect(Rect(0, band_top + BAND_HEIGHT // 2 - 50, WIDTH, 100),
                                (0, 0, 0))
        screen.draw.text(title, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 - 15),
                         fontsize=40, color="white")
        screen.draw.text(subtitle, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 + 20),
                         fontsize=20, color="white")

def _draw_menu():
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 160, WIDTH, 320), (0, 0, 0))
    screen.draw.text("READY TO RACE?", center=(WIDTH // 2, HEIGHT // 2 - 130),
                     fontsize=40, color="white")

    values = [
        CAR_CHOICES[p1_car_index].replace("car_", "").title(),
        CAR_CHOICES[p2_car_index].replace("car_", "").title(),
        str(num_racers),
        LENGTH_OPTIONS[length_index][0],
        DIFFICULTY_OPTIONS[difficulty_index][0],
    ]
    line_y = HEIGHT // 2 - 85
    for i, field in enumerate(MENU_FIELDS):
        is_selected = (i == selected_field)
        arrow = "> " if is_selected else "   "
        color = (255, 220, 120) if is_selected else "white"
        text = f"{arrow}{field}: {'< ' if is_selected else ''}{values[i]}{' >' if is_selected else ''}"
        screen.draw.text(text, center=(WIDTH // 2, line_y), fontsize=26, color=color)
        line_y += 30

    screen.draw.text("UP/DOWN choose a setting, LEFT/RIGHT change it, SPACE to start",
                     center=(WIDTH // 2, line_y + 10), fontsize=20, color="white")
    screen.draw.text("P1: Arrow keys      P2: W A S D",
                     center=(WIDTH // 2, line_y + 34), fontsize=20, color="white")

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

def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"

### UPDATE

def update_player(player):
    if player["state"] == "finished":
        return
    if player["state"] == "frozen":
        player["freeze_timer"] -= 1
        if player["freeze_timer"] <= 0:
            player["state"] = "racing"
    else:
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

    if player["state"] == "racing":
        for r in racers:
            y_local = row_at(r["distance"], player)
            r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                              player["band_top"] + y_local)
            if player["actor"].colliderect(r["actor"]):
                player["state"] = "frozen"
                player["freeze_timer"] = FREEZE_FRAMES
                player["speed"] = 0.0
                r["state"] = "frozen"
                r["freeze_timer"] = FREEZE_FRAMES
                player["actor"].x = lane_to_x(player["start_lane"],
                                               PLAYER_ROW_LOCAL, player)
                break

def update_racers():
    for r in racers:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)

            r["lane_change_timer"] -= 1
            if r["lane_change_timer"] <= 0:
                r["target_lane"] = (random.randrange(LANE_COUNT) + 0.5) / LANE_COUNT
                r["lane_change_timer"] = random.randint(LANE_CHANGE_MIN_HOLD,
                                                          LANE_CHANGE_MAX_HOLD)
            if r["lane"] < r["target_lane"]:
                r["lane"] = min(r["target_lane"], r["lane"] + LANE_EASE_SPEED)
            elif r["lane"] > r["target_lane"]:
                r["lane"] = max(r["target_lane"], r["lane"] - LANE_EASE_SPEED)

    check_racer_collisions()

def check_racer_collisions():
    racing = [r for r in racers if r["state"] == "racing"]
    lane_gap = 0.5 / LANE_COUNT
    for i, r1 in enumerate(racing):
        for r2 in racing[i + 1:]:
            same_lane = abs(r1["lane"] - r2["lane"]) < lane_gap
            same_spot = abs(r1["distance"] - r2["distance"]) < RIVAL_COLLISION_DISTANCE
            if same_lane and same_spot:
                if random.random() < RIVAL_CRASH_CHANCE:
                    r1["state"] = "frozen"
                    r1["freeze_timer"] = FREEZE_FRAMES
                    r2["state"] = "frozen"
                    r2["freeze_timer"] = FREEZE_FRAMES
                else:
                    r1["lane_change_timer"] = 0
                    r2["lane_change_timer"] = 0

def _check_player_collision():
    p1, p2 = players
    if p1["state"] != "racing" or p2["state"] != "racing":
        return
    lane_gap = 0.5 / LANE_COUNT
    same_lane = abs(_player_lane(p1) - _player_lane(p2)) < lane_gap
    same_spot = abs(p1["distance"] - p2["distance"]) < PLAYER_COLLISION_DISTANCE
    if same_lane and same_spot:
        for p in players:
            p["state"] = "frozen"
            p["freeze_timer"] = FREEZE_FRAMES
            p["speed"] = 0.0
            p["actor"].x = lane_to_x(p["start_lane"], PLAYER_ROW_LOCAL, p)

def update():
    global game_state, countdown_timer

    if game_state == "waiting":
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

    update_racers()
    for player in players:
        update_player(player)
    _check_player_collision()

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            player["state"] = "finished"
            player["place"] = len(race_results) + 1
            race_results.append(player)

    if all(player["finished"] for player in players):
        game_state = "won"
```
*Expected State: AI racers drift between lanes over time, and can crash into
(or swerve around) each other using the same freeze/blink mechanic a
player-vs-racer crash already had.*

**Watch for:** the collision check only compares two *actively moving*
racers to each other — a racer that's mid-lane-change can still drive
straight through one that's already frozen and stopped. Rear-ending a
stopped car isn't handled; that's a good "extend this yourself" prompt for
strong students who finish early.
