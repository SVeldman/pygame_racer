# Week 5, Part 1 Walkthrough — An Advanced Start Menu

Built directly on top of Week 4's finished game, this session turns the
plain "READY TO RACE?" screen into a real menu: choose your car, how many
racers total, how long the race is, and how hard the AI is — all before
every race. Two Pygame Zero / Python ideas show up here that no earlier week
needed: a new input hook (`on_key_down`) and settings that reshape the game
between races.

## Starting Code for Week 5, Part 1

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


## Step 1: The Menu's Data

Add `import random` at the top if it isn't already there, then this block of
menu data near the top of the file:

```python
# ---------------------------------------------------------------------------
# MENU OPTIONS
# ---------------------------------------------------------------------------
# Each of these lists is one menu field's set of choices. Keeping them as
# data (lists/tuples) instead of a pile of if/elif statements means adding a
# new difficulty or a new car later is a one-line change.
CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RACERS = 7      # total cars, including the player

# (label shown in the menu, FINISH_DISTANCE for that choice)
# One lap of ONE_LAP (below) is 3900m - the same length as the fixed race in
# every non-menu file in this project. Short is exactly one lap; Medium and
# Long are just more laps of the same course back to back, so every length
# option still has turns the whole way, none of them run out of track early.
LENGTH_OPTIONS = [
    ("Short", 3900),          # 1 lap
    ("Medium", 7800),         # 2 laps
    ("Long", 15600),          # 4 laps
]

# (label shown in the menu, (slowest, fastest) racer base_speed range)
DIFFICULTY_OPTIONS = [
    ("Easy", (4.0, 6.0)),
    ("Normal", (5.0, 8.5)),
    ("Hard", (7.0, 10.0)),
]

MENU_FIELDS = ["Car", "Racers", "Length", "Difficulty"]

# --- The player's current menu selections (change these with the menu) -----
selected_field = 0       # index into MENU_FIELDS - which row is highlighted
car_index = 0             # index into CAR_CHOICES
num_racers = 4            # 1..MAX_RACERS, including the player
length_index = 1          # index into LENGTH_OPTIONS (starts on "Medium")
difficulty_index = 1      # index into DIFFICULTY_OPTIONS (starts on "Normal")
```

**Why "Racers" means the total, not just the AI count:** `num_racers = 4`
means 4 cars total on the grid — you plus 3 AI opponents, not you plus 4.
This choice ripples through the whole file: `LANE_COUNT` (Step 2) becomes
`NUM_RACERS` directly, not `NUM_RACERS + 1` the way `LANE_COUNT = NUM_RIVALS
+ 1` worked in earlier weeks — the player is already counted.

## Step 2: A Fixed Window, Sized for the Biggest Race

Replace the tuning knobs and window-size block:

```python
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

# ---------------------------------------------------------------------------
# WINDOW SIZE - fixed once, sized for the BIGGEST possible race
# ---------------------------------------------------------------------------
# Pygame Zero reads WIDTH once, when the window is created, and can't change
# it afterward. So we size the window for MAX_RACERS lanes, even though most
# races will use fewer. A race with fewer racers just uses a narrower road,
# centered in the same window, with extra grass on each side.
_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600
CENTER = WIDTH // 2
```

**The engineering constraint worth explaining, not glossing over:** the
window's actual pixel size never changes once pgzero creates it. Every
earlier week's `WIDTH` formula used the *current* `NUM_RIVALS` because that
number never changed after the file loaded. Here, the menu lets students
change the racer count *live* — so `WIDTH` has to be sized for the largest
possible choice (`MAX_RACERS`) up front, and a race with fewer racers just
leaves extra grass showing on the sides of that same fixed window.

## Step 3: The Master Track

Replace `TRACK` with a shared "one lap" building block, repeated:

```python
# ---------------------------------------------------------------------------
# THE MASTER TRACK
# ---------------------------------------------------------------------------
# ONE_LAP is a single 3900m loop that starts and ends at CENTER, so copies of
# it can be placed back to back with no seam - `ONE_LAP * 4` is just Python
# repeating the list 4 times, giving a 15,600m course that's really just
# "the same lap, four times." "Short"/"Medium"/"Long" (see LENGTH_OPTIONS
# above) simply stop the race after 1, 2, or 4 of those laps - they all
# share the same curves, so no length option ever runs out of track early.
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
```

