FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps: Tesseract OCR (+ English), fonts if needed later
RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Python deps
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run Streamlit
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
