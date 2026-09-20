# O.R.A.C.L.E.

A voice-controlled assistant with wake-word activation, system automation, and a custom animated 3D holographic UI. Personal project exploring how far a voice interface can go without a full agent framework.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-UI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-8A2BE2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)

## What it does

Say a wake word ("wake up", "hello", "hi") and it starts listening. Most commands go through a deterministic router — system control, opening apps, media, weather/news/IP lookups, alarms, reminders, screenshots, volume/brightness — and only genuinely open-ended stuff falls through to Gemini for a conversational response. Say "bye" and it goes quiet without killing the process, ready for the next wake word.

It can open any installed app by name (via `AppOpener`, not a hardcoded list per app), play local music or search YouTube by voice, send WhatsApp messages, set an alarm that loops until you tell it to stop, and hold reminders across restarts since they're written to disk.

The UI is a rotating geodesic wireframe sphere, hand-built with real rotation matrices and perspective projection, drawn frame-by-frame with `QPainter` — not a canned animation or a static asset.

## Architecture

```
Voice input
    ↓
Wake word detection ("wake up" / "hello" / "hi")
    ↓
Command router (oracle.py) — matches against known intents
    ↓
   ┌──────────┬────────┬───────────┬─────────────┬──────────────┐
   ↓          ↓        ↓           ↓              ↓
 system    media    info lookup  utilities    system stats
 control  (music/                (alarm,      (battery,
 (apps,    YouTube)  (wiki,       reminders,   brightness,
 notepad,            weather,     screenshot)  volume)
 cmd,                news, IP)
 camera)
    │
    ↓ (no match)
Gemini fallback (ai_brain.py) — open-ended conversation
    ↓
Text-to-speech response (pyttsx3 / SAPI5)
```

## Running it

```bash
py -3.13 -m pip install -r requirements.txt

# .env file:
# GEMINI_API_KEY=your_key_here
# NEWS_API_KEY=your_key_here

py -3.13 oracle.py
```
Launches the voice loop and the UI together.

## Project structure

```
oracleproject/
├── oracle.py              # main entry point — voice loop & routing
├── AI_intergration.py     # Gemini wrapper & system prompt
├── oracle_ui.py           # PyQt6 holographic UI (main thread)
├── MyAlarm.py             # voice-controlled looping alarm
├── Reminders.py           # reminder creation & retrieval
├── reminders.json         # persisted reminder storage
├── requirements.txt
└── .env                   # gitignored
```

## Things I had to actually debug my way through

- `pyttsx3` silently drops audio if you reuse the same engine instance across repeated `speak()` calls — fixed by spinning up a fresh engine per call. Took a while to figure out because it fails silently, no exception.
- Qt needs the main thread on Windows, so the voice loop runs in the background and the UI stays on the main thread — got this backwards at first and ended up with invisible/broken windows.
- Migrated from Python 3.14 down to 3.13 partway through because `pyaudio` didn't have wheels for 3.14 yet at the time.
- Gemini is a fallback, not the router — deterministic commands (alarms, system control) never touch the LLM, so they stay fast and predictable. Only open-ended queries hit Gemini. This was a deliberate choice after an earlier version routed everything through the LLM and got noticeably slower and less predictable.

## Limitations

- Windows-only — `pyttsx3`/SAPI5, `winsound`, and `screen_brightness_control` are all Windows-specific
- No conversation memory across sessions, each session starts fresh
- Weather/IP/news lookups depend on third-party API uptime, no fallback if they're down
- Single-user, single-process, wasn't built with multi-session use in mind

## Why I built this

I wanted to see how far I could get with a hybrid approach — deterministic routing for anything time-sensitive or safety-relevant (alarms, opening apps, system control), and an LLM only for the parts that actually need open-ended reasoning — instead of routing everything through an LLM by default. The 3D UI wasn't strictly necessary for any of that, I just wanted to build a real rendering pipeline from scratch instead of using a pre-made animation, and it turned out to be one of the more interesting parts of the project.

## About

Shakshi Soni — Data Science & AI student at IIT Guwahati.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/shakshi-soni-961048411/)
