"""
Unit tests for configuration loader.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from simulator.config.loader import ConfigLoader, load_config, ConfigFileHandler
from simulator.config.schema import SimulatorConfig


class TestConfigLoader:
    """Test ConfigLoader class."""
    
    def test_load_config_file_not_found(self, tmp_path):
        """Test loading non-existent config file."""
        config_file = tmp_path / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            ConfigLoader(str(config_file))
    
    def test_load_config_success(self, sample_config_file):
        """Test successful config loading."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=False)
        config = loader.load()
        
        assert isinstance(config, SimulatorConfig)
        assert config.simulator is not None
    
    def test_get_config_before_load(self, sample_config_file):
        """Test getting config before loading."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=False)
        
        with pytest.raises(RuntimeError):
            loader.get_config()
    
    def test_get_config_after_load(self, sample_config_file):
        """Test getting config after loading."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=False)
        loader.load()
        config = loader.get_config()
        
        assert isinstance(config, SimulatorConfig)
    
    def test_reload_config(self, sample_config_file):
        """Test reloading configuration."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=False)
        config1 = loader.load()
        
        # Modify config file
        with open(sample_config_file, "r") as f:
            data = yaml.safe_load(f)
        data["simulator"]["output"]["batch_size"] = 200
        
        with open(sample_config_file, "w") as f:
            yaml.dump(data, f)
        
        config2 = loader.reload()
        
        assert config2.simulator["output"]["batch_size"] == 200
    
    def test_register_reload_callback(self, sample_config_file):
        """Test registering reload callbacks."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=False)
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        loader.register_reload_callback(callback)
        loader.load()
        
        # Manually trigger callback
        loader._handle_reload_signal(None, None)
        
        assert len(callback_called) == 1
    
    def test_file_watcher_start(self, sample_config_file):
        """Test starting file watcher."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=True)
        loader.load()
        
        assert loader.observer is not None
        loader.stop()
    
    def test_file_watcher_stop(self, sample_config_file):
        """Test stopping file watcher."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=True)
        loader.load()
        loader.stop()
        
        assert loader.observer is None
    
    def test_config_file_handler(self, sample_config_file):
        """Test ConfigFileHandler."""
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        handler = ConfigFileHandler(str(sample_config_file), callback)
        
        # Simulate file modification
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(str(sample_config_file))
        handler.on_modified(event)
        
        assert len(callback_called) == 1
    
    def test_config_file_handler_ignore_other_files(self, sample_config_file, tmp_path):
        """Test ConfigFileHandler ignores other files."""
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        handler = ConfigFileHandler(str(sample_config_file), callback)
        
        # Simulate modification of different file
        other_file = tmp_path / "other.yaml"
        other_file.touch()
        
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(str(other_file))
        handler.on_modified(event)
        
        assert len(callback_called) == 0
    
    def test_load_config_convenience_function(self, sample_config_file):
        """Test load_config convenience function."""
        config = load_config(str(sample_config_file), enable_reload=False)
        
        assert isinstance(config, SimulatorConfig)
    
    def test_empty_yaml_file(self, tmp_path):
        """Test loading empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        loader = ConfigLoader(str(config_file), enable_reload=False)
        # Empty YAML loads as None, which becomes {}
        config = loader.load()
        assert config is not None
        # Will have defaults from SimulatorConfig
    
    def test_invalid_yaml_file(self, tmp_path):
        """Test loading invalid YAML file."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        loader = ConfigLoader(str(config_file), enable_reload=False)
        with pytest.raises(Exception):  # Should raise YAMLError
            loader.load()
    
    def test_on_config_changed_success(self, sample_config_file):
        """Test successful config change handling."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=True)
        loader.load()
        
        callback_called = []
        
        def callback(old, new):
            callback_called.append((old, new))
        
        loader.register_reload_callback(callback)
        loader._on_config_changed()
        
        assert len(callback_called) == 1
    
    def test_on_config_changed_error(self, sample_config_file):
        """Test config change handling with error."""
        loader = ConfigLoader(str(sample_config_file), enable_reload=True)
        loader.load()
        
        # Corrupt the file
        sample_config_file.write_text("invalid: [")
        
        # Should handle error gracefully
        loader._on_config_changed()  # Should not raise

