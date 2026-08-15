import datetime
import time
import threading
import winsound
import speech_recognition as sr
from dateutil import parser as dateparser

ALARM_SOUND = "alarm.wav" 

def _run_alarm(target_hour: int, target_min: int):
    while True:
        now = datetime.datetime.now()
        if now.hour == target_hour and now.minute == target_min:
            winsound.PlaySound(ALARM_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            _wait_for_stop()
            break
        time.sleep(15)

def _wait_for_stop():
    r = sr.Recognizer()
    while True:
        try:
            with sr.Microphone() as source:
                r.pause_threshold = 1
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            query = r.recognize_google(audio, language='en-in').lower()
            if "stop" in query:
                winsound.PlaySound(None, winsound.SND_PURGE)
                break
        except Exception:
            continue

def set_alarm(time_str: str) -> str:
    """Tool function — call this from handle_query"""
    try:
        target = dateparser.parse(time_str)
    except Exception:
        return "I couldn't understand that time, please try again like 7:30 AM"

    thread = threading.Thread(target=_run_alarm, args=(target.hour, target.minute), daemon=True)
    thread.start()
    return f"Alarm set for {target.strftime('%I:%M %p')}"