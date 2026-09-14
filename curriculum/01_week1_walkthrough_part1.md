# Week 1, Part 1 Walkthrough — The Map and the Car

This walkthrough takes students from the bare `racer.py` starter file to the
`01_week1_part1.py` checkpoint, live, step by step. Build in this order on
purpose: **car first, road second.** Getting a car moving on a plain green
field in the first few minutes is a fast, satisfying win — the road's visual
polish (shoulder, tarmac, dashed line) comes after, once something is already
on screen and responding to keypresses.

Two Pygame Zero ideas underpin this whole session, worth saying out loud
before typing anything:
- **It's a runner, not a library.** We don't write `import pgzero` at the top
  of our Python script. When you run a file with `pgzrun <filename>`, pgzero 
  hands your file a set of special names (`screen`, `Rect`, `Actor`, `keyboard`,
  `WIDTH`, `HEIGHT`) that are already defined. That's why the code uses `screen`
  and `Rect` even though nothing in the file ever creates them.
- **Two functions do all the work.** `draw()` runs about 60 times a second
  and repaints the window from scratch. `update()` also runs about 60 times
  a second, right before `draw()`, and is where you change values (like a
  car's position) in response to input or time passing. Keeping "what
  changes" (`update`) separate from "what's shown right now" (`draw`) is a
  pattern worth naming early — it comes up in every file this course builds.

**Note on Pygame's coordinate system:** `(0, 0)` is the **top-left**
corner of the window, `x` increases to the right as usual, but `y` increases
**downward**. This trips people up who are used to graphs where "up" is
positive. It's why `PLAYER_ROW = 480` (a fairly large number, out of
`HEIGHT = 600`) means "near the *bottom* of the screen," not the top.

## Beginning of Class: Setup

Students need Pygame Zero installed. In a terminal, have them run:

```bash
pip install pgzero
```

To run a file, `cd` into the whatever folder it is saved in and run `pgzrun <filename>`.

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
# In Pygame Zero colours are defined as tuples - which is just programmer-lingo for a
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
**NOTE: Students can run the starter script without it erroring, but PyGameZero will just open a blank/black screen.**

This is intentional, and worth pointing out: there's nothing wrong yet.
`racer.py` only defines *constants* — plain values sitting in memory. Nothing
has told pgzero to draw anything. That's what `draw()` is for, and we
haven't written one yet.

## Step 1: Fill the Screen with "Grass"

Add this snippet directly under "GAME CODE":

```python
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))

def draw():
    """Pygame Zero calls this once every frame to repaint the window."""
    screen.fill(GRASS)

    player.draw()
```

**Why:** `Actor("car_red", (x, y))` creates a game object out of
`images/car_red.png`, positioned at `(x, y)`. This line runs **once**, when
the file first loads — not every frame. The car exists as soon as the file
runs; `draw()` is just what makes it *visible*.

Inside `draw()`, order matters: `screen.fill(GRASS)` paints the **entire**
window green, covering anything drawn before it. `player.draw()` runs
*after* that fill, so the car appears on top of the grass instead of getting
painted over by it. If you swapped the two lines, the car would be invisible
— the grass fill would be the last thing drawn, covering it up.

**If students run the program here, they can see the green screen with the
car sprite, but will not be able to interact with it.**

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

**Why:** `keyboard.left` and `keyboard.right` are `True` for **every single
frame** a key is held down — not just the moment it's first pressed. That's
why holding the left arrow key moves the car continuously instead of one
five-pixel hop per press: `update()` runs ~60 times a second, and each of
those frames nudges `player.x` again while the key is down.

(Fun edge case to try live: hold both arrow keys at once. Both `if`
statements run every frame — first `-5`, then `+5` — so the car doesn't move
at all. Neither `if` "wins"; they both just happen, in the order they're
written.)

**Now if they run the program, they can move the car, but it can disappear
off the screen.**

## Step 3: Add Bounds for the Car

Add one line to the bottom of the `update` function:

```python
def update():
    """Pygame Zero calls this once every frame, right before draw()."""
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    player.x = max(20, min(WIDTH - 20, player.x))
```

**Math note — how the clamp works:** this one line is doing two jobs at
once, from the inside out:
1. `min(WIDTH - 20, player.x)` — "don't let `player.x` be bigger than
   `WIDTH - 20`." If `player.x` is `850` and `WIDTH - 20` is `780`, this
   returns `780`. If `player.x` is already less than `780`, it returns
   `player.x` unchanged.
2. `max(20, ...)` — takes the result of step 1 and does the same thing for
   the *lower* bound: "don't let this be smaller than `20`."

So `player.x` always ends up somewhere between `20` and `WIDTH - 20`,
whatever it was before. This `max(low, min(high, value))` shape is called
**clamping**, and it's worth having students recognize the pattern — it
shows up constantly any time a value needs to stay inside a range (screen
edges, speed limits, volume sliders, you name it). The `20` on each side
isn't arbitrary — it roughly matches the car sprite's own half-width, so the
car stops right at the edge of the window instead of half-vanishing off it.

**Now the car can move about freely left and right, but will be prevented
from disappearing off of the game screen.**

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
    """Pygame Zero calls this once every frame to repaint the window."""
    screen.fill(GRASS)

    player.draw()


