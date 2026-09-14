# Week 3, Part 2 Walkthrough — A Proper Start, and Recovering From a Crash

Part 1 played fine, but it had two rough edges: the race started the instant
the file loaded (no "get ready" moment), and a crash ended the whole run
instantly. This session fixes both by growing `game_state` from three values
into five:

```
"waiting"  ->  "countdown"  ->  "racing"  <->  "frozen"  ->  "won"
```

For every state, ask the same two questions: **"what can happen from here?"**
and **"what causes leaving this state?"** Walking through that table on the
board before touching any code pays off enormously in this session.

| State | What can happen | Leaves when... |
|---|---|---|
| `waiting` | Nothing moves. A "READY TO RACE?" screen. | SPACE is pressed → `countdown` |
| `countdown` | Nothing moves. 3...2...1...GO! | timer hits 0 → `racing` |
| `racing` | Normal driving, exactly like Part 1. | a crash → `frozen`, or the finish line → `won` |
| `frozen` | Your car (and the rival you hit) sit still and blink. Everyone else keeps racing. | timer hits 0 → `racing` |
| `won` | The placement banner. | SPACE is pressed → a brand new `waiting` race |


## Step 1: Frame-Based Timers

Add this block of constants:

```python
# ---------------------------------------------------------------------------
# TIMERS
# ---------------------------------------------------------------------------
FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3   # "3","2","1", then a short "GO!"
FREEZE_FRAMES = 2 * FPS        # how long a crash freezes you for
```

Pygame Zero calls update() 60 times a second by default. So "how many
frames is 2 seconds?" is just "2 * 60." We count these timers DOWN, one
frame at a time, and treat "reached zero" as "time to change state."

**Math note:** `len(COUNTDOWN_NUMBERS) * FPS` is "3 numbers, 60 frames
each" = 180 frames, and `FPS // 3` (20 frames, a third of a second) tacks on
a short extra window for a final "GO!" flash — so `COUNTDOWN_FRAMES` is
`200` in total. A "timer" in this style of game is nothing more than a
number that starts at some frame count and gets decremented by `1` every
`update()` call; "the timer expired" just means "that number reached `0`."

## Step 2: New State Variables

