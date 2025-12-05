# Payment Data Simulator - Detailed Design Review

## Overview

This document provides a detailed review of the Payment Data Simulator design, with special focus on **data variability** and **out-of-compliance scenarios** for comprehensive testing.

## Database Schema Alignment

### NormalizedTransactions Fields
```python
{
    "transaction_id": str,              # Unique identifier
    "transaction_timestamp": datetime,   # When transaction occurred
    "ingestion_timestamp": datetime,    # When ingested (auto)
    "processing_timestamp": datetime,    # When processed (auto)
    "amount": decimal,                   # Must be > 0
    "currency": str,                     # ISO 4217, 3 chars
    "payment_method": str,              # credit_card, debit_card, etc.
    "payment_status": str,              # pending, completed, failed, cancelled, refunded
    "customer_id": str,                 # Optional
    "customer_email": str,              # Optional
    "customer_country": str,            # ISO 3166-1 alpha-2, 2 chars
    "merchant_id": str,                 # Optional
    "merchant_name": str,               # Optional
    "merchant_category": str,           # Optional
    "transaction_type": str,            # Optional
    "channel": str,                     # Optional
    "device_type": str,                 # Optional
    "metadata": dict                    # JSONB - flexible
}
```

## Variability Requirements

### 1. Transaction Amount Variability

**Normal Distribution (Most Common)**
- Mean: $50-200 (configurable)
- Standard deviation: $20-100
- Represents typical consumer spending

**Uniform Distribution**
- Flat distribution across min-max range
- Good for stress testing

**Exponential Distribution**
- Many small transactions, few large ones
- Realistic for retail scenarios

**Bimodal Distribution**
- Two peaks (e.g., $10-30 and $200-500)
- Represents different customer segments

**Out-of-Compliance Amounts:**
- ❌ **Negative amounts** (should be rejected)
- ❌ **Zero amounts** (should be rejected)
- ❌ **Extremely large amounts** (> $1M, may trigger AML)
- ❌ **Suspicious round numbers** (e.g., $10,000.00 - potential structuring)

### 2. Payment Method Variability

**Distribution Configuration:**
```yaml
payment_methods:
  credit_card: 0.50      # 50% of transactions
  debit_card: 0.30       # 30%
  bank_transfer: 0.10    # 10%
  digital_wallet: 0.05   # 5%
  cryptocurrency: 0.03   # 3%
  cash_equivalent: 0.02  # 2%
```

**Out-of-Compliance Scenarios:**
- ❌ **Invalid payment method** (e.g., "invalid_method")
- ❌ **Missing payment method** (null/empty)
- ❌ **Unsupported payment method** (e.g., "bitcoin" when not supported)

### 3. Payment Status Variability

**Realistic Distribution:**
```yaml
payment_status:
  completed: 0.85        # 85% succeed
  failed: 0.10           # 10% fail
  pending: 0.03          # 3% pending
  cancelled: 0.01        # 1% cancelled
  refunded: 0.01         # 1% refunded
```

**Out-of-Compliance Scenarios:**
- ❌ **Invalid status** (e.g., "processing" - not in allowed list)
- ❌ **Status mismatch** (e.g., completed transaction with failed amount)
- ❌ **Refunded without original transaction**

### 4. Currency Variability

**Common Currencies:**
```yaml
currencies:
  USD: 0.60              # 60% USD
  EUR: 0.20              # 20% EUR
  GBP: 0.10              # 10% GBP
  JPY: 0.05              # 5% JPY
  CAD: 0.03              # 3% CAD
  AUD: 0.02              # 2% AUD
```

**Out-of-Compliance Scenarios:**
- ❌ **Invalid currency code** (e.g., "XXX", "123")
- ❌ **Wrong length** (e.g., "US" or "USDD")
- ❌ **Unsupported currency** (e.g., "BTC" if not supported)

### 5. Temporal Variability

