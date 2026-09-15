# South Bend Code School Fall 2026 Python Project: "Pygame Racer"

Hello mentors! In this course we will be guiding students through building a **vertical scrolling racer**
gane in [Pygame Zero](https://pygame-zero.readthedocs.io/). This code repository contains all the resources
you will need to prep for and run your weekly classes.

## What You Are Building:

Over the first four weekly sessions, students build a vertical scrolling car racing game from scratch in Pygame Zero, adding one new concept per session: drawing the track, steering a car, and giving it a feel for speed across different terrain (Week 1), turning that speed into the illusion of forward motion and racing their first opponent (Week 2), racing a full grid of rivals to a finish line with a proper starting countdown and crash recovery (Week 3), and making the track curve into a complete multi-turn lap (Week 4). By the end of Week 4, every student has a complete, playable racing game. Week 5 is a bonus "stretch" week that adds a settings menu and then a second human player, so more experienced students can keep building while others catch up. Depending on how things go, it might take all 5 weeks to finish the core curriculum (ending with Week 4), and that is fine. Even students who only make it to the end of Week 3 will finish the class with a great piece for their portfolio.

## What Is in This Repo:
- The `project` folder contains the starter resources each student will build off of during the first class session. Ideally we should make sure these are downloaded to each computer before the first session (and have a copy on a thumb drive handy just in case).
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
- Work through the lesson walkthrough. Use the provided code snippets to build a "clean" copy of the code live on your main/student facing screen, and keep the walkthrough open on your laptop to copy/paste from as you go (or type the additions yourself if you are a faster typist than I am).
- As you add each code snippet, explain what it does. There are LOTS of comments in the Python scripts and notes in the walkthrough files to help with this, but don't feel like you need to cover every last one of these. They are included to support you when student questions come up one the fly, not stress you out. Which points you choose to emphasize should be based on what makes you comfortable, what your students seem to engage with, and what works for your timing/pacing.
- Encourage the students to add their own comments to the code as the go. This will be help them internalize what they are doing, and it will be a useful way to jog their memory each week as the code becomes more complex.
- At regular intervals pause and have the students run their game to see the changes they just implemented. There are "Expected State" notes in the walkthroughs that describe how the game should behave after each code update that can help you pace this.
- Repeat this process for each new part/week.
- Have fun! Building a video game will literally feel like magic for these students, enjoy going on this journey with them.

---
*Curriculum designed and built by Steve Veldman, September 2026*