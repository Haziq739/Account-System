import os

def fix_file(filepath, is_invoice=True):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Import QDialog
    content = content.replace("QHeaderView, QMessageBox, QAbstractItemView, QMenu", "QHeaderView, QMessageBox, QAbstractItemView, QDialog")
    
    # Dialog definitions
    invoice_dialog = """
class RowActionDialog(QDialog):
    def __init__(self, parent=None, title_text="Action"):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedSize(320, 420)
        self.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        self.btn_view = _btn("View Invoice")
        self.btn_edit = _btn("Edit Invoice")
        self.btn_pdf = _btn("Generate / View PDF")
        self.btn_down = _btn("Download Invoice")
        self.btn_print = _btn("Print Invoice")
        self.btn_pay = _btn("Record Payment", primary=True)
        self.btn_history = _btn("Payment History / Previous Transactions")
        self.btn_del = _btn("Delete Invoice")
        self.btn_del.setStyleSheet("background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; padding: 8px; border-radius: 4px; font-weight: 500;")
        self.btn_cancel = _btn("Cancel")
        
        self.btn_view.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_pdf.clicked.connect(lambda: self.done(1)) # Same as view
        self.btn_down.clicked.connect(lambda: self.done(4))
        self.btn_print.clicked.connect(lambda: self.done(5))
        self.btn_pay.clicked.connect(lambda: self.done(6))
        self.btn_history.clicked.connect(lambda: self.done(7))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_view)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_pdf)
        layout.addWidget(self.btn_down)
        layout.addWidget(self.btn_print)
        layout.addWidget(self.btn_pay)
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)
"""

    quotation_dialog = """
class RowActionDialog(QDialog):
    def __init__(self, parent=None, title_text="Action"):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedSize(320, 420)
        self.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        self.btn_view = _btn("View Quotation")
        self.btn_edit = _btn("Edit Quotation")
        self.btn_pdf = _btn("Generate / View PDF")
        self.btn_down = _btn("Download Quotation")
        self.btn_print = _btn("Print Quotation")
        self.btn_convert = _btn("Convert to Invoice", primary=True)
        self.btn_del = _btn("Delete Quotation")
        self.btn_del.setStyleSheet("background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; padding: 8px; border-radius: 4px; font-weight: 500;")
        self.btn_cancel = _btn("Cancel")
        
        self.btn_view.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_pdf.clicked.connect(lambda: self.done(1)) # Same as view
        self.btn_down.clicked.connect(lambda: self.done(4))
        self.btn_print.clicked.connect(lambda: self.done(5))
        self.btn_convert.clicked.connect(lambda: self.done(6))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_view)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_pdf)
        layout.addWidget(self.btn_down)
        layout.addWidget(self.btn_print)
        layout.addWidget(self.btn_convert)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)
"""

    dialog_code = invoice_dialog if is_invoice else quotation_dialog
    content = content.replace("class PDFWorker(QThread):", dialog_code + "\nclass PDFWorker(QThread):")
    
    # Table changes
    if is_invoice:
        content = content.replace("self.table.setColumnCount(9)", "self.table.setColumnCount(8)")
        content = content.replace('self.table.setHorizontalHeaderLabels(["S.No", "Invoice #", "Customer", "Date", "Total", "Paid", "Remaining", "Status", "Actions"])', 'self.table.setHorizontalHeaderLabels(["S.No", "Invoice #", "Customer", "Date", "Total", "Paid", "Remaining", "Status"])')
        content = content.replace("header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)", "")
        content = content.replace("self.table.setColumnWidth(8, 150)", "")
    else:
        content = content.replace("self.table.setColumnCount(7)", "self.table.setColumnCount(6)")
        content = content.replace('self.table.setHorizontalHeaderLabels(["S.No", "Quotation #", "Customer", "Date", "Total", "Status", "Actions"])', 'self.table.setHorizontalHeaderLabels(["S.No", "Quotation #", "Customer", "Date", "Total", "Status"])')
        content = content.replace("header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)", "")
        content = content.replace("self.table.setColumnWidth(6, 150)", "")

    content = content.replace("self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)", "")
    content = content.replace("self.table.customContextMenuRequested.connect(self._show_context_menu)", "")
    content = content.replace("self.table.itemDoubleClicked.connect(self._on_row_double_clicked)", "self.table.cellClicked.connect(self._on_row_clicked)")
    
    # Replace populate row
    if is_invoice:
        content = content.replace("""        action_widget = self._create_action_widget(inv["id"])
        self.table.setCellWidget(row_idx, 8, action_widget)""", "")
    else:
        content = content.replace("""        action_widget = self._create_action_widget(inv["id"])
        self.table.setCellWidget(row_idx, 6, action_widget)""", "")

    # Add row click handler
    invoice_handler = """
    def _on_row_clicked(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item: return
        inv_id = id_item.data(Qt.ItemDataRole.UserRole)
        inv_num = self.table.item(row, 1).text()
        
        dlg = RowActionDialog(self, f"Invoice: {inv_num}")
        res = dlg.exec()
        
        if res == 1:
            self._on_view_pdf(inv_id)
        elif res == 2:
            self._on_edit(inv_id, row)
        elif res == 4:
            self._on_download(inv_id)
        elif res == 5:
            self._on_print(inv_id)
        elif res == 6:
            self._on_record_payment(inv_id, row)
        elif res == 7:
            self._on_payment_history(inv_id)
        elif res == 8:
            self._on_delete(inv_id)
"""

    quotation_handler = """
    def _on_row_clicked(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item: return
        inv_id = id_item.data(Qt.ItemDataRole.UserRole)
        inv_num = self.table.item(row, 1).text()
        
        dlg = RowActionDialog(self, f"Quotation: {inv_num}")
        res = dlg.exec()
        
        if res == 1:
            self._on_view_pdf(inv_id)
        elif res == 2:
            self._on_edit(inv_id, row)
        elif res == 4:
            self._on_download(inv_id)
        elif res == 5:
            self._on_print(inv_id)
        elif res == 6:
            self._on_convert(inv_id)
        elif res == 8:
            self._on_delete(inv_id)
"""

    handler_code = invoice_handler if is_invoice else quotation_handler
    
    # We'll just replace the old _on_row_double_clicked with the new handler
    if "def _on_row_double_clicked" in content:
        import re
        content = re.sub(r'    def _on_row_double_clicked\(self, item\):[\s\S]*?(?=    def _create_action_widget)', handler_code, content)
        content = re.sub(r'    def _create_action_widget.*?return action_widget', '', content, flags=re.DOTALL)
        content = re.sub(r'    def _show_context_menu\(self, pos\):[\s\S]*?menu\.exec\(self\.table\.viewport\(\)\.mapToGlobal\(pos\)\)', '', content, flags=re.DOTALL)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_file(r"d:\Account_System\ui\pages\invoices_page.py", True)
    fix_file(r"d:\Account_System\ui\pages\quotations_page.py", False)