**Time Patterns:**
```yaml
temporal_patterns:
  business_hours: 0.70   # 70% during 9 AM - 5 PM
  evening: 0.20          # 20% 5 PM - 10 PM
  night: 0.05            # 5% 10 PM - 6 AM
  weekend: 0.05          # 5% weekends
  
  timezone_distribution:
    UTC-5: 0.40          # US East
    UTC-8: 0.30          # US West
    UTC+0: 0.20          # UK
    UTC+9: 0.10          # Japan
```

**Out-of-Compliance Scenarios:**
- ❌ **Future timestamps** (transaction in the future)
- ❌ **Very old timestamps** (e.g., 10 years ago)
- ❌ **Invalid timezone** (malformed timestamp)
- ❌ **Out-of-order timestamps** (ingestion before transaction)

### 6. Geographic Variability

**Country Distribution:**
```yaml
countries:
  US: 0.50               # 50% United States
  GB: 0.15               # 15% United Kingdom
  CA: 0.10               # 10% Canada
  AU: 0.08               # 8% Australia
  DE: 0.05               # 5% Germany
  FR: 0.04               # 4% France
  JP: 0.03               # 3% Japan
  other: 0.05            # 5% other countries
```

**Out-of-Compliance Scenarios:**
- ❌ **Invalid country code** (e.g., "XX", "123")
- ❌ **Sanctioned countries** (e.g., "KP", "IR" - if blocked)
- ❌ **Mismatched currency/country** (e.g., USD from Japan)

### 7. Customer Data Variability

**Email Patterns:**
- Valid emails: `user@domain.com`
- Invalid emails: `invalid-email`, `@domain.com`, `user@`
- Missing emails: null/empty

**Customer ID Patterns:**
- Valid: UUID format, numeric IDs
- Invalid: empty, too long, special characters
- Duplicate: same customer_id with different emails

**Out-of-Compliance Scenarios:**
- ❌ **Invalid email format**
- ❌ **Missing required customer data**
- ❌ **PII in wrong fields** (e.g., SSN in customer_id)

### 8. Merchant Data Variability

**Merchant Categories:**
```yaml
merchant_categories:
  retail: 0.30
  food_beverage: 0.20
  travel: 0.15
  entertainment: 0.10
  healthcare: 0.08
  education: 0.07
  other: 0.10
```

**Out-of-Compliance Scenarios:**
- ❌ **High-risk merchant categories** (e.g., gambling, adult)
- ❌ **Missing merchant information**
- ❌ **Invalid merchant IDs**

### 9. Transaction Metadata Variability

**Metadata Fields:**
```python
metadata = {
    "ip_address": str,           # Customer IP
    "user_agent": str,           # Browser/device info
    "card_last4": str,           # Last 4 digits
    "card_brand": str,           # Visa, Mastercard, etc.
    "cvv_provided": bool,        # CVV verification
    "3ds_verified": bool,        # 3D Secure
    "risk_score": float,         # 0.0-1.0
    "fraud_indicators": list,    # List of flags
    "custom_fields": dict        # Additional data
}
```

**Out-of-Compliance Scenarios:**
- ❌ **Missing required metadata** (e.g., no IP address)
- ❌ **Invalid data types** (e.g., string instead of number)
- ❌ **Suspicious patterns** (e.g., same IP for many transactions)

## Compliance Violation Scenarios

### 1. Anti-Money Laundering (AML) Violations

**Structuring Detection:**
- Multiple transactions just under reporting threshold ($10,000)
- Same customer, multiple small transactions in short time
- Round number amounts ($9,999.99 pattern)

**Suspicious Activity:**
- Very large amounts (> $50,000)
- Rapid-fire transactions (100+ in 1 minute)
- Unusual payment method combinations

