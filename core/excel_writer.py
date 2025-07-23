import os
from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.worksheet import Worksheet
from datetime import datetime
import shutil


class ExcelWriter:
    def __init__(self, template_path: str = "outputs/template_resultats.xlsx", output_dir: str = "outputs") -> None:
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template Excel introuvable : {template_path}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mmin%Ss")
        filename = f"resultats_{timestamp}.xlsx"
        self.output_path = os.path.join(output_dir, filename)

        shutil.copy(template_path, self.output_path)

        self.workbook: Workbook = load_workbook(self.output_path)
        sheet = self.workbook.active
        if sheet is None:
            raise ValueError("Aucune feuille active trouvée dans le fichier Excel.")
        self.sheet: Worksheet = sheet

        self.header_map: dict[str, int] = {
            str(cell.value): idx + 1
            for idx, cell in enumerate(self.sheet[1])
            if cell.value
        }

    def insert_row(self, pdf_name: str, responses: dict[str, str]) -> None:
        next_row = 2  # starting after header
        while self.sheet.cell(row=next_row, column=1).value:
            next_row += 1

        self.sheet.cell(row=next_row, column=1, value=pdf_name)
        self.sheet.cell(row=next_row, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        for qid, answer in responses.items():
            col_idx = self.header_map.get(qid)
            if col_idx:
                if isinstance(answer, list):
                    answer = "; ".join(str(item) for item in answer)
                self.sheet.cell(row=next_row, column=col_idx, value=answer)

        self.workbook.save(self.output_path)
