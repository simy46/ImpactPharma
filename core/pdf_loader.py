import pdfplumber

TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "intersection_tolerance": 3
}

class PDFLoader:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text += f"\n{'='*60}\nPage {page_num}\n{'='*60}\n\n"
                tables = page.extract_tables(table_settings=TABLE_SETTINGS)
                
                if tables:
                    for i, table in enumerate(tables, 1):
                        text += f"\n--- TABLE {i} ---\n"
                        text += f"Rows: {len(table)} | Columns: {len(table[0]) if table and table[0] else 0}\n\n"
                        
                        for row_idx, row in enumerate(table):
                            if row and any(cell for cell in row):
                                cleaned = [str(cell).strip() if cell and str(cell).strip() else "" for cell in row]
                                if row_idx == 0:
                                    text += "HEADER: "
                                text += " | ".join(cleaned) + "\n"
                        
                        text += "\n--- END TABLE ---\n\n"
                
                page_text = page.extract_text(layout=True)
                if page_text:
                    text += PDFLoader._clean_whitespace(page_text) + "\n"
        
        return text.strip()
    
    @staticmethod
    def _clean_whitespace(text: str) -> str:
        lines = text.split('\n')
        cleaned = []
        empty_count = 0
        
        for line in lines:
            if line.strip():
                cleaned.append(line.rstrip())
                empty_count = 0
            else:
                empty_count += 1
                if empty_count <= 1:
                    cleaned.append("")
        
        return "\n".join(cleaned)
