import os
from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.worksheet import Worksheet
from datetime import datetime

class ExcelWriter:
    def __init__(self, filepath: str = "outputs/template_resultats.xlsx") -> None:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template Excel introuvable : {filepath}")
        self.filepath = filepath
        self.workbook: Workbook = load_workbook(filepath)
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
        while self.sheet.cell(row=next_row, column=1).value:  # find the next empty row
            next_row += 1

        self.sheet.cell(row=next_row, column=1, value=pdf_name)
        self.sheet.cell(row=next_row, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        for qid, answer in responses.items():
            col_idx = self.header_map.get(qid)
            if col_idx:
                if isinstance(answer, list):
                    answer = "; ".join(str(item) for item in answer)
                self.sheet.cell(row=next_row, column=col_idx, value=answer)

        self.workbook.save(self.filepath)