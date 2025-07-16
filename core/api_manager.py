import os
import time
import tiktoken
from openai import OpenAIError, OpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

TOKENS_PER_MINUTE = 90000
TOKENS_PER_SECOND = TOKENS_PER_MINUTE / 60
SAFETY_MARGIN = 0.9

def count_tokens(prompt1, prompt2, model="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(prompt1)) + len(encoding.encode(prompt2))

def wait_for_token_quota(tokens_needed):
    wait_time = (tokens_needed / TOKENS_PER_SECOND) / SAFETY_MARGIN
    print(f"[Token Wait] Waiting {wait_time:.2f}s to respect token quota.")
    time.sleep(wait_time)

class OpenAIClient:
    def __init__(self, model="gpt-4o", temperature=0.0, max_tokens=1024):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        try:

            tokens_used = count_tokens(system_prompt, user_prompt) + self.max_tokens # dynamic token count to avoid 429/ 500 errors
            print(f"[Token Count] Estimated tokens for request: {tokens_used}")
            wait_for_token_quota(tokens_used)

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
            print(f"[OpenAI Error] {e}")
            raise
