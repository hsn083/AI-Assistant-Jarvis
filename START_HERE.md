# How to install this update (the easy, foolproof way)

This package now installs itself and checks its own work, so a partial
copy can't silently leave old and new code mixed together (that's what
caused issues in the last two updates).

**This update changes Frontend, Backend, AND Main.py** (earlier updates
only touched Frontend + Main.py) — it adds Urdu language support, real
site search (e.g. Facebook), and voice file commands, all of which live
in the Backend folder.

## Steps

1. **Unzip this whole package** somewhere convenient (e.g. your Desktop).
   You should see:
   - `install.bat`
   - `verify.bat`
   - `jarvis-ai-assistant-main\` (folder)

2. **Double-click `install.bat`.**
   - It will ask for the path to your *existing* project folder (the one
     with your real `.env` and `Data` folder in it).
   - Paste that path and press Enter.
   - It deletes the old `Frontend`, `Backend`, and `Main.py` from your
     project, copies in the new ones, and installs the two new Python
     packages (`psutil`, `send2trash`).
   - **It then checks its own work** across all 6 fixes and tells you
     `SUCCESS` or exactly which one `FAILED` — no guessing.

3. Run `python Main.py` from your project folder.

## If you ever want to double check later

Run `verify.bat` from *inside your project folder* any time — it lists
each fix and whether it's currently present.

## What's new this round (Round 5)

- **Fixed: Jarvis replies in Hindi/Devanagari instead of Urdu.** The AI
  model was drifting to Devanagari script (हिन्दी) despite the Urdu
  instruction, since spoken Hindi and Urdu are nearly identical and
  Devanagari is far more common in the model's training data. Now uses
  a stronger instruction, automatic detection, a retry, and a
  Hindi-to-Urdu translation fallback as a last resort — three layers
  instead of one, so it actually works reliably.

## What's new from Round 4

- **Stop button now actually interrupts.** Clicking Stop now cuts off
  both AI reply generation and speech playback close to instantly,
  instead of only taking effect after the current response finished.

## What's new from Round 3

- **Urdu language support** via Settings (⚙) → pick Urdu voice → Save → restart.
- **Real site search**: "find page on Facebook called X" opens Facebook's
  real search results. Also works for Instagram, Amazon, LinkedIn, Wikipedia.
- **Voice file commands**: create/open/delete files by voice. Delete goes
  to Recycle Bin, not permanent deletion.

Full technical details in `jarvis-ai-assistant-main\CHANGES.md`.

