# Week 4, Part 2 Walkthrough — A Real, Multi-Turn Lap

Nothing mechanically new this session — every idea already exists in Part 1.
The only thing that changes is the data in `TRACK` itself: instead of three
segments (a demo), we describe a full lap with turns spread across the
*whole* race instead of clustered near the start. This is a short, light
session — use the extra time for review, or a head start on Week 5.


## Step 1: One More Rival

Bump the rival count and add a fourth color to choose from:

```python
NUM_RIVALS = 4
```
```python
RIVAL_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange"]
```
*Expected State: a fourth rival on the starting grid. The track itself is
still Part 1's tiny 3-segment demo curve — `TRACK` hasn't changed yet.*

**Teaching Note:** bumping `NUM_RIVALS` needed no other code changes
anywhere. `LANE_COUNT`, `ROAD_WIDTH`, `WIDTH`, and the starting grid all
recompute themselves from it. That's the same "just data" idea Step 2 is
about to apply to `TRACK` itself.


## Step 2: Replace the Demo Track With a Full Lap

Replace the entire `TRACK` list:

```python
# ---------------------------------------------------------------------------
# THE TRACK - a full lap
# ---------------------------------------------------------------------------
CENTER = WIDTH // 2
TRACK = [
    (300, CENTER),          # starting straight
    (300, CENTER - 150),    # curve left
    (250, CENTER - 150),    # brief straight, holding left
    (350, CENTER + 160),    # sweeping curve right
    (250, CENTER + 160),    # brief straight, holding right
    (300, CENTER),          # curve back to the middle
    (250, CENTER - 120),    # curve left
    (350, CENTER + 120),    # curve right
    (300, CENTER),          # curve back to centre
    (300, CENTER - 140),    # curve left
    (250, CENTER - 140),    # brief straight, holding left
    (350, CENTER + 150),    # sweeping curve right
    (350, CENTER),          # curve back to centre for the finish
]
FINISH_DISTANCE = sum(length for length, _ in TRACK)
```
*Expected State: a full lap — a real, twisting course with a turn to react
to every few hundred metres, the whole way around. All four rivals track
it automatically, exactly as before.*

**The Concept:** short straights connect a series of curves in alternating
directions, so there's a turn every few hundred metres for the whole race —
nothing like Part 1's single demo curve. Read the list top to bottom and
you're reading the shape of the track: start straight, sweep left, hold
left briefly, sweep hard right, hold right briefly, curve back to centre,
curve left, curve right, and settle at centre for the finish.

**Teaching Note:** `_segment_at()`, `center_x_at_distance()`, `is_turn_at()`,
and `road_center_x()` all work exactly as they did with the 3-segment demo.
A list of `(length, center)` pairs is a list of `(length, center)` pairs,
whether it has 3 entries or 13. `FINISH_DISTANCE` recomputes itself from
whatever `TRACK` currently contains, so it stays correct without anyone
updating it by hand.

**Classroom Demo:** temporarily set every `center` value in `TRACK` to
`CENTER` and rerun. The road runs perfectly straight — the same shape as
Part 1 before curves existed — with none of the surrounding code touched.
Restore the full lap afterward.

