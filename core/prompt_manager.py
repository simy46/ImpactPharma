from typing import List, Dict
import yaml

from params import SYS_PROMPT_EN, SYS_PROMPT_FR

class PromptManager:
    def __init__(self, lang):
        self.lang = lang
        self.schema_path = "config/questions.yaml" if lang == "fr" else "config/questions.en.yaml"

        with open(self.schema_path, "r", encoding="utf-8") as f:
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
            if self.lang == "fr":
                type_hint = f" [Format attendu : {q_type}]" if q_type and q_type != "text" else ""
                if "options" in q:
                    opts = ", ".join(q["options"])
                    formatted += f'{q["id"]}. {q["question"]} (Choisir parmi : {opts}){type_hint}\n'
                else:
                    formatted += f'{q["id"]}. {q["question"]}{type_hint}\n'
            else:
                type_hint = f" [Expected format: {q_type}]" if q_type and q_type != "text" else ""
                if "options" in q:
                    opts = ", ".join(q["options"])
                    formatted += f'{q["id"]}. {q["question"]} (Choose from: {opts}){type_hint}\n'
                else:
                    formatted += f'{q["id"]}. {q["question"]}{type_hint}\n'
                    if elements:
                        for e in elements:
                            formatted += f'   - {e.strip()}\n'

        prefix = "TEXTE DE L'ARTICLE" if self.lang == "fr" else "ARTICLE TEXT"
        instruction = "Réponds uniquement au format JSON brut :  { id1: réponse, id2: réponse, ...}." if self.lang == "fr" else "Respond only in raw JSON format: { id1: answer, id2: answer, ...}."

        return f"""{prefix} :
{article_text.strip()}

QUESTIONS :
{formatted.strip()}

{instruction}
Do not use ```json or markdown formatting.
"""

    def get_system_prompt(self) -> str:
        if self.lang == "fr":
            return SYS_PROMPT_FR.strip()
        else:
            return SYS_PROMPT_EN.strip()
