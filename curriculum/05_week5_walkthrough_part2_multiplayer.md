# Week 5, Part 2 Walkthrough — Multiplayer, Built on Part 1's Menu

Builds directly on Part 1's settings menu, adding a second human player:
Player 1 (arrow keys) and Player 2 (W/A/S/D), each with their own stacked
half of the window. Both players race the exact same race — the same AI
racers, at the same positions, crashing and recovering the same way no
matter which band you're watching them from — not two similar-looking but
independent races.

**Concept: extending beats inventing.** If Part 1 made sense, this file has
very few genuinely new ideas. It's mostly "give the player dict a sibling,
and run everything twice." A racer was already a dict, and the single
player's state was heading the same direction — so adding a second human
player is mostly copy-and-connect work, not new invention. Good design
decisions (a dict per racer, settings as data) show their value here:
extending a feature is cheap because the shape was already right.

## Starting Code for Week 5, Part 2

Start from the Week 5, Part 1 checkpoint (`05_week5_part1_menu.py`).
```python
import random

### MENU OPTIONS

CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RACERS = 7

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

MENU_FIELDS = ["Car", "Racers", "Length", "Difficulty"]

selected_field = 0
car_index = 0
num_racers = 4
length_index = 1
difficulty_index = 1

### CONSTANTS

LANE_WIDTH = 110
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

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3
FREEZE_FRAMES = 2 * FPS

### WINDOW SIZE

_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600
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

### GAME STATE

NUM_RACERS = num_racers
LANE_COUNT = NUM_RACERS
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]

player = Actor(CAR_CHOICES[car_index], (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
racers = []
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

def _apply_menu_choices():
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    player.image = CAR_CHOICES[car_index]

def new_race():
    global player_speed, distance_traveled, racers, game_state, player_start_lane
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

    available_colors = [c for c in CAR_CHOICES if c != CAR_CHOICES[car_index]]
    racer_colors = random.sample(available_colors, k=len(grid) - 1)
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
        for lane_i, color in zip(grid[1:], racer_colors)
    ]
    for r in racers:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)

new_race()

### MENU

def on_key_down(key):
    global selected_field, num_racers, car_index, length_index, difficulty_index
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
        if field == "Car":
            car_index = (car_index + direction) % len(CAR_CHOICES)
        elif field == "Racers":
            num_racers = max(1, min(MAX_RACERS, num_racers + direction))
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        _apply_menu_choices()
        new_race()
    elif key == keys.SPACE:
        # Starts the race with whatever grid is already on screen - every
        # LEFT/RIGHT edit already rebuilt it to match the current menu settings.
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES

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

    for r in racers:
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
        _draw_menu()
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")

def _draw_menu():
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 130, WIDTH, 260), (0, 0, 0))
    screen.draw.text("READY TO RACE?", center=(WIDTH // 2, HEIGHT // 2 - 100),
                     fontsize=44, color="white")

    values = [
        CAR_CHOICES[car_index].replace("car_", "").title(),
        str(num_racers),
        LENGTH_OPTIONS[length_index][0],
        DIFFICULTY_OPTIONS[difficulty_index][0],
    ]
    line_y = HEIGHT // 2 - 55
    for i, field in enumerate(MENU_FIELDS):
        is_selected = (i == selected_field)
        arrow = "> " if is_selected else "   "
        color = (255, 220, 120) if is_selected else "white"
        text = f"{arrow}{field}: {'< ' if is_selected else ''}{values[i]}{' >' if is_selected else ''}"
        screen.draw.text(text, center=(WIDTH // 2, line_y), fontsize=28, color=color)
        line_y += 32

    screen.draw.text("UP/DOWN choose a setting, LEFT/RIGHT change it, SPACE to start",
                     center=(WIDTH // 2, line_y + 10), fontsize=22, color="white")

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

    for r in racers:
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
        for r in racers:
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
*Expected State: running this file plays exactly like the Week 5, Part 1
checkpoint — one player, one band, a settings menu. Nothing here is new
yet.*

**Teaching Note:** this is Part 1's final checkpoint, unchanged. Every step
from here modifies this same code — nothing gets rewritten from scratch.

## Step 1: A Second Car Choice in the Menu

Update the menu constants: a smaller `MAX_RACERS` (two bands now share the
lane budget), a `P2 Car` field, and two car-index variables instead of one:

```python
MAX_RACERS = 5      # total cars on track at once, players included - kept
                    # smaller than Part 1's menu since there are two bands
                    # to fit racers into now, not just one
