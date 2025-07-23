from typing import List, Dict
import yaml

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
                type_hint = f" [Type attendu : {q_type}]" if q_type and q_type != "text" else ""
                if "options" in q:
                    opts = ", ".join(q["options"])
                    formatted += f'{q["id"]}. {q["question"]} (Choisir parmi : {opts}){type_hint}\n'
                else:
                    formatted += f'{q["id"]}. {q["question"]}{type_hint}\n'
            else:
                type_hint = f" [Expected type: {q_type}]" if q_type and q_type != "text" else ""
                if "options" in q:
                    opts = ", ".join(q["options"])
                    formatted += f'{q["id"]}. {q["question"]} (Choose from: {opts}){type_hint}\n'
                else:
                    formatted += f'{q["id"]}. {q["question"]}{type_hint}\n'
                    if elements:
                        print(f"Elements for question {q['id']}: {elements}")
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
            return """
Tu es un expert en lecture critique d’articles scientifiques médicaux.

Ta tâche :
- Lire le texte fourni
- Répondre uniquement aux questions posées, dans la langue requise
- Ne pas extrapoler, ne faire aucune supposition

INSTRUCTIONS :
- Format de réponse : un seul JSON valide
- Clés = ID des questions (ex: Q1, Q2, ...)
- Valeurs = réponses courtes, précises, basées uniquement sur le texte
- Commence directement avec l'information pertinente, sans répéter ou reformuler la question.
- Si l'information est absente : "Non précisé dans l'article"
- Si une question a des choix (options), tu dois répondre mot pour mot avec l'une des options proposées
""".strip()
        else:
            return """
You are an expert in critical appraisal of medical scientific articles.

Your task:
- Read the provided text
- Only answer the questions asked
- Do not extrapolate or make any assumptions

INSTRUCTIONS:
- Response format: only one Valid JSON
- Keys = Question IDs (e.g., Q1, Q2, ...) 
- Values = Short, precise answers based only on the text
- Start directly with the answer, do not repeat or rephrase the question
- If the information is missing: "Not specified in the article"
- If a question has predefined options, you must reply using exactly one of the given options (word-for-word)
""".strip()
