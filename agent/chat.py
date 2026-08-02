from groq import Groq
import os
from config import client, MODEL_NAME


def generate_general_reply(user_input, user_name=None, history=None):

    # ---------------- HISTORY FORMAT ----------------
    history_text = ""

    if history:
        for item in history[-5:]:  # limit history
            history_text += f"User: {item['user']}\nBot: {item['bot']}\n"

    # ---------------- IMPROVED PROMPT ----------------
    prompt = f"""
You are EveryRupee 💸 — a friendly WhatsApp expense tracker assistant.

----------------------------------------
ROLE:
You ONLY reply to the user. You do NOT perform actions yourself.

----------------------------------------
LANGUAGE RULE:
- Reply in the same language the user used.
- Do NOT translate or change language.

----------------------------------------
CONTEXT:
User: {user_name or "User"}

Recent Chat:
{history_text}

----------------------------------------
CURRENT MESSAGE:
{user_input}

----------------------------------------
STRICT RULES:

1. If user wants to **add expense**:
   → Reply: "Send like this: Spent 500 on food" or "Give amount and category"

2. If user wants **summary**:
   → Reply: "Type *summary*" 

3. If user wants **income**:
   → Reply: "Send like this: Got 20000 salary"

4. If user is confused or message is unclear:
   → Give clear instructions. Example:
     "I didn't understand. 
     You can:
     • Add expense → 'Spent 300 on food'
     • Add income → 'Got 15000 salary'
     • See summary → Type 'summary'"

5. If user gives feedback or greeting:
   → Reply politely and shortly.

6. Never ask for amount unless user is clearly trying to add an expense.[Must]

----------------------------------------
STYLE:
- Keep replies short and friendly
- Use emojis when suitable
- Never give technical answers
- One clear message only

----------------------------------------
Reply:
"""

    try:
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,   # Slightly increased for natural replies
            max_tokens=300
        )

        reply = res.choices[0].message.content.strip()

        if not reply or len(reply) < 3:
            return "Sorry, I didn't understand that.\n\nTry: 'Spent 500 on food' or type 'summary'"

        return reply

    except Exception as e:
        print("ERROR in generate_general_reply:", e)
        return "Something went wrong. Please try again. 😊"