# AI Tool
That summarizes + answers specific questions on scientific publications (~2500-3000 articles in total).
There is a question of optimization, to : 
    - reduce tokens used
    - having clear and better responses
    - lowering the "halucinations" rate
    - GETTING THE MOST FROM IT

Returns pre-defined excel document with Q/A columns.
Used in a pharma research lab at CHU Sainte-Justine, Montreal to rework their website.

# Motivation
This is a work for a research lab at a Montreal hospital (the most popular if you ask me). I am happy to help them achieve their goal.

## It is just a gpt-4 wrapper
I am no llm dev (yet : 10/07/2025), but I'm leaning towards that path more and more.
I do love research and might get a paper out of this project.

https://impactpharmacie.org/index.php?p=greeter.php

# APPROACH
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