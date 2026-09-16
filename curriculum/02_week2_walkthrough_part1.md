# Week 2, Part 1 Walkthrough — The Road Scrolls

Start from Week 1's finished game: a car with real speed, three zones, and a
speed number on the HUD — but the car has never felt like it was going
anywhere. This is the session where that changes. Budget extra time for it —
the scrolling formula in Step 2 is the densest piece of math in the
curriculum and most classes need to work through the example more than once.

## Step 1: Retune the Knobs, and Add `distance_traveled`

Update the tuning constants block to match:

```python
MAX_SPEED = 10
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7    # speed the shoulder drags you down to
ROUGH_MAX_SPEED = MAX_SPEED * 0.4       # speed the rough drags you down to
ACCEL = 0.12              # UP key
BRAKE = 0.35              # DOWN key
COAST = 0.04              # slow-down when no key is held
ROUGH_BRAKE = 0.40        # extra slow-down off the tarmac (shoulder or rough)

DASH_PERIOD = 60          # distance from the start of one dash to the next
DASH_LENGTH = 30          # how long each dash is
```

And add a new variable next to `player_speed`:

```python
distance_traveled = 0.0
```
*Expected State: no visible change. The game plays like last week's
checkpoint with slightly retuned accel/brake numbers; `distance_traveled`
exists in memory but nothing reads it yet.*

**Teaching Note:**
- `ACCEL` and `BRAKE` used to run automatically based only on which zone the
  car was in. Starting this week, the player controls them directly with UP
  and DOWN (wired up in Step 4) — relabeled "UP key" / "DOWN key" to match
  their new job.
- `ROUGH_BRAKE` is a new, separate constant for the automatic off-road
  slowdown, since that still has to happen independently of whatever the
  player is pressing.
- `COAST` is new too: letting go of both keys now bleeds speed off slowly
  instead of holding it steady forever — closer to how a real car behaves.

## Step 2: The Scrolling Trick

Add this function right after `on_shoulder()`:

```python
# ---------------------------------------------------------------------------
# THE SCROLLING TRICK
# ---------------------------------------------------------------------------
def dist_at(y):
    """What track distance is being drawn at screen row y, right now?"""
    return distance_traveled + (PLAYER_ROW - y)
```
*Expected State: no visible change. `dist_at()` exists but nothing calls it
yet.*

**Teaching Note:** `distance_traveled` is how far along the course the
player has driven. It only ever goes up, by `player_speed` every frame. The
road itself never moves — only that number does. `dist_at(y)` is the
translator: it takes "a distance along the course" and returns "a row on
screen," for anything that needs to draw at that distance.

**Math Concept:** nothing on screen ever actually moves. Every frame,
`dist_at(y)` answers one question: "given what `distance_traveled` is right
now, what course distance is showing at this row of the screen?"

For example with `PLAYER_ROW = 480` and `distance_traveled = 1000`:
- At `y = 480` (the player's own row): `dist_at(480) = 1000 + (480 - 480) =
  1000`. The player's row shows the player's own current distance.
- At `y = 380` (100 pixels higher, i.e. further ahead): `dist_at(380) = 1000
  + (480 - 380) = 1100`. A hundred pixels higher shows a hundred metres
  further along the track — in this game, 1 pixel of screen height equals 1
  metre of track distance.
- At `y = 580` (100 pixels lower, i.e. behind the player): `dist_at(580) =
  1000 + (480 - 580) = 900` — 100 metres behind where the player is now.

A frame later, `distance_traveled` has grown to `1010` (the player moved
forward 10 metres). Recompute the first case: `dist_at(480) = 1010 + (480 -
480) = 1010`. Distance `1010` was drawn at `y = 470` last frame
(`dist_at(470) = 1000 + 10 = 1010`); this frame it's drawn at `y = 480`
instead. The same distance moved 10 pixels lower on screen between frames —
exactly what "the road scrolled down 10 pixels" looks like. Nothing moved;
the same question was just asked again with a bigger `distance_traveled`.

**Classroom Prompt (For Fast Finishers):** what does `dist_at` return for a
`y` well below `PLAYER_ROW` while `distance_traveled` is still `0`? Could it
go negative — and what would a negative distance mean here?

## Step 3: Use It to Scroll the Centre Line

Change `strip_height` in `draw()` from `20` to `10` — finer dashes, closer
to how a real road's dashes look. Then replace the old alternating-strip
dash logic:

```python
        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )
```

with the distance-based version:

```python
        # The centre line is drawn wherever the current track DISTANCE lands
        # inside a "dash" - as distance_traveled grows, every dash appears to
        # slide down the screen, which is the whole scrolling illusion.
        # Nothing here actually moves; we just re-decide where to paint each
        # dash, every single frame.
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)
```

`dist_at(y)` matches the `y` name already used by `road_center_x()`,
`road_left()`, `road_right()`, `on_road()`, and `on_shoulder()` since Week
1 — no renaming needed here.

Also add a distance readout to the HUD, right after the speed text:

```python
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
                     fontsize=30, color="white")
