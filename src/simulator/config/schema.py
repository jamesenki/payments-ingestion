"""
Pydantic models for configuration schema validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Literal
from decimal import Decimal


class OutputConfig(BaseModel):
    """Output destination configuration."""
    destination: Literal["event_hub", "file", "stdout"] = "event_hub"
    batch_size: int = Field(default=100, ge=1, le=10000)
    rate_limit: int = Field(default=1000, ge=1, le=100000)  # events per second
    connection_string: Optional[str] = None
    file_path: Optional[str] = None


class AmountConfig(BaseModel):
    """Amount distribution configuration."""
    distribution: Literal["normal", "uniform", "exponential", "bimodal"] = "normal"
    mean: Decimal = Field(default=Decimal("100.00"), ge=Decimal("0.01"))
    std_dev: Decimal = Field(default=Decimal("50.00"), ge=Decimal("0.01"))
    min: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.01"))
    max: Decimal = Field(default=Decimal("10000.00"), ge=Decimal("0.01"))
    bimodal_peaks: Optional[List[Decimal]] = Field(default=None, max_items=2)

    @validator('bimodal_peaks')
    def validate_bimodal_peaks(cls, v, values):
        if values.get('distribution') == 'bimodal' and not v:
            raise ValueError('bimodal_peaks required for bimodal distribution')
        return v


class VariabilityConfig(BaseModel):
    """Transaction variability configuration."""
    amounts: AmountConfig = Field(default_factory=AmountConfig)
    payment_methods: Dict[str, float] = Field(
        default={
            "credit_card": 0.50,
            "debit_card": 0.30,
            "bank_transfer": 0.10,
            "digital_wallet": 0.05,
            "cryptocurrency": 0.03,
            "cash_equivalent": 0.02,
        }
    )
    payment_status: Dict[str, float] = Field(
        default={
            "completed": 0.85,
            "failed": 0.10,
            "pending": 0.03,
            "cancelled": 0.01,
            "refunded": 0.01,
        }
    )
    currencies: Dict[str, float] = Field(
        default={
            "USD": 0.60,
            "EUR": 0.20,
            "GBP": 0.10,
            "JPY": 0.05,
            "CAD": 0.03,
            "AUD": 0.02,
        }
    )
    countries: Dict[str, float] = Field(
        default={
            "US": 0.50,
            "GB": 0.15,
            "CA": 0.10,
            "AU": 0.08,
            "DE": 0.05,
            "FR": 0.04,
            "JP": 0.03,
            "other": 0.05,
        }
    )
    temporal: Dict = Field(
        default={
            "business_hours": 0.70,
            "evening": 0.20,
            "night": 0.05,
            "weekend": 0.05,
            "timezone_distribution": {
                "UTC-5": 0.40,
                "UTC-8": 0.30,
                "UTC+0": 0.20,
                "UTC+9": 0.10,
            }
        }
    )
    merchant_categories: Dict[str, float] = Field(
        default={
            "retail": 0.30,
            "food_beverage": 0.20,
            "travel": 0.15,
            "entertainment": 0.10,
            "healthcare": 0.08,
            "education": 0.07,
            "other": 0.10,
        }
    )

    @validator('payment_methods', 'payment_status', 'currencies', 'countries', 'merchant_categories')
    def validate_distribution_sums(cls, v):
        """Validate that distribution percentages sum to approximately 1.0."""
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f'Distribution must sum to 1.0, got {total}')
        return v


class CompliancePattern(BaseModel):
    """Individual compliance violation pattern."""
    enabled: bool = True
    frequency: float = Field(default=0.01, ge=0.0, le=1.0)
    threshold: Optional[Decimal] = None
    transaction_count: Optional[int] = None
    time_window_minutes: Optional[int] = None
    time_window_seconds: Optional[int] = None
    min_amount: Optional[Decimal] = None


class ComplianceScenario(BaseModel):
    """Compliance violation scenario configuration."""
    enabled: bool = True
    percentage: float = Field(default=0.02, ge=0.0, le=1.0)
    patterns: Dict[str, CompliancePattern] = Field(default_factory=dict)


class ComplianceConfig(BaseModel):
    """Compliance violation configuration."""
    enabled: bool = True
    total_violation_percentage: float = Field(default=0.13, ge=0.0, le=1.0)
    scenarios: Dict[str, ComplianceScenario] = Field(default_factory=dict)


class MetadataConfig(BaseModel):
    """Metadata generation configuration."""
    include_ip_address: bool = True
    include_user_agent: bool = True
    include_card_data: bool = True
    include_risk_score: bool = True
    include_fraud_indicators: bool = True
    risk_score: Dict = Field(
        default={
            "distribution": "normal",
            "mean": 0.3,
            "std_dev": 0.2,
            "min": 0.0,
            "max": 1.0,
        }
    )
    fraud_indicators: Dict = Field(
        default={
            "enabled": True,
            "percentage": 0.05,
            "indicators": [
                "velocity_check_failed",
                "device_fingerprint_mismatch",
                "billing_address_mismatch",
                "suspicious_ip_location",
                "high_risk_country",
            ]
        }
    )


class TransactionConfig(BaseModel):
    """Transaction generation configuration."""
    volume: Dict = Field(
        default={
            "total": 10000,
            "rate": 100,  # per second
            "duration": None,  # seconds (overrides total)
        }
    )
    variability: VariabilityConfig = Field(default_factory=VariabilityConfig)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["json", "text"] = "json"
    file: Optional[str] = "simulator.log"
    include_metrics: bool = True
    metrics_interval_seconds: int = Field(default=60, ge=1)


class MetricsConfig(BaseModel):
    """Metrics collection configuration."""
    enabled: bool = True
    publish_interval_seconds: int = Field(default=60, ge=1)
    track: List[str] = Field(
        default=[
            "transaction_count",
            "publish_rate",
            "error_rate",
            "compliance_violations",
            "distribution_breakdown",
        ]
    )


class SimulatorConfig(BaseModel):
    """Root configuration model for the simulator."""
    simulator: Dict = Field(default_factory=dict)
    compliance: Optional[ComplianceConfig] = Field(default_factory=ComplianceConfig)
    metadata: Optional[MetadataConfig] = Field(default_factory=MetadataConfig)
    logging: Optional[LoggingConfig] = Field(default_factory=LoggingConfig)
    metrics: Optional[MetricsConfig] = Field(default_factory=MetricsConfig)

    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow extra fields for flexibility
        validate_assignment = True

