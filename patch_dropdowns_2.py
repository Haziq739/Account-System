import re

def insert_imports(content, imports_str):
    if 'QCompleter' not in content:
        content = content.replace('QComboBox', f'QComboBox, QCompleter, {imports_str}')
    if 'DynamicAddDialog' not in content:
        if 'from ui.components.dynamic_add_dialog import DynamicAddDialog' not in content:
            content = content.replace('from ui.auth.setup_window import show_message', 
                                      'from ui.auth.setup_window import show_message\nfrom ui.components.dynamic_add_dialog import DynamicAddDialog')
    return content

def replace_vendor_cb_vendor():
    path = r'd:\Account_System\ui\components\vendor_dialogs.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = insert_imports(content, 'QListView')
    if 'from PySide6.QtCore' in content and 'Qt' not in content:
        content = content.replace('from PySide6.QtCore import', 'from PySide6.QtCore import Qt,')
    
    cb_code = '''        self.vendor_cb = QComboBox()
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
        
        from ui.design_system import COLORS
        popup = completer.popup()
        popup.setStyleSheet(f"""
            QListView {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 4px; }}
            QListView::item {{ padding: 8px; }}
            QListView::item:selected {{ background-color: #EFF6FF; color: {COLORS['primary']}; }}
        """)
        
        self.vendor_cb.setCompleter(completer)
        self.vendor_cb.lineEdit().returnPressed.connect(self._on_vendor_entered)'''
        
    content = re.sub(
        r'        self\.vendor_cb = QComboBox\(\)[\s\S]*?self\.vendor_cb\.addItem\(v\[\'name\'\], v\[\'id\'\]\)',
        cb_code,
        content
    )
    
    handler = '''
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
                comp_id = self.parent().active_company_id
                user_id = self.parent().current_user["id"]
                new_vend = VendorService.create_vendor(comp_id, text, phone, "", user_id)
                
                self.vendor_cb.blockSignals(True)
                display_name = f"{new_vend['name']} ({new_vend['phone']})" if new_vend.get('phone') else new_vend['name']
                self.vendor_cb.addItem(display_name, new_vend['id'])
                idx = self.vendor_cb.findData(new_vend["id"])
                if idx >= 0: self.vendor_cb.setCurrentIndex(idx)
                self.vendor_cb.blockSignals(False)
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.vendor_cb.lineEdit().clear()
'''
    if 'def _on_vendor_entered' not in content:
        content = content.replace('    def get_data(self) -> dict:', handler + '\n    def get_data(self) -> dict:')
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def replace_add_expense_cbs():
    path = r'd:\Account_System\ui\components\add_expense_dialog.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = insert_imports(content, 'QListView, QCompleter')
    
    # Generic replacement function for all three combo boxes
    def make_cb_code(type_str, plural_str):
        upper_type = type_str.capitalize()
        return f'''        self.{type_str}_cb = QComboBox()
        self.{type_str}_cb.setEditable(True)
        self.{type_str}_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.{type_str}_cb.lineEdit().setPlaceholderText("Search or enter new {type_str}...")
        self.{type_str}_cb.addItem("-- None --", None)
        for item in self.{plural_str}:
            self.{type_str}_cb.addItem(item['name'], item['id'])
            
        completer_{type_str} = QCompleter(self.{type_str}_cb.model(), self)
        completer_{type_str}.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer_{type_str}.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer_{type_str}.setFilterMode(Qt.MatchFlag.MatchContains)
        
        popup_{type_str} = completer_{type_str}.popup()
        popup_{type_str}.setStyleSheet(f"""
            QListView {{ background-color: {{COLORS['bg_card']}}; color: {{COLORS['text_primary']}}; border: 1px solid {{COLORS['border']}}; border-radius: 4px; }}
            QListView::item {{ padding: 8px; }}
            QListView::item:selected {{ background-color: #EFF6FF; color: {{COLORS['primary']}}; }}
        """)
        
        self.{type_str}_cb.setCompleter(completer_{type_str})
        self.{type_str}_cb.lineEdit().returnPressed.connect(self._on_{type_str}_entered)
        layout.addWidget(self.{type_str}_cb)'''
        
    # Replace Customer
    content = re.sub(
        r'        self\.customer_cb = QComboBox\(\)[\s\S]*?layout\.addWidget\(self\.customer_cb\)',
        make_cb_code('customer', 'customers'),
        content
    )
    
    # Replace Vendor
    content = re.sub(
        r'        self\.vendor_cb = QComboBox\(\)[\s\S]*?layout\.addWidget\(self\.vendor_cb\)',
        make_cb_code('vendor', 'vendors'),
        content
    )
    
    # Replace Employee
    content = re.sub(
        r'        self\.employee_cb = QComboBox\(\)[\s\S]*?layout\.addWidget\(self\.employee_cb\)',
        make_cb_code('employee', 'employees'),
        content
    )
    
    handlers = '''
    def _on_customer_entered(self):
        self._handle_dynamic_add(self.customer_cb, "Customer", "regular", "CustomerService", "create_customer")
        
    def _on_vendor_entered(self):
        self._handle_dynamic_add(self.vendor_cb, "Vendor", None, "VendorService", "create_vendor")
        
    def _on_employee_entered(self):
        self._handle_dynamic_add(self.employee_cb, "Employee", None, "EmployeeService", "create_employee")
        
    def _handle_dynamic_add(self, cb, type_name, context, service_name, method_name):
        text = cb.lineEdit().text().strip()
        if not text: return
        
        idx = cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, f"Add {type_name}", f"{type_name} '{text}' not found.\\nDo you want to add this {type_name.lower()}?", "Phone Number (Required)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                import importlib
                module_name = f"services.{type_name.lower()}"
                if type_name == "Vendor": module_name = "services.vendor_service"
                if type_name == "Employee": module_name = "services.employee_service"
                
                module = importlib.import_module(module_name)
                service_class = getattr(module, service_name)
                method = getattr(service_class, method_name)
                
                if context:
                    new_item = method(self.company_id, text, phone, "", self.current_user["id"], context)
                else:
                    new_item = method(self.company_id, text, phone, "", self.current_user["id"])
                
                cb.blockSignals(True)
                display_name = f"{new_item['name']} ({new_item['phone']})" if new_item.get('phone') else new_item['name']
                cb.addItem(display_name, new_item['id'])
                idx = cb.findData(new_item["id"])
                if idx >= 0: cb.setCurrentIndex(idx)
                cb.blockSignals(False)
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            cb.lineEdit().clear()
'''
    if 'def _on_customer_entered' not in content:
        content = content.replace('    def _save(self):', handlers + '\n    def _save(self):')
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    replace_vendor_cb_vendor()
    replace_add_expense_cbs()
    print("Vendor and Expense patched.")
