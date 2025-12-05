# WO-10 Implementation Plan: Metric Engine with Data Extraction and Rule Processing

## Overview

Develop a comprehensive metric processing engine that extracts transaction data, normalizes it, applies rule-based logic, aggregates metrics, and clusters similar transactions/metrics over configurable time windows.

## Architecture Overview

```
┌─────────────────┐
│  Data Source    │ (Event Hubs or PostgreSQL)
│  (Transactions) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Extractor  │ ← Extract raw transaction data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Normalizer │ ← Normalize to consistent format
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Rule Processor  │ ← Apply rules to derive metrics
└────────┬────────┘
         │
         ├─────────────────┐
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│   Aggregator    │  │   Clusterer     │
│  (sum, avg,     │  │  (group similar │
│   count)        │  │   transactions) │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └────────┬───────────┘
                  ▼
         ┌─────────────────┐
         │  Time Window    │ ← Configurable windows
         │    Manager      │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │  PostgreSQL     │ ← Store metrics
         │  (DynamicMetrics│
         │   & payment_    │
         │   metrics_5m)   │
         └─────────────────┘
```

## Database Schema Context

### NormalizedTransactions Table
- Stores normalized transaction data
- Fields: transaction_id, amount, currency, payment_method, payment_status, customer_id, merchant_id, timestamps, metadata (JSONB)

### DynamicMetrics Table
- Stores rule-derived metrics per transaction
- Fields: metric_id, transaction_id, metric_name, metric_value, metric_type, rule_name, context (JSONB)

### payment_metrics_5m Table
- Stores aggregated metrics in 5-minute windows
- Fields: window_start, window_end, dimensions (payment_method, currency, status), aggregated values (count, sum, avg, min, max)

## Implementation Plan

### Phase 1: Core Infrastructure

#### 1. Configuration (`config/metric_engine_settings.yaml`)
- Time window configurations (hourly, daily, weekly, custom)
- Aggregation dimensions (payment_method, currency, status, country)
- Clustering parameters (similarity thresholds, cluster count)
- Rule processing settings
- Data source configuration (Event Hub vs Database)

#### 2. Data Models (`src/metric_engine/models.py`)
- `RawTransaction` - Raw transaction from source
- `NormalizedTransaction` - Normalized transaction
- `DerivedMetric` - Rule-derived metric
- `AggregatedMetric` - Aggregated metric
- `Cluster` - Transaction cluster
- `TimeWindow` - Time window definition

#### 3. Utilities
- `src/metric_engine/utils/time_window_manager.py` - Time window calculations
- `src/metric_engine/utils/logger.py` - Logging utilities

### Phase 2: Core Components

#### 4. Data Extractor (`src/metric_engine/data_extractor.py`)
- Extract from Event Hubs (consumer)
- Extract from PostgreSQL (query NormalizedTransactions)
- Support batch processing
- Handle connection errors and retries

#### 5. Data Normalizer (`src/metric_engine/data_normalizer.py`)
- Normalize transaction structure
- Validate required fields
- Handle missing/null values
- Convert data types
- Enrich with metadata

#### 6. Rule Processor (`src/metric_engine/rule_processor.py`)
- Load rules from configuration
- Apply rules to normalized transactions
- Derive metrics (count, sum, average, ratio, percentage, derived)
- Store to DynamicMetrics table
- Support rule versioning

### Phase 3: Advanced Features

#### 7. Aggregator (`src/metric_engine/aggregator.py`)
- Aggregate by dimensions (payment_method, currency, status, country)
- Support operations: sum, average, count, min, max
- Time window support (hourly, daily, weekly, custom)
- Store to payment_metrics_5m table
- Handle overlapping windows

#### 8. Clusterer (`src/metric_engine/clusterer.py`)
- Group similar transactions
- Support clustering algorithms (K-means, DBSCAN, hierarchical)
- Configurable similarity metrics
- Time window support
- Store cluster assignments

### Phase 4: Orchestration

#### 9. Main Engine (`src/metric_engine/main.py`)
- Orchestrate data flow
- Manage processing pipeline
- Handle errors and retries
- Coordinate time windows
- Logging and metrics

