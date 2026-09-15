# Week 1, Part 2 Walkthrough — Speed, and Three Zones

Starting from the end of Part 1, this part adds `player_speed` — a number
that climbs on the tarmac and falls off it — and gives the shoulder and the
rough grass their own rules.

**Nothing moves up the screen yet.** That's intentional: speed is
introduced first as a number to watch on the HUD, before it's asked to
scroll the road. Week 2 is where this number starts driving something
real.

## Step 1: Add the New Tuning Knobs

Add these new constants next to the existing ones, and a new `player_speed`
variable next to `player`:

```python
MAX_SPEED = 10                          # top speed, reached only on tarmac
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7    # speed the shoulder drags you down to
ROUGH_MAX_SPEED = MAX_SPEED * 0.4       # speed the rough drags you down to
ACCEL = 0.10                            # how much speed builds up each frame
BRAKE = 0.30                            # how much speed drops each frame off-road
```
```python
player_speed = 0.0
```
*Expected State: no visible change — these are just numbers sitting in
memory, the same as when `racer.py` had nothing but constants back in
Part 1.*

**The Concept:** `SHOULDER_MAX_SPEED` and `ROUGH_MAX_SPEED` are written as
`MAX_SPEED * 0.7` and `MAX_SPEED * 0.4`, not as `7` and `4`. Change
`MAX_SPEED` later and both caps scale with it automatically — they always
mean "70% of top speed" and "40% of top speed," not two numbers that
happen to currently equal `7` and `4`.

**Classroom Demo:** change `MAX_SPEED` and re-run. Both derived caps move
with it, with no other edits needed.

## Step 2: Teach the Game About the Three Zones

Add these two functions right after `road_right()`:

```python
def on_road(x, row):
    """True if x is on the tarmac at this row."""
    return road_left(row) <= x <= road_right(row)


def on_shoulder(x, row):
    """True if x is on the gravel shoulder - off the road, but not into the
    rough (grass) yet."""
    if on_road(x, row):
        return False
    return road_left(row) - SHOULDER_WIDTH <= x <= road_right(row) + SHOULDER_WIDTH
```
*Expected State: no visible change — these functions exist, but nothing
calls them yet.*

**Teaching Note — why two functions, not one?** There are three possible
answers to "where is the car?": on the road, on the shoulder, or out in
the rough. `on_road()` answers the first question directly. `on_shoulder()`
answers the second by first ruling out the road (`if on_road(x, row):
return False`), then checking a *wider* range that extends
`SHOULDER_WIDTH` past each edge of the tarmac. Whatever's left over — not
on the road, not on the shoulder — is the rough, by elimination. There's
no `on_rough()` function, because nothing ever needs to ask that question
directly; `update()` just uses `else` for it (Step 3).

**Classroom Prompt (For Fast Finishers):** have them write the
`on_rough(x, row)` function that's conspicuously missing, as a standalone
exercise. It should return `True` exactly when both `on_road()` and
`on_shoulder()` return `False` — a direct check against the `else` branch
`update()` uses instead.

## Step 3: Give Each Zone Its Own Speed Rule

Add this to the bottom of `update()`, after the existing steering/clamp
code:

```python
    if on_road(player.x, PLAYER_ROW):
        if player_speed < MAX_SPEED:
            player_speed += ACCEL
    elif on_shoulder(player.x, PLAYER_ROW):
        if player_speed > SHOULDER_MAX_SPEED:
            player_speed -= BRAKE
    else:
        if player_speed > ROUGH_MAX_SPEED:
            player_speed -= BRAKE

    player_speed = max(0.0, min(MAX_SPEED, player_speed))
```
*Expected State: still no visible change — `player_speed` is climbing and
falling in memory, but nothing on screen shows it yet.*

You'll also need to add `global player_speed` to the top of `update()`.

**Teaching Note:** this is the first time `update()` changes a variable
defined outside itself. `player.x` isn't affected by this rule — `player`
is an `Actor` object, and changing `player.x` changes an *attribute* of
it, not `player` itself. `player_speed` is a plain number, and reassigning
a plain number from inside a function needs `global`.

**Math Concept — three doors, one clamp:** this is an `if` / `elif` /
`else` — exactly one of the three branches runs each frame, based on
which zone the car is in right now.
- **Road:** speed climbs by `ACCEL`, but `if player_speed < MAX_SPEED`
  stops it climbing past the ceiling.
- **Shoulder:** speed falls by `BRAKE`, but only while it's still above
  `SHOULDER_MAX_SPEED` — once it hits that ceiling, this branch stops
  changing speed at all.
- **Rough:** the same idea, with a *lower* ceiling (`ROUGH_MAX_SPEED`), so
  straying further off the road costs more.

The final `player_speed = max(0.0, min(MAX_SPEED, player_speed))` line is
the same clamp pattern from Part 1's `player.x`, applied to speed instead
of position — a safety net that keeps repeated `+= ACCEL` or `-= BRAKE`
calls from pushing `player_speed` outside `0` to `MAX_SPEED`, even if a
single step overshoots a boundary.

This check re-runs every single frame, so there's no "penalty timer" —
steer back onto the road and speed starts climbing toward `MAX_SPEED`
again immediately, from wherever it currently sits.

## Mid-Session Checkpoint: Speed Is Real, but Invisible

At this stage, the full Python script should look something like this:

```python
### CONSTANTS
WIDTH = 800
HEIGHT = 600

ROAD_WIDTH = 220
SHOULDER_WIDTH = 55
PLAYER_ROW = 480
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.10
BRAKE = 0.30

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### PLAYER
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0


### ROAD
def road_center_x(row):
    return WIDTH // 2


def road_left(row):
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
    return road_center_x(row) + ROAD_WIDTH // 2


def on_road(x, row):
    return road_left(row) <= x <= road_right(row)


def on_shoulder(x, row):
    if on_road(x, row):
        return False
    return road_left(row) - SHOULDER_WIDTH <= x <= road_right(row) + SHOULDER_WIDTH


### DRAW
def draw():
    screen.fill(GRASS)

    strip_height = 20
    for top in range(0, HEIGHT, strip_height):
        row = top + strip_height // 2
        center_x = road_center_x(row)

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

        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )

    player.draw()


### UPDATE
def update():
    global player_speed

    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
    player.x = max(20, min(WIDTH - 20, player.x))

    if on_road(player.x, PLAYER_ROW):
        if player_speed < MAX_SPEED:
            player_speed += ACCEL
    elif on_shoulder(player.x, PLAYER_ROW):
        if player_speed > SHOULDER_MAX_SPEED:
            player_speed -= BRAKE
    else:
        if player_speed > ROUGH_MAX_SPEED:
            player_speed -= BRAKE

    player_speed = max(0.0, min(MAX_SPEED, player_speed))
```
*Expected State: the car still just drives around a plain road, exactly
like the end of Part 1. `player_speed` is climbing and falling in memory
exactly the way it should — nothing on screen shows it yet.*

That's deliberate: the mechanic and its display are two separate jobs, and
this is the moment the mechanic itself is done. The rest of this part is
just making it visible.

## Step 4: Show the Speed on the HUD

Add this to the bottom of `draw()`, after `player.draw()`:

```python
    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    if on_shoulder(player.x, PLAYER_ROW):
        screen.draw.text("ON THE SHOULDER", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 220, 120))
    elif not on_road(player.x, PLAYER_ROW):
        screen.draw.text("ON THE ROUGH!", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 90, 60))
```
*Expected State: a speed readout in the top-left corner, plus a warning
banner across the top of the screen when the car drifts onto the shoulder
or into the rough.*

**Teaching Note:** if the car is off the road at all, there are two
possibilities — shoulder, or rough. Checking `on_shoulder()` first and
`on_road()` second (with `elif`) is deliberate: "off the road, and off the
shoulder too" is exactly what `elif not on_road(...)` catches, so by the
time that line runs the shoulder case is already ruled out. Swap the
order and an extra check would be needed to avoid misclassifying the
shoulder as the rough.

**Classroom Demo:** swap the branch order — check `not on_road(...)`
first and `on_shoulder(...)` second — and drive onto the shoulder. The
banner now reads "ON THE ROUGH!" even though the car never left the
shoulder, because `not on_road(...)` is already `True` there and the `if`
claims it before `on_shoulder()` ever gets checked.

## Checkpoint: Final Code for Week 1, Part 2

The full script should now match `01_week1_part2.py`:

```python
### CONSTANTS
WIDTH = 800
HEIGHT = 600

ROAD_WIDTH = 220
SHOULDER_WIDTH = 55
PLAYER_ROW = 480
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7
ROUGH_MAX_SPEED = MAX_SPEED * 0.4
ACCEL = 0.10
BRAKE = 0.30

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### PLAYER
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0


### ROAD
def road_center_x(row):
    return WIDTH // 2


def road_left(row):
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
    return road_center_x(row) + ROAD_WIDTH // 2


def on_road(x, row):
    return road_left(row) <= x <= road_right(row)


def on_shoulder(x, row):
    if on_road(x, row):
        return False
    return road_left(row) - SHOULDER_WIDTH <= x <= road_right(row) + SHOULDER_WIDTH


### DRAW
def draw():
    screen.fill(GRASS)

    strip_height = 20
    for top in range(0, HEIGHT, strip_height):
        row = top + strip_height // 2
        center_x = road_center_x(row)
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
        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )

    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    if on_shoulder(player.x, PLAYER_ROW):
        screen.draw.text("ON THE SHOULDER", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 220, 120))
    elif not on_road(player.x, PLAYER_ROW):
        screen.draw.text("ON THE ROUGH!", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 90, 60))


### UPDATE
def update():
    global player_speed

    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
    player.x = max(20, min(WIDTH - 20, player.x))

    if on_road(player.x, PLAYER_ROW):
        if player_speed < MAX_SPEED:
            player_speed += ACCEL
    elif on_shoulder(player.x, PLAYER_ROW):
        if player_speed > SHOULDER_MAX_SPEED:
            player_speed -= BRAKE
    else:
        if player_speed > ROUGH_MAX_SPEED:
            player_speed -= BRAKE

    player_speed = max(0.0, min(MAX_SPEED, player_speed))
```
*Expected State: a car that drives left and right, gains speed on the
tarmac, loses it on the shoulder or in the rough, and shows both the
speed number and a zone warning on the HUD. It still doesn't move up the
screen.*

**Watch for:** some students expect "speed" to already mean forward
motion, since the car still doesn't move up the screen. This speed number
doesn't drive anything yet — Week 2 takes the same `player_speed` built
here and uses it to scroll the road.
