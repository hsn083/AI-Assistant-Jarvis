"""
TextToSpeech.py  —  Reliable streaming TTS pipeline
=====================================================

Uses ONLY pygame + edge_tts — no pydub, no sounddevice, no ffmpeg.
These were the two libraries that were already working before the
last optimization attempt broke voice output.

Speed improvement is achieved by:
  1. Splitting the response into sentences
  2. Generating sentence N+1 audio in a background thread WHILE
     sentence N is playing — so generation and playback overlap
  3. Each sentence gets its own temp file (speech_0.mp3, speech_1.mp3)
     so there's no file-lock conflict between generation and playback
  4. Sentence files are cleaned up immediately after playing
"""

import asyncio
import edge_tts
import os
import queue
import random
import threading
import time
import re as _re

import pygame
from dotenv import dotenv_values

# ── Config ──────────────────────────────────────────────────────────────────────
env_vars       = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-JennyNeural")
InputLanguage  = env_vars.get("InputLanguage", "en")

os.makedirs("Data", exist_ok=True)

# ── Voice parameters ─────────────────────────────────────────────────────────────
def _get_voice() -> str:
    voice = (AssistantVoice or "").strip()
    if voice:
        return voice
    return "ur-PK-AsadNeural" if (InputLanguage or "en").lower().startswith("ur") else "en-US-GuyNeural"

def _voice_params() -> dict:
    voice = (AssistantVoice or "").lower()
    if voice == "ur-pk-asadneural":
        return {"pitch": "-3Hz", "rate": "+5%"}
    if voice == "ur-in-salmanneural":
        return {"pitch": "-2Hz", "rate": "+5%"}
    if voice.startswith("ur-"):
        return {"pitch": "+0Hz", "rate": "+0%"}
    return {"pitch": "+5Hz", "rate": "+13%"}

# ── Urdu text cleanup ────────────────────────────────────────────────────────────
_URDU_NUM_MAP = {
    "0": "صفر", "1": "ایک", "2": "دو", "3": "تین", "4": "چار",
    "5": "پانچ", "6": "چھ", "7": "سات", "8": "آٹھ", "9": "نو",
}

def _preprocess_urdu(text: str) -> str:
    text = _re.sub(r'[*_`#]', '', text)
    text = _re.sub(r'^\s*[-•·]\s*', '', text, flags=_re.MULTILINE)
    text = _re.sub(r'(?<!\d)([0-9])(?!\d)',
                   lambda m: _URDU_NUM_MAP.get(m.group(0), m.group(0)), text)
    text = _re.sub(r'(?<=[\u0600-\u06FF])\s*[;:,]\s*(?=[\u0600-\u06FF])', '، ', text)
    text = _re.sub(r'[ \t]+', ' ', text).strip()
    return text

# ── Sentence splitter ────────────────────────────────────────────────────────────
_SPLIT_RE = _re.compile(r'(?<=[.!?\u06d4\u061f])\s+')

def _split_sentences(text: str) -> list:
    raw    = _SPLIT_RE.split(text.strip())
    merged = []
    buf    = ""
    for s in raw:
        s = s.strip()
        if not s:
            continue
        buf = (buf + " " + s).strip() if buf else s
        if len(buf) >= 40:
            merged.append(buf)
            buf = ""
    if buf:
        if merged:
            merged[-1] += " " + buf
        else:
            merged.append(buf)
    return merged or [text.strip()]

# ── Pygame: init once ────────────────────────────────────────────────────────────
try:
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=1024)
    pygame.mixer.init()
    pygame.mixer.music.set_volume(1.0)
    _MIXER_OK = True
except Exception as e:
    print(f"[TTS] pygame mixer init error: {e}")
    _MIXER_OK = False

# ── Core: generate one sentence to an mp3 file ──────────────────────────────────
async def _generate_to_file(sentence: str, filepath: str) -> bool:
    """Generate TTS audio for one sentence and save it to filepath.
    Returns True on success, False on failure."""
    if not sentence.strip():
        return False
    if (InputLanguage or "en").lower().startswith("ur"):
        sentence = _preprocess_urdu(sentence)
    if not sentence.strip():
        return False
    try:
        voice  = _get_voice()
        params = _voice_params()
        communicate = edge_tts.Communicate(
            sentence, voice,
            pitch=params["pitch"], rate=params["rate"]
        )
        await communicate.save(filepath)
        return os.path.exists(filepath) and os.path.getsize(filepath) > 0
    except Exception as e:
        print(f"[TTS] generation error: {e}")
        return False

