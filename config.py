from pathlib import Path
import json, os
APP_NAME="OptiSys"; VERSION="20.0.0"
HOME=Path(os.environ.get("APPDATA",Path.home()))/"OptiSys"
DATA_DIR=HOME/"data"; CACHE_DIR=HOME/"cache"; CONFIG_FILE=HOME/"config.json"; DB_FILE=DATA_DIR/"optisys.sqlite3"
for p in (HOME,DATA_DIR,CACHE_DIR): p.mkdir(parents=True,exist_ok=True)
DEFAULT_CONFIG={"photoshop":"","lightroom":"","last_import":"","last_export":""}
def load_config():
    if not CONFIG_FILE.exists(): return DEFAULT_CONFIG.copy()
    try: return {**DEFAULT_CONFIG,**json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
    except Exception: return DEFAULT_CONFIG.copy()
def save_config(data): CONFIG_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8")
