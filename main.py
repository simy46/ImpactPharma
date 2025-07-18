import os
from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.api_manager import OpenAIClient
from core.response_parser import ResponseParser
from core.excel_writer import ExcelWriter
from core.log_manager import LogManager

PDF_DIR = "pdfs"
EXCEL_TEMPLATE_PATH = "outputs/resultats.xlsx"

lg = LogManager()
pm_fr = PromptManager("fr")
pm_en = PromptManager("en")
api = OpenAIClient(logger=lg)
rp = ResponseParser()
writer = ExcelWriter(EXCEL_TEMPLATE_PATH)

pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
categories_fr = pm_fr.get_categories()
categories_en = pm_en.get_categories()

for pdf_path in pdf_files:
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    lg.write("", f"\n\n------ {pdf_name} ------")

    try:
        text = PDFLoader.extract_text(pdf_path)
        lg.write("info", "Texte extrait du pdf")
    except Exception as e:
        lg.write("error", f"Extraction échouée pour {pdf_name} : {e}")
        continue

    # french version
    responses_fr = {}
    for category in categories_fr:
        try:
            lg.write("info", f"[FR] Catégorie : {category}")
            prompt_fr = pm_fr.build_prompt(text, category)
            system_prompt_fr = pm_fr.get_system_prompt()
            raw_fr = api.ask(system_prompt_fr, prompt_fr)
            lg.write("info", f"Réponse brute FR : {raw_fr}")
            parsed_fr = rp.parse(raw_fr)
            responses_fr.update(parsed_fr)
            lg.write("info", f"Réponses parsés FR : {parsed_fr}")
        except Exception as e:
            lg.write("error", f"[FR] Erreur dans la catégorie '{category}' pour {pdf_name} : {e}")

    try:
        writer.insert_row(pdf_name + " (FR)", responses_fr)
        lg.write("info", f"[FR] Résultats ajoutés dans l'Excel pour {pdf_name}")
    except Exception as e:
        lg.write("error", f"[FR] Écriture Excel échouée pour {pdf_name} : {e}")

    # english version
    responses_en = {}
    for category in categories_en:
        try:
            lg.write("info", f"[EN] Category: {category}")
            prompt_en = pm_en.build_prompt(text, category)
            system_prompt_en = pm_en.get_system_prompt()
            raw_en = api.ask(system_prompt_en, prompt_en)
            lg.write("info", f"Raw response EN: {raw_en}")
            parsed_en = rp.parse(raw_en)
            responses_en.update(parsed_en)
            lg.write("info", f"Parsed Responses EN: {parsed_en}")
        except Exception as e:
            lg.write("error", f"[EN] Error in category '{category}' for {pdf_name} : {e}")

    try:
        writer.insert_row(pdf_name + " (EN)", responses_en)
        lg.write("info", f"[EN] Results added to Excel for {pdf_name}")
    except Exception as e:
        lg.write("error", f"[EN] Excel write failed for {pdf_name} : {e}")

lg.write("success", "\nTous les fichiers ont été traités.")
