import json
import os
import random
import time
from typing import Optional

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from openai.types.shared_params.reasoning import Reasoning

from constants.api_consts import (
    MAX_OUTPUT_TOKEN_CAP_EN,
    MAX_OUTPUT_TOKEN_CAP_FR,
    MAX_RETRY_LEVEL,
    RETRYABLE_ERRORS,
    TOKEN_MULTIPLIERS,
)
from constants.general_consts import FR
from constants.params import (
    MODEL,
    MAX_TOKENS,
    MAX_TOKENS_FR,
    REASONING,
    REASONING_FR,
    TEXT,
    TEXT_FR,
    SAFETY_MARGIN,
    TOKEN_COUNTER_MODEL,
    TOKENS_PER_SECOND,
)
from constants.script_consts import OPENAI_API_KEY
from core.log_manager import LogManager


load_dotenv()


class OpenAIQuotaExceeded(RuntimeError):
    pass


class OpenAIClient:
    def __init__(self, logger: LogManager):
        self.logger = logger

        self.api_key = os.getenv(OPENAI_API_KEY)

        if not self.api_key:
            raise RuntimeError(
                f"Missing OpenAI API key. Check env variable: {OPENAI_API_KEY}"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=180,
            max_retries=0,
        )

    def _count_tokens(
        self,
        prompt1: str,
        prompt2: str,
        model: str = TOKEN_COUNTER_MODEL,
    ) -> int:
        encoding = tiktoken.encoding_for_model(model)
        count = len(encoding.encode(prompt1)) + len(encoding.encode(prompt2))

        self.logger.write("token", f"Estimated input tokens: {count}")

        return count

    def _wait_for_token_quota(self, tokens_needed: int) -> None:
        if tokens_needed <= 0:
            return

        wait_time = (tokens_needed / TOKENS_PER_SECOND) / SAFETY_MARGIN

        if wait_time <= 0:
            return

        self.logger.write(
            "wait",
            f"Waiting {wait_time:.2f}s to respect token quota.",
        )
        time.sleep(wait_time)

    def _sleep_before_retry(self, retry_level: int) -> None:
        wait_time = min(60, (2**retry_level) + random.uniform(0, 1.5))

        self.logger.write("wait", f"Retrying after {wait_time:.2f}s.")
        time.sleep(wait_time)

    def _get_max_tokens(self, lang: Optional[str], retry_level: int) -> int:
        base = MAX_TOKENS_FR if lang == FR else MAX_TOKENS
        cap = MAX_OUTPUT_TOKEN_CAP_FR if lang == FR else MAX_OUTPUT_TOKEN_CAP_EN

        multiplier = TOKEN_MULTIPLIERS[
            min(retry_level, len(TOKEN_MULTIPLIERS) - 1)
        ]

        return min(int(base * multiplier), cap)

    def _get_reasoning(self, lang: Optional[str], retry_level: int):
        if lang == FR:
            return REASONING_FR

        if retry_level == 0:
            return REASONING

        return Reasoning(effort="high")

    def _get_text_config(self, lang: Optional[str]):
        return TEXT_FR if lang == FR else TEXT

    def _get_incomplete_reason(self, response) -> Optional[str]:
        details = getattr(response, "incomplete_details", None)

        if not details:
            return None

        if isinstance(details, dict):
            return details.get("reason")

        return getattr(details, "reason", None)

    def _log_usage(self, response) -> None:
        usage = getattr(response, "usage", None)

        if not usage:
            return

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        reasoning_tokens = None
        output_details = getattr(usage, "output_tokens_details", None)

        if output_details:
            if isinstance(output_details, dict):
                reasoning_tokens = output_details.get("reasoning_tokens")
            else:
                reasoning_tokens = getattr(output_details, "reasoning_tokens", None)

        self.logger.write(
            "token",
            (
                f"Usage | input={input_tokens}, output={output_tokens}, "
                f"reasoning={reasoning_tokens}, total={total_tokens}"
            ),
        )

    def _is_valid_json(self, answer: str) -> bool:
        try:
            json.loads(answer)
            return True

        except Exception:
            return False

    def _is_insufficient_quota_error(self, error: Exception) -> bool:
        body = getattr(error, "body", None)

        if isinstance(body, dict):
            error_data = body.get("error", {})

            if isinstance(error_data, dict):
                return error_data.get("code") == "insufficient_quota"

        return "insufficient_quota" in str(error)

    def _build_retry_instruction(self, retry_level: int) -> str:
        if retry_level == 0:
            return ""

        return (
            "\n\nIMPORTANT RETRY INSTRUCTION:\n"
            "The previous attempt was incomplete, empty, or invalid. "
            "Return exactly one complete valid JSON object. "
            "Do not include markdown. Do not include explanations."
        )

    def ask(
        self,
        system_prompt: str,
        user_prompt: str,
        tokens_used: int,
        lang: Optional[str] = None,
        expect_json: bool = True,
    ) -> str:
        last_error = None

        for retry_level in range(MAX_RETRY_LEVEL + 1):
            try:
                reasoning = self._get_reasoning(lang, retry_level)
                text = self._get_text_config(lang)
                max_tokens = self._get_max_tokens(lang, retry_level)

                self.logger.write(
                    "info",
                    (
                        f"OpenAI call | model={MODEL}, lang={lang or 'en'}, "
                        f"retry_level={retry_level}, max_output_tokens={max_tokens}, "
                        f"reasoning={reasoning}"
                    ),
                )

                total_tokens = tokens_used + max_tokens
                self._wait_for_token_quota(total_tokens)

                retry_instruction = self._build_retry_instruction(retry_level)

                response = self.client.responses.create(
                    model=MODEL,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": user_prompt + retry_instruction,
                        },
                    ],
                    reasoning=reasoning,
                    text=text,
                    max_output_tokens=max_tokens,
                )

                self._log_usage(response)

                status = getattr(response, "status", None)
                incomplete_reason = self._get_incomplete_reason(response)

                if status == "incomplete" or incomplete_reason:
                    self.logger.write(
                        "warn",
                        (
                            f"Incomplete response | status={status}, "
                            f"reason={incomplete_reason}"
                        ),
                    )

                    if incomplete_reason == "content_filter":
                        self.logger.write("error", "Response blocked by content filter.")
                        return '{"NA": "Non traité - content filter"}'

                    if retry_level < MAX_RETRY_LEVEL:
                        self._sleep_before_retry(retry_level)
                        continue

                    self.logger.write("error", "Response still incomplete after retries.")
                    return '{"NA": "Non traité - réponse tronquée"}'

                answer = getattr(response, "output_text", None)

                if not answer or not answer.strip():
                    self.logger.write("warn", "Empty response output_text.")

                    if retry_level < MAX_RETRY_LEVEL:
                        self._sleep_before_retry(retry_level)
                        continue

                    self.logger.write("raw", response.model_dump_json(indent=2))
                    return '{"NA": "Non traité - réponse vide"}'

                answer = answer.strip()

                if expect_json and not self._is_valid_json(answer):
                    self.logger.write("warn", "Invalid JSON returned by model.")
                    self.logger.write("raw", answer[:3000])

                    if retry_level < MAX_RETRY_LEVEL:
                        self._sleep_before_retry(retry_level)
                        continue

                    return '{"NA": "Non traité - JSON invalide"}'

                return answer

            except RETRYABLE_ERRORS as e:
                last_error = e

                if self._is_insufficient_quota_error(e):
                    raise OpenAIQuotaExceeded(
                        "OpenAI quota exhausted. Check billing, credits, or project usage limits."
                    ) from e

                self.logger.write(
                    "warn",
                    f"Retryable OpenAI error at retry_level={retry_level}: {e}",
                )

                if retry_level < MAX_RETRY_LEVEL:
                    self._sleep_before_retry(retry_level)
                    continue

                self.logger.write("error", f"OpenAI retryable error after retries: {e}")
                raise

            except OpenAIError as e:
                if self._is_insufficient_quota_error(e):
                    raise OpenAIQuotaExceeded(
                        "OpenAI quota exhausted. Check billing, credits, or project usage limits."
                    ) from e

                self.logger.write("error", f"Non-retryable OpenAI error: {e}")
                raise

            except Exception as e:
                self.logger.write("error", f"Unexpected error: {e}")
                raise

        self.logger.write("error", f"Failed after retries. Last error: {last_error}")
        return '{"NA": "Non traité"}'