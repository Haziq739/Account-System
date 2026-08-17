import os
import re

def fix_employees_page(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import QDialog
    content = content.replace("QHeaderView, QFileDialog, QMessageBox, QAbstractItemView", "QHeaderView, QFileDialog, QMessageBox, QAbstractItemView, QDialog")
    
    # Dialog definition - we inject it after _btn definition or right after imports if _btn is there.
    # Actually, we can inject it right before the EmployeeWorker or EmployeesPage class.
    
    dialog_code = """
class RowActionDialog(QDialog):
    def __init__(self, parent=None, title_text="Action"):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedWidth(320)
        self.setStyleSheet(f\"\"\"
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
        \"\"\")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        self.btn_history = _btn("Employee Advance History")
        self.btn_edit = _btn("Edit")
        self.btn_del = _btn("Delete")
        self.btn_cancel = _btn("Cancel")
        
        self.btn_del.setStyleSheet(\"\"\"
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
        \"\"\")
        
        self.btn_history.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)

"""

    content = content.replace("class EmployeeWorker(QThread):", dialog_code + "class EmployeeWorker(QThread):")
    
    # Table columns changes
    content = content.replace("self.table.setColumnCount(7)", "self.table.setColumnCount(6)")
    content = content.replace('self.table.setHorizontalHeaderLabels(["Sr. No", "Employee Name", "Monthly Salary", "Current Advance", "Net Salary Payable", "Date Added", "Actions"])', 'self.table.setHorizontalHeaderLabels(["Sr. No", "Employee Name", "Monthly Salary", "Current Advance", "Net Salary Payable", "Date Added"])')
    content = content.replace("header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)", "")
    content = content.replace("self.table.setColumnWidth(6, 100)", "")

    # Connect cellClicked
    if "self.table.cellClicked" not in content:
        content = content.replace("self.table.customContextMenuRequested.connect(self._on_context_menu)", "self.table.cellClicked.connect(self._on_row_clicked)")
    
    content = content.replace("self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)", "")
    
    # Remove _create_action_widget definition
    content = re.sub(r'    def _create_action_widget[\s\S]*?return action_widget\n\n', '', content)
    
    # Remove _on_context_menu definition
    content = re.sub(r'    def _on_context_menu\(self, pos\):[\s\S]*?dlg\.exec\(\)\n', '', content)

    # Clean up populate_row
    content = re.sub(r'        action_widget = self\._create_action_widget\(e\["id"\]\)\n        self\.table\.setCellWidget\(row_idx, 6, action_widget\)', '', content)

    # Add _on_row_clicked
    row_clicked_code = """
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
"""
    if "def _on_row_clicked(self," not in content:
        content = content.replace("def _populate_row(self, row_idx: int, e: dict):", row_clicked_code + "\n    def _populate_row(self, row_idx: int, e: dict):")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_employees_page(r"d:\Account_System\ui\pages\employees_page.py")
