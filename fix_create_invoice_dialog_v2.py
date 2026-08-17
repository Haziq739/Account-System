import os
import re

def fix_create_invoice_dialog(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update DynamicAddDialog to support two fields and validation
    dialog_code = """
class DynamicAddDialog(QDialog):
    def __init__(self, parent, title, prompt, input_label, second_label=None):
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
        
        self.second_field = None
        if second_label:
            self.second_field = QLineEdit()
            self.second_field.setPlaceholderText(second_label)
            layout.addWidget(self.second_field)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("outline_btn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("primary_btn")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.input_field.text().strip():
            show_message(self, "error", "Validation Error", "The first field is required.")
            return
        if self.second_field and not self.second_field.text().strip():
            show_message(self, "error", "Validation Error", "The second field is required.")
            return
        self.accept()
        
    def get_inputs(self):
        val1 = self.input_field.text().strip()
        val2 = self.second_field.text().strip() if self.second_field else None
        return val1, val2
"""
    # Replace the old DynamicAddDialog
    content = re.sub(r'class DynamicAddDialog\(QDialog\):[\s\S]*?def get_input\(self\):\n        return self\.input_field\.text\(\)\.strip\(\)\n', dialog_code, content)

    # 2. Update Customer Combobox completer styling and remove "-- Select Customer --"
    customer_cb_code = """        self.customer_cb = QComboBox()
        self.customer_cb.setEditable(True)
        self.customer_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_cb.lineEdit().setPlaceholderText("Search or enter new customer...")
        for c in self.customers:
            display_name = f"{c['name']} ({c['phone']})" if c.get('phone') else c['name']
            self.customer_cb.addItem(display_name, c['id'])
        
        completer = QCompleter(self.customer_cb.model(), self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        popup = completer.popup()
        popup.setStyleSheet(f\"\"\"
            QListView {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 4px; }}
            QListView::item {{ padding: 8px; }}
            QListView::item:selected {{ background-color: #EFF6FF; color: {COLORS['primary']}; }}
        \"\"\")
        
        self.customer_cb.setCompleter(completer)
        self.customer_cb.lineEdit().returnPressed.connect(self._on_customer_entered)
        
        cust_layout.addWidget(self.customer_cb)"""
    content = re.sub(
        r'        self.customer_cb = QComboBox\(\)[\s\S]*?cust_layout\.addWidget\(self\.customer_cb\)',
        customer_cb_code,
        content
    )

    # 3. Update Service Combobox completer styling, add label, and remove "-- Select Service --"
    service_cb_code = """        srv_search_layout = QVBoxLayout()
        srv_search_layout.addWidget(QLabel("Service Search *", styleSheet=f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 13px;"))
        self.service_cb = QComboBox()
        self.service_cb.setEditable(True)
        self.service_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.service_cb.lineEdit().setPlaceholderText("Search or enter new service...")
        self._populate_service_cb()
        
        srv_completer = QCompleter(self.service_cb.model(), self)
        srv_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        srv_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        srv_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        srv_popup = srv_completer.popup()
        srv_popup.setStyleSheet(f\"\"\"
            QListView {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 4px; }}
            QListView::item {{ padding: 8px; }}
            QListView::item:selected {{ background-color: #EFF6FF; color: {COLORS['primary']}; }}
        \"\"\")
        
        self.service_cb.setCompleter(srv_completer)
        self.service_cb.lineEdit().returnPressed.connect(self._on_service_entered)
        
        srv_search_layout.addWidget(self.service_cb)
        root.addLayout(srv_search_layout)"""
    content = re.sub(
        r'        self.service_cb = QComboBox\(\)[\s\S]*?root\.addWidget\(self\.service_cb, alignment=Qt\.AlignmentFlag\.AlignLeft\)',
        service_cb_code,
        content
    )

    # 4. Update handlers to use new DynamicAddDialog and avoid KeyError
    handlers_code = """    def _populate_service_cb(self):
        self.service_cb.clear()
        for s in self.all_services:
            self.service_cb.addItem(s["name"], s["id"])

    def _on_customer_entered(self):
        text = self.customer_cb.lineEdit().text().strip()
        if not text: return
        
        idx = self.customer_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.customer_cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, "Add Customer", f"Customer '{text}' not found.\\nDo you want to add this customer?", "Phone Number (Required)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                new_cust = CustomerService.create_customer(self.company_id, text, phone, "", self.current_user["id"], self.context)
                self.customers = CustomerService.get_customers(self.company_id, customer_type=self.context)
                
                self.customer_cb.clear()
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
        if not text: return
        
        idx = self.service_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.service_cb.setCurrentIndex(idx)
            srv_id = self.service_cb.itemData(idx)
            if srv_id:
                # Add row with this service
                srv = next((s for s in self.all_services if s["id"] == srv_id), None)
                if srv:
                    self._add_item_row()
                    row = self.table.rowCount() - 1
                    row_srv_cb = self.table.cellWidget(row, 1)
                    idx = row_srv_cb.findData(srv_id)
                    if idx >= 0: row_srv_cb.setCurrentIndex(idx)
                    self.service_cb.lineEdit().clear()
            return
            
        dlg = DynamicAddDialog(self, "Add Service", f"Service '{text}' not found.\\nDo you want to add this service?", "Default Price (Required)", "Description (Required)")
        if dlg.exec():
            price_text, desc_text = dlg.get_inputs()
            try:
                price = float(price_text)
                new_srv = ServiceCatalogue.create_service(self.company_id, "General", text, desc_text, price, self.current_user["id"])
                self.all_services = ServiceCatalogue.get_services(self.company_id)
                self.filtered_services = self.all_services
                
                self._populate_service_cb()
                self._add_item_row()
                row = self.table.rowCount() - 1
                row_srv_cb = self.table.cellWidget(row, 1)
                idx = row_srv_cb.findData(new_srv["id"])
                if idx >= 0: row_srv_cb.setCurrentIndex(idx)
                
                self.service_cb.lineEdit().clear()
                
            except ValueError:
                show_message(self, "error", "Error", "Invalid price amount.")
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.service_cb.lineEdit().clear()"""
    
    content = re.sub(r'    def _populate_service_cb[\s\S]*?(?=    def _add_item_row)', handlers_code + '\n\n', content)

    # 5. Fix _add_item_row to handle missing `existing_item` correctly without throwing KeyError
    content = content.replace('desc_input.setText(existing_item["description"] or "")', 'desc_input.setText(existing_item.get("description", ""))')
    content = content.replace('qty_input.setText(str(existing_item["quantity"]))', 'qty_input.setText(str(existing_item.get("quantity", 1)))')
    content = content.replace('price_input.setText(str(existing_item["unit_price"]))', 'price_input.setText(str(existing_item.get("unit_price", 0)))')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_create_invoice_dialog(r"d:\Account_System\ui\components\create_invoice_dialog.py")
