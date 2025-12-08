# Database Schema Deployment Scripts

This directory contains scripts for deploying and validating database schemas.

## Scripts

### `deploy-schema.sh`

Deploys database schemas to PostgreSQL in the correct order.

**Usage:**
```bash
export DATABASE_HOST="your-postgres-host"
export DATABASE_NAME="payments_db"
export DATABASE_USER="your-user"
export DATABASE_PASSWORD="your-password"

# Deploy to dev environment
./scripts/database/deploy-schema.sh dev

# Dry run (validate without applying)
DRY_RUN=true ./scripts/database/deploy-schema.sh dev
```

**Schema Order:**
1. `02_dynamic_metrics_updated.sql` - Dynamic metrics table (updated for WO-11)
2. `03_payment_metrics_5m.sql` - 5-minute window aggregates
3. `04_failed_items.sql` - Dead-letter queue table
4. `05_aggregate_histograms.sql` - Flexible window aggregates

**Note:** `01_normalized_transactions.sql` is deprecated (raw events now stored in Blob Storage per ADR-006).

### `validate-schema.sh`

Validates that all required tables, indexes, and constraints exist.

**Usage:**
```bash
export DATABASE_HOST="your-postgres-host"
export DATABASE_NAME="payments_db"
export DATABASE_USER="your-user"
export DATABASE_PASSWORD="your-password"

./scripts/database/validate-schema.sh
```

**Validates:**
- Required tables exist
- Key indexes exist
- Views exist (if applicable)
- Table statistics

## Environment Variables

Required environment variables:
- `DATABASE_HOST` - PostgreSQL hostname
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database username
- `DATABASE_PASSWORD` - Database password

## Schema Files

All schema files are located in `database/schemas/`:

- `02_dynamic_metrics_updated.sql` - Per-transaction metrics (updated for WO-11)
- `03_payment_metrics_5m.sql` - 5-minute window aggregates
- `04_failed_items.sql` - Dead-letter queue for failed transactions
- `05_aggregate_histograms.sql` - Flexible window aggregates

## Troubleshooting

### Connection Issues
- Verify PostgreSQL is accessible from your network
- Check firewall rules
- Verify credentials

### Schema Conflicts
- Use `IF NOT EXISTS` clauses (already included)
- Check for existing tables before deployment
- Review migration history

### Permission Issues
- Ensure database user has CREATE TABLE permissions
- Verify user has permissions on the target database

## CI/CD Integration

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Deploy Database Schema
  env:
    DATABASE_HOST: ${{ secrets.DATABASE_HOST }}
    DATABASE_NAME: ${{ secrets.DATABASE_NAME }}
    DATABASE_USER: ${{ secrets.DATABASE_USER }}
    DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
  run: |
    ./scripts/database/deploy-schema.sh ${{ env.ENVIRONMENT }}
    ./scripts/database/validate-schema.sh
```

