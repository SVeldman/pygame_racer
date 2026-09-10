# pygame_racer

Curriculum planning and code for a **vertical scrolling racer** built in [Pygame Zero](https://pygame-zero.readthedocs.io/), taught to students over a series of hour-long sessions.

## Project concept

The player's car stays locked forward-facing near the bottom of the screen. Forward motion is simulated by scrolling the road downward. AI opponents are positioned using relative speed:

```python
enemy.y += (player_speed - enemy.base_speed)
```

Drive faster than an opponent and they drift down past you; drive slower and they pull away off the top.

## Current status

- [brainstorm.txt](brainstorm.txt) — design notes and curriculum planning (session breakdowns for both 6-session and condensed 4-session formats, plus a split-screen multiplayer extension for advanced students).
- No code written yet.

## Teaching notes

Pygame Zero gotchas worth enforcing up front with students:

- Images **must** be `.png` and live in a folder named exactly `images`.
- Asset filenames are case-sensitive — enforce lowercase-only names (`mycar.png`, not `MyCar.PNG`).
- Provide a ready-made asset pack on day one so class time goes to coding, not hunting for sprites.

## Working on this project elsewhere

```bash
git clone https://github.com/SVeldman/pygame_racer.git
cd pygame_racer
pip install pgzero
pgzrun main.py   # once there's a main.py
```
