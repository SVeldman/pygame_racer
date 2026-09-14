"""Week 1, Part 2 - Speed, and the difference between road, shoulder, and rough.

WHAT'S NEW SINCE PART 1
-------------------------
Part 1 ended with a car that snaps left and right with no consequences. Now
we add:
  * `player_speed`, a number that goes up automatically while you're on the
    tarmac, capped at `MAX_SPEED`
  * a real difference between three "zones": the ROAD (tarmac), the
    SHOULDER (the gravel strip beside it), and the ROUGH (the grass beyond
    that) - straying off the tarmac costs you speed, and straying further
    costs you more

The car still doesn't move up the screen (no scrolling yet - that's next
week's job). For now, "speed" is just a number you can watch climb and fall
on the HUD as you drift on and off the road. This lays the groundwork Week 2
needs: once we HAVE a speed number, we can use it to scroll the road.

Run it with (from inside the `project` folder):
    pip install pgzero
    pgzrun 01_week1_part2.py
"""

WIDTH = 800
HEIGHT = 600

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
# Think of every constant below as a dial you could turn. Try changing a few
# of these numbers and re-running the game to see what happens - that's the
# fastest way to build intuition for what each one actually controls.
ROAD_WIDTH = 220                        # width of the grey tarmac
SHOULDER_WIDTH = 55                     # width of the gravel strip on each side
PLAYER_ROW = 480                        # the car's fixed height on the screen (y)
MAX_SPEED = 10                          # top speed, reached only on tarmac
SHOULDER_MAX_SPEED = MAX_SPEED * 0.7    # speed the shoulder drags you down to
ROUGH_MAX_SPEED = MAX_SPEED * 0.4       # speed the rough drags you down to
ACCEL = 0.10                            # how much speed builds up each frame
BRAKE = 0.30                            # how much speed drops each frame off-road

# --- Colours -----------------------------------------------------------------
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

# ---------------------------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------------------------
# Unlike the constants above, these two values CHANGE while the game runs -
# player.x moves every time you press an arrow key, and player_speed climbs
# and falls every frame. Pygame Zero keeps calling update() and draw() with
# these same variables, frame after frame, so changes here "stick" between
# frames instead of resetting.
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0


def road_center_x(row):
    """X position of the MIDDLE of the road at a given screen row.

    Still always the centre of the screen - the road doesn't curve until a
    later week. Everything below asks THIS function where the road is,
    rather than hard-coding a number, precisely so that this one function is
    the only thing that will need to change later.
    """
    return WIDTH // 2


def road_left(row):
    return road_center_x(row) - ROAD_WIDTH // 2


def road_right(row):
    return road_center_x(row) + ROAD_WIDTH // 2


def on_road(x, row):
    """True if x is on the tarmac at this row."""
    return road_left(row) <= x <= road_right(row)


def on_shoulder(x, row):
    """True if x is on the gravel shoulder - off the road, but not into the
    rough (grass) yet."""
    if on_road(x, row):
        return False
    return road_left(row) - SHOULDER_WIDTH <= x <= road_right(row) + SHOULDER_WIDTH


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

    # --- NEW PART: HUD (heads-up display) ---
    # screen.draw.text draws text directly onto the window. We show the
    # current speed at all times, and only show a warning when the car has
    # left the tarmac - and a DIFFERENT warning depending on how far off it
    # is. Checking on_shoulder() first, and on_road() second, matters: a car
    # that's off the road AND not on the shoulder must be out in the rough.
    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    if on_shoulder(player.x, PLAYER_ROW):
        screen.draw.text("ON THE SHOULDER", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 220, 120))
    elif not on_road(player.x, PLAYER_ROW):
        screen.draw.text("ON THE ROUGH!", midtop=(WIDTH // 2, 10),
                         fontsize=34, color=(255, 90, 60))


def update():
    global player_speed

    # Steering hasn't changed from Part 1.
    if keyboard.left:
        player.x -= 5
    if keyboard.right:
        player.x += 5
    player.x = max(20, min(WIDTH - 20, player.x))

    # --- NEW PART: three-tier speed ---
    # Every frame, we check which of the three zones the car is in right
    # now, and nudge player_speed toward that zone's speed limit:
    #   * on the road: speed climbs by ACCEL, up to MAX_SPEED
    #   * on the shoulder: speed falls by BRAKE, but never below
    #     SHOULDER_MAX_SPEED
    #   * out in the rough: speed falls by BRAKE, but never below
    #     ROUGH_MAX_SPEED (a lower ceiling than the shoulder's)
    # Because this check re-runs every single frame, moving back onto the
    # road immediately starts you accelerating again - there's no
    # "penalty timer," just a different rule for whichever zone you're in
    # right now.
    if on_road(player.x, PLAYER_ROW):
        if player_speed < MAX_SPEED:
            player_speed += ACCEL
    elif on_shoulder(player.x, PLAYER_ROW):
        if player_speed > SHOULDER_MAX_SPEED:
            player_speed -= BRAKE
    else:
        if player_speed > ROUGH_MAX_SPEED:
            player_speed -= BRAKE

    # Without this line, repeatedly adding ACCEL or subtracting BRAKE could
    # push player_speed slightly above MAX_SPEED or below 0 (for example, if
    # BRAKE is bigger than the gap remaining). Clamping after every change
    # guarantees it always stays in the sensible range.
    player_speed = max(0.0, min(MAX_SPEED, player_speed))
