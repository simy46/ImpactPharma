from decimal import Decimal
from typing import Optional

from core.log_manager import LogManager
from retrieval.consts import (
    ARTICLE_HEADER_RE,
    BLANK_ROW_WRITTEN_RE,
    CATEGORY_RE,
    COST_AFTER_RE,
    COST_BEFORE_RE,
    EXCEL_EN_WRITTEN_RE,
    EXCEL_FR_WRITTEN_RE,
    LANG_EN,
    LANG_FR,
    OPENAI_CALL_RE,
    RAW_RE,
    START_TIME_RE,
    TOKEN_ESTIMATE_RE,
    USAGE_RE,
)
from retrieval.models import (
    ArticleLogState,
    OpenAICallContext,
    RunRecoverySnapshot,
    TokenUsage,
)


class LogParser:
    def __init__(self, logger: LogManager):
        self.logger = logger

    def parse(self, log_path: str) -> RunRecoverySnapshot:
        with open(log_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        snapshot = RunRecoverySnapshot(log_path=log_path)

        current_article: Optional[ArticleLogState] = None
        current_category: Optional[str] = None
        current_call = OpenAICallContext()

        index = 0

        while index < len(lines):
            line = lines[index].rstrip("\n")

            start_match = START_TIME_RE.match(line)
            if start_match:
                snapshot.started_at = start_match.group("value")
                index += 1
                continue

            cost_before_match = COST_BEFORE_RE.match(line)
            if cost_before_match:
                snapshot.cost_before = Decimal(cost_before_match.group("value"))
                index += 1
                continue

            cost_after_match = COST_AFTER_RE.match(line)
            if cost_after_match:
                snapshot.cost_after = Decimal(cost_after_match.group("value"))
                index += 1
                continue

            article_match = ARTICLE_HEADER_RE.match(line)
            if article_match:
                current_article = ArticleLogState(
                    name=article_match.group("article").strip()
                )
                snapshot.articles.append(current_article)
                current_category = None
                current_call = OpenAICallContext()
                index += 1
                continue

            category_match = CATEGORY_RE.match(line)
            if category_match and current_article:
                current_category = category_match.group("category").strip()
                current_article.ensure_category(current_category)
                index += 1
                continue

            estimate_match = TOKEN_ESTIMATE_RE.match(line)
            if estimate_match:
                snapshot.estimated_input_tokens += int(estimate_match.group("tokens"))
                index += 1
                continue

            call_match = OPENAI_CALL_RE.match(line)
            if call_match:
                current_call = OpenAICallContext(
                    model=call_match.group("model").strip(),
                    lang=call_match.group("lang").strip(),
                    retry_level=int(call_match.group("retry_level")),
                    max_output_tokens=int(call_match.group("max_output_tokens")),
                    reasoning=call_match.group("reasoning").strip(),
                )
                index += 1
                continue

            usage_match = USAGE_RE.match(line)
            if usage_match:
                snapshot.token_usages.append(
                    TokenUsage.from_regex_match(
                        match=usage_match,
                        article_name=current_article.name if current_article else None,
                        category=current_category,
                        lang=current_call.lang,
                        model=current_call.model,
                    )
                )
                index += 1
                continue

            raw_match = RAW_RE.match(line)
            if raw_match and current_article and current_category:
                raw_lang = raw_match.group("lang").lower()
                lang = LANG_EN if raw_lang == LANG_EN else LANG_FR
                raw_start = raw_match.group("raw")

                raw_json, index = self._collect_raw_json(
                    raw_start=raw_start,
                    lines=lines,
                    start_index=index,
                )

                if raw_json:
                    current_article.set_raw(
                        category=current_category,
                        lang=lang,
                        raw=raw_json,
                    )
                else:
                    snapshot.corrupted_raw_blocks.append(
                        f"{current_article.name} / {current_category} / {lang}"
                    )

                index += 1
                continue

            en_written_match = EXCEL_EN_WRITTEN_RE.match(line)
            if en_written_match:
                article = snapshot.find_article(en_written_match.group("article").strip())
                if article:
                    article.en_written_to_excel = True
                index += 1
                continue

            fr_written_match = EXCEL_FR_WRITTEN_RE.match(line)
            if fr_written_match:
                article = snapshot.find_article(fr_written_match.group("article").strip())
                if article:
                    article.fr_written_to_excel = True
                index += 1
                continue

            blank_match = BLANK_ROW_WRITTEN_RE.match(line)
            if blank_match:
                article = snapshot.find_article(blank_match.group("article").strip())
                if article:
                    article.blank_row_written = True
                index += 1
                continue

            index += 1

        self.logger.write(
            "info",
            (
                f"Parsed recovery log: {len(snapshot.articles)} article blocks, "
                f"{len(snapshot.token_usages)} usage records, "
                f"{snapshot.estimated_input_tokens} estimated input tokens."
            ),
        )

        return snapshot

    def _collect_raw_json(
        self,
        raw_start: str,
        lines: list[str],
        start_index: int,
    ) -> tuple[str, int]:
        buffer = [raw_start.rstrip()]
        balance = self._json_brace_balance(raw_start)

        if self._looks_complete_json(raw_start, balance):
            return raw_start.strip(), start_index

        index = start_index + 1

        while index < len(lines):
            next_line = lines[index].rstrip("\n")
            buffer.append(next_line)
            balance += self._json_brace_balance(next_line)

            candidate = "\n".join(buffer).strip()

            if self._looks_complete_json(candidate, balance):
                return candidate, index

            if balance <= 0 and self._line_starts_new_log_block(next_line):
                break

            index += 1

        return "\n".join(buffer).strip(), index

    @staticmethod
    def _line_starts_new_log_block(line: str) -> bool:
        return (
            line.startswith("[INFO]")
            or line.startswith("[TOKEN]")
            or line.startswith("[WAIT]")
            or line.startswith("[WARN]")
            or line.startswith("[ERROR]")
            or line.startswith("------ ")
        )

    @staticmethod
    def _looks_complete_json(text: str, balance: int) -> bool:
        stripped = text.strip()
        return stripped.startswith("{") and stripped.endswith("}") and balance == 0

    @staticmethod
    def _json_brace_balance(text: str) -> int:
        balance = 0
        in_string = False
        escaped = False

        for char in text:
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                balance += 1
            elif char == "}":
                balance -= 1

        return balance
