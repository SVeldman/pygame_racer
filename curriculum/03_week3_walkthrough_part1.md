# Week 3, Part 1 Walkthrough — A Pack of Rivals, a Grid, and a Finish Line

Last week you met ONE rival, stored in a single dictionary. This is the
heaviest single session in the whole curriculum — more new vocabulary lands
here than anywhere else (lists of dictionaries, list comprehensions,
`random.shuffle`, a finish line, and placement). Consider splitting your own
delivery across the hour: spawning + movement first, then the finish line +
placement second. Lean on `03_week3_part1.py` itself as an answer key if the
class runs long.

## Step 1: More Rivals, and a Finish Line

Bump `NUM_RIVALS` up, and add a finish distance:

```python
NUM_RIVALS = 3
LANE_COUNT = NUM_RIVALS + 1              # one lane per rival, plus one for you
```

```python
FINISH_DISTANCE = 3900         # matches the "one lap" length used everywhere else
```

Add two new state variables next to `game_state`:
```python
rivals = []                     # filled in by new_race(), below
game_state = "racing"           # "racing" | "crashed" | "won"
race_results = []               # rivals, in the order they crossed the line
player_place = None             # your finish position, once you cross
```
*Expected State: no visible change — `NUM_RIVALS` going from `1` to `3` won't
show up until `new_race()` (Step 2) actually builds three rivals instead of
one.*

**Teaching Note:** `LANE_COUNT` is defined as `NUM_RIVALS + 1`, not typed in
by hand. Every rival needs its own lane, plus one for the player. Push
`NUM_RIVALS` up to `6` later and `LANE_COUNT` — and everything downstream of
it — recalculates on its own.

## Step 2: A Real Starting Grid

This is the big rewrite. Replace `new_race()` entirely:

```python
def new_race():
    """Line every car up at the start (distance 0), each in its own lane."""
    global player_speed, distance_traveled, rivals, game_state
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    race_results = []
    player_place = None

    # ------------------------------------------------------------------
    # THE STARTING GRID
    # ------------------------------------------------------------------
    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_lane, PLAYER_ROW), PLAYER_ROW)

    # random.sample() picks distinct colors, unlike calling random.choice()
    # once per rival - so no two rivals end up looking the same.
    rival_colors = random.sample(RIVAL_COLORS, k=len(grid) - 1)
    rivals = [
        {
            "actor": Actor(color),
            "distance": 0,                         # everyone starts together
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
        }
        for lane_i, color in zip(grid[1:], rival_colors)
    ]
    # Actors don't get positioned until update() runs the movement loop
    # below - but draw() might run BEFORE the first update(). Position them
    # here too, so the very first frame already shows everyone lined up
    # correctly instead of wherever Actor() happened to default to.
    for r in rivals:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)
```
*Expected State: three rivals lined up with you at the start, each in its own
lane. Nobody moves toward a finish line yet — nothing's checking for one.*

**Teaching Note — why `grid[0]` is yours:** `random.shuffle` scrambles the
list of lane numbers in place. Handing the player the first slot and every
rival one of the rest guarantees no two cars ever land in the same lane —
there simply aren't enough slots left for a collision — and the shuffle makes
starting position a fresh draw every race.

