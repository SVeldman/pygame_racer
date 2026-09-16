# Week 2, Part 2 Walkthrough — You Meet Your First Rival

Part 1 already has the road scrolling, throttle/brake, and
`distance_traveled`. This session reuses that same distance to give another
car its own, independent position on the road. There's no finish line and
no "winning" yet — the goal is simply to share the road with one other car
and not hit it.

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
HEIGHT = 600
```
*Expected State: the same game as before — the window may render at a
slightly different width than 800px depending on the formula above, but
there's still no rival on screen.*

**Teaching Note — why `WIDTH` and `HEIGHT` moved:** in Week 1, `WIDTH` and
`HEIGHT` sat at the very top of the file as flat numbers. `WIDTH` can't stay
there anymore because it's now a formula built from `ROAD_WIDTH`, `SHOULDER_WIDTH`,
and `GRASS_MARGIN`, and Python has to see those on earlier lines before it
can compute `WIDTH` from them. `HEIGHT` doesn't depend on anything, so it
didn't *have* to move — it's brought down here purely so the two window-size
constants stay next to each other instead of splitting `WIDTH` and `HEIGHT`
across two different parts of the file.

**Teaching Note:** two numbers changed from flat constants to formulas.
- `ROAD_WIDTH` used to be a flat `220`. Now it's `LANE_WIDTH * LANE_COUNT` —
  the road is exactly as many 110-pixel lanes as there are cars needing
  one. With `NUM_RIVALS = 1`, `LANE_COUNT = 2`, so `ROAD_WIDTH` still comes
  out to `220` — nothing visually changes yet, but the number is now
  derived from how many cars are racing instead of typed by hand.
- `WIDTH` is now `ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN`
  instead of a flat `800`. Next week, when `NUM_RIVALS` grows and the road
  needs more lanes, the window resizes itself automatically — no
  hand-editing `WIDTH` every time the lane count changes.

**Classroom Prompt (For Fast Finishers):** have early finishers hand-compute
`LANE_COUNT`, `ROAD_WIDTH`, and `WIDTH` for `NUM_RIVALS = 3` before running
anything. It's a quick check for whether the formulas actually landed,
versus just being trusted to work.

## Step 2: A State Variable, and Turning a Lane Number into a Pixel

Add a new state variable next to `player_speed`:
```python
game_state = "racing"          # "racing" | "crashed"
```

And this new function, right after `on_shoulder()`:
```python
def lane_to_x(lane, y):
    """Turn a lane FRACTION (0.0 = left edge of road, 1.0 = right edge) into
    an actual X pixel position, at screen row y."""
    return road_left(y) + lane * ROAD_WIDTH
```
*Expected State: no visible change — both additions are groundwork for the
rival that shows up in Step 4.*

**Teaching Note:** `game_state` gives `update()` a way to remember "the race
has stopped." Once a rival can crash into you, something has to stop
`player_speed` and the rival's movement from continuing to change after a
crash — later steps check this variable before touching anything.

**The Concept:** why a fraction, not a lane number? `lane_to_x(0.0, y)`
lands exactly on the road's left edge, `lane_to_x(1.0, y)` on the right
edge, and `0.5` is dead center — a car's horizontal position can be
described this way without caring how wide the road is in pixels. That's
what lets a rival's `"lane"` value stay meaningful even later, when
`ROAD_WIDTH` grows as more rivals join.

## Step 3: `row_at()` — the Trick Solved Backwards

Add this function right after `dist_at()`:

```python
def row_at(dist):
    """The exact opposite of dist_at(): which screen row is track distance
    `dist` drawn at, right now?"""
    return PLAYER_ROW - (dist - distance_traveled)
