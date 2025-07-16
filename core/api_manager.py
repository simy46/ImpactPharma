import os
import time
import tiktoken
from openai import OpenAIError, OpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from core.log_manager import LogManager

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

TOKENS_PER_MINUTE = 90000
TOKENS_PER_SECOND = TOKENS_PER_MINUTE / 60
SAFETY_MARGIN = 0.9


class OpenAIClient:
    def __init__(self, logger : LogManager, model="gpt-4o", temperature=0.0, max_tokens=1024):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger : LogManager = logger

    def _count_tokens(self, prompt1, prompt2, model="gpt-4o"):
        encoding = tiktoken.encoding_for_model(model)
        count = len(encoding.encode(prompt1)) + len(encoding.encode(prompt2))
        self.logger.write("token", f"Estimated tokens for request: {count}")
        return count

    def _wait_for_token_quota(self, tokens_needed):
        wait_time = (tokens_needed / TOKENS_PER_SECOND) / SAFETY_MARGIN
        self.logger.write("wait", f"Waiting {wait_time:.2f}s to respect token quota.")
        time.sleep(wait_time)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        try:

            tokens_used = self._count_tokens(system_prompt, user_prompt) + self.max_tokens # token count to avoid 429/ 500 errors
            self._wait_for_token_quota(tokens_used) # dynamic wait based on token count

            response = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content or ""

        except OpenAIError as e:
            self.logger.write("error", f"OpenAI Error: {e}")
            raise
