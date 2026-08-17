import os
import re

def fix_vendor_bills(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import QDialog
    content = content.replace("QHeaderView, QMessageBox, QAbstractItemView, QMenu", "QHeaderView, QMessageBox, QAbstractItemView, QDialog")
    
    # Dialog definition
    dialog_code = """
class RowActionDialog(QDialog):
    def __init__(self, parent=None, title_text="Action"):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedWidth(320)
        self.setStyleSheet(f\"\"\"
            QDialog { 
                background-color: {COLORS['bg_card']}; 
                border-radius: 8px; 
                border: 2px solid {COLORS['primary']}; 
            }
            QPushButton, QPushButton#outline_btn, QPushButton#primary_btn {
                text-align: center;
                padding: 12px 16px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover, QPushButton#outline_btn:hover, QPushButton#primary_btn:hover {
                background-color: #EFF6FF;
                border: 1px solid {COLORS['primary']};
                color: {COLORS['primary']};
            }
        \"\"\")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        self.btn_view = _btn("View Bill")
        self.btn_edit = _btn("Edit Bill")
        self.btn_del = _btn("Delete Bill")
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
        
        self.btn_view.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_view)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)
"""

    content = content.replace("class PDFWorker(QThread):", dialog_code + "\nclass PDFWorker(QThread):")
    
    # Table changes
    content = content.replace("self.table.setColumnCount(7)", "self.table.setColumnCount(6)")
    content = content.replace('self.table.setHorizontalHeaderLabels(["S.No", "Bill #", "Vendor", "Date", "Description", "Amount", "Actions"])', 'self.table.setHorizontalHeaderLabels(["S.No", "Bill #", "Vendor", "Date", "Description", "Amount"])')
    content = content.replace("header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)", "")
    content = content.replace("self.table.setColumnWidth(6, 120)", "")

    content = content.replace("self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)", "")
    content = content.replace("self.table.customContextMenuRequested.connect(self._show_context_menu)", "")
    content = content.replace("self.table.itemDoubleClicked.connect(self._on_row_double_clicked)", "self.table.cellClicked.connect(self._on_row_clicked)")
    
    # Replace populate row
    content = content.replace("""        action_widget = self._create_action_widget(bill["id"])
        self.table.setCellWidget(row_idx, 6, action_widget)""", "")

    # Add row click handler
    handler_code = """
    def _on_row_clicked(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item: return
        bill_id = id_item.data(Qt.ItemDataRole.UserRole)
        bill_num = self.table.item(row, 1).text()
        
        dlg = RowActionDialog(self, f"Bill: {bill_num}")
        res = dlg.exec()
        
        if res == 1:
            self._on_view_pdf(bill_id)
        elif res == 2:
            self._on_edit(bill_id)
        elif res == 8:
            self._on_delete(bill_id)
"""
    
    if "def _on_row_double_clicked" in content:
        content = re.sub(r'    def _on_row_double_clicked\(self, item\):[\s\S]*?(?=    def _create_action_widget)', handler_code, content)
        content = re.sub(r'    def _create_action_widget.*?return action_widget', '', content, flags=re.DOTALL)
        content = re.sub(r'    def _show_context_menu\(self, pos\):[\s\S]*?menu\.exec\(self\.table\.viewport\(\)\.mapToGlobal\(pos\)\)', '', content, flags=re.DOTALL)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_vendor_bills(r"d:\Account_System\ui\pages\vendor_bills_page.py")
