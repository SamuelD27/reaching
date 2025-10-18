"""
Configuration Management System
Handles loading from config.yaml and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """
    Configuration manager with defaults

    Priority (high to low):
    1. Environment variables
    2. config.yaml
    3. Defaults
    """

    DEFAULT_CONFIG = {
        'rocketreach': {
            'base_url': 'https://api.rocketreach.co/v2/api',
            'timeout': 30,
            'rate_limits': {
                'minute': {'limit': 10, 'window': 60},
                'hour': {'limit': 35, 'window': 3600},
                'day': {'limit': 350, 'window': 86400}
            }
        },
        'extraction': {
            'max_total_contacts': 500,
            'max_per_company': 20,
            'batch_size': 10,
            'checkpoint_enabled': True,
            'checkpoint_interval': 10  # Save every N contacts
        },
        'output': {
            'format': 'xlsx',  # xlsx, csv, or json
            'directory': './output',
            'timestamp_filenames': True
        },
        'verification': {
            'enabled': True,
            'timeout': 15,
            'max_workers': 3
        },
        'logging': {
            'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
            'file': 'extraction.log',
            'max_bytes': 10485760,  # 10MB
            'backup_count': 5
        }
    }

    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize configuration

        Args:
            config_file: Path to config YAML file
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment"""
        # Start with defaults
        config = self.DEFAULT_CONFIG.copy()

        # Load from YAML if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config = self._deep_merge(config, file_config)
            except Exception as e:
                print(f"⚠️  Error loading config file: {e}")
                print(f"   Using defaults")

        # Override with environment variables
        config = self._load_env_overrides(config)

        return config

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _load_env_overrides(self, config: Dict) -> Dict:
        """Override config with environment variables"""
        # API Key (required)
        api_key = os.getenv("ROCKETREACH_API_KEY")
        if api_key:
            if 'rocketreach' not in config:
                config['rocketreach'] = {}
            config['rocketreach']['api_key'] = api_key

        # Max contacts
        max_contacts = os.getenv("MAX_TOTAL_CONTACTS")
        if max_contacts:
            try:
                config['extraction']['max_total_contacts'] = int(max_contacts)
            except ValueError:
                pass

        # Output format
        output_format = os.getenv("OUTPUT_FORMAT")
        if output_format:
            config['output']['format'] = output_format.lower()

        # Log level
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            config['logging']['level'] = log_level.upper()

        return config

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Path to config value (e.g., 'extraction.max_total_contacts')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation

        Args:
            key_path: Path to config value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, file_path: Optional[str] = None) -> None:
        """
        Save configuration to YAML file

        Args:
            file_path: Path to save to (defaults to config.yaml)
        """
        file_path = Path(file_path) if file_path else self.config_file

        try:
            # Don't save API key to file
            config_to_save = self.config.copy()
            if 'rocketreach' in config_to_save and 'api_key' in config_to_save['rocketreach']:
                del config_to_save['rocketreach']['api_key']

            with open(file_path, 'w') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, sort_keys=False)

            print(f"✅ Configuration saved to {file_path}")
        except Exception as e:
            print(f"⚠️  Error saving configuration: {e}")

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like setting"""
        self.config[key] = value


# Create example config file
def create_example_config():
    """Create config.example.yaml"""
    example_config = {
        'rocketreach': {
            'timeout': 30,
            'rate_limits': {
                'minute': {'limit': 10, 'window': 60},
                'hour': {'limit': 35, 'window': 3600},
                'day': {'limit': 350, 'window': 86400}
            }
        },
        'extraction': {
            'max_total_contacts': 500,
            'max_per_company': 20,
            'batch_size': 10
        },
        'output': {
            'format': 'xlsx',
            'directory': './output'
        },
        'verification': {
            'enabled': True,
            'timeout': 15
        }
    }

    with open('config.example.yaml', 'w') as f:
        yaml.dump(example_config, f, default_flow_style=False)

    print("✅ Created config.example.yaml")


# Example usage
if __name__ == "__main__":
    # Create example config
    create_example_config()

    # Load config
    config = Config()

    # Access values
    print(f"Max contacts: {config.get('extraction.max_total_contacts')}")
    print(f"Output format: {config.get('output.format')}")
    print(f"Rate limit (minute): {config.get('rocketreach.rate_limits.minute.limit')}")

    # Set value
    config.set('extraction.max_total_contacts', 1000)
    print(f"Updated max contacts: {config.get('extraction.max_total_contacts')}")

    # Access with dict notation
    print(f"Logging level: {config['logging']['level']}")