**Configuration:**
```yaml
compliance_scenarios:
  aml_violations:
    enabled: true
    percentage: 0.02              # 2% of transactions
    patterns:
      - name: "structuring"
        description: "Multiple transactions under threshold"
        frequency: 0.01
      - name: "large_amount"
        description: "Suspiciously large transaction"
        frequency: 0.005
      - name: "rapid_fire"
        description: "Too many transactions too quickly"
        frequency: 0.005
```

### 2. Know Your Customer (KYC) Violations

**Missing Information:**
- No customer_id
- No customer_email
- No customer_country
- Incomplete merchant information

**Invalid Information:**
- Invalid email format
- Invalid country code
- Missing required fields

**Configuration:**
```yaml
compliance_scenarios:
  kyc_violations:
    enabled: true
    percentage: 0.03              # 3% of transactions
    patterns:
      - name: "missing_customer_id"
        frequency: 0.01
      - name: "invalid_email"
        frequency: 0.01
      - name: "missing_country"
        frequency: 0.01
```

### 3. PCI DSS Violations

**Card Data Issues:**
- Missing card_last4 in metadata
- Invalid card brand
- Missing CVV verification flag
- Missing 3DS verification

**Configuration:**
```yaml
compliance_scenarios:
  pci_violations:
    enabled: true
    percentage: 0.01              # 1% of transactions
    patterns:
      - name: "missing_card_data"
        frequency: 0.005
      - name: "invalid_card_brand"
        frequency: 0.005
```

### 4. Data Quality Violations

**Schema Violations:**
- Invalid data types
- Missing required fields
- Out-of-range values
- Constraint violations

**Configuration:**
```yaml
compliance_scenarios:
  data_quality_violations:
    enabled: true
    percentage: 0.05              # 5% of transactions
    patterns:
      - name: "negative_amount"
        frequency: 0.01
      - name: "zero_amount"
        frequency: 0.01
      - name: "invalid_currency"
        frequency: 0.01
      - name: "invalid_status"
        frequency: 0.01
      - name: "future_timestamp"
        frequency: 0.01
```

### 5. Business Rule Violations

**Logical Inconsistencies:**
- Refunded transaction without original
- Failed transaction marked as completed
- Amount mismatch between transaction and refund
- Currency mismatch

**Configuration:**
```yaml
compliance_scenarios:
  business_rule_violations:
    enabled: true
    percentage: 0.02              # 2% of transactions
    patterns:
      - name: "status_mismatch"
        frequency: 0.01
      - name: "orphan_refund"
        frequency: 0.005
      - name: "currency_mismatch"
        frequency: 0.005
```

## Enhanced Configuration Schema

