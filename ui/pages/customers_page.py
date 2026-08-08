from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QDialog, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from ui.components.customer_dialogs import CustomerFormDialog, CSVImportSummaryDialog
from services.customer import CustomerService

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
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; }}")
        
        layout = QVBoxLayout(self)
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 600;")
        layout.addWidget(lbl)

class CSVImportWorker(QThread):
    """Background worker thread to run CSV import without freezing the UI."""
    finished_import = Signal(int, int, int)
    error_import = Signal(str)

    def __init__(self, file_path: str, user_id: int, context: str = "regular"):
        super().__init__()
        self.file_path = file_path
        self.user_id = user_id
        self.context = context

    def run(self):
        try:
            imported, skipped, failed = CustomerService.import_customers_from_csv(self.file_path, self.user_id, customer_type=self.context)
            self.finished_import.emit(imported, skipped, failed)
        except Exception as e:
            self.error_import.emit(str(e))

class CustomersPage(QWidget):
    """Page for managing customers."""
    def __init__(self, current_user: dict, context: str = "regular", parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.context = context
        self.customers = []
        self._build()
        self.refresh_data()
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_data)

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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["S.No", "Name", "Phone", "Address", "Date Added", "Actions"])
        
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
                background-color: #E2E8F0;
                color: {COLORS['text_primary']};
            }}
        """)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 140)
        
        root.addWidget(self.table)

    def _on_search_changed(self):
        self.search_timer.start(300) # 300ms debounce

    def refresh_data(self):
        term = self.search_input.text().strip()
        self.customers = CustomerService.get_customers(term, customer_type=self.context)
        
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        
        for i, c in enumerate(self.customers):
            self.table.insertRow(i)
            self._populate_row(i, c)
            
        self.table.setUpdatesEnabled(True)
        
    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))

    def _create_action_widget(self, cid: int) -> QWidget:
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 2, 4, 2)
        action_layout.setSpacing(8)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        edit_btn.setToolTip("Edit Customer")
        edit_btn.clicked.connect(lambda checked, c_id=cid: self._on_edit(c_id))
        
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        del_btn.setToolTip("Delete Customer")
        del_btn.clicked.connect(lambda checked, c_id=cid: self._on_delete(c_id))
        
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(del_btn)
        return action_widget

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
        
        # Actions
        action_widget = self._create_action_widget(c["id"])
        self.table.setCellWidget(row_idx, 5, action_widget)

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
            if not data["name"] or not data["phone"]:
                show_message(self, "error", "Validation Error", "Customer Name and Phone Number are required.")
                return
            
            try:
                new_c = CustomerService.create_customer(data["name"], data["phone"], data["address"], self.current_user["id"], customer_type=self.context)
                show_message(self, "success", "Success", "Customer created successfully.")
                
                # Instantly append to the bottom of the table
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                # Ensure the created_at key exists for populate_row
                from datetime import datetime
                new_c["created_at"] = datetime.now() 
                self.customers.append(new_c)
                self._populate_row(row_idx, new_c)
                
            except ValueError as e:
                show_message(self, "error", "Error", str(e))

    def _on_edit(self, customer_id: int):
        cust = next((c for c in self.customers if c["id"] == customer_id), None)
        if not cust:
            return
            
        dlg = CustomerFormDialog(self, customer_data=cust)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"] or not data["phone"]:
                show_message(self, "error", "Validation Error", "Customer Name and Phone Number are required.")
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

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Customers CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return
            
        # Launch background worker
        self.loading_dlg = LoadingDialog(self, "Importing Customers...")
        self.worker = CSVImportWorker(file_path, self.current_user["id"], context=self.context)
        
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
