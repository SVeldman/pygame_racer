# Week 4, Part 1 Walkthrough — The Road Curves!

Every week so far, `road_center_x()` has returned the exact same number no
matter what row you pass it — the road has always been perfectly straight.
That was deliberate: `road_left()`, `road_right()`, `on_road()`,
`on_shoulder()`, and every rival's position all ask `road_center_x()` where
the road is, instead of assuming they know.

**Concept: one seam, one change.** This part rewrites `road_center_x()` to
read from a list of track segments instead of returning a constant. Because
every other function already asks `road_center_x()` for the answer instead
of computing its own, that single rewrite is the entire lesson — nothing
else in the file changes. Budget real time for it anyway: segment-lookup
and linear interpolation are new math, not just new code, and students need
room to sit with that before it clicks.

## Step 1: A Short Demo Track

Replace the flat `FINISH_DISTANCE = 3900` line with:

```python
# ---------------------------------------------------------------------------
# THE TRACK
# ---------------------------------------------------------------------------
CENTER = WIDTH // 2
TRACK = [
    (400, CENTER),          # a straight starting stretch
    (400, CENTER - 140),    # curve left
    (400, CENTER),          # curve back to the middle
]

FINISH_DISTANCE = sum(length for length, _ in TRACK)
```
*Expected State: no visible change — `TRACK` exists, but nothing reads from
it until Step 3.*

**Teaching Note:** each entry in `TRACK` is `(length, end_center)` — how far
this stretch runs, and where the road's center should sit by the end of it.
This demo track is drive straight, curve left, curve back to center.
`CENTER` is just a reference point for measuring curves against, so the
whole track shifts automatically if `WIDTH` ever changes. `FINISH_DISTANCE
= sum(length for length, _ in TRACK)` puts the finish line at the exact end
of the last described segment, so the race never runs past `TRACK` into a
stretch with no curve defined for it.

## Step 2: Walking the Track to Find "Which Segment Am I In?"

Add this function anywhere above `road_center_x()`:

```python
def _segment_at(dist):
    """Find which TRACK segment covers `dist`, and how far through it we
    are (as a fraction from 0.0 at the start of the segment to 1.0 at the
    end). Returns (segment_start_center, segment_end_center, fraction)."""
    start_center = CENTER
    covered = 0
    for length, end_center in TRACK:
        if dist < covered + length:
            fraction = (dist - covered) / length
            return start_center, end_center, fraction
        covered += length
        start_center = end_center
    return start_center, start_center, 1.0
```
*Expected State: no visible change — this function isn't called from
anywhere yet.*

**Math Concept — walking a list of lengths to find a position:** `covered`
tracks how much of the track has been accounted for so far, starting at
`0`. For each segment, ask "does `dist` fall before this segment ends
(`covered + length`)?"
- If yes, this is the segment: `fraction` is how far into it `dist` sits,
  from `0.0` (just entered) to `1.0` (about to leave).
- If no, add this segment's `length` to `covered` and move to the next
  one, carrying its `end_center` forward as the next segment's
  `start_center` — that hand-off is what makes the curve continuous
  instead of jumping between segments.

Walk it by hand with the demo track and `dist = 500`:
- Segment 1 is `(400, CENTER)`. Is `500 < 0 + 400`? No. `covered` becomes
  `400`, `start_center` becomes `CENTER`.
- Segment 2 is `(400, CENTER - 140)`. Is `500 < 400 + 400 = 800`? Yes.
  `fraction = (500 - 400) / 400 = 0.25` — a quarter of the way through the
  curve-left segment. Returns `(CENTER, CENTER - 140, 0.25)`.

The final line, `return start_center, start_center, 1.0`, only runs once
`dist` is past the whole track's length (`1200` here) — the loop finished
without ever returning, so it holds the last segment's center steady
instead of crashing.

**Classroom Prompt (For Fast Finishers):** trace `_segment_at(1300)` by
hand against this demo track before running it. Which branch returns, and
what does it return?

## Step 3: Linear Interpolation

Add this function right after `_segment_at()`:

```python
def center_x_at_distance(dist):
    """Where should the road's centre be, at this distance along the track?
    We slide smoothly from the segment's starting centre to its ending
    centre as `fraction` goes from 0 to 1 - this is called LINEAR
    INTERPOLATION, and it's the same idea as "80% of the way between A and
    B is A + 0.8 * (B - A)."
    """
    start_center, end_center, fraction = _segment_at(dist)
    return start_center + (end_center - start_center) * fraction
```
*Expected State: no visible change — this function isn't called from
anywhere yet either.*

**Math Concept — linear interpolation:** `end_center - start_center` is the
total distance to travel across the whole segment. Multiplying that by
`fraction` scales it down to "how far we should have travelled by now."
Adding that onto `start_center` gives the actual position — the docstring's
"80% of the way from A to B" formula, applied to road centers instead of
two arbitrary points.

