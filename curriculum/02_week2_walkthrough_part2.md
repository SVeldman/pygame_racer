# Week 2, Part 2 Walkthrough — You Meet Your First Rival

Part 1 already has the road scrolling, throttle/brake, and
`distance_traveled`. This session uses that same distance to give another
car its own, independent position — the single most important trick in the
whole game. There's no finish line and no "winning" yet; the goal is simply
to share the road with one other car and not hit it.


## Step 1: New Knobs, and a Computed Window Size

Add `import random` at the very top of the file (before any other code).
Then update the tuning knobs block:

```python
NUM_RIVALS = 1                           # just one other car this week
LANE_COUNT = NUM_RIVALS + 1              # one lane for the rival, one for you
LANE_WIDTH = 110                         # width of a single lane
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT     # total width of the tarmac
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
```

And replace the plain `WIDTH = 800` with a computed version, placed after
the block above:

```python
# ---------------------------------------------------------------------------
# WINDOW SIZE - NOW COMPUTED, NOT HARD-CODED
# ---------------------------------------------------------------------------
# Instead of picking a WIDTH by hand, we calculate one that's just wide
# enough for the road plus a little grass on each side. This matters a lot
# starting next week, when NUM_RIVALS grows and the road needs more lanes -
# changing ONE number (NUM_RIVALS) will automatically resize the window to
# fit, instead of us having to guess a new WIDTH by hand every time.
GRASS_MARGIN = 200        # how much grass to leave visible on each side
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
```

**Why `ROAD_WIDTH` is a formula now:** `ROAD_WIDTH` used to be a flat number
(`220`). Now it's `LANE_WIDTH * LANE_COUNT` — the road is exactly as many
110-pixel lanes as there are cars needing one. With `NUM_RIVALS = 1`,
`LANE_COUNT = 2`, so `ROAD_WIDTH = 220`, the same value as before — nothing
*visually* changes yet, but the number is no longer an accident; it's
derived from how many cars are racing.

**At this point, running the game shows the same game as before** (the
window might be a slightly different width than `800` depending on the
formula above, but there's still no rival on screen).

## Step 2: A State Variable, and Turning a Lane Number into a Pixel

Add a new state variable next to `player_speed`:
```python
game_state = "racing"          # "racing" | "crashed"
```
Now that a rival can crash into you, `update()` needs a way to remember
"the race has stopped" instead of just letting `player_speed` keep changing
— that's what `game_state` tracks, and later steps check it before moving
anything.

And this new function, right after `on_shoulder()`:
```python
def lane_to_x(lane, y):
    """Turn a lane FRACTION (0.0 = left edge of road, 1.0 = right edge) into
    an actual X pixel position, at screen row y."""
    return road_left(y) + lane * ROAD_WIDTH
```

**Why a fraction, not a lane number?** `lane_to_x(0.0, y)` lands exactly on
the road's left edge, `lane_to_x(1.0, y)` on the right edge, and `0.5` is
dead centre — any car's horizontal position can be described this way
without caring how wide the road is in pixels. That's what lets a rival's
`"lane"` value stay meaningful even later, when `ROAD_WIDTH` grows as more
rivals join.

## Step 3: `row_at()` — the Trick Solved Backwards

Add this function right after `dist_at()`, and read the comment above it
carefully:

```python
def row_at(dist):
    """The exact opposite question: which screen row is track distance
    `dist` drawn at, right now? This is `dist_at` solved backwards.
    """
    return PLAYER_ROW - (dist - distance_traveled)
```

**Math note — solving for the other variable.** Recall from Part 1:
`dist_at(y) = distance_traveled + (PLAYER_ROW - y)`. That answers "given a
screen row, what distance is drawn there?" But a rival doesn't have a screen
row to start with — it has its own *distance*, and we need to work out
*where on screen* that puts it. That means we need the same equation solved
for `y` instead of for the distance. A little algebra:

```
dist = distance_traveled + (PLAYER_ROW - y)
dist - distance_traveled = PLAYER_ROW - y
y = PLAYER_ROW - (dist - distance_traveled)
```

That last line is exactly `row_at()`. Try a number: if `distance_traveled =
1000` and a rival's `dist = 1000` too (right next to you), `row_at(1000) =
480 - (1000 - 1000) = 480` — drawn right at `PLAYER_ROW`, i.e. right next to
your own car. If the rival is 50 metres ahead (`dist = 1050`), `row_at(1050)
= 480 - 50 = 430` — 50 pixels *higher* on screen, i.e. further ahead, which
matches intuition.

## Step 4: Build the Rival with `new_race()`

Add this function, and call it once right after defining it:

```python
def new_race():
    """Reset everything back to the start."""
    global player_speed, distance_traveled, rival, game_state
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    player.pos = (lane_to_x(0.75, PLAYER_ROW), PLAYER_ROW)
    rival = {
        "actor": Actor(random.choice(RIVAL_COLORS)),
        "distance": 0,              # the rival starts even with you, not ahead
        "lane": 0.25,               # pick a lane that isn't where you start
        "base_speed": 6.5,          # the rival's own, constant, forward speed
    }


new_race()
```

**Why a function, instead of just setting these variables directly at the
top of the file?** Because we're going to need to reset the race after a
crash — pressing SPACE (added in Step 6) calls this same function again.
Wrapping "set everything back to a fresh start" in one function means there's
exactly one place that logic lives, whether it's the very first race or the
fifth retry.

**Why a dictionary for the rival?** `rival` bundles four related values —
its sprite, its distance, its lane, and its speed — into one object instead
of four separate loose variables (`rival_actor`, `rival_distance`, and so
on). Next week, when there's more than one rival, this same shape becomes
one entry in a *list* of dictionaries — this is the small-scale version of
that idea.

## Step 5: Draw the Rival, and a Crash Banner

In `draw()`, draw the rival right before the player:
```python
    rival["actor"].draw()
    player.draw()
```

Then, after the HUD text, add:
```python
    if game_state == "crashed":
        _banner("CRASHED!", "Press SPACE to try again")
```

And add this small helper function anywhere below `draw()`:
```python
def _banner(title, subtitle):
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=60, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=30, color="white")
```

## Mid-Session Checkpoint: A Rival That Just... Sits There

At this stage, the full Python script should look something like this:

```python
import random

