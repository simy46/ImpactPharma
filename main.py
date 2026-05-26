from datetime import datetime
from decimal import Decimal
import os
from typing import Optional

from dotenv import load_dotenv

from constants.general_consts import FR
from constants.script_consts import (
    PDF_DIR,
    METHODOLOGY_CATEGORY,
    OUTCOMES_CATEGORY,
    QUESTION_8,
)

from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.api_manager import OpenAIClient
from core.response_parser import ResponseParser
from core.excel_writer import ExcelWriter
from core.log_manager import LogManager
from core.stats_manager import StatsManager
from core.openai_costs import (
    fetch_openai_cost_usd,
    unix_start_of_today_utc,
)


load_dotenv()

lg = LogManager()
pm = PromptManager()
api = OpenAIClient(logger=lg)
rp = ResponseParser()
writer = ExcelWriter()
stats = StatsManager()


def log_cost_snapshot(label: str, value: Optional[Decimal]) -> None:
    if value is None:
        lg.write("warn", f"{label}: Unavailable")
    else:
        lg.write("info", f"{label}: ${value:.6f}")


def try_fetch_openai_cost(label: str, start_time: int) -> Optional[Decimal]:
    """
    Non-blocking cost fetch.

    If OpenAI cost fetching fails, the script continues normally.
    """

    try:
        value = fetch_openai_cost_usd(start_time=start_time)
        log_cost_snapshot(label, value)
        return value

    except Exception as e:
        lg.write("warn", f"{label} unavailable: {e}")
        return None


def write_run_metadata(output_dir: str, stats_report: str, model_report: str) -> None:
    reports = {
        "stats.txt": stats_report,
        "model.txt": model_report,
    }

    for filename, content in reports.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


def main():
    # Costs are optional. If this fails, the run should still continue.
    cost_window_start = unix_start_of_today_utc()

    stats.start()

    lg.write(
        "info",
        f"Début du traitement : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    cost_before = try_fetch_openai_cost(
        label="OpenAI cost before run",
        start_time=cost_window_start,
    )
    stats.set_openai_cost_before(cost_before)

    for pdf_path in os.listdir(PDF_DIR):
        if not pdf_path.endswith(".pdf"):
            continue

        pdf_name = os.path.splitext(pdf_path)[0]
        stats.add_article()
        lg.logger.info(f"\n\n------ {pdf_name} ------")

        try:
            text = PDFLoader.extract_text(os.path.join(PDF_DIR, pdf_path))
            lg.write("info", "Texte extrait du pdf")
        except Exception as e:
            lg.write("error", f"Extraction échouée pour {pdf_name} : {e}")
            continue

        responses_en = {}
        responses_fr = {}
        context_for_outcomes = {}

        for category in pm.get_categories():
            lg.write("info", f"[CATEGORY] {category}")

            # ========== Analyse EN ==========
            system_prompt = pm.get_system_prompt()
            user_prompt = pm.build_prompt(
                text,
                category,
                previous_answers=(
                    context_for_outcomes
                    if category == OUTCOMES_CATEGORY and context_for_outcomes
                    else None
                ),
            )

            tok_en = api._count_tokens(system_prompt, user_prompt)
            stats.add_tokens(tok_en)

            raw_en = api.ask(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tokens_used=tok_en,
            )

            lg.write("info", f"[EN] Raw: {raw_en}")
            parsed_en = rp.parse(raw_en)

            if category == METHODOLOGY_CATEGORY and QUESTION_8 in parsed_en:
                context_for_outcomes[QUESTION_8] = parsed_en[QUESTION_8]

            responses_en.update(parsed_en)

            # ========== Traduction FR ==========
            raw_json_en = rp.to_json_string(parsed_en)
            system_prompt_fr = pm.translate_prompt()

            tok_fr = api._count_tokens(system_prompt_fr, raw_json_en)
            stats.add_tokens(tok_fr)

            raw_fr = api.ask(
                system_prompt=system_prompt_fr,
                user_prompt=raw_json_en,
                tokens_used=tok_fr,
                lang=FR,
            )

            lg.write("info", f"[FR] Raw: {raw_fr}")
            parsed_fr = rp.parse(raw_fr)
            responses_fr.update(parsed_fr)

        try:
            writer.insert_row(pdf_name + " (EN)", responses_en)
            lg.write("info", f"[EN] Results added to Excel for {pdf_name}")

            writer.insert_row(pdf_name + " (FR)", responses_fr)
            lg.write("info", f"[FR] Results added to Excel for {pdf_name}")

            writer.insert_blank_row()
            lg.write("info", f"Blank row added after {pdf_name}")

        except Exception as e:
            lg.write("error", f"Excel write failed for {pdf_name} : {e}")

    cost_after = try_fetch_openai_cost(
        label="OpenAI cost after run",
        start_time=cost_window_start,
    )
    stats.set_openai_cost_after(cost_after)

    total_cost = stats.total_cost()
    if total_cost is not None:
        log_cost_snapshot("OpenAI real run cost", total_cost)
    else:
        lg.write("warn", "OpenAI real run cost unavailable.")

    stats.stop()

    lg.write(
        "info",
        f"Tous les fichiers ont été traités : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
    )

    stats_report = stats.stats_report()
    model_report = stats.model_report()

    write_run_metadata(writer.output_dir, stats_report, model_report)
    lg.write("info", f"Statistiques \n{stats.summary()}")


if __name__ == "__main__":
    main()
