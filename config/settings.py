import os
from pathlib import Path

# Base Directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Database Configuration
DATABASE_NAME = "K_Dynamics_System.db"
DATABASE_PATH = BASE_DIR / DATABASE_NAME
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Assets Configuration
ASSETS_DIR = BASE_DIR / "assets"
LOGO_K_DYNAMICS = ASSETS_DIR / "k_dynamics_logo.png"
LOGO_RN_SCANNER = ASSETS_DIR / "rn_scanner_logo.png"

# Logging Configuration
LOG_FILE = BASE_DIR / "app.log"

# Application Settings
APP_NAME = "RN Scanner and Digital Print House"
APP_VERSION = "1.0.0"
