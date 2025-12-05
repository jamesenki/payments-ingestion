-- ============================================================================
-- Table: DynamicMetrics
-- Purpose: Stores calculated metrics derived from payment transactions
-- ============================================================================

CREATE TABLE IF NOT EXISTS DynamicMetrics (
    -- Primary Key
    metric_id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Key to Transaction
    transaction_id VARCHAR(255) NOT NULL,
    
    -- Metric Information
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(19, 4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_category VARCHAR(100),
    
    -- Temporal Information
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    effective_date DATE NOT NULL,
    
    -- Rule Information
    rule_name VARCHAR(100),
    rule_version VARCHAR(20),
    
    -- Additional Context
    context JSONB,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT fk_dynamic_metrics_transaction 
        FOREIGN KEY (transaction_id) 
        REFERENCES NormalizedTransactions(transaction_id)
        ON DELETE CASCADE
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for transaction lookups
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_transaction 
    ON DynamicMetrics(transaction_id);

-- Index for metric name queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_name 
    ON DynamicMetrics(metric_name);

-- Index for time-series analysis
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_calculated_at 
    ON DynamicMetrics(calculated_at DESC);

-- Index for metric type queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_type 
    ON DynamicMetrics(metric_type);

-- Composite index for efficient metric retrieval
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_name_date 
    ON DynamicMetrics(metric_name, effective_date DESC);

-- Index for rule-based queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_rule 
    ON DynamicMetrics(rule_name);

-- GIN index for context JSONB queries
CREATE INDEX IF NOT EXISTS idx_dynamic_metrics_context 
    ON DynamicMetrics USING GIN (context);

-- ============================================================================
-- Constraints
-- ============================================================================

-- Check constraint for metric types
ALTER TABLE DynamicMetrics 
    ADD CONSTRAINT chk_dynamic_metrics_type 
    CHECK (metric_type IN ('count', 'sum', 'average', 'ratio', 'percentage', 'derived'));

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE DynamicMetrics IS 'Stores calculated metrics derived from payment transactions based on configurable rules';
COMMENT ON COLUMN DynamicMetrics.metric_id IS 'Auto-incrementing primary key';
COMMENT ON COLUMN DynamicMetrics.transaction_id IS 'Reference to the source transaction';
COMMENT ON COLUMN DynamicMetrics.metric_name IS 'Name of the calculated metric';
COMMENT ON COLUMN DynamicMetrics.metric_value IS 'Calculated value of the metric';
COMMENT ON COLUMN DynamicMetrics.metric_type IS 'Type of metric calculation';
COMMENT ON COLUMN DynamicMetrics.rule_name IS 'Name of the rule that generated this metric';
COMMENT ON COLUMN DynamicMetrics.rule_version IS 'Version of the rule for tracking changes';
COMMENT ON COLUMN DynamicMetrics.context IS 'Additional context data stored as JSONB';

