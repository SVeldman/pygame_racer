"""Week 5, Bonus Option 2 - Stacked split-screen, two human players.

WHAT THIS FILE ADDS
--------------------
Built on the same road/curve ideas as Week 4, but now there is no AI at all -
two HUMAN players race each other, head to head, on the same course. Player
1 uses the arrow keys; Player 2 uses W/A/S/D. Both cars race independently
and simultaneously, but they can't see each other's half of the screen -
Pygame Zero's window is split into two horizontal bands, stacked one above
the other, each showing that player's own view of the (identical) track.

TWO NEW IDEAS MAKE THIS WORK
-----------------------------
  1. EVERYTHING THAT USED TO BE A HANDFUL OF GLOBAL VARIABLES
     (`player_speed`, `distance_traveled`, ...) now lives inside a
     DICTIONARY instead - one dict per player. That's the same trick we
     already used for rivals (a dict bundles related values together) -
     we're just using it for the human players too, so the exact same
     drawing/steering code can run once for Player 1 and once for Player 2
     instead of being duplicated.

  2. `screen.surface.set_clip(rect)` tells Pygame Zero "only actually paint
     pixels inside this rectangle, ignore anything I try to draw outside
     it." We draw Player 1's whole world (road, car, HUD) normally, but
     with the clip rectangle limited to the TOP half of the window - even
     though our drawing code doesn't know or care that it's being clipped.
     Then we do the exact same thing for Player 2, clipped to the BOTTOM
     half. `set_clip(None)` turns clipping back off.

There are no AI rivals in this file, and no collisions between the two
players (they're each racing their own private copy of the track) - see if
you can add rival cars to each band, or make the two players able to bump
into each other, as a challenge once this makes sense!

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 05_week5_split_screen.py
"""

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
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

# --- Colours -----------------------------------------------------------------
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)
DIVIDER = (20, 20, 20)     # the bar between the two bands


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
    """Draw one player's entire world - road, car, HUD - clipped to their
    own band so it can never draw over the other player's half."""
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


def _draw_countdown():
    elapsed = COUNTDOWN_FRAMES - countdown_timer
    counting_frames = len(COUNTDOWN_NUMBERS) * FPS
    if elapsed < counting_frames:
        number = COUNTDOWN_NUMBERS[elapsed // FPS]
        _banner(str(number), "Get ready...")
    else:
        _banner("GO!", "")


def _banner(title, subtitle):
    screen.surface.set_clip(None)   # banners always span the WHOLE window
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=54, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=24, color="white")


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
