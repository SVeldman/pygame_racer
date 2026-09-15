# Week 1, Part 1 Walkthrough — The Map and the Car

This walkthrough takes students from the bare `racer.py` starter file to the
`01_week1_part1.py` checkpoint, step by step. Build in this order on purpose:
**car first, road second.** Getting a car moving on the plain green field in
the first few minutes should help hook the students in. The road's visual polish
(shoulder, tarmac, dashed line) will take a little more patience, so help them
enjoy that initial quick win.

**Concept: pgzero is a runner, not a library.** We don't write `import
pgzero` at the top of our Python script. When you run a file with `pgzrun
<filename>`, pgzero hands your file a set of special names (`screen`,
`Rect`, `Actor`, `keyboard`, `WIDTH`, `HEIGHT`) that are already defined.
That's why the code uses `screen` and `Rect` even though nothing in the
file ever creates them.

**Concept: two functions do all the work.** `draw()` runs about 60
times a second and repaints the window from scratch. `update()` also runs
about 60 times a second, right before `draw()`, and is where you change
values (like a car's position) in response to input or time passing.
Keeping "what changes" (`update`) separate from "what's shown right now"
(`draw`) comes up in every file this course builds — name the split early.

**Geometry: Pygame's coordinate system.** `(0, 0)` is the **top-left**
corner of the window. `x` increases to the right as usual, but `y`
increases **downward**. This trips up anyone used to graphs where "up" is
positive. It's why `PLAYER_ROW = 480` (out of `HEIGHT = 600`) means "near
the *bottom* of the screen," not the top.

## Beginning of Class: Setup

Students will need Pygame Zero installed. In a terminal, have them run:

```bash
pip install pgzero
```

To run a file, `cd` into whatever folder it's saved in and run `pgzrun
<filename>`.

For our main project file:

```bash
cd project
pgzrun racer.py
```

## Starting Code for Week 1, Part 1

Start with the `racer.py` script:
```python

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
# We store measurements and settings in named constants (ALL_CAPS by
# convention) instead of typing raw numbers all over the place. That way,
# if we want a wider road later, we change ONE number instead of hunting
# through the code base to change it in multiple places.

# ---------------------------------------------------------------------------
# SCREEN SIZE, ROAD DIMENSIONS, AND PLAYER LOCATION
# ---------------------------------------------------------------------------
WIDTH = 800             # Width of the entire game screen
HEIGHT = 600            # Height of the entire game screen
ROAD_WIDTH = 220        # how wide the grey tarmac is, in pixels
SHOULDER_WIDTH = 55     # width of the gravel strip on each side of the road
PLAYER_ROW = 480        # how far down the screen the car sits, in pixels

# ---------------------------------------------------------------------------
# COLOURS
# ---------------------------------------------------------------------------
# In Pygame Zero colours are defined as tuples, which is just programmer-lingo for a
# list that you cannot change with code later. Here, each color is defined by how much
# of the three base colors (red, green, blue) are used to make it (each value must be a
# minimum of 0 and a maximum of 255).
GRASS = (40, 120, 55)     # dark green - covers the whole background
GRAVEL = (150, 140, 110)  # tan - the "shoulder" strip beside the road
TARMAC = (60, 60, 68)     # dark grey - the actual road
LINE = (240, 240, 240)    # near-white - the dashed centre line

# ---------------------------------------------------------------------------
# GAME CODE
# ---------------------------------------------------------------------------

#### We will add code here as we build out our game logic

```
*Expected State: the script will run without erroring, but pgzero just opens a
blank black window.*

**Teaching Note:** that's correct, not broken. `racer.py` only defines
*constants* — plain values sitting in memory. Nothing has told pgzero to
draw anything yet. That's what `draw()` is for, and we haven't written one.

## Step 1: Fill the Screen with "Grass"

Add this snippet directly under "GAME CODE":

```python
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))

def draw():
    """Pygame Zero calls this once every frame to repaint the window."""
    screen.fill(GRASS)

    player.draw()
