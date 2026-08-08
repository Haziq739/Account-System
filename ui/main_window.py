from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal
from datetime import date as _date
from config.settings import APP_NAME, APP_VERSION
from ui.design_system import get_auth_stylesheet, COLORS
from ui.auth.setup_window import center_window
from ui.components.sidebar import Sidebar
from ui.components.header import Header
from ui.components.header import Header


class PlaceholderPage(QWidget):
    """Temporary page for unimplemented sidebar links."""
    def __init__(self, title: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"{title} Module\n(Coming in Future Phase)")
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)


class MainWindow(QMainWindow):
    """Main application shell holding sidebar, header, and pages."""
    theme_changed = Signal()

    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.active_company_id = None
        self.setWindowTitle(f"{APP_NAME}  —  v{APP_VERSION}")
        self.setMinimumSize(1024, 720)
        self.resize(1200, 800)
        center_window(self)
        self.setStyleSheet(get_auth_stylesheet() + f"""
            QMainWindow {{ background-color: {COLORS['bg_app']}; }}
        """)
        self._build_ui()
        self._setup_midnight_timer()
        
    def refresh_theme(self):
        active_company_id = self.active_company_id
        current_page_idx = self.pages.currentIndex()
        page_name = None
        for name, idx in self.page_map.items():
            if idx == current_page_idx:
                page_name = name
                break

        self.setStyleSheet(get_auth_stylesheet() + f"""
            QMainWindow {{ background-color: {COLORS['bg_app']}; }}
        """)
        
        self._build_ui()
        
        if active_company_id:
            idx = self.header.company_combo.findData(active_company_id)
            if idx >= 0:
                self.header.company_combo.setCurrentIndex(idx)
        if page_name:
            self._navigate_to(page_name)

    def _setup_midnight_timer(self):
        """Check every 60 seconds if the day has changed and auto-save Day Book PDF."""
        self._last_saved_daybook_date = _date.today()
        self._midnight_timer = QTimer(self)
        self._midnight_timer.timeout.connect(self._check_midnight_daybook)
        self._midnight_timer.start(60_000)  # fire every 60 seconds

    def _check_midnight_daybook(self):
        """If the calendar date has changed, generate Day Book PDF for the previous day."""
        today = _date.today()
        if today != self._last_saved_daybook_date:
            prev_day = self._last_saved_daybook_date
            self._last_saved_daybook_date = today
            if self.active_company_id:
                self._auto_save_daybook_pdf(self.active_company_id, prev_day)

    def _auto_save_daybook_pdf(self, company_id: int, target_date):
        """Background generation of Day Book PDF — does NOT block the UI."""
        try:
            from PySide6.QtCore import QThread, Signal
            from services.daybook_service import DayBookService

            class _DayBookAutoWorker(QThread):
                def __init__(self, cid, tdate):
                    super().__init__()
                    self.cid = cid
                    self.tdate = tdate

                def run(self):
                    try:
                        from services.pdf_generator import PDFGenerator
                        data = DayBookService.get_daybook_transactions(self.cid, self.tdate)
                        PDFGenerator.generate_daybook_pdf(self.cid, self.tdate, data)
                    except Exception as e:
                        from utils.logger import logger
                        logger.error(f"Auto Day Book PDF error: {e}")

            self._daybook_auto_worker = _DayBookAutoWorker(company_id, target_date)
            self._daybook_auto_worker.start()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Day Book auto-save setup error: {e}")

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central_widget")
        central.setStyleSheet(f"QWidget#central_widget {{ background-color: {COLORS['bg_app']}; }}")
        self.setCentralWidget(central)

        # Main horizontal layout: [ Sidebar | Right Area ]
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────────
        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self._navigate_to)
        main_layout.addWidget(self.sidebar)

        # ── Right Area ──────────────────────────────────────────────────────
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header
        self.header = Header(self.current_user)
        self.header.company_changed.connect(self._on_company_changed)
        right_layout.addWidget(self.header)

        # Pages (QStackedWidget)
        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages)
        
        main_layout.addWidget(right_area)

        # Setup Pages
        self.page_map = {}
        
        # Determine initial company ID from header
        if self.header.companies:
            self.active_company_id = self.header.companies[0]["id"]
        
        from ui.pages.customers_page import CustomersPage
        self.customers_page = CustomersPage(self.current_user, context="regular")
        self._add_page("customers", self.customers_page)
        
        from ui.pages.services_page import ServicesPage
        self.services_page = ServicesPage(self.current_user)
        self._add_page("services", self.services_page)
        
        from ui.pages.invoices_page import InvoicesPage
        self.invoices_page = InvoicesPage(self.current_user, context="regular")
        if self.active_company_id:
            self.invoices_page.set_company(self.active_company_id)
        self._add_page("invoices", self.invoices_page)
        
        from ui.pages.quotations_page import QuotationsPage
        self.quotations_page = QuotationsPage(self.current_user, context="regular")
        if self.active_company_id:
            self.quotations_page.set_company(self.active_company_id)
        self._add_page("quotations", self.quotations_page)
        
        from ui.pages.ledger_page import LedgerPage
        self.ledger_page = LedgerPage(self.active_company_id, context="regular")
        self._add_page("ledger", self.ledger_page)
        
        # --- Day Book Page ---
        from ui.pages.daybook_page import DayBookPage
        self.day_book_page = DayBookPage(self.active_company_id, self.current_user)
        self._add_page("day_book", self.day_book_page)
        
        # --- Vendor Pages ---
        from ui.pages.vendors_page import VendorsPage
        self.vendors_page = VendorsPage({"id": self.active_company_id} if self.active_company_id else None, self.current_user)
        self._add_page("vendors", self.vendors_page)
        
        from ui.pages.vendor_bills_page import VendorBillsPage
        self.vendor_bills_page = VendorBillsPage(self.current_user)
        if self.active_company_id:
            self.vendor_bills_page.set_company(self.active_company_id)
        self._add_page("vendor_bills", self.vendor_bills_page)
        
        # --- Employees Page ---
        from ui.pages.employees_page import EmployeesPage
        self.employees_page = EmployeesPage({"id": self.active_company_id} if self.active_company_id else None, self.current_user)
        self._add_page("employees", self.employees_page)

        # --- Backup Page ---
        from ui.pages.backup_page import BackupPage
        initial_company_dict = None
        if self.active_company_id and self.header.companies:
            for c in self.header.companies:
                if c["id"] == self.active_company_id:
                    initial_company_dict = c
                    break
        self.backup_page = BackupPage(current_company=initial_company_dict, current_user=self.current_user)
        self._add_page("backup", self.backup_page)
        
        from ui.pages.settings_page import SettingsPage
        self.settings_page = SettingsPage()
        self.settings_page.theme_changed.connect(self.refresh_theme)
        self._add_page("settings", self.settings_page)

    def _add_page(self, name: str, widget: QWidget):
        idx = self.pages.addWidget(widget)
        self.page_map[name] = idx

    def _navigate_to(self, page_name: str):
        if page_name in self.page_map:
            self.pages.setCurrentIndex(self.page_map[page_name])
            if hasattr(self, 'sidebar'):
                self.sidebar.set_active(page_name)
            if page_name == "ledger" and hasattr(self, 'ledger_page'):
                self.ledger_page.refresh_data()
            if page_name == "db_ledger" and hasattr(self, 'db_ledger_page'):
                self.db_ledger_page.refresh_data()
            if page_name == "employees" and hasattr(self, 'employees_page'):
                self.employees_page.refresh_data()

    def _on_company_changed(self, company_id: int):
        self.active_company_id = company_id
        # Notify pages that care about the active company
        
        if hasattr(self, 'invoices_page'):
            self.invoices_page.set_company(company_id)
        if hasattr(self, 'quotations_page'):
            self.quotations_page.set_company(company_id)
        if hasattr(self, 'ledger_page'):
            self.ledger_page.set_company(company_id)
            
        if hasattr(self, 'day_book_page'):
            self.day_book_page.set_company(company_id)
            
        if hasattr(self, 'vendors_page'):
            self.vendors_page.current_company = {"id": company_id}
            self.vendors_page.refresh_data()
            
        if hasattr(self, 'vendor_bills_page'):
            self.vendor_bills_page.set_company(company_id)

        if hasattr(self, 'employees_page'):
            self.employees_page.current_company = {"id": company_id}
            self.employees_page.refresh_data()

        if hasattr(self, 'backup_page'):
            # Find full company dict so BackupPage can show name
            company_dict = {"id": company_id}
            if self.header.companies:
                for c in self.header.companies:
                    if c["id"] == company_id:
                        company_dict = c
                        break
            self.backup_page.set_company(company_dict)
