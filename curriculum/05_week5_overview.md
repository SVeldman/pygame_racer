# Week 5 Overview: Advanced Settings & Split-Screen Multiplayer

Welcome to Week 5! This is our grand finale "stretch" week. It follows a linear progression like previous weeks, but it serves a dual purpose in the classroom. 

For students who need extra time to polish their Week 4 projects, this session is a safe runway to catch up and cross the finish line with a complete, playable game. For advanced students who are chomping at the bit for more, Week 5 serves up a spectacular architectural challenge: transforming the prototype into a fully functional arcade game with an advanced settings menu and a true, split-screen two-player multiplayer mode.

Depending on class size and where everyone is at, you might consider printing coppies of this week's walkthroughs for the advanced students to attempt on their own. This could free you up to run the class like an "office hours" session for students still working through issues from previous weeks.

---

## Part 1: An Advanced Start Menu (`05_week5_part1_menu.py`)

**The Student Goal:** Evolve the basic "READY TO RACE?" title screen into a real interactive menu where players can select their car sprite, the total number of racers, the track length, and the AI difficulty before booting up the engine.

This session introduces a valuable user-interface programming concept: input polling versus discrete event hooks.

### Key Themes to Track:
* **The Menu Event Hook:** Up until now, we have used continuous input checking (`keyboard.left`) for steering. Using that method on a menu would cause the selection selector to fly through the options 60 times a second. We introduce `on_key_down(key)`, a brand-new tool that fires exactly *once* per physical button press.
* **Fixed Window Constraints:** Notice that `WIDTH` is calculated from a `MAX_RACERS` constant rather than the player's active menu selection. If a student chooses fewer rivals, the window size doesn't dynamically shrink—it just leaves more grass rendering on the sides. This is a brilliant real-world software engineering constraint to point out to the class.
* **Classroom Delivery:** Make sure instructors clarify that "Racers" represents the *total* number of vehicles on the track, including the player. Setting "Racers: 4" means the player plus 3 AI cars, not 4 opponents. 

---

## Part 2: A Second Human Player (`05_week5_part2_multiplayer.py`)

**The Student Goal:** Add a second human player who can control a car using the W/A/S/D keys, slice the monitor into a stacked, split-screen split-surface layout, and allow both players to race on the exact same track simultaneously.

This introduces fairly complex data parameterization. Instead of writing entirely new collision engines or tracking separate game loops, we modify our existing formulas (`dist_at`, `row_at`, etc.) to accept a `player` object as an argument instead of reading a single global variable.

### Key Themes to Track:
* **One Shared World, Two Viewports:** Emphasize to the class that the players are racing in the exact same world space, not two separate copy-pasted games. If Player 1 crashes into an AI car, that AI car is frozen and blinking on Player 2's viewport as well. 
* **The Screen-Clipping Trick:** To keep Player 1's rendering from spilling over onto Player 2's half of the screen, we introduce `screen.surface.set_clip(rect)`. This functions like digital masking tape, telling Pygame Zero exactly where drawing code is allowed to land.
* **The Geometry Swap:** Because a player's real coordinate data drives their movement on the next frame, we can't just casually manipulate their sprite positions to draw them on the opposite screen. We introduce a temporary save-and-restore "ghost-draw" method to project the cars onto each other's viewports safely. We also step away from standard bounding boxes and compare their positions directly using track lane coordinates.

---

## Pacing & Classroom Flow

Approach this week with *a lot* of flexibility based on your specific classroom's progress. It is very possible even the most advanced students won't get any further than the Pre-Game Menu, and that is FINE. None of Week 5 is a mandatory requirement for a finished, successful game. If some (or all) of the students spend this entire final hour debugging and personalizing their Week 4 tracks, celebrate that as a massive win. They have still engineered a complete, vertical scrolling racing game entirely from scratch!

Consider loading the finale `05_week5_part2_multiplayer.py` script onto all of the students' computers ahead of class, and as a treat for the last 10 minutes let them partner up to race each other - just don't point the file out to them until you are ready for them to play! You could also consider this as an interractive activity they could do with their parents during week 6.
