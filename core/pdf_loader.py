import PyPDF2

class PDFLoader:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        text = ""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
