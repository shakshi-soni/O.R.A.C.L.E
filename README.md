# 🔮 O.R.A.C.L.E

A voice-controlled AI assistant with wake-word activation, system automation, and a real-time animated 3D holographic UI. Built as a personal engineering project exploring agentic voice interfaces.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-UI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-8A2BE2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)

---

## Quick Start

```bash
# 1. Install dependencies
py -3.13 -m pip install -r requirements.txt

# 2. Set your API keys
# Create a .env file in the project root:
# GEMINI_API_KEY=your_key_here
# NEWS_API_KEY=your_key_here

# 3. Run it
py -3.13 oracle.py
```

This launches the voice loop and the holographic UI together.

---

## Architecture Overview

```
Voice Input
    │
    ▼
┌─────────────────────────────────────────┐
│         WAKE WORD DETECTION              │
│  "wake up" / "hello" / "hi" → activate   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│         COMMAND ROUTER (oracle.py)       │
│  Matches query against known intents     │
└─────────────────────────────────────────┘
    │
    ├── System control  → apps, notepad, cmd, camera
    ├── Media            → music, YouTube
    ├── Info lookup       → Wikipedia, weather, news, IP
    ├── Utilities         → alarm, reminders, screenshot
    ├── System stats      → battery, brightness, volume
    │
    ▼ (no match)
┌─────────────────────────────────────────┐
│         GEMINI FALLBACK (ai_brain.py)    │
│  Open-ended conversational response      │
└─────────────────────────────────────────┘
    │
    ▼
Text-to-Speech Response (pyttsx3 / SAPI5)
    │
    ▼
"bye" → sleeps quietly, waits for wake word again
```

---

## Project Structure

```
oracleproject/
├── oracle.py              # Main entry point — voice loop & command routing
├── AI_intergration.py     # Gemini API wrapper & system prompt
├── oracle_ui.py           # PyQt6 holographic UI (runs on main thread)
├── MyAlarm.py             # Voice-controlled looping alarm
├── Reminders.py           # Reminder creation & retrieval
├── reminders.json         # Persisted reminder storage
├── requirements.txt
└── .env                   # API keys (gitignored)
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Fresh `pyttsx3` engine per `speak()` call | SAPI5 silently drops audio on repeated calls from a reused engine instance — reinit avoids this |
| UI on main thread, voice loop on background thread | Qt's GUI must own the main thread on Windows; running it in the background caused invisible/broken windows |
| `AppOpener` for generic "open X" | Avoids hardcoding one `elif` per application — opens any installed app by name |
| Gemini as fallback, not primary router | Keeps deterministic commands (alarms, system control) fast and predictable; LLM only handles open-ended queries |

---

## Features


🎙️ Wake-word activated, continuous listening, graceful sleep on "bye" (no process kill, resumes on next wake word)
🤖 Gemini-powered fallback for open-ended conversation — not just a fixed command list
⏰ Voice-set alarm with a looping alert that only stops when you say "stop"
📝 Persistent reminders, saved to disk across restarts
🖥️ Opens any installed application by name — no hardcoded app list
🎵 Plays local music or searches/plays songs on YouTube by voice
🌐 Live weather, latest news headlines, IP address, and real-time location lookups
📚 Wikipedia summarization on demand
💬 Sends WhatsApp messages instantly by voice
📊 Reports battery %, and adjusts screen brightness and system volume
📸 Takes screenshots and switches between open windows, hands-free
😄 Tells jokes and has a bit of personality (it knows who built it)
🌀 Custom-built animated 3D holographic UI — a real rotating geodesic wireframe sphere (not a static image), rendered with live perspective projection and depth-based shading

---

## Known Limitations

- Windows-only (`pyttsx3` SAPI5, `winsound`, `screen_brightness_control`)
- No persistent conversation memory across sessions
- Weather/IP lookups depend on third-party API uptime
- Single-user, single-process — no multi-session support

---

## 🙋‍♀️ About the Developer

Built by **Shakshi Soni** — Data Science & AI student at IIT Guwahati, exploring agentic AI systems that combine voice, tool-calling, and real-time UI.


📫 **Connect with me:**
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/shakshi-soni-961048411/)
<div align="center">

**⭐ If you found this project interesting, a star helps a lot.**

</div>
