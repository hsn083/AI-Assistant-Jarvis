# Changes in this update

## Round 5: Fixed Urdu replies coming back in Hindi (Devanagari) script

**Real root cause, finally pinned down:** Urdu and Hindi are nearly the
same *spoken* language -- they mainly differ in writing system (Urdu
uses Perso-Arabic script, Hindi uses Devanagari) and some formal
vocabulary. Two different things were going wrong because of this:

1. The AI model (Groq/Llama) was sometimes ignoring the "reply in Urdu
   script" instruction and defaulting to Devanagari instead, since
   that's the far more common way this shared spoken language appears
   in its training data. This explains the chat text showing up in
   Devanagari (हिन्दी) even though Urdu was selected in Settings.
2. `Backend/RealtimeSearchEngine.py` (used for news/realtime questions)
   had no language instruction at all until this round, so it could
   answer those specific questions in English regardless of the Urdu
   setting -- a separate gap I'd already partially closed last round but
   is worth restating since it compounds the same symptom.

**Fix -- a three-layer approach, since prompting alone isn't fully
reliable for this specific Hindi/Urdu confusion:**

1. **Much stronger system instruction**, explicitly naming Devanagari as
   forbidden with concrete examples of both correct (Urdu) and
   incorrect (Devanagari) script, instead of a softer "write in Urdu
   script" phrasing that the model was apparently not treating as a hard
   constraint.
