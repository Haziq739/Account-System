import os

# --- Patch create_invoice_dialog.py ---
inv_path = r'd:\Account_System\ui\components\create_invoice_dialog.py'
with open(inv_path, 'r', encoding='utf-8') as f:
    inv = f.read()

# UI Layout for Invoice
if 'w_tax_input' not in inv:
    old_ui = '''self.tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1'''
    new_ui = '''self.tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1
        
        # Withholding Tax
        totals_grid.addWidget(QLabel("Withholding Tax %:"), row, 0)
        self.w_tax_input = QLineEdit("5.0")
        self.w_tax_input.setFixedWidth(100)
        self.w_tax_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.w_tax_input, row, 1)
        row += 1
        
        totals_grid.addWidget(QLabel("W. Tax Amount:"), row, 0)
        self.w_tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.w_tax_amt_lbl, row, 1)
        row += 1'''
    inv = inv.replace(old_ui, new_ui)

if 'w_tax_input.setText' not in inv:
    old_init = '''        if getattr(self, "parent_window", None):
            comp_id = getattr(self.parent_window, "current_company_id", 1)'''
    new_init = '''        if getattr(self, "parent_window", None):
            comp_id = getattr(self.parent_window, "current_company_id", 1)
            
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == getattr(self, "company_id", 1)).first()
            is_kd = comp and "K Dynamics" in comp.name
            if hasattr(self, 'w_tax_input'):
                self.w_tax_input.setText("5" if is_kd else "0")'''
    inv = inv.replace(old_init, new_init)

with open(inv_path, 'w', encoding='utf-8') as f:
    f.write(inv)


# --- Patch create_quotation_dialog.py ---
quot_path = r'd:\Account_System\ui\components\create_quotation_dialog.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot = f.read()

if 'w_tax_input' not in quot:
    quot = quot.replace(old_ui, new_ui)

if 'w_tax_input.setText' not in quot:
    quot = quot.replace(old_init, new_init)

with open(quot_path, 'w', encoding='utf-8') as f:
    f.write(quot)


# --- Patch vendor_dialogs.py ---
bill_path = r'd:\Account_System\ui\components\vendor_dialogs.py'
with open(bill_path, 'r', encoding='utf-8') as f:
    bill = f.read()

if 'w_tax_input' not in bill:
    old_bill_ui = '''        self.amount_input = QLineEdit()
        layout.addRow("Amount:", self.amount_input)'''
    new_bill_ui = '''        self.amount_input = QLineEdit()
        layout.addRow("Amount:", self.amount_input)
        
        self.w_tax_input = QLineEdit("5")
        layout.addRow("Withholding Tax %:", self.w_tax_input)
        
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == getattr(self, "company_id", 1)).first()
            is_kd = comp and "K Dynamics" in comp.name
            self.w_tax_input.setText("5" if is_kd else "0")'''
    bill = bill.replace(old_bill_ui, new_bill_ui)

    old_bill_save = '''            success = VendorBillService.create_bill(
                company_id=self.company_id,
                vendor_id=self.vendor_cb.currentData(),
                description=self.desc_input.toPlainText(),
                amount=amount
            )'''
    new_bill_save = '''            w_tax = 0.0
            try:
                w_tax = float(self.w_tax_input.text() or "0")
            except:
                pass
            success = VendorBillService.create_bill(
                company_id=self.company_id,
                vendor_id=self.vendor_cb.currentData(),
                description=self.desc_input.toPlainText(),
                amount=amount,
                withholding_tax_percentage=w_tax
            )'''
    bill = bill.replace(old_bill_save, new_bill_save)

    old_bill_upd = '''            success = VendorBillService.update_bill(
                company_id=self.company_id,
                bill_id=self.bill_data.id,
                vendor_id=self.vendor_cb.currentData(),
                description=self.desc_input.toPlainText(),
                amount=amount
            )'''
    new_bill_upd = '''            w_tax = 0.0
            try:
                w_tax = float(self.w_tax_input.text() or "0")
            except:
                pass
            success = VendorBillService.update_bill(
                company_id=self.company_id,
                bill_id=self.bill_data.id,
                vendor_id=self.vendor_cb.currentData(),
                description=self.desc_input.toPlainText(),
                amount=amount,
                withholding_tax_percentage=w_tax
            )'''
    bill = bill.replace(old_bill_upd, new_bill_upd)

    old_bill_edit = '''            self.amount_input.setText(str(self.bill_data.amount))'''
    new_bill_edit = '''            self.amount_input.setText(str(self.bill_data.amount))
            self.w_tax_input.setText(str(getattr(self.bill_data, "withholding_tax_percentage", 0.0)))'''
    bill = bill.replace(old_bill_edit, new_bill_edit)

with open(bill_path, 'w', encoding='utf-8') as f:
    f.write(bill)

print("UI patches successfully applied!")
