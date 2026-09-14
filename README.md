# South Bend Code School Fall 2026 Python Project: "Pygame Racer"

Hello mentors! In this course we will be guiding students through building a **vertical scrolling racer**
gane in [Pygame Zero](https://pygame-zero.readthedocs.io/). This code repository contains all the resources
you will need to prep for and run your weekly classes.

## What You Are Building:

Over five weekly one-hour sessions, students build a vertical scrolling car racing game from scratch in Pygame Zero, adding one new concept per session: drawing the track and steering a car (Week 1), giving the car real speed and the illusion of forward motion, then racing their first opponent (Week 2), racing a full grid of rivals to a finish line with a proper starting countdown and crash recovery (Week 3), and making the track curve (Week 4). By the end of Week 4, every student has a complete, playable racing game. Week 5 is a bonus week offering two optional extensions - an in-game settings menu and a two-player split-screen mode - so faster students can go further while others catch up.

## What Is in This Repo:
- The `project` folder contains the starter resources each student will build off of during the first class session.
    - `images` contains all of the racecar images they will use as sprites
    - `racer.py` is a script with starter code. It defines a bunch of the variables they will use during the first week. Rather than spending a ton of time having them copy this code from your screen, the starter code will allow you to explain what we will use each variable for, as well as some fundamental coding concepts (all included in the comments in that file).
- The `curriculum` folder has your teaching resources broken down by week, with the fist two characters representing the files for a given week (e.g. "01" for week 1, "02" for week 2, etc.)
    - Each week has 5 files - three markdown (.md) files and two Pyton (.py) scripts.
        - The Overview markdown file is an intro to the week's lesson for you, the mentor. Read it first to get a sense of what you are doing that week.
        - The Python scripts represent what the students' games should look like at major checkpoints throughout the session. Part 2 is the end-of-class target and Part 1 is checkpoint somewhere (*around-ish*) the middle of class. These scripts are heavily commented with explainations around the code is doing; the walkthroughs contain this information as well, but these are a great reference to print out and have on hand as a quick reference to help answer questions during class.
        - Each Python script has an accompanying Walkthrough Walkthrough markdown file that will guide you through building the project live with the class. Fore example, in week 1, you will start will the same `racer.py` file the students have, and progressively build it up until it matches the `01_week1_part1.py` checkpoint (and then the `01_week1_part2.py` checkpoint).

## Teaching Suggestions:
As mentioned above, each week's lesson is broken down into two major checkpoints. It will probably be helpful to treat these as two "lesson chunks", with a pause in between to get everyone caught up if necessary. For each part, try a progression like this:
- Take a moment to explain what the goal for that section is (for week 1 part 1 it is "draw the game screen + car, and implement left/right controls").
- Run the .py file for that section (e.g. 01_week1_part1.py at the beginning of the first class) so the students can see what they are building towards.
- Work through the lesson walkthrough. Try sharing a "clean" copy of the code on your main/student facing screen, and keep the walkthrough open on your laptop to copy/paste code snippets as you build (or type the additions yourself if you are a faster typist than I am).
- As you add each code snippet, explain what it does.
- Encourage the students to add their own comments to the code as the go. This will be help them internalize what they are doing, and it will be a useful way to jog their memory each week as the code becomes more complex.
- At regular intervals pause and have the students run their game to see the changes they just implemented (there are suggestions in the walkthrough, but feel free to pace as you see fit).
- Repeat this process for each new part/week.

---
*Curriculum designed and built by Steve Veldman, September 2026*