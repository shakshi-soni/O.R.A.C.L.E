import os
import json
import time
import threading
import datetime
import dateparser

REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")
_lock = threading.Lock()
_speak_fn = None  # injected from oracle.py to avoid circular import


def init_reminders(speak_fn):
    """Call once from oracle.py, passing in the speak() function."""
    global _speak_fn
    _speak_fn = speak_fn
    _load()
    thread = threading.Thread(target=_checker_loop, daemon=True)
    thread.start()


def _load():
    if not os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "w") as f:
            json.dump([], f)


def _read_all():
    with _lock:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)


def _write_all(reminders):
    with _lock:
        with open(REMINDERS_FILE, "w") as f:
            json.dump(reminders, f, indent=2)


def add_reminder(text: str, time_str: str) -> str:
    """Tool function. text = what to remind, time_str = natural language time."""
    target = dateparser.parse(
        time_str,
        settings={"PREFER_DATES_FROM": "future"}
    )
    if not target:
        return "I couldn't understand that time, please try again like 'tomorrow at 6 PM'"

    reminders = _read_all()
    reminders.append({
        "id": len(reminders) + 1,
        "text": text,
        "datetime": target.strftime("%Y-%m-%d %H:%M"),
        "done": False,
    })
    _write_all(reminders)
    return f"Reminder set: {text}, on {target.strftime('%A, %B %d at %I:%M %p')}"


def list_reminders() -> str:
    """Tool function. Lists all upcoming (not-done) reminders."""
    reminders = [r for r in _read_all() if not r["done"]]
    if not reminders:
        return "You have no upcoming reminders"

    reminders.sort(key=lambda r: r["datetime"])
    lines = []
    for r in reminders:
        dt = datetime.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M")
        lines.append(f"{r['text']} on {dt.strftime('%A at %I:%M %p')}")
    return "Here is your schedule: " + "; ".join(lines)


def _checker_loop():
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        reminders = _read_all()
        changed = False
        for r in reminders:
            if not r["done"] and r["datetime"] == now:
                if _speak_fn:
                    _speak_fn(f"Reminder: {r['text']}")
                r["done"] = True
                changed = True
        if changed:
            _write_all(reminders)
        time.sleep(30)