from dotenv import load_dotenv

from core.log_manager import LogManager
from core.prompt_manager import PromptManager
from core.response_parser import ResponseParser

from retrieval.iteration_selector import IterationSelector
from retrieval.log_parser import LogParser
from retrieval.recovery_planner import RecoveryPlanner
from retrieval.recovered_excel_writer import RecoveredExcelWriter
from retrieval.recovered_stats import RecoveredStats
from retrieval.resume_api_client import RecoveryOpenAIClient
from retrieval.resume_runner import ResumeRunner


load_dotenv()

logger = LogManager()
prompt_manager = PromptManager()
response_parser = ResponseParser()

selector = IterationSelector(logger=logger)
selection = selector.select()

log_parser = LogParser(logger=logger)
snapshot = log_parser.parse(selection.log_path)

planner = RecoveryPlanner(
    logger=logger,
    prompt_manager=prompt_manager,
    response_parser=response_parser,
)
plan = planner.build(snapshot=snapshot)

writer = RecoveredExcelWriter()

stats = RecoveredStats(
    selection=selection,
    snapshot=snapshot,
    plan=plan,
)

api = RecoveryOpenAIClient(
    logger=logger,
    recovered_stats=stats,
)

runner = ResumeRunner(
    logger=logger,
    prompt_manager=prompt_manager,
    api=api,
    response_parser=response_parser,
    writer=writer,
    stats=stats,
)

try:
    runner.run(plan)

    writer.verify_persisted_articles(
        entry.article_name for entry in plan.entries
    )

finally:
    stats.write_reports(writer.output_dir)

logger.write("info", f"Recovered Excel written to: {writer.output_path}")
logger.write("info", f"Recovery stats written to: {writer.output_dir}")