2. **Automatic detection + one retry.** After getting a reply, the code
   now checks whether it actually contains Devanagari characters. If it
   does, it automatically retries once with an even more forceful
   correction message ("your previous reply was wrong, rewrite in Urdu
   script only").
3. **Translation fallback as a last resort.** If the retry still comes
   back in Devanagari, the code translates it from Hindi to Urdu using
   Google Translate (via the `mtranslate` library already used
   elsewhere in this project) rather than sending wrong-script text to
   text-to-speech. This guarantees Urdu-script output even in the worst
   case, instead of just hoping the prompt works.

This applies to both the regular chatbot and realtime/news answers.

**One thing I want to be upfront about:** this fixes the *reply*
language reliably. I can't fully guarantee the same for the *speech
recognition* side (what Jarvis hears when you talk) -- that step
depends on Google's cloud speech-recognition backend (used internally by
Chrome's Web Speech API, which this project relies on), and Urdu speech
recognition quality there is outside anything I can patch in this
codebase. In practice this should matter less than it sounds: even if
Chrome mis-hears your Urdu as Hindi-script text, the existing translation
step (`UniversalTranslator` in `Backend/SpeechToText.py`) already
converts whatever it hears into English before Jarvis processes it, so
your *meaning* should still come through correctly -- it's specifically
the *reply* that this round's fix locks to Urdu script.

---

# Changes from the previous update (for reference)

## Round 4: Stop button actually interrupts now, Urdu pronunciation fixed

### 1. Stop button: real root cause found and fixed

**What was actually happening:** the button itself was working correctly
(setting the stop flag) the whole time, but `ChatBot()` and
`RealtimeSearchEngine()` are single network calls to Groq's API with no
way to interrupt mid-flight, and -- separately -- `TextToSpeech()` was
always called without the stop-aware callback it's designed to accept,
so once speech started playing, nothing could cut it off either. The
flag was being checked *before* and *after* these operations, but never
*during* them, so Stop only ever "worked" once the in-flight call or
playback finished on its own, which could be several seconds later. That
matches exactly what you described.

**Fix:**
- `Backend/Chatbot.py` and `Backend/RealtimeSearchEngine.py` both stream
  their responses chunk-by-chunk already (they were built that way) --
  added a stop-flag check *inside* that streaming loop, so clicking Stop
  now cuts the response short within about one chunk, not after the full
  reply finishes generating.
- `Main.py` now passes a real stop-aware callback into every
  `TextToSpeech()` call (except the goodbye message on exit, which
  intentionally finishes playing). `TextToSpeech` polls this ~10x/second
  while audio is playing, so Stop now interrupts speech that's already
  partway through playing too, not just speech that hasn't started yet.
- Hardened a few status-reading functions in `Frontend/GUI.py`
  (`GetAssistantStatus`, `GetMicrophoneStatus`) to not throw on a missing
  file, and added error logging to the Stop button's click handler so
  any future failure prints a visible error instead of silently doing
  nothing.

### 2. Urdu pronunciation fixed

Two separate real bugs were making Urdu speech sound garbled:

- **Pitch/rate tuned only for English:** `Backend/TextToSpeech.py` was
  applying a `+13%` speed and `+5Hz` pitch boost to every voice, with no
  exceptions. That boost was tuned by ear for the default English voice
  and doesn't transfer cleanly to a different language's natural pacing
  -- it was very likely making the Urdu voice sound rushed and
  distorted. Urdu voices now use neutral, untouched pitch/rate.
- **Realtime/news answers had no language instruction at all:**
  `Backend/RealtimeSearchEngine.py` never had any "reply in X language"
  instruction (unlike the plain chatbot), so a realtime question asked
  in Urdu would still come back in English -- the language of the
  underlying search results. An Urdu voice reading an English sentence
  (or, worse, a reply mixing both) is exactly what "garbled" sounds
  like. Fixed: it now gets the same language instruction as the main
  chatbot, with an explicit note to translate the English search data
  into Urdu rather than read it as-is.

Both fixes are driven by the same `InputLanguage`/voice settings as
before -- no extra setup needed beyond what you already configured in
Settings.

---

# Changes from the previous update (for reference)

## Round 3: Urdu language, real site search, and PC file commands

### 1. Urdu support (speak + recognize)

- **Root cause of "can't speak Urdu":** `Backend/Chatbot.py` had a
  hardcoded instruction forcing every reply into English, regardless of
  what language you spoke in. Fixed: it now reads `InputLanguage` from
  `.env` and instructs the model to reply in Urdu (explicitly in Urdu
  script, not Roman Urdu) when that's configured.
- **New voice options in Settings:** a proper dropdown of valid
  `edge-tts` voices including Urdu (Pakistan: Uzma/Asad, India: Gul/
  Salman), instead of a free-text field where you'd need to already know
  the exact voice ID string. Picking a voice automatically syncs the
  matching listening language too.
- **Fixed a real bug in the language dropdown:** it previously offered
  bare codes like `"ur"`, `"en"`, but the speech-recognition engine needs
  a full locale tag like `ur-PK` to reliably work in the browser. Now
  uses proper tags throughout (`en-US`, `ur-PK`, `ur-IN`, etc). Your
  existing `.env` with bare `en` still works fine — only new Urdu setups
  need the full tag, which Settings now sets automatically.
- **Fixed TTS truncation bug:** when a long reply gets shortened for
  speech (so Jarvis doesn't read out a huge answer), it used to split on
  `.` only — Urdu sentences end in `۔`, a different character, so this
  silently failed to find sentence boundaries in Urdu text. Now splits on
  `.`, `۔`, `!`, and `؟` correctly, and uses an Urdu "rest is on the chat
  screen" filler line instead of an English one when speaking Urdu.

**To switch to Urdu:** open Settings (⚙ in the top bar) → pick a Urdu
voice → Save → restart Jarvis.

### 2. Site search actually works now (the Facebook issue)

**What was happening:** "find page on Facebook called X" was being
correctly classified as a general chat question (no automation category
matched it), so it went straight to the plain Groq chatbot — which
correctly and honestly said it can't access the internet, since it
really can't on its own. That response wasn't a bug exactly, but it
meant a request like this just didn't do anything useful.

**Fix:** added a new `site search` command category. "find page on
facebook called islamic lab" now actually opens Facebook's real search
results page for "islamic lab" in your browser, instead of going to the
chatbot. Also works for Instagram, Twitter/X, LinkedIn, Amazon,
Wikipedia, Reddit, Pinterest, and GitHub by name; unrecognized sites fall
back to a Google `site:` search so it still does something useful.

**Also fixed along the way:** found and fixed a real typo bug in
`Backend/Model.py` — the word `"open"` was misspelled `"ohepen"` in the
filter list, which meant **every single "open app/website" voice command
was silently being dropped** before it ever reached automation. This was
a pre-existing bug unrelated to your Facebook report, but almost
certainly affected other commands too.

**Important limit:** this is targeted search, not general autonomous
browsing. Jarvis still can't click around inside a website, fill out
forms, or read page content back to you — it opens the right results
page and you take it from there. True autonomous browsing (a system that
navigates and reads pages like a person) is a much larger feature outside
this update's scope.

### 3. File management by voice (create / open / delete)

Three new voice commands, with no folder restriction (per your choice):

- **"create a file called notes.txt on my desktop"** → creates an empty
  file at that location (creates parent folders if needed; won't
  overwrite an existing file).
- **"open my downloads folder"** / **"open report.docx"** → opens a file
  or folder with its default app. If you don't give a full path, it
  checks Desktop, Documents, Downloads, Pictures, Music, and Videos for a
  matching name.
- **"delete the file called old_notes.txt"** → moves the file to the
  **Recycle Bin**, not permanent deletion. This was a deliberate safety
  choice: voice transcription can mishear a filename, and an
  unrecoverable delete is the one mistake that can't be undone. Recycle
  Bin deletion means a misheard command is still recoverable.
- All three are also announced in the chat panel before they run (e.g.
  "Moving to Recycle Bin: old_notes.txt"), so you can see exactly what
  Jarvis understood.

**New dependency:** `send2trash` (added to `Requirements.txt`) — this is
what makes delete recoverable instead of permanent.

---

# Changes from the previous update (for reference)

## ⚠️ IMPORTANT: how to install this update correctly

Last time, only some files were copied over, which left old and new code
mixed together — that's almost certainly what caused the broken-looking
screen you saw (empty dashes instead of text, stray colored borders,
oversized pill shapes). Python doesn't politely refuse to run a mismatched
mix of old/new files; it just produces something visually broken like
that.

**To install this update correctly:**

1. Close the app completely if it's running.
2. **Delete these from your project folder entirely:**
   - the whole `Frontend` folder
   - `Main.py`
   - any `__pycache__` folders anywhere in the project (search and delete
     all of them — stale compiled bytecode can also cause weird mismatches)
3. **Copy in the new ones** from this zip:
   - the whole `Frontend` folder
   - `Main.py`
4. **Do not** mix old and new files — copy both as complete wholesale
   replacements, not a merge.
5. Your `.env`, `Data` folder, and `Backend` folder are untouched by this
   update — leave your existing ones in place.
6. Run `pip install -r Requirements.txt` (only `psutil` is new).
7. Launch with `python Main.py`.

If it still looks wrong after a full clean replacement, send me a fresh
screenshot — that'll tell us it's a real bug in the code, not a file-sync
issue, and I'll dig in further.

## Round 2 fixes (this update)

### Real bug found and fixed: stylesheet cascade corrupting nested widgets

Independent of the file-mixing issue above, I found and fixed a genuine
bug while re-auditing the code: `SidebarCard` set its background/border
using a bare Qt stylesheet type-selector (`QFrame { ... }`). In Qt,
that selector form cascades to **every** `QFrame` nested inside it, not
just the one it's set on — including the thin 6px progress-bar `track`/
`fill` frames inside `MetricBar`. That could turn the slim progress bars
into bordered, rounded mini-panels and squash the label text into the
corner, which actually matches the visual pattern in your screenshot
quite well. Fixed by scoping the stylesheet to `QFrame#sidebarCard` via
`setObjectName`, so it only ever applies to the card itself. Applied the
same defensive fix to `CustomTopBar`.

### New: Network usage bar

Added a 4th bar to System Stats (CPU / RAM / Disk / **Network**), matching
your `index.html` reference. Calculated from `psutil`'s network I/O
counters as combined send+receive throughput, scaled against a 50 Mbps
reference ceiling (network "usage" has no natural 0–100% scale the way
CPU/RAM/disk do, so this is an approximation, not a literal interface
utilization percentage).

### New: Weather city search box

The Weather card now has a "Enter city name..." search box (matching
`index.html`), so you can look up any city's weather on demand instead of
only ever showing the fixed city from `.env`.

### New: Camera placeholder panel

Added back a styled Camera card (status dot + "Camera OFF" + "No Signal"
preview box), matching the look in `index.html`. This is still a visual
placeholder only — no webcam is opened — per your earlier instruction
that no live camera feature was needed.

---

# Changes from the previous update (for reference)

## 1. Bug fix: voice "stop" command now works

**Root cause:** Nothing in the codebase ever listened for a spoken "stop."
The Stop *button* worked because it called `SetStopFlag(True)` directly.
But when you said "stop" out loud, `SpeechRecognition()` just transcribed
it like any other sentence and sent it to the AI decision model
(`FirstLayerDMM` in `Backend/Model.py`) to classify — and "stop" was never
one of its known categories (open/close/play/general/realtime/etc), so it
did nothing useful, slowly, via an API call.

**Fix (`Main.py`):**
- Added `STOP_PHRASES` and `IsStopCommand()` — a fast local check for
  "stop", "cancel", "never mind", "shut up", etc.
- Both `MainExecution()` (voice) and `FirstThread()` (typed text) now check
  `IsStopCommand()` immediately after getting the query, *before* it's
  sent to `ProcessQuery`/`FirstLayerDMM`. If matched, `HandleStopCommand()`
  runs — the same effective action as clicking the Stop button.
- This means saying "stop" now reacts instantly (no AI round-trip) and
  behaves identically to pressing the button.

**Known limitation (architectural, not fixed):** `TextToSpeech()` runs
synchronously on the same thread that listens for voice input. While
Jarvis is mid-sentence speaking an answer, it is not yet listening again,
so a spoken "stop" during playback can't be heard until that sentence
finishes. The Stop *button* still works instantly in that window since
it's on a separate UI thread. Making voice interruption work mid-speech
would require restructuring `TextToSpeech`/`SpeechRecognition` to run
concurrently — a bigger change outside this request's scope. Flagging
this so it doesn't surprise you.

## 2. Bug fix: Stop button could silently "un-stop" itself

**Root cause:** `_resetStop()` was called on a blind 2.5-second
`QTimer.singleShot`, regardless of whether the backend had actually
finished what it was doing. If a task ran longer than 2.5s, the stop flag
would flip back to `False` on its own and the backend would carry on.

**Fix (`Frontend/GUI.py`, `CustomTopBar.stopJarvis`):** the button now
re-enables itself quickly (800ms, just for UI responsiveness) but the
actual stop flag is only cleared once a 150ms watcher confirms the
backend status has returned to `"Available..."` — i.e. once the backend
loop has actually observed the flag and stopped what it was doing.

## 3. GUI redesign

Rebuilt around the reference image layout:

- **Top bar:** logo + Online status (left), live clock (center), weather
  pill + Stop/Settings (right). Removed the old Home/Chat page toggle —
  everything now lives on one screen, like the reference.
- **Left sidebar:**
  - **System Stats** — live CPU/RAM/Disk usage via `psutil`, refreshed
    every 2s.
  - **Weather** — live data via OpenWeatherMap (needs `WeatherAPIKey` in
    `.env` or Settings — see below). Shows a friendly message if the key
    is missing instead of breaking.
  - **System Uptime** — session timer, plus persistent sessions/commands
    counters (stored in `Data/Stats.json`).
- **Center:** new custom-painted animated AI core (`AICore` class) that
  changes color/speed based on status (listening/thinking/searching/
  answering/stopped), assistant name, status pill, and mic/keyboard
  buttons.
- **Right:** Conversation panel restyled to match the reference —
  header with Clear/Export, message list, message input.
- **No camera panel**, per your request.
- **Settings dialog** now also has Weather API Key + City fields, so you
  don't have to hand-edit `.env`.

## What you need to do

1. Install the one new dependency:
   ```
   pip install -r Requirements.txt
   ```
   (only `psutil` is new; everything else you already had)

2. Add your weather API key. Two options:
   - Open the app → click the ⚙ Settings button → fill in "Weather API
     Key" and "Weather City" → Save. **Restart the app** after saving
     (env vars are read at startup).
   - Or edit `.env` directly — see `.env.example` for the exact key
     names (`WeatherAPIKey`, `WeatherCity`).

   Free key: https://openweathermap.org/api (the free "Current Weather
   Data" tier is enough).

3. Your real `.env` (with your existing API keys) was **not** overwritten
   or included in this delivered copy — only `.env.example` is included,
   as a template. Copy your real `.env` back into the project root before
   running (or just keep using your existing one — none of your existing
   keys were touched).

## Testing note from me

I don't have a Windows machine, display, or network access in this
sandbox, so I could not actually launch the PyQt5 app or screenshot it to
confirm it visually matches what I intended. I checked everything
statically — syntax-compiled both files clean, and manually traced every
method/attribute reference across the rewritten classes to catch typos or
missing wiring. Please run it and let me know what (if anything) looks or
behaves wrong — I'd rather fix a real issue you hit than have you
discover it cold.