**Classroom Prompt (For Fast Finishers):** what happens to a stretch of
track where two *consecutive* entries share the same `center` value — does
it curve, or run straight? (Straight. `is_turn_at()` only reports a turn
when a segment's start and end centres differ.)


## Suggested In-Class Exercise: Design Your Own Track

Give students the last 10-15 minutes to design their own `TRACK` — a
hairpin-heavy course, a mostly straight course with one dramatic sweep,
whatever they want. `FINISH_DISTANCE` is derived from `TRACK`'s own total
length, so this is safe to hand to students without them touching any other
constant: lengthening a straight, sharpening a turn, or adding a whole new
bend is purely a data change.

**Watch for:** a `TRACK` with very few segments but very large `center`
swings between them can produce sharper, more sudden-feeling curves than a
gentle multi-segment sweep — a good excuse to talk about why the current
track uses several smaller steps for each direction change instead of one
giant jump.


## Checkpoint: Final Code for Week 4, Part 2

The full script should now match `04_week4_part2.py` — the finished,
playable game from the end of the core curriculum.

```python
import random

### CONSTANTS
NUM_RIVALS = 4
LANE_COUNT = NUM_RIVALS + 1
LANE_WIDTH = 110
ROAD_WIDTH = LANE_WIDTH * LANE_COUNT
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

RIVAL_COLORS = ["car_blue", "car_green", "car_yellow", "car_orange"]

GRASS_MARGIN = 200
WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN
HEIGHT = 600

FPS = 60
COUNTDOWN_NUMBERS = [3, 2, 1]
COUNTDOWN_FRAMES = len(COUNTDOWN_NUMBERS) * FPS + FPS // 3
FREEZE_FRAMES = 2 * FPS

### TRACK
CENTER = WIDTH // 2
TRACK = [
    (300, CENTER),
    (300, CENTER - 150),
    (250, CENTER - 150),
    (350, CENTER + 160),
    (250, CENTER + 160),
    (300, CENTER),
    (250, CENTER - 120),
    (350, CENTER + 120),
    (300, CENTER),
    (300, CENTER - 140),
    (250, CENTER - 140),
    (350, CENTER + 150),
    (350, CENTER),
]
FINISH_DISTANCE = sum(length for length, _ in TRACK)

### COLOURS
GRASS = (40, 120, 55)
GRAVEL = (150, 140, 110)
TARMAC = (60, 60, 68)
LINE = (240, 240, 240)

### GAME STATE
player = Actor("car_red", (WIDTH // 2, PLAYER_ROW))
player_speed = 0.0
distance_traveled = 0.0
rivals = []
game_state = "waiting"
race_results = []
player_place = None
countdown_timer = 0
freeze_timer = 0
player_start_lane = 0.0


### TRACK MATH
def _segment_at(dist):
    start_center = CENTER
    covered = 0
    for length, end_center in TRACK:
        if dist < covered + length:
            fraction = (dist - covered) / length
            return start_center, end_center, fraction
        covered += length
        start_center = end_center
    return start_center, start_center, 1.0


def center_x_at_distance(dist):
    start_center, end_center, fraction = _segment_at(dist)
    return start_center + (end_center - start_center) * fraction


def is_turn_at(dist):
    start_center, end_center, _ = _segment_at(dist)
    return start_center != end_center


def dist_at(y):
    return distance_traveled + (PLAYER_ROW - y)


def row_at(dist):
    return PLAYER_ROW - (dist - distance_traveled)


### ROAD
def road_center_x(y):
    return center_x_at_distance(dist_at(y))


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


def lane_to_x(lane, y):
    return road_left(y) + lane * ROAD_WIDTH


### RACE SETUP
def new_race():
    global player_speed, distance_traveled, rivals, game_state, player_start_lane
    global race_results, player_place
    player_speed = 0.0
    distance_traveled = 0.0
    game_state = "waiting"
    race_results = []
    player_place = None

    grid = list(range(LANE_COUNT))
    random.shuffle(grid)
    player_start_lane = (grid[0] + 0.5) / LANE_COUNT
    player.pos = (lane_to_x(player_start_lane, PLAYER_ROW), PLAYER_ROW)

    rival_colors = random.sample(RIVAL_COLORS, k=len(grid) - 1)
    rivals = [
        {
            "actor": Actor(color),
            "distance": 0,
            "lane": (lane_i + 0.5) / LANE_COUNT,
            "base_speed": random.uniform(5.0, 8.5),
            "finished": False,
            "state": "racing",
            "freeze_timer": 0,
        }
        for lane_i, color in zip(grid[1:], rival_colors)
    ]
    for r in rivals:
        r["actor"].pos = (lane_to_x(r["lane"], PLAYER_ROW), PLAYER_ROW)


new_race()


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
            for lane_i in range(1, LANE_COUNT):
                divider_x = center_x - ROAD_WIDTH // 2 + lane_i * LANE_WIDTH
                screen.draw.filled_rect(Rect(divider_x - 4, top, 8, strip_height), LINE)

    finish_y = row_at(FINISH_DISTANCE)
    if -20 < finish_y < HEIGHT:
        left = road_center_x(finish_y) - ROAD_WIDTH // 2
        for i in range(0, ROAD_WIDTH, 20):
            color = "white" if (i // 20) % 2 == 0 else "black"
            screen.draw.filled_rect(Rect(left + i, finish_y - 8, 20, 16), color)

    for r in rivals:
        if r["state"] != "frozen" or (r["freeze_timer"] // 6) % 2 == 0:
            r["actor"].draw()
    if game_state != "frozen" or (freeze_timer // 6) % 2 == 0:
        player.draw()

    screen.draw.text(f"Speed: {player_speed:0.1f}", topleft=(10, 10),
                     fontsize=30, color="white")
    screen.draw.text(f"Distance: {int(distance_traveled)} / {FINISH_DISTANCE} m",
                     topleft=(10, 40), fontsize=30, color="white")

    if game_state == "frozen":
        screen.draw.text("CRASHED! Recovering...", midtop=(WIDTH // 2, 10),
                         fontsize=32, color=(255, 90, 60))
    elif game_state == "racing" and is_turn_at(distance_traveled):
        screen.draw.text("TURN - stay on the road!", midtop=(WIDTH // 2, 10),
                         fontsize=32, color=(255, 220, 120))

    if game_state == "waiting":
        _banner("READY TO RACE?", "Press SPACE to start")
    elif game_state == "countdown":
        _draw_countdown()
    elif game_state == "won":
        title = "YOU WIN!" if player_place == 1 else f"YOU FINISHED {_ordinal(player_place)}!"
        _banner(title, "Press SPACE to race again")


def _draw_countdown():
    elapsed = COUNTDOWN_FRAMES - countdown_timer
    counting_frames = len(COUNTDOWN_NUMBERS) * FPS
    if elapsed < counting_frames:
        number = COUNTDOWN_NUMBERS[elapsed // FPS]
        _banner(str(number), "Get ready...")
    else:
        _banner("GO!", "")


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}TH"
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"


def _banner(title, subtitle):
    screen.draw.filled_rect(Rect(0, HEIGHT // 2 - 60, WIDTH, 120), (0, 0, 0))
    screen.draw.text(title, center=(WIDTH // 2, HEIGHT // 2 - 15),
                     fontsize=60, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, HEIGHT // 2 + 30),
                     fontsize=30, color="white")


### UPDATE
def update():
    global player_speed, distance_traveled, game_state, player_place
    global countdown_timer, freeze_timer

    if game_state == "waiting":
        if keyboard.space:
            game_state = "countdown"
            countdown_timer = COUNTDOWN_FRAMES
        return

    if game_state == "countdown":
        countdown_timer -= 1
        if countdown_timer <= 0:
            game_state = "racing"
        return

    if game_state == "won":
        if keyboard.space:
            new_race()
        return

    if game_state == "frozen":
        freeze_timer -= 1
        if freeze_timer <= 0:
            game_state = "racing"
    else:
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

    for r in rivals:
        if r["state"] == "frozen":
            r["freeze_timer"] -= 1
            if r["freeze_timer"] <= 0:
                r["state"] = "racing"
        if r["state"] == "racing":
            r["distance"] += r["base_speed"]
            y = row_at(r["distance"])
            r["actor"].pos = (lane_to_x(r["lane"], y), y)
            if not r["finished"] and r["distance"] >= FINISH_DISTANCE:
                r["finished"] = True
                race_results.append(r)

    if game_state == "racing":
        for r in rivals:
            if player.colliderect(r["actor"]):
                game_state = "frozen"
                freeze_timer = FREEZE_FRAMES
                player_speed = 0.0
                r["state"] = "frozen"
                r["freeze_timer"] = FREEZE_FRAMES
                player.x = lane_to_x(player_start_lane, PLAYER_ROW)
                r["actor"].x = lane_to_x(r["lane"], row_at(r["distance"]))
                break

        if distance_traveled >= FINISH_DISTANCE:
            player_place = len(race_results) + 1
            game_state = "won"
```
*Expected State: a complete, playable racing game — a full 13-segment lap,
four rivals, a countdown, collisions, and a finish line. This is the last
checkpoint of the core 4-week curriculum.*

**Up Next:** Week 5 is optional bonus content. Part 1 turns the "READY TO
RACE?" screen into a real start menu (car choice, race length, AI
difficulty); Part 2 adds a second human player sharing the keyboard.
