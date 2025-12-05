-- ============================================================================
-- Table: NormalizedTransactions
-- Purpose: Stores normalized payment transaction data
-- ============================================================================

CREATE TABLE IF NOT EXISTS NormalizedTransactions (
    -- Primary Key
    transaction_id VARCHAR(255) PRIMARY KEY,
    
    -- Temporal Information
    transaction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Transaction Details
    amount DECIMAL(19, 4) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    
    -- Customer Information
    customer_id VARCHAR(255),
    customer_email VARCHAR(255),
    customer_country VARCHAR(2),
    
    -- Merchant Information
    merchant_id VARCHAR(255),
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    
    -- Transaction Metadata
    transaction_type VARCHAR(50),
    channel VARCHAR(50),
    device_type VARCHAR(50),
    
    -- Additional Data (JSONB for flexibility)
    metadata JSONB,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for timestamp-based queries (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_timestamp 
    ON NormalizedTransactions(transaction_timestamp DESC);

-- Index for customer queries
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_customer 
    ON NormalizedTransactions(customer_id);

-- Index for merchant queries
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_merchant 
    ON NormalizedTransactions(merchant_id);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_status 
    ON NormalizedTransactions(payment_status);

-- Index for payment method analysis
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_method 
    ON NormalizedTransactions(payment_method);

-- Composite index for time-series queries with filters
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_time_method 
    ON NormalizedTransactions(transaction_timestamp DESC, payment_method);

-- GIN index for JSONB metadata queries
CREATE INDEX IF NOT EXISTS idx_normalized_transactions_metadata 
    ON NormalizedTransactions USING GIN (metadata);

-- ============================================================================
-- Constraints
-- ============================================================================

-- Check constraint for positive amounts
ALTER TABLE NormalizedTransactions 
    ADD CONSTRAINT chk_normalized_transactions_amount_positive 
    CHECK (amount > 0);

-- Check constraint for valid currency codes (ISO 4217)
ALTER TABLE NormalizedTransactions 
    ADD CONSTRAINT chk_normalized_transactions_currency_length 
    CHECK (LENGTH(currency) = 3);

-- Check constraint for valid payment status
ALTER TABLE NormalizedTransactions 
    ADD CONSTRAINT chk_normalized_transactions_status 
    CHECK (payment_status IN ('pending', 'completed', 'failed', 'cancelled', 'refunded'));

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE NormalizedTransactions IS 'Stores normalized payment transaction data from Event Hub';
COMMENT ON COLUMN NormalizedTransactions.transaction_id IS 'Unique identifier for the transaction';
COMMENT ON COLUMN NormalizedTransactions.transaction_timestamp IS 'Timestamp when the transaction occurred';
COMMENT ON COLUMN NormalizedTransactions.ingestion_timestamp IS 'Timestamp when the transaction was ingested into Event Hub';
COMMENT ON COLUMN NormalizedTransactions.processing_timestamp IS 'Timestamp when the transaction was processed';
COMMENT ON COLUMN NormalizedTransactions.amount IS 'Transaction amount';
COMMENT ON COLUMN NormalizedTransactions.currency IS 'ISO 4217 currency code';
COMMENT ON COLUMN NormalizedTransactions.payment_method IS 'Payment method used (e.g., credit_card, debit_card, bank_transfer)';
COMMENT ON COLUMN NormalizedTransactions.payment_status IS 'Current status of the payment';
COMMENT ON COLUMN NormalizedTransactions.metadata IS 'Additional flexible data stored as JSONB';

