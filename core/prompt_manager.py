import yaml
from typing import List, Dict
from constants.params import SYS_PROMPT_EN, SYS_PROMPT_FR
from constants.script_consts import SCHEMA_PATH

class PromptManager:
    def __init__(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.questions: List[Dict] = yaml.safe_load(f)

    def get_categories(self) -> List[str]:
        return sorted(set(q["category"] for q in self.questions))

    def get_questions_by_category(self, category: str) -> List[Dict]:
        return [q for q in self.questions if q["category"] == category]

    def build_prompt(self, article_text: str, category: str, previous_answers: dict | None = None) -> str:
        questions = self.get_questions_by_category(category)
        lines = []

        for q in questions:
            qid = q["id"]
            qtext = q["question"]
            qtype = q.get("type", "").strip()
            qopts = q.get("options", [])
            qelems = q.get("elements", [])
            espec = q.get("extra_specification", "")

            type_hint = f" [Expected format: {qtype}]" if qtype else ""
            line = f"{qid}. {qtext}{type_hint}"

            if qopts:
                opts_str = ", ".join(qopts)
                line += f" (Choose from: {opts_str})"

            lines.append(line)

            for e in qelems:
                lines.append(f"   - {e.strip()}")

            if espec:
                lines.append(f"   (Note: {espec.strip()})")

        context_str = ""
        if previous_answers:
            qid, answer = next(iter(previous_answers.items()))
            context_str = f"Context from previous answers:\n {qid}: {answer}\n\n"

        formatted_questions = "\n".join(lines)
        prefix = "ARTICLE TEXT"
        instruction = "Respond only in raw JSON format: { Q1: answer, Q2: answer, ... }."

        return (
            f"{prefix}:\n{article_text.strip()}\n\n"
            f"{context_str}"
            f"QUESTIONS:\n{formatted_questions}\n\n"
            f"{instruction}\n"
        )


    def get_system_prompt(self) -> str:
        return SYS_PROMPT_EN.strip()
    
    def translate_prompt(self) -> str:
        return SYS_PROMPT_FR.strip()