```
*Expected State: a green screen with a stationary car sprite on it. No
controls work yet.*

**The Concept:** `Actor("car_red", (x, y))` creates a game object out of
`images/car_red.png`, positioned at `(x, y)`. This line runs **once**, when
the file first loads — not every frame. The car exists as soon as the file
runs; `draw()` is just what makes it *visible*.

**Teaching Note:** order matters inside `draw()`. `screen.fill(GRASS)`
paints the **entire** window green, covering anything drawn before it.
`player.draw()` runs *after* that fill, so the car appears on top of the
grass instead of getting painted over by it. Swap the two lines and the car
vanishes — the grass fill becomes the last thing drawn.

## Step 2: Add Controls

Add the following function to the very end of the script (after the `draw`
function):

```python
def update():
    """Pygame Zero calls this once every frame, right before draw()."""
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
```
*Expected State: the car moves left and right with the arrow keys, and can
now drive straight off either edge of the screen.*

**The Concept:** `keyboard.left` and `keyboard.right` are `True` for
**every single frame** a key is held down — not just the moment it's first
pressed. That's why holding the left arrow key moves the car continuously
instead of one five-pixel hop per press: `update()` runs ~60 times a
second, and each of those frames nudges `player.x` again while the key is
down.

**Classroom Demo:** hold both arrow keys at once. Both `if` statements run
every frame — first `-5`, then `+5` — so the car doesn't move at all.
Neither `if` "wins"; they both just happen, in the order they're written.

## Step 3: Add Bounds for the Car

Add one line to the bottom of the `update` function:

```python
def update():
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    player.x = max(20, min(WIDTH - 20, player.x))
```
*Expected State: the car moves freely left and right but stops at the
edges of the window instead of driving off them.*

**Math Concept — how the clamp works:** this one line does two jobs at once,
from the inside out.
1. `min(WIDTH - 20, player.x)` — "don't let `player.x` be bigger than
   `WIDTH - 20`." If `player.x` is `850` and `WIDTH - 20` is `780`, this
   returns `780`. If `player.x` is already less than `780`, it returns
   `player.x` unchanged.
2. `max(20, ...)` — takes the result of step 1 and does the same thing for
   the *lower* bound: "don't let this be smaller than `20`."

`player.x` always ends up somewhere between `20` and `WIDTH - 20`. This
`max(low, min(high, value))` shape is called **clamping** — it shows up
any time a value needs to stay inside a range (screen edges, speed limits,
volume sliders). The `20` on each side isn't arbitrary — it roughly
matches the car sprite's own half-width, so the car stops right at the
edge of the window instead of half-vanishing off it.

**Classroom Demo:** comment out the clamp line and run it. Drive the car
off either edge and let students watch it disappear entirely, then restore
the line and drive it back into view — makes the "why" land faster than
describing it.

## Mid-Session Checkpoint: Car, Green Field, Movement

At this stage, the full Python script should look something like this:

```python

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# SCREEN SIZE, ROAD DIMENSIONS, AND PLAYER LOCATION
WIDTH = 800             # Width of the entire game screen
HEIGHT = 600            # Height of the entire game screen
ROAD_WIDTH = 220        # how wide the grey tarmac is, in pixels
SHOULDER_WIDTH = 55     # width of the gravel strip on each side of the road
PLAYER_ROW = 480        # how far down the screen the car sits, in pixels

# COLOURS
GRASS = (40, 120, 55)     # dark green - covers the whole background
GRAVEL = (150, 140, 110)  # tan - the "shoulder" strip beside the road
TARMAC = (60, 60, 68)     # dark grey - the actual road
LINE = (240, 240, 240)    # near-white - the dashed centre line

# ---------------------------------------------------------------------------
# GAME CODE
# ---------------------------------------------------------------------------

player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))


def draw():
    screen.fill(GRASS)

    player.draw()


def update():
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    player.x = max(20, min(WIDTH - 20, player.x))
```
*Expected State: a car on a plain green field, moving left/right, clamped
to the window edges. No road yet.*

That's the whole point of building in this order: a "real," runnable
program with visible feedback, before we've touched anything more
complicated. Everything from here is visual polish — nothing about *how
the car moves* changes for the rest of Part 1.

## Step 4: Define the Road

Add the following code directly under "GAME CODE" (right above
`player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))`):
```python
# ROAD DEFINITION
def road_center_x(row):
    """X position of the MIDDLE of the road at a given screen row (y value)."""
    return WIDTH // 2


def road_left(row):
    """X position of the LEFT edge of the tarmac at this row."""
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
    """X position of the RIGHT edge of the tarmac at this row."""
    return road_center_x(row) + ROAD_WIDTH // 2
```
*Expected State: no visible change. The road's bounds now exist in code,
but nothing draws them yet.*

**Teaching Note — why a function, and not just a constant?**
`road_center_x(row)` returns the exact same number right now (`WIDTH //
2`), so it *looks* pointless. The payoff is a few weeks away: later in the
course, this function starts returning a *different* number depending on
`row`, and that's what makes the road curve. Because every other piece of
the game always **asks this function** where the road is instead of
assuming it knows, the road will be able to curve later without rewriting
any of the code that draws it or drives on it. Plant the seed now; it's
fine if it doesn't fully click until Week 4.

**Math Concept — integer division (`//`):** `WIDTH // 2` and `ROAD_WIDTH //
2` both use `//`, not `/`. Regular division (`/`) can produce a fraction
(`801 / 2 = 400.5`), but there's no such thing as half a pixel to draw at.
`//` ("floor division") divides and rounds *down* to the nearest whole
number, so `801 // 2 = 400`.

**Classroom Prompt (For Fast Finishers):** `road_center_x(row)` takes a
`row` argument it doesn't use yet. Ask early finishers to guess what kind
of value it might return once curves exist — is it the same for every
`row`, or different depending on how far down the screen you look?

## Step 5: Draw the Road

Now we'll add the grey tarmac to our game screen.
Add the following code to the `draw` function, right after `screen.fill(GRASS)`. *Pay careful attention to the indents here.*