```
*Expected State: no visible change — `row_at()` has no caller until Step 4
builds the rival.*

**Math Concept — solving for the other variable:** `dist_at(y) =
distance_traveled + (PLAYER_ROW - y)` answers "given a screen row, what
distance is drawn there?" A rival doesn't have a screen row to start with
— it has its own distance, and we need the row that distance lands on.
That means solving the same equation for `y` instead of for the distance:

```
dist = distance_traveled + (PLAYER_ROW - y)
dist - distance_traveled = PLAYER_ROW - y
y = PLAYER_ROW - (dist - distance_traveled)
```

That last line is `row_at()`. Try a number: if `distance_traveled = 1000`
and a rival's `dist = 1000` too (right next to you), `row_at(1000) = 480 -
(1000 - 1000) = 480` — drawn right at `PLAYER_ROW`, i.e. right next to your
own car. If the rival is 50 metres ahead (`dist = 1050`), `row_at(1050) =
480 - 50 = 430` — 50 pixels *higher* on screen, i.e. further ahead, which
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
*Expected State: no visible change yet — `new_race()` builds the rival
dict, but `draw()` doesn't show it until Step 5.*

**Teaching Note:** why a function, instead of just setting these variables
directly at the top of the file? Because the race needs to reset after a
crash — pressing SPACE (added in Step 6) calls this same function again.
Wrapping "set everything back to a fresh start" in one function means
there's exactly one place that logic lives, whether it's the first race or
the fifth retry.

**The Concept:** why a dictionary for the rival? `rival` bundles four
related values — its sprite, its distance, its lane, and its speed — into
one object instead of four separate loose variables (`rival_actor`,
`rival_distance`, and so on). Next week, when there's more than one rival,
this same shape becomes one entry in a *list* of dictionaries — this is the
small-scale version of that idea.

**Classroom Demo:** restart the script a few times and point out the
rival's sprite color changes each run — that's `random.choice(RIVAL_COLORS)`
picking a new image every call to `new_race()`.

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
*Expected State: the rival's sprite is now visible on screen — still
stationary, since `update()` doesn't move it yet. The "CRASHED!" banner
exists in code but never appears, since `game_state` never becomes
`"crashed"` until Step 6.*

**Teaching Note:** the rival is drawn before the player, the same ordering
rule as Week 1's grass-before-car draw order — whichever `.draw()` call
runs last ends up on top if the two sprites ever overlap.

**The Geometry:** the banner box is `120` pixels tall, so it's centered
vertically by starting `60` pixels above the middle of the screen
(`HEIGHT // 2 - 60`). The title and subtitle text use `center=` instead of
`topleft=`, so pgzero centers each string horizontally on `WIDTH // 2` —
no manual text-width math needed.

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
*Expected State: the rival is visible for the first time — parked in its
lane, 500m up the road — but it never moves, and driving straight through
it does nothing at all. `new_race()` builds the rival dict and `draw()`
shows it, but `update()` doesn't know it exists yet.*

**Up Next:** Step 6 makes the rival move (by its own `base_speed`) and
makes it possible to crash into.

## Step 6: Relative Speed, and Handling a Crash

First, make `game_state != "racing"` short-circuit `update()` — add this at
the very top of the function body (after the `global` line):

```python
    if game_state != "racing":
        if keyboard.space:
            new_race()
        return
```

**Teaching Note:** once crashed, none of the driving code below should run
at all — the car shouldn't keep accelerating, and the rival shouldn't keep
moving, while a "CRASHED!" banner is up. `return` exits the function
immediately; the only thing still checked is whether SPACE was pressed to
start over.

Then, at the very end of `update()` (after `distance_traveled +=
player_speed`), add the rival's own movement and the collision check.
You'll also need to add `game_state` to the `global` line at the top of
`update()`.

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
*Expected State: the rival now drives up the road under its own power —
catch up to it and you pass it, fall behind and it pulls away. Touching it
ends the run with a "CRASHED!" banner, and SPACE starts a new race.*

**The Concept:** the rival never "knows" where you are, and nothing steers
it toward or away from you. It just adds `base_speed` to its own distance
every frame, at a constant rate. `row_at()` converts the *gap* between that
distance and yours into a screen position — speed up and the gap shrinks,
so the rival visibly comes toward you and slides past; slow down and the
gap grows, so it pulls away. That single comparison is the entire "AI" for
every opponent in this project, all the way through Week 5.

**Classroom Demo:** bump the rival's `base_speed` in `new_race()` past
`MAX_SPEED` and run it — the rival pulls away no matter how hard the class
accelerates, a quick way to show the comparison is just two numbers, not
real steering.

## Checkpoint: Final Code for Week 2, Part 2

The full script should now match `02_week2_part2.py` — one rival, sharing
the road with its own lane, moving by relative speed, with a crash ending
the run and SPACE starting over.

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
*Expected State: a full drive with one rival — it moves under its own
speed, you can catch and pass it or fall behind, colliding ends the run
with a banner, and SPACE restarts. Still no finish line: the run only ends
by crashing, not by reaching a goal.*

**Up Next:** `WIDTH` is a formula now, not a plain number — that matters
starting next week, when `NUM_RIVALS` grows past `1` and the window needs
to get wider to fit more lanes automatically. There's still no finish line
and no "winning" — that arrives next week, once there's a real pack of
rivals to place, not just one.
