"""
YAML configuration loader with validation and reload capability.
"""

import os
import yaml
import signal
from pathlib import Path
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .schema import SimulatorConfig


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes."""
    
    def __init__(self, config_path: str, reload_callback: Callable):
        self.config_path = config_path
        self.reload_callback = reload_callback
        super().__init__()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.src_path == self.config_path:
            self.reload_callback()


class ConfigLoader:
    """
    Configuration loader with YAML parsing, validation, and hot reload.
    
    Features:
    - YAML file parsing
    - Pydantic schema validation
    - Hot reload on file changes
    - Signal-based reload (SIGHUP)
    - Default value handling
    """
    
    def __init__(self, config_path: str, enable_reload: bool = True):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
            enable_reload: Enable file watching for hot reload
        """
        self.config_path = Path(config_path)
        self.enable_reload = enable_reload
        self.config: Optional[SimulatorConfig] = None
        self.reload_callbacks: list[Callable] = []
        self.observer: Optional[Observer] = None
        
        # Validate file exists
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Setup signal handler for reload
        if enable_reload:
            signal.signal(signal.SIGHUP, self._handle_reload_signal)
    
    def load(self) -> SimulatorConfig:
        """
        Load and validate configuration from YAML file.
        
        Returns:
            Validated SimulatorConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValidationError: If schema validation fails
        """
        with open(self.config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        if raw_config is None:
            raw_config = {}
        
        # Validate with Pydantic
        self.config = SimulatorConfig(**raw_config)
        
        # Start file watcher if enabled
        if self.enable_reload:
            self._start_file_watcher()
        
        return self.config
    
    def reload(self) -> SimulatorConfig:
        """
        Reload configuration from file.
        
        Returns:
            Updated SimulatorConfig instance
        """
        return self.load()
    
    def get_config(self) -> SimulatorConfig:
        """
        Get the current configuration.
        
        Returns:
            Current SimulatorConfig instance
            
        Raises:
            RuntimeError: If config hasn't been loaded yet
        """
        if self.config is None:
            raise RuntimeError("Configuration not loaded. Call load() first.")
        return self.config
    
    def register_reload_callback(self, callback: Callable):
        """
        Register a callback to be invoked on configuration reload.
        
        Args:
            callback: Function to call when config is reloaded
        """
        self.reload_callbacks.append(callback)
    
    def _handle_reload_signal(self, signum, frame):
        """Handle SIGHUP signal for manual reload."""
        self.reload()
        for callback in self.reload_callbacks:
            callback()
    
    def _start_file_watcher(self):
        """Start watching the configuration file for changes."""
        if self.observer is not None:
            return  # Already watching
        
        event_handler = ConfigFileHandler(
            str(self.config_path),
            self._on_config_changed
        )
        
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            path=str(self.config_path.parent),
            recursive=False
        )
        self.observer.start()
    
    def _on_config_changed(self):
        """Handle configuration file change."""
        try:
            old_config = self.config
            new_config = self.reload()
            
            # Notify callbacks
            for callback in self.reload_callbacks:
                callback(old_config, new_config)
            
            print(f"Configuration reloaded from {self.config_path}")
        except Exception as e:
            print(f"Error reloading configuration: {e}")
    
    def stop(self):
        """Stop file watching."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None


def load_config(config_path: str, enable_reload: bool = True) -> SimulatorConfig:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Path to YAML configuration file
        enable_reload: Enable hot reload
        
    Returns:
        Validated SimulatorConfig instance
    """
    loader = ConfigLoader(config_path, enable_reload)
    return loader.load()

