# Data‑Vista

Streamlit app for text analysis and reporting: upload documents, extract keywords and entities, model topics, build a concept graph, generate summaries, and export a clean PDF.

## Features

- Document ingestion: TXT, PDF, DOCX, or pasted text
- NLP: keyword frequency, word cloud, named entities, topic modeling
- Visuals: interactive charts and a concept graph, plus high‑res PNG exports
- Summarization: DistilBART‑based summaries for quick overviews
- Reporting: one‑click PDF export with optional Unicode fonts
- Caching: faster re-runs with persisted resources


## Demo

- Local run instructions below
- Optional hosted demo: add your Space link here once deployed


## Tech stack

- Python 3.11, Streamlit
- spaCy, Transformers, Torch
- Plotly, Matplotlib, NetworkX
- pdfplumber, python‑docx, ReportLab
- pytesseract + Tesseract OCR (optional)


## Quick start (local)

```bash
git clone https://github.com/<your-username>/data-vista.git
cd data-vista

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```


### Optional: system OCR

- Windows: install Tesseract from UB‑Mannheim builds
- Debian/Ubuntu:

```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```


## Project structure

```
.
├─ app.py                  # entrypoint
├─ pages/                  # Streamlit pages (keywords, topics, word cloud, PDF export)
├─ utils/                  # helpers (if present)
├─ requirements.txt
├─ Dockerfile              # for container/Spaces deploys
└─ fonts/                  # optional DejaVu fonts for Unicode PDF (track with Git LFS)
```


## Key pages

- Keyword Frequency: tokenization, stopwords, bar chart, PNG export
- Word Cloud: top‑terms cloud image
- Topic Modeling: LDA/NMF distribution + charts
- Concept Graph: co‑occurrence network with communities
- Export Report (PDF): sanitized text, headers/footers, figures, spacing, and saved charts


## Docker deploy

When base registry access is restricted, use a slim Python base:

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```


## Hugging Face Spaces

- Create a Space with SDK: Docker, hardware: CPU Basic
- Push the repo; set “App file” to app.py if not auto‑detected
- Build logs should show Tesseract and Python deps installed


## Fonts and PDF export

- To avoid missing glyph boxes in PDFs, add DejaVuSans.ttf and DejaVuSans‑Bold.ttf under fonts/, tracked with Git LFS:
git lfs track "fonts/*.ttf"
- Toggle the Unicode font option in the PDF page to enable


## Known limitations

- Very large documents can be slow on CPU Basic
- OCR depends on scan quality; manual edits may be needed
- PNG is raster; increase DPI/scale for print‑quality output


## Roadmap

- GPU‑accelerated summarization
- Multi‑doc comparison and timeline views
- Project save/load and export presets


## Contributing

Issues and PRs are welcome. For major changes, open an issue first to discuss approach.

## License

MIT
