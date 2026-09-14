"""Week 3, Part 2 - A proper start, a countdown, and recovering from a crash.

WHAT'S NEW SINCE PART 1
-------------------------
Part 1 played fine, but it had two rough edges: the race just started the
instant the file loaded (no "get ready" moment), and a crash ended the whole
run instantly. This lesson fixes both by growing `game_state` from three
values into five:

    "waiting"  ->  "countdown"  ->  "racing"  <->  "frozen"  ->  "won"

  * "waiting": a "READY TO RACE?" screen. Nothing moves. Pressing SPACE
    moves you to "countdown".
  * "countdown": a 3...2...1...GO! sequence. Still nothing moves - the race
    clock doesn't start for ANYONE until this is over.
  * "racing": exactly like Part 1.
  * "frozen": NEW. Instead of a collision ending the race, it freezes your
    car (your speed drops to 0 and your controls stop responding) for about
    two seconds, with your car blinking and a "Recovering..." message. The
    rivals keep racing while you're stuck - so a crash still costs you real
    ground, it just doesn't end your run.
  * "won": the same placement banner as Part 1.

Whenever you add a new state to a machine like this, the important design
question is always "what can happen FROM this state, and what causes moving
to the NEXT one?" - see the big comment inside update() below.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 03_week3_part2.py
"""

import random

NUM_RIVALS = 3
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

FINISH_DISTANCE = 3900         # matches the "one lap" length used everywhere else
RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600

# ---------------------------------------------------------------------------
# TIMERS
# ---------------------------------------------------------------------------
# Pygame Zero calls update() 60 times a second by default. So "how many
# frames is 2 seconds?" is just "2 * 60." We count these timers DOWN, one
# frame at a time, and treat "reached zero" as "time to change state."
FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3   # "3","2","1", then a short "GO!"
FREEZE_FRAMES = 2 * FPS        # how long a crash freezes you for

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
rivals = []
game_state = "waiting"          # "waiting"|"countdown"|"racing"|"frozen"|"won"
race_results = []
player_place = None
countdown_timer = 0             # frames left in the "countdown" state
freeze_timer = 0                 # frames left in the "frozen" state
player_start_lane = 0.0          # the player's lane on the starting grid


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
    return road_left(y) + lane * ROAD_WIDTH


def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)


def row_at(dist):
    return PLAYER_ROW - (dist - distance_traveled)


def new_race():
    """Reset to a fresh starting grid. Note this ends in "waiting", not
    "racing" - pressing SPACE from here is what kicks off the countdown."""
    global player_speed, distance_traveled, rivals, game_state
    global race_results, player_place, player_start_lane
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
    # once per rival - so no two rivals end up looking the same.
    rival_colors = random.sample(RIVAL_COLORS, k=len(grid) - 1)
    rivals = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
            "state": "racing",       # "racing" | "frozen" - mirrors the player's own
            "freeze_timer": 0,
        }
        for lane_i, color in zip(grid[1:], rival_colors)
    ]
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
        # Blink a frozen rival too, the same way the player blinks below.
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()

    # Blink the player's car during "frozen" instead of drawing it solid -
    # dividing the timer by 6 and checking even/odd toggles roughly 5 times
    # a second, which reads clearly as "blinking" without a dedicated
    # animation.
    if game_state != "frozen" or (freeze_timer // 6) % 2 == 0:
        player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} / {FINISH_DISTANCE} m",
                     topleft=(10, 40), fontsize=30, color="white")

    if game_state == "frozen":
        screen.draw.text("CRASHED! Recovering...", midtop=(WIDTH // 2, 10),
                         fontsize=32, color=(255, 90, 60))
    elif game_state == "waiting":
        _banner("READY TO RACE?", "Press SPACE to start")
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")


def _draw_countdown():
    """Work out whether we're still on a number (3, 2, 1) or into the final
    "GO!" flash, based on how many frames have elapsed since the countdown
    began."""
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

    # ------------------------------------------------------------------
    # THE STATE MACHINE
    # ------------------------------------------------------------------
    # Each `if` below handles ONE state, and is responsible for deciding
    # when (and to what) that state transitions. "waiting", "countdown" and
    # "won" all `return` immediately after handling their own state - they
    # have nothing to do with cars moving, so there's no reason to run the
    # rest of this function.
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

    # From here on, game_state is either "racing" or "frozen" - both need
    # the rivals to keep moving, so that logic lives outside this if/else.
    if game_state == "frozen":
        freeze_timer -= 1
        if freeze_timer <= 0:
            game_state = "racing"
        # No steering, no throttle, no off-road checks while frozen -
        # player_speed just stays at 0 until you're back to "racing".
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

    # Rivals keep racing whether you're "racing" or "frozen" - this is what
    # makes freezing a real penalty instead of a free pause. A rival that's
    # frozen itself (because it just collided with you) sits out its own
    # timer instead of moving - exactly the same shape as the player's own
    # "frozen" handling above.
    for r in rivals:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        # Not "elif" - a rival that JUST switched back to "racing" above
        # still needs its position updated this same frame. Otherwise it
        # would stay drawn at its old, overlapping spot for one more frame
        # and immediately collide with you again the instant you both wake
        # up, freezing you both forever.
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            y = row_at(r["distance"])
            r["actor"].pos = (lane_to_x(r["lane"], y), y)
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)

    if game_state == "racing":
        # A crash freezes you instead of ending the run - and now freezes
        # the rival you hit too, for the same length of time. `break` after
        # the first hit stops us from freezing twice in the same frame if
        # you're somehow touching two rivals at once.
        for r in rivals:
            if player.colliderect(r["actor"]):
                game_state = "frozen"
                freeze_timer = FREEZE_FRAMES
                player_speed = 0.0
                r["state"] = "frozen"
                r["freeze_timer"] = FREEZE_FRAMES
                # Snap both cars back to their own starting-grid lane.
                # Every car got a different lane on the grid, so this is
                # guaranteed to separate them - unlike knocking the rival
                # back in distance, which leaves both cars in the same
                # lane and lets the player drift straight back into the
                # rival the instant they unfreeze, re-triggering the
                # freeze over and over.
                player.x = lane_to_x(player_start_lane, PLAYER_ROW)
                r["actor"].x = lane_to_x(r["lane"], row_at(r["distance"]))
                break

        if distance_traveled >= FINISH_DISTANCE:
            player_place = len(race_results) + 1
            game_state = "won"
