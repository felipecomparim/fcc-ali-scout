import os
from typing import Dict, Any

PROPERTIES_PATH = os.path.join(os.path.dirname(__file__), "config.properties")

def load_properties() -> Dict[str, Any]:
    """Reads the config.properties file and returns a dictionary of configurations."""
    config = {
        "search.keywords": "fidget slider",
        "scrape.interval.minutes": 60,
        "max.products.per.day": 10,
        "use.mock.fallback": True,
        "database.type": "json",
        "database.path": "data/posts.json",
        "sqlite.path": "data/posts.db"
    }
    
    if not os.path.exists(PROPERTIES_PATH):
        return config
        
    try:
        with open(PROPERTIES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Type conversion
                    if value.lower() in ("true", "yes", "on"):
                        config[key] = True
                    elif value.lower() in ("false", "no", "off"):
                        config[key] = False
                    else:
                        try:
                            if "." in value:
                                config[key] = float(value)
                            else:
                                config[key] = int(value)
                        except ValueError:
                            config[key] = value
    except Exception as e:
        print(f"Error loading properties: {e}")
        
    return config

def save_properties(new_config: Dict[str, Any]) -> None:
    """Updates the config.properties file, keeping original keys and inserting new values."""
    # Load existing lines to preserve comments
    lines = []
    if os.path.exists(PROPERTIES_PATH):
        with open(PROPERTIES_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    updated_keys = set()
    output_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(";") and "=" in stripped:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            if key in new_config:
                val = new_config[key]
                # Format boolean as string
                if isinstance(val, bool):
                    val = "true" if val else "false"
                output_lines.append(f"{key}={val}\n")
                updated_keys.add(key)
                continue
        output_lines.append(line)
        
    # Append any keys that weren't in the original file
    for key, val in new_config.items():
        if key not in updated_keys:
            if isinstance(val, bool):
                val = "true" if val else "false"
            output_lines.append(f"{key}={val}\n")
            
    with open(PROPERTIES_PATH, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
