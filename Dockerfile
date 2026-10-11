FROM python:3.11-slim

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure start.sh has LF line endings and is executable
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# Environment settings
ENV PORT=8501
ENV API_PORT=8000
ENV API_HOST=127.0.0.1
ENV API_URL=http://127.0.0.1:8000

# Streamlit port
EXPOSE 8501

CMD ["./start.sh"]
