# Week 2 — Instructor Overview

## Run it

```bash
cd project
pgzrun 03_week2_part1.py       # or 04_week2_part2.py
```

## Part 1 — `03_week2_part1.py`: Speed, and three zones

**Goal for students:** watch a speed number climb on the tarmac and fall on
the shoulder/rough.

| Concept | Where it shows up |
|---|---|
| A persistent variable that changes every frame | `player_speed` |
| A function returning `True`/`False` to drive behaviour | `on_road()`, `on_shoulder()` |
| A 3-way `if`/`elif`/`else` mapped onto three zones | `update()` |
| Clamping again, now on a float | `player_speed = max(0.0, min(MAX_SPEED, player_speed))` |

**The idea to put on the board:** the car doesn't have one "off-road" rule,
it has two — a gravel SHOULDER right next to the road that costs a little
speed, and the ROUGH (grass) beyond that, which costs more.
`SHOULDER_MAX_SPEED` and `ROUGH_MAX_SPEED` are written as fractions of
`MAX_SPEED` on purpose — turning that dial (say, `MAX_SPEED * 0.9`) is a good
"try it yourself" moment.

**Watch for:** the car still doesn't move up the screen. Some students
expect "speed" to mean forward motion already — worth clarifying that this
speed number doesn't drive anything *yet*.

## Part 2 — `04_week2_part2.py`: Scrolling, and your first rival

**Goal for students:** feel like you're driving forward, and share the road
with one other car.

Two ideas land together here because the second depends on the first already
existing — see the big comment above `row_at()` in the file.

| Concept | Where it shows up |
|---|---|
| An accumulator that only ever grows | `distance_traveled += player_speed` |
| The scrolling illusion (nothing moves — we just draw based on distance) | `dist_at(y)`, the dash-drawing condition |
| UP/DOWN throttle and brake replacing auto-accelerate | `update()` |
| A dictionary bundling related values | `rival = {...}` |
| Relative speed - the core trick of the whole game | `row_at()`, and the big comment above it |
| A simple state machine (2 states) | `game_state` = `"racing"` / `"crashed"` |

**The idea to put on the board:** `dist_at(y) = distance_traveled + (PLAYER_ROW - y)`.
A point drawn higher on screen (smaller `y`) is further ahead on the track.
`row_at()` is the same formula solved backwards — given a distance, which
row is it drawn at right now? That single function is *why* a rival with its
own independent `distance` can be placed on screen correctly every frame.

**Watch for:** the scrolling math is the classic brain-twister of this whole
curriculum. Have the `dist_at`/`row_at` formulas up on a whiteboard or slide
so students can copy the shape of it rather than deriving it live.

## Pacing

Part 1 (~20-25 min) then Part 2 (~25-30 min) should fit one hour. Part 2 is
the heavier of the two — if a class is running behind, it's fine to leave
`NUM_RIVALS`/throttle tuning for the start of next week rather than rushing.
