from datetime import datetime
import os
from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.api_manager import OpenAIClient
from core.response_parser import ResponseParser
from core.excel_writer import ExcelWriter
from core.log_manager import LogManager
from core.stats_manager import StatsManager
from params import TOKENS_PER_MINUTE, PDF_DIR, TEMPLATE_PATH

lg = LogManager()
pm = PromptManager()
api = OpenAIClient(logger=lg)
rp = ResponseParser()
writer = ExcelWriter(template_path=TEMPLATE_PATH)
stats = StatsManager(model=api.model, token_limit=TOKENS_PER_MINUTE)  # on récupère le modèle utilisé

stats.start()
lg.write("info", f"Début du traitement : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for pdf_path in os.listdir(PDF_DIR):
    if not pdf_path.endswith(".pdf"):
        continue
    pdf_name = os.path.splitext(pdf_path)[0]
    stats.add_article()
    lg.write("", f"\n\n------ {pdf_name} ------")

    try:
        text = PDFLoader.extract_text(os.path.join(PDF_DIR, pdf_path))
        lg.write("info", "Texte extrait du pdf")
    except Exception as e:
        lg.write("error", f"Extraction échouée pour {pdf_name} : {e}")
        continue

    # ========== Process ==========
    responses_en = {}
    responses_fr = {}
    for category in pm.get_categories():
        lg.write("info", f"[CATEGORY] {category}")

        # --- Analyse EN ---
        system_prompt = pm.get_system_prompt()
        user_prompt = pm.build_prompt(text, category)
        tok_en = api._count_tokens(system_prompt, user_prompt)
        stats.add_tokens(tok_en)

        raw_en = api.ask(system_prompt=system_prompt, user_prompt=user_prompt, tokens_used=tok_en)
        lg.write("info", f"[EN] Raw: {raw_en}")
        parsed_en = rp.parse(raw_en)
        responses_en.update(parsed_en)

        # --- Translates in FR ---
        raw_json_en = rp.to_json_string(parsed_en)
        system_prompt_fr = pm.translate_prompt()
        tok_fr = api._count_tokens(system_prompt_fr, raw_json_en)
        stats.add_tokens(tok_fr)

        raw_fr = api.ask(system_prompt=system_prompt_fr, user_prompt=raw_json_en, tokens_used=tok_fr, lang="fr")
        lg.write("info", f"[FR] Raw: {raw_fr}")
        parsed_fr = rp.parse(raw_fr)
        responses_fr.update(parsed_fr)
            

    try:
        writer.insert_row(pdf_name + " (EN)", responses_en)
        lg.write("info", f"[EN] Results added to Excel for {pdf_name}")

        writer.insert_row(pdf_name + " (FR)", responses_fr)
        lg.write("info", f"[FR] Results added to Excel for {pdf_name}")
    except Exception as e:
        lg.write("error", f"[EN] Excel write failed for {pdf_name} : {e}")

stats.stop()
lg.write("info", f"Tous les fichiers ont été traités : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
lg.write("info", f"Statistiques \n{stats.summary()}")
 