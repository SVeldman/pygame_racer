# Pygame Zero Vertical Racer — Game Design & Curriculum

A teaching project: students build a top-locked vertical scrolling racer with a
road that turns, AI opponents, crashes, and a finish line. Core build is **4
one-hour lessons**, with a **5th bonus week** for advanced students.

---

## 1. Game concept

You drive a car that stays near the bottom of the screen, facing up. You never
rotate — "forward speed" is faked by scrolling the road and the other cars
downward. The road is a **narrow band** that snakes left and right down the
course. Stray onto the rough shoulder and you lose speed; leave the road
entirely on a turn and you crash out. Pass the AI cars, survive to the target
distance, and you win.

### Core mechanics at a glance

| Element | Rule |
|---|---|
| Player movement | Left / right only, clamped to the screen. No rotation. |
| Speed | `player_speed` scalar. Accelerate / brake keys change it. |
| Forward progress | `distance_traveled += player_speed` each frame. |
| Race end | `distance_traveled >= FINISH_DISTANCE` → you win. |
| Road | A band `ROAD_WIDTH` wide, centered on `road_center_x(row)`. |
| Rough shoulder | A strip on each side of the road. On it → speed bleeds down fast. |
| Turns | `road_center_x` varies with distance, so the band drifts sideways. |
| Off-road on a turn | Past the shoulder during a turn segment → crash out. |
| Opponents | Cars with a `base_speed`; move by relative speed; `colliderect` → crash. |

Everything is 2D grid math — no trigonometry, no pseudo-3D projection, no
physics engine.

---

## 2. The one idea that makes turns simple: `road_center_x(row)`

"Center-X" is the X coordinate of the **middle of the road** at a given screen
row. At that row the road covers:

```
left edge  = road_center_x(row) - ROAD_WIDTH // 2
right edge = road_center_x(row) + ROAD_WIDTH // 2
```

On an 800-wide screen with `ROAD_WIDTH = 220`:

```
        rough        ROAD          rough
   0 ......|############|...... 800
          290   400   510
                 ^ road_center_x = 400
```

**A straight road** just returns the same number for every row:

```python
def road_center_x(row):
    return 400
```

**A turn** is nothing more than that function returning different values as you
travel — the band jogs diagonally across the screen:

```
row (top)     road_center_x     road spans
-------------------------------------------------
  40             520            410 .. 630
 120             480            370 .. 590
 200             440            330 .. 550
 280 (player)    400            290 .. 510   <- road curving right as you climb
```

Because **every** part of the game asks `road_center_x()` where the road is —
the drawing code, the rough-shoulder check, the crash check, the opponent
placement — turning the road on in Lesson 4 is a change to **one function**, not
a rewrite.

> **Instructor note:** enforce this from Lesson 1. If students hard-code numbers
> like `290` and `510` for the road edges, Lesson 4 becomes painful. If they
> always call `road_center_x(row)`, Lesson 4 is easy.

---

## 3. Data structures

### Screen / tuning constants

```python
WIDTH, HEIGHT     = 800, 600
ROAD_WIDTH        = 220
SHOULDER_WIDTH    = 60
PLAYER_ROW        = 500          # fixed screen Y of the player car
MAX_SPEED         = 10
ROUGH_MAX_SPEED   = 4            # speed you get dragged down to on the shoulder
FINISH_DISTANCE   = 5000
```

### The track (added in Lesson 4)

A list of segments, each covering a chunk of distance and holding a target
center-X. `road_center_x(row)` converts a screen row to a track distance, finds
the segment there, and interpolates.

```python
# (length_in_distance_units, center_x_at_end_of_segment)
TRACK = [
    (800, 400),   # straight
    (400, 250),   # curve left
    (600, 250),   # straight
    (400, 550),   # curve right
    (500, 400),   # straight back to center
    # ... repeats / extends to FINISH_DISTANCE
]
```

### Opponent cars

Stored by **world position**, not screen position:

```python
enemy = {
    "distance": 1800,   # how far along the course this car is
    "lane": 0.25,       # 0.0 = left edge of road, 1.0 = right edge
    "base_speed": 7,
}
```

Screen position is derived every frame:

```python
row = PLAYER_ROW - (enemy["distance"] - distance_traveled)
x   = road_center_x(row) + (enemy["lane"] - 0.5) * ROAD_WIDTH
```

Because `x` runs through `road_center_x()`, opponents hug every curve for free.

### Game state

```python
player_speed     = 0
distance_traveled = 0
game_state       = "racing"   # "racing" | "crashed" | "won"
enemies          = []
```

---

## 4. The 4-lesson core curriculum

Each lesson ends with a game that is visibly better than the last. Provide a
**checkpoint file** (`lesson_1_end.py`, `lesson_2_end.py`, …) so a class that
runs slow can start the next week from a known-good state.

### Lesson 1 — Control, the road, and the rough

**Goal:** a car you can drive left and right on a straight road, with rough
shoulders that slow you down.

**Concepts taught:**
- The Pygame Zero skeleton: `draw()`, `update()`, `WIDTH`/`HEIGHT`.
- `Actor`, drawing, positioning.
- `keyboard.left` / `keyboard.right`, clamping to screen bounds.
- Writing and calling a helper function (`road_center_x`, returning a constant).
- A boolean check: is the player on the road or the shoulder?

**By the end:** car drives side to side; driving onto the grass/shoulder drags
speed down to `ROUGH_MAX_SPEED`; back on tarmac, speed recovers.

