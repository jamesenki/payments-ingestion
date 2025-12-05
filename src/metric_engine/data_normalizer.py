"""
Data normalization module for the metric engine.
"""

from typing import List, Optional
from decimal import Decimal

from .models import RawTransaction, NormalizedTransaction
from .utils.logger import get_logger


class DataNormalizer:
    """Normalizes raw transaction data to consistent format."""
    
    def __init__(self):
        """Initialize data normalizer."""
        self.logger = get_logger("metric_engine.data_normalizer")
    
    def normalize(self, raw_transaction: RawTransaction) -> Optional[NormalizedTransaction]:
        """
        Normalize a raw transaction.
        
        Args:
            raw_transaction: Raw transaction to normalize
            
        Returns:
            NormalizedTransaction or None if validation fails
        """
        try:
            # Validate and normalize amount
            amount = self._normalize_amount(raw_transaction.amount)
            if amount is None:
                return None
            
            # Validate and normalize currency
            currency = self._normalize_currency(raw_transaction.currency)
            if currency is None:
                return None
            
            # Validate payment status
            payment_status = self._normalize_payment_status(raw_transaction.payment_status)
            if payment_status is None:
                return None
            
            # Normalize country code
            country = self._normalize_country(raw_transaction.customer_country)
            
            return NormalizedTransaction(
                transaction_id=raw_transaction.transaction_id,
                transaction_timestamp=raw_transaction.transaction_timestamp,
                amount=amount,
                currency=currency,
                payment_method=raw_transaction.payment_method,
                payment_status=payment_status,
                customer_id=raw_transaction.customer_id,
                customer_email=raw_transaction.customer_email,
                customer_country=country,
                merchant_id=raw_transaction.merchant_id,
                merchant_name=raw_transaction.merchant_name,
                merchant_category=raw_transaction.merchant_category,
                transaction_type=raw_transaction.transaction_type,
                channel=raw_transaction.channel,
                device_type=raw_transaction.device_type,
                metadata=raw_transaction.metadata
            )
        
        except Exception as e:
            self.logger.warning(
                f"Failed to normalize transaction {raw_transaction.transaction_id}: {e}",
                exc_info=True
            )
            return None
    
    def normalize_batch(self, raw_transactions: List[RawTransaction]) -> List[NormalizedTransaction]:
        """
        Normalize a batch of transactions.
        
        Args:
            raw_transactions: List of raw transactions
            
        Returns:
            List of normalized transactions (invalid ones are skipped)
        """
        normalized = []
        for raw_tx in raw_transactions:
            normalized_tx = self.normalize(raw_tx)
            if normalized_tx:
                normalized.append(normalized_tx)
        
        if len(normalized) < len(raw_transactions):
            self.logger.warning(
                f"Normalized {len(normalized)}/{len(raw_transactions)} transactions"
            )
        
        return normalized
    
    def _normalize_amount(self, amount: any) -> Optional[Decimal]:
        """Normalize and validate amount."""
        try:
            if isinstance(amount, Decimal):
                decimal_amount = amount
            elif isinstance(amount, (int, float)):
                decimal_amount = Decimal(str(amount))
            else:
                decimal_amount = Decimal(str(amount))
            
            if decimal_amount <= 0:
                self.logger.warning(f"Invalid amount: {decimal_amount}")
                return None
            
            return decimal_amount
        
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to normalize amount {amount}: {e}")
            return None
    
    def _normalize_currency(self, currency: Optional[str]) -> Optional[str]:
        """Normalize and validate currency code."""
        if not currency:
            return None
        
        currency_upper = currency.upper().strip()
        
        if len(currency_upper) != 3:
            self.logger.warning(f"Invalid currency code length: {currency}")
            return None
        
        return currency_upper
    
    def _normalize_payment_status(self, status: Optional[str]) -> Optional[str]:
        """Normalize and validate payment status."""
        if not status:
            return None
        
        status_lower = status.lower().strip()
        valid_statuses = ["pending", "completed", "failed", "cancelled", "refunded"]
        
        if status_lower not in valid_statuses:
            self.logger.warning(f"Invalid payment status: {status}")
            return None
        
        return status_lower
    
    def _normalize_country(self, country: Optional[str]) -> Optional[str]:
        """Normalize country code."""
        if not country:
            return None
        
        country_upper = country.upper().strip()
        
        if len(country_upper) != 2:
            self.logger.warning(f"Invalid country code length: {country}")
            return None
        
        return country_upper

