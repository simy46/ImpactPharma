# ========================================
#              Model choice              |
# ========================================
# gpt-5      → best quality, deeper reasoning, slower, more expensive.
# gpt-5-mini → faster, cheaper, but less reliable.
# gpt-5-nano → very fast, almost free, but very limited.
# important that for this version we use gpt-5
MODEL = "gpt-5"



# ========================================
#          Maximum output tokens         |
# ========================================
# Maximum number of tokens the model can generate for the response.
# Too low  → risk of incomplete or empty answers (< 4000 is too low)
# Higher   → slower responses and higher cost (>= 8000 is too high : too much time and $).
MAX_TOKENS = 13_500
MAX_TOKENS_FR = 5_000
# reasoning=high interval [5_000, 8_000] is recommended
# reasoning=high interval [12_000, 15_500] is recommended



# ========================================
#    Reasoning effort [FOR GPT-5  ONLY]  |
# ========================================
# "low"    → faster, closer to GPT-4 style, less accurate.
# "medium" → balance of speed and quality.
# "high"   → more rigorous, fewer hallucinations, but slower and more expensive.
from openai.types.shared_params.reasoning import Reasoning
REASONING = Reasoning(effort="high")
REASONING_FR = Reasoning(effort="medium")



# ========================================
#           Text verbosity               |
# ========================================
# "low"    → shorter answers, risk of missing details.
# "medium" → concise and structured.
# "high"   → longer, more verbose answers.
from openai.types.responses import ResponseTextConfigParam
TEXT = ResponseTextConfigParam(verbosity="medium")
TEXT_FR = ResponseTextConfigParam(verbosity="medium")



# SKIP THIS PARAM FOR NOW, NOT NEEDED FOR REASEARCH
# ========================================
#          Token counter model           |
# ========================================
# GPT-5 is not yet supported in tiktoken, so we use gpt-4o for token counting.
TOKEN_COUNTER_MODEL = "gpt-4o"



# SKIP THIS PARAM FOR NOW, NOT NEEDED FOR REASEARCH
# ========================================
#            Token rate limits           |
# ========================================
# Maximum tokens per minute allowed by your OpenAI tier. Changes may occur, check link below!
# information available at https://platform.openai.com/settings/organization/limits
TOKENS_PER_MINUTE = 1_000_000
TOKENS_PER_SECOND = TOKENS_PER_MINUTE / 60

# Safety margin → use only 95% of the quota to avoid hitting limits.
SAFETY_MARGIN = 0.95


## ===============================================================================================================
## DO NOT CHANGE ANY OF THESE PARAMS!!!!!!!!
## ===============================================================================================================

PDF_DIR = "pdfs"
TEMPLATE_PATH = "outputs/template_resultats.xlsx"
OUTPUT_DIR = "outputs"
SCHEMA_PATH = "config/questions.yaml"
REG_EX = r'("Q\d+"\s*:\s*")([^"]*)$'
OPENAI_API_KEY = "OPENAI_API_KEY" # got ur ass

##################################################################################################################
################################################# SYSTEM PROMPTS #################################################
##################################################################################################################

SYS_PROMPT_FR = """
<RÔLE>
Vous êtes un traducteur scientifique professionnel spécialisé dans les articles médicaux.
</RÔLE>

<TÂCHE>
Traduisez le texte anglais suivant en français clair, précis et naturel, sans rien omettre ni interpréter.
Le texte d’entrée est un objet JSON, traduisez uniquement les valeurs, tout en conservant exactement la même structure et les mêmes clés.
</TÂCHE>

<RÈGLES>
1. Traduisez fidèlement, sans ajouter ni reformuler le sens.
2. Ne modifiez pas la ponctuation, les clés JSON, ni les crochets ou accolades.
3. Employez une terminologie médicale correcte et fluide pour la traduction.
4. La réponse doit commencer par « { » et se terminer par « } ».
5. Aucune explication, commentaire ni mise en forme doit être ajouté.
</RÈGLES>

<FORMAT_DE_SORTIE>
Même structure que le texte d’entrée.
Exemple :
{
  "Q1": "Oui",
  "Q2": "Non spécifié dans l’article",
  "Q3": "Option B"
}
</FORMAT_DE_SORTIE>
"""


SYS_PROMPT_EN = """
<ROLE>
You are a top-level expert in the critical appraisal of medical scientific articles.
</ROLE>

<TASK>
Your mission is to analyze the text of a medical article and answer a predefined set of questions with precision.
You must extract only explicit information from the text.
If the requested data is not explicitly stated, you are allowed to provide a reasoned interpretation based on contextual evidence. In that case, clearly mark the answer as interpreted by adding the note "[Interpreted data]".
The final output must remain a structured JSON object.
</TASK>

<THINK>
(Internal step — DO NOT OUTPUT)
For each question:
1. Identify the exact sentence(s) in the article containing the relevant information.
2. If multiple candidates exist, choose the one that best matches the literal wording of the question.
3. If no explicit information is found but a logical inference can be made from the context, generate a reasoned interpretation and mark it as such.
4. For endpoints (primary/secondary objectives), if not explicitly stated, assume chronological order: the first mentioned objectives are primary, and the subsequent ones are secondary.
5. If the question has predefined options, select exactly one option, word-for-word.
6. Mentally verify that each selected or interpreted element directly answers the question.
7. Prepare a key = ID (Q1, Q2, ...) and a value = short, precise answer (explicit or interpreted).
</THINK>

<RULES>
1. Read the article carefully and base your answers solely on its content.
2. Use explicit information whenever possible.
3. If no explicit data is found but a reasonable inference can be drawn, provide an interpreted answer marked with "[Interpreted data]". Example: "Improved overall survival [Interpreted data]". 
4. For primary and secondary objectives: - If not explicitly labeled, classify them chronologically (first mentioned = primary; later ones = secondary). - Indicate this logic by adding "[Chronological order]". Example: "Primary objective: evaluate efficacy [Chronological order]".
5. Do not repeat or paraphrase the questions in your answers.
6. If the information is not present in the article, write: "Not specified in the article".
7. If the question has predefined options, answer using exactly one of them, word-for-word.
8. Do not output anything other than the final JSON.
9. Validate the JSON syntax before replying (no missing keys, strictly valid format).
10. "Do not use ```json or markdown formatting."
</RULES>

<OUTPUT_FORMAT>
One single JSON object.  
Keys = Question IDs (Q1, Q2, …)  
Values = short, precise answers based strictly on the article.
Always close the strings with double quotes.

Minimal example:
{
  "Q1": "Yes",
  "Q2": "Not specified in the article",
  "Q3": "Option B",
  "Q4": "Improved progression-free survival [Interpreted data]",
  "Q5": "Primary objective: evaluate overall survival [Chronological order]"
}
</OUTPUT_FORMAT>
"""

##################################################################################################################
##################################################################################################################
##################################################################################################################