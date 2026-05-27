import argparse
import os

from core.log_manager import LogManager
from core.prompt_manager import PromptManager
from core.response_parser import ResponseParser

from retrieval.consts import MODE_FR_ONLY, MODE_FULL, MODE_RECOVERED
from retrieval.log_parser import LogParser
from retrieval.recovered_excel_writer import RecoveredExcelWriter
from retrieval.recovery_planner import RecoveryPlanner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild a recovered workbook from the original pipeline log and a recovery log."
    )

    parser.add_argument(
        "--source-log",
        required=True,
        help="Original pipeline log path.",
    )
    parser.add_argument(
        "--recovery-log",
        required=True,
        help="Recovery run log path.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output workbook path.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger = LogManager(name="repair_recovered_excel")
    prompt_manager = PromptManager()
    response_parser = ResponseParser()
    parser = LogParser(logger=logger)

    source_snapshot = parser.parse(args.source_log)
    recovery_snapshot = parser.parse(args.recovery_log)

    planner = RecoveryPlanner(
        logger=logger,
        prompt_manager=prompt_manager,
        response_parser=response_parser,
    )
    plan = planner.build(snapshot=source_snapshot)

    writer = RecoveredExcelWriter(output_path=args.output)

    missing_articles: list[str] = []

    for entry in plan.entries:
        if entry.mode == MODE_RECOVERED:
            writer.insert_article_results(
                pdf_name=entry.article_name,
                responses_en=entry.recovered_en or {},
                responses_fr=entry.recovered_fr or {},
                partial=False,
            )
            continue

        if entry.mode not in (MODE_FULL, MODE_FR_ONLY):
            raise ValueError(f"Unsupported plan mode: {entry.mode}")

        article = recovery_snapshot.find_article(entry.article_name)

        if article is None:
            missing_articles.append(entry.article_name)
            continue

        responses_en = article.merged_response(
            lang="en",
            expected_categories=plan.expected_categories,
            response_parser=response_parser,
        )
        responses_fr = article.merged_response(
            lang="fr",
            expected_categories=plan.expected_categories,
            response_parser=response_parser,
        )

        if responses_en is None or responses_fr is None:
            missing_articles.append(entry.article_name)
            continue

        writer.insert_article_results(
            pdf_name=entry.article_name,
            responses_en=responses_en,
            responses_fr=responses_fr,
            partial=False,
        )

    if missing_articles:
        raise ValueError(
            "Unable to rebuild all planned articles from the provided logs: "
            f"{missing_articles}"
        )

    writer.verify_persisted_articles(
        entry.article_name for entry in plan.entries
    )

    print(f"Rebuilt workbook written to: {os.path.abspath(writer.output_path)}")


if __name__ == "__main__":
    main()