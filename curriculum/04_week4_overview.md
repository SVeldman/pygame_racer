# Week 4 Overview: Bending the Track

Welcome to Week 4! This week features a massive mechanical payoff: we are finally introducing curves to our road. 

The key concept for this week is a MASSIVE payoff that we set up in week 1. We are going to completely redefine how the entire game landscape behaves by changing exactly *one* function. Every single non-player object on screen (the tarmac, the shoulders, the dashed center line, and all AI rivals) will automatically conform to the new bending geometry without us touching their underlying code.

This illustrates a valuable lesson to developing coders - the concept of *extensibility*. When we say that "good code is extensible" we mean that it can be built upon and expanded as the project grows, without massive rewrites or *refactors*. It is worth taking the time this week to emphasize this concept, as the students will get to see for themselves just how powerful it is.

---

## Part 1: The Road Curves (`04_week4_part1.py`)

**The Student Goal:** Make the straight vertical road bend dynamically to the left and right, and watch every rival car follow the curve automatically.

This session introduces linear interpolation (Lerp), which is conceptually the hardest single idea in the entire curriculum. We shift from a static highway center to reading a list of sequential segments, calculating exactly where the player is on the track, and smoothly transitioning the road's X-coordinate between a start point and an endpoint. The walkthrough gives you some pointers on breaking down the math, but don't dwell on it. As in previous weeks, getting the students to wrap their heads around the high-level idea is what really matters, as it will help them appreciate just how much goes into building even a relatively simple game.

### Key Themes to Track:
* **The Week 1 Payoff:** Have the students look back at the `road_center_x()` function we insisted on writing all the way back in Week 1. Show them that `road_left`, `road_right`, `on_road()`, and the rival placement math *all* rely on this function—and none of those components are changing this week. We are simply updating the inside of `road_center_x()` from returning a static `WIDTH // 2` to reading a track data layout. Hopefully this is a massive "aha!" moment when they see it come together.
* **The Track Array:** We introduce a `TRACK` list that holds track segments, where each segment has its own length and target curvature. The engine walks this list to figure out which segment the player is currently driving through and blends the coordinates smoothly.
* **Classroom Delivery:** The interpolation math (`start + (end - start) * fraction`) can look intimidating on a screen. Don't let the raw math stall your pacing. Keep the focus on the high-level concept: we are telling the computer to look at how far along a segment a car is (e.g., *"80% of the way through this turn"*), and shift the pixels accordingly. 

---

## Part 2: A Real Lap (`04_week4_part2.py`)

**The Student Goal:** Build out a complete, multi-turn racetrack layout and customize the course design to make it their own.

From a programming standpoint, there are zero new mechanics introduced in this session. The `TRACK` data structure simply grows from a basic 3-segment test pattern into a robust, 13-segment racing circuit with sweeping turns and long straightaways. It is ok to move through this quickly - ideally students have ample time at the end of class to experiment building their own custom tracks.

### Key Themes to Track:
* **Data-Driven Design:** Because the entire racetrack is generated cleanly out of data rather than hardcoded logic, changing the track layout requires absolutely no new code. Lengthening a straightaway, sharpening a curve, or inventing an entirely new path is done purely by updating the numbers inside the `TRACK` list.
* **The Automatic Finish Line:** `FINISH_DISTANCE = sum(length for length, _ in TRACK)` automatically totals up the length of their custom track segments. This means the finish line will always dynamically place itself at the exact end of the course, no matter how much they modify the map.
* **Sandbox Time:** Try to leave at least the last 15 minutes of class for a design exercise. Challenge the students to architect their own custom raceway. Some might build a punishing, curvey nightmare-track; others might build a high-speed drag strip with one massive sweep. This should be a rewarding creative outlet where they get to test-drive their own game design.

---

## Pacing & Classroom Flow

Because of the conceptual weight of the interpolation math in Part 1, the time split leans heavily toward the front half of the session:
* **Part 1 (Curve Math & Segments):** ~25 to 30 minutes (give this room to breathe, do not rush it).
* **Part 2 (Track Customization Sandbox):** ~10 to 15 minutes of light adjustments and playtesting.
* **Open Buffer:** ~15 minutes.

**Note on Timing:** Week 4 is intentionally designed with significant slack. If your class spent extra time wrapping their heads around the lists of dictionaries or state machines from Week 3, there is ample time to catch up. Also, the core curriculum ends here. Week 5 is an ambitious "bonus week" with challenges for the advanced students. Even if you take all 5 weeks to get to the end of Week 4, the class will have accomplished *a lot*. You can always print out the walkthroughs for Week 5 and send them home for students to work through on their own time.
