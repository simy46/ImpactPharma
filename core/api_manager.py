import os
import time
from typing import Optional
import tiktoken
from openai import OpenAIError, OpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from core.log_manager import LogManager
from constants.params import (
    MODEL, MAX_TOKENS, MAX_TOKENS_FR,
    REASONING, REASONING_FR,
    TEXT, TEXT_FR,
    SAFETY_MARGIN, TOKEN_COUNTER_MODEL, TOKENS_PER_SECOND
)

from constants.script_consts import OPENAI_API_KEY

load_dotenv()
api_key = os.getenv(OPENAI_API_KEY)
client = OpenAI(api_key=api_key)

class OpenAIClient:
    def __init__(self, logger: LogManager):
        self.logger = logger

    def _count_tokens(self, prompt1, prompt2, model=TOKEN_COUNTER_MODEL) -> int:
        encoding = tiktoken.encoding_for_model(model)
        count = len(encoding.encode(prompt1)) + len(encoding.encode(prompt2))
        self.logger.write("token", f"Estimated tokens for request: {count}")
        return count

    def _wait_for_token_quota(self, tokens_needed) -> None:
        wait_time = (tokens_needed / TOKENS_PER_SECOND) / SAFETY_MARGIN
        self.logger.write("wait", f"Waiting {wait_time:.2f}s to respect token quota.")
        time.sleep(wait_time)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def ask(self, system_prompt: str, user_prompt: str, tokens_used: int,
            lang: Optional[str] = None, retry_level: int = 0) -> str:

        try:
            reasoning = REASONING_FR if lang == "fr" else REASONING
            text = TEXT_FR if lang == "fr" else TEXT
            base_max_tokens = MAX_TOKENS_FR if lang == "fr" else MAX_TOKENS

            # augmentation progressive → max +50%
            max_tokens = int(base_max_tokens * (1 + 0.2 * retry_level))
            # max_tokens = min(max_tokens, 15000) # should i?

            self.logger.write("info", f"Using max_tokens={max_tokens} (retry_level={retry_level})")

            total_tokens = tokens_used + max_tokens
            self._wait_for_token_quota(total_tokens)

            response = client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                reasoning=reasoning,
                text=text,
                max_output_tokens=max_tokens,
            )

            if hasattr(response, "incomplete_details") and response.incomplete_details:
                details = response.incomplete_details
                reason = getattr(details, "reason", None)

                if reason == "max_output_tokens":
                    if retry_level < 3:
                        self.logger.write("warn", f"Réponse tronquée → relance avec +20% tokens")
                        return self.ask(system_prompt, user_prompt, tokens_used,
                                        lang=lang, retry_level=retry_level + 1)
                    else:
                        self.logger.write("error", "Réponse encore tronquée après 3 tentatives.")
                        return '{"NA": "Non traité"}'

            answer = response.output_text
            if not answer:
                self.logger.write("warn", "Réponse vide ! Dump brut…")
                self.logger.write("raw", response.model_dump_json(indent=2))
                return '{"NA": "Non traité"}'

            return answer

        except OpenAIError as e:
            self.logger.write("error", f"OpenAI Error: {e}")
            raise
