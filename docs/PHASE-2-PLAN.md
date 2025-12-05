# Phase 2 Implementation Plan

## Overview

Phase 2 focuses on developing the **Payment Data Simulator** application - a Python-based tool for generating realistic payment transaction data to test and validate the ingestion pipeline.

## Work Order Summary

| # | Work Order | Status | Dependencies | Priority |
|---|------------|--------|--------------|----------|
| WO-5 | YAML Configuration Loader | ⏳ Ready | None | **1st** |
| WO-6 | Event Hub Publisher Integration | ⏳ Ready | None | **2nd** |
| WO-4 | Python Data Simulator | ⏳ Ready | WO-5, WO-6 | **3rd** |
| WO-7 | Unit Tests (90% Coverage) | ⏳ Backlog | WO-4 | **4th** |
| WO-8 | User Documentation | ⏳ Backlog | WO-4 | **5th** |

## Recommended Execution Order

```
┌─────────────┐
│   WO-5      │ ← Start here (no dependencies)
│ YAML Config │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   WO-6      │ ← Can start in parallel with WO-5
│Event Hub    │
│  Publisher  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   WO-4      │ ← Main application (uses WO-5 & WO-6)
│  Simulator  │
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│   WO-7      │ │   WO-8      │ ← Can do in parallel
│ Unit Tests  │ │  Docs       │
└─────────────┘ └─────────────┘
```

## Detailed Work Order Plans

---

## WO-5: YAML Configuration Loader

**Status:** Ready | **Priority:** 1st | **Estimated Time:** 2-3 hours

### Purpose
Create a configuration management system using YAML that allows flexible control of simulator behavior without code changes.

### Requirements
- ✅ YAML parser for `simulator_config.yaml` with validation
- ✅ Support transaction volumes, patterns, and data characteristics
- ✅ Schema validation to prevent invalid configurations
- ✅ Configuration reload capability without application restart

### Files to Create

```
src/simulator/
├── config/
│   ├── __init__.py
│   ├── loader.py          # Main YAML loader with validation
│   ├── schema.py          # Pydantic models for schema validation
│   └── validator.py       # Custom validation logic
└── config/
    └── simulator_config.yaml.example  # Example configuration
```

### Implementation Details

**Key Components:**
1. **YAML Parser** - Use `PyYAML` or `ruamel.yaml` for parsing
2. **Schema Validation** - Use Pydantic models for type safety
3. **Reload Mechanism** - File watcher or signal-based reload
4. **Default Values** - Sensible defaults for all configuration options

**Configuration Schema:**
```yaml
simulator:
  output:
    destination: "event_hub"  # event_hub, file, stdout
    batch_size: 100
    rate_limit: 1000  # events per second
  
  transaction:
    volume:
      total: 10000
      rate: 100  # per second
    patterns:
      payment_methods:
        credit_card: 0.6
        debit_card: 0.3
        bank_transfer: 0.1
      amounts:
        min: 1.00
        max: 10000.00
        distribution: "normal"  # normal, uniform, exponential
```

### Dependencies
- `PyYAML` or `ruamel.yaml`
- `pydantic` for schema validation
- `watchdog` (optional) for file watching

---

## WO-6: Event Hub Publisher Integration

**Status:** Ready | **Priority:** 2nd | **Estimated Time:** 3-4 hours

### Purpose
Create the publishing mechanism that sends generated payment transaction data to Azure Event Hubs.

### Requirements
- ✅ Event Hubs producer client with authentication
- ✅ Batch publishing for improved throughput
- ✅ Retry logic and error handling
- ✅ Monitoring and metrics collection

### Files to Create

```
src/simulator/
├── publishers/
│   ├── __init__.py
│   ├── base.py            # Abstract base publisher
│   ├── event_hub.py       # Azure Event Hub implementation
│   └── metrics.py         # Metrics collection
```

### Implementation Details

**Key Components:**
1. **Event Hub Client** - Use `azure-eventhub` SDK
2. **Authentication** - Support connection string and managed identity
3. **Batching** - Collect events and send in batches
4. **Retry Logic** - Exponential backoff with max retries
5. **Metrics** - Track publish rate, errors, latency

