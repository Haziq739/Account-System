from PySide6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from ui.components.employee_dialogs import EmployeeFormDialog
from services.employee_service import EmployeeService

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    bg = COLORS['primary'] if primary else COLORS['bg_input']
    color = "white" if primary else COLORS['text_primary']
    border = "none" if primary else f"1px solid {COLORS['border']}"
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {color};
            border: {border};
            border-radius: 6px;
            padding: 4px;
            font-weight: bold;
            font-size: 13px;
        }}
        QPushButton:hover {{ opacity: 0.9; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

from PySide6.QtWidgets import QDialog

class RowActionDialog(QDialog):
    def __init__(self, parent=None, title_text="Action"):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            QDialog {{ 
                background-color: {COLORS['bg_card']}; 
                border-radius: 8px; 
                border: 2px solid {COLORS['primary']}; 
            }}
            QPushButton, QPushButton#outline_btn, QPushButton#primary_btn {{
                text-align: center;
                padding: 12px 16px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QPushButton:hover, QPushButton#outline_btn:hover, QPushButton#primary_btn:hover {{
                background-color: #EFF6FF;
                border: 1px solid {COLORS['primary']};
                color: {COLORS['primary']};
            }}
        """)
        self.setWindowFlags(Qt.WindowType.Dialog)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        from PySide6.QtWidgets import QPushButton
        self.btn_history = QPushButton("Employee Advance History")
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del = QPushButton("Delete")
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_del.setStyleSheet("""
            QPushButton, QPushButton#outline_btn {
                background-color: #FEF2F2; 
                color: #DC2626; 
                border: 1px solid #FECACA; 
                text-align: center;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover, QPushButton#outline_btn:hover {
                background-color: #FEE2E2;
                border: 1px solid #EF4444;
                color: #B91C1C;
            }
        """)
        
        self.btn_history.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)

class EmployeesPage(QWidget):
    """Page for managing employee salaries."""
    def __init__(self, current_company: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_company = current_company
        self.current_user = current_user
        self.employees = []
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
        
        title = QLabel("Employee Salaries")
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
        root.addLayout(top_bar)
        
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        
        dl_btn = _btn("Download Salary PDF", icon="📄")
        dl_btn.setFixedSize(210, 38)
        dl_btn.setStyleSheet(dl_btn.styleSheet() + f"""
            QPushButton:pressed, QPushButton:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        dl_btn.clicked.connect(self._on_download_pdf)
        action_bar.addWidget(dl_btn)
        
        reset_btn = _btn("Reset Monthly Advances", icon="🔄")
        reset_btn.setFixedSize(210, 38)
        reset_btn.setStyleSheet(reset_btn.styleSheet() + f"""
            QPushButton:pressed, QPushButton:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        reset_btn.clicked.connect(self._on_reset_advances)
        action_bar.addWidget(reset_btn)
        
        add_btn = _btn("Add Employee", primary=True, icon="➕")
        add_btn.setFixedSize(210, 38)
        add_btn.clicked.connect(self._on_add)
        action_bar.addWidget(add_btn)
        
        root.addLayout(action_bar)
        
        # ── Table ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Sr. No", "Employee Name", "Monthly Salary", "Current Advance", "Net Salary Payable", "Date Added"])
        
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
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        
        
        root.addWidget(self.table)


    def _on_download_pdf(self):
        if not self.current_company:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime
        import shutil
        
        default_name = f"Employee_Salaries_{datetime.now().strftime('%b_%Y')}.pdf"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Employee Salaries PDF", default_name, "PDF Files (*.pdf)")
        if not save_path:
            return
        
        try:
            from services.pdf_generator import PDFGenerator
            filepath = PDFGenerator.generate_employee_salary_pdf(self.current_company["id"])
            if filepath and save_path:
                shutil.copy2(filepath, save_path)
            show_message(self, "success", "PDF Downloaded", f"Salary Report successfully downloaded to:\n{save_path}")
        except Exception as e:
            show_message(self, "error", "Error", f"Failed to generate PDF: {e}")
            
    def _on_reset_advances(self):
        if not self.current_company:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        from ui.components.employee_dialogs import ResetAdvancesDialog
        dlg = ResetAdvancesDialog(self)
        if dlg.exec():
            month_str = dlg.get_selected_month()
            msg = QMessageBox(self)
            msg.setWindowTitle("Confirm Reset")
            msg.setText(f"Are you sure you want to reset the current month's ({month_str}) employee advances?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            reply = msg.exec()
            
            if reply == QMessageBox.StandardButton.Yes:
                success = EmployeeService.clear_employee_advances(self.current_company["id"], month_str, self.current_user.get("id"))
                if success:
                    show_message(self, "success", "Reset Complete", f"Advances for {month_str} have been cleared.")
                    self.refresh_data()
                else:
                    show_message(self, "error", "Error", "Failed to reset advances.")

    def _on_search_changed(self):
        self.search_timer.start(300) # 300ms debounce

    def refresh_data(self):
        term = self.search_input.text().strip()
        if self.current_company and "id" in self.current_company:
            self.employees = EmployeeService.get_employees(self.current_company["id"], term)
        else:
            self.employees = []
        
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for i, e in enumerate(self.employees):
            self.table.insertRow(i)
            self._populate_row(i, e)
            
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)
        
    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))

    
    def _on_row_clicked(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item: return
        emp_id = id_item.data(Qt.ItemDataRole.UserRole)
        emp_name = self.table.item(row, 1).text()
        
        dlg = RowActionDialog(self, f"Employee: {emp_name}")
        res = dlg.exec()
        
        if res == 1:
            from ui.components.employee_dialogs import EmployeeAdvanceHistoryDialog
            hist_dlg = EmployeeAdvanceHistoryDialog(self, employee_name=emp_name, employee_id=emp_id)
            hist_dlg.exec()
        elif res == 2:
            self._on_edit(emp_id)
        elif res == 8:
            self._on_delete(emp_id)

    def _populate_row(self, row_idx: int, e: dict):
        # S.No (Display Row Index + 1)
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # Store Database ID in UserRole to maintain logic
        id_item.setData(Qt.ItemDataRole.UserRole, e["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        # Name
        self.table.setItem(row_idx, 1, QTableWidgetItem(e["name"]))
        
        # Monthly Salary
        self.table.setItem(row_idx, 2, QTableWidgetItem(f"{e.get('salary', 0):,.2f}"))
        
        # Current Advance
        self.table.setItem(row_idx, 3, QTableWidgetItem(f"{e.get('current_advance', 0):,.2f}"))
        
        # Net Salary Payable
        self.table.setItem(row_idx, 4, QTableWidgetItem(f"{e.get('net_salary', 0):,.2f}"))
        
        # Date Added
        dt_str = e["created_at"].strftime("%Y-%m-%d") if e["created_at"] else ""
        self.table.setItem(row_idx, 5, QTableWidgetItem(dt_str))
        
        # Actions


    def _find_row_by_id(self, employee_id: int) -> int:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == employee_id:
                return row
        return -1

    def _on_add(self):
        if not self.current_company or "id" not in self.current_company:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        dlg = EmployeeFormDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                show_message(self, "error", "Validation Error", "Employee Name is required.")
                return
            if data["salary"] <= 0:
                show_message(self, "error", "Validation Error", "Salary must be greater than zero.")
                return
            
            try:
                new_e = EmployeeService.create_employee(
                    company_id=self.current_company["id"], 
                    name=data["name"], 
                    salary=data["salary"], 
                    phone=data["phone"], 
                    address=data["address"], 
                    user_id=self.current_user["id"]
                )
                show_message(self, "success", "Success", "Employee created successfully.")
                self.refresh_data()
                return True
                
            except ValueError as e:
                from ui.auth.setup_window import handle_duplicate_error
                if not handle_duplicate_error(self, e):
                    show_message(self, "error", "Error", str(e))
            except Exception as e:
                show_message(self, "error", "Error", str(e))

    def _on_edit(self, employee_id: int):
        emp = next((e for e in self.employees if e["id"] == employee_id), None)
        if not emp:
            return
            
        dlg = EmployeeFormDialog(self, employee_data=emp)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                show_message(self, "error", "Validation Error", "Employee Name is required.")
                return
            if data["salary"] <= 0:
                show_message(self, "error", "Validation Error", "Salary must be greater than zero.")
                return
            
            try:
                success = EmployeeService.update_employee(
                    company_id=self.current_company["id"], 
                    employee_id=employee_id, 
                    name=data["name"], 
                    salary=data["salary"], 
                    phone=data["phone"], 
                    address=data["address"], 
                    user_id=self.current_user["id"]
                )
                if success:
                    show_message(self, "success", "Success", "Employee updated successfully.")
                    self.refresh_data()
                else:
                    show_message(self, "error", "Error", "Failed to update employee.")
            except ValueError as e:
                from ui.auth.setup_window import handle_duplicate_error
                if not handle_duplicate_error(self, e):
                    show_message(self, "error", "Error", str(e))
            except Exception as e:
                show_message(self, "error", "Error", str(e))

    def _on_delete(self, employee_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this employee? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = EmployeeService.soft_delete_employee(self.current_company["id"], employee_id, self.current_user["id"])
            if success:
                show_message(self, "success", "Deleted", "Employee deleted successfully.")
                # Instantly remove local row
                row_idx = self._find_row_by_id(employee_id)
                if row_idx != -1:
                    self.table.removeRow(row_idx)
                    self.employees = [e for e in self.employees if e["id"] != employee_id]
                    self._update_serial_numbers()
            else:
                show_message(self, "error", "Error", "Failed to delete employee.")
