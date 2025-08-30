# ------------------------------
# Model choice
# ------------------------------
# gpt-5      → best quality, deeper reasoning, slower, more expensive.
# gpt-5-mini → faster, cheaper, but less reliable.
# gpt-5-nano → very fast, almost free, but very limited.
MODEL = "gpt-5"


# ------------------------------
# Maximum output tokens
# ------------------------------
# Maximum number of tokens the model can generate for the response.
# Too low  → risk of incomplete or empty answers.
# Higher   → slower responses and higher cost (you pay for generated tokens).
MAX_TOKENS = 4500   # for long texts, 4000–8000 is recommended


# ------------------------------
# Reasoning effort [FOR GPT-5  ONLY]
# ------------------------------
# "low"    → faster, closer to GPT-4 style, less accurate.
# "medium" → balance of speed and quality.
# "high"   → more rigorous, fewer hallucinations, but slower and more expensive.
REASONING = {"effort": "medium"}


# ------------------------------
# Text verbosity
# ------------------------------
# "low"    → shorter answers, risk of missing details.
# "medium" → concise and structured.
# "high"   → longer, more verbose answers.
TEXT = {"verbosity": "medium"}



# SKIP THIS PARAM FOR NOW, NOT NEEDED FOR REASEARCH
# ------------------------------
# Token counter model
# ------------------------------
# GPT-5 is not yet supported in tiktoken, so we use gpt-4o for token counting.
TOKEN_COUNTER_MODEL = "gpt-4o"


# SKIP THIS PARAM FOR NOW, NOT NEEDED FOR REASEARCH
# ------------------------------
# Token rate limits
# ------------------------------
# Maximum tokens per minute allowed by your OpenAI tier. Changes may occur, check link below!
# information available at https://platform.openai.com/settings/organization/limits
TOKENS_PER_MINUTE = 450000
TOKENS_PER_SECOND = TOKENS_PER_MINUTE / 60

# Safety margin → use only 90% of the quota to avoid hitting limits.
SAFETY_MARGIN = 0.9

