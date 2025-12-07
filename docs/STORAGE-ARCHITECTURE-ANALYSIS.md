# Storage Architecture Analysis - Work Order Review

**Date:** December 5, 2025  
**Purpose:** Analyze storage architecture requirements from latest work orders

---

## Key Finding: Hybrid Storage Architecture

Based on **WO-61: Implement Hybrid Storage Layer with PostgreSQL and Blob Storage**, the architecture is:

### ✅ Correct Architecture (from WO-61)

1. **Raw Events** → **Azure Blob Storage (Parquet files)**
   - Store raw transaction events as Parquet files
   - Date-based folder structure: `raw_events/yyyy={year}/mm={month}/dd={day}/`
   - For archival and compliance

2. **Dynamic Metrics** → **PostgreSQL (dynamic_metrics table)**
   - Store extracted metrics per transaction
   - For real-time analysis queries

3. **Aggregate Histograms** → **PostgreSQL (aggregate_histograms table)**
   - Store pre-computed KPIs and summary statistics
   - For dashboard consumption

---

## Work Order Analysis

### ❌ Potentially Obsolete Work Orders

#### WO-21: Execute CREATE TABLE Script for NormalizedTransactions
**Status:** ❌ **OBSOLETE or MISALIGNED**

**Current Requirement:**
- "Create the NormalizedTransactions table, which will store the raw, normalized transaction data"

**Issue:** 
- WO-61 clearly states: **"Store raw transaction events as Parquet files in Azure Blob Storage"**
- NormalizedTransactions table conflicts with Parquet storage approach

**Resolution Needed:**
- Either WO-21 is obsolete, OR
- NormalizedTransactions serves a different purpose (metadata/indexing?)
- Need clarification on whether this table is still needed

#### WO-22: Execute CREATE TABLE Script for DynamicMetrics
**Status:** ✅ **ALIGNED** (but table name may differ)

**Current Requirement:**
- "Create the DynamicMetrics table, which will store the individually extracted metrics"

**Alignment:**
- WO-61: "Store extracted metrics in PostgreSQL dynamic_metrics table"
- WO-44: "Implement Dynamic Metrics Storage Table and Operations"
- ✅ This aligns with hybrid storage architecture

**Note:** Table name is `dynamic_metrics` (lowercase, plural) per WO-34

#### WO-23: Execute CREATE TABLE Script for payment_metrics_5m
**Status:** ⚠️ **UNCLEAR**

**Current Requirement:**
- "Create the payment_metrics_5m table, which will store the time-windowed aggregations"

**Issue:**
- WO-61 mentions "aggregate_histograms table" (not payment_metrics_5m)
- WO-53: "Implement Aggregate Histogram Storage Table and Operations"
- May be the same table with different name, or different tables

**Resolution Needed:**
- Clarify if `payment_metrics_5m` is the same as `aggregate_histograms`
- Or if they serve different purposes

---

### ✅ Correct Work Orders (Aligned with Hybrid Storage)

#### WO-31: Implement Raw Events Database Schema and Data Model
**Status:** ⚠️ **CONFLICTING**

**Requirement:**
- "Create raw_events table with BIGSERIAL primary key..."

**Issue:**
- WO-61 says raw events go to **Blob Storage (Parquet)**, not PostgreSQL
- WO-31 creates a PostgreSQL table for raw_events

**Possible Resolution:**
- The `raw_events` table might be for **metadata/indexing** only
- Actual payloads stored in Blob Storage
- Or WO-31 is obsolete

#### WO-34: Create PostgreSQL Database Schema with Core Tables
**Status:** ⚠️ **PARTIALLY ALIGNED**

**Requirement:**
- Create `raw_events` table (PostgreSQL)
- Create `dynamic_metrics` table (PostgreSQL) ✅
- Create `aggregate_histograms` table (PostgreSQL) ✅
- Create `failed_items` table (PostgreSQL) ✅

**Issue:**
- Includes `raw_events` table, but WO-61 says raw events go to Blob Storage
- May be for metadata/indexing, not actual storage

#### WO-40: Implement Raw Events Storage Service with Connection Pooling
**Status:** ❌ **CONFLICTING**

**Requirement:**
- "Implement PostgresRawEventStore class that implements RawEventStore interface"
- "persists raw events to the database"

**Issue:**
- WO-64: "Implement BlobRawEventStore class" (for Blob Storage)
- WO-61: Raw events go to Blob Storage, not PostgreSQL
- WO-40 conflicts with hybrid storage architecture

**Resolution:**
- WO-40 might be obsolete
- OR PostgresRawEventStore is for a different purpose (metadata?)

#### WO-61: Implement Hybrid Storage Layer with PostgreSQL and Blob Storage
**Status:** ✅ **AUTHORITATIVE** (This is the correct architecture)

**Key Requirements:**
- ✅ "Store raw transaction events as Parquet files in Azure Blob Storage"
- ✅ "Store extracted metrics in PostgreSQL dynamic_metrics table"
- ✅ "Store calculated aggregate data in PostgreSQL histograms table"

