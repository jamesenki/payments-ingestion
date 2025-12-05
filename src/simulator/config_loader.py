"""
Configuration loader wrapper that integrates with WO-5 config loader.
"""

from typing import Optional
from pathlib import Path

from .config.loader import ConfigLoader, load_config
from .config.schema import SimulatorConfig


def load_simulator_config(config_path: Optional[str] = None) -> SimulatorConfig:
    """
    Load simulator configuration from YAML file.
    
    Args:
        config_path: Path to configuration file. If None, uses default.
        
    Returns:
        SimulatorConfig instance
    """
    if config_path is None:
        # Default to config/simulator_config.yaml
        config_path = Path(__file__).parent.parent.parent / "config" / "simulator_config.yaml"
    
    return load_config(str(config_path), enable_reload=True)