```
```python
MENU_FIELDS = ["P1 Car", "P2 Car", "Racers", "Length", "Difficulty"]

selected_field = 0
p1_car_index = 0
p2_car_index = 1
num_racers = 4       # total cars, including both players - so this is
                     # 2 AI racers by default
length_index = 1
difficulty_index = 1
```

Pull the AI's color palette out into its own constant too. Part 1 picked AI
colors inline, straight out of `CAR_CHOICES`. Now that *two* colors need
excluding (one per player) instead of one, a curated list is simpler —
`RACER_COLORS` already leaves out `"car_red"` (reserved as the default
player car color), so there's one less color to exclude by hand later:
```python
RACER_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange",
                "car_pink", "car_silver", "car_white"]
```
*Expected State: the file no longer runs on its own — `car_index` no longer
exists, but `player = Actor(CAR_CHOICES[car_index], ...)` and
`_apply_menu_choices()` still reference it. That's expected; Step 6 finishes
reconnecting the menu to both car fields.*

**Teaching Note:** `RACER_COLORS` is a separate list, not a filtered copy of
`CAR_CHOICES` computed at runtime. Excluding both players' current colors
happens once per race, inside `_new_grid()` (Step 5) — keeping a curated
starting list here just means that filtering step has less work to do, and
`"car_red"` never needs excluding by hand.

## Step 2: A Window Split Into Two Stacked Bands

Replace the window-size block:

```python
# --- Window size: fixed for the largest possible race (see Part 1) -------
_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120
CENTER = WIDTH // 2
```

And add a colour for the divider between the two bands:
```python
DIVIDER = (20, 20, 20)
```
*Expected State: still not runnable, for the same reason as Step 1 — this
step only reworks the window-size math and adds a color.*

**The Geometry:** each player's car sits at a fixed row *within their own
band* — `BAND_HEIGHT - 120` pixels down from wherever that band starts, not
from the top of the whole window. That's what `PLAYER_ROW_LOCAL` names: a
row relative to a band, not an absolute screen row. `HEIGHT = BAND_HEIGHT *
2` makes the window exactly tall enough for both bands stacked on top of
each other.

## Step 3: Every Formula Now Takes a `player`

This step touches almost every function already built. `dist_at`, `row_at`,
`road_center_x`, `road_left`, `road_right`, `on_road`, `on_shoulder`, and
`lane_to_x` all gain a `player` parameter, and read that player's own
distance instead of one shared global:

```python
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


def lane_to_x(lane, y_local, player):
    return road_left(y_local, player) + lane * ROAD_WIDTH
