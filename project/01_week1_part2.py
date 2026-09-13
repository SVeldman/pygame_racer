"""Week 1, Part 2 - Add the car, and drive it left and right.

WHAT'S NEW SINCE PART 1
------------------------
Part 1 only drew a road. Now we add:
  * a car (a Pygame Zero `Actor`) sitting on the road
  * `update()`, a new function pgzero calls every frame, where we read the
    keyboard and move the car

There is still NO concept of speed yet - press an arrow key and the car
snaps left or right by a fixed amount every frame. It doesn't build up speed,
it doesn't slow down on the grass, and it can't crash. All of that comes in
Week 2. For now, the goal is just: "I press a key, my car moves."

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 02_week1_part2.py
"""

WIDTH = 800
HEIGHT = 600

# --- Tuning "knobs" ---------------------------------------------------------
ROAD_WIDTH = 220
SHOULDER_WIDTH = 55
PLAYER_ROW = 480          # how far down the screen the car sits, in pixels

# --- Colours -----------------------------------------------------------------
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)


def road_center_x(row):
    return WIDTH // 2


def road_left(row):
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
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

    # Draw the car on top of the road. If you comment this line out, the car
    # will still exist and still move (because update() still runs) - it
    # just won't be visible. draw() and update() are separate jobs:
    # update() changes WHERE things are, draw() shows what's there right now.
    player.draw()


def update():
    """Pygame Zero calls this once every frame, right before draw()."""

    # `keyboard` is another pgzero special name - it's always up to date
    # with which keys are currently held down. `keyboard.left` is True for
    # every single frame the left arrow is held, not just the first one, so
    # holding the key moves the car continuously.
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5

    # Without this, the car could be steered right off the edge of the
    # window and disappear. `max(...)` and `min(...)` together "clamp" a
    # value between a low and a high bound - a very common pattern anywhere
    # you need to keep a number inside a range.
    player.x = max(20, min(WIDTH - 20, player.x))

    # Notice there's nothing here checking whether the car is on the road,
    # the shoulder, or the grass - right now they all feel identical to
    # drive on. That distinction, and the whole idea of a "speed" the car
    # can build up or lose, is exactly what Week 2 adds.
