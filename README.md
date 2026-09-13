# pygame_racer

Curriculum planning and code for a **vertical scrolling racer** built in [Pygame Zero](https://pygame-zero.readthedocs.io/), taught to students over a series of hour-long sessions.

## Project concept

The player's car stays locked forward-facing near the bottom of the screen. Forward motion is simulated by scrolling the road downward. AI opponents are positioned using relative speed:

```python
enemy.y += (player_speed - enemy.base_speed)
```

Drive faster than an opponent and they drift down past you; drive slower and they pull away off the top.

## Current status

- [docs/brainstorm.md](docs/brainstorm.md) — original design notes from the planning session.
- [docs/game-design.md](docs/game-design.md) — the original game-design writeup (superseded in pacing details by the overview docs below, but still a good concept overview).
- [project/](project/) — all curriculum code and instructor docs, flat in one folder, numbered `01`-`11` so they sort in teaching order:
  - **Week 1** (`01_week1_part1.py`, `02_week1_part2.py`) — draw the map, then add a car with plain left/right movement. No speed concept yet.
  - **Week 2** (`03_week2_part1.py`, `04_week2_part2.py`) — speed + shoulder/rough tiers, then the scrolling illusion, throttle/brake, and your first rival.
  - **Week 3** (`05_week3_part1.py`, `06_week3_part2.py`) — scale up to a full grid of rivals with a finish line and placement, then a proper start screen / countdown / crash-recovery state machine.
  - **Week 4** (`07_week4_part1.py`, `08_week4_part2.py`) — the road curves via a `TRACK` segment list, then a full multi-turn lap.
  - **Week 5 (bonus)** (`09_week5_start_menu.py`, `10_week5_split_screen.py`, `11_week5_combined.py`) — an advanced settings menu, a stacked split-screen 2-player mode, or both together.
  - Each week has an `0N_weekN_overview.md` instructor primer covering setup, concepts, and pacing for that week.

## Teaching notes

Pygame Zero gotchas worth enforcing up front with students:

- Images **must** be `.png` and live in a folder named exactly `images`.
- Asset filenames are case-sensitive — enforce lowercase-only names (`mycar.png`, not `MyCar.PNG`).
- Provide a ready-made asset pack on day one so class time goes to coding, not hunting for sprites.

## Working on this project elsewhere

```bash
git clone https://github.com/SVeldman/pygame_racer.git
cd pygame_racer/project
pip install pgzero
pgzrun 01_week1_part1.py   # or any other file in project/
```
