# Week 1 Overview: Building the Foundation

Welcome to Week 1! This week, we lay the bedrock for our vertical racing game. For your instructors reading ahead, the core philosophy of this week is **immediate feedback.** 

We deliberately build the car first and the road second. Getting a sprite moving on a plain green field within the first ten minutes is a massive psychological win for middle and high school students. The visual polish—the asphalt, shoulders, and dashed lines—comes after they already feel the satisfaction of interactive controls.

Here is your high-level roadmap for the week.

---

## Part 0: Housekeeping & Environment Check

Before diving into game loops, there are a few quick items to cover regarding PyGame Zero.

### Core Prereqs:
* **Installation:** Ensure every student machine has Pygame Zero on their machine. Have them run `pip install pgzero` in the terminal. To spin up the starter template, `cd` into the project directory and execute `pgzrun racer.py`.
* **Starter Code:** The `racer.py` and `images/` directory contain everything the students need to get started. Have them make sure they are available on their machine, and that they are both located in the same root project directory.
* **The "Runner" Framework:** Explain to instructors that Pygame Zero is a "runner," not a traditional imported library. You will notice there is no `import pgzero` at the top of the files. Instead, the `pgzrun` terminal engine boots the script and automatically injects global objects like `screen`, `Actor`, and `keyboard` into memory.

**Instructor Tip:** Anticipate the question, *"Wait, where does `screen` come from if we didn't import it?"* Use this moment to demystify the magic—explain that the engine handles the boilerplate setup so they can focus strictly on building game logic.

**Quick Note on Images:** All image assets are pre-packaged inside the `images/` directory, so that students will not need to hunt for art during the lesson. But if they *do* choose to integrate some of their own files later on, note that Pygame Zero assets are case-sensitive and must be lowercase `.png` files (e.g., `car_red.png`, not `Car_Red.PNG`).

---

## Part 1: The Map and the Car (`racer.py` to Checkpoint 1)

**The Student Goal:** Build a plain field, render a controllable car, and lay down a straight highway.

Students will tackle the core engine design of the game loop here, balancing structural loops with real-time player input.

### Key Themes to Track:
* **The Twin Hooks:** Students will learn that `draw()` loops continuously to repaint the window (~60 times a second), while `update()` runs right before it to handle inputs and positions. Keeping "what changes" separate from "what is rendered" is the core architecture of the entire course.
* **The Boundary Trap:** Once controls are added, the car will drive completely off the screen. We solve this using a math pattern called **clamping** (`max(low, min(high, value))`). Think of it like physical guardrails on a bowling lane.
* **Planting the Seed:** We introduce a function called `road_center_x()`. Right now, it feels completely pointless because it just returns a static number down the middle of the screen. **Instructor Tip:** Tell students, *"Trust the process here. Everything in our game asks this function where the road is, rather than assuming it knows. In a few weeks, this function is how we make the road curve without rewriting any other code."*

---

## Part 2: Speed and the Three Terrain Zones (Checkpoint 2)

**The Student Goal:** Make a dynamic "speedometer" number climb on the pavement and drop when off-road.

This session shifts from pure geometry to simple in-game physics and state logic. The car doesn't just have an "on/off" road rule, it now has three distinct terrain zones (the tarmac, a gravel shoulder, and the rough grass).

### Key Themes to Track:
* **Terrain Penalties:** We implement a three-way `if / elif / else` block to check the car's coordinates. Driving on the gravel shoulder caps their maximum speed slightly; driving into the deep grass cuts it even more. 
* **The "Tuning Knob" Moment:** Speed caps are written as mathematical fractions of their absolute maximum speed (e.g., `MAX_SPEED * 0.9`). This is the first of many "try it yourself" moments for students to dial in the difficulty and feel of their own game.
* **Managing Expectations:** The car still does *not* move up the screen. The background is completely static. Students frequently hear the word "speed" and expect forward momentum immediately. Clarify upfront that this number is just a data value sitting in memory for now—we will use it to drive the scrolling background in Week 2.

---

## Pacing & Classroom Flow

This entire sequence fits comfortably into a standard one-hour block:
* **Part 0 (Housekeeping):** ~5 to 10 minutes of environment check.
* **Part 1 (The Car & Road):** ~15 minutes of core assembly.
* **Part 2 (Terrain & Speed Physics):** ~25 to 30 minutes of logic building.
* **Open Buffer:** ~10 minutes at the end of class. 

Protect that final buffer time. It allows students to experiment safely with their constants—changing starting positions, widening the roads, adjusting maximum speeds, or changing car colors. Letting them break and tune the game safely is a great learning moment, and also gives you time to help any stragglers catch up.