**Features:**
- Connection pooling
- Async publishing support
- Error recovery
- Connection health monitoring

### Dependencies
- `azure-eventhub` (>= 5.11.0)
- `azure-identity` for managed identity auth

---

## WO-4: Python Data Simulator Application

**Status:** Ready | **Priority:** 3rd | **Estimated Time:** 6-8 hours

### Purpose
Create a Python application that generates realistic payment transaction data for testing.

### Requirements
- ✅ Configurable transaction generation patterns
- ✅ Multiple payment types and realistic distributions
- ✅ Error handling and logging
- ✅ Containerizable and deployable

### Files to Create (9 files)

```
src/simulator/
├── __init__.py
├── main.py                    # Entry point
├── config_loader.py           # Uses WO-5
├── transaction_generator.py   # Core generation logic
├── event_publisher.py         # Uses WO-6
├── models.py                  # Pydantic models
└── logger_config.py          # Logging setup

config/
└── simulator_config.yaml      # Configuration file

Dockerfile                      # Containerization
requirements.txt                # Dependencies
```

### Implementation Details

**Main Components:**

1. **Transaction Generator** (`transaction_generator.py`)
   - Generate realistic payment transactions
   - Support multiple payment types
   - Configurable distributions (normal, uniform, exponential)
   - Use Faker for realistic data

2. **Models** (`models.py`)
   - Pydantic models for type safety
   - Transaction schema matching database
   - Validation rules

3. **Main Application** (`main.py`)
   - Orchestrate generation and publishing
   - Handle graceful shutdown
   - Signal handling for reload

4. **Logging** (`logger_config.py`)
   - Structured logging
   - Log levels configuration
   - Error tracking

### Payment Types to Support
- Credit Card
- Debit Card
- Bank Transfer
- Digital Wallet
- Cryptocurrency (optional)

### Data Realism
- Realistic customer names (Faker)
- Valid currency codes (ISO 4217)
- Realistic amounts with distributions
- Timestamp patterns (business hours, weekends)
- Geographic distribution

### Dependencies
- `faker` - Realistic data generation
- `pydantic` - Data validation
- `python-dotenv` - Environment variables
- WO-5 config loader
- WO-6 Event Hub publisher

---

## WO-7: Unit Tests (90% Coverage)

**Status:** Backlog | **Priority:** 4th | **Estimated Time:** 4-6 hours

### Purpose
Create comprehensive unit tests achieving >90% code coverage.

### Requirements
- ✅ >90% code coverage
- ✅ Tests for all modules
- ✅ Mock external dependencies
- ✅ Test fixtures and utilities
- ✅ Performance tests

### Files to Create

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_config_loader.py    # WO-5 tests
├── test_event_publisher.py  # WO-6 tests
├── test_transaction_generator.py
├── test_models.py
├── test_main.py
├── fixtures/
│   ├── sample_config.yaml
│   └── sample_transactions.json
└── utils/
    └── test_helpers.py
```

### Test Coverage Targets

| Module | Target Coverage | Key Test Areas |
|--------|----------------|----------------|
| config_loader | 95% | YAML parsing, validation, reload |
| event_publisher | 90% | Publishing, retries, error handling |
| transaction_generator | 95% | Generation logic, distributions |
| models | 100% | Validation, serialization |
| main | 85% | Orchestration, error handling |

### Testing Strategy
- **Unit Tests**: Mock all external dependencies
- **Integration Tests**: Test with real Event Hub (optional)
- **Performance Tests**: Measure throughput and latency
- **Fixtures**: Reusable test data

### Dependencies
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `pytest-asyncio` - Async test support
- `faker` - Test data generation

---

## WO-8: User Documentation

**Status:** Backlog | **Priority:** 5th | **Estimated Time:** 2-3 hours

### Purpose
Provide comprehensive user documentation for the simulator.

### Requirements
- ✅ Installation instructions
- ✅ Configuration documentation
- ✅ Usage examples
- ✅ Troubleshooting guide

### Files to Create

```
docs/
└── SIMULATOR-GUIDE.md        # Complete user guide

