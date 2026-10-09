import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.invoice_service import invoice_service
from app.services.validation_service import validation_service
from app.services.category_service import category_service
from app.core.config import settings

def test_invoice_service_initialization():
    """Test that invoice service initializes correctly"""
    assert invoice_service is not None
    assert hasattr(invoice_service, 'validate_file')
    assert hasattr(invoice_service, 'generate_invoice_id')

def test_invoice_id_generation():
    """Test invoice ID generation"""
    invoice_id = invoice_service.generate_invoice_id()
    assert invoice_id.startswith("INV-")
    assert len(invoice_id) == 12  # INV- + 8 characters

def test_file_validation():
    """Test file validation"""
    # Valid file
    is_valid, message = invoice_service.validate_file("test.pdf", 1024, b"fake content")
    assert is_valid == True
    
    # Invalid extension
    is_valid, message = invoice_service.validate_file("test.exe", 1024, b"fake content")
    assert is_valid == False
    assert "Invalid file type" in message
    
    # File too large
    is_valid, message = invoice_service.validate_file("test.pdf", 20000000, b"fake content")
    assert is_valid == False
    assert "too large" in message
    
    # Empty file
    is_valid, message = invoice_service.validate_file("test.pdf", 0, b"")
    assert is_valid == False
    assert "empty" in message

def test_validation_service():
    """Test validation service"""
    # Valid invoice data
    valid_invoice = {
        "vendor_name": "Test Vendor",
        "invoice_number": "INV-001",
        "invoice_date": "2026-09-21",
        "total_amount": 1000.0,
        "subtotal": 900.0,
        "tax_amount": 100.0,
        "currency": "INR"
    }
    
    result = validation_service.validate_invoice(valid_invoice)
    assert result.is_valid == True
    assert len(result.errors) == 0
    
    # Missing required fields
    invalid_invoice = {
        "vendor_name": None,
        "invoice_number": None,
        "total_amount": None
    }
    
    result = validation_service.validate_invoice(invalid_invoice)
    assert result.is_valid == False
    assert len(result.errors) > 0

def test_category_service():
    """Test category service"""
    # Test category summary
    summary = category_service.get_category_summary()
    assert "categories" in summary
    assert "total_amount" in summary
    assert "total_invoices" in summary

def test_config_settings():
    """Test configuration settings"""
    assert settings.EXPENSE_CATEGORIES is not None
    assert len(settings.EXPENSE_CATEGORIES) > 0
    assert "Software & Technology" in settings.EXPENSE_CATEGORIES
    assert "Other" in settings.EXPENSE_CATEGORIES
    
    assert settings.INVOICE_STATUSES is not None
    assert "pending" in settings.INVOICE_STATUSES
    assert "approved" in settings.INVOICE_STATUSES

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
