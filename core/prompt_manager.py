import yaml
from typing import List, Dict
from params import SYS_PROMPT_EN, SCHEMA_PATH, SYS_PROMPT_FR

class PromptManager:
    def __init__(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.questions: List[Dict] = yaml.safe_load(f)

    def get_categories(self) -> List[str]:
        return sorted(set(q["category"] for q in self.questions))

    def get_questions_by_category(self, category: str) -> List[Dict]:
        return [q for q in self.questions if q["category"] == category]

    def build_prompt(self, article_text: str, category: str) -> str:
        questions = self.get_questions_by_category(category)

        formatted = ""
        for q in questions:
            q_type = q.get("type", "")
            elements = q.get("elements", [])
            type_hint = f" [Expected format: {q_type}]"

            if "options" in q:
                opts = ", ".join(q["options"])
                formatted += f'{q["id"]}. {q["question"]} (Choose from: {opts}){type_hint}\n'
            else:
                formatted += f'{q["id"]}. {q["question"]}{type_hint}\n'
                for e in elements:
                    formatted += f'   - {e.strip()}\n'

        prefix = "ARTICLE TEXT"
        instruction = "Respond only in raw JSON format: { Q1: answer, Q2: answer, ...}."

        return f"""{prefix} :
{article_text.strip()}

QUESTIONS :
{formatted.strip()}

{instruction}
Do not use ```json or markdown formatting.
"""

    def get_system_prompt(self) -> str:
        return SYS_PROMPT_EN.strip()
    
    def translate_prompt(self) -> str:
        return SYS_PROMPT_FR.strip()
