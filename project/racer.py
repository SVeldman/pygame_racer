"""
Week 1, Part 1 - Draw the map, add the car, and drive it left and right.

WHAT THIS FILE DOES
--------------------
This is the starter code, or "stub" that you will build on to create your game.
It defines a series of Python variables that we will use in the first week of class.

Instead of making each of you type these out by hand, we've provided them for you ahead
of time so that you can focus on understanding HOW each piece works and WHAT it contributes.

USING PYGAME ZERO
--------------------
We will be using a Python library called PyGame Zero throughout this course (in coding,
a library is a collection of code that someone - maybe you, maybe someone else - wrote ahead
of time to make your task easier). To install PyGame Zero, run the following command in your
terminal:
    pip install pgzero

Once PyGame Zero is installed, you can run your game with the following command:
    pgzrun racer.py

NOTE: When running this command in your terminal, you need to be in the same directory
as the `racer.py` file (in the case, your project's root directory). If you run this command
and get a "file not found" error, you need to navigate your command line to the correct directory.

Another NOTE: Make sure the `images` folder stays in your project root along with `racer.py`.
This is where PyGame Zero will look for the racecar images we will use for our sprites. For now,
don't change or rename them (future code will be looking for specific files there).
"""

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

