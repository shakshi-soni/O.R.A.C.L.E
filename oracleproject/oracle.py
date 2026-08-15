import os
import datetime
import sys
import threading
import traceback
import pyttsx3
import pythoncom
import speech_recognition as sr
import requests
import psutil
import pyautogui
import wikipedia
import pywhatkit as kit
import pyjokes
import screen_brightness_control as sbc
from dotenv import load_dotenv
from google import genai
from google.genai import types
from AppOpener import open as app_open, close as app_close
from MyAlarm import set_alarm
from Reminders import init_reminders, add_reminder, list_reminders
from oracle_ui import run_ui

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ---------- Voice engine ----------
# NOTE: engine is created fresh inside speak() each call, not once globally.
# pyttsx3 (SAPI5) needs COM initialized per-thread, and speak() is called
# from a background thread (voice_loop), so a single shared engine object
# created on the main thread will silently fail to produce audio.
_speak_lock = threading.Lock()

def speak(text):
    print(text)
    with _speak_lock:
        pythoncom.CoInitialize()
        try:
            local_engine = pyttsx3.init("sapi5")
            local_engine.setProperty("voice", local_engine.getProperty("voices")[0].id)
            local_engine.say(text)
            local_engine.runAndWait()
        finally:
            pythoncom.CoUninitialize()

def takecommand():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=0.5)
            # timeout=None -> wait indefinitely for user to start speaking (no crash on silence)
            # phrase_time_limit=None -> no cap once speech starts, stops on natural pause
            audio = r.listen(source, timeout=None, phrase_time_limit=None)
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}")
        return query
    except sr.UnknownValueError:
        return None
    except Exception as e:
        print(f"takecommand error: {e}")
        return None

def wish():
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good Morning! I am Oracle mam. Please tell me how may I help you?")
    elif hour < 18:
        speak("Good Afternoon! I am Oracle mam. Please tell me how may I help you?")
    else:
        speak("Good Evening! I am Oracle mam. Please tell me how may I help you?")

# ---------- TOOLS ----------

def get_weather(city: str) -> str:
    response = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
    if response.status_code == 200:
        current = response.json()["current_condition"][0]
        return f"{current['temp_C']} degrees Celsius, {current['weatherDesc'][0]['value']}"
    return "City not found"

def get_battery() -> str:
    percentage = psutil.sensors_battery().percent
    if percentage >= 75:
        note = "we have enough power to continue"
    elif percentage >= 30:
        note = "we should connect to charging soon"
    else:
        note = "we should connect to charging now"
    return f"Battery is at {percentage} percent, {note}"

def open_app(app_name: str) -> str:
    try:
        app_open(app_name, match_closest=True)
        return f"Opened {app_name}"
    except Exception:
        return f"Couldn't find {app_name} on this system"

def close_app(app_name: str) -> str:
    try:
        app_close(app_name, match_closest=True)
        return f"Closed {app_name}"
    except Exception:
        return f"Couldn't close {app_name}"

def search_wikipedia(topic: str) -> str:
    try:
        return wikipedia.summary(topic, sentences=2)
    except Exception:
        return f"Couldn't find anything on Wikipedia for {topic}"

def set_brightness(direction: str) -> str:
    current = sbc.get_brightness()[0]
    if direction == "increase":
        sbc.set_brightness(min(100, current + 25))
        return "Brightness increased"
    sbc.set_brightness(max(0, current - 25))
    return "Brightness decreased"

def play_youtube(song: str) -> str:
    kit.playonyt(song)
    return f"Playing {song} on YouTube"

def search_youtube(query: str) -> str:
    import webbrowser
    webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
    return f"Searching {query} on YouTube"

def tell_joke() -> str:
    return pyjokes.get_joke()

def get_ip_address() -> str:
    ip = requests.get('https://api.ipify.org').text
    return f"Your IP address is {ip}"

def get_location() -> str:
    try:
        ip = requests.get('https://api.ipify.org').text
        geo = requests.get(f'https://get.geojs.io/v1/ip/geo/{ip}.json').json()
        return f"We are in {geo['city']} city, {geo['country']}"
    except Exception:
        return "Sorry, I couldn't find our location due to a network issue"

def take_screenshot() -> str:
    path = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots", "screenshot.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = pyautogui.screenshot()
    img.save(path)
    return "Screenshot taken and saved"

def adjust_volume(direction: str) -> str:
    if direction == "up":
        pyautogui.press("volumeup")
        return "Volume increased"
    pyautogui.press("volumedown")
    return "Volume decreased"

def get_news() -> str:
    url = f"https://newsapi.org/v2/top-headlines?sources=the-times-of-india&apiKey={NEWS_API_KEY}"
    articles = requests.get(url).json().get("articles", [])[:5]
    headlines = [a["title"] for a in articles]
    return "Here are the latest headlines: " + "; ".join(headlines)

def play_local_music() -> str:
    music_dir = os.path.expanduser("~/Music")
    songs = [s for s in os.listdir(music_dir) if s.endswith(".mp3")]
    if not songs:
        return "No music files found"
    os.startfile(os.path.join(music_dir, songs[0]))
    return "Playing music"

TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "get_battery": get_battery,
    "open_app": open_app,
    "close_app": close_app,
    "search_wikipedia": search_wikipedia,
    "set_brightness": set_brightness,
    "play_youtube": play_youtube,
    "search_youtube": search_youtube,
    "tell_joke": tell_joke,
    "get_ip_address": get_ip_address,
    "get_location": get_location,
    "take_screenshot": take_screenshot,
    "adjust_volume": adjust_volume,
    "get_news": get_news,
    "play_local_music": play_local_music,
    "set_alarm": set_alarm,
    "add_reminder": add_reminder,
    "list_reminders": list_reminders,
}

