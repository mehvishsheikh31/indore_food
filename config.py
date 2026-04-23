import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️  Warning: GROQ_API_KEY not found in .env file!")

_client = None

def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client

# App constants
APP_TITLE = "Indore Food Intelligence"
APP_ICON = "🍴"
DEFAULT_LAT = 22.7196
DEFAULT_LON = 75.8577
GROQ_MODEL = "llama-3.1-8b-instant"
TOP_N = 5
