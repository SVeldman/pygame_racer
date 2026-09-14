"""Week 1, Part 1 - Draw the map, add the car, and drive it left and right.

WHAT THIS FILE DOES
--------------------
By the end of this section:
  * a road is drawn - grass, a gravel shoulder, and tarmac
  * a car (a Pygame Zero `Actor`) sits on it, and the arrow keys move it
    left and right

There is NO concept of speed yet - press an arrow key and the car moves left
or right by a fixed amount every frame. It doesn't build up speed, it
doesn't slow down on the grass, and it can't crash. All of that comes in
Part 2. For now, the goal is just: "I press a key, my car moves."

Pygame Zero (pgzero) is a wrapper around Pygame that is built for teaching.
Two things remember:
  * It is NOT imported like a normal library. You never write
    `import pgzero` in a game file. Instead, you run the file with the
    `pgzrun` command, and pgzero quietly makes a handful of special names
    available to you: `screen`, `Rect`, `WIDTH`, `HEIGHT`, `Actor`,
    `keyboard`, and a few more. That's why you'll see `screen` and `Rect`
    used below even though nothing defines them in this file - pgzero does
    that for us.
  * Pygame Zero looks for two functions you write yourself: `draw()`, which
    it calls every frame to repaint the screen, and `update()`, which it
    calls every frame to move things around.

Run it with (from inside the `project` folder):
    pgzrun 01_week1_part1.py
"""

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
# WHERE IS THE ROAD?
# ---------------------------------------------------------------------------
# These three functions answer "where is the road, at this height on
# the screen?" Right now the answer never changes (the road runs straight up
# the middle), so road_center_x always returns the same number. We're
# writing it as a FUNCTION rather than a plain constant on purpose: in a
# later week, we'll make the road curve by having this function return a
# *different* number depending on how far along the track you are. Nothing
# else in the file will need to change when that happens, because
# everything else already asks this function where the road is instead of
# assuming it knows.
def road_center_x(row):
    """X position of the MIDDLE of the road at a given screen row (y value).

    `row` isn't used yet - the road is straight, so every row has the same
    centre. It's already a parameter so this function's "shape" won't need
    to change later when the road starts to curve.
    """
    return WIDTH // 2


def road_left(row):
    """X position of the LEFT edge of the tarmac at this row."""
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
    """X position of the RIGHT edge of the tarmac at this row."""
    return road_center_x(row) + ROAD_WIDTH // 2


# ---------------------------------------------------------------------------
# THE PLAYER'S CAR
# ---------------------------------------------------------------------------
# `Actor` is a Pygame Zero class that bundles together an image, a position,
# and handy helpers like `.draw()` and `.colliderect()`. `Actor("car_red", ...)`
# looks for a file called `images/car_red.png` (pgzero always looks in a
# folder named exactly `images`, right next to your game file).
#
# This line runs ONCE, when the file first loads - it creates the car and
# places it at the horizontal centre of the screen, on PLAYER_ROW. Every
# frame after that, `update()` below is what actually moves it.
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))


def draw():
    """Pygame Zero calls this once every frame to repaint the window."""

    # Start by covering the whole window in grass. Everything we draw after
    # this gets painted on top of it.
    screen.fill(GRASS)

    # We draw the road as a stack of thin horizontal strips, rather than one
    # tall rectangle. Right now every strip lines up perfectly, so it just
    # looks like one long straight road. But building it this way means
    # that later, when the road curves, we can shift each strip left or
    # right by a different amount and the road will visibly bend. None of
    # this drawing code will need to be rewritten when that happens.
    strip_height = 20
    for top in range(0, HEIGHT, strip_height):
        # `row` is the vertical centre of this particular strip. We look up
        # the road's position at that row (even though, for now, it's
        # always the same answer).
        row = top + strip_height // 2
        center_x = road_center_x(row)

        # The gravel SHOULDER sits just outside the tarmac on both sides.
        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2 - SHOULDER_WIDTH, top,
                 SHOULDER_WIDTH, strip_height),
            GRAVEL,
        )
        screen.draw.filled_rect(
            Rect(center_x + ROAD_WIDTH // 2, top, SHOULDER_WIDTH, strip_height),
            GRAVEL,
        )

        # The tarmac itself, centered on center_x.
        screen.draw.filled_rect(
            Rect(center_x - ROAD_WIDTH // 2, top, ROAD_WIDTH, strip_height),
            TARMAC,
        )

        # A dashed white line down the middle of the road. Skipping every
        # other strip is what makes it look "dashed" instead of solid.
        if (top // strip_height) % 2 == 0:
            screen.draw.filled_rect(
                Rect(center_x - 3, top + 3, 6, strip_height - 6), LINE
            )

    # Draw the car on top of the road. If you comment this line out, the car
    # will still exist and still move (because update() still runs) - it
    # just won't be visible. draw() and update() are separate jobs:
    # update() changes WHERE things are, draw() shows what's there right now.
    player.draw()


def update():
    """Pygame Zero calls this once every frame, right before draw()."""

    # `keyboard` is another pgzero special name. It's always up to date
    # with which keys are currently held down. `keyboard.left` is True for
    # every single frame the left arrow is held, not just the first one, so
    # holding the key moves the car continuously.
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    # Without this, the car could be steered off the edge of the
    # window and disappear. `max(...)` and `min(...)` together "clamp" a
    # value between a low and a high bound - a very common pattern anywhere
    # you need to keep a number inside a range.
    player.x = max(20, min(WIDTH - 20, player.x))

    # Notice there's nothing here checking whether the car is on the road,
    # the shoulder, or the grass. Right now they all feel identical to
    # drive on. That distinction, and the whole idea of a "speed" the car
    # can build up or lose, is exactly what Part 2 adds.
