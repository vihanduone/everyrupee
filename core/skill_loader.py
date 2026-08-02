import os

BASE_PATH = "skills"


def load_skill(skill_name: str) -> str:
    path = os.path.join(BASE_PATH, skill_name, "skill.md")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()