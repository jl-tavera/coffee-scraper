import os
import json
from dotenv import dotenv_values

def load_config_json(config_filename="config.json"):
    """
    Load configuration from a JSON file 
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, "../../"))
    config_path = os.path.join(root_dir, config_filename)
    with open(config_path, "r") as f:
        return json.load(f)


def load_env_variables(env_path=".env"):
    """
    Load environment variables from a .env file
    """
    return dotenv_values(env_path)
