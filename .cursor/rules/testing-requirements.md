# Testing Requirements for Payments Ingestion Project

## Mandatory Testing Standards

### Code Coverage Requirements
- **Minimum Coverage:** 90% for all new code and changes
- **Target Coverage:** 95% for critical components
- **Coverage Measurement:** Use `pytest --cov` with `pytest-cov` plugin

### Test Requirements for New Code

1. **Unit Tests (Required)**
   - All new functions, classes, and methods MUST have unit tests
   - Test all code paths including error cases
   - Test edge cases and boundary conditions
   - Mock external dependencies (databases, APIs, file systems)
   - Use pytest fixtures for test data and setup

2. **API/Contract Tests (Required)**
   - All public APIs MUST have contract/integration tests
   - Test API interfaces and contracts
   - Test data models and serialization/deserialization
   - Test error responses and validation
   - Test integration between components

3. **Test File Naming**
   - Test files MUST be named `test_<module_name>.py`
   - Place tests in `tests/` directory mirroring `src/` structure
   - Example: `src/function_app/messaging/message.py` → `tests/function_app/messaging/test_message.py`

4. **Test Structure**
   - Use pytest framework
   - Group related tests in classes
   - Use descriptive test names: `test_<functionality>_<scenario>`
   - Example: `test_get_body_as_dict_with_invalid_json()`

### Test Coverage Enforcement

1. **Before Committing**
   - Run `pytest --cov=src/<module> --cov-report=term-missing`
   - Ensure coverage is at least 90%
   - Fix any failing tests before committing

2. **CI/CD Integration**
   - All tests MUST pass in CI/CD pipeline
   - Coverage reports are generated automatically
   - Coverage below 90% will fail the build

3. **New Components Checklist**
   - [ ] Unit tests created for all functions/classes
   - [ ] API/contract tests created for all public interfaces
   - [ ] Edge cases and error paths tested
   - [ ] Coverage verified at 90%+ for new code
   - [ ] All tests passing locally
   - [ ] Test fixtures and mocks properly configured

### Test Quality Standards

1. **Test Independence**
   - Tests MUST be independent (no shared state)
   - Use fixtures for setup/teardown
   - Clean up resources after each test

2. **Test Clarity**
   - Tests MUST be readable and self-documenting
   - Use descriptive assertions
   - Include comments for complex test scenarios

3. **Mock Usage**
   - Mock external dependencies (databases, APIs, file I/O)
   - Use `unittest.mock` or `pytest-mock`
   - Verify mock calls when appropriate

4. **Performance Tests**
   - Include performance tests for critical paths
   - Test throughput and latency requirements
   - Use pytest-benchmark for performance testing

### Exceptions

The following may have lower coverage (but still require tests):
- System-level integration code (main() entry points)
- Azure SDK integration code (requires complex mocking)
- Rare edge cases that are difficult to trigger

**Note:** Even exceptions should have at least basic tests and be documented.

### Testing Tools

- **Framework:** pytest
- **Coverage:** pytest-cov
- **Mocking:** unittest.mock, pytest-mock
- **Fixtures:** pytest fixtures in `conftest.py`
- **Assertions:** pytest assertions, assert statements

### Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from src.function_app.messaging import Message, MessageBatch

class TestMessage:
    """Tests for Message dataclass."""
    
    def test_message_creation(self):
        """Test basic message creation."""
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            body='{"key": "value"}'
        )
        assert msg.message_id == "msg-1"
        assert msg.correlation_id == "corr-1"
    
    def test_get_body_as_dict_valid_json(self):
        """Test parsing valid JSON body."""
        msg = Message(..., body='{"amount": 100.0}')
        data = msg.get_body_as_dict()
        assert data["amount"] == 100.0
    
    def test_get_body_as_dict_invalid_json(self):
        """Test handling invalid JSON gracefully."""
        msg = Message(..., body="invalid json")
        data = msg.get_body_as_dict()
        assert data == {}  # Should return empty dict, not raise
```

---

**Last Updated:** December 5, 2025  
**Enforcement:** Mandatory for all new code and changes

