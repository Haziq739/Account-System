import os
import sys
from pathlib import Path

# Base Directory of the project
if getattr(sys, 'frozen', False):
    # If running as PyInstaller bundle, use the temporary extracted folder for assets
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Application Data Directory for Persistent Storage (Database, Logs)
APP_DIR_NAME = "K_Dynamics_System"
if os.name == 'nt':
    LOCAL_APP_DATA = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
else:
    LOCAL_APP_DATA = Path.home() / '.local' / 'share'
    
DATA_DIR = LOCAL_APP_DATA / APP_DIR_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_NAME = "K_Dynamics_System.db"
DATABASE_PATH = DATA_DIR / DATABASE_NAME
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Assets Configuration
ASSETS_DIR = BASE_DIR / "assets"
LOGO_K_DYNAMICS = ASSETS_DIR / "k_dynamics_logo.png"
LOGO_RN_SCANNER = ASSETS_DIR / "rn_scanner_logo.png"

# Logging Configuration
LOG_FILE = DATA_DIR / "app.log"

# Application Settings
APP_NAME = "RN Scanner and Digital Print House"
APP_VERSION = "1.0.1"
