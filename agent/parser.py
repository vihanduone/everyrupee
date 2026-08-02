import json
import re
import difflib
from config import client, MODEL_NAME
import logging
from core.skill_loader import load_skill

logger = logging.getLogger("everyrupee.parser")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTENTS = {
    "add_expense",
    "adding_income",
    "get_summary",
    "delete_last",
    "send_report",
    "save_feedback",
    "greeting",
    "unknown",
}

INCOME_KEYWORDS = [
    "salary", "income", "received", "earned", "bonus", "allowance", "refund",
    "sold", "payment received", "commission", "freelance", "interest", "deposit", "cashback",
]

EXPENSE_KEYWORDS = [
    "spent", "paid", "bought", "expense", "cost", "purchase", "ordered",
]

FEEDBACK_KEYWORDS = [
    "good", "great", "excellent", "awesome", "love", "bad", "terrible",
    "slow", "bug", "issue", "problem", "hate",
]

GREETING_KEYWORDS = [
    "hello", "hi", "hey", "good morning", "good evening",
]

SUMMARY_KEYWORDS = [
    "summary", "balance", "monthly", "expenses", "income summary", "report",
]

DELETE_KEYWORDS = [
    "undo", "delete last", "remove last", "delete", "remove previous", "cancel last"
]

CATEGORY_MAP = {
    "Food": ["food", "restaurant", "lunch", "dinner", "breakfast", "snack", "coffee", "tea", "pizza", "burger", "kfc", "mcdonald", "swiggy", "zomato", "cofee", "cafe", "starbucks"],
    "Transport": ["fuel", "petrol", "diesel", "bus", "train", "uber", "ola", "pickme", "taxi", "rickshaw", "auto"],
    "Shopping": ["shopping", "shirt", "clothes", "shoes", "amazon", "flipkart", "myntra"],
    "Bills": ["wifi", "electricity", "water", "gas", "internet", "mobile", "recharge"],
    "Entertainment": ["movie", "netflix", "spotify", "games", "ott"],
    "Health": ["doctor", "medicine", "hospital", "pharmacy"],
    "Gym": ["gym", "fitness", "protein"],
    "Education": ["course", "udemy", "coursera", "book", "class", "tuition"],
    "Rent": ["rent", "house"],
    "Misc": ["gift", "donation", "other", "general", "misc", "wash", "domain", "needs"]
}

# ---------------------------------------------------------------------------
# Amount & Helpers
# ---------------------------------------------------------------------------

