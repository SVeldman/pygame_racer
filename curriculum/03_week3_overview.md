# Week 3 Overview: Scaling Up to a Real Race

Welcome to Week 3! This week, we transition our 1v1 prototype into a full, multi-rival racing grid. There are some heavy stretches of coding this week, but help your students hang in there .This is where our project starts to feel like a classic arcade game, which should be a great payoff for their hard work.

We tackle two major upgrades: expanding from one rival car to a multi-car starting grid, and evolving our basic crash rule into a dynamic, state-driven race loop featuring a pre-race countdown and a time-penalty recovery system.

**Quick Note on Pacing:** If some of the heftier code blocks bogged the class down last week, consider creating a .txt file with some of the larger/trickier chunks and load it onto the computers for students to copy/paste from. Don't lean on this too much, but it is more important that they wrap their heads around the *concepts* and keep having fun than that they write every single line by hand.

---

## Part 1: A Pack of Rivals, a Grid, and a Finish Line (`03_week3_part1.py`)

**The Student Goal:** Race against a full grid of rival cars from a randomized starting lineup, cross a literal finish line, and calculate their final placement (1st, 2nd, 3rd, etc.).

This session is the heaviest structural lift of the curriculum. We shift from managing individual floating variables to working with data collections (specifically a Python list of dictionaries).

### Key Themes to Track:
* **The Starting Grid:** Every car starts at `distance = 0`. To prevent cars from awkwardly overlapping at the starting line, we derive the track lanes dynamically: `LANE_COUNT = NUM_RIVALS + 1`. We then use `random.shuffle()` on the list of available lane indices to guarantee a fresh, randomized starting line-up every single race.
* **Looping Through the Pack:** Because all opponents are bundled into a single `rivals` list, students will write `for` loops in both `update()` and `draw()` to handle movement, positioning, and rendering for the entire pack simultaneously. 
* **Classroom Delivery:** More new vocabulary and programming structures land in this week than any other lesson (lists of dictionaries, list comprehensions, `random`, and string formatting for the final placement ranking). **Important Note:** If the class feels overwhelmed, explicitly split the delivery. Focus entirely on spawning and moving the pack first. Take a pause and let the experienced students play their game a little while you help any stragglers catch up, then tackle the finish line logic and ranking math.

---

## Part 2: Countdowns and Crash Recovery (`03_week3_part2.py`)

**The Student Goal:** Build a "Ready to Race?" title screen, a 3-2-1-GO countdown, and a crash penalty that costs the player time instead of ending the game.

Even though right now the cars are all just driving in a straight line, crashes will become more common next week when we add curves to the road. We expand our basic 2-state game into 5 states (`"waiting"`, `"countdown"`, `"racing"`, `"frozen"`, and `"won"`).

### Key Themes to Track:
* **The State Machine Logic:** If time allows, map out the states on a whiteboard. For each state, ask the class two practical questions: *"What can a player do here?"* and *"What event triggers us to leave this state?"* For example, `"waiting"` requires a keypress (SPACE) to leave, whereas `"countdown"` and `"frozen"` rely purely on frame-based timers ticking down to zero. This is a valuable programming lesson and a great concept to spend time on if students need a breather after the heavy coding in part 1.
* **Visualizing the Crash:** When the player collides with a rival, we switch the state to `"frozen"`, start a timer, and use a clever math trick—integer division mixed with a modulo on the frame timer (`(freeze_timer // 6) % 2 == 0`)—to make the player's car blink.
* **The Real Penalty:** While the player's car is locked in the `"frozen"` state, the AI rivals *keep driving forward*. A crash is no longer a frustrating "Game Over" screen, but it costs significant ground on the leaderboard, mimicking real racing games.

---

## Pacing & Classroom Flow

Because of the more complex concepts in Part 1, expect the first half of the session to take up a significant chunk of your time:
* **Part 1 (Rival Packs & Grids):** ~25 to 30 minutes (heavy data structure focus).
* **Part 2 (State Machines & Countdown Timers):** ~20 to 25 minutes of logic building.
* **Open Buffer:** ~5 to 10 minutes.

**Note on Timing:** Do not compromise on Part 1's grid architecture just to rush into timers. If your class overruns during the list of dictionaries section, Part 2's state-machine implementation can spill into the beginning of Week 4 if you need (week 4 is intentionally designed with time for experimentation and customization).
