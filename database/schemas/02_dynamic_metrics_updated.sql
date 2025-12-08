-- ============================================================================
-- Table: dynamic_metrics
-- Purpose: Stores calculated metrics derived from payment transactions
-- Updated: December 7, 2025 - Aligned with WO-11 implementation
-- ============================================================================

CREATE TABLE IF NOT EXISTS dynamic_metrics (
    -- Primary Key
    metric_id BIGSERIAL PRIMARY KEY,
    
    -- Transaction Information
    transaction_id VARCHAR(255) NOT NULL,
    correlation_id UUID NOT NULL,
    
    -- Metric Information
    metric_type VARCHAR(100) NOT NULL,
    metric_value NUMERIC(19, 4),
    metric_data JSONB,
    
    -- Temporal Information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional Context (optional)
    effective_date DATE,
    rule_name VARCHAR(100),
    rule_version VARCHAR(20)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for transaction lookups
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_transaction_id 
    ON dynamic_metrics(transaction_id);

-- Index for correlation ID lookups
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_correlation_id 
    ON dynamic_metrics(correlation_id);

-- Index for metric type queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_metric_type 
    ON dynamic_metrics(metric_type);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_created_at 
    ON dynamic_metrics(created_at DESC);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_type_created 
    ON dynamic_metrics(metric_type, created_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE dynamic_metrics IS 'Stores per-transaction extracted metrics for real-time analysis';
COMMENT ON COLUMN dynamic_metrics.metric_id IS 'Primary key, auto-incrementing';
COMMENT ON COLUMN dynamic_metrics.transaction_id IS 'Transaction identifier (links to raw event in Blob Storage)';
COMMENT ON COLUMN dynamic_metrics.correlation_id IS 'Correlation ID for request tracing';
COMMENT ON COLUMN dynamic_metrics.metric_type IS 'Type of metric (transaction_amount, channel_usage, transaction_status, etc.)';
COMMENT ON COLUMN dynamic_metrics.metric_value IS 'Numeric value of the metric';
COMMENT ON COLUMN dynamic_metrics.metric_data IS 'Additional metric data as JSON';
COMMENT ON COLUMN dynamic_metrics.created_at IS 'Timestamp when the metric was created';

