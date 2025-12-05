-- ============================================================================
-- Table: payment_metrics_5m
-- Purpose: Stores aggregated payment metrics in 5-minute time windows
-- ============================================================================

CREATE TABLE IF NOT EXISTS payment_metrics_5m (
    -- Primary Key (composite: time window + dimensions)
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Dimensions (for grouping/filtering)
    payment_method VARCHAR(50) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    
    -- Aggregated Metrics
    total_count BIGINT NOT NULL DEFAULT 0,
    total_amount DECIMAL(19, 4) NOT NULL DEFAULT 0,
    avg_amount DECIMAL(19, 4),
    min_amount DECIMAL(19, 4),
    max_amount DECIMAL(19, 4),
    
    -- Status Breakdown
    completed_count BIGINT DEFAULT 0,
    failed_count BIGINT DEFAULT 0,
    pending_count BIGINT DEFAULT 0,
    
    -- Payment Method Breakdown (JSONB for flexibility)
    payment_method_breakdown JSONB,
    currency_breakdown JSONB,
    
    -- Customer Metrics
    unique_customers BIGINT DEFAULT 0,
    unique_merchants BIGINT DEFAULT 0,
    
    -- Geographic Metrics
    country_breakdown JSONB,
    
    -- Additional Aggregations
    additional_metrics JSONB,
    
    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Primary Key
    PRIMARY KEY (window_start, payment_method, currency, payment_status)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for time-series queries (most common pattern)
CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_window 
    ON payment_metrics_5m(window_start DESC);

-- Index for payment method analysis
CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_method 
    ON payment_metrics_5m(payment_method, window_start DESC);

-- Index for currency analysis
CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_currency 
    ON payment_metrics_5m(currency, window_start DESC);

-- Index for status analysis
CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_status 
    ON payment_metrics_5m(payment_status, window_start DESC);

-- Composite index for multi-dimensional queries
CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_method_currency 
    ON payment_metrics_5m(payment_method, currency, window_start DESC);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_method_breakdown 
    ON payment_metrics_5m USING GIN (payment_method_breakdown);

CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_currency_breakdown 
    ON payment_metrics_5m USING GIN (currency_breakdown);

CREATE INDEX IF NOT EXISTS idx_payment_metrics_5m_country_breakdown 
    ON payment_metrics_5m USING GIN (country_breakdown);

-- ============================================================================
-- Constraints
-- ============================================================================

-- Check constraint for window end after window start
ALTER TABLE payment_metrics_5m 
    ADD CONSTRAINT chk_payment_metrics_5m_window_order 
    CHECK (window_end > window_start);

-- Check constraint for 5-minute window duration
ALTER TABLE payment_metrics_5m 
    ADD CONSTRAINT chk_payment_metrics_5m_window_duration 
    CHECK (EXTRACT(EPOCH FROM (window_end - window_start)) = 300);

-- Check constraint for non-negative counts
ALTER TABLE payment_metrics_5m 
    ADD CONSTRAINT chk_payment_metrics_5m_counts_positive 
    CHECK (
        total_count >= 0 AND 
        completed_count >= 0 AND 
        failed_count >= 0 AND 
        pending_count >= 0
    );

-- Check constraint for non-negative amounts
ALTER TABLE payment_metrics_5m 
    ADD CONSTRAINT chk_payment_metrics_5m_amounts_positive 
    CHECK (
        total_amount >= 0 AND 
        (avg_amount IS NULL OR avg_amount >= 0) AND
        (min_amount IS NULL OR min_amount >= 0) AND
        (max_amount IS NULL OR max_amount >= 0)
    );

-- Check constraint for valid currency codes
ALTER TABLE payment_metrics_5m 
    ADD CONSTRAINT chk_payment_metrics_5m_currency_length 
    CHECK (LENGTH(currency) = 3);

-- Check constraint for valid payment status
ALTER TABLE payment_metrics_5m 
    ADD CONSTRAINT chk_payment_metrics_5m_status 
    CHECK (payment_status IN ('completed', 'failed', 'pending', 'cancelled', 'refunded', 'all'));

-- ============================================================================
-- Functions for Time Window Calculation
-- ============================================================================

-- Function to round timestamp down to nearest 5-minute window
CREATE OR REPLACE FUNCTION round_to_5min_window(ts TIMESTAMP WITH TIME ZONE)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
BEGIN
    RETURN date_trunc('hour', ts) + 
           (FLOOR(EXTRACT(MINUTE FROM ts) / 5) * INTERVAL '5 minutes');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- View for hourly rollups
CREATE OR REPLACE VIEW payment_metrics_hourly AS
SELECT 
    date_trunc('hour', window_start) AS hour_start,
    payment_method,
    currency,
    SUM(total_count) AS total_count,
    SUM(total_amount) AS total_amount,
    AVG(avg_amount) AS avg_amount,
    MIN(min_amount) AS min_amount,
    MAX(max_amount) AS max_amount,
    SUM(completed_count) AS completed_count,
    SUM(failed_count) AS failed_count,
    SUM(pending_count) AS pending_count
FROM payment_metrics_5m
GROUP BY hour_start, payment_method, currency
ORDER BY hour_start DESC;

-- View for daily rollups
CREATE OR REPLACE VIEW payment_metrics_daily AS
SELECT 
    DATE(window_start) AS date,
    payment_method,
    currency,
    SUM(total_count) AS total_count,
    SUM(total_amount) AS total_amount,
    AVG(avg_amount) AS avg_amount,
    MIN(min_amount) AS min_amount,
    MAX(max_amount) AS max_amount,
    SUM(completed_count) AS completed_count,
    SUM(failed_count) AS failed_count,
    SUM(pending_count) AS pending_count
FROM payment_metrics_5m
GROUP BY date, payment_method, currency
ORDER BY date DESC;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE payment_metrics_5m IS 'Aggregated payment metrics calculated in 5-minute time windows for real-time analytics';
COMMENT ON COLUMN payment_metrics_5m.window_start IS 'Start timestamp of the 5-minute window';
COMMENT ON COLUMN payment_metrics_5m.window_end IS 'End timestamp of the 5-minute window';
COMMENT ON COLUMN payment_metrics_5m.total_count IS 'Total number of transactions in the window';
COMMENT ON COLUMN payment_metrics_5m.total_amount IS 'Sum of all transaction amounts in the window';
COMMENT ON COLUMN payment_metrics_5m.avg_amount IS 'Average transaction amount in the window';
COMMENT ON COLUMN payment_metrics_5m.payment_method_breakdown IS 'JSONB containing breakdown by payment method';
COMMENT ON COLUMN payment_metrics_5m.currency_breakdown IS 'JSONB containing breakdown by currency';
COMMENT ON COLUMN payment_metrics_5m.country_breakdown IS 'JSONB containing breakdown by country';

