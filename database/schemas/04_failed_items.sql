-- ============================================================================
-- Table: failed_items
-- Purpose: Dead-letter queue for failed transaction processing
-- ============================================================================

CREATE TABLE IF NOT EXISTS failed_items (
    -- Primary Key
    failed_id BIGSERIAL PRIMARY KEY,
    
    -- Transaction Information
    transaction_id VARCHAR(255) NOT NULL,
    correlation_id UUID NOT NULL,
    
    -- Error Information
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    
    -- Raw Payload (stored as JSONB for querying)
    raw_payload JSONB NOT NULL,
    
    -- Temporal Information
    failed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional Context
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for transaction lookups
CREATE INDEX IF NOT EXISTS idx_failed_items_transaction_id 
    ON failed_items(transaction_id);

-- Index for correlation ID lookups
CREATE INDEX IF NOT EXISTS idx_failed_items_correlation_id 
    ON failed_items(correlation_id);

-- Index for error type queries
CREATE INDEX IF NOT EXISTS idx_failed_items_error_type 
    ON failed_items(error_type);

-- Index for unresolved items (most common query)
CREATE INDEX IF NOT EXISTS idx_failed_items_unresolved 
    ON failed_items(resolved, failed_at) 
    WHERE resolved = FALSE;

-- Index for retry processing
CREATE INDEX IF NOT EXISTS idx_failed_items_retry 
    ON failed_items(retry_count, last_retry_at) 
    WHERE resolved = FALSE;

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_failed_items_failed_at 
    ON failed_items(failed_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE failed_items IS 'Dead-letter queue for failed transaction processing';
COMMENT ON COLUMN failed_items.failed_id IS 'Primary key, auto-incrementing';
COMMENT ON COLUMN failed_items.transaction_id IS 'Transaction identifier from original event';
COMMENT ON COLUMN failed_items.correlation_id IS 'Correlation ID for request tracing';
COMMENT ON COLUMN failed_items.error_type IS 'Type of error (validation_error, processing_error, storage_error, etc.)';
COMMENT ON COLUMN failed_items.error_message IS 'Detailed error message';
COMMENT ON COLUMN failed_items.raw_payload IS 'Original transaction payload as JSON';
COMMENT ON COLUMN failed_items.failed_at IS 'Timestamp when the failure occurred';
COMMENT ON COLUMN failed_items.retry_count IS 'Number of retry attempts';
COMMENT ON COLUMN failed_items.last_retry_at IS 'Timestamp of last retry attempt';
COMMENT ON COLUMN failed_items.resolved IS 'Whether this failure has been resolved';
COMMENT ON COLUMN failed_items.resolved_at IS 'Timestamp when resolved';
COMMENT ON COLUMN failed_items.resolution_notes IS 'Notes about how the failure was resolved';