### Phase 5: Testing

#### 10. Test Suite
- Unit tests for each component
- Integration tests for full pipeline
- Performance tests
- Mock Event Hub and database

## Detailed File Structure

```
src/metric_engine/
├── __init__.py
├── main.py                    # Main orchestrator
├── models.py                  # Data models
├── data_extractor.py          # Extract from Event Hub/DB
├── data_normalizer.py         # Normalize transactions
├── rule_processor.py          # Apply rules, derive metrics
├── aggregator.py              # Aggregate metrics
├── clusterer.py               # Cluster transactions
└── utils/
    ├── __init__.py
    ├── time_window_manager.py # Time window utilities
    └── logger.py              # Logging utilities

config/
└── metric_engine_settings.yaml  # Configuration

tests/metric_engine/
├── __init__.py
├── test_data_extractor.py
├── test_data_normalizer.py
├── test_rule_processor.py
├── test_aggregator.py
├── test_clusterer.py
└── test_main.py
```

## Key Design Decisions

### 1. Data Source
- **Primary**: PostgreSQL (read from NormalizedTransactions)
- **Secondary**: Event Hubs (for real-time processing)
- Support both for flexibility

### 2. Time Windows
- **Predefined**: hourly, daily, weekly
- **Custom**: Configurable duration (e.g., 5-minute, 15-minute)
- **Sliding**: Overlapping windows for continuous analysis

### 3. Aggregation Dimensions
- payment_method
- currency
- payment_status
- customer_country
- merchant_category
- Custom dimensions via configuration

### 4. Clustering Algorithms
- **K-means**: For known cluster count
- **DBSCAN**: For density-based clustering
- **Hierarchical**: For hierarchical grouping
- Configurable similarity metrics

### 5. Rule Processing
- YAML-based rule definitions
- Support for: count, sum, average, ratio, percentage, derived
- Rule versioning for tracking changes
- Context storage in JSONB

## Configuration Structure

```yaml
metric_engine:
  data_source:
    type: "postgresql"  # or "event_hub"
    connection_string: "${DATABASE_URL}"
    batch_size: 1000
  
  time_windows:
    - name: "5min"
      duration_seconds: 300
    - name: "hourly"
      duration_seconds: 3600
    - name: "daily"
      duration_seconds: 86400
  
  aggregation:
    dimensions:
      - payment_method
      - currency
      - payment_status
    operations:
      - sum
      - average
      - count
      - min
      - max
  
  clustering:
    algorithm: "kmeans"
    n_clusters: 5
    similarity_metric: "euclidean"
    enabled: true
  
  rules:
    enabled: true
    rules_file: "config/metric_rules.yaml"
```

## Implementation Steps

1. ✅ Create configuration structure
2. ✅ Create data models
3. ✅ Implement time window manager
4. ✅ Implement data extractor (PostgreSQL first)
5. ✅ Implement data normalizer
6. ✅ Implement rule processor
7. ✅ Implement aggregator
8. ✅ Implement clusterer
9. ✅ Implement main orchestrator
10. ✅ Create test suite
11. ✅ Add logging throughout
12. ✅ Add error handling

## Dependencies

- `psycopg2` or `asyncpg` - PostgreSQL connection
- `azure-eventhub` - Event Hub consumer (optional)
- `scikit-learn` - Clustering algorithms
- `pandas` - Data manipulation (optional, for efficiency)
- `pydantic` - Data validation
- `pyyaml` - Configuration parsing

## Testing Strategy

- **Unit Tests**: Mock all external dependencies
- **Integration Tests**: Test with test database
- **Performance Tests**: Measure throughput and latency
- **End-to-End Tests**: Full pipeline with sample data

## Success Criteria

- ✅ Extract transactions from PostgreSQL
- ✅ Normalize transaction data
- ✅ Apply rules to derive metrics
- ✅ Aggregate metrics by dimensions and time windows
- ✅ Cluster similar transactions
- ✅ Store results in database
- ✅ Support configurable time windows
- ✅ Comprehensive logging
- ✅ Error handling and retries
- ✅ Unit tests with >80% coverage