```yaml
simulator:
  # Output Configuration
  output:
    destination: "event_hub"      # event_hub, file, stdout
    batch_size: 100
    rate_limit: 1000             # events per second
    connection_string: "${EVENTHUB_CONNECTION_STRING}"
  
  # Transaction Volume
  transaction:
    volume:
      total: 10000               # Total transactions to generate
      rate: 100                   # Transactions per second
      duration: null              # Duration in seconds (overrides total)
    
    # Variability Configuration
    variability:
      # Amount Distribution
      amounts:
        distribution: "normal"    # normal, uniform, exponential, bimodal
        mean: 100.00
        std_dev: 50.00
        min: 1.00
        max: 10000.00
        bimodal_peaks: [25.00, 300.00]  # For bimodal distribution
      
      # Payment Method Distribution
      payment_methods:
        credit_card: 0.50
        debit_card: 0.30
        bank_transfer: 0.10
        digital_wallet: 0.05
        cryptocurrency: 0.03
        cash_equivalent: 0.02
      
      # Payment Status Distribution
      payment_status:
        completed: 0.85
        failed: 0.10
        pending: 0.03
        cancelled: 0.01
        refunded: 0.01
      
      # Currency Distribution
      currencies:
        USD: 0.60
        EUR: 0.20
        GBP: 0.10
        JPY: 0.05
        CAD: 0.03
        AUD: 0.02
      
      # Geographic Distribution
      countries:
        US: 0.50
        GB: 0.15
        CA: 0.10
        AU: 0.08
        DE: 0.05
        FR: 0.04
        JP: 0.03
        other: 0.05
      
      # Temporal Patterns
      temporal:
        business_hours: 0.70
        evening: 0.20
        night: 0.05
        weekend: 0.05
        timezone_distribution:
          UTC-5: 0.40
          UTC-8: 0.30
          UTC+0: 0.20
          UTC+9: 0.10
      
      # Merchant Categories
      merchant_categories:
        retail: 0.30
        food_beverage: 0.20
        travel: 0.15
        entertainment: 0.10
        healthcare: 0.08
        education: 0.07
        other: 0.10
  
  # Compliance Violation Scenarios
  compliance:
    enabled: true
    total_violation_percentage: 0.13  # 13% of transactions have violations
    
    scenarios:
      aml_violations:
        enabled: true
        percentage: 0.02
        patterns:
          structuring:
            enabled: true
            frequency: 0.01
            threshold: 10000.00
            transaction_count: 5
            time_window_minutes: 60
          large_amount:
            enabled: true
            frequency: 0.005
            min_amount: 50000.00
          rapid_fire:
            enabled: true
            frequency: 0.005
            transaction_count: 100
            time_window_seconds: 60
      
      kyc_violations:
        enabled: true
        percentage: 0.03
        patterns:
          missing_customer_id:
            enabled: true
            frequency: 0.01
          invalid_email:
            enabled: true
            frequency: 0.01
          missing_country:
            enabled: true
            frequency: 0.01
      
      pci_violations:
        enabled: true
        percentage: 0.01
        patterns:
          missing_card_data:
            enabled: true
            frequency: 0.005
          invalid_card_brand:
            enabled: true
            frequency: 0.005
      
      data_quality_violations:
        enabled: true
        percentage: 0.05
        patterns:
          negative_amount:
            enabled: true
            frequency: 0.01
          zero_amount:
            enabled: true
            frequency: 0.01
          invalid_currency:
            enabled: true
            frequency: 0.01
          invalid_status:
            enabled: true
            frequency: 0.01
          future_timestamp:
            enabled: true
            frequency: 0.01
      
      business_rule_violations:
        enabled: true
        percentage: 0.02
        patterns:
          status_mismatch:
            enabled: true
            frequency: 0.01
          orphan_refund:
            enabled: true
            frequency: 0.005
          currency_mismatch:
            enabled: true
            frequency: 0.005
  
  # Metadata Generation
  metadata:
    include_ip_address: true
    include_user_agent: true
    include_card_data: true
    include_risk_score: true
    include_fraud_indicators: true
    
    risk_score:
      distribution: "normal"
      mean: 0.3
      std_dev: 0.2
      min: 0.0
      max: 1.0
    
    fraud_indicators:
      enabled: true
      percentage: 0.05              # 5% have fraud indicators
      indicators:
        - "velocity_check_failed"
        - "device_fingerprint_mismatch"
        - "billing_address_mismatch"
        - "suspicious_ip_location"
        - "high_risk_country"
  
  # Logging
  logging:
    level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
    format: "json"                  # json, text
    file: "simulator.log"
    include_metrics: true
    metrics_interval_seconds: 60

# Metrics Collection
metrics:
  enabled: true
  publish_interval_seconds: 60
  track:
    - transaction_count
    - publish_rate
    - error_rate
    - compliance_violations
    - distribution_breakdown
```

## Implementation Components

### 1. Transaction Generator (`transaction_generator.py`)