**Math note — why `ONE_LAP * 4` works seamlessly:** Python's `*` on a list
repeats it — `[1, 2] * 3` is `[1, 2, 1, 2, 1, 2]`. This only produces a
smooth track because `ONE_LAP` was deliberately designed to start AND end at
`CENTER` — so segment 13 (the end of lap one) hands off to segment 14 (the
start of lap two) at the exact same centre position, with no jump. `Short`
(one lap) stops the race after `3900` of this `15,600`-long `TRACK`; `Long`
uses the whole thing.

## Step 4: "Currently Applied" Settings vs. Menu Selections

Replace the game-state block:

```python
# ---------------------------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------------------------
# NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, and DIFFICULTY_RANGE
# used to be constants that never changed. Now they're just the CURRENTLY
# APPLIED settings, and `_apply_menu_choices()` (below) is the one place
# that ever changes them, right when a race is about to start.
NUM_RACERS = num_racers
LANE_COUNT = NUM_RACERS      # total cars IS the lane count - it already
                              # includes the player
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]

player = Actor(CAR_CHOICES[car_index], (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
racers = []
game_state = "waiting"          # "waiting"|"countdown"|"racing"|"frozen"|"won"
race_results = []
player_place = None
countdown_timer = 0
freeze_timer = 0
player_start_lane = 0.0          # the player's lane on the starting grid
```

**The idea worth sitting with:** `num_racers` (the menu's *current
selection*) and `NUM_RACERS` (the *applied* setting the race is actually
using) are two different variables, on purpose. Changing the menu selection
shouldn't retroactively resize a race that's already running — `Step 6`'s
`_apply_menu_choices()` is the one and only place that ever copies a
selection into its applied counterpart.

Add this function, right after `lane_to_x()`:
```python
def _apply_menu_choices():
    """Copy the menu's current selections into the actual game settings.
    This only runs once, right when SPACE is pressed on the menu - the game
    settings stay fixed for the whole race after that."""
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    player.image = CAR_CHOICES[car_index]
```

**A brand-new trick:** `player.image = CAR_CHOICES[car_index]` reassigns an
`Actor`'s sprite *after* it's already been created — the same `player`
object just starts drawing a different picture. Nothing before this week
ever needed to change a car's look mid-game.

## Step 5: Update `new_race()`

```python
def new_race():
    """Set up a fresh starting grid using whatever settings are CURRENTLY
    applied (NUM_RACERS / ROAD_WIDTH / etc). Ends in "waiting" so players
    can adjust the menu again before the next race, too."""
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

    # random.sample() picks distinct colors, unlike calling random.choice()
    # once per racer - so no two AI racers end up looking the same, and none
    # of them match the player's own car either.
    available_colors = [c for c in CAR_CHOICES if c != CAR_CHOICES[car_index]]
    racer_colors = random.sample(available_colors, k=len(grid) - 1)
    racers = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
            "state": "racing",       # "racing" | "frozen" - mirrors the player's own
            "freeze_timer": 0,
        }
        for lane_i, color in zip(grid[1:], racer_colors)
    ]
    for r in racers:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)
```

Only two things changed from Week 4's version: `LANE_COUNT` already includes
the player (no `+ 1` anywhere), and the list of possible AI racer colors
first excludes whatever color the player picked — so nobody ever ends up
racing a clone of their own car.

## Mid-Session Checkpoint: The Menu's Data Model Works, Nobody Can Touch It Yet

At this stage, the full Python script should look something like this. (One
small change not called out as its own step: the AI-drawing loop in
`draw()` now says `racers` instead of `rivals`, matching the rename `Step 5`
just made to `new_race()` — without it, `draw()` would crash looking for a
variable that no longer exists.)

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


def _apply_menu_choices():
    global NUM_RACERS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RACERS = num_racers
    LANE_COUNT = NUM_RACERS
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    player.image = CAR_CHOICES[car_index]


