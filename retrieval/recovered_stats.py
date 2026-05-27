import os
from datetime import datetime
from decimal import Decimal
from typing import Optional

from constants.params import (
    MODEL,
    MAX_TOKENS,
    MAX_TOKENS_FR,
    REASONING,
    REASONING_FR,
    SAFETY_MARGIN,
    SYS_PROMPT_EN,
    TEXT,
    TEXT_FR,
    TOKENS_PER_MINUTE,
)
from retrieval.models import IterationSelection, ResumePlan, RunRecoverySnapshot, TokenUsage


class RecoveredStats:
    def __init__(
        self,
        selection: IterationSelection,
        snapshot: RunRecoverySnapshot,
        plan: ResumePlan,
    ):
        self.selection = selection
        self.snapshot = snapshot
        self.plan = plan

        self.started_at = datetime.now()
        self.ended_at: Optional[datetime] = None

        self.new_usages: list[TokenUsage] = []
        self.new_estimated_input_tokens = 0

        self.completed_recovered_articles = 0
        self.completed_fr_only_articles = 0
        self.completed_full_articles = 0
        self.partial_articles = 0

    def add_new_usage(self, usage: TokenUsage) -> None:
        self.new_usages.append(usage)

    def add_new_estimated_input_tokens(self, value: int) -> None:
        self.new_estimated_input_tokens += value

    def mark_recovered_article_complete(self) -> None:
        self.completed_recovered_articles += 1

    def mark_fr_only_article_complete(self) -> None:
        self.completed_fr_only_articles += 1

    def mark_full_article_complete(self) -> None:
        self.completed_full_articles += 1

    def mark_partial_article(self) -> None:
        self.partial_articles += 1

    def stop(self) -> None:
        self.ended_at = datetime.now()

    def recovered_usage(self) -> TokenUsage:
        return self.snapshot.total_usage()

    def new_usage(self) -> TokenUsage:
        total = TokenUsage()

        for usage in self.new_usages:
            total.input_tokens += usage.input_tokens
            total.output_tokens += usage.output_tokens
            total.reasoning_tokens += usage.reasoning_tokens
            total.total_tokens += usage.total_tokens

        return total

    def total_usage(self) -> TokenUsage:
        recovered = self.recovered_usage()
        new = self.new_usage()

        return TokenUsage(
            input_tokens=recovered.input_tokens + new.input_tokens,
            output_tokens=recovered.output_tokens + new.output_tokens,
            reasoning_tokens=recovered.reasoning_tokens + new.reasoning_tokens,
            total_tokens=recovered.total_tokens + new.total_tokens,
        )

    @staticmethod
    def _money(value: Optional[Decimal]) -> str:
        if value is None:
            return "Unavailable"

        return f"${value:.6f}"

    @staticmethod
    def _dict_value(data: dict, key: str, fallback: str = "unknown") -> str:
        value = data.get(key, fallback) if isinstance(data, dict) else fallback
        return str(value)

    def stats_report(self) -> str:
        self.stop()

        duration_min = (
            (self.ended_at - self.started_at).total_seconds() / 60
            if self.ended_at
            else 0
        )

        recovered_usage = self.recovered_usage()
        new_usage = self.new_usage()
        total_usage = self.total_usage()

        return (
            f"--- RECOVERY STATISTICS ---\n"
            f"Selected iteration          : {self.selection.iteration_number}\n"
            f"Source log                  : {self.selection.log_path}\n"
            f"Original run started at     : {self.snapshot.started_at or 'Unavailable'}\n"
            f"Recovery duration           : {round(duration_min, 2)} min\n"
            f"\n"
            f"Final articles planned      : {self.plan.final_article_count()}\n"
            f"Final language rows planned : {self.plan.final_language_rows()}\n"
            f"Recovered complete articles : {self.completed_recovered_articles}\n"
            f"FR-only resumed articles    : {self.completed_fr_only_articles}\n"
            f"Full API resumed articles   : {self.completed_full_articles}\n"
            f"Partial articles            : {self.partial_articles}\n"
            f"Skipped errors              : {len(self.plan.skipped_errors)}\n"
            f"\n"
            f"Recovered estimated input tokens : {self.snapshot.estimated_input_tokens}\n"
            f"New estimated input tokens       : {self.new_estimated_input_tokens}\n"
            f"Combined estimated input tokens  : {self.snapshot.estimated_input_tokens + self.new_estimated_input_tokens}\n"
            f"\n"
            f"Recovered real usage tokens : input={recovered_usage.input_tokens}, "
            f"output={recovered_usage.output_tokens}, reasoning={recovered_usage.reasoning_tokens}, "
            f"total={recovered_usage.total_tokens}\n"
            f"New real usage tokens       : input={new_usage.input_tokens}, "
            f"output={new_usage.output_tokens}, reasoning={new_usage.reasoning_tokens}, "
            f"total={new_usage.total_tokens}\n"
            f"Combined real usage tokens  : input={total_usage.input_tokens}, "
            f"output={total_usage.output_tokens}, reasoning={total_usage.reasoning_tokens}, "
            f"total={total_usage.total_tokens}\n"
            f"\n"
            f"Original cost before        : {self._money(self.snapshot.cost_before)}\n"
            f"Original cost after         : {self._money(self.snapshot.cost_after)}\n"
            f"Model                       : {MODEL}\n"
            f"Token limit / minute        : {TOKENS_PER_MINUTE}"
        )

    def model_report(self) -> str:
        reasoning_effort = self._dict_value(REASONING, "effort")
        reasoning_fr_effort = self._dict_value(REASONING_FR, "effort")
        text_verbosity = self._dict_value(TEXT, "verbosity")
        text_fr_verbosity = self._dict_value(TEXT_FR, "verbosity")

        return f"""
# ========================================
#         Model Configuration Summary
# ========================================
MODEL            = "{MODEL}"
MAX_TOKENS       = {MAX_TOKENS}
MAX_TOKENS_FR    = {MAX_TOKENS_FR}
REASONING        = "{reasoning_effort}"
REASONING_FR     = "{reasoning_fr_effort}"
TEXT             = "{text_verbosity}"
TEXT_FR          = "{text_fr_verbosity}"
SAFETY_MARGIN    = {SAFETY_MARGIN}

# ========================================
#         English System Prompt
# ========================================
{SYS_PROMPT_EN.strip()}
""".strip()

    def recovery_report(self) -> str:
        errors = "\n".join(f"- {error}" for error in self.plan.skipped_errors)

        if not errors:
            errors = "None"

        return (
            f"--- RECOVERY REPORT ---\n"
            f"Selected iteration : {self.selection.iteration_number}\n"
            f"Source log         : {self.selection.log_path}\n"
            f"\n"
            f"Plan summary\n"
            f"- Final articles       : {self.plan.final_article_count()}\n"
            f"- Final language rows  : {self.plan.final_language_rows()}\n"
            f"- Recovered complete   : {self.plan.recovered_complete_count()}\n"
            f"- FR-only API resume   : {self.plan.fr_only_count()}\n"
            f"- Full API resume      : {self.plan.full_count()}\n"
            f"\n"
            f"Skipped errors\n"
            f"{errors}\n"
        )

    def write_reports(self, output_dir: str) -> None:
        reports = {
            "stats.txt": self.stats_report(),
            "model.txt": self.model_report(),
            "recovery_report.txt": self.recovery_report(),
        }

        for filename, content in reports.items():
            path = os.path.join(output_dir, filename)

            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
