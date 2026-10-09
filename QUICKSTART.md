# Quick Start Guide

## Prerequisites Check

- Python 3.11+ installed ✅
- Tesseract OCR installed (optional, for scanned PDFs)

## Installation Steps

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
```

Edit `.env` file:
- Add your OpenAI API key or Anthropic API key
- (Windows) Set Tesseract path if using OCR

## Running the Application

### Start Backend API
```bash
python -m app.main
```
API will be available at: http://localhost:8000

### Start Frontend Dashboard
```bash
streamlit run frontend/app.py
```
Dashboard will be available at: http://localhost:8501

## First Use

1. Open http://localhost:8501 in your browser
2. Navigate to "Upload Invoice"
3. Upload a PDF or image invoice
4. Wait for AI processing
5. Review extracted data in "Invoices" page
6. Approve/reject in "Review Queue"
7. Ask questions in "AI Assistant"
8. Generate reports in "Reports"

## Troubleshooting

### API Not Connecting
- Ensure backend is running on port 8000
- Check for firewall issues

### OCR Not Working
- Install Tesseract OCR
- Update TESSERACT_PATH in .env file

### AI Extraction Failing
- Check API key in .env file
- Ensure you have API credits

### Import Errors
- Ensure all dependencies are installed
- Check Python version (3.11+)

## Testing

Run tests:
```bash
pytest tests/test_services.py -v
```

## Support

For issues or questions, check the main README.md file.
