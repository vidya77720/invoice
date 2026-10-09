from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date
from decimal import Decimal

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    amount: Optional[Decimal] = None

class InvoiceBase(BaseModel):
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(default="INR")
    subtotal: Optional[Decimal] = None
    discount: Optional[Decimal] = Field(default=Decimal('0'))
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    line_items: Optional[List[LineItem]] = None
    category: Optional[str] = None
    confidence_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    status: str = Field(default="pending")
    
    @field_validator('total_amount')
    @classmethod
    def validate_total_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Total amount cannot be negative')
        return v
    
    @field_validator('subtotal')
    @classmethod
    def validate_subtotal(cls, v):
        if v is not None and v < 0:
            raise ValueError('Subtotal cannot be negative')
        return v

class InvoiceCreate(InvoiceBase):
    file_path: str
    file_hash: str
    file_name: str
    file_size: int

class InvoiceUpdate(BaseModel):
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    subtotal: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    line_items: Optional[List[LineItem]] = None
    category: Optional[str] = None
    status: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: str
    file_path: str
    file_hash: str
    file_name: str
    file_size: int
    duplicate_status: str = Field(default="NO_DUPLICATE")
    anomaly_flags: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}

class InvoiceValidation(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
