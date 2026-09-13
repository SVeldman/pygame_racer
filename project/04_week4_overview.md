# Week 4 — Instructor Overview

## Run it

```bash
cd project
pgzrun 07_week4_part1.py       # or 08_week4_part2.py
```

## Part 1 — `07_week4_part1.py`: The road curves

**Goal for students:** see the road bend, and watch every rival follow the
bend automatically.

| Concept | Where it shows up |
|---|---|
| Replacing a constant answer with a computed one | `road_center_x()` now calls `center_x_at_distance()` |
| A list of segments, each with its own "target" | `TRACK` |
| Walking a list to find "which segment am I in?" | `_segment_at()` |
| Linear interpolation ("80% of the way from A to B") | `start + (end - start) * fraction` |
| A derived boolean from data | `is_turn_at()` |

**The idea to put on the board, and the whole point of this lesson:**
`road_left`, `road_right`, `on_road`, `on_shoulder`, and every rival's
position all go through `road_center_x()` - and NONE of them changed this
week. Only `road_center_x()`'s own implementation changed, from
`return WIDTH // 2` to reading `TRACK`. This is the payoff for insisting on
that one function all the way back in Week 1 - have students scroll through
the diff (or just count: one function body changed) to see it for
themselves.

**Watch for:** `FINISH_DISTANCE = sum(length for length, _ in TRACK)` is
worth calling out explicitly - it guarantees the described curves cover the
*entire* race. If a student's custom `TRACK` is shorter than `FINISH_DISTANCE`,
the road will hold its last curve's center steady for the remainder, which
looks like a bug but is actually `_segment_at()`'s documented "past the end"
fallback.

## Part 2 — `08_week4_part2.py`: A real lap

**Goal for students:** the finished game - a full, multi-turn course.

Nothing new mechanically. `TRACK` grows from 3 segments to 9, describing a
lap with turns spread across the whole distance instead of clustered at the
start. This is a great "make it your own" moment: `TRACK` is just data, so
lengthening a straight, sharpening a turn, or adding a whole new bend needs
no new code.

**Suggested in-class exercise:** have students design their OWN `TRACK` in
the last 10-15 minutes - a hairpin-heavy course, a mostly-straight course
with one dramatic sweep, whatever they like. Since `FINISH_DISTANCE` is
derived from `TRACK`'s own length, this is safe to hand to students without
them needing to touch any other constant.

## Pacing

Part 1 (~25-30 min) is the conceptually hardest single idea in the whole
curriculum (real interpolation math) - give it room, and don't rush into
Part 2's track design just to "finish the syllabus." Part 2 itself is light
(~10-15 min) by design, leaving slack in this week for review or a head
start on Week 5.
