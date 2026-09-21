import os

# --- Patch create_invoice_dialog.py ---
inv_path = r'd:\Account_System\ui\components\create_invoice_dialog.py'
with open(inv_path, 'r', encoding='utf-8') as f:
    inv = f.read()

# Add to UI layout
ui_old = '''        self.tax_input = QLineEdit(str(self.tax_rate))
        self.tax_input.setFixedWidth(100)
        self.tax_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.tax_input, row, 1)
        row += 1
        
        self.tax_amt_lbl_ui = QLabel("Tax Amount:")
        totals_grid.addWidget(self.tax_amt_lbl_ui, row, 0)
        self.tax_amt_lbl = QLabel("0.00")
        self.tax_amt_lbl.setStyleSheet("font-weight: bold;")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1'''

ui_new = '''        self.tax_input = QLineEdit(str(self.tax_rate))
        self.tax_input.setFixedWidth(100)
        self.tax_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.tax_input, row, 1)
        row += 1
        
        self.tax_amt_lbl_ui = QLabel("Tax Amount:")
        totals_grid.addWidget(self.tax_amt_lbl_ui, row, 0)
        self.tax_amt_lbl = QLabel("0.00")
        self.tax_amt_lbl.setStyleSheet("font-weight: bold;")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1
        
        # Withholding Tax
        totals_grid.addWidget(QLabel("Withholding Tax %:"), row, 0)
        self.w_tax_input = QLineEdit("5.0") # Default to 5.0 for KD
        self.w_tax_input.setFixedWidth(100)
        self.w_tax_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.w_tax_input, row, 1)
        row += 1
        
        totals_grid.addWidget(QLabel("W. Tax Amount:"), row, 0)
        self.w_tax_amt_lbl = QLabel("0.00")
        self.w_tax_amt_lbl.setStyleSheet("font-weight: bold;")
        totals_grid.addWidget(self.w_tax_amt_lbl, row, 1)
        row += 1'''

inv = inv.replace(ui_old, ui_new)

# Calculate totals
calc_old = '''        tax_pct = self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0
        tax_amt = after_disc * (tax_pct / 100.0)
        self.tax_amt_lbl.setText(f"{tax_amt:.2f}")
        
        net = after_disc + tax_amt
        self.net_total_lbl.setText(f"{net:.2f}")'''

calc_new = '''        tax_pct = self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0
        tax_amt = after_disc * (tax_pct / 100.0)
        self.tax_amt_lbl.setText(f"{tax_amt:.2f}")
        
        w_tax_pct = self._get_float(self.w_tax_input.text()) if hasattr(self, 'w_tax_input') else 0.0
        w_tax_amt = after_disc * (w_tax_pct / 100.0)
        if hasattr(self, 'w_tax_amt_lbl'):
            self.w_tax_amt_lbl.setText(f"{w_tax_amt:.2f}")
        
        net = after_disc + tax_amt + w_tax_amt
        self.net_total_lbl.setText(f"{net:.2f}")'''

inv = inv.replace(calc_old, calc_new)

# Handle KD default setting inside init_ui (if company name is KD)
init_old = '''        if getattr(self, "parent_window", None):
            comp_id = getattr(self.parent_window, "current_company_id", 1)'''
init_new = '''        if getattr(self, "parent_window", None):
            comp_id = getattr(self.parent_window, "current_company_id", 1)
            
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == getattr(self, "company_id", 1)).first()
            is_kd = comp and "K Dynamics" in comp.name
            if hasattr(self, 'w_tax_input'):
                self.w_tax_input.setText("5" if is_kd else "0")
'''
inv = inv.replace(init_old, init_new)

# Save invoice
save_old = '''                tax_percentage=self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0,'''
save_new = '''                tax_percentage=self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0,
                withholding_tax_percentage=self._get_float(self.w_tax_input.text()) if hasattr(self, 'w_tax_input') else 0.0,'''
