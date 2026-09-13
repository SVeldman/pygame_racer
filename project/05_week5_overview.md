# Week 5 — Instructor Overview (Bonus)

Week 5 is pick-your-own-adventure. By the end of Week 4, every student has a
complete, playable game. This week offers two independent extensions - pick
one, do both back to back, or use the time to catch up if a student is
behind. There's no "right" choice; steer students toward whichever extension
sounds more fun to them.

## Run it

```bash
cd project
pgzrun 09_week5_start_menu.py      # Option 1
pgzrun 10_week5_split_screen.py    # Option 2
pgzrun 11_week5_combined.py        # Both together
```

## Option 1 — `09_week5_start_menu.py`: An advanced start menu

Turns the "READY TO RACE?" screen into a real menu: choose your car, how
many rivals, how long the race is, and how hard the rivals are, before every
race.

| Concept | Where it shows up |
|---|---|
| `on_key_down(key)` - fires once per press, not every held frame | new hook, used only during the menu |
| Settings that reshape the game between races | `_apply_menu_choices()` |
| A fixed window sized for the "biggest" case | `WIDTH` computed from `MAX_RIVALS`, not the current `NUM_RIVALS` |
| One long track, sliced to different lengths | `TRACK` + `LENGTH_OPTIONS` |
| Reassigning an `Actor`'s image at runtime | `player.image = CAR_CHOICES[car_index]` |

**The idea to put on the board:** `keyboard.left` (used everywhere else in
this project) is `True` for every frame a key is held - perfect for
continuous movement, terrible for a menu (it would fly through options 60
times a second). `on_key_down` is a different tool for a different job: it
fires exactly once per press. Point out the moment `game_state != "waiting": return`
appears at the top of `on_key_down` - the menu should only ever respond to
input on the menu screen.

**Watch for:** the window's actual size never changes once pgzero creates it
- picking fewer rivals just leaves more grass showing on the sides of a
fixed-size window, it doesn't shrink the window. This is a real engineering
constraint worth explaining, not a workaround to gloss over.

## Option 2 — `10_week5_split_screen.py`: Two human players, stacked

Two people can race each other on the same keyboard - Player 1 on the arrow
keys, Player 2 on W/A/S/D - each seeing their own half of the window.

| Concept | Where it shows up |
|---|---|
| Moving global variables into a dict, per player | `make_player()` |
| The same function running for two different players | `update_player(player)`, `draw_player_band(player)` |
| `getattr(keyboard, name)` instead of hard-coding `keyboard.left` | inside `update_player()` |
| `screen.surface.set_clip(rect)` restricting where drawing can land | `draw_player_band()` |

**The idea to put on the board:** every formula from earlier weeks
(`dist_at`, `row_at`, `road_center_x`, ...) now takes a `player` argument
instead of reading a single global `distance_traveled`. Same formulas, just
parameterized - this is a good moment to discuss *why* we bundled the
player's state into a dict as early as Week 2/3 for rivals: the exact same
pattern scales to human players with barely any new ideas.

**Watch for:** there are no AI rivals and no collisions between the two
players in this file - both are natural "extend this yourself" prompts for
strong students who finish early.

## Option 3 — `11_week5_combined.py`: Both together

Combines Options 1 and 2: the menu now has fields for both players' cars
plus shared rival count/length/difficulty, and each player's band gets its
own independent set of AI rivals and its own crash-freeze state.

This file has very little that's mechanically new - it's mostly "connect the
two things we already built." That's worth saying explicitly: good design
(a dict per rival, a dict per player, settings as data) is what makes
combining two features cheap instead of a rewrite. If a student has built
both Option 1 and Option 2 and wants to combine them on their own before
looking at this file, encourage it - this file is meant as an answer key,
not necessarily a third from-scratch build.

## Pacing

There's no fixed pacing this week - let students choose their own path. A
student who spends the whole hour on Option 1 (or Option 2) alone has done
the assignment. A student who is behind on Weeks 1-4 should spend this hour
catching up instead; none of Week 5 is required for a finished, playable
game.
