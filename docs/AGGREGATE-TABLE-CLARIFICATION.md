# Aggregate Table Clarification

**Date:** December 5, 2025  
**Purpose:** Clarify aggregate table naming and structure

---

## Table Comparison

### payment_metrics_5m (Existing)

**Structure:**
- Primary Key: (window_start, payment_method, currency, payment_status)
- Fixed 5-minute time windows
- Dimensions: payment_method, currency, payment_status
- Metrics: total_count, total_amount, avg_amount, min_amount, max_amount
- Status breakdown: completed_count, failed_count, pending_count
- JSONB breakdowns: payment_method_breakdown, currency_breakdown, country_breakdown

**Purpose:** Pre-aggregated payment metrics in 5-minute windows with specific dimensions

### aggregate_histograms (WO-34 Requirement)

**Structure (from WO-34):**
- Primary Key: BIGSERIAL
- Unique constraint: (metric_type, event_type, time_window_start, time_window_end)
- Fields: metric_type, event_type, time_window_start, time_window_end, event_count
- More flexible time windows (not fixed to 5 minutes)
- More generic metric types

**Purpose:** Pre-aggregated KPIs with flexible time windows and metric types

---

## Decision

**These are DIFFERENT tables serving DIFFERENT purposes:**

1. **payment_metrics_5m** → Specific payment metrics in 5-minute windows
   - Use for: Real-time payment dashboard
   - Fixed dimensions: payment_method, currency, payment_status
   - Fixed window: 5 minutes

2. **aggregate_histograms** → Generic aggregate metrics with flexible windows
   - Use for: Compliance monitoring, general KPIs
   - Flexible dimensions: metric_type, event_type
   - Flexible windows: Configurable (hourly, daily, weekly, etc.)

**Both tables are needed:**
- `payment_metrics_5m` for payment-specific real-time metrics
- `aggregate_histograms` for general compliance and KPI metrics

---

## Implementation Plan

1. ✅ Keep `payment_metrics_5m` as-is (already implemented)
2. ✅ Create `aggregate_histograms` table (WO-34 requirement)
3. ✅ Both tables will coexist in PostgreSQL

---

**Status:** ✅ **CLARIFIED** - Both tables needed