**Math Concept — lane index to fraction:** `lane_to_x()` (from Week 2)
expects a fraction from `0.0` to `1.0`, not a raw lane number. `(lane_i +
0.5) / LANE_COUNT` converts index `lane_i` into "the middle of that lane, as
a fraction of the whole road." With `LANE_COUNT = 4`, lane `0` becomes `0.5 /
4 = 0.125`, lane `1` becomes `1.5 / 4 = 0.375`, and so on — four evenly
spaced positions, each centered in its own lane instead of jammed against an
edge.

**The Concept — list comprehensions:** the `rivals = [...]` block is a list
comprehension: "build one dictionary like *this*, for every `(lane_i,
color)` pair in `zip(grid[1:], rival_colors)`." `zip()` pairs up two lists
item-by-item — the first leftover lane number with the first sampled color,
the second with the second, and so on. If this syntax is new, show the slow
way first: a `for` loop appending to an empty list one dictionary at a time.
Then show that the comprehension does exactly the same thing in fewer lines.

**Classroom Demo:** comment out `random.shuffle(grid)` and run a few races
back to back. The grid order stays identical every time — you always start
in the same lane — which makes "the shuffle is what randomizes starting
position" concrete before you put the line back.

## Step 3: Draw Lane Dividers and the Finish Line

In `draw()`'s road-drawing loop, replace the single centre dash with one
dash *per lane boundary*:

```python
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)
```
*Expected State: dashed lines now mark every lane boundary, instead of one
dash down the middle of the road.*

**Math Concept — counting lane boundaries:** a road with `LANE_COUNT` lanes
has exactly `LANE_COUNT - 1` boundaries *between* them (4 lanes → 3
dividers, not 4). `range(1, LANE_COUNT)` produces `1, 2, 3` for `LANE_COUNT
= 4` — one number per boundary, skipping `0` (the road's own left edge,
already drawn by the shoulder/tarmac rectangles).

**The Geometry:** `divider_x` starts at the road's own left edge (`center_x
- ROAD_WIDTH // 2` — the same expression `road_left()` computes) and walks
right by `LANE_WIDTH` pixels per boundary. Boundary `1` sits one lane-width
in, boundary `2` sits two lane-widths in, and so on — exactly where each
lane meets its neighbor.

After the road-drawing loop (but still inside `draw()`, before the cars are
drawn), add the finish line:

```python
    # The checkered finish line.
    finish_y = row_at(FINISH_DISTANCE)
    if -20 < finish_y < HEIGHT:
        left = road_center_x(finish_y) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)
```

**Math Concept — checkered flag with a loop:** `row_at(FINISH_DISTANCE)`
reuses last week's trick to find *where on screen* the finish line currently
is — it's just another fixed distance, exactly like a rival's distance,
converted to a row. The `for i in range(0, ROAD_WIDTH, 20)` loop then walks
across the whole width of the road in 20-pixel steps, alternating white and
black with the same `(i // 20) % 2 == 0` pattern from Week 1's dashed line.
The only difference is it alternates *across* the road instead of *down* it.

**Classroom Demo:** change the step size from `20` to `40` in both the
`range()` call and the rectangle width, and rerun. Bigger checker squares
make the alternating pattern obvious without touching the underlying logic.

Update the rival-drawing loop to handle a list instead of one dictionary:
```python
    for r in rivals:
        r["actor"].draw()
    player.draw()
```

## Mid-Session Checkpoint: A Pack, a Grid, a Finish Line — Not Yet Moving as a Pack

This is a natural stopping point if a group is running behind — save the
rest for the start of Part 2's session. At this stage, the full Python
script should look something like this:

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
game_state = "racing"
race_results = []
player_place = None


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
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    race_results = []
    player_place = None

    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_lane, PLAYER_ROW), PLAYER_ROW)

    rival_colors = random.sample(RIVAL_COLORS, k=len(grid) - 1)
    rivals = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
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
        r["actor"].draw()
    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
                     fontsize=30, color="white")

    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")


def _banner(title, subtitle):
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=60, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=30, color="white")


### UPDATE
def update():
    global player_speed, distance_traveled, game_state

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

    # Temporary - just enough to keep the pack moving and crash-able. Step 5
    # replaces this with a version that also tracks who's finished.
    for r in rivals:
        r["distance"] += r["base_speed"]
        y = row_at(r["distance"])
        r["actor"].pos = (lane_to_x(r["lane"], y), y)

    for r in rivals:
        if player.colliderect(r["actor"]):
            game_state = "crashed"