def _generate_sync(sentence: str, filepath: str) -> bool:
    """Blocking wrapper around the async generator."""
    try:
        return asyncio.run(_generate_to_file(sentence, filepath))
    except Exception as e:
        print(f"[TTS] asyncio error: {e}")
        return False

# ── Playback: play one mp3 file via pygame ───────────────────────────────────────
def _play_file(filepath: str, stop_fn) -> bool:
    """Play an mp3 file with pygame, polling stop_fn every 100ms.
    Returns True if fully played, False if interrupted."""
    if not _MIXER_OK:
        print("[TTS] pygame mixer not available")
        return True
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            if not stop_fn():
                pygame.mixer.music.stop()
                return False
            clock.tick(10)   # 100ms polling interval
        return True
    except Exception as e:
        print(f"[TTS] playback error: {e}")
        return True
    finally:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

# ── Filler lines ─────────────────────────────────────────────────────────────────
_FILLERS_EN = [
    "The rest of the result has been printed to the chat screen, kindly check it out sir.",
    "The rest of the text is now on the chat screen, sir, please check it.",
    "You can see the rest of the text on the chat screen, sir.",
    "Sir, the remaining part of the answer is on the chat screen.",
    "Sir, please look at the chat screen for the complete answer.",
]
_FILLERS_UR = [
    "باقی جواب چیٹ سکرین پر موجود ہے، براہ کرم وہاں دیکھ لیں۔",
    "مکمل جواب چیٹ سکرین پر لکھ دیا گیا ہے۔",
    "باقی تفصیل چیٹ سکرین پر دیکھی جا سکتی ہے۔",
    "مزید معلومات کے لیے چیٹ سکرین ملاحظہ کریں۔",
]

def _fillers():
    return _FILLERS_UR if (InputLanguage or "en").lower().startswith("ur") else _FILLERS_EN

# ── Public interface ─────────────────────────────────────────────────────────────

def TextToSpeech(text: str, stop_fn=lambda r=None: True):
    """
    Sentence-streaming TTS pipeline.

    For each sentence:
      1. Start generating audio for sentence[i+1] in a background thread
      2. Play sentence[i] while that's happening
    → Generation and playback overlap, reducing perceived latency.
    """
    text = str(text).strip()
    if not text:
        return
    if not _MIXER_OK:
        print(f"[TTS] no audio output available, text was: {text[:80]}")
        return

    sentences = _split_sentences(text)

    # Trim long responses: speak first 2 sentences + filler
    if len(sentences) > 4 and len(text) >= 250:
        sentences = sentences[:2] + [random.choice(_fillers())]

    t0 = time.perf_counter()

    # Queue carries (filepath, success_bool)
    file_queue = queue.Queue()

    def _gen_and_queue(sentence: str, idx: int):
        fp = os.path.join("Data", f"speech_{idx}.mp3")
        ok = _generate_sync(sentence, fp)
        file_queue.put((fp, ok))

    # Start generating sentence 0 immediately
    threading.Thread(target=_gen_and_queue, args=(sentences[0], 0), daemon=True).start()

    for i, sentence in enumerate(sentences):
        # Get the audio file for this sentence (blocks until ready)
        filepath, ok = file_queue.get()

        # Start generating the next sentence while this one plays
        if i + 1 < len(sentences):
            threading.Thread(
                target=_gen_and_queue,
                args=(sentences[i + 1], i + 1),
                daemon=True
            ).start()

        if not ok:
            print(f"[TTS] skipping sentence {i} — generation failed")
            continue

        if i == 0:
            print(f"[TTS] ⚡ first audio ready: {(time.perf_counter()-t0)*1000:.0f}ms")

        played = _play_file(filepath, stop_fn)
        if not played:
            # Drain remaining queue entries and clean up their files
            while not file_queue.empty():
                try:
                    fp, _ = file_queue.get_nowait()
                    if os.path.exists(fp):
                        os.remove(fp)
                except Exception:
                    pass
            break

    print(f"[TTS] total: {(time.perf_counter()-t0)*1000:.0f}ms")


# Backwards-compat alias
def TTS(text: str, func=lambda r=None: True):
    TextToSpeech(text, func)

# Legacy alias
responses = _FILLERS_EN

if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter text: "))
