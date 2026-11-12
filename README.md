# OoT Remake Randomizer (Switch 2)

A work-in-progress randomizer for the Switch 2 *Ocarina of Time* remake (title ID `0400486024DEC000`, update 1.1.1).
It needs your own dump of the game; nothing from the game is included here.

**Randomized so far:** chest contents, with logic up to the Forest Temple (every seed beatable) or with no logic
across every chest in the game. The Hookshot and the strength upgrades are progressive. NPC gifts, songs, freestanding
items, scrubs, Skulltulas and shops aren't shuffled yet.

**Just want to play or test?** Use the Windows program and follow [README_TESTERS.md](README_TESTERS.md).

## Running from source
Needs Python 3.8+ and zstd support: Python 3.14+ has it built in, otherwise `pip install zstandard`.

1. Copy `config.example.json` to `config.json` and set `dump` to your dump folder (the one with `base/` and
   `updates/<version>/` inside). Or pass `--dump PATH` to the scripts.
2. Make a seed, either with the program or from the command line:

| Command | What it does |
|---|---|
| `python app.py` | The randomizer in its own window (needs `pip install pywebview`). |
| `python gui.py` (or `run.bat` / `run.sh`) | The same page in your browser. |
| `python logic_seed.py --world forest_temple --seed 1234` | Builds a seed. Leave out `--seed` for a random one. |
| `python tweaks_mod.py --skip-opening` | Builds a mod with only the chosen options, no randomization. |

Worlds: `forest` (Kokiri Forest + Deku Tree), `dodongo` (to King Dodongo), `jabu` (all three child dungeons),
`forest_temple` (to Phantom Ganon), `all_chests` (no logic, every chest in the game, may be unbeatable).

Options: `--bombs-without-bracelet`, `--skip-opening`, `--skip-owls` (`--skip-child-zelda` is experimental and breaks
story progress).

Seeds go to `output/mods/0400486024DEC000/<seed name>/`, spoiler logs to `output/spoilers/`.
The first run unpacks the game's compression dictionaries into `cache/`.

## Installing a seed
Copy the seed folder into your emulator's mod folder for the game, enable only one seed at a time, and start a new save.

## Building the Windows program
Double-click `build_exe.bat` (or run `powershell -ExecutionPolicy Bypass -File build_exe.ps1`). It sets up its own
Python environment in `build/` and writes `output/release/OoT-Remake-Rando.exe` plus a zip with the tester guide.
The version number is `VERSION` in `lib/build.py`.

`python -m tools.make_release` zips the source version instead (for Python users and macOS/Linux).

## Checking a seed
`python verify.py --mod RandoForestTemple_1234 --world forest_temple` compares a built seed with the original game
files and replays the logic.

## Project layout
- `app.py`, `gui.py`, `web/` - the program
- `logic_seed.py`, `tweaks_mod.py`, `verify.py` - command-line tools
- `logic/` - the worlds: locations, rules and goals
- `lib/` - file formats, mod builder, logic core, options
- `tools/` - research scripts (location and gift lists, file round-trip tests), run with `python -m tools.<name>`
- `docs/technical-notes.md` - how it works and what was found in the game files
