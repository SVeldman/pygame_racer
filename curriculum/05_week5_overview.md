# Week 5 — Instructor Overview

Week 5 is a linear progression, same as Weeks 1-4: each part builds
directly on the one before it. By the end of Week 4, every student has a
complete, playable game - Week 5 takes it from there in three steps: a real
menu, then a second human player, then AI rivals that change lanes (and
occasionally crash into each other).

The big difference is that this is a "stretch" week. Students who need the
time to catch up to where week 4 ended can do so, and have a great, playable
game by the end. Advanced students who are chomping at the bit for more have
PLENTY of advanced features they can add.

## Run it

```bash
cd project
pgzrun 05_week5_part1_menu.py               # Part 1
pgzrun 05_week5_part2_multiplayer.py        # Part 2
pgzrun 05_week5_part3_advanced_rivals.py    # Part 3
```

## Part 1 — `05_week5_part1_menu.py`: An advanced start menu

Turns the "READY TO RACE?" screen into a real menu: choose your car, how
many racers total, how long the race is, and how hard the AI is, before
every race.

| Concept | Where it shows up |
|---|---|
| `on_key_down(key)` - fires once per press, not every held frame | new hook, used only during the menu |
| Settings that reshape the game between races | `_apply_menu_choices()` |
| A fixed window sized for the "biggest" case | `WIDTH` computed from `MAX_RACERS`, not the current `NUM_RACERS` |
| One long track, sliced to different lengths | `TRACK` + `LENGTH_OPTIONS` |
| Reassigning an `Actor`'s image at runtime | `player.image = CAR_CHOICES[car_index]` |

**The idea to put on the board:** `keyboard.left` (used everywhere else in
this project) is `True` for every frame a key is held - perfect for
continuous movement, terrible for a menu (it would fly through options 60
times a second). `on_key_down` is a different tool for a different job: it
fires exactly once per press. Point out the moment `game_state != "waiting": return`
appears at the top of `on_key_down` - the menu should only ever respond to
input on the menu screen.

**Watch for:** "Racers" means the TOTAL number of cars, including the
player - "Racers: 4" is you plus 3 AI opponents, not 4 AI opponents. Also,
the window's actual size never changes once pgzero creates it - picking
fewer racers just leaves more grass showing on the sides of a fixed-size
window, it doesn't shrink the window. This is a real engineering constraint
worth explaining, not a workaround to gloss over.

## Part 2 — `05_week5_part2_multiplayer.py`: A second human player

Builds directly on Part 1: adds Player 2 (W/A/S/D) alongside Player 1
(arrow keys), each seeing their own stacked half of the window. The menu
gains a car-choice field for each player, and "Racers" now counts both of
them - "Racers: 4" is 2 players plus 2 AI opponents. Both players race the
exact same set of AI racers, at the exact same positions - not two
similar-looking but independent races. Each player still gets their own
crash-freeze state, but a racer that's frozen by one player's crash is
frozen (and blinking) in the other player's band too, since it's one shared
car, not two copies. The two human players can also see and crash into each
other, using the same track-space comparison Part 3 later reuses for
rival-vs-rival crashes.

| Concept | Where it shows up |
|---|---|
| Moving global variables into a dict, per player | `make_player()` |
| The same function running for two different players | `update_player(player)`, `draw_player_band(player)` |
| `getattr(keyboard, name)` instead of hard-coding `keyboard.left` | inside `update_player()` |
| `screen.surface.set_clip(rect)` restricting where drawing can land | `draw_player_band()` |
| One shared object, projected onto two different screens | `racers` list, read by both bands via `row_at`/`lane_to_x` |
| Projecting one player into the other's band without corrupting their real position | `_player_lane()`, the save/restore ghost-draw in `draw_player_band()` |
| Comparing two entities in track-space instead of `colliderect()` | `_check_player_collision()` |

**The idea to put on the board:** every formula from Part 1 (`dist_at`,
`row_at`, `road_center_x`, ...) now takes a `player` argument instead of
reading a single global `distance_traveled`. Same formulas, just
parameterized - this is a good moment to discuss *why* we bundled the
player's state into a dict as early as Week 2/3 for rivals: the exact same
pattern scales to a second human player with barely any new ideas.

**Watch for:** most of this file is "give the player dict a sibling, and run
everything twice" - good design (a dict per racer, a dict per player,
settings as data) is what makes extending a feature cheap instead of a
rewrite. The one genuinely new idea is the last step: a *player's*
`actor.pos` is not disposable the way a racer's is (it's the real value
`update_player()` steers from next frame), so making players visible to
each other needs a save/restore around the ghost-draw, and the collision
check compares lane/distance directly instead of using `colliderect()`.

## Part 3 — `05_week5_part3_advanced_rivals.py`: Lane changes and rival crashes

Builds directly on Part 2: AI racers no longer sit in one lane for the
whole race. Each one holds a lane for a random few seconds, then eases
smoothly over to a new one, and repeats. And now that racers can share a
lane (even briefly), two of them can actually meet - `check_racer_collisions()`
rolls a die on every overlap: 25% of the time it's a real crash (both
freeze and blink, exactly like a player hitting a racer already works),
75% of the time they swerve to avoid it by picking a fresh lane instead.

| Concept | Where it shows up |
|---|---|
| A value that eases toward a changing target instead of jumping | `r["lane"]` easing toward `r["target_lane"]` in `update_racers()` |
| Comparing objects in "the real world" instead of on screen | `check_racer_collisions()` compares `lane`/`distance` directly - not projected pixels, since a racer's true position doesn't belong to either band |
| Reusing an existing mechanic for a new kind of event | rival-vs-rival crashes freeze exactly like player-vs-rival crashes already did - same `state`/`freeze_timer` fields, no new ones needed |

**The idea to put on the board:** nothing about drawing or player-vs-racer
collision had to change to support lane-changing - they already read
`r["lane"]` fresh every frame, so making that value drift instead of
staying constant just flows through code that already existed. The only
genuinely new mechanic is racers noticing EACH OTHER, which needed a check
that never existed before.

**Watch for:** the collision check only compares two *actively moving*
racers to each other - a racer that's mid-lane-change can still drive
straight through one that's already frozen. Rear-ending a stopped car isn't
handled; that's a good "extend this yourself" prompt for strong students.

## Optional Extra — `05_week5_split_screen.py`: Two players, no menu, no AI

Not part of the required path. This is a smaller, standalone stepping stone
to Part 2: it adds the second human player exactly the way Part 2 does
(same `make_player()`/`update_player()`/`draw_player_band()` pattern), but
skips the menu and has no AI rivals at all. Good for a student who wants an
even gentler first step into split-screen before tackling Part 2, or as a
quick aside for a fast finisher - "no AI rivals and no collisions between
the two players in this file" is an intentional gap, and a natural "extend
this yourself" prompt.

## Pacing

Treat this like Weeks 1-4: work through Part 1, then Part 2, then Part 3,
in order. A student who is behind on Weeks 1-4 should spend this hour
catching up instead - none of Week 5 is required for a finished, playable
game. The Optional Extra is exactly that: optional, for students with time
to spare.
