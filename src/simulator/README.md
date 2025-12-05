# Payment Data Simulator

A Python application for generating realistic payment transaction data to test and validate the payments ingestion pipeline.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set Event Hub connection string
export EVENTHUB_CONNECTION_STRING="Endpoint=sb://..."
```

### Basic Usage

```bash
# Run with default configuration
python -m src.simulator.main

# Run with custom configuration
python -m src.simulator.main --config /path/to/config.yaml
```

### Docker

```bash
# Build image
docker build -t payment-simulator .

# Run container
docker run -e EVENTHUB_CONNECTION_STRING="..." payment-simulator
```

## Configuration

The simulator uses a YAML configuration file (`config/simulator_config.yaml`). See the [example configuration](../config/simulator_config.yaml.example) for all available options.

Key configuration sections:
- **Output**: Event Hub destination and batching
- **Transaction**: Volume and variability settings
- **Compliance**: Violation generation settings
- **Metadata**: Optional transaction metadata
- **Logging**: Log level and format

## Features

- ✅ Realistic payment transaction generation
- ✅ Configurable data variability (amounts, methods, currencies)
- ✅ Compliance violation generation (AML, KYC, PCI, data quality)
- ✅ Azure Event Hub integration
- ✅ Hot reload configuration
- ✅ Performance metrics and logging

## Documentation

For detailed documentation, see:
- **[Complete User Guide](../docs/SIMULATOR-USER-GUIDE.md)** - Comprehensive guide with all options
- **[Configuration Reference](../config/simulator_config.yaml.example)** - Example configuration file
- **[Architecture Overview](../docs/ARCHITECTURE.md)** - System architecture

## Examples

### Generate 1000 transactions
```yaml
# config/simulator_config.yaml
simulator:
  transaction:
    volume:
      total: 1000
      rate: 100
```

### High volume load test
```yaml
simulator:
  transaction:
    volume:
      duration: 3600  # Run for 1 hour
      rate: 1000      # 1000 transactions/second
```

### Compliance testing
```yaml
compliance:
  enabled: true
  total_violation_percentage: 0.10  # 10% violations
```

## Troubleshooting

See the [User Guide](../docs/SIMULATOR-USER-GUIDE.md#troubleshooting) for common issues and solutions.

## Support

For issues or questions, refer to:
- [User Guide](../docs/SIMULATOR-USER-GUIDE.md)
- [Testing Procedures](../docs/TESTING-PROCEDURES.md)
- [Architecture Documentation](../docs/ARCHITECTURE.md)

