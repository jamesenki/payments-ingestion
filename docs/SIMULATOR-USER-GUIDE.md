# Payment Data Simulator - Complete User Guide

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Features](#advanced-features)

---

## Overview

The Payment Data Simulator is a Python application that generates realistic payment transaction data for testing and validating the payments ingestion pipeline. It supports:

- **Realistic Data Generation**: Configurable transaction amounts, payment methods, currencies, and temporal patterns
- **Compliance Violations**: Generate out-of-compliance transactions for testing (AML, KYC, PCI, data quality)
- **Azure Event Hub Integration**: Publish transactions directly to Azure Event Hubs
- **Hot Reload**: Update configuration without restarting
- **Performance Metrics**: Track generation and publishing statistics

---

## Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Azure Subscription**: For Event Hub access (if using Event Hub output)
- **Azure Event Hub**: Created and configured (if using Event Hub output)

### Installation Steps

#### Option 1: Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd payments-ingestion

# Install dependencies
pip install -r requirements.txt

# For development (includes test dependencies)
pip install -r requirements-dev.txt
```

#### Option 2: Docker Installation

```bash
# Build Docker image
docker build -t payment-simulator .

# Run container
docker run \
  -e EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
  -v $(pwd)/config:/app/config \
  payment-simulator
```

### Environment Setup

Set the Event Hub connection string:

```bash
export EVENTHUB_CONNECTION_STRING="Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=...;EntityPath=your-event-hub"
```

Or create a `.env` file:

```bash
EVENTHUB_CONNECTION_STRING=Endpoint=sb://...
```

---

## Configuration

The simulator uses a YAML configuration file located at `config/simulator_config.yaml` by default.

### Configuration File Structure

```yaml
simulator:
  output:              # Output destination configuration
    destination: "event_hub"
    batch_size: 100
    rate_limit: 1000
  
  transaction:         # Transaction generation settings
    volume:            # Generation volume
      total: 10000
      rate: 100
    variability:       # Data variability settings
      # ... (see below)

compliance:            # Compliance violation settings
  enabled: true
  total_violation_percentage: 0.13
  scenarios: { }

metadata:              # Optional metadata
  include_ip_address: true
  include_user_agent: true

logging:               # Logging configuration
  level: "INFO"
  format: "json"
```

### Configuration Options

#### Output Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `destination` | string | `"event_hub"` | Output destination (`event_hub`, `file`, `stdout`) |
| `batch_size` | integer | `100` | Number of transactions per batch (1-10000) |
| `rate_limit` | integer | `1000` | Maximum events per second (1-100000) |
| `connection_string` | string | `${EVENTHUB_CONNECTION_STRING}` | Event Hub connection string (supports env var references) |

**Example:**
```yaml
simulator:
  output:
    destination: "event_hub"
    batch_size: 100
    rate_limit: 1000
    connection_string: "${EVENTHUB_CONNECTION_STRING}"
```

#### Transaction Volume

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `total` | integer | `10000` | Total number of transactions to generate |
| `rate` | integer | `100` | Transactions per second |
| `duration` | integer | `null` | Duration in seconds (overrides `total` if set) |

**Examples:**

Count-based (generate 1000 transactions):
```yaml
transaction:
  volume:
    total: 1000
    rate: 100
```

Time-based (run for 1 hour):
```yaml
transaction:
  volume:
    duration: 3600  # 1 hour
    rate: 1000      # 1000 transactions/second
```

#### Amount Distribution

Configure how transaction amounts are generated:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `distribution` | string | `"normal"` | Distribution type: `normal`, `uniform`, `exponential`, `bimodal` |
| `mean` | decimal | `100.00` | Mean for normal/bimodal distributions |
| `std_dev` | decimal | `50.00` | Standard deviation |
| `min` | decimal | `1.00` | Minimum amount |
| `max` | decimal | `10000.00` | Maximum amount |
| `bimodal_peaks` | array | `null` | Two peak values for bimodal distribution |

**Examples:**

Normal distribution:
```yaml
variability:
  amounts:
    distribution: "normal"
    mean: 100.00
    std_dev: 50.00
    min: 1.00
    max: 1000.00
```

Uniform distribution:
```yaml
variability:
  amounts:
    distribution: "uniform"
    min: 10.00
    max: 500.00
```

#### Payment Method Distribution

Configure the distribution of payment methods:

```yaml
variability:
  payment_methods:
    credit_card: 0.50      # 50%
    debit_card: 0.30       # 30%
    bank_transfer: 0.10    # 10%
    digital_wallet: 0.05   # 5%
    cryptocurrency: 0.03   # 3%
    cash_equivalent: 0.02  # 2%
```

**Note:** Percentages must sum to approximately 1.0 (0.99-1.01).

#### Payment Status Distribution

```yaml
variability:
  payment_status:
    completed: 0.85        # 85%
    failed: 0.10           # 10%
    pending: 0.03          # 3%
    cancelled: 0.01        # 1%
    refunded: 0.01         # 1%
```

#### Currency Distribution

```yaml
variability:
  currencies:
    USD: 0.60              # 60%
    EUR: 0.20              # 20%
    GBP: 0.10              # 10%
    JPY: 0.05              # 5%
    CAD: 0.03              # 3%
    AUD: 0.02              # 2%
```

#### Country Distribution

```yaml
variability:
  countries:
    US: 0.50               # 50%
    GB: 0.15               # 15%
    CA: 0.10               # 10%
    AU: 0.08               # 8%
    DE: 0.05               # 5%
    FR: 0.04               # 4%
    JP: 0.03               # 3%
    other: 0.05            # 5%
```

#### Temporal Patterns

Configure time-based patterns:

```yaml
variability:
  temporal:
    business_hours: 0.70   # 70% during 9 AM - 5 PM
    evening: 0.20          # 20% during 5 PM - 10 PM
    night: 0.05            # 5% during night
    weekend: 0.05          # 5% on weekends
    timezone_distribution:
      UTC-5: 0.40          # 40% EST
      UTC-8: 0.30          # 30% PST
      UTC+0: 0.20          # 20% GMT
      UTC+9: 0.10          # 10% JST
```

#### Compliance Violations

Configure compliance violation generation:

```yaml
compliance:
  enabled: true
  total_violation_percentage: 0.13  # 13% of transactions
  
  scenarios:
    aml_violations:
      enabled: true
      percentage: 0.02      # 2% of all transactions
      patterns:
        structuring:
          enabled: true
          frequency: 0.01
          threshold: 10000.00
        large_amount:
          enabled: true
          frequency: 0.005
          min_amount: 50000.00
    
    kyc_violations:
      enabled: true
      percentage: 0.03
      patterns:
        missing_customer_id:
          enabled: true
          frequency: 0.01
    
    data_quality_violations:
      enabled: true
      percentage: 0.05
      patterns:
        negative_amount:
          enabled: true
          frequency: 0.01
        invalid_currency:
          enabled: true
          frequency: 0.01
```

**Violation Types:**
- **AML**: Structuring, large amounts, rapid-fire transactions
- **KYC**: Missing customer data, invalid email, missing country
- **PCI**: Missing card data, invalid card brand
- **Data Quality**: Negative amounts, zero amounts, invalid formats
- **Business Rules**: Status mismatches, orphan refunds, currency mismatches

#### Metadata Configuration

Include optional transaction metadata:

```yaml
metadata:
  include_ip_address: true
  include_user_agent: true
  include_card_data: true
  include_risk_score: true
  include_fraud_indicators: true
  
  risk_score:
    distribution: "normal"
    mean: 0.3
    std_dev: 0.2
    min: 0.0
    max: 1.0
```

#### Logging Configuration

```yaml
logging:
  level: "INFO"            # DEBUG, INFO, WARNING, ERROR
  format: "json"          # json or text
  file: "simulator.log"   # Optional log file path
  include_metrics: true
  metrics_interval_seconds: 60
```

---

## Usage

### Basic Usage

```bash
# Run with default configuration (config/simulator_config.yaml)
python -m src.simulator.main

# Run with custom configuration file
python -m src.simulator.main --config /path/to/config.yaml
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Path to configuration YAML file | `config/simulator_config.yaml` |

### Running with Docker

```bash
# Build image
docker build -t payment-simulator .

# Run with environment variable
docker run \
  -e EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
  -v $(pwd)/config:/app/config \
  payment-simulator

# Run with custom config
docker run \
  -e EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
  -v $(pwd)/custom_config.yaml:/app/config/simulator_config.yaml \
  payment-simulator
```

### Hot Reload

The simulator supports hot reload of configuration files. When you modify `config/simulator_config.yaml`, the simulator will automatically reload the configuration without restarting.

You can also trigger a reload by sending a SIGHUP signal:

```bash
# Find the process ID
ps aux | grep simulator

# Send reload signal
kill -HUP <PID>
```

### Stopping the Simulator

The simulator can be stopped gracefully:
- Press `Ctrl+C` (SIGINT)
- Send `SIGTERM` signal: `kill <PID>`
- The simulator will finish the current batch and shutdown cleanly

---

## Examples

### Example 1: Basic Transaction Generation

Generate 1000 transactions at 100 transactions/second:

```yaml
# config/simulator_config.yaml
simulator:
  output:
    destination: "event_hub"
    batch_size: 100
  
  transaction:
    volume:
      total: 1000
      rate: 100
```

Run:
```bash
python -m src.simulator.main
```

### Example 2: High Volume Load Test

Run for 1 hour at 1000 transactions/second:

```yaml
simulator:
  transaction:
    volume:
      duration: 3600  # 1 hour
      rate: 1000      # 1000 tx/sec
```

### Example 3: Compliance Testing

Generate transactions with 20% compliance violations:

```yaml
compliance:
  enabled: true
  total_violation_percentage: 0.20
  
  scenarios:
    aml_violations:
      enabled: true
      percentage: 0.10
      patterns:
        large_amount:
          enabled: true
          frequency: 1.0
          min_amount: 50000.00
    
    data_quality_violations:
      enabled: true
      percentage: 0.10
      patterns:
        negative_amount:
          enabled: true
          frequency: 1.0
```

### Example 4: Specific Payment Method Testing

Generate only credit card transactions:

```yaml
variability:
  payment_methods:
    credit_card: 1.0      # 100% credit card
```

### Example 5: Custom Amount Distribution

Generate transactions with bimodal distribution (many small, few large):

```yaml
variability:
  amounts:
    distribution: "bimodal"
    bimodal_peaks: [50.00, 500.00]
    std_dev: 25.00
    min: 1.00
    max: 1000.00
```

### Example 6: Time-Based Generation

Generate transactions only during business hours:

```yaml
variability:
  temporal:
    business_hours: 1.0   # 100% business hours
    evening: 0.0
    night: 0.0
    weekend: 0.0
```

---

## Troubleshooting

### Common Issues

#### 1. Connection String Not Found

**Error:**
```
ValueError: Environment variable EVENTHUB_CONNECTION_STRING not set
```

**Solution:**
```bash
# Set environment variable
export EVENTHUB_CONNECTION_STRING="Endpoint=sb://..."

# Or use .env file
echo "EVENTHUB_CONNECTION_STRING=Endpoint=sb://..." > .env
```

#### 2. Configuration File Not Found

**Error:**
```
FileNotFoundError: Configuration file not found: config/simulator_config.yaml
```

**Solution:**
```bash
# Copy example configuration
cp config/simulator_config.yaml.example config/simulator_config.yaml

# Or specify custom path
python -m src.simulator.main --config /path/to/config.yaml
```

#### 3. Invalid Configuration

**Error:**
```
ValidationError: Distribution must sum to 1.0, got 1.2
```

**Solution:**
Ensure all distribution percentages sum to approximately 1.0 (0.99-1.01). Check:
- `payment_methods`
- `payment_status`
- `currencies`
- `countries`
- `merchant_categories`

#### 4. Azure SDK Not Installed

**Error:**
```
ImportError: azure-eventhub package not installed
```

**Solution:**
```bash
pip install azure-eventhub azure-identity
```

#### 5. Low Throughput

**Symptoms:** Simulator generating fewer transactions than expected

**Solutions:**
- Increase `batch_size` in output configuration
- Check Event Hub throughput limits
- Reduce `rate` if hitting network limits
- Check system resources (CPU, memory)

#### 6. Configuration Not Reloading

**Symptoms:** Changes to config file not taking effect

**Solution:**
- Ensure hot reload is enabled (default)
- Check file permissions
- Manually trigger reload: `kill -HUP <PID>`
- Restart simulator if needed

### Error Messages

#### Validation Errors

**Distribution Sum Error:**
```
ValidationError: Distribution must sum to 1.0, got 1.2
```
Fix: Adjust distribution percentages to sum to 1.0

**Invalid Amount Range:**
```
ValidationError: max must be greater than min
```
Fix: Ensure `max` > `min` in amount configuration

#### Connection Errors

**Event Hub Connection Failed:**
```
ConnectionError: Unable to connect to Event Hub
```
Fix: Verify connection string, check network, verify Event Hub exists

**Authentication Failed:**
```
AuthenticationError: Invalid credentials
```
Fix: Verify connection string, check Shared Access Key

### Performance Tuning

#### Increase Throughput

1. **Increase batch size:**
   ```yaml
   output:
     batch_size: 500  # Increase from default 100
   ```

2. **Increase rate:**
   ```yaml
   transaction:
     volume:
       rate: 2000  # Increase transactions per second
   ```

3. **Optimize Event Hub:**
   - Increase Event Hub throughput units
   - Use multiple partitions
   - Enable batching

#### Reduce Resource Usage

1. **Decrease batch size:**
   ```yaml
   output:
     batch_size: 50
   ```

2. **Lower generation rate:**
   ```yaml
   transaction:
     volume:
       rate: 10
   ```

3. **Disable metadata:**
   ```yaml
   metadata:
     include_ip_address: false
     include_user_agent: false
   ```

---

## Advanced Features

### Hot Reload

The simulator automatically reloads configuration when the file changes. This allows you to adjust settings without restarting:

1. Start simulator
2. Edit `config/simulator_config.yaml`
3. Save file
4. Configuration reloads automatically

### Signal Handling

The simulator handles signals gracefully:

- **SIGINT** (Ctrl+C): Graceful shutdown
- **SIGTERM**: Graceful shutdown
- **SIGHUP**: Reload configuration

### Logging

#### JSON Logging (Default)

```json
{
  "timestamp": "2025-12-05T14:30:00.123456",
  "level": "INFO",
  "logger": "simulator",
  "message": "Starting transaction generation",
  "module": "main",
  "function": "run",
  "line": 94
}
```

#### Text Logging

```yaml
logging:
  format: "text"
```

Output:
```
2025-12-05 14:30:00 - simulator - INFO - Starting transaction generation
```

#### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General information (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages only

### Metrics

The simulator tracks and logs metrics:

- Total transactions generated
- Total transactions published
- Total compliance violations
- Publishing rate
- Error rate
- Average latency

Metrics are logged at the end of simulation and can be accessed via publisher metrics.

### Environment Variables

The simulator supports environment variable references in configuration:

```yaml
output:
  connection_string: "${EVENTHUB_CONNECTION_STRING}"
```

This will read from the `EVENTHUB_CONNECTION_STRING` environment variable.

---

## Best Practices

### 1. Start Small

Begin with low volumes to verify configuration:

```yaml
transaction:
  volume:
    total: 100
    rate: 10
```

### 2. Use Hot Reload

Take advantage of hot reload to iterate on configuration without restarting.

### 3. Monitor Logs

Watch logs for errors and performance metrics:

```bash
tail -f simulator.log
```

### 4. Test Compliance Scenarios

Use compliance violations to test error handling:

```yaml
compliance:
  enabled: true
  total_violation_percentage: 0.20
```

### 5. Validate Configuration

Before running large volumes, validate your configuration:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/simulator_config.yaml'))"
```

---

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md) - System architecture overview
- [Testing Procedures](TESTING-PROCEDURES.md) - Testing guidelines
- [Configuration Example](../config/simulator_config.yaml.example) - Complete example configuration
- [Phase 2 Plan](PHASE-2-PLAN.md) - Development plan

---

## Support

For issues or questions:
1. Check this user guide
2. Review troubleshooting section
3. Check logs for error messages
4. Verify configuration file syntax
5. Review architecture documentation

---

**Version:** 1.0  
**Last Updated:** December 2025

