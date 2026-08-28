from PySide6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QDialog, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from ui.components.customer_dialogs import CustomerFormDialog, CSVImportSummaryDialog
from services.customer import CustomerService
from services.ledger_service import LedgerService
from services.daybook_service import DayBookService
from ui.pages.ledger_page import StatementPDFWorker
from PySide6.QtCore import QDate

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class LoadingDialog(QDialog):
    """A lightweight, non-blocking loading dialog for background tasks."""
    def __init__(self, parent=None, title="Processing..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 2px solid {COLORS['primary']}; }}")
        
        layout = QVBoxLayout(self)
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 600;")
        layout.addWidget(lbl)

class RowActionDialog(QDialog):
    def __init__(self, parent, title: str, balance: float):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedSize(420, 300)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 2px solid {COLORS['primary']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        bal_text = f"Outstanding Balance: {balance:.2f}"
        if balance < 0:
            bal_text = f"Advance Balance: {abs(balance):.2f}"
        bal_color = "#E53E3E" if balance > 0 else COLORS['primary'] if balance < 0 else COLORS['text_primary']
        
        bal_lbl = QLabel(bal_text)
        bal_lbl.setStyleSheet(f"color: {bal_color}; font-size: 14px; font-weight: 600;")
        bal_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(bal_lbl)
        
        layout.addSpacing(15)
        
        btn_width, btn_height = 180, 40
        
        self.add_bal_btn = _btn("Add Balance", primary=True)
        self.stmt_btn = _btn("Download Statement")
        self.edit_btn = _btn("Edit")
        self.del_btn = QPushButton("Delete")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet(f"background-color: #FEE2E2; color: #EF4444; border: 1px solid #FCA5A5; padding: 8px 16px; border-radius: 6px; font-weight: 600;")
        self.cancel_btn = _btn("Cancel")
        
        for btn in [self.add_bal_btn, self.stmt_btn, self.edit_btn, self.del_btn, self.cancel_btn]:
            btn.setFixedSize(btn_width, btn_height)
            
        row1 = QHBoxLayout()
        row1.addWidget(self.add_bal_btn)
        row1.addWidget(self.stmt_btn)
        
        row2 = QHBoxLayout()
        row2.addWidget(self.edit_btn)
        row2.addWidget(self.del_btn)
        
        row3 = QHBoxLayout()
        row3.addWidget(self.cancel_btn)
        row3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        
        self.cancel_btn.clicked.connect(self.reject)
        self.edit_btn.clicked.connect(lambda: self.done(1))
        self.del_btn.clicked.connect(lambda: self.done(2))
        self.add_bal_btn.clicked.connect(lambda: self.done(3))
        self.stmt_btn.clicked.connect(lambda: self.done(4))

class AddBalanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Outstanding Balance")
        self.setFixedSize(350, 220)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 2px solid {COLORS['primary']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        lbl = QLabel("Add Balance")
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(lbl)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount (e.g. 500)")
        self.amount_input.setStyleSheet(f"padding: 8px; border: 1px solid {COLORS['border']}; border-radius: 4px;")
        layout.addWidget(self.amount_input)
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes (optional)")
        self.notes_input.setStyleSheet(f"padding: 8px; border: 1px solid {COLORS['border']}; border-radius: 4px;")
        layout.addWidget(self.notes_input)
        
        btn_layout = QHBoxLayout()
        save_btn = _btn("Save", primary=True)
        cancel_btn = _btn("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def get_data(self):
        try:
            amount = float(self.amount_input.text() or "0")
        except:
            amount = 0.0
        return {
            "amount": amount,
            "notes": self.notes_input.text()
        }

class CSVImportWorker(QThread):
    """Background worker thread to run CSV import without freezing the UI."""
    finished_import = Signal(int, int, int)
    error_import = Signal(str)

    def __init__(self, file_path: str, user_id: int, company_id: int, context: str = "regular"):
        super().__init__()
        self.file_path = file_path
        self.user_id = user_id
        self.company_id = company_id
        self.context = context

    def run(self):
        try:
            imported, skipped, failed = CustomerService.import_customers_from_csv(self.company_id, self.file_path, self.user_id, customer_type=self.context)
            self.finished_import.emit(imported, skipped, failed)
        except Exception as e:
            self.error_import.emit(str(e))

class CustomersPage(QWidget):
    """Page for managing customers."""
    def __init__(self, current_user: dict, context: str = "regular", parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.context = context
        self.active_company_id = None
        self.customers = []
        self._build()
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_data)
        
    def set_company(self, company_id: int):
        self.active_company_id = company_id
        self.refresh_data()
        
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(20)
        
        # ── Top Bar ──────────────────────────────────────────────
        top_bar = QHBoxLayout()
        
        title = QLabel("Walk-in Customers" if self.context == "day_book" else "Customers")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700; background: transparent;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by name or phone...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 10px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.search_input)
        
        import_btn = _btn("Import CSV", icon="📁")
        import_btn.clicked.connect(self._on_import)
        top_bar.addWidget(import_btn)
        
        add_btn = _btn("Add Walk-in Customer" if self.context == "day_book" else "Add Customer", primary=True, icon="➕")
        add_btn.clicked.connect(self._on_add)
        top_bar.addWidget(add_btn)
        
        root.addLayout(top_bar)
        
        # ── Table ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["S.No", "Name", "Phone", "Address", "Date Added"])
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border_card']};
                font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS['border_card']};
                border-right: 1px solid {COLORS['border_card']};
                font-weight: 600;
                text-align: left;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._on_row_clicked)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        root.addWidget(self.table)

    def _on_search_changed(self):
        self.search_timer.start(300) # 300ms debounce

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        term = self.search_input.text().strip()
        self.customers = CustomerService.get_customers(self.active_company_id, term, customer_type=self.context)
        
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for i, c in enumerate(self.customers):
            self.table.insertRow(i)
            self._populate_row(i, c)
            
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)
        
    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))

    def _on_row_clicked(self, row, col):
        item = self.table.item(row, 0)
        if not item: return
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        customer_name = self.table.item(row, 1).text()
        
        entries = LedgerService.get_customer_ledger(self.active_company_id, customer_id)
        balance = entries[-1]['balance'] if entries else 0.0
        
        dlg = RowActionDialog(self, f"Customer: {customer_name}", balance)
        result = dlg.exec()
        if result == 1:
            self._on_edit(customer_id)
        elif result == 2:
            self._on_delete(customer_id)
        elif result == 3:
            self._on_add_balance(customer_id, customer_name)
        elif result == 4:
            self._on_download_statement(customer_id, customer_name)

    def _populate_row(self, row_idx: int, c: dict):
        # S.No (Display Row Index + 1)
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # Store Database ID in UserRole to maintain logic
        id_item.setData(Qt.ItemDataRole.UserRole, c["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        # Name
        self.table.setItem(row_idx, 1, QTableWidgetItem(c["name"]))
        
        # Phone
        self.table.setItem(row_idx, 2, QTableWidgetItem(c["phone"]))
        
        # Address
        self.table.setItem(row_idx, 3, QTableWidgetItem(c["address"]))
        
        # Date
        dt_str = c["created_at"].strftime("%Y-%m-%d") if c["created_at"] else ""
        self.table.setItem(row_idx, 4, QTableWidgetItem(dt_str))

    def _find_row_by_id(self, customer_id: int) -> int:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == customer_id:
                return row
        return -1

    def _on_add(self):
        dlg = CustomerFormDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                show_message(self, "error", "Validation Error", "Customer Name is required.")
                return
            
            try:
                new_cust = CustomerService.create_customer(
                    company_id=self.active_company_id, 
                    name=data["name"], 
                    phone=data["phone"], 
                    address=data["address"], 
                    user_id=self.current_user["id"],
                    customer_type=self.context
                )
                show_message(self, "success", "Success", "Customer created successfully.")
                
                # Instantly append to the bottom of the table
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                # Ensure the created_at key exists for populate_row
                from datetime import datetime
                new_cust["created_at"] = datetime.now() 
                self.customers.append(new_cust)
                self._populate_row(row_idx, new_cust)
                return True
                
            except Exception as e:
                from ui.auth.setup_window import handle_duplicate_error
                if not handle_duplicate_error(self, e):
                    show_message(self, "error", "Error", str(e))

    def _on_edit(self, customer_id: int):
        cust = next((c for c in self.customers if c["id"] == customer_id), None)
        if not cust:
            return
            
        dlg = CustomerFormDialog(self, customer_data=cust)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                show_message(self, "error", "Validation Error", "Customer Name is required.")
                return
            
            try:
                success = CustomerService.update_customer(customer_id, data["name"], data["phone"], data["address"], self.current_user["id"])
                if success:
                    show_message(self, "success", "Success", "Customer updated successfully.")
                    # Instantly update local row
                    row_idx = self._find_row_by_id(customer_id)
                    if row_idx != -1:
                        cust["name"] = data["name"]
                        cust["phone"] = data["phone"]
                        cust["address"] = data["address"]
                        self._populate_row(row_idx, cust)
                else:
                    show_message(self, "error", "Error", "Failed to update customer.")
            except ValueError as e:
                from ui.auth.setup_window import handle_duplicate_error
                if not handle_duplicate_error(self, e):
                    show_message(self, "error", "Error", str(e))

    def _on_delete(self, customer_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this customer? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = CustomerService.soft_delete_customer(customer_id, self.current_user["id"])
            if success:
                show_message(self, "success", "Deleted", "Customer deleted successfully.")
                # Instantly remove local row
                row_idx = self._find_row_by_id(customer_id)
                if row_idx != -1:
                    self.table.removeRow(row_idx)
                    self.customers = [c for c in self.customers if c["id"] != customer_id]
                    self._update_serial_numbers()
            else:
                show_message(self, "error", "Error", "Failed to delete customer.")


    def _on_add_balance(self, customer_id: int, customer_name: str):
        dlg = AddBalanceDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if data['amount'] <= 0:
                show_message(self, "error", "Invalid Amount", "Please enter an amount greater than 0.")
                return
            
            try:
                from datetime import date
                LedgerService.add_adjustment(
                    company_id=self.active_company_id,
                    customer_id=customer_id,
                    amount=data['amount'],
                    notes=data['notes'],
                    date_val=date.today()
                )
                show_message(self, "success", "Success", "Balance added successfully.")
            except Exception as e:
                show_message(self, "error", "Error", f"Failed to add balance: {e}")

    def _on_download_statement(self, customer_id: int, customer_name: str):
        # We need a loading state, we can use LoadingDialog
        self.loading_dlg = LoadingDialog(self, "Generating Statement...")
        
        # Fetch all entries without date filters to get full history
        entries = LedgerService.get_customer_ledger(self.active_company_id, customer_id)
        
        e_date = QDate.currentDate().toPython()
        if entries:
            s_date = entries[0]["date"]
        else:
            s_date = e_date
            
        cust_name_safe = customer_name.replace(" ", "_")
        default_name = f"Statement_{cust_name_safe}_{s_date.strftime('%Y%m%d')}_to_{e_date.strftime('%Y%m%d')}.pdf"
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Statement", default_name, "PDF Files (*.pdf)")
        if not save_path: return
        
        self.worker = StatementPDFWorker(self.active_company_id, customer_id, s_date, e_date, 'download', save_path, entries)
        self.worker.finished.connect(self._on_pdf_ready)
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()
        self.loading_dlg.exec()
        
    def _on_pdf_ready(self, path: str, action: str, save_path: str):
        self.loading_dlg.accept()
        import shutil
        if save_path:
            try:
                shutil.copy2(path, save_path)
                show_message(self, "success", "Success", "Statement downloaded successfully.")
            except Exception as e:
                show_message(self, "error", "Error", f"Failed to save statement: {e}")

    def _on_pdf_error(self, err: str):
        self.loading_dlg.accept()
        show_message(self, "error", "Error", f"Failed to generate statement: {err}")

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Customers CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return
            
        # Launch background worker
        self.loading_dlg = LoadingDialog(self, "Importing Customers...")
        self.worker = CSVImportWorker(file_path, self.current_user["id"], self.active_company_id, context=self.context)
        
        self.worker.finished_import.connect(self._on_import_success)
        self.worker.error_import.connect(self._on_import_error)
        
        self.worker.start()
        self.loading_dlg.exec()

    def _on_import_success(self, imported, skipped, failed):
        self.loading_dlg.accept()
        dlg = CSVImportSummaryDialog(self, imported, skipped, failed)
        dlg.exec()
        self.refresh_data()

    def _on_import_error(self, err_msg):
        self.loading_dlg.accept()
        show_message(self, "error", "Import Failed", f"An error occurred during import:\n{err_msg}")