**Pitfalls:**
- Images must be lowercase `.png` in an `images/` folder — `Actor('car')` needs
  `images/car.png`. Capital letters or `.PNG` crash instantly.
- Make sure students route the road edges through `road_center_x()` — do a quick
  code check before they leave.

### Lesson 2 — The illusion of speed

**Goal:** the road scrolls, so it feels like you are driving forward; you can
accelerate and brake.

**Concepts taught:**
- `player_speed` as a variable "knob"; accelerate/brake keys.
- Infinite scroll: two copies of the road art (or repeating dashed lane lines)
  moved downward and wrapped to the top.
- `distance_traveled` as an accumulator.
- Drawing text with `screen.draw.text` (speed, distance).

**By the end:** holding the gas scrolls the road faster; releasing slows it; a
distance counter climbs.

**Pitfalls:**
- The scroll-wrap math is the classic brain-twister. Give it as a copyable
  snippet on the projector:
  ```python
  road_y = (road_y + player_speed) % road_height
  # draw the image at road_y and at road_y - road_height
  ```

### Lesson 3 — Competitors and the race *(heaviest lesson)*

**Goal:** AI cars to race against, crashes, a game-over screen, and a finish
line.

**Concepts taught:**
- Python lists; looping over a list in `update()` and `draw()`.
- `random.choice` / `random.uniform` to spawn enemies in random lanes ahead.
- Relative-speed movement:
  ```python
  enemy["distance"] += enemy["base_speed"]
  # its screen row = PLAYER_ROW - (enemy["distance"] - distance_traveled)
  ```
- `player.colliderect(enemy_actor)` → set `game_state = "crashed"`.
- Win check: `distance_traveled >= FINISH_DISTANCE` → `game_state = "won"`.
- Branching `draw()` on `game_state`.

**By the end:** a real race — pass cars by out-accelerating them, hitting one
ends the run, reaching the finish distance wins.

**Pitfalls:**
- This lesson has the most moving parts. Consider splitting: spawning + movement
  first, then collisions + end states. Have `lesson_3_end.py` ready.
- Enemies spawning on top of the player — spawn them well above the screen
  (`distance` comfortably greater than `distance_traveled + a screen height`).

### Lesson 4 — Drift (the turns)

**Goal:** the road curves.

**Concepts taught:**
- Replacing a constant with a computed value: `road_center_x()` now reads the
  `TRACK` list.
- Mapping a screen row → track distance → segment → interpolated center-X.
- Redrawing the road as a stack of horizontal strips, each offset by its own
  `road_center_x(row)` (no scaling, just horizontal shift). Alternatively, shift
  a single road-band sprite per row.
- A richer rule: on turn segments, off-road = crash, not just slow.

**By the end:** the road snakes left and right; you must steer through curves;
opponents follow the curves automatically (they already use `road_center_x()`).

**Pitfalls:**
- Keep the strip height reasonable (e.g. 10–20px) — 1px strips are smooth but
  slow and fiddly.
- Provide the drift-accumulation + strip-drawing snippet. Students should *use*
  it and understand it, not derive it.
- Test that the rough/crash check uses `road_center_x(player_row)`, not a stale
  constant.

---

## 5. Bonus week (Lesson 5) — advanced & open-ended

Self-paced. Pick from:

- **Two-player shared screen:** add `player2 = Actor('car_blue')` on `W/A/S/D`;
  both race the AI on the same road; scroll based on the leader's speed. Whoever
  falls off the bottom respawns with a time penalty. *(Low rendering cost.)*
- **True split-screen:** split the window down the middle, clip each player's
  world to their half with `screen.surface.set_clip(...)`. *(Advanced — expect
  extra debugging of coordinate offsets.)*
- **Customization / juice:** sprite swaps, tuning the knobs (`MAX_SPEED`,
  `base_speed`, drift strength, `ROAD_WIDTH`), oil slicks that spin the car,
  fuel pickups that end the race if you run dry, engine/crash sounds via
  `sounds.play()`.

---

## 6. Feasibility & risk

**Verdict: achievable in 4 hours — if the prep below is done.** Without it,
budget 5–6 sessions.

| Requirement | Why it matters |
|---|---|
| Asset pack pre-made, lowercase `.png` in `images/` | The #1 source of student crashes; also saves coding time. |
| Copy-paste snippets for: scroll-wrap math, drift accumulation, strip drawing | These are the parts students should use and understand, not invent under time pressure. |
| `road_center_x()` helper used everywhere from Lesson 1 | Single biggest risk mitigation — makes Lesson 4 a one-function change. |
| Checkpoint file per lesson (`lesson_N_end.py`) | A slow week doesn't cascade into the next. |

**Highest-risk lesson:** Lesson 3 (most moving parts). Have a fallback plan to
push collisions/end-states into the start of Lesson 4 if needed.

---

## 7. Asset-pack checklist

Deliver on day one, all lowercase `.png`, in `images/`:

- [ ] `car_red.png` — player car (top-down, facing up), ~40×70px
- [ ] `car_blue.png`, `car_green.png`, `car_yellow.png` — opponents / player 2
- [ ] `road.png` — vertically tileable road-band texture, `ROAD_WIDTH` wide
- [ ] `grass.png` or `rough.png` — shoulder / off-road texture, tileable
- [ ] `finish.png` — checkered finish-line banner
- [ ] Optional: `oil.png`, `fuel.png` for the bonus week
- [ ] Optional sounds in `sounds/`: `engine.wav`, `crash.wav`, `skid.wav`