```
*Expected State: still not runnable — every function above now also
requires a `player` argument that nothing passes in yet.*

**Teaching Note:** these are the exact same formulas from every earlier
week — `dist_at(y) = distance_traveled + (PLAYER_ROW - y)` becomes
`dist_at(y_local, player) = player["distance"] + (PLAYER_ROW_LOCAL -
y_local)`. The only change is *whose* distance gets read. This refactor is
mechanical because the game's state already lived in a dictionary for every
rival, all the way back in Week 2 — extending that same shape to a second
human player is barely a new idea, just a new use of an old one.

## Step 4: A Dictionary Per Player

Replace the plain `player = Actor(...)` / `player_speed` / `distance_traveled`
globals entirely with a builder function and a list:

```python
def make_player(label, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor("car_red", (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "state": "racing",       # "racing" | "frozen" (per-player, not global)
        "freeze_timer": 0,
        "start_lane": 0.0,        # this player's lane on the starting grid
        "keys": (key_left, key_right, key_up, key_down),
    }


game_state = "waiting"          # "waiting"|"countdown"|"racing"|"won"
countdown_timer = 0
winner_label = None

players = [
    make_player("P1", 0, "left", "right", "up", "down"),
    make_player("P2", BAND_HEIGHT, "a", "d", "w", "s"),
]
```
*Expected State: still not runnable — `draw()` and `update()` still
reference the old `player`/`player_speed`/`distance_traveled` globals, which
no longer exist.*

**Teaching Note:**
- `"keys"` stores key names as strings (`"left"`, `"a"`), not
  `keyboard.left` directly. `keyboard` is an object where `keyboard.left`
  and `keyboard.a` are both valid attributes, but there's no normal
  dot-notation way to pick *which* attribute to check from a variable.
  Storing the name as a string and looking it up with `getattr(keyboard,
  name)` (Step 8) is what lets one function serve both players with
  different key bindings.
- `game_state` is also much smaller now — just `"waiting"`, `"countdown"`,
  `"racing"`, `"won"`. There's no shared `"frozen"` state anymore, because
  freezing is now per-player (each player's own `"state"` field), not a
  whole-race thing.

## Step 5: One Shared List of AI Racers

Add a shared `racers` list, and a function that builds one starting grid for
*everyone* — both players and every AI racer, out of a single shuffle:

```python
# The AI racers, shared by both players - there is exactly ONE of these
# lists for the whole race, not one per player. Both bands look at the same
# racers; they just each project them onto their own half of the screen
# (see update_racers, draw_player_band and the collision check below).
racers = []


def _new_grid():
    """Build ONE starting grid for the whole race: both players and every
    AI racer each get a different lane out of the same shuffle, so it's
    genuinely one shared race, not two independent-but-similar ones."""
    global racers
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)

    for i, player in enumerate(players):
        player["start_lane"] = (grid[i] + 0.5) / LANE_COUNT
        player["actor"].x = lane_to_x(player["start_lane"], PLAYER_ROW_LOCAL, player)

    # Give every racer a different color, and skip whatever colors the two
    # players are currently using - random.sample() picks from RACER_COLORS
    # without repeats, unlike calling random.choice() once per racer.
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
            "state": "racing",       # "racing" | "frozen" - mirrors a player's own
            "freeze_timer": 0,
        }
        for lane_i, color in zip(ai_lanes, racer_colors)
    ]
    for r in racers:
        # Any player's band works fine for this initial placement - every
        # player starts at distance 0, so the projection is identical for
        # both right now. It'll be recomputed per-band every frame anyway.
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW_LOCAL, players[0]),
                          players[0]["band_top"] + PLAYER_ROW_LOCAL)


def new_race():
    global game_state, winner_label
    game_state = "waiting"
    winner_label = None
    _new_grid()
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["state"] = "racing"
        player["freeze_timer"] = 0
        player["actor"].y = player["band_top"] + PLAYER_ROW_LOCAL


_apply_menu_choices()   # both players start with car_red from make_player() -
new_race()              # this sets each one's REAL starting car before the first draw
```
*Expected State: still not runnable — `draw()` and `update()` don't know
about the `players` list or the shared `racers` list yet.*

**Teaching Note:** `make_player()` always creates both actors with
`"car_red"` as a placeholder image. The extra `_apply_menu_choices()` call
at the bottom sets each one to its *actual* chosen car
(`CAR_CHOICES[p1_car_index]` / `CAR_CHOICES[p2_car_index]`) even if a player
never touches LEFT/RIGHT and accepts the defaults — `on_key_down()`'s own
call to `_apply_menu_choices()` never fires in that case, so without this
extra call both cars would show up red regardless of `p2_car_index`.

**Teaching Note:** `grid[i]` for `enumerate(players)`, and
`grid[len(players):]` for AI, is Week 3's starting-grid trick generalized.
Instead of always reserving `grid[0]` for one player, the first
`len(players)` slots (2, here) go to the players in order, and everything
left over goes to AI racers. The player count is no longer hard-coded as 1.

## Step 6: The Menu Handles Two Car Fields

Update `_apply_menu_choices()` to set both players' images:
```python
def _apply_menu_choices():
    """Copy the menu's current picks into the actual game settings - the
    same idea as Part 1's _apply_menu_choices(), just also touching each
    player's chosen car image."""
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    players[0]["actor"].image = CAR_CHOICES[p1_car_index]
    players[1]["actor"].image = CAR_CHOICES[p2_car_index]
