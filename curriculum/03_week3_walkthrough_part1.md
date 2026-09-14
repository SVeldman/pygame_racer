# Week 3, Part 1 Walkthrough — A Pack of Rivals, a Grid, and a Finish Line

Last week you met ONE rival, stored in a single dictionary. This is the
heaviest single session in the whole curriculum — more new vocabulary lands
here than anywhere else (lists of dictionaries, list comprehensions,
`random.shuffle`, a finish line, and placement). **Consider splitting your
own delivery across the hour: spawning + movement first, then the finish
line + placement second**, and lean on `03_week3_part1.py` itself as an
answer key if the class runs long.


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

**Nothing to run yet** — `NUM_RIVALS` going from `1` to `3` will show up once
`new_race()` (Step 2) actually builds three rivals instead of one.

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

**Why `grid[0]` for you, and `grid[1:]` for everyone else:** `random.shuffle`
scrambles the list of lane numbers *in place*. Handing the player the first
slot and every rival one of the rest guarantees no two cars ever get the
same lane — there simply aren't enough slots for a collision, and the
shuffle makes it a different draw every race.

**Math note — turning a lane index into a lane fraction:** `lane_to_x()`
(from Week 2) expects a fraction from `0.0` to `1.0`, not a raw lane number.
`(lane_i + 0.5) / LANE_COUNT` converts index `lane_i` into "the *middle* of
that lane, as a fraction of the whole road." With `LANE_COUNT = 4`, lane `0`
becomes `0.5 / 4 = 0.125`, lane `1` becomes `1.5 / 4 = 0.375`, and so on —
four evenly spaced positions across the road, each one centred in its own
lane rather than jammed against an edge.

**The idea to put on the board — a list comprehension:** the `rivals = [...]`
block is a list comprehension: "build one dictionary like *this*, for every
`(lane_i, color)` pair in `zip(grid[1:], rival_colors)`." `zip()` pairs up
two lists item-by-item — the first leftover lane number with the first
sampled color, the second with the second, and so on. If this syntax is new,
it can help to first show the *slow* way (a `for` loop appending to an empty
list one dictionary at a time) and then show that the comprehension does the
exact same thing in fewer lines.

**Running the game now shows three rivals lined up with you at the start,
each in their own lane** — but they don't move toward a finish line yet, and
there's nothing checking for one.

## Step 3: Draw Lane Dividers and the Finish Line

In `draw()`'s road-drawing loop, replace the single centre dash with one
dash *per lane boundary*:

```python
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)
```

**Why `range(1, LANE_COUNT)`:** a road with `LANE_COUNT` lanes has exactly
`LANE_COUNT - 1` *boundaries between* them (4 lanes → 3 dividers, not 4) —
`range(1, LANE_COUNT)` produces `1, 2, 3` for `LANE_COUNT = 4`, one number
per boundary, skipping `0` (the road's own left edge, which is already drawn
by the shoulder/tarmac rectangles).

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

**Math note — checkered flag with a loop:** `row_at(FINISH_DISTANCE)` reuses
last week's trick to find *where on screen* the finish line currently is —
it's just another fixed distance, exactly like a rival's distance, converted
to a row. The `for i in range(0, ROAD_WIDTH, 20)` loop then walks across the
whole width of the road in 20-pixel steps, alternating white and black using
the same `(i // 20) % 2 == 0` pattern from Week 1's dashed line — the only
difference is it's alternating *across* the road instead of *down* it.

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

Run it and there's a full grid of four cars, lane dividers, and a real
checkered finish line that scrolls into view — genuinely close to the
finished game. But nobody's placement is tracked yet: driving past the
finish line does nothing, and there's no way to actually win. The movement
loop above is a deliberately bare-bones stand-in for what Step 5 builds —
it's here only so the pack has somewhere to go before finish-line tracking
exists.

## Step 4: Turning a Number into "1ST" / "2ND" / "3RD"

Add this small helper function anywhere below `draw()`:

```python
def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"
```
This turns 1 into '1ST', 2 into '2ND', 3 into '3RD', 4 into '4TH', and so
on (11-20 are all 'TH', which is why they're special-cased first).

**Why 11-20 need special handling:** English ordinals mostly depend on the
*last digit* (`1st`, `2nd`, `3rd`, `4th`...), but `11th`, `12th`, and `13th`
break that pattern — they're never "11st" or "12nd." Checking `10 <= n % 100
<= 20` catches the whole 11-20 range (and 111-120, 211-220, and so on) before
the last-digit rule below it ever runs.

Update `draw()`'s end-of-race banner to use it:
```python
    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")
```

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

**Why `not r["finished"]` guards the append:** without it, a rival that's
already crossed the line would keep re-appending itself to `race_results`
every single frame for the rest of the race (its `distance` stays above
`FINISH_DISTANCE` forever after crossing). The flag makes "you crossed the
line" a one-time event per rival, exactly like a checkbox that only gets
ticked once.

**The idea to put on the board:** every car — rivals and player alike —
starts at `distance = 0` on the grid. Because `race_results` only ever
contains rivals that finished *before* the current frame, "how many rivals
already finished" is always accurate at the exact moment the player crosses,
with no extra bookkeeping needed.

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

**Watch for:** this file is dense. If a group is behind, it's completely
fine to stop after Step 3 (rivals racing, no finish line yet) and pick up
Steps 4-5 (finish line + placement) at the very start of Part 2's session
instead — nothing about Part 2's state machine depends on exactly when the
placement logic gets typed in, only that it's there by the time Part 2
starts building on top of it.
