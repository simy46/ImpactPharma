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
MAX_TOKENS = 4500   # for long texts, interval [4000, 8000] is recommended


# ========================================
#    Reasoning effort [FOR GPT-5  ONLY]  |
# ========================================
# "low"    → faster, closer to GPT-4 style, less accurate.
# "medium" → balance of speed and quality.
# "high"   → more rigorous, fewer hallucinations, but slower and more expensive.
REASONING = {"effort": "medium"}


# ========================================
#           Text verbosity               |
# ========================================
# "low"    → shorter answers, risk of missing details.
# "medium" → concise and structured.
# "high"   → longer, more verbose answers.
TEXT = {"verbosity": "medium"}



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
TOKENS_PER_MINUTE = 450000
TOKENS_PER_SECOND = TOKENS_PER_MINUTE / 60

# Safety margin → use only 90% of the quota to avoid hitting limits.
SAFETY_MARGIN = 0.9

##################################################################################################################
################################################# SYSTEM PROMPTS #################################################
##################################################################################################################

SYS_PROMPT_FR = """
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
"""

SYS_PROMPT_EN = """
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
"""

##################################################################################################################
##################################################################################################################
##################################################################################################################
