import json

def load_db():
    try:
        with open("expenses.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_db(db):
    with open("expenses.json", "w") as f:
        json.dump(db, f, indent=2)
