import os

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_tax_amt = '''        self.tax_amt_lbl_ui = QLabel("Tax Amount:")
        totals_grid.addWidget(self.tax_amt_lbl_ui, row, 0)
        self.tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1'''

    new_tax_amt = '''        self.tax_amt_lbl_ui = QLabel("Tax Amount:")
        totals_grid.addWidget(self.tax_amt_lbl_ui, row, 0)
        self.tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1
        
        self.w_tax_label_ui = QLabel("W. Tax (%):")
        totals_grid.addWidget(self.w_tax_label_ui, row, 0)
        default_w_tax = "5.0" if getattr(self, "company_name", "").find("K Dynamics") >= 0 else "0.0"
        self.w_tax_input = QLineEdit(default_w_tax)
        self.w_tax_input.setFixedWidth(100)
        self.w_tax_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.w_tax_input, row, 1)
        row += 1
        
        self.w_tax_amt_lbl_ui = QLabel("W. Tax Amount:")
        totals_grid.addWidget(self.w_tax_amt_lbl_ui, row, 0)
        self.w_tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.w_tax_amt_lbl, row, 1)
        row += 1'''

    old_hide = '''        if not self.tax_enabled:
            self.tax_label_ui.hide()
            self.tax_input.hide()
            self.tax_amt_lbl_ui.hide()
            self.tax_amt_lbl.hide()
            self.tax_input.setText("0.0")'''

    new_hide = '''        if not self.tax_enabled:
            self.tax_label_ui.hide()
            self.tax_input.hide()
            self.tax_amt_lbl_ui.hide()
            self.tax_amt_lbl.hide()
            self.tax_input.setText("0.0")
            
        if getattr(self, "company_name", "").find("K Dynamics") < 0:
            self.w_tax_label_ui.hide()
            self.w_tax_input.hide()
            self.w_tax_amt_lbl_ui.hide()
            self.w_tax_amt_lbl.hide()
            self.w_tax_input.setText("0.0")'''

    old_load_data = '''        with SessionLocal() as s:
            self.all_companies = [{"id": c.id, "name": c.name} for c in s.query(Company).all()]
            comp = s.query(Company).filter(Company.id == self.company_id).first()
            if comp:
                self.tax_enabled = comp.tax_enabled
                self.tax_rate = float(comp.default_tax_rate)'''

    new_load_data = '''        with SessionLocal() as s:
            self.all_companies = [{"id": c.id, "name": c.name} for c in s.query(Company).all()]
            comp = s.query(Company).filter(Company.id == self.company_id).first()
            if comp:
                self.company_name = comp.name
                self.tax_enabled = comp.tax_enabled
                self.tax_rate = float(comp.default_tax_rate)'''

    if "w_tax_label_ui" not in content:
        content = content.replace(old_tax_amt, new_tax_amt)
        content = content.replace(old_hide, new_hide)
        content = content.replace(old_load_data, new_load_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {path}")
    else:
        print(f"Already patched {path}")

patch_file(r'd:\Account_System\ui\components\create_invoice_dialog.py')
patch_file(r'd:\Account_System\ui\components\create_quotation_dialog.py')
