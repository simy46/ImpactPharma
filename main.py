import os
from core.pdf_loader import PDFLoader
from core.prompt_manager import PromptManager
from core.api_manager import OpenAIClient
from core.response_parser import ResponseParser
from core.excel_writer import ExcelWriter 

PDF_DIR = "pdfs"
EXCEL_TEMPLATE_PATH = "outputs/resultats.xlsx"

pm = PromptManager()
api = OpenAIClient()
rp = ResponseParser()
writer = ExcelWriter(EXCEL_TEMPLATE_PATH)

pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
categories = pm.get_categories()

for pdf_path in pdf_files:
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"\n[INFO] Traitement de : {pdf_name}")
    
    try:
        text = PDFLoader.extract_text(pdf_path)
    except Exception as e:
        print(f"[ERREUR] Extraction échouée pour {pdf_name} : {e}")
        continue

    responses = {}
    for category in categories:
        try:
            user_prompt = pm.build_prompt(text, category)
            system_prompt = pm.get_system_prompt()
            print(f"[INFO] Catégorie : {category}")
            raw = api.ask(system_prompt, user_prompt)
            parsed = rp.parse(raw)
            responses.update(parsed)
        except Exception as e:
            print(f"[ERREUR] Échec pour catégorie '{category}' dans {pdf_name} : {e}")

    try:
        writer.insert_row(pdf_name, responses)
    except Exception as e:
        print(f"[ERREUR] Écriture Excel échouée pour {pdf_name} : {e}")

print("\n Tous les fichiers ont été traités.")