```

And `on_key_down()` gains a branch for each car field (same shape as Part
1's single `"Car"` field, just split in two), plus a floor of `2` racers
instead of `1` (there are always two human players sharing that total):
```python
        if field == "P1 Car":
            p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
            if p1_car_index == p2_car_index:
                # Skip straight past whatever P2 is already driving, in the
                # same direction, instead of landing on it.
                p1_car_index = (p1_car_index + direction) % len(CAR_CHOICES)
        elif field == "P2 Car":
            p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
            if p2_car_index == p1_car_index:
                p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
        elif field == "Racers":
            # Never fewer than 2 - there are always 2 human players sharing
            # this total.
            num_racers = max(2, min(MAX_RACERS, num_racers + direction))
```
(`Length` and `Difficulty` are unchanged from Part 1.) Remember to add
`p1_car_index` and `p2_car_index` to the `global` line at the top of
`on_key_down()`, in place of the old single `car_index`.
*Expected State: still not runnable on its own — the Mid-Session Checkpoint
just ahead is the first point where `draw()` and `update()` catch up and the
game runs again.*

**Teaching Note:** skipping past a taken color, instead of just refusing the
move, matters for feel. Leaving `p1_car_index` unchanged when it would land
on P2's car makes LEFT/RIGHT silently do nothing at that one spot — it reads
as a bug, not a rule. Skipping past means every press always moves the
selection; it just never lands on a car the other player already has. Since
P1 and P2 start on two different cars (`p1_car_index = 0`, `p2_car_index =
1`), this only ever fires when a player's own edit would create a clash.

## Mid-Session Checkpoint: The Data Model Is Two Players Deep, Nothing Draws It Yet

Steps 1-6 replace the entire data model — one global player and rival list
becomes `players` and a shared `racers` list — in one connected block, which
leaves nothing runnable in between: the old single-player `draw()`/
`update()` still expect globals that no longer exist. This checkpoint
borrows `draw()`/`draw_player_band()` from Step 7, `update_player()`/
`update_racers()`/`update()` from Step 8, the other-player visibility and
collision code from Step 9, and the per-player finish/placement code from
Step 10, purely to keep the game playable (and fully finishable by both
players) at this halfway point. Steps 7-10 below explain this same code,
piece by piece. At this stage, the full Python script should look something
like this:

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
*Expected State: the game is fully playable again — a two-player menu, both
bands visible, shared AI racers, collisions, and per-player finish placement
all work, even though Steps 7-10 haven't "explained" any of it yet.*

Run it and this already plays like the finished file — a real two-player
menu, split-screen bands, shared AI racers, all of it. Steps 7-10 don't add
new behavior from here; they walk through the code above one piece at a
time, explaining `set_clip` for the band split and the split between
per-player and shared updates. Read them as commentary on this code, not as
new code to type.

## Step 7: Drawing Two Bands With `set_clip`

Replace `draw()` with a loop over both players:
```python
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
    elif game_state == "won":
        _banner(f"{winner_label} WINS!", "Press SPACE to race again")
