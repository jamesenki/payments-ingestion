"""
Data models for payment transactions using Pydantic for validation.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal
import uuid


class Transaction(BaseModel):
    """
    Payment transaction model matching the database schema.
    """
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_timestamp: datetime = Field(default_factory=datetime.now)
    ingestion_timestamp: Optional[datetime] = None
    processing_timestamp: Optional[datetime] = None
    amount: Decimal = Field(...)  # Amount (may be negative/zero for compliance testing)
    currency: str = Field(..., min_length=3, max_length=3)
    payment_method: str
    payment_status: str
    customer_id: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_country: Optional[str] = Field(None, min_length=2, max_length=2)
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_type: Optional[str] = None
    channel: Optional[str] = None
    device_type: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    
    # Compliance tracking (not in database, for simulator use)
    compliance_violations: List[str] = Field(default_factory=list)
    violation_severity: Optional[str] = None  # low, medium, high, critical
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }
        validate_assignment = True
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate ISO 4217 currency code."""
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR', 'BRL']
        if v not in valid_currencies:
            # Allow invalid for compliance testing
            pass
        return v
    
    @validator('payment_status')
    def validate_status(cls, v):
        """Validate payment status."""
        valid_statuses = ['pending', 'completed', 'failed', 'cancelled', 'refunded']
        if v not in valid_statuses:
            # Allow invalid for compliance testing
            pass
        return v
    
    @validator('customer_country')
    def validate_country_code(cls, v):
        """Validate ISO 3166-1 alpha-2 country code."""
        if v is None:
            return v
        if len(v) != 2:
            # Allow invalid for compliance testing
            pass
        return v
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = self.dict()
        # Convert datetime and Decimal for JSON
        if isinstance(data.get('transaction_timestamp'), datetime):
            data['transaction_timestamp'] = data['transaction_timestamp'].isoformat()
        if isinstance(data.get('ingestion_timestamp'), datetime):
            data['ingestion_timestamp'] = data['ingestion_timestamp'].isoformat()
        if isinstance(data.get('processing_timestamp'), datetime):
            data['processing_timestamp'] = data['processing_timestamp'].isoformat()
        if isinstance(data.get('amount'), Decimal):
            data['amount'] = float(data['amount'])
        return data
    
    def to_event_hub_format(self) -> Dict:
        """Convert to format suitable for Event Hub."""
        return self.to_dict()

