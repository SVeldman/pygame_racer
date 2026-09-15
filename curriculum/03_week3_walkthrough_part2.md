# Week 3, Part 2 Walkthrough — A Proper Start, and Recovering From a Crash

Part 1 played fine, but it had two rough edges: the race started the instant
the file loaded (no "get ready" moment), and a crash ended the whole run
instantly. This session fixes both by growing `game_state` from three values
into five:

```
"waiting"  ->  "countdown"  ->  "racing"  <->  "frozen"  ->  "won"
```

**Concept: design each state by asking two questions.** For every state:
"what can happen from here?" and "what causes leaving this state?" The table
below answers both for all five states — refer back to it while wiring up
Step 5's state machine.

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
*Expected State: no visible change — nothing reads these constants yet.*

**Teaching Note:** Pygame Zero calls `update()` 60 times a second by
default, so "how many frames is 2 seconds?" is just "2 * 60." These timers
count down, one frame at a time, and "reached zero" is treated as "time to
change state."

**Math Concept:** `len(COUNTDOWN_NUMBERS) * FPS` is "3 numbers, 60 frames
each" = 180 frames. `FPS // 3` (20 frames, a third of a second) adds a short
extra window for a final "GO!" flash, so `COUNTDOWN_FRAMES` totals 200
frames. A timer in this style of game is just a number that starts at some
frame count and gets decremented by `1` every `update()` call — "the timer
expired" means it reached `0`.

## Step 2: New State Variables

Add these alongside the existing state variables (and change
`game_state`'s starting value):

```python
game_state = "waiting"          # "waiting"|"countdown"|"racing"|"frozen"|"won"
countdown_timer = 0             # frames left in the "countdown" state
freeze_timer = 0                 # frames left in the "frozen" state
player_start_lane = 0.0          # the player's lane on the starting grid
```
*Expected State: no visible change. `update()` still gates all driving
behind `game_state == "racing"`, and `game_state` now starts as `"waiting"`
instead — the car simply sits still.*

**Teaching Note:** Part 1 used the player's starting lane once, then
discarded it. This session needs it again — when a crash happens, the
player snaps back to their own grid lane instead of staying wherever the
collision occurred (Step 5 explains why).

## Step 3: Update `new_race()`

Two small changes: rename the local `player_lane` to the new global
`player_start_lane` (and remember its value), and give every rival its own
`state`/`freeze_timer`, matching the player's own. Also change the ending
state from `"racing"` to `"waiting"`.

```python
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
*Expected State: no visible change yet — starting a race still looks
identical, since nothing reads `state` or `freeze_timer` on a rival dict
until Step 5.*

**Teaching Note:** in Part 1, a rival was either racing or it wasn't. This
session adds a third possibility — frozen, after a crash — so each rival
needs the same two-field shape (`state` + `freeze_timer`) the player
already has, tracked per-rival instead of once globally.

**Classroom Prompt (For Fast Finishers):** the player gets one global
`freeze_timer`, but each rival carries its own inside its dictionary. Why
can't rivals share a single global timer the way the player does?

## Step 4: Drawing Every State

Blink the rivals and the player while frozen, instead of drawing them
solid:

```python
    for r in rivals:
        # Blink a frozen rival too, the same way the player blinks below.
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()

    if game_state != "frozen" or (freeze_timer // 6) % 2 == 0:
        player.draw()
```

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
*Expected State: the game now boots straight to a "READY TO RACE?" banner
instead of a moving car. Pressing SPACE reshuffles the grid (`new_race()`
runs) but nothing advances past "waiting" — `update()` hasn't been taught
the other four states yet.*

**Math Concept — the blink toggle:** `freeze_timer // 6` groups every 6
consecutive frame-counts together, and `% 2` alternates even/odd as that
grouped number falls. At 60 FPS, 6 frames is a tenth of a second, so this
toggles roughly 5 times a second — fast enough to read as blinking, without
a dedicated animation system.

**Math Concept — countdown indexing:** `elapsed` counts up from 0 — the
opposite direction from `countdown_timer`, which counts down.
`elapsed // FPS` turns that into whole seconds elapsed (`0`, `1`, `2`),
which indexes straight into `COUNTDOWN_NUMBERS = [3, 2, 1]`. Once a full 3
seconds have passed, that index would run off the end of the list — the
`else` branch catches exactly that case and shows "GO!" instead.

**Classroom Demo:** temporarily set `game_state = "frozen"` right after the
`new_race()` call at module load and run it. The READY TO RACE banner is
replaced by the blinking freeze overlay — a quick way to prove the blink
logic works before Step 5 makes "frozen" reachable through normal play.
Undo the change afterward.

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
*Expected State: stuck on "READY TO RACE?" forever. Pressing SPACE quietly
calls `new_race()` — the grid reshuffles — but nothing advances to
`countdown` or `racing`.*

`update()` still only knows the old two-state world (`"racing"` vs.
"anything else"), so every state can now draw its own screen correctly, but
none of them can be *reached* yet. That gap is what Step 5 closes — this
old two-state logic is left in place deliberately, not an oversight.

## Step 5: The State Machine in `update()`

This is where the five states above actually get wired together. Replace
the top of `update()`:

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

**Teaching Note:** each `if` owns exactly one state and decides when it
ends. `"waiting"`, `"countdown"`, and `"won"` all `return` immediately —
none of them involve cars moving, so there's no reason to run the rest of
the function on those frames.

**Classroom Demo:** delete the `return` after the `"waiting"` block and run
it. Every frame now falls through into the rival-movement and collision
logic below even before the countdown starts, and rivals begin racing
before the player ever sees GO!. Restore the `return` afterward.

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

**Teaching Note — the "not elif" bug:** this exact project once shipped
this as `elif`. If a rival's position update were skipped on the frame it
wakes up, it stays drawn at its old, overlapping spot for one more frame. A
frozen car doesn't move, so that overlap doesn't resolve on its own — the
very next collision check finds the same overlap, refreezes both cars, and
repeats forever. Two independent `if` statements fix it: a rival that flips
to `"racing"` in the first `if` gets its position updated in the second
`if`, the same frame.

Finally, update the collision check to freeze both cars, and separate
them:

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
*Expected State: the full game loop works — READY TO RACE, a 3-2-1-GO
countdown, driving, a crash that freezes and blinks both cars for two
seconds instead of ending the run, and a win banner.*

**Teaching Note — why snap to a LANE, not just a gap:** the obvious fix is
pushing the rival back a little in distance to make room. That doesn't
hold: both cars are frozen and don't move again until they wake up, so if
they're still in the same lane, the instant both unfreeze the player is
right back on a collision course — a narrow gap can close again within one
frame at full speed. Snapping each car to its own starting-grid lane
sidesteps this: every car already has a guaranteed-unique lane, so no
amount of speed puts two just-unfrozen cars back in the same spot by
accident.

**Classroom Prompt (For Fast Finishers):** the collision loop `break`s
after the first hit each frame. What happens on a frame where the player
is touching two rivals at once — does the second rival ever get frozen?

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
*Expected State: a full race — READY TO RACE, countdown, driving, a crash
that freezes and blinks both cars for two seconds, and a placement banner
at the finish line.*

**Watch for:** the biggest behavior change from Part 1 is that rivals keep
moving while the player is frozen — make sure students see that a crash
still costs real ground, it just isn't fatal anymore.

**Up Next:** if a class runs long, this state-machine work can spill into
the start of Week 4 without breaking anything — Week 4 builds on this
finished file either way.