```
*Expected State: a full grid of four cars, lane dividers, and a checkered
finish line scrolling into view. Nobody's placement is tracked yet — driving
past the finish line does nothing, and there's no way to win.*

The movement loop at the end of `update()` is a deliberate placeholder —
just enough to keep the pack moving and crashable until Step 5 replaces it
with real finish-line tracking.

## Step 4: Turning a Number into "1ST" / "2ND" / "3RD"

Add this small helper function anywhere below `draw()`:

```python
def _ordinal(n):
    """Turns 1 into '1ST', 2 into '2ND', 3 into '3RD', 4 into '4TH', and so
    on (11-20 are all 'TH', which is why they're special-cased first)."""
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"
```

Update `draw()`'s end-of-race banner to use it:
```python
    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")
```
*Expected State: no visible change — `player_place` doesn't get set until
Step 5, so the `"won"` branch never runs yet.*

**Math Concept — special-casing 11-20:** English ordinals mostly depend on
the *last digit* (`1st`, `2nd`, `3rd`, `4th`...), but `11th`, `12th`, and
`13th` break that pattern — they're never "11st" or "12nd." Checking `10 <=
n % 100 <= 20` catches the whole 11-20 range (and 111-120, 211-220, and so
on) before the last-digit rule below it ever runs.

## Step 5: Move the Whole Pack, and Track Who Finished

Replace the single-rival movement code at the end of `update()` with a loop
over the list, plus a check for anyone crossing the line:

```python
    # Move every rival and note anyone who's just crossed the line. Because
    # this is a normal `for` loop over a LIST, adding a 4th, 5th, or 20th
    # rival to NUM_RIVALS needs no other changes anywhere in this function.
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

    # Your place is "how many rivals got there before you, plus one."
    if distance_traveled >= FINISH_DISTANCE:
        player_place = len(race_results) + 1
        game_state = "won"
```

You'll need `player_place` added to the `global` line at the top of
`update()`.
*Expected State: rivals cross the finish line and register their place;
drive across `FINISH_DISTANCE` yourself and the "YOU WIN!" / "YOU FINISHED
Nth!" banner appears.*

**Teaching Note — one-time finish, reliable placement:** `not r["finished"]`
makes crossing the line a one-time event per rival — without it, a rival
sitting past `FINISH_DISTANCE` would re-append itself to `race_results`
every single frame for the rest of the race. That one-time append is also
what makes `player_place` reliable: `race_results` only ever holds rivals
that finished *before* the current frame, so "how many rivals already
finished" is accurate at the exact instant the player crosses — no separate
bookkeeping needed.

**Classroom Prompt (For Fast Finishers):** two rivals could, in principle,
cross the finish line on the same frame. `race_results.append(r)` runs in
list order, so whichever rival comes first in the `rivals` list wins the
tie. Ask fast finishers whether that's fair, and how they'd break the tie
differently (distance is identical, so what else could decide it?).

## Checkpoint: Final Code for Week 3, Part 1

The full script should now match `03_week3_part1.py` — a full grid of
rivals, a finish line, and a placement banner. Crashing still just ends the
run for now (`"CRASHED!"`, SPACE to retry) — making that gentler is the next
part of this lesson.

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
game_state = "racing"
race_results = []
player_place = None


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
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    race_results = []
    player_place = None

    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_lane, PLAYER_ROW), PLAYER_ROW)

    rival_colors = random.sample(RIVAL_COLORS, k=len(grid) - 1)
    rivals = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
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
        r["actor"].draw()
    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} / {FINISH_DISTANCE} m",
                     topleft=(10, 40), fontsize=30, color="white")

    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")


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
*Expected State: a full grid of cars racing to a checkered finish line, with
a "YOU WIN!" or "YOU FINISHED Nth!" banner on crossing it. Crashing still
just ends the run.*

**Watch for:** this file is dense. If a group is behind, stop after Step 3
(rivals racing, no finish line yet) and pick up Steps 4-5 (finish line +
placement) at the very start of Part 2's session instead. Nothing about Part
2's state machine depends on exactly when the placement logic gets typed in
— only that it's there by the time Part 2 starts building on top of it.
