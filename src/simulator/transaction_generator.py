"""
Transaction generator with configurable variability and realistic data generation.
"""

import random
import math
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from faker import Faker

from .models import Transaction
from .config.schema import VariabilityConfig, TransactionConfig


class TransactionGenerator:
    """
    Generates realistic payment transactions with configurable variability.
    
    Features:
    - Multiple amount distributions (normal, uniform, exponential, bimodal)
    - Realistic customer and merchant data (Faker)
    - Temporal patterns (business hours, timezones)
    - Geographic distribution
    - Payment method and status distribution
    """
    
    def __init__(self, config: TransactionConfig):
        """
        Initialize transaction generator.
        
        Args:
            config: Transaction configuration with variability settings
        """
        self.config = config
        self.variability = config.variability
        self.faker = Faker()
        
        # Pre-compute weighted choices for efficiency
        self._payment_method_choices = self._prepare_weighted_choices(
            self.variability.payment_methods
        )
        self._status_choices = self._prepare_weighted_choices(
            self.variability.payment_status
        )
        self._currency_choices = self._prepare_weighted_choices(
            self.variability.currencies
        )
        self._country_choices = self._prepare_weighted_choices(
            self.variability.countries
        )
        self._merchant_category_choices = self._prepare_weighted_choices(
            self.variability.merchant_categories
        )
    
    def _prepare_weighted_choices(self, distribution: Dict[str, float]) -> List[Tuple[str, float]]:
        """Prepare weighted choices list for random.choices()."""
        return [(key, weight) for key, weight in distribution.items()]
    
    def _weighted_choice(self, choices: List[Tuple[str, float]]) -> str:
        """Select a value based on weighted distribution."""
        values, weights = zip(*choices)
        return random.choices(values, weights=weights, k=1)[0]
    
    def generate_amount(self) -> Decimal:
        """
        Generate transaction amount based on configured distribution.
        
        Returns:
            Decimal amount
        """
        amounts_config = self.variability.amounts
        distribution = amounts_config.distribution
        min_amount = amounts_config.min
        max_amount = amounts_config.max
        
        if distribution == "normal":
            # Normal distribution
            mean = float(amounts_config.mean)
            std_dev = float(amounts_config.std_dev)
            amount = random.gauss(mean, std_dev)
        
        elif distribution == "uniform":
            # Uniform distribution
            amount = random.uniform(float(min_amount), float(max_amount))
        
        elif distribution == "exponential":
            # Exponential distribution (many small, few large)
            # Scale to fit min-max range
            scale = float(max_amount) / 10.0
            amount = random.expovariate(1.0 / scale)
        
        elif distribution == "bimodal":
            # Bimodal distribution (two peaks)
            if amounts_config.bimodal_peaks and len(amounts_config.bimodal_peaks) == 2:
                peak1, peak2 = float(amounts_config.bimodal_peaks[0]), float(amounts_config.bimodal_peaks[1])
                # Choose one peak randomly
                peak = random.choice([peak1, peak2])
                std_dev = float(amounts_config.std_dev)
                amount = random.gauss(peak, std_dev)
            else:
                # Fallback to normal
                amount = random.gauss(float(amounts_config.mean), float(amounts_config.std_dev))
        
        else:
            # Default to uniform
            amount = random.uniform(float(min_amount), float(max_amount))
        
        # Clamp to min-max range
        amount = max(float(min_amount), min(float(max_amount), amount))
        
        # Round to 2 decimal places
        return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def generate_timestamp(self) -> datetime:
        """
        Generate transaction timestamp based on temporal patterns.
        
        Returns:
            datetime timestamp
        """
        now = datetime.now()
        temporal = self.variability.temporal
        
        # Determine time of day
        time_of_day = self._weighted_choice([
            ("business_hours", temporal.get("business_hours", 0.70)),
            ("evening", temporal.get("evening", 0.20)),
            ("night", temporal.get("night", 0.05)),
            ("weekend", temporal.get("weekend", 0.05)),
        ])
        
        # Generate base timestamp
        if time_of_day == "weekend":
            # Random day in next 7 days, weighted to weekends
            days_ahead = random.randint(0, 6)
            if days_ahead < 5:  # Monday-Friday
                days_ahead = random.choice([5, 6])  # Force to weekend
            timestamp = now + timedelta(days=days_ahead)
        else:
            # Random day in next 7 days
            days_ahead = random.randint(0, 6)
            timestamp = now + timedelta(days=days_ahead)
        
        # Set time based on pattern
        if time_of_day == "business_hours":
            hour = random.randint(9, 17)
        elif time_of_day == "evening":
            hour = random.randint(17, 22)
        else:  # night
            hour = random.choice(list(range(0, 6)) + list(range(22, 24)))
        
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        timestamp = timestamp.replace(hour=hour, minute=minute, second=second, microsecond=0)
        
        return timestamp
    
    def generate_customer_data(self, country: str) -> Dict[str, Optional[str]]:
        """
        Generate realistic customer data.
        
        Args:
            country: Country code for locale-specific data
            
        Returns:
            Dictionary with customer_id, email, country
        """
        # Set Faker locale based on country
        locale_map = {
            "US": "en_US",
            "GB": "en_GB",
            "CA": "en_CA",
            "AU": "en_AU",
            "DE": "de_DE",
            "FR": "fr_FR",
            "JP": "ja_JP",
        }
        locale = locale_map.get(country, "en_US")
        fake = Faker(locale)
        
        return {
            "customer_id": f"CUST-{fake.uuid4()[:8].upper()}",
            "customer_email": fake.email(),
            "customer_country": country,
        }
    
    def generate_merchant_data(self, category: str) -> Dict[str, Optional[str]]:
        """
        Generate realistic merchant data.
        
        Args:
            category: Merchant category
            
        Returns:
            Dictionary with merchant_id, name, category
        """
        fake = Faker()
        
        # Generate merchant name based on category
        company_name = fake.company()
        
        return {
            "merchant_id": f"MERCH-{fake.uuid4()[:8].upper()}",
            "merchant_name": company_name,
            "merchant_category": category,
        }
    
    def generate_metadata(
        self,
        payment_method: str,
        include_ip: bool = True,
        include_user_agent: bool = True,
        include_card_data: bool = True,
        include_risk_score: bool = True,
        include_fraud_indicators: bool = False,
    ) -> Dict:
        """
        Generate transaction metadata.
        
        Returns:
            Metadata dictionary
        """
        fake = Faker()
        metadata = {}
        
        if include_ip:
            metadata["ip_address"] = fake.ipv4()
        
        if include_user_agent:
            metadata["user_agent"] = fake.user_agent()
        
        if include_card_data and payment_method in ["credit_card", "debit_card"]:
            metadata["card_last4"] = fake.numerify("####")
            metadata["card_brand"] = random.choice(["Visa", "Mastercard", "Amex", "Discover"])
            metadata["cvv_provided"] = random.choice([True, False])
            metadata["3ds_verified"] = random.choice([True, False])
        
        if include_risk_score:
            # Generate risk score (0.0-1.0)
            metadata["risk_score"] = round(random.uniform(0.0, 1.0), 3)
        
        if include_fraud_indicators:
            fraud_indicators = [
                "velocity_check_failed",
                "device_fingerprint_mismatch",
                "billing_address_mismatch",
                "suspicious_ip_location",
                "high_risk_country",
            ]
            metadata["fraud_indicators"] = random.sample(
                fraud_indicators,
                k=random.randint(1, min(3, len(fraud_indicators)))
            )
        
        return metadata
    
    def generate_transaction(self, metadata_config: Optional[Dict] = None) -> Transaction:
        """
        Generate a single transaction with realistic data.
        
        Args:
            metadata_config: Optional metadata configuration
            
        Returns:
            Transaction object
        """
        # Generate core transaction data
        amount = self.generate_amount()
        currency = self._weighted_choice(self._currency_choices)
        payment_method = self._weighted_choice(self._payment_method_choices)
        payment_status = self._weighted_choice(self._status_choices)
        country_key = self._weighted_choice(self._country_choices)
        
        # Handle "other" country - select a random country from a list
        if country_key == "other":
            other_countries = ["MX", "BR", "IN", "CN", "KR", "SG", "NZ", "NL", "IT", "ES"]
            country = random.choice(other_countries)
        else:
            country = country_key
        
        merchant_category = self._weighted_choice(self._merchant_category_choices)
        timestamp = self.generate_timestamp()
        
        # Generate customer and merchant data
        customer_data = self.generate_customer_data(country)
        merchant_data = self.generate_merchant_data(merchant_category)
        
        # Generate metadata
        metadata = {}
        if metadata_config:
            metadata = self.generate_metadata(
                payment_method,
                include_ip=metadata_config.get("include_ip_address", True),
                include_user_agent=metadata_config.get("include_user_agent", True),
                include_card_data=metadata_config.get("include_card_data", True),
                include_risk_score=metadata_config.get("include_risk_score", True),
                include_fraud_indicators=metadata_config.get("include_fraud_indicators", False),
            )
        
        # Create transaction
        transaction = Transaction(
            transaction_timestamp=timestamp,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            payment_status=payment_status,
            customer_id=customer_data["customer_id"],
            customer_email=customer_data["customer_email"],
            customer_country=customer_data["customer_country"],
            merchant_id=merchant_data["merchant_id"],
            merchant_name=merchant_data["merchant_name"],
            merchant_category=merchant_data["merchant_category"],
            transaction_type="payment",
            channel=random.choice(["web", "mobile", "pos", "api"]),
            device_type=random.choice(["desktop", "mobile", "tablet", "pos"]),
            metadata=metadata,
        )
        
        return transaction
    
    def generate_batch(self, count: int, metadata_config: Optional[Dict] = None) -> List[Transaction]:
        """
        Generate a batch of transactions.
        
        Args:
            count: Number of transactions to generate
            metadata_config: Optional metadata configuration
            
        Returns:
            List of Transaction objects
        """
        return [self.generate_transaction(metadata_config) for _ in range(count)]

