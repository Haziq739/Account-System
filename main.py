import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from ui.auth.splash_screen import SplashScreen
from ui.main_window import MainWindow
from ui.auth.setup_window import SetupWindow
from ui.auth.login_window import LoginWindow
from ui.auth.signup_window import SignupWindow
from utils.logger import logger
from services.auth import AuthService


class ApplicationManager:
    """Manages top-level window navigation."""

    def __init__(self):
        self._win = None

    def start(self):
        logger.info("Showing splash screen.")
        splash = SplashScreen()
        splash.splash_done.connect(self._after_splash)
        splash.show()
        self._win = splash

    def _after_splash(self):
        if AuthService.is_first_run():
            logger.info("First run — showing setup window.")
            self._show_setup()
        else:
            settings = QSettings("KDynamics", "RNScanner")
            user_id = settings.value("last_logged_in_user_id")
            if user_id:
                user = AuthService.get_user_by_id(int(user_id))
                if user:
                    logger.info("Auto-login triggered.")
                    self._show_main(user)
                    return
            
            logger.info("Users exist — showing login window.")
            self._show_login()

    # ── Setup (first-run) ──────────────────────────────────────────────────────
    def _show_setup(self):
        self._close_current()
        w = SetupWindow()
        w.setup_successful.connect(self._show_login)
        w.show()
        self._win = w

    # ── Login ──────────────────────────────────────────────────────────────────
    def _show_login(self):
        self._close_current()
        w = LoginWindow()
        w.login_successful.connect(self._on_login_successful)
        w.go_signup.connect(self._show_signup)
        w.show()
        self._win = w

    # ── Signup ─────────────────────────────────────────────────────────────────
    def _show_signup(self):
        self._close_current()
        w = SignupWindow()
        w.signup_successful.connect(self._show_login)
        w.back_to_login.connect(self._show_login)
        w.show()
        self._win = w

    # ── Main dashboard ─────────────────────────────────────────────────────────
    def _on_login_successful(self, user: dict):
        settings = QSettings("KDynamics", "RNScanner")
        settings.setValue("last_logged_in_user_id", user["id"])
        self._show_main(user)

    def _show_main(self, user: dict):
        self._close_current()
        logger.info(f"User '{user['username']}' logged in.")
        w = MainWindow(user)
        w.showMaximized()
        self._win = w

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _close_current(self):
        if self._win:
            self._win.close()
            self._win = None


def migrate_quotation_pdfs():
    """Migrate any existing Quotation PDFs from invoices/ to quotations/."""
    import os, shutil
    invoices_dir = os.path.join(os.getcwd(), "invoices")
    quotations_dir = os.path.join(os.getcwd(), "quotations")
    os.makedirs(quotations_dir, exist_ok=True)
    if os.path.exists(invoices_dir):
        for f in os.listdir(invoices_dir):
            if f.startswith("Quotation-") and f.endswith(".pdf"):
                src = os.path.join(invoices_dir, f)
                dst = os.path.join(quotations_dir, f)
                if not os.path.exists(dst):
                    try:
                        shutil.move(src, dst)
                    except Exception:
                        pass

def main():
    logger.info("Starting RN Scanner Business Management System")
    
    # Ensure database schema exists
    from database.connection import engine
    from models import Base
    Base.metadata.create_all(engine)
    logger.info("Database schema verified.")
    
    # Seed required company data
    AuthService.seed_companies()
    
    # Organize legacy quotation files
    migrate_quotation_pdfs()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Fix QComboBox dropdown popup colors globally.
    # Without this, the Fusion style renders dropdown popups with its own
    # default colors (near-black) regardless of per-dialog stylesheets.
    from ui.design_system import COLORS, init_theme
    init_theme()
    # Cleared broken stylesheet

    manager = ApplicationManager()
    manager.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
