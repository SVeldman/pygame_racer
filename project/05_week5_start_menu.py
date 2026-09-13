"""Week 5, Bonus Option 1 - An advanced start menu.

WHAT THIS FILE ADDS
--------------------
Built on top of Week 4 Part 2, this file turns the plain "READY TO RACE?"
screen into a real menu where you choose, before every race:
  * CAR   - which sprite you drive
  * RIVALS - how many opponents you're racing against
  * LENGTH - Short / Medium / Long (how far FINISH_DISTANCE is)
  * DIFFICULTY - Easy / Normal / Hard (how fast rivals are allowed to be)

Two new Pygame Zero / Python ideas show up here that earlier weeks avoided:

  1. `on_key_down(key)` - a THIRD special function pgzero will call for you,
     alongside draw() and update(). Unlike `keyboard.left` (which is True
     for every frame a key is held down - great for continuous movement),
     `on_key_down` fires exactly ONCE per key press. That's exactly what a
     menu wants: press LEFT once, move to the previous choice once - not 60
     times a second for as long as the key is held.

  2. SETTINGS THAT CHANGE THE GAME'S SHAPE. Earlier weeks had constants
     (`NUM_RIVALS`, `FINISH_DISTANCE`, ...) that were fixed for the whole
     file. Here, the menu can change them between races. Because the window
     itself can't resize once pgzero creates it, `WIDTH` is calculated ONCE
     from `MAX_RIVALS` (the largest the menu allows) - picking fewer rivals
     just leaves extra grass showing on the sides instead of shrinking the
     window.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 09_week5_start_menu.py
"""

import random

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
MAX_RIVALS = 6

# (label shown in the menu, FINISH_DISTANCE for that choice)
# All three lengths are cut from the SAME master TRACK below, just at
# different distances - so every length option still has turns the whole
# way, none of them run out of track early.
LENGTH_OPTIONS = [
    ("Short", 1300),
    ("Medium", 2650),
    ("Long", 3900),
]

# (label shown in the menu, (slowest, fastest) rival base_speed range)
DIFFICULTY_OPTIONS = [
    ("Easy", (4.0, 6.0)),
    ("Normal", (5.0, 8.5)),
    ("Hard", (7.0, 10.0)),
]

MENU_FIELDS = ["Car", "Rivals", "Length", "Difficulty"]

# --- The player's current menu selections (change these with the menu) -----
selected_field = 0       # index into MENU_FIELDS - which row is highlighted
car_index = 0             # index into CAR_CHOICES
num_rivals = 3            # 1..MAX_RIVALS
length_index = 1          # index into LENGTH_OPTIONS (starts on "Medium")
difficulty_index = 1      # index into DIFFICULTY_OPTIONS (starts on "Normal")

# ---------------------------------------------------------------------------
# TUNING "KNOBS" THAT DON'T CHANGE
# ---------------------------------------------------------------------------
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
# it afterward. So we size the window for MAX_RIVALS lanes, even though most
# races will use fewer. A race with fewer rivals just uses a narrower road,
# centered in the same window, with extra grass on each side.
_MAX_LANE_COUNT = MAX_RIVALS + 1
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600
CENTER = WIDTH // 2

# ---------------------------------------------------------------------------
# THE MASTER TRACK
# ---------------------------------------------------------------------------
# One long course. "Short"/"Medium"/"Long" just stop the race at different
# points along it (see LENGTH_OPTIONS above) - they all share the same
# curves, so a short race is simply "the first part of the long race."
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

# --- Colours -----------------------------------------------------------------
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

# ---------------------------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------------------------
# NUM_RIVALS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, and DIFFICULTY_RANGE
# used to be constants that never changed. Now they're just the CURRENTLY
# APPLIED settings, and `_apply_menu_choices()` (below) is the one place
# that ever changes them, right when a race is about to start.
NUM_RIVALS = num_rivals
LANE_COUNT = NUM_RIVALS + 1
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]

player = Actor(CAR_CHOICES[car_index], (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
rivals = []
game_state = "waiting"          # "waiting"|"countdown"|"racing"|"frozen"|"won"
race_results = []
player_place = None
countdown_timer = 0
freeze_timer = 0


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
    """Copy the menu's current selections into the actual game settings.
    This only runs once, right when SPACE is pressed on the menu - the game
    settings stay fixed for the whole race after that."""
    global NUM_RIVALS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RIVALS = num_rivals
    LANE_COUNT = NUM_RIVALS + 1
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    player.image = CAR_CHOICES[car_index]


def new_race():
    """Set up a fresh starting grid using whatever settings are CURRENTLY
    applied (NUM_RIVALS / ROAD_WIDTH / etc). Ends in "waiting" so players
    can adjust the menu again before the next race, too."""
    global player_speed, distance_traveled, rivals, game_state
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "waiting"
    race_results = []
    player_place = None

    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_lane, PLAYER_ROW), PLAYER_ROW)

    rivals = [
        {
            "actor": Actor(random.choice(
                [c for c in CAR_CHOICES if c != CAR_CHOICES[car_index]])),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
        }
        for lane_i in grid[1:]
    ]
    for r in rivals:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)


new_race()


# ---------------------------------------------------------------------------
# on_key_down - fires ONCE per keypress, not every frame it's held
# ---------------------------------------------------------------------------
def on_key_down(key):
    global selected_field, num_rivals, car_index, length_index, difficulty_index
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
        elif field == "Rivals":
            num_rivals = max(1, min(MAX_RIVALS, num_rivals + direction))
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        # Apply the change immediately and rebuild the starting grid, so the
        # cars lined up behind the menu always match what the menu currently
        # says - change "Rivals" from 3 to 5 and you'll see 2 more cars
        # appear on the grid right away, without needing to start the race
        # first.
        _apply_menu_choices()
        new_race()
    elif key == keys.SPACE:
        _apply_menu_choices()
        new_race()                      # make sure the grid matches, then go
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES


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
    """Draw the settings menu: one line per field, with the currently
    selected field highlighted and an arrow pointing at it."""
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 130, WIDTH, 260), (0, 0, 0))
    screen.draw.text("READY TO RACE?", center=(WIDTH // 2, HEIGHT // 2 - 100),
                     fontsize=44, color="white")

    values = [
        CAR_CHOICES[car_index].replace("car_", "").title(),
        str(num_rivals),
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


def update():
    global player_speed, distance_traveled, game_state, player_place
    global countdown_timer, freeze_timer

    # "waiting" is handled entirely by on_key_down() above now - update()
    # has nothing to do while the menu is open, since nothing should move.
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

    for r in rivals:
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
                break

        if distance_traveled >= FINISH_DISTANCE:
            player_place = len(race_results) + 1
            game_state = "won"
