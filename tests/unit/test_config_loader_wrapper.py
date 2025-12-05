"""
Unit tests for config_loader.py wrapper.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from simulator.config_loader import load_simulator_config


class TestConfigLoaderWrapper:
    """Test config_loader wrapper functions."""
    
    def test_load_with_path(self, sample_config_file):
        """Test loading config with explicit path."""
        config = load_simulator_config(str(sample_config_file))
        
        assert config is not None
        assert config.simulator is not None
    
    def test_load_with_default_path(self):
        """Test loading config with default path."""
        # Mock the default path
        default_path = Path(__file__).parent.parent.parent / "config" / "simulator_config.yaml"
        
        if default_path.exists():
            config = load_simulator_config()
            assert config is not None
        else:
            # If default doesn't exist, should raise error
            with pytest.raises(Exception):
                load_simulator_config()
    
    def test_load_with_none_path(self):
        """Test loading config with None path (uses default)."""
        # Should use default path
        default_path = Path(__file__).parent.parent.parent / "config" / "simulator_config.yaml"
        
        if default_path.exists():
            config = load_simulator_config(None)
            assert config is not None
        else:
            with pytest.raises(Exception):
                load_simulator_config(None)

