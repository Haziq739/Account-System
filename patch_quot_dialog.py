import re

def patch_quotation_dialog(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Imports
    if "QCompleter" not in content:
        content = content.replace(
            "QHeaderView, QAbstractItemView, QWidget, QGridLayout",
            "QHeaderView, QAbstractItemView, QWidget, QGridLayout, QCompleter, QTextEdit"
        )

    # 2. DynamicAddDialog injection and accept override
    dialog_code = """
class DynamicAddDialog(QDialog):
    def __init__(self, parent, title, prompt, input_label, second_label=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(350)
        from ui.design_system import COLORS
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
        from PySide6.QtCore import Qt
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
        from ui.auth.setup_window import show_message
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

class CreateQuotationDialog(QDialog):
"""
    if "class DynamicAddDialog(QDialog):" not in content:
        content = content.replace("class CreateQuotationDialog(QDialog):", dialog_code)

    accept_override = """    def accept(self):
        pass
        
    def _force_accept(self):
        super().accept()
"""
    if "def accept(self):" not in content:
        content = content.replace("    def _load_existing_quotation(self):", accept_override + "\n    def _load_existing_quotation(self):")
        content = content.replace("self.accept()", "self._force_accept()")
        
        # restore inner accept inside DynamicAddDialog
        content = content.replace("        self._force_accept()\n        \n    def get_inputs", "        self.accept()\n        \n    def get_inputs")

    # 3. Customer Combobox replacement
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

    # 4. Service combo box replacement
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
        r'        # Add Item Button[\s\S]*?root\.addWidget\(add_item_btn, alignment=Qt\.AlignmentFlag\.AlignLeft\)',
        service_cb_code,
        content
    )

    # 5. Notes QTextEdit
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
    content = content.replace('notes=self.notes_input.text().strip(),', 'notes=self.notes_input.toPlainText().strip(),')

    # 6. Handlers
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
            self.service_cb.lineEdit().clear()

    def _add_item_row"""
    content = content.replace("    def _add_item_row", handlers_code)

    # 7. Default row behavior when no item passed
    if "def _add_item_row(self, existing_item=None):" in content:
        pass
    else:
        # modify signature
        content = content.replace("def _add_item_row(self, item=None):", "def _add_item_row(self, existing_item=None):")
        
        # update variable usage
        content = content.replace("def _add_item_row(self, item=None):", "def _add_item_row(self, existing_item=None):")
        content = content.replace("item['service_id']", "existing_item['service_id']")
        content = content.replace("item['description']", "existing_item['description']")
        content = content.replace("item['quantity']", "existing_item['quantity']")
        content = content.replace("item['unit_price']", "existing_item['unit_price']")
        
        # fix existing_item dict accesses
        content = content.replace('desc_input.setText(existing_item["description"] or "")', 'desc_input.setText(existing_item.get("description", ""))')
        content = content.replace('qty_input.setText(str(existing_item["quantity"]))', 'qty_input.setText(str(existing_item.get("quantity", 1)))')
        content = content.replace('price_input.setText(str(existing_item["unit_price"]))', 'price_input.setText(str(existing_item.get("unit_price", 0)))')

    # Remove the old "Please add at least one item" checks from anywhere except _save
    # Actually _save naturally checks `if not self.items_data:`

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_quotation_dialog(r"d:\Account_System\ui\components\create_quotation_dialog.py")
    print("Quotation dialog patched successfully.")
