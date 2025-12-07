# WO-11: Updated Requirements - Main Azure Function Entry Point

**Date:** December 5, 2025  
**Work Order:** WO-11  
**Status:** Updated to align with hybrid storage architecture (WO-61)

---

## Original Requirements (OBSOLETE)

❌ **Original (Outdated):**
- Insert the normalized transaction record into the `NormalizedTransactions` table
- Insert the extracted metrics into the `DynamicMetrics` table
- Perform an UPSERT (INSERT...ON CONFLICT) operation to update the correct time window in the `payment_metrics_5m` table

---

## Updated Requirements (Based on WO-61)

✅ **Corrected Requirements:**

### 1. Store Raw Transaction Events to Azure Blob Storage (Parquet)

**Purpose:** Archive raw transaction events for compliance and audit trails

**Implementation:**
- Serialize normalized transaction to Parquet format
- Upload to Azure Blob Storage with date-based path: `raw_events/yyyy={year}/mm={month}/dd={day}/events_{timestamp}.parquet`
- Use `BlobRawEventStore` (WO-64) for buffered batch writes
- Handle serialization errors and route to dead-letter queue if needed

**Data Structure:**
- Use `RawEvent` data model (WO-63)
- Include all transaction fields from normalized transaction
- Store `event_payload` as JSON-encoded string in Parquet

### 2. Insert Extracted Metrics into PostgreSQL `dynamic_metrics` Table

**Purpose:** Store per-transaction extracted metrics for real-time analysis

**Implementation:**
- Insert extracted metrics into `dynamic_metrics` table
- Use `transaction_id` to link to raw event (stored in Blob Storage)
- Include `metric_type`, `metric_value`, `metric_data` (JSONB)
- Handle duplicate transaction_id gracefully (if applicable)

**Table Structure:**
- `metric_id` (BIGSERIAL PRIMARY KEY)
- `transaction_id` (VARCHAR(255))
- `correlation_id` (UUID)
- `metric_type` (VARCHAR(100))
- `metric_value` (NUMERIC)
- `metric_data` (JSONB)
- `created_at` (TIMESTAMP WITH TIME ZONE)

### 3. Perform UPSERT Operation for Aggregate Metrics

**Purpose:** Update pre-computed KPIs in aggregate tables

**Implementation:**
- **Option A:** UPSERT to `payment_metrics_5m` table (5-minute windows, payment-specific)
  - Primary Key: (window_start, payment_method, currency, payment_status)
  - Update aggregated values: total_count, total_amount, avg_amount, etc.
  
- **Option B:** UPSERT to `aggregate_histograms` table (flexible windows, generic metrics)
  - Unique Constraint: (metric_type, event_type, time_window_start, time_window_end)
  - Update event_count for the time window

**Decision:** Use both tables as appropriate:
- `payment_metrics_5m` for payment-specific real-time metrics
- `aggregate_histograms` for compliance and general KPI metrics

---

## Complete Workflow

```
┌─────────────────┐
│ Event Hub       │
│ (Transaction)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Azure Function          │
│ (run.py)                │
└────────┬────────────────┘
         │
         ├─────────────────┬──────────────────┬──────────────────┐
         ▼                 ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Blob Storage     │  │ PostgreSQL   │  │ PostgreSQL   │  │ PostgreSQL   │
│ (Parquet Files)  │  │ dynamic_     │  │ payment_     │  │ aggregate_   │
│                  │  │ metrics      │  │ metrics_5m   │  │ histograms   │
│ raw_events/      │  │              │  │              │  │              │
│ yyyy/mm/dd/     │  │ Per-         │  │ 5-min        │  │ Flexible     │
│                  │  │ transaction │  │ windows      │  │ windows      │
│ For archival    │  │ metrics      │  │ Payment      │  │ Generic      │
│                  │  │              │  │ metrics      │  │ KPIs         │
└──────────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Implementation Details

### Function Entry Point Structure

```python
# src/function_app/run.py

import azure.functions as func
from datetime import datetime
from typing import List

def main(events: func.EventHubEvent):
    """
    Azure Function entry point for processing payment transactions.
    
    Implements three-part data persistence:
    1. Store raw event to Blob Storage (Parquet)
    2. Store extracted metrics to PostgreSQL dynamic_metrics
    3. Update aggregate metrics in PostgreSQL (payment_metrics_5m and aggregate_histograms)
    """
    # 1. Parse and normalize transaction
    transaction = parse_and_normalize(events.get_body())
    
    # 2. Store raw event to Blob Storage (Parquet)
    store_raw_event_to_blob(transaction)
    
    # 3. Extract metrics
    metrics = extract_metrics(transaction)
    
    # 4. Store metrics to dynamic_metrics table
    store_dynamic_metrics(transaction.transaction_id, metrics)
    
    # 5. Update aggregate metrics
    update_payment_metrics_5m(transaction)
    update_aggregate_histograms(transaction, metrics)
```

### Error Handling

- **Blob Storage failures:** Route to dead-letter queue (failed_items table)
- **PostgreSQL failures:** Retry with exponential backoff, then route to dead-letter queue
- **Serialization errors:** Log and route to dead-letter queue
- **Validation errors:** Route to dead-letter queue with detailed error information

---

## Dependencies

### Required Work Orders

- ✅ **WO-63:** Raw Events Parquet Data Model and Serialization
- ✅ **WO-64:** Batched Blob Storage Service with Parquet Operations
- ✅ **WO-44:** Dynamic Metrics Storage Table and Operations
- ✅ **WO-53:** Aggregate Histogram Storage Table and Operations
- ✅ **WO-61:** Hybrid Storage Layer (overall architecture)

### Required Components

- `BlobRawEventStore` class (WO-64)
- `RawEvent` data model (WO-63)
- PostgreSQL connection pool (WO-41)
- Data access layer (WO-49)
- Metrics extraction engine (WO-33, WO-42)

---

## Testing Requirements

1. **Unit Tests:**
   - Test raw event storage to Blob Storage
   - Test dynamic metrics insertion
   - Test aggregate metrics UPSERT operations
   - Test error handling and dead-letter queue routing

2. **Integration Tests:**
   - Test end-to-end workflow with mocked dependencies
   - Test concurrent processing
   - Test failure scenarios

3. **Performance Tests:**
   - Verify 10,000+ transactions/second throughput
   - Verify <100ms write latency (95th percentile)
   - Verify efficient batch operations

---

## Migration Notes

### From Old Architecture

**Old (Obsolete):**
- NormalizedTransactions table (PostgreSQL)
- Single storage location

**New (Current):**
- Blob Storage (Parquet) for raw events
- PostgreSQL for metrics and aggregates
- Hybrid storage architecture

### Breaking Changes

- ❌ `NormalizedTransactions` table no longer used
- ✅ Raw events stored in Blob Storage
- ✅ Foreign key from `dynamic_metrics` to `NormalizedTransactions` removed
- ✅ New `aggregate_histograms` table added

---

**Last Updated:** December 5, 2025  
**Status:** ✅ **REQUIREMENTS UPDATED**

