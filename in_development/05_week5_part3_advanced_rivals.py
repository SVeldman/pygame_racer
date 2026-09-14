"""Week 5, Part 3 - Advanced rivals: lane changes and rival-vs-rival crashes.

WHAT'S NEW SINCE PART 2
------------------------
Every AI racer used to sit in one lane for the whole race - `r["lane"]` was
set once, at the starting grid, and never touched again. Now each racer
occasionally changes lanes: it holds its lane for a random few seconds,
then smoothly eases over to a newly-picked one, and repeats. Nothing about
DRAWING or COLLIDING with a racer had to change for this - `lane_to_x`,
`draw_player_band`, and the player-vs-racer collision check all already
just read `r["lane"]` fresh every frame. Making that value drift instead of
staying constant flows straight through code that already existed.

The one genuinely new mechanic: now that racers can share a lane with each
other (even briefly, while changing lanes), two racers can actually meet.
`check_racer_collisions()` catches that and rolls a die - 25% of the time
it's a real crash (both freeze, blinking, exactly like a player hitting a
racer already works), and 75% of the time they swerve to avoid it by
picking a fresh lane instead of finishing the one they were headed for.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 05_week5_part3_advanced_rivals.py
"""

import random

# ---------------------------------------------------------------------------
# MENU OPTIONS
# ---------------------------------------------------------------------------
CAR_CHOICES = [
    "car_red", "car_blue", "car_green", "car_yellow",
    "car_orange", "car_pink", "car_silver", "car_white",
]
MAX_RACERS = 5      # total cars on track at once, players included - kept
                    # smaller than Part 1's menu since there are two bands
                    # to fit racers into now, not just one

LENGTH_OPTIONS = [
    ("Short", 3900),          # 1 lap
    ("Medium", 7800),         # 2 laps
    ("Long", 15600),          # 4 laps
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
num_racers = 4       # total cars, including both players - so this is
                     # 2 AI racers by default
length_index = 1
difficulty_index = 1

# ---------------------------------------------------------------------------
# CONSTANTS
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
PLAYER_COLLISION_DISTANCE = 80    # "same spot" = within roughly a car length

RACER_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange",
                "car_pink", "car_silver", "car_white"]

# --- Lane-changing rivals ----------------------------------------------------
LANE_CHANGE_MIN_HOLD = FPS * 2   # hold a lane for at least 2 seconds...
LANE_CHANGE_MAX_HOLD = FPS * 5   # ...and at most 5, before picking a new one
LANE_EASE_SPEED = 0.02           # fraction of the road crossed per frame
                                  # while easing toward a new lane

# --- Rival-vs-rival crashes --------------------------------------------------
RIVAL_COLLISION_DISTANCE = 80    # "same spot" = within roughly a car length
RIVAL_CRASH_CHANCE = 0.25        # otherwise they swerve to avoid it

# --- Window size: fixed for the largest possible race (see Part 1) -------
_MAX_LANE_COUNT = MAX_RACERS
_MAX_ROAD_WIDTH = LANE_WIDTH * _MAX_LANE_COUNT
GRASS_MARGIN = 200
WIDTH = _MAX_ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
BAND_HEIGHT = 400
HEIGHT = BAND_HEIGHT * 2
PLAYER_ROW_LOCAL = BAND_HEIGHT - 120
CENTER = WIDTH // 2

# --- The master track (same idea as Part 1 - short/medium/long are all
# some number of laps of this one 3900m course) ------------------------------
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

# --- Colours -----------------------------------------------------------------
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)
DIVIDER = (20, 20, 20)

# ---------------------------------------------------------------------------
# CURRENTLY APPLIED SETTINGS
# ---------------------------------------------------------------------------
NUM_RACERS = num_racers
LANE_COUNT = NUM_RACERS       # total cars IS the lane count now - it already
                               # includes both players, unlike Part 1's
                               # "rivals + 1 for the player"
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


def _player_lane(player):
    """This player's current lane, as a fraction of the road (0.0-1.0) -
    computed from their actor's x the same way a racer's stored "lane"
    already works, so it's meaningful to compare across two different
    players' bands even though each band's road curves differently."""
    return (player["actor"].x - road_left(PLAYER_ROW_LOCAL, player)) / ROAD_WIDTH


def make_player(label, band_top, key_left, key_right, key_up, key_down):
    return {
        "label": label,
        "actor": Actor("car_red", (WIDTH // 2, band_top + PLAYER_ROW_LOCAL)),
        "band_top": band_top,
        "speed": 0.0,
        "distance": 0.0,
        "finished": False,
        "state": "racing",       # "racing" | "frozen" | "finished" (per-player, not global)
        "freeze_timer": 0,
        "place": None,            # this player's finishing place, once "finished"
        "start_lane": 0.0,        # this player's lane on the starting grid
        "keys": (key_left, key_right, key_up, key_down),
    }


game_state = "waiting"          # "waiting"|"countdown"|"racing"|"won"
countdown_timer = 0

players = [
    make_player("P1", 0, "left", "right", "up", "down"),
    make_player("P2", BAND_HEIGHT, "a", "d", "w", "s"),
]

# The AI racers, shared by both players - there is exactly ONE of these
# lists for the whole race, not one per player. Both bands look at the same
# racers; they just each project them onto their own half of the screen
# (see update_racers, draw_player_band and the collision check below).
racers = []

# Every racer AND every player, in the order they cross the finish line -
# this is what turns "did I finish" into "what PLACE did I finish," for
# both players, the same way race_results already worked in single-player.
race_results = []


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
    for r in racers:
        # Any player's band works fine for this initial placement - every
        # player starts at distance 0, so the projection is identical for
        # both right now. It'll be recomputed per-band every frame anyway.
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


_apply_menu_choices()   # both players start with car_red from make_player() -
new_race()              # this sets each one's REAL starting car before the first draw


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
        elif field == "Length":
            length_index = (length_index + direction) % len(LENGTH_OPTIONS)
        elif field == "Difficulty":
            difficulty_index = (difficulty_index + direction) % len(DIFFICULTY_OPTIONS)
        _apply_menu_choices()
        new_race()          # keep the preview grids matching the menu live
    elif key == keys.SPACE:
        # Starts the race with whatever grid is already on screen - every
        # LEFT/RIGHT edit already rebuilt it to match the current menu settings.
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


def update_player(player):
    if player["state"] == "finished":
        return   # this player's race is over - nothing left to update
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
                # Snap the player back to their own starting-grid lane.
                # Every car got a different lane on the shared grid, so
                # this is guaranteed to separate them - unlike knocking the
                # racer back in distance, which leaves both cars in the
                # same lane and lets the player drift straight back into
                # the racer the instant they unfreeze, re-triggering the
                # freeze over and over.
                player["actor"].x = lane_to_x(player["start_lane"],
                                               PLAYER_ROW_LOCAL, player)
                break


def update_racers():
    """Advance the shared racers exactly once per frame - not once per
    player. A racer that's frozen (because it just collided with a player
    or another racer, in EITHER band) sits out its own timer, the same
    shape as a player's own "frozen" state."""
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
                race_results.append(r)

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

    check_racer_collisions()


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


def update():
    global game_state, countdown_timer

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
    _check_player_collision()

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