```

And write `draw_player_band()`, based on your existing `draw()` from Part 1
but reading from `player`:
```python
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
        # Every racer is shared, but its screen spot depends on which
        # band is looking at it - recompute that here, for THIS player,
        # right before drawing it (same set-then-use pattern as everywhere
        # else in this file).
        y_local = row_at(r["distance"], player)
        r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                          player["band_top"] + y_local)
        # Blink a frozen racer too, the same way the player blinks below.
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()
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
```
*Expected State: identical on screen to the Mid-Session Checkpoint — this
step only explains code already in place, it doesn't change behavior.*

**Teaching Note:** `screen.surface.set_clip(rect)` tells Pygame Zero to only
actually paint pixels inside that rectangle, and ignore anything drawn
outside it. `draw_player_band()` doesn't know or care that it's being
clipped — it just draws a whole player's world normally, starting from
`band_top`. Calling it once with the clip set to the top half, then again
with the clip set to the bottom half, produces two independent-looking views
from one drawing function. `set_clip(None)` (used in `draw()`, and inside
`_banner`) turns clipping back off, so full-window elements like the divider
bar and banners aren't accidentally cut in half.

**The Concept:** each racer in the `for r in racers` loop gets its screen
position recomputed once per band, using *that* player's own `row_at()`/
`lane_to_x()`. The racer has exactly one real position (its `distance` and
`lane`), but it gets projected onto two different bands, once per
`draw_player_band()` call — the same shared car shows up in a different spot
in each half of the screen, because each half measures distance relative to
a different player.

**Classroom Demo:** comment out the `screen.surface.set_clip(Rect(...))`
line at the top of `draw_player_band()` and run it — both players' roads
bleed across the whole window instead of staying confined to their own
half, which makes the point about what clipping actually buys you land
fast.

## Step 8: Splitting `update()` Into "Per-Player" and "Shared"

Add `update_player(player)` — nearly identical to Part 1's `update()`
driving logic, but reading and writing `player[...]` instead of globals, and
using `getattr` for the keys:

```python
def update_player(player):
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
        # A crash freezes this player instead of ending their run - and now
        # freezes the racer they hit too, for the same length of time. This
        # racer is shared, so freezing it here also freezes it (and makes
        # it blink) in the OTHER player's band, on the same frame.
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
```

**The Concept:** `getattr(keyboard, key_left)` replaces `keyboard.left`
because `key_left` is a string stored in the player's own dict (`"left"`
for Player 1, `"a"` for Player 2) — `keyboard.key_left` would make Python
look for a literal attribute named `key_left`, which doesn't exist.
`getattr(object, name_as_string)` is the tool for looking up an attribute
whose name is only known as a string. This one line is what lets
`update_player()` serve both players with completely different keys.

Then add `update_racers()`, which moves every AI racer **exactly once per
frame**, not once per player:

```python
def update_racers():
    """Advance the shared racers exactly once per frame - not once per
    player. A racer that's frozen (because it just collided with a player,
    in EITHER band) sits out its own timer, the same shape as a player's
    own "frozen" state."""
    for r in racers:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        # Not "elif" - a racer that JUST switched back to "racing" above
        # still needs its distance updated this same frame. Otherwise it
        # would stay at its old, overlapping distance for one more frame
        # and immediately collide with a player again the instant they
        # both wake up, freezing them again.
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
```

**Teaching Note:** advancing a racer's `distance` can't live inside
`update_player()`. If it did, every racer would move twice as fast in a
2-player race as it would solo — its distance would grow once during P1's
update, then again during P2's. Racers are shared state, so they get
exactly one update per frame, called once, separate from the per-player
loop.

Finally, `update()` itself becomes a short coordinator:
```python
def update():
    global game_state, countdown_timer, winner_label

    if game_state == "waiting":
        return   # the menu is driven entirely by on_key_down()

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

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            winner_label = player["label"]
            game_state = "won"
            break
```
*Expected State: identical on screen to the Mid-Session Checkpoint — still
explaining existing code, no behavior change.*

**Teaching Note:** racers update before the players' loop. This doesn't
strictly matter for correctness here, but it reads naturally as "move the
shared world first, then let each player react to it" — and it means both
players' collision checks in the same frame see racers at their
already-updated positions, rather than one player seeing this frame's
positions and the other seeing last frame's.

## Step 9: Seeing (and Crashing Into) the Other Player

Right now `draw_player_band()` draws the shared `racers` — projected fresh
into whichever band is currently drawing — but it only ever draws
`player["actor"]` for the *one* player that band belongs to. The other
human player is never drawn at all, in either band, and there's no way for
the two players to collide with each other either. This step fixes both.

Add this new constant near `FREEZE_FRAMES`:
```python
PLAYER_COLLISION_DISTANCE = 80    # "same spot" = within roughly a car length
```

And this new helper, right after `lane_to_x()`:
```python
def _player_lane(player):
    """This player's current lane, as a fraction of the road (0.0-1.0) -
    computed from their actor's x the same way a racer's stored "lane"
    already works, so it's meaningful to compare across two different
    players' bands even though each band's road curves differently."""
    return (player["actor"].x - road_left(PLAYER_ROW_LOCAL, player)) / ROAD_WIDTH
