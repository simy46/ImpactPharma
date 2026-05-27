import os
import re


LOG_DIR = "logs"

RECOVERY_OUTPUT_PREFIX = "resultats_recovered"

LANG_EN = "en"
LANG_FR = "fr"

MODE_RECOVERED = "recovered"
MODE_FR_ONLY = "fr_only"
MODE_FULL = "full"

ARTICLE_HEADER_RE = re.compile(r"^------ (?P<article>.+?) ------\s*$")
CATEGORY_RE = re.compile(r"^\[INFO\] \[CATEGORY\] (?P<category>.+?)\s*$")

RAW_RE = re.compile(r"^\[INFO\] \[(?P<lang>EN|FR)\] Raw:\s*(?P<raw>.*)$")

TOKEN_ESTIMATE_RE = re.compile(r"^\[TOKEN\] Estimated input tokens:\s*(?P<tokens>\d+)\s*$")

OPENAI_CALL_RE = re.compile(
    r"^\[INFO\] OpenAI call \| model=(?P<model>[^,]+), "
    r"lang=(?P<lang>[^,]+), retry_level=(?P<retry_level>\d+), "
    r"max_output_tokens=(?P<max_output_tokens>\d+), reasoning=(?P<reasoning>.+?)\s*$"
)

USAGE_RE = re.compile(
    r"^\[TOKEN\] Usage \| input=(?P<input>\d+|None), "
    r"output=(?P<output>\d+|None), "
    r"reasoning=(?P<reasoning>\d+|None), "
    r"total=(?P<total>\d+|None)\s*$"
)

EXCEL_EN_WRITTEN_RE = re.compile(
    r"^\[INFO\] \[EN\] Results added to Excel for (?P<article>.+?)\s*$"
)
EXCEL_FR_WRITTEN_RE = re.compile(
    r"^\[INFO\] \[FR\] Results added to Excel for (?P<article>.+?)\s*$"
)
BLANK_ROW_WRITTEN_RE = re.compile(
    r"^\[INFO\] Blank row added after (?P<article>.+?)\s*$"
)

START_TIME_RE = re.compile(r"^\[INFO\] Début du traitement : (?P<value>.+?)\s*$")
COST_BEFORE_RE = re.compile(r"^\[INFO\] OpenAI cost before run: \$(?P<value>[0-9.]+)\s*$")
COST_AFTER_RE = re.compile(r"^\[INFO\] OpenAI cost after run: \$(?P<value>[0-9.]+)\s*$")

PIPELINE_LOG_PREFIX = "pipeline_"
PIPELINE_LOG_SUFFIX = ".log"


def is_pipeline_log(filename: str) -> bool:
    return (
        filename.startswith(PIPELINE_LOG_PREFIX)
        and filename.endswith(PIPELINE_LOG_SUFFIX)
        and os.path.isfile(os.path.join(LOG_DIR, filename))
    )