inv = inv.replace(save_old, save_new)

# Update invoice
upd_old = '''                    tax_percentage=self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0,'''
upd_new = '''                    tax_percentage=self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0,
                    withholding_tax_percentage=self._get_float(self.w_tax_input.text()) if hasattr(self, 'w_tax_input') else 0.0,'''
inv = inv.replace(upd_old, upd_new)

# Set edit data
edit_old = '''self.tax_input.setText(str(inv["tax_percentage"]))'''
edit_new = '''self.tax_input.setText(str(inv["tax_percentage"]))
        if hasattr(self, 'w_tax_input') and "withholding_tax_percentage" in inv:
            self.w_tax_input.setText(str(inv["withholding_tax_percentage"]))'''
inv = inv.replace(edit_old, edit_new)

with open(inv_path, 'w', encoding='utf-8') as f:
    f.write(inv)


# --- Patch create_quotation_dialog.py ---
# Very similar to create_invoice_dialog.py
quot_path = r'd:\Account_System\ui\components\create_quotation_dialog.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot = f.read()

quot = quot.replace(ui_old, ui_new)
quot = quot.replace(calc_old, calc_new)
quot = quot.replace(init_old, init_new)
quot = quot.replace(save_old, save_new)
quot = quot.replace(upd_old, upd_new)
edit_old_q = '''self.tax_input.setText(str(q["tax_percentage"]))'''
edit_new_q = '''self.tax_input.setText(str(q["tax_percentage"]))
        if hasattr(self, 'w_tax_input') and "withholding_tax_percentage" in q:
            self.w_tax_input.setText(str(q["withholding_tax_percentage"]))'''
quot = quot.replace(edit_old_q, edit_new_q)

with open(quot_path, 'w', encoding='utf-8') as f:
    f.write(quot)

# --- Patch vendor_dialogs.py (Vendor Bill) ---
bill_path = r'd:\Account_System\ui\components\vendor_dialogs.py'
with open(bill_path, 'r', encoding='utf-8') as f:
    bill = f.read()

# UI Layout for vendor bill
bill_ui_old = '''        self.amount_input = QLineEdit()
        layout.addRow("Amount:", self.amount_input)'''
bill_ui_new = '''        self.amount_input = QLineEdit()
        layout.addRow("Amount:", self.amount_input)
        
        self.w_tax_input = QLineEdit("5")
        layout.addRow("Withholding Tax %:", self.w_tax_input)
        
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == getattr(self, "company_id", 1)).first()
            is_kd = comp and "K Dynamics" in comp.name
            self.w_tax_input.setText("5" if is_kd else "0")
'''
bill = bill.replace(bill_ui_old, bill_ui_new)

# Save logic
bill_save_old = '''            success = VendorBillService.create_bill(
                company_id=self.company_id,
                vendor_id=self.vendor_cb.currentData(),
                description=self.desc_input.toPlainText(),
                amount=amount
            )'''
bill_save_new = '''            w_tax = 0.0
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
bill = bill.replace(bill_save_old, bill_save_new)

# Edit logic
bill_upd_old = '''            success = VendorBillService.update_bill(
                company_id=self.company_id,
                bill_id=self.bill_data.id,
                vendor_id=self.vendor_cb.currentData(),
                description=self.desc_input.toPlainText(),
                amount=amount
            )'''
bill_upd_new = '''            w_tax = 0.0
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
bill = bill.replace(bill_upd_old, bill_upd_new)

# Edit init
bill_edit_old = '''            self.amount_input.setText(str(self.bill_data.amount))'''
bill_edit_new = '''            self.amount_input.setText(str(self.bill_data.amount))
            self.w_tax_input.setText(str(getattr(self.bill_data, "withholding_tax_percentage", 0.0)))'''
bill = bill.replace(bill_edit_old, bill_edit_new)

with open(bill_path, 'w', encoding='utf-8') as f:
    f.write(bill)

print('Done patching UI')