tools = types.Tool(function_declarations=[
    {"name": "get_weather", "description": "Get current weather for a city",
     "parameters": {"type": "OBJECT", "properties": {"city": {"type": "STRING"}}, "required": ["city"]}},
    {"name": "get_battery", "description": "Get current laptop battery percentage",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "open_app", "description": "Open an application on the system",
     "parameters": {"type": "OBJECT", "properties": {"app_name": {"type": "STRING"}}, "required": ["app_name"]}},
    {"name": "close_app", "description": "Close an application on the system",
     "parameters": {"type": "OBJECT", "properties": {"app_name": {"type": "STRING"}}, "required": ["app_name"]}},
    {"name": "search_wikipedia", "description": "Search Wikipedia and get a short summary",
     "parameters": {"type": "OBJECT", "properties": {"topic": {"type": "STRING"}}, "required": ["topic"]}},
    {"name": "set_brightness", "description": "Increase or decrease screen brightness",
     "parameters": {"type": "OBJECT", "properties": {"direction": {"type": "STRING", "enum": ["increase", "decrease"]}}, "required": ["direction"]}},
    {"name": "play_youtube", "description": "Play a specific song on YouTube",
     "parameters": {"type": "OBJECT", "properties": {"song": {"type": "STRING"}}, "required": ["song"]}},
    {"name": "search_youtube", "description": "Search something on YouTube",
     "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}},
    {"name": "tell_joke", "description": "Tell a random joke",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "get_ip_address", "description": "Get the system's public IP address",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "get_location", "description": "Get the current city and country based on IP",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "take_screenshot", "description": "Take a screenshot and save it",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "adjust_volume", "description": "Increase or decrease system volume",
     "parameters": {"type": "OBJECT", "properties": {"direction": {"type": "STRING", "enum": ["up", "down"]}}, "required": ["direction"]}},
    {"name": "get_news", "description": "Get the latest news headlines",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "play_local_music", "description": "Play music from the local music folder",
     "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "set_alarm", "description": "Set an alarm for a specific time",
     "parameters": {"type": "OBJECT", "properties": {"time_str": {"type": "STRING", "description": "e.g. '7:30 AM'"}}, "required": ["time_str"]}},
    {"name": "add_reminder", "description": "Add a reminder or note for a specific time",
     "parameters": {"type": "OBJECT", "properties": {
         "text": {"type": "STRING", "description": "what to remind, e.g. 'I have work to do'"},
         "time_str": {"type": "STRING", "description": "when, e.g. 'tomorrow at 6 PM'"}
     }, "required": ["text", "time_str"]}},
    {"name": "list_reminders", "description": "List all upcoming reminders/schedule",
     "parameters": {"type": "OBJECT", "properties": {}}},
])

system_prompt = (
    "You are Oracle, a personal voice assistant. You are smart, professional, "
    "strict, and a little funny. When the user asks you to DO something, use "
    "the matching tool. Otherwise reply normally, in short simple terms. "
    "Current year is 2026."
    "be active and give all acuurate answer "
    "You can call MULTIPLE tools one after another to complete a request that "
    "needs more than one step, for example checking the weather and then "
    "adding a reminder based on the result. Keep calling tools until you have "
    "everything you need, then give ONE short final spoken reply summarizing "
    "what you did."
)

conversation_history = []
MAX_STEPS = 5  # safety cap so a bad loop can't call tools forever

def handle_query(query: str):
    conversation_history.append(types.Content(role="user", parts=[types.Part(text=query)]))

    for step in range(MAX_STEPS):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation_history[-10:],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.5,
                tools=[tools],
            ),
        )

        part = response.candidates[0].content.parts[0]

        if part.function_call:
            fn_name = part.function_call.name
            args = dict(part.function_call.args)
            print(f"[step {step + 1}] calling {fn_name}({args})")
            try:
                result = TOOL_FUNCTIONS[fn_name](**args)
            except Exception as e:
                traceback.print_exc()
                result = f"Sorry, something went wrong with {fn_name}"

            # record the model's function call, then feed the tool's result
            # back in as a function_response so the model can decide whether
            # it needs another tool call or is ready to give a final answer
            conversation_history.append(types.Content(role="model", parts=[part]))
            conversation_history.append(types.Content(
                role="user",
                parts=[types.Part(function_response=types.FunctionResponse(
                    name=fn_name,
                    response={"result": result},
                ))],
            ))
            continue  # let the model decide the next step

        # no function call -> model is giving its final spoken answer
        speak(response.text)
        conversation_history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))
        return

    # safety net: stopped after MAX_STEPS tool calls without a final answer
    speak("I did a few things but I'm not fully sure I finished that one, mam.")

def taskexecution():
    wish()
    while True:
        query = takecommand()
        if query is None:
            continue
        if any(x in query.lower() for x in ["bye", "no thanks", "go sleep", "so ja"]):
            speak("Thank you for using Oracle. Have a nice day!")
            sys.exit()
        handle_query(query)

if __name__ == "__main__":
    init_reminders(speak)

    def voice_loop():
        while True:
            permission = takecommand()
            if permission is None:
                continue
            permission = permission.lower()
            if "wake up" in permission or "hello" in permission or "hi" in permission:
                speak("I am online mam, how may I help you?")
                taskexecution()
            elif "good bye" in permission or "goodbye" in permission:
                speak("Thank you for using Oracle. Have a nice day!")
                sys.exit()

    threading.Thread(target=voice_loop, daemon=True).start()
    run_ui()