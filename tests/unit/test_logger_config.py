"""
Unit tests for logger configuration.
"""

import pytest
import logging
import tempfile
from pathlib import Path

from simulator.logger_config import setup_logging, get_logger, JSONFormatter


class TestJSONFormatter:
    """Test JSONFormatter class."""
    
    def test_format_log_record(self):
        """Test formatting log record as JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert isinstance(result, str)
        assert "Test message" in result
        assert "timestamp" in result
        assert "level" in result
    
    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=(ValueError, ValueError("Test error"), None),
        )
        
        result = formatter.format(record)
        
        assert "exception" in result
        assert "Error message" in result


class TestSetupLogging:
    """Test setup_logging function."""
    
    def test_default_logging(self):
        """Test default logging setup."""
        logger = setup_logging()
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "simulator"
        assert logger.level == logging.INFO
    
    def test_custom_level(self):
        """Test custom log level."""
        logger = setup_logging(level="DEBUG")
        
        assert logger.level == logging.DEBUG
    
    def test_json_format(self):
        """Test JSON format."""
        logger = setup_logging(format_type="json")
        
        # Check that formatter is JSONFormatter
        handlers = logger.handlers
        assert len(handlers) > 0
        assert isinstance(handlers[0].formatter, JSONFormatter)
    
    def test_text_format(self):
        """Test text format."""
        logger = setup_logging(format_type="text")
        
        # Check that formatter is not JSONFormatter
        handlers = logger.handlers
        assert len(handlers) > 0
        assert not isinstance(handlers[0].formatter, JSONFormatter)
    
    def test_file_logging(self, tmp_path):
        """Test file logging."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file))
        
        logger.info("Test message")
        
        assert log_file.exists()
        assert "Test message" in log_file.read_text()
    
    def test_multiple_handlers(self, tmp_path):
        """Test multiple handlers (console + file)."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file))
        
        assert len(logger.handlers) == 2  # Console + file


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_default_logger(self):
        """Test getting default logger."""
        logger = get_logger()
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "simulator"
    
    def test_get_custom_logger(self):
        """Test getting custom logger."""
        logger = get_logger("custom")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "custom"

