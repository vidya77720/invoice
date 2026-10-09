import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    PROCESSED_DIR = BASE_DIR / "processed"
    DATA_DIR = BASE_DIR / "data"
    REPORTS_DIR = BASE_DIR / "reports"
    
    # File settings
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB default
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "pdf,png,jpg,jpeg").split(","))
    
    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # OCR Settings
    TESSERACT_PATH = os.getenv("TESSERACT_PATH")
    
    # API Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Expense Categories
    EXPENSE_CATEGORIES = [
        "Software & Technology",
        "Office Supplies",
        "Travel",
        "Marketing",
        "Professional Services",
        "Utilities",
        "Equipment",
        "Logistics",
        "Other"
    ]
    
    # Invoice Statuses
    INVOICE_STATUSES = [
        "pending",
        "processing",
        "review_required",
        "approved",
        "rejected"
    ]
    
    # Duplicate Statuses
    DUPLICATE_STATUSES = [
        "NO_DUPLICATE",
        "POSSIBLE_DUPLICATE",
        "EXACT_DUPLICATE"
    ]

settings = Settings()