#### WO-63: Implement Raw Events Parquet Data Model and Serialization
**Status:** ✅ **ALIGNED**

**Requirement:**
- Parquet schema definition
- RawEvent data model
- Serialization to Parquet format

#### WO-64: Implement Batched Blob Storage Service with Parquet Operations
**Status:** ✅ **ALIGNED**

**Requirement:**
- BlobRawEventStore class
- Buffer events and flush as Parquet files
- Upload to Blob Storage with date-based paths

#### WO-65: Implement Azure Blob Storage Infrastructure and Lifecycle Management
**Status:** ✅ **ALIGNED**

**Requirement:**
- Blob Storage container configuration
- Lifecycle policies (90-day archive, retention)
- Date-based folder structure

#### WO-66: Implement Blob Storage Query and Retrieval Operations
**Status:** ✅ **ALIGNED**

**Requirement:**
- Query Parquet files by date/time range
- Retrieve RawEvent objects from Blob Storage

---

## WO-11 Analysis: Main Azure Function Entry Point

**Current Requirement:**
- "Insert the normalized transaction record into the `NormalizedTransactions` table"
- "Insert the extracted metrics into the `DynamicMetrics` table"
- "Perform an UPSERT operation to update the correct time window in the `payment_metrics_5m` table"

**Issues:**
1. ❌ Mentions `NormalizedTransactions` table (should be Blob Storage per WO-61)
2. ✅ Mentions `DynamicMetrics` (should be `dynamic_metrics` per WO-34)
3. ⚠️ Mentions `payment_metrics_5m` (should be `aggregate_histograms` per WO-61?)

**Corrected Requirements (based on WO-61):**
- ✅ Store raw transaction events as Parquet files in Azure Blob Storage
- ✅ Insert extracted metrics into `dynamic_metrics` table (PostgreSQL)
- ✅ Perform UPSERT operation to update `aggregate_histograms` table (PostgreSQL)

---

## Summary of Conflicts

### Storage Architecture Conflicts

| Component | WO-21/WO-40/WO-31 | WO-61/WO-64 | Resolution Needed |
|-----------|-------------------|-------------|-------------------|
| Raw Events | PostgreSQL table | Blob Storage (Parquet) | ❌ Conflict - WO-61 is authoritative |
| Dynamic Metrics | PostgreSQL (DynamicMetrics) | PostgreSQL (dynamic_metrics) | ✅ Aligned (name difference) |
| Aggregates | PostgreSQL (payment_metrics_5m) | PostgreSQL (aggregate_histograms) | ⚠️ Unclear if same or different |

### Recommended Resolution

1. **Raw Events Storage:**
   - ✅ Use **Blob Storage (Parquet)** per WO-61, WO-64, WO-65, WO-66
   - ❌ Do NOT use PostgreSQL table for raw events (WO-21, WO-31, WO-40 are obsolete or for different purpose)

2. **Dynamic Metrics Storage:**
   - ✅ Use **PostgreSQL `dynamic_metrics` table** per WO-44, WO-61
   - ✅ Aligns with WO-22 (but use lowercase plural name)

3. **Aggregate Storage:**
   - ✅ Use **PostgreSQL `aggregate_histograms` table** per WO-53, WO-61
   - ⚠️ Clarify if `payment_metrics_5m` is the same as `aggregate_histograms`

---

## Action Items

1. **Clarify Obsolete Work Orders:**
   - WO-21: NormalizedTransactions table - Is this needed?
   - WO-31: raw_events PostgreSQL table - Is this for metadata only?
   - WO-40: PostgresRawEventStore - Is this obsolete?

2. **Update WO-11:**
   - Change from NormalizedTransactions table → Blob Storage (Parquet)
   - Change DynamicMetrics → dynamic_metrics
   - Clarify payment_metrics_5m vs aggregate_histograms

3. **Verify Current Implementation:**
   - Check if `database/schemas/01_normalized_transactions.sql` should be removed
   - Verify if we need raw_events PostgreSQL table for metadata/indexing
   - Confirm aggregate table naming

---

## Recommended Architecture (Based on WO-61)

```
┌─────────────────────┐
│  Event Hub          │
│  (Transaction Data) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Azure Function     │
│  (Processing)       │
└──────────┬──────────┘
           │
           ├─────────────────┬──────────────────┐
           ▼                 ▼                  ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Blob Storage     │  │ PostgreSQL  │  │ PostgreSQL       │
│ (Parquet Files)  │  │ dynamic_    │  │ aggregate_       │
│                  │  │ metrics     │  │ histograms       │
│ raw_events/      │  │             │  │                  │
│ yyyy/mm/dd/      │  │ Per-        │  │ Pre-computed     │
│                  │  │ transaction │  │ KPIs             │
│ For archival     │  │ metrics     │  │                  │
└──────────────────┘  └──────────────┘  └──────────────────┘
```

---

**Last Updated:** December 5, 2025  
**Status:** ⚠️ **ARCHITECTURE CONFLICTS IDENTIFIED**