Concretely, using the `(CENTER, CENTER - 140, 0.25)` result from Step 2
(say `CENTER = 400`): `center_x_at_distance = 400 + (260 - 400) * 0.25 =
400 - 35 = 365`. A quarter of the way through a curve that eventually
reaches `260`, the road's center sits at `365` — a quarter of the way
there. At `fraction = 0.0` this always returns exactly `start_center`; at
`fraction = 1.0` it always returns exactly `end_center`, so the curve is
smooth and continuous the whole way between.

## Step 4: A Derived Yes/No From the Same Data

```python
def is_turn_at(dist):
    """True if this point in the track is part of a curve (its segment's
    start and end centres are different) rather than a straight."""
    start_center, end_center, _ = _segment_at(dist)
    return start_center != end_center
```
*Expected State: no visible change — `is_turn_at()` isn't called from
anywhere yet.*

**Teaching Note:** `_segment_at()` already knows everything needed to
answer "is this a turn?" — a segment is a turn exactly when its start and
end centers differ. `is_turn_at()` doesn't recompute anything; it just asks
the same question a different way.

**Classroom Prompt (For Fast Finishers):** add a fourth entry to `TRACK`
that curves back out to the right. Before running it, predict which of the
four segments `is_turn_at()` will report as a turn versus a straight.

## Mid-Session Checkpoint: The Math Works, Nothing Uses It Yet

At this stage, the full Python script should look something like this:

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

RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

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
    (400, CENTER),
    (400, CENTER - 140),
    (400, CENTER),
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
*Expected State: nothing looks different from last week — `road_center_x()`
still returns `WIDTH // 2`, so the road is as straight as ever.*

`_segment_at()`, `center_x_at_distance()`, and `is_turn_at()` are fully
built and correct even though nothing on screen uses them yet — call
`center_x_at_distance(500)` from a REPL right now and it returns a real
answer. The curve-math engine exists and works; it's just not wired up yet.
Step 5 wires it up.

## Step 5: The One Line That Changes Everything

Replace `road_center_x()`'s body:

```python
def road_center_x(y):
    return center_x_at_distance(dist_at(y))
```
*Expected State: the road curves left and back, and every rival tracks the
bend automatically — no other code changed.*

**The Concept:** every previous file had `return WIDTH // 2` here. Now it
asks `TRACK`, through `center_x_at_distance()`, where the road should be at
whatever distance is being drawn at row `y`. `road_left()`, `road_right()`,
`on_road()`, `on_shoulder()`, and every rival's `lane_to_x()` call all still
call this same function — none of them changed. That's the payoff of
insisting, since Week 1, that everything ask `road_center_x()` instead of
assuming it knew the answer.

**Classroom Demo:** have the class scroll through the rest of the file and
count how many function *bodies* changed to make the road curve. The answer
is one — this one.

## Step 6: Warn About Turns

Add one more HUD line, in `draw()`:

```python
    elif game_state == "racing" and is_turn_at(distance_traveled):
        screen.draw.text("TURN - stay on the road!", midtop=(WIDTH // 2, 10),
                         fontsize=32, color=(255, 220, 120))
```
*Expected State: a yellow "TURN - stay on the road!" warning appears near
the top of the screen only while `distance_traveled` sits inside a curved
segment.*

**Teaching Note:** this sits as an `elif` alongside the existing "CRASHED!
Recovering" check, since only one banner should show at a time. Off-road
physics don't change on a curve — the same shoulder and rough-speed caps
from Week 1 apply, unmodified. This text is a heads-up, not a new penalty.
Turns are just easier to drift off of, since the road itself is moving out
from under the car.

**Classroom Demo:** temporarily change that `elif` to a plain `if` and
crash while inside a turn — both banners try to draw at once and overlap.
Restore the `elif` and show the fix.

## Checkpoint: Final Code for Week 4, Part 1

The full script should now match `04_week4_part1.py` — a small 3-segment
demo curve, with every rival following it automatically.

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

RIVAL_COLORS = ["car_blue", "car_green", "car_yellow"]

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
    (400, CENTER),
    (400, CENTER - 140),
    (400, CENTER),
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
*Expected State: player and rivals race down a curving three-segment track
— straight, left bend, straight — with the TURN warning showing during the
bend and every other rule (speed, shoulders, crashes, finishing) unchanged
from Week 3.*

**Watch for:** if a custom `TRACK` a student writes is shorter than
`FINISH_DISTANCE`, the road holds its last curve's center steady for the
rest of the race — that's `_segment_at()`'s fallback from Step 2, not a
bug, but it can look like one. This file's `TRACK` is intentionally tiny
(three segments) so the new idea is easy to see in isolation; Part 2 swaps
in a full multi-turn lap using the exact same mechanism.