**Key Functions:**
```python
class TransactionGenerator:
    def generate_transaction(self, config: Config) -> Transaction:
        """Generate a single transaction with variability"""
        
    def generate_batch(self, count: int, config: Config) -> List[Transaction]:
        """Generate multiple transactions"""
        
    def apply_compliance_violations(
        self, 
        transaction: Transaction, 
        config: ComplianceConfig
    ) -> Transaction:
        """Apply compliance violations based on configuration"""
        
    def generate_aml_violation(self, transaction: Transaction) -> Transaction:
        """Generate AML violation pattern"""
        
    def generate_kyc_violation(self, transaction: Transaction) -> Transaction:
        """Generate KYC violation pattern"""
        
    def generate_data_quality_violation(
        self, 
        transaction: Transaction
    ) -> Transaction:
        """Generate data quality violation"""
```

### 2. Compliance Violation Generator (`compliance_generator.py`)

**New Module for Compliance:**
```python
class ComplianceViolationGenerator:
    def __init__(self, config: ComplianceConfig):
        self.config = config
        self.violation_patterns = {
            'aml': AMLViolationPatterns(),
            'kyc': KYCViolationPatterns(),
            'pci': PCIViolationPatterns(),
            'data_quality': DataQualityViolationPatterns(),
            'business_rules': BusinessRuleViolationPatterns()
        }
    
    def should_apply_violation(self) -> bool:
        """Determine if this transaction should have a violation"""
        
    def apply_violation(
        self, 
        transaction: Transaction
    ) -> Tuple[Transaction, str]:
        """Apply a random violation and return violation type"""
```

### 3. Enhanced Models (`models.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal

class Transaction(BaseModel):
    transaction_id: str
    transaction_timestamp: datetime
    amount: Decimal = Field(gt=0)  # Must be positive
    currency: str = Field(min_length=3, max_length=3)
    payment_method: str
    payment_status: str
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_country: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_type: Optional[str] = None
    channel: Optional[str] = None
    device_type: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    
    # Compliance tracking
    compliance_violations: List[str] = Field(default_factory=list)
    violation_severity: Optional[str] = None  # low, medium, high, critical
    
    @validator('currency')
    def validate_currency(cls, v):
        # ISO 4217 validation
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']
        if v not in valid_currencies:
            raise ValueError(f'Invalid currency: {v}')
        return v
    
    @validator('payment_status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'completed', 'failed', 'cancelled', 'refunded']
        if v not in valid_statuses:
            raise ValueError(f'Invalid status: {v}')
        return v
```

## Testing Scenarios

### Scenario 1: Normal Operation
- 87% compliant transactions
- Realistic distributions
- All fields populated correctly

### Scenario 2: Compliance Testing
- 13% violation rate
- Mix of all violation types
- Tests detection and handling

### Scenario 3: Stress Testing
- High volume (10,000+ transactions/second)
- All violation types enabled
- Tests system under load

### Scenario 4: Edge Cases
- Boundary values
- Extreme distributions
- Rare combinations

## Metrics and Reporting

### Generated Metrics
- Total transactions generated
- Transactions by payment method
- Transactions by status
- Compliance violations by type
- Distribution breakdowns
- Error rates

### Output Format
```json
{
  "timestamp": "2025-12-04T12:00:00Z",
  "metrics": {
    "total_transactions": 10000,
    "compliant": 8700,
    "violations": {
      "aml": 200,
      "kyc": 300,
      "pci": 100,
      "data_quality": 500,
      "business_rules": 200
    },
    "distribution": {
      "payment_methods": {...},
      "currencies": {...},
      "countries": {...}
    }
  }
}
```

## Summary

This enhanced design provides:

✅ **High Variability**
- Multiple distribution types
- Configurable patterns
- Realistic data generation

✅ **Compliance Violations**
- 5 violation categories
- 13% violation rate (configurable)
- Realistic violation patterns

✅ **Comprehensive Testing**
- Normal operations
- Compliance validation
- Edge cases
- Stress testing

✅ **Flexible Configuration**
- YAML-based configuration
- Per-violation-type control
- Easy to adjust percentages

---

**Ready for implementation!** This design ensures the simulator generates realistic, variable data with meaningful compliance violations for thorough testing.

