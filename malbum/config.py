import json
import os
from pathlib import Path
from django.conf import settings

# Use environment variable for config directory or fall back to BASE_DIR
CONFIG_DIR = os.getenv('CONFIG_DIR', str(settings.BASE_DIR))
CONFIG_FILE = Path(CONFIG_DIR) / 'config' / 'config.json'

def get_default_config():
    return {
        'dominio': '',
        'clave_activitypub': ''
    }

def load_config():
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return get_default_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return get_default_config()

def save_config(config):
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_valor(clave, default=None):
    config = load_config()
    return config.get(clave, default)

def set_valor(clave, valor):
    config = load_config()
    config[clave] = valor
    return save_config(config) 