```
*Expected State: the same speed/zone behavior as last week, plus a distance
counter on the HUD that doesn't move yet.*

**Math Concept:** `dist_at(y) % DASH_PERIOD` finds how far into the current
60-metre repeating pattern a given point sits — a number from `0` up to
(but not including) `60`. Below `30` (`DASH_LENGTH`) is the painted half of
the pattern; at or above it is the 30-metre gap. Because `dist_at(y)`
changes every frame as `distance_traveled` grows, this same check paints a
different strip on each successive frame — that's what makes the dashes
appear to travel down the screen instead of just flickering in place.

**Classroom Prompt (For Fast Finishers):** what happens if `DASH_LENGTH` is
set equal to `DASH_PERIOD`? What if it's set larger? (Larger than
`DASH_PERIOD` produces a solid, undashed line — the "gap" portion of the
pattern never occurs.)

## Mid-Session Checkpoint: The Scrolling Code in Place, But No Visible Changes

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
ACCEL = 0.12
BRAKE = 0.35
COAST = 0.04
ROUGH_BRAKE = 0.40

DASH_PERIOD = 60
DASH_LENGTH = 30

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### GAME STATE
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0


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


def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)


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

    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
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
*Expected State: the dashes sit frozen — `dist_at(y)` is computed every
frame, but `distance_traveled` never changes, so it keeps answering with the
same numbers.*

The scrolling machinery from Step 2 is fully built and wired into `draw()`.
The only piece missing is a line in `update()` that actually grows
`distance_traveled` — that's Step 4.

## Step 4: Throttle, Brake, and Coast

Replace the automatic three-tier speed block in `update()` with:

```python
    # throttle / brake / coast - this replaces last week's auto-accelerate.
    # Holding UP builds speed, DOWN sheds it fast, and letting go bleeds it
    # off slowly (COAST) instead of holding steady - a real car doesn't
    # coast at a constant speed forever either.
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
```

**Teaching Note:** `ROUGH_BRAKE` now drives the shoulder/rough check, while
`BRAKE` is reserved for the DOWN key. These are two independent reasons
speed can drop, and both can apply on the same frame — holding DOWN while
drifting onto the shoulder, for instance. Keeping them as separate constants
lets you tune "how hard braking feels" and "how harsh the shoulder is"
without one affecting the other.

Finally, add the line that makes Step 2's scrolling machinery actually run,
at the very end of `update()`:

```python
    # This is the only place distance_traveled changes - it only ever grows,
    # by however fast you're currently going. Everything scrolling on
    # screen is downstream of this one line.
    distance_traveled += player_speed
```

You'll need `distance_traveled` added to the `global` line at the top of
`update()`, alongside `player_speed`.
*Expected State: UP/DOWN throttle and brake the car, letting go coasts it
down, straying off the tarmac drags speed toward the zone's cap, and the
centre line now streams down the screen as `distance_traveled` grows.*

**Classroom Demo:** comment out the `distance_traveled += player_speed`
line and run it. UP/DOWN still change `player_speed` and the HUD number
still moves, but the road stops scrolling entirely — a clean demonstration
that scrolling depends on exactly that one line and nothing else.

## Checkpoint: Final Code for Week 2, Part 1

The full script should now match `02_week2_part1.py` — road scrolling, UP/DOWN
throttle and brake, coasting, and a distance counter, with no rival yet.

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
ACCEL = 0.12
BRAKE = 0.35
COAST = 0.04
ROUGH_BRAKE = 0.40

DASH_PERIOD = 60
DASH_LENGTH = 30

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### GAME STATE
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0


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


def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)


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

    player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
                     fontsize=30, color="white")
    if on_shoulder(player.x, PLAYER_ROW):
        screen.draw.text("ON THE SHOULDER", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 220, 120))
    elif not on_road(player.x, PLAYER_ROW):
        screen.draw.text("ON THE ROUGH!", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 90, 60))


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
*Expected State: a car that throttles, brakes, and coasts under UP/DOWN,
drags toward each zone's speed cap off the tarmac, and drives over a centre
line that streams continuously down the screen. No rival on screen yet.*

**Watch for:** dashes that look uneven or jump around usually trace back to
`dist_at(y)` being called with a different variable than the one used to
compute `center_x` and the strip's on-screen position — double-check both
use the same `y` inside the loop.

**Up Next:** there's no rival in this file yet, and nothing to crash into —
that's deliberate, so the scrolling illusion can be understood completely on
its own before Part 2 adds a second car.
