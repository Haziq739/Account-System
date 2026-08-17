import re
import os

def insert_imports(content, imports_str):
    if "QCompleter" not in content:
        content = content.replace("QComboBox", f"QComboBox, QCompleter, {imports_str}")
    if "DynamicAddDialog" not in content:
        if "from ui.components.dynamic_add_dialog import DynamicAddDialog" not in content:
            content = content.replace("from ui.auth.setup_window import show_message", 
                                      "from ui.auth.setup_window import show_message\nfrom ui.components.dynamic_add_dialog import DynamicAddDialog")
    return content

def replace_customer_cb_ledger(content):
    content = insert_imports(content, "QListView")
    
    # Label replacement (make it dynamic based on context)
    content = content.replace('ctrl_layout.addWidget(QLabel("Customer:", styleSheet=f"color: {COLORS[\'text_primary\']};"))',
                              'lbl_text = "Customer:" if self.context == "regular" else "Vendor:" if self.context == "vendor" else "Employee:"\n        ctrl_layout.addWidget(QLabel(lbl_text, styleSheet=f"color: {COLORS[\'text_primary\']};"))')
    
    cb_code = """        self.customer_cb = QComboBox()
        self.customer_cb.setEditable(True)
        self.customer_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_cb.lineEdit().setPlaceholderText("Search or enter new...")
        self.customer_cb.currentIndexChanged.connect(self._load_ledger)
        self.customer_cb.setStyleSheet(f\"\"\"
            QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px; padding: 8px 12px;
                color: {COLORS['text_primary']};
                min-width: 200px;
            }}
        \"\"\")
        
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
        ctrl_layout.addWidget(self.customer_cb)"""
    
    content = re.sub(
        r'        self.customer_cb = QComboBox\(\)[\s\S]*?ctrl_layout\.addWidget\(self\.customer_cb\)',
        cb_code,
        content
    )
    
    handler = """
    def _on_customer_entered(self):
        text = self.customer_cb.lineEdit().text().strip()
        if not text: return
        
        idx = self.customer_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.customer_cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, f"Add New", f"'{text}' not found.\\nDo you want to add this?", "Phone Number (Required)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                new_cust = CustomerService.create_customer(self.company_id, text, phone, "", self.current_user["id"], self.context)
                self.customer_cb.blockSignals(True)
                display_name = f"{new_cust['name']} ({new_cust['phone']})" if new_cust.get('phone') else new_cust['name']
                self.customer_cb.addItem(display_name, new_cust['id'])
                idx = self.customer_cb.findData(new_cust["id"])
                if idx >= 0: self.customer_cb.setCurrentIndex(idx)
                self.customer_cb.blockSignals(False)
                self._load_ledger()
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.customer_cb.lineEdit().clear()
"""
    if "def _on_customer_entered" not in content:
        content += handler
        
    return content

def patch_ledger_page():
    path = r"d:\Account_System\ui\pages\ledger_page.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = replace_customer_cb_ledger(content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def replace_customer_cb_payment(content):
    content = insert_imports(content, "QListView")
    
    cb_code = """        self.customer_cb = QComboBox()
        self.customer_cb.setEditable(True)
        self.customer_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.customer_cb.lineEdit().setPlaceholderText("Search or enter new...")
        self.customer_cb.addItem("-- Select Customer --", None)
        for c in self.customers:
            self.customer_cb.addItem(c['name'], c['id'])
        self.customer_cb.currentIndexChanged.connect(self._on_customer_changed)
        
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
        layout.addWidget(self.customer_cb)"""
    
    content = re.sub(
        r'        self\.customer_cb = QComboBox\(\)[\s\S]*?layout\.addWidget\(self\.customer_cb\)',
        cb_code,
        content
    )
    
    handler = """    def _on_customer_entered(self):
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
                from services.customer import CustomerService
                new_cust = CustomerService.create_customer(self.company_id, text, phone, "", self.current_user["id"], "regular")
                
                self.customer_cb.blockSignals(True)
                display_name = f"{new_cust['name']} ({new_cust['phone']})" if new_cust.get('phone') else new_cust['name']
                self.customer_cb.addItem(display_name, new_cust['id'])
                idx = self.customer_cb.findData(new_cust["id"])
                if idx >= 0: self.customer_cb.setCurrentIndex(idx)
                self.customer_cb.blockSignals(False)
                self._on_customer_changed()
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.customer_cb.lineEdit().clear()
"""
    if "def _on_customer_entered" not in content:
        content = content.replace("    def _on_customer_changed(self):", handler + "\n    def _on_customer_changed(self):")
        
    return content

def patch_payment_dialogs():
    path = r"d:\Account_System\ui\components\payment_dialogs.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = replace_customer_cb_payment(content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def replace_vendor_cb_vendor(content):
    content = insert_imports(content, "QListView")
    
    cb_code = """        self.vendor_cb = QComboBox()
        self.vendor_cb.setEditable(True)
        self.vendor_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.vendor_cb.lineEdit().setPlaceholderText("Search or enter new vendor...")
        self.vendor_cb.addItem("-- Select Vendor --", None)
        for v in self.vendors:
            self.vendor_cb.addItem(v['name'], v['id'])
            
        completer = QCompleter(self.vendor_cb.model(), self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        popup = completer.popup()
        popup.setStyleSheet(f\"\"\"
            QListView {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 4px; }}
            QListView::item {{ padding: 8px; }}
            QListView::item:selected {{ background-color: #EFF6FF; color: {COLORS['primary']}; }}
        \"\"\")
        
        self.vendor_cb.setCompleter(completer)
        self.vendor_cb.lineEdit().returnPressed.connect(self._on_vendor_entered)
        layout.addWidget(self.vendor_cb)"""
        
    content = re.sub(
        r'        self\.vendor_cb = QComboBox\(\)[\s\S]*?layout\.addWidget\(self\.vendor_cb\)',
        cb_code,
        content
    )
    
    handler = """
    def _on_vendor_entered(self):
        text = self.vendor_cb.lineEdit().text().strip()
        if not text: return
        
        idx = self.vendor_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.vendor_cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, "Add Vendor", f"Vendor '{text}' not found.\\nDo you want to add this vendor?", "Phone Number (Required)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                from services.vendor_service import VendorService
                # We need company_id. VendorService.add_vendor might require it. Wait, the dialog has self.vendors but not company_id?
                # CreateBillDialog has self.vendors but no company_id?
                # Actually, let's look for company_id. If not, we'll pass it from parent.
                pass 
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.vendor_cb.lineEdit().clear()
"""
    # Wait! CreateBillDialog doesn't have company_id or current_user passed to it! 
    # Let me check vendor_dialogs.py first before writing this part.
    return content

if __name__ == "__main__":
    patch_ledger_page()
    patch_payment_dialogs()
    print("Ledger and Payment patched.")