### CONSTANTS
NUM_RIVALS = 1
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

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### GAME STATE
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
game_state = "racing"


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
    global player_speed, distance_traveled, rival, game_state
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    player.pos = (lane_to_x(0.75, PLAYER_ROW), PLAYER_ROW)
    rival = {
        "actor": Actor(random.choice(RIVAL_COLORS)),
        "distance": 0,
        "lane": 0.25,
        "base_speed": 6.5,
    }


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
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    rival["actor"].draw()
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
    global player_speed, distance_traveled

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

Run it now and the rival is visible for the first time — parked in its lane,
500m up the road — but it never moves, and driving straight through it does
nothing at all. That's exactly what's expected: `new_race()` builds the
rival dict and `draw()` shows it, but `update()` doesn't know it exists yet.
Step 6 is what makes it move (by its own `base_speed`) and makes it possible
to crash into.

## Step 6: Relative Speed, and Handling a Crash

First, make `game_state != "racing"` short-circuit `update()` — add this at
the very top of the function body (after the `global` line):

```python
    if game_state != "racing":
        if keyboard.space:
            new_race()
        return
```

**Why `return` here:** once crashed, none of the driving code below should
run at all — the car shouldn't keep accelerating or the rival keep moving
while a "CRASHED!" banner is up. `return` exits the function immediately,
and the only thing checked is whether SPACE was pressed to start over.

Then, at the very end of `update()` (after `distance_traveled +=
player_speed`), add the rival's own movement and the collision check:

```python
    # ---------------------------------------------------------------------
    # RELATIVE SPEED - THE CORE TRICK
    # ---------------------------------------------------------------------
    # The rival has its OWN distance, which grows by its OWN base_speed -
    # completely independently of yours. Every frame we work out where that
    # puts it on screen right now with row_at(), and place its Actor there.
    #
    #   * If you're driving FASTER than the rival's base_speed, the GAP
    #     between your distance and its distance shrinks every frame, which
    #     means row_at() returns a bigger row number (further down the
    #     screen) - the rival appears to drift toward you and then past you.
    #   * If you're SLOWER, the gap grows, row_at() returns a smaller row
    #     number, and the rival pulls away up the screen.
    #
    # This is the whole trick behind every car in this game "racing" you -
    # nothing is being steered by an AI, it's just two independent numbers
    # (your distance and the rival's) being compared every frame.
    rival["distance"] += rival["base_speed"]
    rival_y = row_at(rival["distance"])
    rival["actor"].pos = (lane_to_x(rival["lane"], rival_y), rival_y)

    if player.colliderect(rival["actor"]):
        game_state = "crashed"
```

You'll need `game_state` added to the `global` line at the top of `update()`.

**The idea to sit with:** the rival never "knows" where you are, and nothing
is steering it toward or away from you. It just keeps adding `base_speed` to
its own distance, forever, at a constant rate. Every frame, `row_at()`
converts the *gap* between that distance and yours into a screen position.
Speed up, and the gap shrinks — the rival visibly comes toward you and slides
past. Slow down, and the gap grows — it pulls away. That single comparison
is the entire "AI" for every opponent in this whole project, all the way
through Week 5.

## Checkpoint: Final Code for Week 2, Part 2

The full script should now match `02_week2_part2.py` — one rival, sharing the
road with its own lane, moving by relative speed, with a crash ending the
run and SPACE starting over.

```python
import random

### CONSTANTS
NUM_RIVALS = 1
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

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### GAME STATE
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
game_state = "racing"


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
    global player_speed, distance_traveled, rival, game_state
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "racing"
    player.pos = (lane_to_x(0.75, PLAYER_ROW), PLAYER_ROW)
    rival = {
        "actor": Actor(random.choice(RIVAL_COLORS)),
        "distance": 0,
        "lane": 0.25,
        "base_speed": 6.5,
    }


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
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)

    rival["actor"].draw()
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

    rival["distance"] += rival["base_speed"]
    rival_y = row_at(rival["distance"])
    rival["actor"].pos = (lane_to_x(rival["lane"], rival_y), rival_y)

    if player.colliderect(rival["actor"]):
        game_state = "crashed"
```

**Watch for:** `WIDTH` is a formula now, not a plain number — that matters a
lot starting next week when `NUM_RIVALS` grows past `1` and the window needs
to get wider to fit more lanes automatically. There's still no finish line
and no "winning" — that's next week, once there's a real pack of rivals to
place, not just one.
