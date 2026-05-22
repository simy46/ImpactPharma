from datetime import datetime
from decimal import Decimal
from typing import Optional

from constants.params import (
    MODEL,
    MAX_TOKENS,
    MAX_TOKENS_FR,
    REASONING,
    REASONING_FR,
    SYS_PROMPT_EN,
    TEXT,
    TEXT_FR,
    SAFETY_MARGIN,
    TOKENS_PER_MINUTE,
)


class StatsManager:
    def __init__(self, model: str = MODEL, token_limit: int = TOKENS_PER_MINUTE):
        self.model = model
        self.token_limit = token_limit

        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        self.article_count = 0

        # Used only for throughput/rate-limit reporting.
        # It is NOT used for cost.
        self.counted_tokens_for_rate_limit = 0

        # Official OpenAI cost snapshots.
        self.openai_cost_before: Optional[Decimal] = None
        self.openai_cost_after: Optional[Decimal] = None

    def start(self):
        self.start_time = datetime.now()

    def stop(self):
        self.end_time = datetime.now()

    def add_article(self):
        self.article_count += 1

    def add_tokens(self, n: int):
        self.counted_tokens_for_rate_limit += n

    def set_openai_cost_before(self, value: Optional[Decimal]):
        self.openai_cost_before = value

    def set_openai_cost_after(self, value: Optional[Decimal]):
        self.openai_cost_after = value

    def total_cost(self) -> Optional[Decimal]:
        if self.openai_cost_before is None or self.openai_cost_after is None:
            return None

        return self.openai_cost_after - self.openai_cost_before

    def cost_per_article(self) -> Optional[Decimal]:
        total = self.total_cost()

        if total is None or self.article_count == 0:
            return None

        return total / Decimal(self.article_count)

    def cost_per_article_lang(self) -> Optional[Decimal]:
        per_article = self.cost_per_article()

        if per_article is None:
            return None

        return per_article / Decimal("2")

    @staticmethod
    def _money(value: Optional[Decimal]) -> str:
        if value is None:
            return "Unavailable"

        return f"${value:.6f}"

    def summary_dict(self) -> dict:
        duration_min = (
            (self.end_time - self.start_time).total_seconds() / 60
            if self.start_time and self.end_time
            else 0
        )

        avg_tokens = (
            self.counted_tokens_for_rate_limit / self.article_count
            if self.article_count
            else 0
        )

        tpm = (
            self.counted_tokens_for_rate_limit / duration_min
            if duration_min
            else 0
        )

        return {
            "articles": self.article_count,
            "duration_min": round(duration_min, 2),
            "counted_tokens_for_rate_limit": self.counted_tokens_for_rate_limit,
            "avg_tokens": round(avg_tokens, 2),
            "tokens_per_min": round(tpm, 2),
            "model": self.model,
            "token_limit": self.token_limit,
            "openai_cost_before": self.openai_cost_before,
            "openai_cost_after": self.openai_cost_after,
            "total_cost": self.total_cost(),
            "cost_per_article": self.cost_per_article(),
            "cost_per_article_lang": self.cost_per_article_lang(),
        }

    def stats_report(self) -> str:
        stats = self.summary_dict()
        n_articles = stats["articles"]

        duration_total_sec = stats["duration_min"] * 60
        minutes = int(duration_total_sec // 60)
        seconds = int(duration_total_sec % 60)
        duration_readable = f"{minutes} min {seconds} s"

        articles_per_minute = (
            round(n_articles / stats["duration_min"], 2)
            if stats["duration_min"]
            else 0
        )
        minutes_per_article = (
            round(stats["duration_min"] / n_articles, 2) if n_articles else 0
        )

        tokens_article_per_minute = (
            round(stats["avg_tokens"] / stats["duration_min"], 2)
            if stats["duration_min"]
            else 0
        )

        return (
            f"--- STATISTICS ---\n"
            f"Articles processed          : {n_articles}\n"
            f"Total duration              : {stats['duration_min']} min ({duration_readable})\n"
            f"Articles/minute             : {articles_per_minute}\n"
            f"Minute/article              : {minutes_per_article}\n"
            f"\n"
            f"Tokens counted for quota    : {stats['counted_tokens_for_rate_limit']}\n"
            f"Average tokens/article      : {stats['avg_tokens']}\n"
            f"Tokens per minute           : {stats['tokens_per_min']}\n"
            f"Tokens/article/minute       : {tokens_article_per_minute}\n"
            f"\n"
            f"Model                       : {stats['model']}\n"
            f"Token limit / minute        : {stats['token_limit']}\n"
            f"\n"
            f"OpenAI cost before          : {self._money(stats['openai_cost_before'])}\n"
            f"OpenAI cost after           : {self._money(stats['openai_cost_after'])}\n"
            f"Total real cost             : {self._money(stats['total_cost'])}\n"
            f"Real cost/article           : {self._money(stats['cost_per_article'])}\n"
            f"Real cost/article/lang      : {self._money(stats['cost_per_article_lang'])}"
        )

    def model_report(self) -> str:
        return f"""
# ========================================
#         Model Configuration Summary
# ========================================
MODEL            = "{MODEL}"
MAX_TOKENS       = {MAX_TOKENS}
MAX_TOKENS_FR    = {MAX_TOKENS_FR}
REASONING        = "{REASONING.get('effort', 'unknown')}"
REASONING_FR     = "{REASONING_FR.get('effort', 'unknown')}"
TEXT             = "{TEXT.get('verbosity', 'unknown')}"
TEXT_FR          = "{TEXT_FR.get('verbosity', 'unknown')}"
SAFETY_MARGIN    = {SAFETY_MARGIN}

# ========================================
#         English System Prompt
# ========================================
{SYS_PROMPT_EN.strip()}
""".strip()

    def summary(self) -> str:
        return f"{self.stats_report()}\n\n{self.model_report()}"
