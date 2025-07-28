from datetime import datetime
import os
from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.api_manager import OpenAIClient
from core.response_parser import ResponseParser
from core.excel_writer import ExcelWriter
from core.log_manager import LogManager
from core.stats_manager import StatsManager  # <— nouveau

PDF_DIR = "pdfs"
TEMPLATE_PATH = "outputs/template_resultats.xlsx"

lg = LogManager()
pm_fr = PromptManager("fr")
pm_en = PromptManager("en")
api = OpenAIClient(logger=lg)
rp = ResponseParser()
writer = ExcelWriter(template_path=TEMPLATE_PATH)
stats = StatsManager(model=api.model, token_limit=450000)  # on récupère le modèle utilisé

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

    # ========== version FR ==========
    responses_fr = {}
    for category in pm_fr.get_categories():
        lg.write("info", f"[FR] Catégorie : {category}")
        system_fr = pm_fr.get_system_prompt()
        prompt_fr = pm_fr.build_prompt(text, category)
        tok = api._count_tokens(system_fr, prompt_fr)
        stats.add_tokens(tok)
        raw_fr = api.ask(system_fr, prompt_fr)
        lg.write("info", f"Réponse brute FR : {raw_fr}")
        parsed_fr = rp.parse(raw_fr)
        responses_fr.update(parsed_fr)

    try:
        writer.insert_row(pdf_name + " (FR)", responses_fr)
        lg.write("info", f"[FR] Résultats ajoutés dans l'Excel pour {pdf_name}")
    except Exception as e:
        lg.write("error", f"[FR] Écriture Excel échouée pour {pdf_name} : {e}")

    # ========== version EN ==========
    responses_en = {}
    for category in pm_en.get_categories():
        lg.write("info", f"[EN] Category: {category}")
        system_en = pm_en.get_system_prompt()
        prompt_en = pm_en.build_prompt(text, category)

        tok = api._count_tokens(system_en, prompt_en)
        stats.add_tokens(tok)

        raw_en = api.ask(system_en, prompt_en)
        lg.write("info", f"Raw response EN: {raw_en}")
        parsed_en = rp.parse(raw_en)
        responses_en.update(parsed_en)

    try:
        writer.insert_row(pdf_name + " (EN)", responses_en)
        lg.write("info", f"[EN] Results added to Excel for {pdf_name}")
    except Exception as e:
        lg.write("error", f"[EN] Excel write failed for {pdf_name} : {e}")

stats.stop()
lg.write("info", f"Tous les fichiers ont été traités : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
lg.write("info", f"Statistiques \n{stats.summary()}")
