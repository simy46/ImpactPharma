import os
import time
from typing import Optional
import tiktoken
from openai import OpenAIError, OpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from core.log_manager import LogManager
from params import (
    MODEL, MAX_TOKENS, MAX_TOKENS_FR,
    REASONING, REASONING_FR,
    TEXT, TEXT_FR,
    SAFETY_MARGIN, TOKEN_COUNTER_MODEL, TOKENS_PER_SECOND
)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

class OpenAIClient:
    def __init__(self, logger: LogManager, model=MODEL, max_tokens=MAX_TOKENS):
        self.model = model
        self.max_tokens = max_tokens
        self.logger: LogManager = logger

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
    def ask(self, system_prompt: str, user_prompt: str, tokens_used: int, lang: Optional[str] = None) -> str:
        try:
            reasoning = REASONING_FR if lang == "fr" else REASONING
            text = TEXT_FR if lang == "fr" else TEXT
            max_tokens = MAX_TOKENS_FR if lang == "fr" else self.max_tokens

            total_tokens = tokens_used + max_tokens
            self._wait_for_token_quota(total_tokens)

            response = client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                reasoning=reasoning,
                text=text,
                max_output_tokens=max_tokens,
            )

            answer = response.output_text
            if not answer:
                self.logger.write("warn", "Réponse vide, dump brut...")
                self.logger.write("raw", response.model_dump_json(indent=2))
                answer = '{"NA": "Non traité"}'
            return answer

        except OpenAIError as e:
            self.logger.write("error", f"OpenAI Error: {e}")
            raise
