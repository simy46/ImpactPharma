from constants.general_consts import FR
from constants.script_consts import METHODOLOGY_CATEGORY, OUTCOMES_CATEGORY, QUESTION_8
from core.api_manager import OpenAIQuotaExceeded
from core.log_manager import LogManager
from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.response_parser import ResponseParser
from retrieval.consts import LANG_EN, LANG_FR, MODE_FULL, MODE_FR_ONLY, MODE_RECOVERED
from retrieval.models import PlanEntry, ResumePlan
from retrieval.recovered_excel_writer import RecoveredExcelWriter
from retrieval.recovered_stats import RecoveredStats
from retrieval.resume_api_client import RecoveryOpenAIClient


class ResumeRunner:
    def __init__(
        self,
        logger: LogManager,
        prompt_manager: PromptManager,
        api: RecoveryOpenAIClient,
        response_parser: ResponseParser,
        writer: RecoveredExcelWriter,
        stats: RecoveredStats,
    ):
        self.logger = logger
        self.prompt_manager = prompt_manager
        self.api = api
        self.response_parser = response_parser
        self.writer = writer
        self.stats = stats

    def run(self, plan: ResumePlan) -> None:
        self.logger.write("info", "Starting recovery execution.")

        for entry in plan.entries:
            try:
                if entry.mode == MODE_RECOVERED:
                    self._write_recovered_entry(entry)
                    continue

                if entry.mode == MODE_FR_ONLY:
                    self._run_fr_only_entry(entry, plan.expected_categories)
                    continue

                if entry.mode == MODE_FULL:
                    self._run_full_entry(entry, plan.expected_categories)
                    continue

                raise ValueError(f"Unsupported recovery mode: {entry.mode}")

            except OpenAIQuotaExceeded:
                self.logger.write(
                    "error",
                    f"Recovery stopped because OpenAI quota is exhausted at article: {entry.article_name}",
                )
                break

        self.writer.verify_persisted_articles(entry.article_name for entry in plan.entries)
        self.logger.write("info", "Recovery execution finished.")

    def _write_recovered_entry(self, entry: PlanEntry) -> None:
        if entry.recovered_en is None or entry.recovered_fr is None:
            raise ValueError(f"Recovered entry is missing data: {entry.article_name}")

        self.writer.insert_article_results(
            pdf_name=entry.article_name,
            responses_en=entry.recovered_en,
            responses_fr=entry.recovered_fr,
            partial=False,
        )
        self.stats.mark_recovered_article_complete()
        self.logger.write("info", f"Recovered from log and verified: {entry.article_name}")

    def _run_fr_only_entry(
        self,
        entry: PlanEntry,
        expected_categories: list[str],
    ) -> None:
        if entry.recovered_en is None or entry.article_state is None:
            raise ValueError(f"FR-only entry is missing recovered EN data: {entry.article_name}")

        responses_fr = {}
        partial = False

        try:
            for category in expected_categories:
                parsed_en = entry.article_state.parsed_category(
                    category=category,
                    lang=LANG_EN,
                    response_parser=self.response_parser,
                )

                if parsed_en is None:
                    raise ValueError(
                        f"Missing recovered EN category for FR-only resume: "
                        f"{entry.article_name} / {category}"
                    )

                raw_json_en = self.response_parser.to_json_string(parsed_en)
                system_prompt_fr = self.prompt_manager.translate_prompt()

                tok_fr = self.api._count_tokens(system_prompt_fr, raw_json_en)
                self.stats.add_new_estimated_input_tokens(tok_fr)

                self.api.set_call_context(
                    article_name=entry.article_name,
                    category=category,
                    lang=LANG_FR,
                )

                raw_fr = self.api.ask(
                    system_prompt=system_prompt_fr,
                    user_prompt=raw_json_en,
                    tokens_used=tok_fr,
                    lang=FR,
                )

                self.logger.write("info", f"[FR] Raw: {raw_fr}")

                parsed_fr = self.response_parser.parse(raw_fr)
                responses_fr.update(parsed_fr)

        except Exception:
            partial = True
            raise

        finally:
            if responses_fr:
                self.writer.insert_article_results(
                    pdf_name=entry.article_name,
                    responses_en=entry.recovered_en,
                    responses_fr=responses_fr,
                    partial=partial,
                )

                if partial:
                    self.stats.mark_partial_article()
                else:
                    self.stats.mark_fr_only_article_complete()
                    self.logger.write("info", f"FR resumed from recovered EN and verified: {entry.article_name}")

    def _run_full_entry(
        self,
        entry: PlanEntry,
        expected_categories: list[str],
    ) -> None:
        if not entry.pdf_path:
            raise ValueError(f"Full resume entry is missing PDF path: {entry.article_name}")

        self.logger.logger.info(f"\n\n------ {entry.article_name} ------")
        self.logger.write("info", f"Full API resume for {entry.article_name}")

        text = PDFLoader.extract_text(entry.pdf_path)
        self.logger.write("info", "Texte extrait du pdf")

        responses_en = {}
        responses_fr = {}
        context_for_outcomes = {}
        partial = False

        try:
            for category in expected_categories:
                self.logger.write("info", f"[CATEGORY] {category}")

                parsed_en = self._run_en_category(
                    article_name=entry.article_name,
                    text=text,
                    category=category,
                    context_for_outcomes=context_for_outcomes,
                )
                responses_en.update(parsed_en)

                if category == METHODOLOGY_CATEGORY and QUESTION_8 in parsed_en:
                    context_for_outcomes[QUESTION_8] = parsed_en[QUESTION_8]

                parsed_fr = self._run_fr_category(
                    article_name=entry.article_name,
                    category=category,
                    parsed_en=parsed_en,
                )
                responses_fr.update(parsed_fr)

        except Exception:
            partial = True
            raise

        finally:
            if responses_en or responses_fr:
                self.writer.insert_article_results(
                    pdf_name=entry.article_name,
                    responses_en=responses_en,
                    responses_fr=responses_fr,
                    partial=partial,
                )

                if partial:
                    self.stats.mark_partial_article()
                else:
                    self.stats.mark_full_article_complete()
                    self.logger.write("info", f"Full article resumed and verified: {entry.article_name}")

    def _run_en_category(
        self,
        article_name: str,
        text: str,
        category: str,
        context_for_outcomes: dict,
    ) -> dict:
        system_prompt = self.prompt_manager.get_system_prompt()
        user_prompt = self.prompt_manager.build_prompt(
            text,
            category,
            previous_answers=(
                context_for_outcomes
                if category == OUTCOMES_CATEGORY and context_for_outcomes
                else None
            ),
        )

        tok_en = self.api._count_tokens(system_prompt, user_prompt)
        self.stats.add_new_estimated_input_tokens(tok_en)

        self.api.set_call_context(
            article_name=article_name,
            category=category,
            lang=LANG_EN,
        )

        raw_en = self.api.ask(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tokens_used=tok_en,
        )

        self.logger.write("info", f"[EN] Raw: {raw_en}")

        return self.response_parser.parse(raw_en)

    def _run_fr_category(
        self,
        article_name: str,
        category: str,
        parsed_en: dict,
    ) -> dict:
        raw_json_en = self.response_parser.to_json_string(parsed_en)
        system_prompt_fr = self.prompt_manager.translate_prompt()

        tok_fr = self.api._count_tokens(system_prompt_fr, raw_json_en)
        self.stats.add_new_estimated_input_tokens(tok_fr)

        self.api.set_call_context(
            article_name=article_name,
            category=category,
            lang=LANG_FR,
        )

        raw_fr = self.api.ask(
            system_prompt=system_prompt_fr,
            user_prompt=raw_json_en,
            tokens_used=tok_fr,
            lang=FR,
        )

        self.logger.write("info", f"[FR] Raw: {raw_fr}")

        return self.response_parser.parse(raw_fr)