```

**Teaching Note:** a racer stores `"lane"` directly — one fraction,
meaningful in any band. A player doesn't have that field; they just have a
raw pixel `x`, last set inside their own band. `_player_lane()` derives the
same kind of band-independent fraction on the fly from that `x`, so it can
be compared against a *different* player's lane even though the two
players' roads curve differently (each one curves relative to that player's
own distance).

In `draw_player_band()`, add this right after the `racers` loop, before
`player["actor"].draw()`:
```python
    for other in players:
        if other is player:
            continue
        # The other player's actor.pos is their REAL position, used by
        # their own update_player() next frame - project a ghost of it
        # into THIS band, draw it, then put it right back, so nothing
        # about their real position survives this band's draw call.
        other_y_local = row_at(other["distance"], player)
        saved_pos = other["actor"].pos
        other["actor"].pos = (lane_to_x(_player_lane(other), other_y_local, player),
                              player["band_top"] + other_y_local)
        if other["state"] != "frozen" or (other["freeze_timer"] // 6) % 2 == 0:
            other["actor"].draw()
        other["actor"].pos = saved_pos
```

**Teaching Note:** a racer's `.pos` is disposable — nothing depends on its
value between draws, so overwriting it fresh every band is fine. A player's
`.pos` is not disposable: it's the exact value `update_player()` reads and
steers from next frame. Save the real position before the ghost-draw and
restore it immediately after, and the ghost stays purely visual — nothing
about either player's real state gets touched.

**Classroom Demo:** delete the `other["actor"].pos = saved_pos` restore
line and run a two-player race. Watch Player 2 visibly "teleport" toward
wherever Player 1's band last drew their ghost — a clean demonstration of
why the save/restore matters, not just a defensive habit.

Now add the collision check itself, anywhere near `update_racers()`:
```python
def _check_player_collision():
    """Freeze both players if they're in the same lane at the same spot -
    compared directly in track-space (lane fraction + distance), not with
    colliderect(). Unlike a racer, a player's actor.pos is their REAL
    position for steering, so this avoids projecting one player into the
    other's band just to check a collision."""
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
            # Snap back to each player's own starting-grid lane, same
            # reasoning as a player-vs-racer collision: guarantees they
            # separate instead of drifting straight back into each other
            # the instant they unfreeze.
            p["actor"].x = lane_to_x(p["start_lane"], PLAYER_ROW_LOCAL, p)
```

**Math Concept:** a player-vs-racer check can use `colliderect()` because
the racer's position has already been freshly projected into that exact
player's band, right there in `update_player()`, a moment earlier. Checking
player-vs-player would need one player's actor temporarily projected into
the other's band first — the same ghost-position trick `draw_player_band()`
just used, but for a collision check instead of a draw. Comparing
`_player_lane()` and `["distance"]` directly sidesteps that: it's a plain
track-space comparison, no position mutation needed.

Finally, call it once per frame from `update()`, right after the per-player
loop:
```python
    update_racers()
    for player in players:
        update_player(player)
    _check_player_collision()
```
*Expected State: both players' cars are now visible in both bands, and
driving into the other player freezes both of them, exactly like a
player-vs-racer crash.*

**Classroom Prompt (For Fast Finishers):** `PLAYER_COLLISION_DISTANCE` is
set to 80. Ask early finishers to predict what happens to head-on passing at
high speed if that number were doubled, or cut in half — would players
"phase through" each other more or less often?

## Step 10: Each Player Gets Their Own Finish

Right now the race ends the INSTANT one player crosses the finish line —
`game_state` jumps straight to `"won"`, which makes `update()` return early
and freezes the other player mid-race, whether they've finished or not.
This step makes the race wait for both players, and gives each one their
own placement banner, the same idea as the single-player "YOU FINISHED
Nth!" screen from Week 3.

Add a `"place"` field to each player, and a shared `race_results` list —
right after `racers = []`:
```python
"place": None,            # this player's finishing place, once "finished"
```
```python
# Every racer AND every player, in the order they cross the finish line -
# this is what turns "did I finish" into "what PLACE did I finish," for
# both players, the same way race_results already worked in single-player.
race_results = []
```

**Teaching Note:** one shared list works for both racers and players
because placement only means something relative to *everyone* in the race,
not just the other human player. If an AI racer finishes between the two
players, that counts — Player 2 finishing after one AI racer crosses is
genuinely "2nd," not "1st," even though no other *player* beat them. One
list, appended to by whoever crosses the line — AI or human — in the order
it actually happens, keeps that count correct automatically: `len(
race_results) + 1` is always "how many finished before me."

Update `new_race()` to reset it (and each player's `place`) alongside
everything else:
```python
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
```

In `update_racers()`, append a racer to `race_results` the moment it
finishes:
```python
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)
```

Give `update_player()` a new short-circuit at the very top, the same shape
as the existing `"frozen"` check — a finished player has nothing left to
update:
```python
def update_player(player):
    if player["state"] == "finished":
        return   # this player's race is over - nothing left to update
    if player["state"] == "frozen":
