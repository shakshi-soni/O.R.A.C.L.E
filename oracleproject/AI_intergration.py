import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

system_prompt = (
    "You are a personal AI assistant. You are incredibly smart, professional, strict "
    "and a little funny. Whatever the user says, understand it and respond "
    "politely. If you really don't know what to do, say "
    "'I am really sorry, I can't help with that.'"
    " and keep in mind that you give all the updates and current information about what the user asks you it should be accurate,precise and up to date "
    " current year is 2026 and say the answer or reply in short and simple terms."
)

def ask_ai(user_query):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.5,
        ),
    )
    return response.text