import os
from groq import Groq
from dotenv import load_dotenv
import resend


load_dotenv() 

MODEL_NAME = "llama-3.3-70b-versatile"

api_key = os.getenv("GROQ_API_KEY")

print("DEBUG GROQ KEY:", api_key)

client = Groq(api_key=api_key)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

resend.api_key = RESEND_API_KEY