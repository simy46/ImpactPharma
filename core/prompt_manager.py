from typing import List, Dict
import yaml

class PromptManager:
    def __init__(self, schema_path="config/questions.yaml"):
        with open(schema_path, "r", encoding="utf-8") as f:
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
            type_hint = f" [Type attendu : {q_type}]" if q_type and q_type != "text" else ""
            
            if "options" in q:
                opts = ", ".join(q["options"])
                formatted += f'{q["id"]}. {q["question"]} (Choisir parmi : {opts}){type_hint}\n'
            else:
                formatted += f'{q["id"]}. {q["question"]}{type_hint}\n'

        return f"""TEXTE DE L'ARTICLE :
{article_text.strip()}

QUESTIONS :
{formatted.strip()}

Réponds uniquement au format JSON brut :  {{ id: réponse }}. 
N'utilise aucune balise de type ```json ou markdown.
"""

    @staticmethod
    def get_system_prompt() -> str:
        return """
Tu es un expert en lecture critique d’articles scientifiques médicaux.

Ta tâche :
- Lire le texte fourni
- Répondre uniquement aux questions posées
- Ne pas extrapoler, ne faire aucune supposition

INSTRUCTIONS :
- Format de réponse : JSON valide
- Clés = ID des questions (ex: Q1, Q2, ...)
- Valeurs = réponses courtes, précises, basées uniquement sur le texte
- Commence directement avec l'information pertinente, sans répéter ou reformuler la question.
- Si l'information est absente : "Non précisé dans l'article"
- Si une question a des choix (options), tu dois répondre mot pour mot avec l'une des options proposées
""".strip()
