# Week 2 — Instructor Overview

## Run it

```bash
cd project
pgzrun 02_week2_part1.py       # or 02_week2_part2.py
```

## Part 1 — `02_week2_part1.py`: The road scrolls

**Goal for students:** feel like you're driving forward for the first time.

| Concept | Where it shows up |
|---|---|
| An accumulator that only ever grows | `distance_traveled += player_speed` |
| The scrolling illusion (nothing moves — we just draw based on distance) | `dist_at(y)`, the dash-drawing condition |
| UP/DOWN throttle and brake replacing last week's auto-accelerate | `update()` |
| Coasting — speed bleeding off on its own when no key is held | `COAST` |

**The idea to put on the board:** `dist_at(y) = distance_traveled + (PLAYER_ROW - y)`.
A point drawn higher on screen (smaller `y`) is further ahead on the track.
The dashed line is painted wherever that distance lands inside a dash
(`dist_at(y) % DASH_PERIOD < DASH_LENGTH`) — nothing on screen actually
moves, we just repaint based on a growing number.

**Watch for:** the scrolling math is the classic brain-twister of this whole
curriculum. Have the `dist_at` formula up on a whiteboard or slide so
students can copy the shape of it rather than deriving it live. There's no
rival and nothing to crash into in this file — that's deliberate, so the
scrolling illusion can be understood on its own first.

## Part 2 — `02_week2_part2.py`: You meet your first rival

**Goal for students:** share the road with one other car, and avoid hitting
it.

| Concept | Where it shows up |
|---|---|
| A dictionary bundling related values | `rival = {...}` |
| Relative speed - the core trick of the whole game | `row_at()`, and the big comment above it |
| A window size calculated from the game's settings, not hard-coded | `WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN` |
| A simple state machine (2 states) | `game_state` = `"racing"` / `"crashed"` |

**The idea to put on the board:** `row_at()` is `dist_at()` solved
backwards — given a distance, which screen row is it drawn at *right now*?
That single function is why a rival with its own independent `distance` can
be placed on screen correctly every frame: drive faster than the rival's
`base_speed` and the gap between your distances shrinks, so `row_at()`
returns a bigger row number and the rival appears to drift toward you and
past you. Drive slower and it pulls away up the screen.

**Watch for:** `WIDTH` is no longer a plain number — it's a formula. This
matters starting next week, when `NUM_RIVALS` grows past 1: changing that
one number automatically resizes the window to fit, instead of hand-tuning
`WIDTH` per file the way earlier prototypes of this project did.

## Pacing

Part 1 (~25-30 min, mostly because of the scrolling-math brain-twister) then
Part 2 (~20 min) should fit one hour. If a class is running behind, Part 2
survives being pushed to the start of Week 3 without breaking anything.
