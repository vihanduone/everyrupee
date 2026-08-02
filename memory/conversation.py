conversation_memory = {}

MAX_HISTORY = 20

def update_memory(user_id, user_input, reply):

    if user_id not in conversation_memory:
        conversation_memory[user_id] = {"history": [], "pending": None}

    history = conversation_memory[user_id]["history"]

    history.append({
        "user": user_input,
        "bot": reply
    })

    # 🔥 keep only last 20
    conversation_memory[user_id]["history"] = history[-MAX_HISTORY:]