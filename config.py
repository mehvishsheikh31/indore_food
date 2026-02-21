import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize the Groq Client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in .env file!")

client = Groq(api_key=GROQ_API_KEY)

def get_groq_client():
    return client