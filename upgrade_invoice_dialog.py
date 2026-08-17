import os
import re

def upgrade_invoice_dialog(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Imports
    content = content.replace(
        "QHeaderView, QAbstractItemView, QWidget, QGridLayout",
        "QHeaderView, QAbstractItemView, QWidget, QGridLayout, QCompleter, QTextEdit"
    )

    # 2. DynamicAddDialog injection
    dialog_code = """
class DynamicAddDialog(QDialog):
    def __init__(self, parent, title, prompt, input_label):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(350)
        self.setStyleSheet(f\"\"\"
            QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 2px solid {COLORS['primary']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: bold; font-size: 14px; }}
            QLineEdit {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 8px; color: {COLORS['text_primary']}; }}
            QLineEdit:focus {{ border: 1px solid {COLORS['primary']}; }}
            QPushButton {{ padding: 12px; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton#outline_btn {{ background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; color: {COLORS['text_primary']}; }}
            QPushButton#outline_btn:hover {{ background-color: #EFF6FF; border: 1px solid {COLORS['primary']}; color: {COLORS['primary']}; }}
            QPushButton#primary_btn {{ background-color: {COLORS['primary']}; color: white; border: none; }}
            QPushButton#primary_btn:hover {{ opacity: 0.9; }}
        \"\"\")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel(prompt))
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(input_label)
        layout.addWidget(self.input_field)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("outline_btn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("primary_btn")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
        
    def get_input(self):
        return self.input_field.text().strip()

class CreateInvoiceDialog(QDialog):
"""
    content = content.replace("class CreateInvoiceDialog(QDialog):", dialog_code)

    # 3. Add Customer Combobox updates
    customer_cb_code = """        self.customer_cb = QComboBox()
        self.customer_cb.setEditable(True)
        self.customer_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_cb.addItem("-- Select Customer --", None)
        for c in self.customers:
            display_name = f"{c['name']} ({c['phone']})" if c.get('phone') else c['name']
            self.customer_cb.addItem(display_name, c['id'])
        
        completer = QCompleter(self.customer_cb.model(), self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.customer_cb.setCompleter(completer)
        self.customer_cb.lineEdit().returnPressed.connect(self._on_customer_entered)
        
        cust_layout.addWidget(self.customer_cb)"""
    
    content = re.sub(
        r'        self.customer_cb = QComboBox\(\)[\s\S]*?cust_layout\.addWidget\(self\.customer_cb\)',
        customer_cb_code,
        content
    )

    # 4. Service combo box replacement
    service_cb_code = """        self.service_cb = QComboBox()
        self.service_cb.setEditable(True)
        self.service_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.service_cb.setPlaceholderText("Search or enter new service...")
        self.service_cb.addItem("-- Select Service to Add --", None)
        self._populate_service_cb()
        
        srv_completer = QCompleter(self.service_cb.model(), self)
        srv_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        srv_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        srv_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.service_cb.setCompleter(srv_completer)
        self.service_cb.lineEdit().returnPressed.connect(self._on_service_entered)
        
        root.addWidget(self.service_cb, alignment=Qt.AlignmentFlag.AlignLeft)"""
    
    content = re.sub(
        r'        # Add Item Button[\s\S]*?root\.addWidget\(add_item_btn, alignment=Qt\.AlignmentFlag\.AlignLeft\)',
        service_cb_code,
        content
    )

    # 5. QTextEdit for Notes
    notes_code = """        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(80)
        self.notes_input.setStyleSheet(f\"\"\"
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {COLORS['text_primary']};
            }}
            QTextEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        \"\"\")"""
    content = content.replace("self.notes_input = QLineEdit()", notes_code)
    
    # Text fetch adjustment for _save
    content = content.replace('notes=self.notes_input.text().strip(),', 'notes=self.notes_input.toPlainText().strip(),')

    # 6. Handlers
    handlers_code = """
    def _populate_service_cb(self):
        self.service_cb.clear()
        self.service_cb.addItem("-- Select Service to Add --", None)
        for s in self.all_services:
            self.service_cb.addItem(s["name"], s["id"])

    def _on_customer_entered(self):
        text = self.customer_cb.lineEdit().text().strip()
        if not text or text == "-- Select Customer --": return
        
        idx = self.customer_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.customer_cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, "Add Customer", f"Customer '{text}' not found.\\nDo you want to add this customer?", "Phone Number (Optional)")
        if dlg.exec():
            phone = dlg.get_input()
            try:
                new_cust = CustomerService.create_customer(self.company_id, text, phone, "", self.current_user["id"], self.context)
                self.customers = CustomerService.get_customers(self.company_id, customer_type=self.context)
                
                self.customer_cb.clear()
                self.customer_cb.addItem("-- Select Customer --", None)
                for c in self.customers:
                    display_name = f"{c['name']} ({c['phone']})" if c.get('phone') else c['name']
                    self.customer_cb.addItem(display_name, c['id'])
                    
                idx = self.customer_cb.findData(new_cust["id"])
                if idx >= 0: self.customer_cb.setCurrentIndex(idx)
                
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.customer_cb.lineEdit().clear()

    def _on_service_entered(self):
        text = self.service_cb.lineEdit().text().strip()
        if not text or text == "-- Select Service to Add --": return
        
        idx = self.service_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.service_cb.setCurrentIndex(idx)
            srv_id = self.service_cb.itemData(idx)
            if srv_id:
                # Add row with this service
                srv = next((s for s in self.all_services if s["id"] == srv_id), None)
                if srv:
                    self._add_item_row({"service_id": srv_id})
                    self.service_cb.lineEdit().clear()
            return
            
        dlg = DynamicAddDialog(self, "Add Service", f"Service '{text}' not found.\\nDo you want to add this service?", "Default Price (Required)")
        if dlg.exec():
            price_text = dlg.get_input()
            try:
                price = float(price_text)
                new_srv = ServiceCatalogue.create_service(self.company_id, "General", text, "", price, self.current_user["id"])
                self.all_services = ServiceCatalogue.get_services(self.company_id)
                self.filtered_services = self.all_services
                
                self._populate_service_cb()
                self._add_item_row({"service_id": new_srv["id"]})
                self.service_cb.lineEdit().clear()
                
            except ValueError:
                show_message(self, "error", "Error", "Invalid price amount.")
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.service_cb.lineEdit().clear()

    def _add_item_row"""
    content = content.replace("    def _add_item_row", handlers_code)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    upgrade_invoice_dialog(r"d:\Account_System\ui\components\create_invoice_dialog.py")
