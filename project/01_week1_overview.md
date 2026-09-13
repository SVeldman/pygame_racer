# Week 1 — Instructor Overview

## Before class: setup

Students need Pygame Zero installed. In a terminal:

```bash
pip install pgzero
```

**Pygame Zero is a runner, not a normal library.** Game files never contain
`import pgzero`. Instead, you run a game file with the `pgzrun` command, and
pgzero makes a handful of special names (`screen`, `Rect`, `WIDTH`, `HEIGHT`,
`Actor`, `keyboard`, ...) available inside it automatically. This is worth
saying out loud in class the first time a student asks "wait, where does
`screen` come from?" — it isn't magic, pgzero just runs your file with those
names already defined.

To run a file, `cd` into the `project` folder and run `pgzrun <filename>`:

```bash
cd project
pgzrun 01_week1_part1.py
```

**Have the asset pack ready before class starts.** `images/` already has a
set of placeholder car sprites and textures — students should never need to
go hunting for art during a lesson. Two gotchas worth mentioning up front:
images must be `.png`, and filenames are case-sensitive (`car_red.png`, not
`Car_Red.PNG`).

## Part 1 — `01_week1_part1.py`: Draw the map

**Goal for students:** run the file and see a road.

There is no `Actor`, no `update()`, and nothing moves — this is intentionally
the smallest possible first step. The point is just getting comfortable with
`draw()`, `screen.fill()`, `screen.draw.filled_rect()`, and the idea of
constants (`ROAD_WIDTH`, colours) as adjustable "knobs."

| Concept | Where it shows up |
|---|---|
| `draw()`, pgzero's per-frame repaint hook | top-level structure |
| `screen.fill()` / `screen.draw.filled_rect()` | the whole `draw()` body |
| A function as "the answer to a question," not a stored value | `road_center_x(row)` |
| Constants as tuning knobs | `ROAD_WIDTH`, `SHOULDER_WIDTH`, the colour tuples |

**Instructor note:** `road_center_x()` always returning the same number
looks pointless right now — that's fine, don't over-explain it. Just plant
the seed: "everything asks this function where the road is, instead of
assuming it knows." Weeks 3–4 pay this off.

## Part 2 — `02_week1_part2.py`: The car appears

**Goal for students:** drive left and right.

| Concept | Where it shows up |
|---|---|
| `Actor` — an image + a position + `.draw()` | `player = Actor("car_red", ...)` |
| `update()`, pgzero's per-frame "move things" hook | new this file |
| `keyboard.left` / `keyboard.right` — true every frame a key is held | `update()` |
| Clamping a value into a range | `max(20, min(WIDTH - 20, player.x))` |

**Watch for:** students expecting the car to accelerate or feel "weighted."
It doesn't yet — every keypress moves it by a fixed amount, no speed variable
exists at all. If a student asks "why doesn't it go off-road slower," that's
a perfect segue into next week.

## Pacing

Both parts together should comfortably fit in a one-hour session (~10 minutes
for Part 1, ~15 for Part 2), leaving room for setup, questions, and letting
students tweak constants (car start position, road width, colours) at the
end.
