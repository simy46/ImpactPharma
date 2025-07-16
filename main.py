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
pm = PromptManager()
api = OpenAIClient(logger=lg)
rp = ResponseParser()
writer = ExcelWriter(EXCEL_TEMPLATE_PATH)

pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
categories = pm.get_categories()

for pdf_path in pdf_files:
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    lg.write("", f"\n\n------ {pdf_name} ------")

    try:
        text = PDFLoader.extract_text(pdf_path)
        lg.write("info", f"Texte extrait du pdf")
    except Exception as e:
        lg.write("error", f"Extraction échouée pour {pdf_name} : {e}")
        continue

    responses = {}
    for category in categories:
        try:
            lg.write("info", f"Catégorie : {category}")
            user_prompt = pm.build_prompt(text, category)
            system_prompt = pm.get_system_prompt()
            raw = api.ask(system_prompt, user_prompt)
            parsed = rp.parse(raw)
            responses.update(parsed)
        except Exception as e:
            lg.write("error", f"Échec pour catégorie '{category}' dans {pdf_name} : {e}")

    try:
        writer.insert_row(pdf_name, responses)
        lg.write("info", f"Résultats ajoutés dans l'Excel pour {pdf_name}")
    except Exception as e:
        lg.write("error", f"Écriture Excel échouée pour {pdf_name} : {e}")

lg.write("success", "\nTous les fichiers ont été traités.")
