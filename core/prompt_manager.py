from typing import Dict, List

import yaml

from constants.params import SYS_PROMPT_EN, SYS_PROMPT_FR
from constants.script_consts import SCHEMA_PATH


class PromptManager:
    def __init__(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            self.questions: List[Dict] = yaml.safe_load(file)

        if not isinstance(self.questions, list):
            raise ValueError("Schema YAML must contain a list of questions.")

    def get_categories(self) -> List[str]:
        categories = []

        for question in self.questions:
            category = question["category"]

            if category not in categories:
                categories.append(category)

        return categories

    def get_questions_by_category(self, category: str) -> List[Dict]:
        return [
            question
            for question in self.questions
            if question.get("category") == category
        ]

    def build_prompt(
        self,
        article_text: str,
        category: str,
        previous_answers: dict | None = None,
    ) -> str:
        questions = self.get_questions_by_category(category)
        lines = []

        for question in questions:
            qid = question["id"]
            qtext = question["question"]
            qtype = question.get("type", "").strip()
            qopts = question.get("options", [])
            qelems = question.get("elements", [])

            type_hint = f" [Expected format: {qtype}]" if qtype else ""
            line = f"{qid}. {qtext}{type_hint}"

            if qopts:
                opts_str = ", ".join(qopts)
                line += f" (Choose from: {opts_str})"

            lines.append(line)

            for element in qelems:
                lines.append(f"   - {element.strip()}")

        context_str = ""

        if previous_answers:
            qid, answer = next(iter(previous_answers.items()))
            context_str = f"Context from previous answers:\n{qid}: {answer}\n\n"

        formatted_questions = "\n".join(lines)

        return (
            f"ARTICLE TEXT:\n{article_text.strip()}\n\n"
            f"{context_str}"
            f"QUESTIONS:\n{formatted_questions}\n\n"
            "Respond only in raw JSON format: { Q1: answer, Q2: answer, ... }.\n"
        )

    def get_system_prompt(self) -> str:
        return SYS_PROMPT_EN.strip()

    def translate_prompt(self) -> str:
        return SYS_PROMPT_FR.strip()