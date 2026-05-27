from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

from retrieval.consts import LANG_EN, LANG_FR, MODE_FULL, MODE_FR_ONLY, MODE_RECOVERED


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    article_name: Optional[str] = None
    category: Optional[str] = None
    lang: Optional[str] = None
    model: Optional[str] = None

    @staticmethod
    def _to_int(value: str | None) -> int:
        if value in (None, "None", ""):
            return 0

        return int(value)

    @classmethod
    def from_regex_match(
        cls,
        match,
        article_name: Optional[str],
        category: Optional[str],
        lang: Optional[str],
        model: Optional[str],
    ) -> "TokenUsage":
        return cls(
            input_tokens=cls._to_int(match.group("input")),
            output_tokens=cls._to_int(match.group("output")),
            reasoning_tokens=cls._to_int(match.group("reasoning")),
            total_tokens=cls._to_int(match.group("total")),
            article_name=article_name,
            category=category,
            lang=lang,
            model=model,
        )


@dataclass
class OpenAICallContext:
    model: Optional[str] = None
    lang: Optional[str] = None
    retry_level: Optional[int] = None
    max_output_tokens: Optional[int] = None
    reasoning: Optional[str] = None


@dataclass
class CategoryLogRecord:
    name: str
    en_raw: Optional[str] = None
    fr_raw: Optional[str] = None

    def raw_for_lang(self, lang: str) -> Optional[str]:
        if lang == LANG_EN:
            return self.en_raw

        if lang == LANG_FR:
            return self.fr_raw

        raise ValueError(f"Unsupported language: {lang}")

    def set_raw(self, lang: str, raw: str) -> None:
        if lang == LANG_EN:
            self.en_raw = raw
            return

        if lang == LANG_FR:
            self.fr_raw = raw
            return

        raise ValueError(f"Unsupported language: {lang}")


@dataclass
class ArticleLogState:
    name: str
    categories: dict[str, CategoryLogRecord] = field(default_factory=dict)
    category_order: list[str] = field(default_factory=list)
    en_written_to_excel: bool = False
    fr_written_to_excel: bool = False
    blank_row_written: bool = False

    def ensure_category(self, category: str) -> CategoryLogRecord:
        if category not in self.categories:
            self.categories[category] = CategoryLogRecord(name=category)
            self.category_order.append(category)

        return self.categories[category]

    def set_raw(self, category: str, lang: str, raw: str) -> None:
        self.ensure_category(category).set_raw(lang, raw)

    def raw_for_category(self, category: str, lang: str) -> Optional[str]:
        record = self.categories.get(category)

        if not record:
            return None

        return record.raw_for_lang(lang)

    def parsed_category(
        self,
        category: str,
        lang: str,
        response_parser,
    ) -> Optional[dict[str, Any]]:
        raw = self.raw_for_category(category, lang)

        if not raw:
            return None

        parsed = response_parser.parse(raw)

        if "error" in parsed:
            return None

        return parsed

    def merged_response(
        self,
        lang: str,
        expected_categories: list[str],
        response_parser,
    ) -> Optional[dict[str, Any]]:
        merged: dict[str, Any] = {}

        for category in expected_categories:
            parsed = self.parsed_category(
                category=category,
                lang=lang,
                response_parser=response_parser,
            )

            if parsed is None:
                return None

            merged.update(parsed)

        return merged

    def is_language_complete(
        self,
        lang: str,
        expected_categories: list[str],
        response_parser,
    ) -> bool:
        return self.merged_response(
            lang=lang,
            expected_categories=expected_categories,
            response_parser=response_parser,
        ) is not None

    def is_complete(
        self,
        expected_categories: list[str],
        response_parser,
    ) -> bool:
        return (
            self.is_language_complete(LANG_EN, expected_categories, response_parser)
            and self.is_language_complete(LANG_FR, expected_categories, response_parser)
        )


@dataclass
class RunRecoverySnapshot:
    log_path: str
    started_at: Optional[str] = None
    cost_before: Optional[Decimal] = None
    cost_after: Optional[Decimal] = None
    articles: list[ArticleLogState] = field(default_factory=list)
    token_usages: list[TokenUsage] = field(default_factory=list)
    estimated_input_tokens: int = 0
    corrupted_raw_blocks: list[str] = field(default_factory=list)

    def article_names(self) -> list[str]:
        return [article.name for article in self.articles]

    def find_article(self, article_name: str) -> Optional[ArticleLogState]:
        for article in self.articles:
            if article.name == article_name:
                return article

        return None

    def total_usage(self) -> TokenUsage:
        total = TokenUsage()

        for usage in self.token_usages:
            total.input_tokens += usage.input_tokens
            total.output_tokens += usage.output_tokens
            total.reasoning_tokens += usage.reasoning_tokens
            total.total_tokens += usage.total_tokens

        return total


@dataclass
class IterationSelection:
    iteration_number: int
    log_path: str
    all_logs: list[str]


@dataclass
class PlanEntry:
    article_name: str
    mode: str
    pdf_path: Optional[str] = None
    article_state: Optional[ArticleLogState] = None
    recovered_en: Optional[dict[str, Any]] = None
    recovered_fr: Optional[dict[str, Any]] = None

    def needs_api(self) -> bool:
        return self.mode in (MODE_FR_ONLY, MODE_FULL)

    def is_recovered(self) -> bool:
        return self.mode == MODE_RECOVERED


@dataclass
class ResumePlan:
    entries: list[PlanEntry]
    expected_categories: list[str]
    skipped_errors: list[str] = field(default_factory=list)

    def recovered_complete_count(self) -> int:
        return sum(1 for entry in self.entries if entry.mode == MODE_RECOVERED)

    def fr_only_count(self) -> int:
        return sum(1 for entry in self.entries if entry.mode == MODE_FR_ONLY)

    def full_count(self) -> int:
        return sum(1 for entry in self.entries if entry.mode == MODE_FULL)

    def api_entry_count(self) -> int:
        return sum(1 for entry in self.entries if entry.needs_api())

    def final_article_count(self) -> int:
        return len(self.entries)

    def final_language_rows(self) -> int:
        return len(self.entries) * 2