src/simulator/
└── README.md                 # Quick start guide
```

### Documentation Sections

1. **Installation**
   - Prerequisites
   - Installation steps
   - Docker setup

2. **Configuration**
   - Configuration file structure
   - All options explained
   - Example configurations

3. **Usage**
   - Basic usage
   - Advanced scenarios
   - Command-line options

4. **Examples**
   - Low volume testing
   - High volume load testing
   - Specific payment type testing

5. **Troubleshooting**
   - Common issues
   - Error messages
   - Performance tuning

---

## Project Structure (After Phase 2)

```
payments-ingestion/
├── src/
│   └── simulator/
│       ├── __init__.py
│       ├── main.py
│       ├── models.py
│       ├── logger_config.py
│       ├── config_loader.py      # WO-5
│       ├── transaction_generator.py
│       ├── event_publisher.py     # WO-6
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── schema.py
│       │   └── validator.py
│       └── publishers/
│           ├── __init__.py
│           ├── base.py
│           ├── event_hub.py
│           └── metrics.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_*.py
│   ├── fixtures/
│   └── utils/
├── config/
│   └── simulator_config.yaml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── docs/
    └── SIMULATOR-GUIDE.md
```

---

## Implementation Timeline

### Week 1: Foundation
- **Day 1-2**: WO-5 (YAML Configuration Loader)
- **Day 3-4**: WO-6 (Event Hub Publisher)
- **Day 5**: Integration testing of WO-5 + WO-6

### Week 2: Main Application
- **Day 1-3**: WO-4 (Data Simulator) - Core generation
- **Day 4**: WO-4 - Integration with WO-5 & WO-6
- **Day 5**: WO-4 - Dockerization and deployment

### Week 3: Quality & Documentation
- **Day 1-3**: WO-7 (Unit Tests)
- **Day 4**: WO-8 (Documentation)
- **Day 5**: Final integration testing and review

**Total Estimated Time:** 2-3 weeks

---

## Dependencies & Prerequisites

### Python Version
- Python 3.11+ (matches Function App runtime)

### Key Libraries
```python
# Core
pydantic>=2.0.0
pyyaml>=6.0
faker>=20.0.0

# Azure
azure-eventhub>=5.11.0
azure-identity>=1.15.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Development
black>=23.0.0
flake8>=6.1.0
mypy>=1.7.0
```

### Infrastructure Requirements
- Azure Event Hub (from Phase 1)
- Connection string or managed identity access
- Docker (for containerization)

---

## Success Criteria

### WO-5: Configuration Loader
- ✅ Loads YAML configuration successfully
- ✅ Validates schema and reports errors
- ✅ Supports hot reload
- ✅ Provides sensible defaults

### WO-6: Event Hub Publisher
- ✅ Publishes events successfully
- ✅ Handles batching efficiently
- ✅ Implements retry logic
- ✅ Collects metrics

### WO-4: Data Simulator
- ✅ Generates realistic payment transactions
- ✅ Supports all required payment types
- ✅ Configurable via YAML
- ✅ Containerizable
- ✅ Integrates with Event Hub

### WO-7: Unit Tests
- ✅ >90% code coverage achieved
- ✅ All modules tested
- ✅ Performance tests included
- ✅ CI/CD integration

### WO-8: Documentation
- ✅ Complete installation guide
- ✅ Configuration reference
- ✅ Usage examples
- ✅ Troubleshooting guide

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Event Hub connection issues | High | Implement robust retry logic, connection pooling |
| Configuration complexity | Medium | Use Pydantic for validation, provide examples |
| Performance bottlenecks | Medium | Profile and optimize, use async where possible |
| Test coverage gaps | Low | Set coverage threshold in CI, enforce in PRs |

---

## Next Steps

1. **Review this plan** with the team
2. **Start with WO-5** (YAML Configuration Loader)
3. **Proceed sequentially** through the work orders
4. **Integrate continuously** - test each component as it's built
5. **Document as you go** - keep documentation updated

---

**Ready to begin Phase 2!** 🚀

Would you like me to start with WO-5 (YAML Configuration Loader)?

