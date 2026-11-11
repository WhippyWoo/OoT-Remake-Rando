# OoT Remake Randomizer — tester guide

A work-in-progress randomizer for *The Legend of Zelda: Ocarina of Time* on Nintendo Switch 2.
It shuffles chest contents with logic, so every seed can be finished. Thank you for testing!

## What you need
- Your **own** dump of the game (title ID `0400486024DEC000`) **with update 1.1.1**, extracted to RomFS folders.
  The randomizer reads it; it never copies, uploads or shares game files.
- An emulator or setup that loads RomFS mods (LayeredFS).
- Windows 10 or 11 for the program. (On macOS/Linux, use the source version with Python 3.8+: run `./run.sh`.)

## Making a seed
1. Put `OoT-Remake-Rando.exe` in its own folder: it saves your settings and seeds next to itself.
2. Double-click it. Windows may warn that it's from an unknown publisher (it isn't signed):
   choose *More info* → *Run anyway*.
3. **Game files:** choose your dump folder (the one containing `base/romfs` and `updates/…/romfs`), or the base
   and update RomFS folders separately, then press *Check game files*.
4. **Seed:** pick how much of the game to randomize, a seed number (or leave it random) and the options.
5. Press **Generate seed**. After a minute you get a folder named like `RandoForestTemple_123456_SkipOpening`.

## Playing it
1. Copy that folder into your emulator's mod folder for the game (usually right-click the game →
   *Open Mod Data Location*). Only enable **one** seed at a time.
2. Start a **new save file**.
3. Play to the goal shown for the world you picked (the no-logic world has no goal and can be unbeatable). `spoiler.txt` in the seed folder lists every item, if you get stuck.

## What's randomized (so far)
- Chest contents in the areas of the world you picked. Song and NPC gifts, Skulltulas, scrubs and shops are not randomized yet.
- Dungeon Maps and Compasses stay in their own dungeon. Small keys and Boss Keys stay where they normally are.
- Chests marked `[junk only]` in the spoiler are ones whose requirements aren't confirmed yet: they only hold rupees and
  similar items. Telling us where they are and what you needed to reach them helps a lot.

## Reporting a problem
After generating, the page shows a **bug report** template with your seed and options filled in. Copy it, describe what
happened and where, and send it back. Especially useful:
- a chest or area you could not reach although the spoiler says you should be able to (a logic mistake)
- a crash, freeze, softlock, missing NPC or invisible wall
- a chest that gave a different item than the spoiler says

## Known issues
- *Skip child Zelda* is disabled: it breaks story progress.
- In the remake, bombs need the Goron Bracelet. Tick *Bombs without Goron Bracelet* if you want them earlier.
