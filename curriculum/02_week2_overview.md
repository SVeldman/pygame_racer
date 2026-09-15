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


# Week 2 Overview: Creating the Illusion of Speed

Welcome to Week 2! This week, our vertical racer moves from a static sandbox to a real (though simple) game engine.

We introduce two heavy mechanics: a scrolling background and an independent rival car. The secret here, which is worth emphasizing to the students, is that **nothing is actually moving forward**. The player’s car stays glued to the bottom of the screen while we manipulate the landscape and the rival's coordinates around it to manufacture the illusion of high-speed racing.

---

## Part 1: The Road Scrolls (`02_week2_part1.py`)

**The Student Goal:** Implement throttle, brakes, and coasting physics while making the highway look like it is flying past the tires.

This session introduces a classic game development brain-twister. Instead of physically moving the player sprite up an infinite map, we accumulate a `distance_traveled` float variable based on the player’s speed and repaint the dashed center lines dynamically to match.

### Key Themes to Track:
* **The Scrolling Formula:** The basic building block for drawing the moving road is: `dist_at(y) = distance_traveled + (PLAYER_ROW - y)`. At a high level, we are drawing each frame one row at a time, and a pixel drawn higher up on the monitor (a smaller Y value) represents a point further ahead on the racetrack.
* **Dynamic Throttle Control:** We replace last week’s automatic acceleration with deliberate UP (throttle) and DOWN (brake) key maps. We also introduce a `COAST` constant so speed naturally bleeds off over time if the student lets go of the controls.
* **Classroom Delivery:** Some of the more complicated math (as well as the for loop for drawing the road) can easily stall a class. Its OK to let the students copy the code off of your projector. Do your best to help them understand the high-level concepts and how they build/fit together to accomplish something cool, but don't get too bogged down in the details.

---

## Part 2: Your First Rival (`02_week2_part2.py`)

**The Student Goal:** Share the asphalt with a computer-controlled opponent and implement a simple "crashed" state machine.

Now we'll shift from environment generation to managing multiple objects in-game. Students will spawn a rival vehicle that travels down the track at its own independent speed, requiring the program to calculate relative distance.

### Key Themes to Track:
* **Bundling Data with Dictionaries:** Instead of tracking floating variables all over the script, we introduce Python dictionaries to tie the rival's parameters together neatly: `rival = {"distance": 0, "speed": 2, ...}`.
* **Relative Motion Math:** This section features `row_at()`, which is simply `dist_at()` solved backwards. It answers the question: *Given a rival's distance relative to mine, which screen pixel row should it draw on right now?* If the student drives faster than the rival, the distance gap closes, `row_at()` returns a larger screen row, and the opponent drops toward the bottom of the window. If the two cars end up in the same place, we use PyGame Zero's built in `colliderect()` to trigger a crash (for now this ends the game, but latter we will write logic to "freeze" the crashed cars for a few seconds before allowing them to continue).
* **Flexible Windows:** Notice that `WIDTH` is no longer a hardcoded integer. It is now derived from an architectural formula: `WIDTH = ROAD_WIDTH + 2 * SHOULDER_WIDTH + 2 * GRASS_MARGIN`. This keeps the window perfectly scaled as we add more lanes and cars later.
* **The State Switch:** We introduce a 2-state variable: `game_state = "racing"` or `"crashed"`. This is a student's first exposure to a finite state machine.

---

## Pacing & Classroom Flow

The logical heavy-lifting of the scrolling math makes Part 1 the longer half of the session:
* **Part 1 (Scrolling Road Physics):** ~25 to 30 minutes (due to the coordinate math).
* **Part 2 (Rival Car Logic):** ~20 minutes of data-bundling and rendering.
* **Open Buffer:** ~10 to 15 minutes.
