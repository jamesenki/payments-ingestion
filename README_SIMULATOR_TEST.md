# Simulator Local Testing Guide

## Quick Start

### Run the Simulator

```bash
# Using Python script
python3 scripts/test_simulator_local.py

# Or using shell script
./scripts/test_simulator_local.sh

# Or directly
python3 -m src.simulator.main --config config/simulator_config_test.yaml
```

### Output

Transactions are written to: `output/transactions.jsonl`

Each line is a JSON object representing a payment transaction.

### Configuration

Edit `config/simulator_config_test.yaml` to customize:
- Number of transactions (`total`)
- Transaction rate (`rate`)
- Output file path (`file_path`)
- Output format (`jsonl` or `json_array`)
- Compliance violations percentage

### View Generated Transactions

```bash
# Count transactions
wc -l output/transactions.jsonl

# View first transaction (pretty-printed)
head -n 1 output/transactions.jsonl | python3 -m json.tool

# View all transactions
cat output/transactions.jsonl | python3 -m json.tool

# Search for specific fields
grep "credit_card" output/transactions.jsonl | head -n 5
```

### Example Transaction Structure

Each transaction includes:
- `transaction_id`: Unique identifier
- `amount`: Transaction amount
- `currency`: Currency code (USD, EUR, GBP, etc.)
- `payment_method`: credit_card, debit_card, etc.
- `payment_status`: completed, declined, timeout, error
- `customer_id`, `customer_email`, `customer_country`
- `merchant_id`, `merchant_name`, `merchant_category`
- `metadata`: IP address, card info, risk score, fraud indicators
- `compliance_violations`: Array of any compliance issues

### Testing Different Scenarios

1. **High Volume Test**: Increase `total` to 10000
2. **Compliance Testing**: Increase `total_violation_percentage` to 0.20
3. **Different Formats**: Change `format` to `json_array` for array output
4. **Append Mode**: Set `append: true` to add to existing file