### RACE SETUP
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

Run it and the race itself already works end-to-end with the new menu data
model underneath — but there's still no menu on screen, and no way to
change any setting. The old plain "READY TO RACE?" text and the old
SPACE-to-start handling in `update()` are both still doing their Week 4 job
untouched. Steps 6-8 are what make the menu actually visible and
interactive; nothing about the race itself changes again after this point.

## Step 6: `on_key_down` — a Different Tool for a Different Job

Add this function anywhere below `new_race()`:

```python
# ---------------------------------------------------------------------------
# on_key_down - fires ONCE per keypress, not every frame it's held
# ---------------------------------------------------------------------------
def on_key_down(key):
    global selected_field, num_racers, car_index, length_index, difficulty_index
    global game_state, countdown_timer

    if game_state != "waiting":
        return   # the menu only responds to input on the "waiting" screen

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
        # Apply the change immediately and rebuild the starting grid, so the
        # cars lined up behind the menu always match what the menu currently
        # says - change "Racers" from 4 to 6 and you'll see 2 more cars
        # appear on the grid right away, without needing to start the race
        # first.
        _apply_menu_choices()
        new_race()
    elif key == keys.SPACE:
        # Starts the race with whatever grid is already on screen - every
        # LEFT/RIGHT edit already rebuilt it to match the current menu settings.
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES
```

**The idea to put on the board:** `keyboard.left` (used everywhere else in
this project) is `True` for every frame a key is held — perfect for
continuous movement, but terrible for a menu, since it would fly through
options 60 times a second. `on_key_down(key)` is a third special function
pgzero will call for you, alongside `draw()` and `update()` — but it only
fires *once*, exactly when a key is first pressed down, no matter how long
it's then held. That's exactly what a menu needs: press LEFT once, move to
the previous choice once.

Point out the `if game_state != "waiting": return` line at the top — the
menu should only ever respond to input on the menu screen, so every other
state is a no-op here.

**Why `_apply_menu_choices()` and `new_race()` run on every LEFT/RIGHT, not
just on SPACE:** without this, the starting grid shown behind the menu would
be stale — you could set "Racers" to 6 but still see the 4-car grid from
before until the race actually started. Rebuilding immediately keeps what's
on screen honest about what will actually happen.

## Step 7: Draw the Menu

Replace the plain `"READY TO RACE?"` banner call with:
```python
    if game_state == "waiting":
        _draw_menu()
```

And add the drawing function itself:
```python
def _draw_menu():
    """Draw the settings menu: one line per field, with the currently
    selected field highlighted and an arrow pointing at it."""
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
```

**Why `CAR_CHOICES[car_index].replace("car_", "").title()`:** the raw value
`"car_blue"` is a filename, not something you'd want to show a player.
`.replace("car_", "")` strips the prefix down to `"blue"`, and `.title()`
capitalizes it to `"Blue"` — a small string-manipulation chain worth reading
right to left: start with the raw string, strip a prefix, then fix
capitalization.

## Step 8: `update()` Barely Has to Change

The only change to `update()` is at the very top — replace the old
"waiting" handling:
```python
    # "waiting" is handled entirely by on_key_down() above now - update()
    # has nothing to do while the menu is open, since nothing should move.
    if game_state == "waiting":
        return
```

Everything else in `update()` — countdown, racing, frozen, won — is
unchanged from Week 4.

## Checkpoint: Final Code for Week 5, Part 1

The full script should now match `05_week5_part1_menu.py` — a real settings
menu controlling car, racer count, race length, and difficulty, feeding into
the same race you've been building since Week 3.

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

**Watch for:** every other field (`Car`, `Length`, `Difficulty`) wraps
around with `%` when you push past an end — LEFT past the first car choice
lands you on the last one. `Racers` is the odd one out: it's clamped with
`max(1, min(MAX_RACERS, ...))`, so pushing LEFT at `1` or RIGHT at
`MAX_RACERS` just stops instead of wrapping. Worth calling out explicitly so
students don't assume all four fields behave identically.
