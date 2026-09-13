# Week 3 — Instructor Overview

## Run it

```bash
cd project
pgzrun 05_week3_part1.py       # or 06_week3_part2.py
```

## Part 1 — `05_week3_part1.py`: A pack of rivals, a grid, a finish line

**Goal for students:** race several cars at once, from a shared starting
line, to an actual finish line, and find out what place they came in.

| Concept | Where it shows up |
|---|---|
| A LIST of dictionaries (scaling up from one rival to many) | `rivals = [...]` |
| A list comprehension | the `rivals = [...for lane_i in grid[1:]]` block |
| `random.shuffle` for a fair, varied starting order | `new_race()` |
| `LANE_COUNT` / `WIDTH` computed from `NUM_RIVALS`, not hand-tuned | the "Tuning knobs" block |
| Looping over a list in both `update()` and `draw()` | rival movement, rival drawing |
| Deriving a rank from a list built up over time | `race_results`, `player_place` |
| String formatting a number into "1ST"/"2ND"/"3RD" | `_ordinal()` |

**The idea to put on the board:** every car - rivals and player - starts at
`distance = 0`. `LANE_COUNT = NUM_RIVALS + 1` guarantees there's exactly
enough room for everyone to get their own lane with no overlap.
`random.shuffle` on the list of lane numbers is what makes the grid order
different every race.

**Watch for:** this is the heaviest single file in the whole curriculum -
more new vocabulary lands here than in any other lesson (dicts, lists of
dicts, list comprehensions, `random`, relative speed, an inverse function,
finish-line rendering, string formatting). Consider splitting your own
delivery: spawn + movement first, then finish line + placement, using
`05_week3_part1.py` itself as the "answer key" checkpoint if the class runs
long.

## Part 2 — `06_week3_part2.py`: A proper start, and recovering from a crash

**Goal for students:** a "READY TO RACE?" screen, a 3-2-1-GO countdown, and a
crash that costs you time instead of ending your run.

| Concept | Where it shows up |
|---|---|
| Growing a state machine from 3 states to 5 | `game_state` comment at the top of the file |
| Frame-based timers (pgzero runs at 60 fps by default) | `COUNTDOWN_FRAMES`, `FREEZE_FRAMES` |
| Early `return` to keep each state's logic separate | the top of `update()` |
| A blink effect from a modulo on a timer | `(freeze_timer // 6) % 2 == 0` |

**The idea to put on the board:** for every state, ask two questions - "what
can happen from here?" and "what causes leaving this state?" `"waiting"`
leaves on SPACE. `"countdown"` and `"frozen"` leave when their timer hits
zero - no key needed. `"racing"` leaves on a crash (to `"frozen"`) or
reaching the finish (to `"won"`). Walking through that table on the board
before touching code helps a lot here.

**Watch for:** the biggest behavior change from Part 1 is that rivals now
keep moving while YOU are frozen - make sure students see that a crash still
costs real ground, it just isn't fatal anymore.

## Pacing

Part 1 (~25-30 min) then Part 2 (~20-25 min). If Part 1 overruns, Part 2's
state-machine work can spill into the start of Week 4 without breaking
anything - Week 4 builds on Part 2's finished file either way.
