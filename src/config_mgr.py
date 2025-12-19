import json
import os
from pathlib import Path
from typing import Any, Dict

# Define the path for the dynamic configuration file
CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / 'config' / 'local_settings.json'

DEFAULT_CONFIG = {
    "RISK_PERCENT": 2.0,
    "MIN_LIQUIDITY_IDR": 5000000000,
    "SL_ATR_MULTIPLIER": 2.0,
    "TP1_ATR_MULTIPLIER": 3.0,
    "HMA_PERIOD": 60,
    "SUPERTREND_MULTIPLIER": 3.0,
    "VOLUME_LOW_THRESHOLD": 0.8,
    "RS_STRONG": 5.0,
    "RS_WEAK": -5.0
}

class ConfigManager:
    """Manages dynamic configuration settings"""
    
    def __init__(self):
        self.config_path = CONFIG_FILE_PATH
        self._ensure_config_exists()
        
    def _ensure_config_exists(self):
        """Create config file with defaults if it doesn't exist"""
        if not self.config_path.exists():
            self._save_config(DEFAULT_CONFIG)
            
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to JSON file"""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return DEFAULT_CONFIG
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value"""
        config = self.get_all()
        return config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set a specific configuration value"""
        config = self.get_all()
        config[key] = value
        self._save_config(config)
        
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self._save_config(DEFAULT_CONFIG)

# Global instance
config_mgr = ConfigManager()
