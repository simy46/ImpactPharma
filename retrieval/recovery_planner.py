import os

from constants.script_consts import PDF_DIR
from core.log_manager import LogManager
from core.prompt_manager import PromptManager
from core.response_parser import ResponseParser
from retrieval.consts import LANG_EN, LANG_FR, MODE_FULL, MODE_FR_ONLY, MODE_RECOVERED
from retrieval.models import PlanEntry, ResumePlan, RunRecoverySnapshot


class RecoveryPlanner:
    def __init__(
        self,
        logger: LogManager,
        prompt_manager: PromptManager,
        response_parser: ResponseParser,
        pdf_dir: str = PDF_DIR,
    ):
        self.logger = logger
        self.prompt_manager = prompt_manager
        self.response_parser = response_parser
        self.pdf_dir = pdf_dir

    def build(self, snapshot: RunRecoverySnapshot) -> ResumePlan:
        expected_categories = self.prompt_manager.get_categories()
        pdf_map = self._build_pdf_map()

        entries: list[PlanEntry] = []
        skipped_errors: list[str] = []
        seen_article_names: set[str] = set()

        for article in snapshot.articles:
            seen_article_names.add(article.name)

            recovered_en = article.merged_response(
                lang=LANG_EN,
                expected_categories=expected_categories,
                response_parser=self.response_parser,
            )
            recovered_fr = article.merged_response(
                lang=LANG_FR,
                expected_categories=expected_categories,
                response_parser=self.response_parser,
            )

            if recovered_en is not None and recovered_fr is not None:
                entries.append(
                    PlanEntry(
                        article_name=article.name,
                        mode=MODE_RECOVERED,
                        article_state=article,
                        recovered_en=recovered_en,
                        recovered_fr=recovered_fr,
                    )
                )
                continue

            if recovered_en is not None:
                entries.append(
                    PlanEntry(
                        article_name=article.name,
                        mode=MODE_FR_ONLY,
                        pdf_path=pdf_map.get(article.name),
                        article_state=article,
                        recovered_en=recovered_en,
                    )
                )
                continue

            pdf_path = pdf_map.get(article.name)

            if not pdf_path:
                skipped_errors.append(
                    f"Cannot recover incomplete article because PDF is missing: {article.name}"
                )
                continue

            entries.append(
                PlanEntry(
                    article_name=article.name,
                    mode=MODE_FULL,
                    pdf_path=pdf_path,
                    article_state=article,
                )
            )

        remaining_article_names = sorted(
            article_name
            for article_name in pdf_map
            if article_name not in seen_article_names
        )

        for article_name in remaining_article_names:
            entries.append(
                PlanEntry(
                    article_name=article_name,
                    mode=MODE_FULL,
                    pdf_path=pdf_map[article_name],
                )
            )

        plan = ResumePlan(
            entries=entries,
            expected_categories=expected_categories,
            skipped_errors=skipped_errors,
        )

        self._log_plan(plan)

        return plan

    def _build_pdf_map(self) -> dict[str, str]:
        if not os.path.isdir(self.pdf_dir):
            raise FileNotFoundError(f"PDF directory not found: {self.pdf_dir}")

        pdf_map = {}

        for filename in os.listdir(self.pdf_dir):
            if not filename.lower().endswith(".pdf"):
                continue

            article_name = os.path.splitext(filename)[0]
            pdf_map[article_name] = os.path.join(self.pdf_dir, filename)

        return pdf_map

    def _log_plan(self, plan: ResumePlan) -> None:
        self.logger.write(
            "info",
            (
                "Recovery plan built | "
                f"final_articles={plan.final_article_count()}, "
                f"final_language_rows={plan.final_language_rows()}, "
                f"recovered={plan.recovered_complete_count()}, "
                f"fr_only={plan.fr_only_count()}, "
                f"full_api={plan.full_count()}, "
                f"skipped_errors={len(plan.skipped_errors)}"
            ),
        )

        for error in plan.skipped_errors:
            self.logger.write("warn", error)
