from typing import Optional

from core.api_manager import OpenAIClient
from core.log_manager import LogManager
from retrieval.models import TokenUsage
from retrieval.recovered_stats import RecoveredStats


class RecoveryOpenAIClient(OpenAIClient):
    def __init__(self, logger: LogManager, recovered_stats: RecoveredStats):
        super().__init__(logger=logger)
        self.recovered_stats = recovered_stats
        self._current_article_name: Optional[str] = None
        self._current_category: Optional[str] = None
        self._current_lang: Optional[str] = None

    def set_call_context(
        self,
        article_name: Optional[str],
        category: Optional[str],
        lang: Optional[str],
    ) -> None:
        self._current_article_name = article_name
        self._current_category = category
        self._current_lang = lang

    def _log_usage(self, response) -> None:
        super()._log_usage(response)

        usage = getattr(response, "usage", None)

        if not usage:
            return

        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", 0) or 0

        reasoning_tokens = 0
        output_details = getattr(usage, "output_tokens_details", None)

        if output_details:
            if isinstance(output_details, dict):
                reasoning_tokens = output_details.get("reasoning_tokens") or 0
            else:
                reasoning_tokens = getattr(output_details, "reasoning_tokens", 0) or 0

        self.recovered_stats.add_new_usage(
            TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=total_tokens,
                article_name=self._current_article_name,
                category=self._current_category,
                lang=self._current_lang,
            )
        )
