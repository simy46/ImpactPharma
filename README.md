# AI Tool
That answers specific questions on scientific publications (~2500-3000 articles in total).
Automating the process, while keeping great results.
There is a question of optimization, to : 
    - reduce tokens used
    - having clear and better responses
    - lowering the "hallucinations" rate
    - GETTING THE MOST FROM AI

Returns pre-defined excel document with Q/A columns.
Used in a pharma research lab at CHU Sainte-Justine, Montreal to rework their website.

# How to Use the Project

---

## Step 1 – Download the Project

If you received this as a ZIP file, unzip it on your Desktop.

Right-click on the forlder, find 'Open in terminal'

Skip to next step.


If you’re using Git:

On your Desktop, right-click and find 'Open in terminal'

Once openned, run the commands :

```bash
git clone https://github.com/simy46/ImpactPharma.git
cd ImpactPharma
```

---

## Step 2 – Add Your PDFs

Place all the PDF files you want to analyze inside the `/pdfs` folder of the project.

These are the pdfs that will be used : Chose the ones that YOU want.

Example: `ImpactPharma/pdfs/*.pdf`

---

## Step 3 – Run on Windows

Make sure you have **Python 3.10 or newer** installed.  

Then on the terminal

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Output

After the script finishes, results will be saved in:

- `/outputs/resultats.xlsx`            : Excel with all extracted answers  
- `/logs/pipeline_YYYYMMDD_HHMMSS.log` : detailed processing log for each PDF

---

## Notes

- Don't edit the Excel file while the script is running.
- If you have questions or errors, share the log file with the developer.
- It will always write inside `/outputs/resultats.xlsx`, if you want to reset copy `/outputs/template_resultats.xlsx`, move the old `resultats.xlsx` and rename the copy `resultats.xlsx` [sorry will simplify this]


# Motivation
This is a work for a research lab at a Montreal hospital (the most popular if you ask me). I am happy to help them achieve their goal.

## It is just a gpt-4 wrapper
I am no llm dev (yet : 10/07/2025), but I'm leaning towards that path more and more.
I do love research and might get a paper out of this project.

https://impactpharmacie.org/index.php?p=greeter.php

# Simple Approach (abstraction)
```
for pdf in pdf_files:
    text = PDFLoader.extract_text(pdf)
    responses = {}

    for category in categories:
        prompt = PromptManager.build_prompt(category, text)
        answer_raw = APIManager.ask(prompt)
        parsed = ResponseParser.parse(answer_raw)
        responses.update(parsed)

    ExcelWriter.insert_row(pdf_name, responses)
```