def update():
    """Pygame Zero calls this once every frame, right before draw()."""
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    player.x = max(20, min(WIDTH - 20, player.x))
```

Notice there's no road yet — just a car on a green field. That's the whole
point of building in this order: this is already a "real," runnable program
with visible feedback, before we've touched anything more complicated. The
road is purely visual polish from here — nothing about *how the car moves*
changes for the rest of Part 1.

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

**Why a function, and not just a constant?** `road_center_x(row)` always
returns the exact same number right now (`WIDTH // 2`), so it *looks*
pointless — you could ask "why not just use a `ROAD_CENTER_X` constant?" The
payoff is a few weeks away: later in the course, this function starts
returning a *different* number depending on `row`, and that's what makes the
road curve. Because every other piece of the game always **asks this
function** where the road is (instead of assuming it knows), the road will
be able to curve later without rewriting any of the code that draws it or
drives on it. Plant that seed now; it's fine if it doesn't fully click until
Week 4.

**Math note — integer division (`//`):** `WIDTH // 2` and `ROAD_WIDTH // 2`
both use `//`, not `/`. Regular division (`/`) can produce a fraction (e.g.
`801 / 2 = 400.5`), but there's no such thing as half a pixel to draw at —
screen positions need to be whole numbers. `//` ("floor division") divides
and then rounds *down* to the nearest whole number, so `801 // 2 = 400`. Try
it in a Python shell if students want to see it directly.

**At this stage, running the game will not show any visible changes - we
have defined the bounds of the road in code, but have not drawn it.**

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

**Why a loop of strips, instead of one tall rectangle?** A single rectangle
would draw a straight road just fine — but it could never bend. Drawing the
road as a stack of many short horizontal strips means each strip could,
later, be shifted left or right by a *different* amount. Right now they all
line up (because `road_center_x()` always returns the same value), so it
just looks like one solid road. Nothing about this loop will need to change
when the road starts curving — only what `road_center_x()` returns.

**Math note — walking through one loop iteration:** say `top = 100` and
`strip_height = 20`.
- `row = top + strip_height // 2` → `100 + 10 = 110`. This is the **vertical
  middle** of the strip (which spans screen rows 100–120), not its top edge
  — that matters once `road_center_x()` varies smoothly by row, so the strip
  is positioned using the road's location at its *center*, not its edge.
- `center_x = road_center_x(row)` → `400` (still constant for now).
- `Rect(center_x - ROAD_WIDTH // 2, top, ROAD_WIDTH, strip_height)` →
  `Rect(400 - 110, 100, 220, 20)` → `Rect(290, 100, 220, 20)`.

**Math note — why subtract `ROAD_WIDTH // 2` at all?** `Rect(x, y, width,
height)` positions a rectangle by its **top-left corner**, not its center.
To draw a 220-pixel-wide rectangle *centered* on `x = 400`, its left edge
has to start 110 pixels to the left of center — otherwise the whole
rectangle would be drawn hanging off to the right of where you want it.
This "shift left by half the width" trick is exactly what `road_left()`
already computes — this loop is doing the same math inline, just for
drawing instead of for answering "is the car on the road?"

The `draw` function should now look like this:
```python
def draw():
    """Pygame Zero calls this once every frame to repaint the window."""
    screen.fill(GRASS)

    strip_height = 20
    for top in range(0, HEIGHT, strip_height):
        row = top + strip_height // 2
        center_x = road_center_x(row)

        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2, top, ROAD_WIDTH, strip_height),
            TARMAC,
        )

    player.draw()
```
**Running the game now shows a grey strip of road, but no shoulder or center line.**

## Step 6: Add the shoulder

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

**Why these two rectangles sit where they do:** the tarmac's left edge is at
`center_x - ROAD_WIDTH // 2` (that's the same expression `road_left()`
computes). The left shoulder needs to sit *immediately* to the left of that
edge, so its own left edge is pushed out one more `SHOULDER_WIDTH`:
`center_x - ROAD_WIDTH // 2 - SHOULDER_WIDTH`. The right shoulder is
simpler — it just starts exactly where the tarmac's right edge is
(`center_x + ROAD_WIDTH // 2`) and extends `SHOULDER_WIDTH` further right,
so no extra subtraction is needed on that side.

*Discussion prompt for faster students:* this loop is computing `center_x -
ROAD_WIDTH // 2` and `center_x + ROAD_WIDTH // 2` by hand, but we already
wrote `road_left(row)` and `road_right(row)` to compute exactly those two
values in Step 4. Could this code call those functions instead of repeating
the formula? (Yes — it's a nice cleanup, and a good way to check whether the
earlier functions actually clicked. We leave it written out longhand here
just to keep every number visible while it's new.)

So the draw function now looks like this:
```python
def draw():
    """Pygame Zero calls this once every frame to repaint the window."""
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

    player.draw()
```
**Running the game now shows a grey strip of road, with shoulder but no center line.**

## Step 7: Add the Center Line

Add this snippet after the tarmac logic:
```python
        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )
```

**Math note — how the dashing pattern works:** this is the trickiest bit of
math in Part 1, worth slowing down for.
- `top` increases by `strip_height` (20) every time through the loop: `0,
  20, 40, 60, ...`
- `top // strip_height` turns that into a plain strip **index**: `0, 1, 2,
  3, ...` — "this is the 0th strip, the 1st strip, the 2nd strip..."
- `% 2` (modulo 2) reduces any whole number down to just its remainder when
  divided by 2, which for whole numbers is always `0` or `1` — and it
  **alternates** every time the index goes up by one: `0, 1, 0, 1, 0, 1...`
- `== 0` turns that alternating `0`/`1` into `True`/`False`: `True, False,
  True, False, ...`

Put together: every *other* strip draws a short white rectangle, and the
rest don't — which is exactly what makes a solid line look "dashed." This
`x % 2 == 0` pattern (alternate every other item) is common enough to be
worth naming — it's the same trick used for striped table rows, checkerboard
patterns, and more.

So the draw function now looks like this:
```python
def draw():
    """Pygame Zero calls this once every frame to repaint the window."""
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
