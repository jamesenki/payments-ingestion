# Parquet Schema Design for Raw Events

**Date:** December 5, 2025  
**Purpose:** Define Parquet schema for raw transaction events stored in Azure Blob Storage  
**Based on:** Deprecated `NormalizedTransactions` table schema (WO-21, now obsolete)

---

## Overview

Raw transaction events are stored in Azure Blob Storage as Parquet files per the hybrid storage architecture (WO-61). This document defines the Parquet schema based on the original `NormalizedTransactions` table structure.

---

## Parquet Schema Definition

### Schema Structure

```python
import pyarrow as pa

parquet_schema = pa.schema([
    # Primary Identifier
    pa.field('transaction_id', pa.string()),
    
    # Temporal Information
    pa.field('transaction_timestamp', pa.timestamp('ns', tz='UTC')),
    pa.field('ingestion_timestamp', pa.timestamp('ns', tz='UTC')),
    pa.field('processing_timestamp', pa.timestamp('ns', tz='UTC')),
    
    # Transaction Details
    pa.field('amount', pa.decimal128(19, 4)),
    pa.field('currency', pa.string()),
    pa.field('payment_method', pa.string()),
    pa.field('payment_status', pa.string()),
    
    # Customer Information (nullable)
    pa.field('customer_id', pa.string()),
    pa.field('customer_email', pa.string()),
    pa.field('customer_country', pa.string()),  # ISO 3166-1 alpha-2
    
    # Merchant Information (nullable)
    pa.field('merchant_id', pa.string()),
    pa.field('merchant_name', pa.string()),
    pa.field('merchant_category', pa.string()),
    
    # Transaction Metadata (nullable)
    pa.field('transaction_type', pa.string()),
    pa.field('channel', pa.string()),
    pa.field('device_type', pa.string()),
    
    # Additional Data (JSON stored as string)
    pa.field('metadata', pa.string()),  # JSON-encoded
    
    # Audit Fields
    pa.field('created_at', pa.timestamp('ns', tz='UTC')),
    pa.field('updated_at', pa.timestamp('ns', tz='UTC')),
])
```

---

## Field Mappings

### From NormalizedTransactions Table to Parquet

| Database Column | Parquet Field | Type | Nullable | Notes |
|----------------|---------------|------|----------|-------|
| transaction_id | transaction_id | string | No | Primary identifier |
| transaction_timestamp | transaction_timestamp | timestamp(UTC) | No | Transaction occurrence time |
| ingestion_timestamp | ingestion_timestamp | timestamp(UTC) | Yes | Event Hub ingestion time |
| processing_timestamp | processing_timestamp | timestamp(UTC) | Yes | Function processing time |
| amount | amount | decimal128(19,4) | No | Transaction amount |
| currency | currency | string | No | ISO 4217 code (3 chars) |
| payment_method | payment_method | string | No | Payment method type |
| payment_status | payment_status | string | No | Status enum |
| customer_id | customer_id | string | Yes | Customer identifier |
| customer_email | customer_email | string | Yes | Customer email |
| customer_country | customer_country | string | Yes | ISO 3166-1 alpha-2 |
| merchant_id | merchant_id | string | Yes | Merchant identifier |
| merchant_name | merchant_name | string | Yes | Merchant name |
| merchant_category | merchant_category | string | Yes | Merchant category |
| transaction_type | transaction_type | string | Yes | Transaction type |
| channel | channel | string | Yes | Transaction channel |
| device_type | device_type | string | Yes | Device type |
| metadata | metadata | string | Yes | JSON-encoded object |
| created_at | created_at | timestamp(UTC) | No | Record creation time |
| updated_at | updated_at | timestamp(UTC) | No | Record update time |

---

## Data Type Considerations

### Timestamps
- **Format:** UTC timestamps with nanosecond precision
- **Storage:** Parquet timestamp type with timezone
- **Serialization:** ISO 8601 format when converting to/from JSON

### Decimal Amounts
- **Type:** `decimal128(19, 4)` for precision
- **Range:** Supports amounts up to 999,999,999,999,999.9999
- **Precision:** 4 decimal places for currency

### JSON Metadata
- **Storage:** JSON object serialized as string in Parquet
- **Deserialization:** Parse JSON string back to dict when reading
- **Benefits:** Flexible schema, efficient storage

### Nullable Fields
- All customer, merchant, and metadata fields are nullable
- Parquet supports null values efficiently
- Use appropriate null handling in serialization/deserialization

---

## File Organization

### Blob Storage Path Structure

```
raw_events/
  yyyy={year}/
    mm={month}/
      dd={day}/
        events_{timestamp}.parquet
```

**Example:**
```
raw_events/
  yyyy=2025/
    mm=12/
      dd=05/
        events_20251205_143022.parquet
        events_20251205_143052.parquet
```

### File Naming Convention

- Format: `events_{YYYYMMDD}_{HHMMSS}.parquet`
- Timestamp: UTC time when file was created
- Uniqueness: Timestamp ensures no collisions

---

## Compression and Performance

### Compression Settings

- **Compression:** SNAPPY (default, good balance)
- **Row Group Size:** 128 MB (default)
- **Page Size:** 1 MB (default)

### Performance Optimizations

1. **Columnar Storage:** Efficient for analytical queries
2. **Partitioning:** Date-based partitioning for fast filtering
3. **Compression:** Reduces storage costs
4. **Batch Writes:** Write multiple events per file

---

## Serialization Example

### Python to Parquet

```python
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

# Raw event data
events = [
    {
        'transaction_id': 'tx-123',
        'transaction_timestamp': datetime.utcnow(),
        'amount': 100.50,
        'currency': 'USD',
        'payment_method': 'credit_card',
        'payment_status': 'completed',
        'metadata': '{"key": "value"}'  # JSON string
    }
]

# Convert to PyArrow Table
table = pa.Table.from_pylist(events, schema=parquet_schema)

# Write to Parquet
pq.write_table(table, 'events.parquet', compression='snappy')
```

### Parquet to Python

```python
import pyarrow.parquet as pq
import json

# Read Parquet file
table = pq.read_table('events.parquet')

# Convert to list of dicts
events = table.to_pylist()

# Parse JSON metadata
for event in events:
    if event['metadata']:
        event['metadata'] = json.loads(event['metadata'])
```

---

## Schema Evolution

### Versioning Strategy

- **Schema Version:** Include in file metadata
- **Backward Compatibility:** Add new fields as nullable
- **Migration:** Handle schema changes in deserialization

### Future Considerations

- Additional fields can be added as nullable
- Deprecated fields can be marked but retained for compatibility
- Schema registry for version tracking

---

## Validation Rules

### Field Constraints (from original schema)

1. **Amount:** Must be positive (enforced in application layer)
2. **Currency:** ISO 4217 code, exactly 3 characters
3. **Payment Status:** Enum: pending, completed, failed, cancelled, refunded
4. **Customer Country:** ISO 3166-1 alpha-2, exactly 2 characters (if provided)

### Data Quality

- All required fields must be present
- Timestamps must be valid UTC timestamps
- Amounts must be valid decimal numbers
- JSON metadata must be valid JSON

---

## Implementation References

- **WO-63:** Raw Events Parquet Data Model and Serialization
- **WO-64:** Batched Blob Storage Service with Parquet Operations
- **WO-65:** Azure Blob Storage Infrastructure and Lifecycle Management
- **WO-66:** Blob Storage Query and Retrieval Operations

---

**Last Updated:** December 5, 2025  
**Status:** ✅ **PARQUET SCHEMA DESIGNED**

