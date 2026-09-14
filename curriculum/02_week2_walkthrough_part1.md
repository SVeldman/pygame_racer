# Week 2, Part 1 Walkthrough — The Road Scrolls

Start from Week 1's finished game: a car with real speed, three zones, and a
speed number on the HUD — but the car has never felt like it was going
anywhere. This is the session where that changes. **This is also the
conceptual brain-twister of the whole curriculum — budget real time for it,
and don't be afraid to put the key formula on a whiteboard rather than
deriving it live.**


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

**What changed and why:** `ACCEL` and `BRAKE` used to run automatically
based only on which zone you were in. Starting this week, you control them
directly with UP and DOWN (Step 4 wires that up) — so they're relabeled
"UP key" / "DOWN key" here to reflect their new job. `ROUGH_BRAKE` is a
*new*, separate constant for the automatic off-road slow-down, since that
still needs to happen independently of whether you're pressing anything.
`COAST` is new too — letting go of both keys now bleeds speed off slowly
instead of holding it steady forever, which feels more like a real car.

## Step 2: The Scrolling Trick

Add this function, with a comment block explaining the idea, right after
`on_shoulder()`:

```python
# ---------------------------------------------------------------------------
# THE SCROLLING TRICK
# ---------------------------------------------------------------------------
def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)
```

`distance_traveled` is how far along the course you've driven so far. It
only ever goes up (by `player_speed` every frame). We never move the
ROAD - we only ever move the NUMBER - and then use dist_at() to translate
"a distance along the course" into "a row on screen" wherever we need to
draw something at that distance.

**Math note — this is the whole trick, so let's earn it.** Nothing on
screen is ever going to move. Instead, every frame, we ask "if
`distance_traveled` is what it is right now, what distance is being shown at
each row of the screen?" — and `dist_at(y)` is the answer.

Walk through an example. Say `PLAYER_ROW = 480` and `distance_traveled =
1000` right now.
- At `y = 480` (the player's own row): `dist_at(480) = 1000 + (480 - 480) =
  1000`. Makes sense — the player's own row shows the player's own current
  distance.
- At `y = 380` (100 pixels *higher* on screen, i.e. further ahead):
  `dist_at(380) = 1000 + (480 - 380) = 1100`. A hundred pixels higher up
  shows a hundred metres *further along the track* — because in this game,
  1 pixel of screen height = 1 metre of track distance.
- At `y = 580` (100 pixels lower, i.e. behind you — off the bottom of a
  600-tall window, but the formula still works): `dist_at(580) = 1000 + (480
  - 580) = 900` — 100 metres *behind* where you are now.

Now the payoff: a frame later, say `distance_traveled` has grown to `1010`
(you drove forward 10 metres). Redo the very first example: `dist_at(480) =
1010 + (480 - 480) = 1010`. But what distance is now showing at `y = 470` (10
pixels higher than before)? `dist_at(470) = 1010 + (480 - 470) = 1020`. Compare:
last frame, distance `1010` was drawn at `y = 470` (from the second bullet
above, roughly). This frame, it's drawn at `y = 480` instead. **The same
distance is now drawn 10 pixels lower on screen than it was a moment ago —
which is exactly what "the road scrolled down by 10 pixels" looks like.**
Nothing moved. We just kept asking the same question with a bigger
`distance_traveled` each time.

## Step 3: Use It to Scroll the Centre Line

Change `strip_height` in `draw()` from `20` to `10` (this just makes the
dashes finer-grained, closer to how a real road's dashes look), and replace
the old alternating-strip dash logic:

```python
        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )
```

with the new distance-based version:

```python
        # The centre line is drawn wherever the current track DISTANCE lands
        # inside a "dash" - as distance_traveled grows, every dash appears to
        # slide down the screen, which is the whole scrolling illusion.
        # Nothing here actually moves; we just re-decide where to paint each
        # dash, every single frame.
        if dist_at(y) % DASH_PERIOD < DASH_LENGTH:
            screen.draw.filled_rect(Rect(center_x - 4, top, 8, strip_height), LINE)
```

(While you're in there: rename the `row` parameter on `road_center_x()`,
`road_left()`, and `road_right()` from Week 1 to `y`, matching `dist_at(y)`.
Either name works — it's just a screen row either way — but the checkpoint
file below uses `y` everywhere for consistency.)

**Math note — why `%` (modulo) again:** `dist_at(y) % DASH_PERIOD` finds
"how far into the current 60-metre repeating pattern is this point?" — a
number from `0` up to (but not including) `60`. Whenever that remainder is
less than `30` (`DASH_LENGTH`), we're in the "painted" half of the pattern;
otherwise we're in the 30-metre gap. Because `dist_at(y)` changes every
frame as `distance_traveled` grows, this same check paints a *different*
strip on each successive frame — which is what makes the dashes appear to
travel down the screen continuously, instead of just flickering on and off
in place.

Also add a distance readout to the HUD, right after the speed text:
```python
    screen.draw.text(f"Distance: {int(distance_traveled)} m", topleft=(10, 40),
                     fontsize=30, color="white")
```

**Running the game now shows the same speed/zone behavior as last week, plus
a distance counter that... doesn't move yet.** That's expected — nothing
calls `dist_at()` from `update()` to actually grow `distance_traveled` until
the next step.

## Mid-Session Checkpoint: The Scrolling Machinery, Not Yet Turning

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

Run it and the dashes just sit there, frozen — `dist_at(y)` is being computed
every frame, but `distance_traveled` itself never changes, so it keeps
answering with the same numbers. The whole scrolling trick from Step 2 is
built and wired into `draw()`; the only thing missing is a line in
`update()` that actually grows `distance_traveled`. That's the very next
step.

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

**Why the off-road check still needs its own rate:** notice `ROUGH_BRAKE` is
used for the shoulder/rough check, while `BRAKE` is now reserved for the DOWN
key. These are two *independent* reasons speed might drop, and they can even
both apply on the same frame (holding DOWN while also drifting onto the
shoulder) — keeping them as separate constants lets you tune "how hard does
braking feel" and "how harsh is the shoulder" without one affecting the
other.

Finally, add the one line that makes everything from Step 2 actually happen
— at the very end of `update()`:
```python
    # This is the only place distance_traveled changes - it only ever grows,
    # by however fast you're currently going. Everything scrolling on
    # screen is downstream of this one line.
    distance_traveled += player_speed
```

You'll need `distance_traveled` added to the `global` line at the top of
`update()`, alongside `player_speed`.

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

**Watch for:** if the dashes look like they're not moving smoothly, or jump
around, the most common cause is a leftover reference to the old `row`
variable name instead of `y` somewhere in `draw()` — make sure `dist_at(y)`
is being called with the *same* variable that's used to compute `center_x`
and the row's Y position. There's no rival in this file yet, and nothing to
crash into — that's deliberate, so this scrolling illusion can be understood
completely on its own before Part 2 adds a second car.