```

**Teaching Note:** `"finished"` needs to be a real state, not just the
existing `player["finished"]` boolean. The boolean already exists — it's
what the finish-line check tests — but `update_player()` doesn't look at
it; it only branches on `player["state"]` (`"frozen"` vs. everything else,
which falls into the movement code). Without a `"finished"` state to check,
a player who already crossed the line would keep steering and accelerating
every frame after finishing, same as any other frame.

Now replace the finish-line check in `update()` — instead of declaring an
immediate winner, each player gets their own place, and the race only ends
once **everyone** has one:
```python
    # Each player gets their OWN place, the moment THEY cross - the race
    # keeps going for whoever hasn't finished yet, instead of ending the
    # instant the first player crosses the line.
    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            player["state"] = "finished"
            player["place"] = len(race_results) + 1
            race_results.append(player)

    # Only once EVERY player has finished does the race actually end.
    if all(player["finished"] for player in players):
        game_state = "won"
```

Also remove `winner_label` entirely — it's no longer needed anywhere
(`global game_state, countdown_timer` is all `update()` needs now), since
each band shows its own result instead of one shared announcement.

Add the same `_ordinal()` helper single-player used since Week 3, right
after `_banner()`:
```python
def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"
```

Finally, replace `draw()`'s old whole-window `"won"` banner (delete the
`elif game_state == "won": _banner(...)` line — it's dead code now, nothing
sets `winner_label` anymore) with a per-band banner in `draw_player_band()`,
right after the existing `"CRASHED! Recovering..."` check:
```python
    elif player["state"] == "finished":
        # This player's own band gets its own placement banner - the race
        # isn't over globally until BOTH players have one of these.
        title = "YOU WIN!" if player["place"] == 1 else f"YOU FINISHED {_ordinal(player['place'])}!"
        subtitle = ("Press SPACE to race again" if game_state == "won"
                    else "Waiting for the other player...")
        screen.draw.filled_rect(Rect(0, band_top + BAND_HEIGHT // 2 - 50, WIDTH, 100),
                                (0, 0, 0))
        screen.draw.text(title, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 - 15),
                         fontsize=40, color="white")
        screen.draw.text(subtitle, center=(WIDTH // 2, band_top + BAND_HEIGHT // 2 + 20),
                         fontsize=20, color="white")
```

**Teaching Note:** this banner lives inside `draw_player_band()`, not
`draw()`, because finishing isn't a whole-race state anymore. Every earlier
full-window banner (`"waiting"`, `"countdown"`) genuinely is one — nothing
else is happening, so covering the whole screen makes sense. One player can
now be celebrating while the other is still mid-turn. Drawing this banner
from inside the already-clipped `draw_player_band()` call keeps it confined
to that one player's own band, exactly like the "CRASHED! Recovering..."
text right above it.

*Expected State: the race continues for whoever hasn't finished — the first
player to cross sees their own placement banner immediately ("YOU WIN!" or
"YOU FINISHED 2ND!") and a "Waiting for the other player..." subtitle,
while the other band keeps racing normally. Only once both players have
finished does the subtitle switch to "Press SPACE to race again" and
`game_state` becomes `"won"`.*

## Checkpoint: Final Code for Week 5, Part 2

The full script should now match `05_week5_part2_multiplayer.py` — two human
players, stacked, racing the same shared field of AI racers.

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
*Expected State: two-player split-screen racing, shared AI field, per-player
crashes and finishes, matching the `.py` checkpoint exactly.*

**Watch for:** ties on the finish line aren't broken by whoever is truly
ahead by a pixel — they're broken by list order. If both players cross on
the exact same frame, the finish-check loop processes P1 first: P1's
`place` gets set and appended to `race_results` before P2 is even checked,
so P2's `len(race_results) + 1` already counts P1 as ahead. P1 wins every
exact tie, silently. Line the two cars up and cross together — it's a good
live demonstration that "who's ahead" here is decided by iteration order,
not by who was truly a half-pixel in front.
