"""Week 5, Bonus Option 3 - The menu AND split-screen, together.

WHAT THIS FILE ADDS
--------------------
This combines both bonus options: a settings menu (car choice per player,
rival count, race length, difficulty) feeding into a stacked split-screen
race where Player 1 (arrow keys) and Player 2 (W/A/S/D) each get their own
band, their own AI rivals, and their own chance to crash and recover.

If Options 1 and 2 both made sense to you, this file has very few genuinely
NEW ideas - it's mostly "put the two things we already built together."
That's worth noticing: once `player` was a dict (Option 2) and `rivals` was
a list built from menu settings (Option 1), combining them is mostly
copy-and-connect, not new invention. Good code design pays off when you
combine features, not just when you write them the first time.

The one new wrinkle: each player now needs their OWN list of rivals (P1's
opponents shouldn't be the same Actors as P2's), and their own little
"racing"/"frozen" state, so those live inside each player's dict alongside
everything Option 2 already put there.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 11_week5_combined.py
"""

import random

# ---------------------------------------------------------------------------
# MENU OPTIONS
# ---------------------------------------------------------------------------
CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RIVALS = 4     # kept smaller than Option 1's menu - there are two bands
                    # to fit rivals into now, not just one

LENGTH_OPTIONS = [
    ("Short", 1300),
    ("Medium", 2650),
    ("Long", 3900),
]
DIFFICULTY_OPTIONS = [
    ("Easy", (4.0, 6.0)),
    ("Normal", (5.0, 8.5)),
    ("Hard", (7.0, 10.0)),
]
MENU_FIELDS = ["P1 Car", "P2 Car", "Rivals", "Length", "Difficulty"]

selected_field = 0
p1_car_index = 0
p2_car_index = 1
num_rivals = 2
length_index = 1
difficulty_index = 1

# ---------------------------------------------------------------------------
# TUNING "KNOBS"
# ---------------------------------------------------------------------------
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

RIVAL_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange",
                "car_pink", "car_silver", "car_white"]

# --- Window size: fixed for the largest possible race (see Option 1) -------
_MAX_LANE_COUNT = MAX_RIVALS + 1
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120
CENTER = WIDTH // 2

# --- The master track (same idea as Option 1 - short/medium/long are all
# prefixes of this one course) -----------------------------------------------
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
DIVIDER = (20, 20, 20)

# ---------------------------------------------------------------------------
# CURRENTLY APPLIED SETTINGS
# ---------------------------------------------------------------------------
NUM_RIVALS = num_rivals
LANE_COUNT = NUM_RIVALS + 1
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]


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
        "rivals": [],
        "keys": (key_left, key_right, key_up, key_down),
    }


game_state = "waiting"          # "waiting"|"countdown"|"racing"|"won"
countdown_timer = 0
winner_label = None

players = [
    make_player("P1", 0, "left", "right", "up", "down"),
    make_player("P2", BAND_HEIGHT, "a", "d", "w", "s"),
]


def _apply_menu_choices():
    """Copy the menu's current picks into the actual game settings - the
    same idea as Option 1's _apply_menu_choices(), just also touching each
    player's chosen car image."""
    global NUM_RIVALS, LANE_COUNT, ROAD_WIDTH, FINISH_DISTANCE, DIFFICULTY_RANGE
    NUM_RIVALS = num_rivals
    LANE_COUNT = NUM_RIVALS + 1
    ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
    FINISH_DISTANCE = LENGTH_OPTIONS[length_index][1]
    DIFFICULTY_RANGE = DIFFICULTY_OPTIONS[difficulty_index][1]
    players[0]["actor"].image = CAR_CHOICES[p1_car_index]
    players[1]["actor"].image = CAR_CHOICES[p2_car_index]


def _new_grid_for(player):
    """Build a starting grid of AI rivals for just ONE player's band. Both
    players get their own independent set of rivals, built the same way."""
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_lane = (grid[0] + 0.5) / LANE_COUNT
    player["actor"].x = lane_to_x(player_lane, PLAYER_ROW_LOCAL, player)

    player["rivals"] = [
        {
            "actor": Actor(random.choice(RIVAL_COLORS)),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(*DIFFICULTY_RANGE),
            "finished": False,
        }
        for lane_i in grid[1:]
    ]
    for r in player["rivals"]:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW_LOCAL, player),
                          player["band_top"] + PLAYER_ROW_LOCAL)


def new_race():
    global game_state, winner_label
    game_state = "waiting"
    winner_label = None
    for player in players:
        player["speed"] = 0.0
        player["distance"] = 0.0
        player["finished"] = False
        player["state"] = "racing"
        player["freeze_timer"] = 0
        _new_grid_for(player)
        player["actor"].y = player["band_top"] + PLAYER_ROW_LOCAL


new_race()


def on_key_down(key):
    global selected_field, p1_car_index, p2_car_index
    global num_rivals, length_index, difficulty_index
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
        elif field == "P2 Car":
            p2_car_index = (p2_car_index + direction) % len(CAR_CHOICES)
        elif field == "Rivals":
            num_rivals = max(0, min(MAX_RIVALS, num_rivals + direction))
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        _apply_menu_choices()
        new_race()          # keep the preview grids matching the menu live
    elif key == keys.SPACE:
        _apply_menu_choices()
        new_race()
        game_state = "countdown"
        countdown_timer = COUNTDOWN_FRAMES


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

    for r in player["rivals"]:
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


def _draw_menu():
    screen.surface.set_clip(None)
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 160, WIDTH, 320), (0, 0, 0))
    screen.draw.text("READY TO RACE?", center=(WIDTH // 2, HEIGHT // 2 - 130),
                     fontsize=40, color="white")

    values = [
        CAR_CHOICES[p1_car_index].replace("car_", "").title(),
        CAR_CHOICES[p2_car_index].replace("car_", "").title(),
        str(num_rivals),
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

    # This player's own rivals move regardless of whether THEY are frozen -
    # exactly like every earlier week, just scoped inside this player's dict.
    for r in player["rivals"]:
        r["distance"] += r["base_speed"]
        y_local = row_at(r["distance"], player)
        r["actor"].pos = (lane_to_x(r["lane"], y_local, player),
                          player["band_top"] + y_local)
        if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
            r["finished"] = True

    if player["state"] == "racing":
        for r in player["rivals"]:
            if player["actor"].colliderect(r["actor"]):
                player["state"] = "frozen"
                player["freeze_timer"] = FREEZE_FRAMES
                player["speed"] = 0.0
                break


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

    for player in players:
        update_player(player)

    for player in players:
        if not player["finished"] and player["distance"] >= FINISH_DISTANCE:
            player["finished"] = True
            winner_label = player["label"]
            game_state = "won"
            break
