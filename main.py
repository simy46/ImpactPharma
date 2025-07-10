import os
from openai import OpenAI
from dotenv import load_dotenv
from PyPDF2 import PdfReader

PROMPT = ""

QUESTIONS = [

]

PDF_PATHS = [
    "pdfs/Abou 2025.pdf",
    "pdfs/Adisa 2024.pdf",
    "pdfs/Benny 2024.pdf"
]

def extract_text_from_pdf(pdf_path : str) -> list[str]:
    with open(pdf_path, 'rb') as pdf:
        reader = PdfReader(pdf)
        text = []
        for page in reader.pages:
            text.append(page.extract_text())

        print(text)
        return text

def create_excel():
    pass


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {api_key}")

    text1 = extract_text_from_pdf(pdf_path)
    for pdf_path in PDF_PATHS:
        print(f"Extracting text from {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted text: {text[:2]}...")
    # client = OpenAI()
    # client.api_key = os.environ["OPENAI_API_KEY"]

    # response = client.responses.create(
    #     model="gpt-4-0125-preview",
    #     input="Write a one-sentence bedtime story about a unicorn."
    # )

    # print(response.output_text)
    pass