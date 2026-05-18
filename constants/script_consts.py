## ===============================================================================================================
## DO NOT CHANGE ANY OF THESE CONSTS!!!!!!!!
## ===============================================================================================================

import os

PDF_DIR = "pdfs"
RESULTS_DIR = "results"
RESULTS_BATCH = "IP63"
TEMPLATE_FILENAME = "template_resultats.xlsx"
TEMPLATE_PATH = os.path.join(RESULTS_DIR, TEMPLATE_FILENAME)
SCHEMA_PATH = "config/questions.yaml"
REG_EX = r'("Q\d+"\s*:\s*")([^"]*)$'
OPENAI_API_KEY = "OPENAI_API_KEY" # got ur ass
METHODOLOGY_CATEGORY = "Methodology"
OUTCOMES_CATEGORY = "Outcomes"
QUESTION_8 = "Q8"
QUESTION_9 = "Q9"


def get_results_batch_dir(batch: str = RESULTS_BATCH) -> str:
    return os.path.join(RESULTS_DIR, batch)


def get_next_iteration_dir(batch: str = RESULTS_BATCH) -> str:
    batch_dir = get_results_batch_dir(batch)
    os.makedirs(batch_dir, exist_ok=True)

    iteration_count = sum(
        1 for entry in os.scandir(batch_dir)
        if entry.is_dir() and entry.name.endswith(" iteration")
    )
    next_iteration = iteration_count + 1
    suffix = "ere" if next_iteration == 1 else "e"

    return os.path.join(batch_dir, f"{next_iteration}{suffix} iteration")
