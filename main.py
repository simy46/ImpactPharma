import os
from datetime import datetime
from dotenv import load_dotenv
from constants.general_consts import FR
from constants.script_consts import (
    PDF_DIR,
    METHODOLOGY_CATEGORY,
    OUTCOMES_CATEGORY,
    QUESTION_8,
)
from core.api_manager import OpenAIClient, OpenAIQuotaExceeded
from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.response_parser import ResponseParser
from core.excel_writer import ExcelWriter
from core.log_manager import LogManager
from core.stats_manager import StatsManager
from core.openai_costs import (
    safe_fetch_openai_cost_usd,
    unix_start_of_today_utc,
)


load_dotenv()

logger = LogManager()
prompt_manager = PromptManager()
api = OpenAIClient(logger=logger)
response_parser = ResponseParser()
writer = ExcelWriter()
stats = StatsManager()

cost_window_start = unix_start_of_today_utc()

stats.start()

logger.write(
    "info",
    f"Début du traitement : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
)

cost_before = safe_fetch_openai_cost_usd(
    logger=logger,
    label="OpenAI cost before run",
    start_time=cost_window_start,
)
stats.set_openai_cost_before(cost_before)

try:
    pdf_files = sorted(
        filename
        for filename in os.listdir(PDF_DIR)
        if filename.lower().endswith(".pdf")
    )

    if not pdf_files:
        logger.write("warn", f"No PDF files found in {PDF_DIR}")

    stop_run = False

    for pdf_filename in pdf_files:
        pdf_name = os.path.splitext(pdf_filename)[0]
        pdf_full_path = os.path.join(PDF_DIR, pdf_filename)

        logger.logger.info(f"\n\n------ {pdf_name} ------")

        try:
            text = PDFLoader.extract_text(pdf_full_path)
            logger.write("info", "Texte extrait du pdf")

        except Exception as e:
            logger.write("error", f"Extraction échouée pour {pdf_name}: {e}")
            continue

        stats.add_article()

        responses_en = {}
        responses_fr = {}
        context_for_outcomes = {}
        partial_article = False

        for category in prompt_manager.get_categories():
            logger.write("info", f"[CATEGORY] {category}")

            try:
                # ========== Analyse EN ==========
                system_prompt = prompt_manager.get_system_prompt()
                user_prompt = prompt_manager.build_prompt(
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

                logger.write("info", f"[EN] Raw: {raw_en}")

                parsed_en = response_parser.parse(raw_en)
                responses_en.update(parsed_en)

                if category == METHODOLOGY_CATEGORY and QUESTION_8 in parsed_en:
                    context_for_outcomes[QUESTION_8] = parsed_en[QUESTION_8]

                # ========== Traduction FR ==========
                raw_json_en = response_parser.to_json_string(parsed_en)
                system_prompt_fr = prompt_manager.translate_prompt()

                tok_fr = api._count_tokens(system_prompt_fr, raw_json_en)
                stats.add_tokens(tok_fr)

                raw_fr = api.ask(
                    system_prompt=system_prompt_fr,
                    user_prompt=raw_json_en,
                    tokens_used=tok_fr,
                    lang=FR,
                )

                logger.write("info", f"[FR] Raw: {raw_fr}")

                parsed_fr = response_parser.parse(raw_fr)
                responses_fr.update(parsed_fr)

            except OpenAIQuotaExceeded as e:
                logger.write(
                    "error",
                    f"OpenAI quota exhausted for {pdf_name} / {category}: {e}",
                )
                partial_article = True
                stop_run = True
                break

            except Exception as e:
                logger.write(
                    "error",
                    f"Category failed for {pdf_name} / {category}: {e}",
                )
                partial_article = True
                break

        if responses_en or responses_fr:
            writer.insert_article_results(
                pdf_name=pdf_name,
                responses_en=responses_en,
                responses_fr=responses_fr,
                partial=partial_article,
            )
            logger.write("info", f"Results written to Excel for {pdf_name}")

        else:
            logger.write("warn", f"No results to write for {pdf_name}")

        if stop_run:
            logger.write("error", "Run stopped early because OpenAI quota is exhausted.")
            break

finally:
    cost_after = safe_fetch_openai_cost_usd(
        logger=logger,
        label="OpenAI cost after run",
        start_time=cost_window_start,
    )
    stats.set_openai_cost_after(cost_after)

    total_cost = stats.total_cost()

    if total_cost is not None:
        logger.write("info", f"OpenAI real run cost: ${total_cost:.6f}")
    else:
        logger.write("warn", "OpenAI real run cost unavailable.")

    stats.stop()

    logger.write(
        "info",
        f"Traitement terminé : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    stats.write_reports(writer.output_dir)

    logger.write("info", f"Statistiques \n{stats.summary()}")