```python
    strip_height = 20
    for top in range(0, HEIGHT, strip_height):
        row = top + strip_height // 2
        center_x = road_center_x(row)

        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2, top, ROAD_WIDTH, strip_height),
            TARMAC,
        )
```
*Expected State: a grey strip of road down the screen. No shoulder or
center line yet.*

**Teaching Note — why a loop of strips, instead of one tall rectangle?** A
single rectangle would draw a straight road just fine, but it could never
bend. Drawing the road as a stack of many short horizontal strips means
each strip could, later, be shifted left or right by a *different* amount.
Right now they all line up (`road_center_x()` always returns the same
value), so it looks like one solid road. Nothing about this loop changes
when the road starts curving — only what `road_center_x()` returns.

**The Geometry:**
- `row = top + strip_height // 2` finds the **vertical middle** of the
  strip, not its top edge. With `top = 100` and `strip_height = 20`, `row =
  110`. That matters once `road_center_x()` varies smoothly by row — the
  strip gets positioned using the road's location at its *center*.
- `Rect(x, y, width, height)` positions a rectangle by its **top-left
  corner**, not its center. To draw a 220-pixel-wide rectangle *centered*
  on `center_x = 400`, its left edge has to start 110 pixels left of
  center: `Rect(400 - 110, 100, 220, 20)` → `Rect(290, 100, 220, 20)`.
  Skip that subtraction and the whole rectangle draws hanging off to the
  right of where you want it.
- This "shift left by half the width" trick is exactly what `road_left()`
  already computes — this loop does the same math inline, for drawing
  instead of for answering "is the car on the road?"

## Step 6: Add the Shoulder

Add the following above the code for the tarmac:
```python
        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2 - SHOULDER_WIDTH, top,
                 SHOULDER_WIDTH, strip_height),
            GRAVEL,
        )
        screen.draw.filled_rect(
            Rect(center_x + ROAD_WIDTH // 2, top, SHOULDER_WIDTH, strip_height),
            GRAVEL,
        )
```
*Expected State: a grey road with a tan gravel shoulder on each side. Still
no center line.*

**The Geometry:** the tarmac's left edge is at `center_x - ROAD_WIDTH //
2` — the same expression `road_left()` computes. The left shoulder sits
*immediately* to the left of that edge, so its own left edge is pushed out
one more `SHOULDER_WIDTH`: `center_x - ROAD_WIDTH // 2 - SHOULDER_WIDTH`.
The right shoulder is simpler — it starts exactly where the tarmac's right
edge is (`center_x + ROAD_WIDTH // 2`) and extends `SHOULDER_WIDTH`
further right, no extra subtraction needed.

**Classroom Prompt (For Fast Finishers):** this code computes `center_x -
ROAD_WIDTH // 2` and `center_x + ROAD_WIDTH // 2` by hand, but
`road_left(row)` and `road_right(row)` from Step 4 already compute exactly
those two values. Could this call those functions instead of repeating the
formula? (Yes — it's a good check for whether the earlier functions
actually clicked. We leave it written out longhand here to keep every
number visible while it's new.)

## Step 7: Add the Center Line

Add this snippet after the tarmac logic:
```python
        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )
```
*Expected State: shoulder and tarmac render solid; the road now has a
dashed white line down the center.*

**The Geometry — how the dashing pattern works:**
- `top` increases by `strip_height` (20) every loop: `0, 20, 40, 60, ...`
- `top // strip_height` turns that into a strip **index**: `0, 1, 2, 3,
  ...`
- `% 2` alternates that index between `0` and `1` every strip: `0, 1, 0, 1,
  ...`
- `== 0` flips that alternation into `True`/`False` — draw a dash, skip a
  dash, repeat.

Every *other* strip draws a short white rectangle, and the rest don't —
that's what makes a solid line read as "dashed." This `x % 2 == 0`
alternation is the same trick behind striped table rows and checkerboard
patterns.

**Classroom Demo:** change `% 2` to `% 3` and ask the class to predict the
new dash spacing before you run it.

The `draw` function should now look like this in full:
```python
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
```

## Checkpoint: Final Code for Week 1, Part 1

After completing this section, our full code should look something like this
(and should match `01_week1_part1.py`):

```python
### CONSTANTS
WIDTH = 800
HEIGHT = 600
ROAD_WIDTH = 220
SHOULDER_WIDTH = 55
PLAYER_ROW = 480

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)


### ROAD
def road_center_x(row):
    return WIDTH // 2


def road_left(row):
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
    return road_center_x(row) + ROAD_WIDTH // 2


### PLAYER
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))


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
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    player.x = max(20, min(WIDTH - 20, player.x))
```
*Expected State: a car driving left/right on a dashed grey road with
gravel shoulders, clamped to the window. Nothing scrolls yet.*

**Up Next:** Part 2 adds a `player_speed` number and gives the shoulder
and rough grass their own rules. Nothing scrolls yet (that's Week 2).