_AMOUNT_PATTERNS = [
    re.compile(r"(?:rs\.?|inr|rupees?)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"(?:\$|usd)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"([\d,]+(?:\.\d+)?)\s*dollars?\b", re.IGNORECASE),
    re.compile(r"dollars?\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"([\d,]+(?:\.\d+)?)\s*/-"),
    re.compile(r"(?:spent|paid|bought|cost|purchase[d]?|ordered)\D{0,15}?([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"\b([\d,]+(?:\.\d+)?)\b"),
]


def extract_amount(text: str):
    if not text:
        return None
    for pattern in _AMOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except:
                continue
    return None


def _contains_any(text: str, keywords: list) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(re.search(r"\b" + re.escape(kw) + r"\b", lowered) for kw in keywords)


def fuzzy_match(text: str, keywords: list, threshold: float = 0.65) -> bool:
    lowered = text.lower()
    for kw in keywords:
        if kw in lowered or lowered in kw:
            return True
        if difflib.SequenceMatcher(None, lowered, kw).ratio() >= threshold:
            return True
    return False


def detect_category_improved(text: str) -> str:
    if not text:
        return "Misc"
    lowered = text.lower().replace("_", " ")
    for category, keywords in CATEGORY_MAP.items():
        if fuzzy_match(lowered, keywords):
            return category
    return "Misc"


def detect_income(text: str) -> bool:
    return _contains_any(text, INCOME_KEYWORDS)


def detect_expense(text: str) -> bool:
    if not text:
        return False
    if re.match(r"^\s*\d", text):
        return True
    return _contains_any(text, EXPENSE_KEYWORDS)


def detect_feedback(text: str) -> bool:
    return _contains_any(text, FEEDBACK_KEYWORDS)


def detect_summary(text: str) -> bool:
    return _contains_any(text, SUMMARY_KEYWORDS)


def detect_delete(text: str) -> bool:
    """Improved delete detection"""
    if not text:
        return False
    lowered = text.lower().strip()
    for kw in DELETE_KEYWORDS:
        if kw in lowered or lowered == kw:
            return True
    return False


def detect_greeting(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower().strip()
    return any(lowered.startswith(kw) or lowered == kw for kw in GREETING_KEYWORDS)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# JSON Helpers
# ---------------------------------------------------------------------------

def clean_json(raw_text: str) -> str:
    if not raw_text:
        return raw_text
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return text.strip()


def safe_json_load(raw_text: str):
    if not raw_text:
        return None
    try:
        return json.loads(raw_text)
    except:
        return None


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def _build_response(intent: str, amount=None, category=None, raw=None,
                    needs_followup=False, question=None, missing=None):
    if intent not in INTENTS:
        intent = "unknown"
    return {
        "intent": intent,
        "entity": {"amount": amount, "category": category, "raw": raw},
        "needs_followup": needs_followup,
        "question": question,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# Rule-based Parser
# ---------------------------------------------------------------------------

def rule_parse(user_input: str, history: list = None):
    text = normalize(user_input)
    if not text:
        return None

    # High priority commands
    if detect_greeting(text):
        return _build_response(intent="greeting", raw=text)

    if detect_feedback(text):
        return _build_response(intent="save_feedback", raw=text)

    # UNDO - Very high priority
    if detect_delete(text):
        print(f"DEBUG: Delete/Undo command detected: {text}")
        return _build_response(intent="delete_last", raw=text)

    if detect_summary(text):
        intent = "send_report" if "report" in text.lower() else "get_summary"
        return _build_response(intent=intent, raw=text)

    # Expense / Income
    is_income = detect_income(text)
    is_expense = detect_expense(text)

    if not is_income and not is_expense:
        return None

    amount = extract_amount(text)
    category = detect_category_improved(text)

    intent = "adding_income" if is_income and not is_expense else "add_expense"

    # Accept strong category matches
    if category != "Misc" and amount is not None:
        return _build_response(intent=intent, amount=amount, category=category, raw=text)

    # Fallback to AI for ambiguous cases
    return None


# ---------------------------------------------------------------------------
# AI Fallback
# ---------------------------------------------------------------------------

def fallback(user_input: str, history: list = None) -> dict:
    text = normalize(user_input)

    try:
        skill_prompt = load_skill("intent_parser")
    except Exception:
        logger.exception("Failed to load intent_parser skill")
        skill_prompt = ""

    messages = [{"role": "system", "content": skill_prompt}]
    if history:
        for turn in history:
            if isinstance(turn, dict) and "role" in turn:
                messages.append(turn)

    messages.append({"role": "user", "content": text})

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
        raw_content = completion.choices[0].message.content
    except Exception as e:
        logger.exception("Groq API call failed")
        return _build_response(
            intent="unknown",
            raw=text,
            needs_followup=True,
            question="Sorry, I couldn't understand that. Could you rephrase?"
        )

    cleaned = clean_json(raw_content)
    parsed = safe_json_load(cleaned)

    if parsed is None:
        return _build_response(
            intent="add_expense",
            raw=text,
            needs_followup=True,
            question="I couldn't detect a valid category. Please enter amount with one of these: Food, Transport, Shopping, Bills, Education, Rent, Misc, etc."
        )

    return _coerce_to_schema(parsed, fallback_raw=text)


def _coerce_to_schema(parsed: dict, fallback_raw: str = None) -> dict:
    intent = parsed.get("intent") or "unknown"
    if intent not in INTENTS:
        intent = "unknown"

    entity = parsed.get("entity") or {}
    amount = entity.get("amount")
    if amount is not None:
        try:
            amount = float(amount)
        except:
            amount = None

    category = entity.get("category")
    raw = entity.get("raw") or fallback_raw

    needs_followup = bool(parsed.get("needs_followup", False))
    question = parsed.get("question")
    missing = parsed.get("missing")
    if not isinstance(missing, list):
        missing = None

    return _build_response(intent, amount, category, raw, needs_followup, question, missing)


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def ai_parse_user_input(user_input: str, history: list = None) -> dict:
    text = normalize(user_input)
    if not text:
        return _build_response(intent="unknown", raw=user_input, needs_followup=True,
                             question="I didn't receive any message.")

    # Rule-based first
    result = rule_parse(text, history)
    if result is not None:
        return result

    # AI fallback for complex cases
    return fallback(text, history)