Add these alongside the existing state variables (and change
`game_state`'s starting value):

```python
game_state = "waiting"          # "waiting"|"countdown"|"racing"|"frozen"|"won"
countdown_timer = 0             # frames left in the "countdown" state
freeze_timer = 0                 # frames left in the "frozen" state
player_start_lane = 0.0          # the player's lane on the starting grid
```

**Why remember `player_start_lane`:** Part 1 only ever used the player's
starting lane once, right when it was picked, then threw it away. This
session needs it again later — when a crash happens, we're going to snap the
player back to their own grid lane rather than leave them wherever the
collision occurred (Step 5 explains why).

## Step 3: Update `new_race()`

Two small changes: rename the local `player_lane` to the new global
`player_start_lane` (and remember its value), and give every rival its own
`state`/`freeze_timer`, matching the player's own. Also change the ending
state from `"racing"` to `"waiting"`.

```python
def new_race():
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
```

**Why give rivals a `state` at all:** in Part 1, a rival was either racing or
it wasn't — there was no in-between. This session adds a *third* possibility
for a rival (frozen, after a crash), so it needs the same two-field shape
(`state` + `freeze_timer`) the player already has, tracked per-rival instead
of once globally.

## Step 4: Drawing Every State

Blink the rivals and the player while frozen, instead of drawing them solid:

```python
    for r in rivals:
        # Blink a frozen rival too, the same way the player blinks below.
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()

    if game_state != "frozen" or (freeze_timer // 6) % 2 == 0:
        player.draw()
```

**Math note — a blink from a timer:** `freeze_timer // 6` groups every 6
consecutive frame-counts together (`120-115` all give `20`, `114-109` all
give `19`, ...), and `% 2` alternates between even and odd as that grouped
number decreases. At 60 FPS, 6 frames is a tenth of a second, so this toggles
roughly 5 times a second — fast enough to read as "blinking," without
needing a dedicated animation system.

Add the new HUD messages and screens, replacing the old crashed-only check:

```python
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
```

And add the countdown-drawing helper:
```python
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
```

**Math note:** `elapsed` is "how many frames have ticked by since the
countdown started" — the *opposite direction* from `countdown_timer`, which
counts down. `elapsed // FPS` turns that into "how many whole seconds have
elapsed" (`0` for the first second, `1` for the second, `2` for the third),
which indexes straight into `COUNTDOWN_NUMBERS = [3, 2, 1]`. Once a full 3
seconds have elapsed, that index would run off the end of the list — that's
exactly the case the `else` branch catches, showing "GO!" instead.

## Mid-Session Checkpoint: Every State Can Draw Itself, None of Them Work Yet

This is a natural stopping point if a group is running behind — save Step 5
for the start of Week 4's session. At this stage, the full Python script
should look something like this:

```python
import random

### CONSTANTS
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

FINISH_DISTANCE = 3900
RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3
FREEZE_FRAMES = 2 * FPS

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


### ROAD
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


### RACE SETUP
def new_race():
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
    elif game_state == "waiting":
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

    if distance_traveled >= FINISH_DISTANCE:
        player_place = len(race_results) + 1
        game_state = "won"
```

Run it and you're stuck looking at "READY TO RACE?" forever — pressing
SPACE quietly calls `new_race()` (you can tell because the grid reshuffles),
but nothing ever advances to `countdown` or `racing`, because `update()`
still only knows the old two-state world (`"racing"` vs. "anything else").
Every state can now draw its own screen correctly; none of them can be
*reached*. That's exactly the gap Step 5 closes.

## Step 5: The State Machine in `update()`

This is the whole session's payoff. Replace the top of `update()`:

```python
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
```

Then replace the old steering/throttle block with a version gated on
`"frozen"` vs. everything else:

```python
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
```

Now update the rival-movement loop so a frozen rival sits out its own timer
instead of moving:

```python
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
```

**This "not elif" comment is worth pausing on — it's a real bug this exact
project once had.** If a rival's movement were skipped on the very frame it
wakes back up, it would still be drawn at the old, overlapping spot for one
more frame. Since a frozen car doesn't move, "overlapping" doesn't go away
on its own — the very next collision check (below) would find the same
overlap immediately, refreeze both cars, and repeat forever. Using a second,
independent `if` (instead of `elif`) means a rival that flips to `"racing"`
in the first `if` immediately gets its position updated in the second one,
in that same frame.

Finally, update the collision check to freeze both cars, and separate them:

```python
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
```

**Why snap back to a LANE, not just any gap:** the first fix that might come
to mind is "push the rival back a little in distance so there's room." That
almost works, but both cars are frozen and don't move again until they wake
up — if they're still in the *same lane*, the instant both unfreeze, the
player is right back on a collision course with that same rival, and a
narrow gap can close again within a single frame of driving at full speed.
Snapping each car to its OWN lane from the starting grid sidesteps the
problem completely: since every car already has a guaranteed-unique lane, no
amount of speed can put two just-unfrozen cars back in the same spot by
accident.

## Checkpoint: Final Code for Week 3, Part 2

The full script should now match `03_week3_part2.py` — a "READY TO RACE?"
screen, a 3-2-1-GO countdown, and a crash that costs time instead of ending
the run.

```python
import random

### CONSTANTS
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

FINISH_DISTANCE = 3900
RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3
FREEZE_FRAMES = 2 * FPS

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


### ROAD
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


### RACE SETUP
def new_race():
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
    elif game_state == "waiting":
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

**Watch for:** the biggest behavior change from Part 1 is that rivals keep
moving while YOU are frozen — make sure students see that a crash still
costs real ground, it just isn't fatal anymore. If a class runs long, this
state-machine work can spill into the start of Week 4 without breaking
anything — Week 4 builds on this finished file either way.
