"""Week 1, Part 1 - Draw the map.

WHAT THIS FILE DOES
--------------------
This is the very first step: before we drive a car anywhere, we need
somewhere to drive it. This file just opens a window and draws a road.
There is no player, no keyboard input, and nothing moves. If you run this,
you'll see a picture - that's the whole goal for today's first half hour.

Pygame Zero (pgzero) is a "batteries included" wrapper around Pygame that is
built for teaching. Two things to know up front:
  * It is NOT imported like a normal library. You never write
    `import pgzero` in a game file. Instead, you run the file with the
    `pgzrun` command, and pgzero quietly makes a handful of special names
    available to you: `screen`, `Rect`, `WIDTH`, `HEIGHT`, `Actor`,
    `keyboard`, and a few more. That's why you'll see `screen` and `Rect`
    used below even though nothing defines them in this file - pgzero does
    that for us.
  * Pygame Zero looks for two functions you write yourself: `draw()`, which
    it calls every frame to repaint the screen, and `update()`, which it
    calls every frame to move things around. This file only needs `draw()` -
    there is nothing to update yet!

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 01_week1_part1.py
"""

# ---------------------------------------------------------------------------
# SCREEN SIZE
# ---------------------------------------------------------------------------
# Pygame Zero reads WIDTH and HEIGHT once, when the window is first created,
# and uses them to size the window. (800, 600) is a comfortable default -
# wide enough to see the road and some grass on either side of it.
WIDTH = 800
HEIGHT = 600

# ---------------------------------------------------------------------------
# TUNING "KNOBS"
# ---------------------------------------------------------------------------
# We store measurements and settings in named constants (ALL_CAPS by
# convention) instead of typing raw numbers all over the place. That way,
# if we want a wider road later, we change ONE number instead of hunting
# through the whole file.
ROAD_WIDTH = 220        # how wide the grey tarmac is, in pixels
SHOULDER_WIDTH = 55     # width of the gravel strip on each side of the road

# ---------------------------------------------------------------------------
# COLOURS
# ---------------------------------------------------------------------------
# Pygame Zero colours are just (red, green, blue) tuples, each 0-255.
GRASS = (40, 120, 55)     # dark green - covers the whole background
GRAVEL = (150, 140, 110)  # tan - the "shoulder" strip beside the road
TARMAC = (60, 60, 68)     # dark grey - the actual road
LINE = (240, 240, 240)    # near-white - the dashed centre line


# ---------------------------------------------------------------------------
# WHERE IS THE ROAD?
# ---------------------------------------------------------------------------
# These three little functions answer "where is the road, at this height on
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


def draw():
    """Pygame Zero calls this once every frame to repaint the window."""

    # Start by covering the whole window in grass. Everything we draw after
    # this gets painted on top of it.
    screen.fill(GRASS)

    # We draw the road as a stack of thin horizontal strips, rather than one
    # tall rectangle. Right now every strip lines up perfectly, so it just
    # looks like one long straight road - but building it this way means
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

# Notice there's no update() function in this file at all - that's allowed!
# Pygame Zero is happy with a game that only draws a picture and never
# changes it. We'll add update() (and a car to move around) in Part 2.
