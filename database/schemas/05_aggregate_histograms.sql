-- ============================================================================
-- Table: aggregate_histograms
-- Purpose: Stores pre-aggregated KPIs and summary statistics with flexible
--          time windows for compliance monitoring and dashboard consumption
-- ============================================================================
-- 
-- This table is separate from payment_metrics_5m:
-- - payment_metrics_5m: Fixed 5-minute windows, payment-specific dimensions
-- - aggregate_histograms: Flexible time windows, generic metric types
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS aggregate_histograms (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Metric Identification
    metric_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    
    -- Time Window
    time_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Aggregated Count
    event_count BIGINT NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique Constraint: One record per metric/event type per time window
    CONSTRAINT uq_aggregate_histograms_unique 
        UNIQUE (metric_type, event_type, time_window_start, time_window_end)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for metric type queries
CREATE INDEX IF NOT EXISTS idx_aggregate_histograms_metric_type 
    ON aggregate_histograms(metric_type);

-- Index for event type queries
CREATE INDEX IF NOT EXISTS idx_aggregate_histograms_event_type 
    ON aggregate_histograms(event_type);

-- Index for time window queries (most common pattern)
CREATE INDEX IF NOT EXISTS idx_aggregate_histograms_time_window 
    ON aggregate_histograms(time_window_start DESC, time_window_end DESC);

-- Composite index for metric type and time window
CREATE INDEX IF NOT EXISTS idx_aggregate_histograms_metric_time 
    ON aggregate_histograms(metric_type, time_window_start DESC);

-- Composite index for event type and time window
CREATE INDEX IF NOT EXISTS idx_aggregate_histograms_event_time 
    ON aggregate_histograms(event_type, time_window_start DESC);

-- ============================================================================
-- Constraints
-- ============================================================================

-- Check constraint for window end after window start
ALTER TABLE aggregate_histograms 
    ADD CONSTRAINT chk_aggregate_histograms_window_order 
    CHECK (time_window_end > time_window_start);

-- Check constraint for non-negative event count
ALTER TABLE aggregate_histograms 
    ADD CONSTRAINT chk_aggregate_histograms_count_positive 
    CHECK (event_count >= 0);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE aggregate_histograms IS 
    'Stores pre-aggregated KPIs and summary statistics with flexible time windows for compliance monitoring and dashboard consumption';

COMMENT ON COLUMN aggregate_histograms.id IS 
    'Auto-incrementing primary key';

COMMENT ON COLUMN aggregate_histograms.metric_type IS 
    'Type of metric being aggregated (e.g., transaction_success_rate, channel_failure_rate)';

COMMENT ON COLUMN aggregate_histograms.event_type IS 
    'Type of event being counted (e.g., transaction_success, transaction_failure, timeout)';

COMMENT ON COLUMN aggregate_histograms.time_window_start IS 
    'Start timestamp of the aggregation time window';

COMMENT ON COLUMN aggregate_histograms.time_window_end IS 
    'End timestamp of the aggregation time window';

COMMENT ON COLUMN aggregate_histograms.event_count IS 
    'Number of events of the specified type in the time window';

COMMENT ON COLUMN aggregate_histograms.created_at IS 
    'Timestamp when the aggregate record was created';

COMMENT ON COLUMN aggregate_histograms.updated_at IS 
    'Timestamp when the aggregate record was last updated';

