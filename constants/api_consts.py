from openai import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

RETRYABLE_ERRORS = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

MAX_RETRY_LEVEL = 3

# Keep these conservative. Your JSON should never need more than this.
MAX_OUTPUT_TOKEN_CAP_EN = 40_000
MAX_OUTPUT_TOKEN_CAP_FR = 10_000

# More aggressive than +20%, because truncation with reasoning models can happen hard.
TOKEN_MULTIPLIERS = [1.0, 1.5, 2.2, 3.0]