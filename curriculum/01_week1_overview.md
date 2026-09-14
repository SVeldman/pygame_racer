# Week 1 — Instructor Overview

## Start of Class: Setup

Students need Pygame Zero installed. In a terminal:

```bash
pip install pgzero
```

**Pygame Zero is a runner, not a normal library.** Game files never contain
`import pgzero`. Instead, you run a game file with the `pgzrun` command, and
pgzero makes a handful of special names (`screen`, `Rect`, `WIDTH`, `HEIGHT`,
`Actor`, `keyboard`, ...) available inside it automatically. This is worth
saying out loud in class the first time a student asks "wait, where does
`screen` come from?" It isn't magic, pgzero just runs your file with those
names already defined.

To run a file, `cd` into the `project` folder and run `pgzrun <filename>`:

```bash
cd project
pgzrun 01_week1_part1.py
```

**All of your image assets are provided** `images/` already has a
set of car sprites. Students should never need to
go hunting for art during a lesson.

This will only come up if students try to add their own images, but there are
two gotchas worth mentioning up front: images must be `.png`, and filenames are 
case-sensitive (`car_red.png`, not `Car_Red.PNG`).

## Part 1 — `01_week1_part1.py`: The map and the car

**Goal for students:** by the end of this section their game will have a road, and 
a car they can move laterally left and right on it.

Two ideas land together in this first file, because a road with nothing on
it isn't very exciting to look at for long: the road itself (`draw()`,
`screen.fill()`, `screen.draw.filled_rect()`, constants as tuning knobs), and
a car that responds to the arrow keys (`Actor`, `update()`, `keyboard.left`/
`keyboard.right`, clamping).

| Concept | Where it shows up |
|---|---|
| `draw()`, pgzero's per-frame repaint hook | top-level structure |
| `screen.fill()` / `screen.draw.filled_rect()` | the road-drawing loop |
| A function as "the answer to a question," not a stored value | `road_center_x(row)` |
| Constants as tuning knobs | `ROAD_WIDTH`, `SHOULDER_WIDTH`, the colour tuples |
| `Actor` — an image + a position + `.draw()` | `player = Actor("car_red", ...)` |
| `update()`, pgzero's per-frame "move things" hook | new this file |
| `keyboard.left` / `keyboard.right` — true every frame a key is held | `update()` |
| Clamping a value into a range | `max(20, min(WIDTH - 20, player.x))` |

**Instructor note:** `road_center_x()` always returning the same number
looks pointless right now. That's fine, don't over-explain it. Just plant
the seed: "everything asks this function where the road is, instead of
assuming it knows." Weeks 3–4 pay this off.


## Part 2 — `01_week1_part2.py`: Speed, and three "terrain" zones

**Goal for students:** watch a speed number climb on the tarmac and fall on
the shoulder/rough.

| Concept | Where it shows up |
|---|---|
| A persistent variable that changes every frame | `player_speed` |
| A function returning `True`/`False` to drive behaviour | `on_road()`, `on_shoulder()` |
| A 3-way `if`/`elif`/`else` mapped onto three zones | `update()` |
| Clamping again, now on a float | `player_speed = max(0.0, min(MAX_SPEED, player_speed))` |

**The main idea we are implementing:** the car doesn't have one "off-road" rule,
it has two — a gravel SHOULDER right next to the road that costs a little
speed, and the ROUGH (grass) beyond that, which costs more.
`SHOULDER_MAX_SPEED` and `ROUGH_MAX_SPEED` are written as fractions of
`MAX_SPEED` on purpose. Turning that dial (say, `MAX_SPEED * 0.9`) is a good
"try it yourself" moment.

**Note:** the car still doesn't move up the screen. Some students
expect "speed" to mean forward motion already — worth clarifying that this
speed number doesn't drive anything *yet*. That's Week 2.

## Pacing

Both parts together should comfortably fit in a one-hour session (~15
minutes for Part 1, ~25-30 for Part 2), leaving room for questions and 
letting students experiment with constants (car start position, road width,
speed caps, colours) at the end.
