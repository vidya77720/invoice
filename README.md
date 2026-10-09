# AI Invoice & Expense Intelligence System

A complete Python-based AI-powered invoice processing system that automatically extracts, validates, categorizes, and analyzes invoices.

## Features

- **AI Invoice Extraction**: Automatic data extraction from PDF/image invoices
- **OCR Support**: Process scanned invoices using Tesseract OCR
- **Expense Categorization**: Intelligent categorization into predefined categories
- **Anomaly Detection**: Detect duplicates, unusual amounts, and potential issues
- **Vendor Intelligence**: Track vendor analytics and spending patterns
- **AI Assistant**: Natural language queries about expenses
- **Professional Dashboard**: Streamlit-based SaaS-style dashboard
- **Reports**: Generate PDF and Excel reports

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: Streamlit
- **Validation**: Pydantic
- **PDF Processing**: PyMuPDF
- **OCR**: Tesseract
- **Analytics**: Pandas, Plotly
- **Reports**: ReportLab, openpyxl
- **AI**: LLM API (OpenAI/Anthropic)
- **Storage**: JSON files (No database)

## Installation

### Prerequisites

1. Python 3.11 or higher
2. Tesseract OCR (for scanned PDFs)
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Mac: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

### Setup

1. Clone the repository:
```bash
cd ai-invoice-intelligence
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
```

Edit `.env` and add your LLM API key:
```
OPENAI_API_KEY=your_key_here
# or
ANTHROPIC_API_KEY=your_key_here
```

5. Update Tesseract path in `.env` (Windows):
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

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

## Project Structure

```
ai-invoice-intelligence/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic
│   ├── storage/             # JSON storage layer
│   ├── schemas/             # Pydantic models
│   └── core/                # Configuration
├── frontend/
│   └── app.py              # Streamlit dashboard
├── uploads/                # Uploaded invoices
├── processed/              # Processed files
├── data/                   # JSON data files
├── reports/                # Generated reports
└── tests/                  # Test files
```

## API Endpoints

- `POST /api/invoices/upload` - Upload invoice
- `GET /api/invoices` - List all invoices
- `GET /api/invoices/{id}` - Get invoice details
- `PUT /api/invoices/{id}` - Update invoice
- `POST /api/invoices/{id}/approve` - Approve invoice
- `POST /api/invoices/{id}/reject` - Reject invoice
- `GET /api/analytics/summary` - Get analytics summary
- `GET /api/vendors` - Get vendor data
- `GET /api/anomalies` - Get anomalies
- `POST /api/assistant/query` - AI assistant query
- `POST /api/reports/monthly` - Generate monthly report

## Development Phases

- ✅ Phase 1: Project setup + JSON storage + FastAPI + Streamlit
- ✅ Phase 2: Invoice upload + PDF extraction + OCR
- ✅ Phase 3: AI extraction + Pydantic validation
- ✅ Phase 4: Duplicate detection + validation + categorization + anomaly detection
- ✅ Phase 5: Dashboard + invoice review + vendor analytics
- ✅ Phase 6: AI Expense Assistant + reports
- ✅ Phase 7: Testing + UI polish + README

## Testing

Run the test suite:
```bash
pytest tests/test_services.py -v
```

## Usage

1. **Upload Invoice**: Go to "Upload Invoice" page and upload PDF/image invoices
2. **Review Processed Data**: Check "Invoices" page to see extracted data
3. **Review Queue**: Approve or reject invoices in "Review Queue"
4. **Analytics**: View spending patterns in "Analytics" page
5. **Vendor Intelligence**: Track vendor performance in "Vendors" page
6. **AI Assistant**: Ask natural language questions about expenses
7. **Reports**: Generate PDF/Excel reports in "Reports" page

## Key Features Explained

### AI Invoice Extraction
- Uses LLM API (OpenAI/Anthropic) to extract structured data from invoices
- Extracts vendor name, invoice number, dates, amounts, line items
- Provides confidence scores for each extraction

### Duplicate Detection
- SHA-256 file hash comparison for exact duplicates
- Vendor + invoice number + date + amount matching for possible duplicates
- Never deletes invoices automatically

### Anomaly Detection
- Detects unusually high amounts
- Identifies tax calculation mismatches
- Flags new/unusual vendors
- Checks for missing important information

### Expense Categorization
- Automatic categorization into 9 predefined categories
- AI-powered category suggestions
- Custom category support

### AI Expense Assistant
- Natural language query processing
- Questions like "How much did we spend on software?"
- Real-time data analysis without guessing

## Security

- File type validation
- File size limits
- Random stored filenames
- Environment variables for API keys
- Safe JSON writes
- No secrets in code

## License

MIT License
