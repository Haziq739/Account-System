import os

# 1. Patch vendor_dialogs.py
vd_path = r'd:\Account_System\ui\components\vendor_dialogs.py'
with open(vd_path, 'r', encoding='utf-8') as f:
    vd = f.read()

old_amount = '''        layout.addWidget(_label("Amount *"))
        layout.addWidget(self.amount_input)
        
        layout.addWidget(_label("Date *"))'''

new_amount = '''        layout.addWidget(_label("Amount *"))
        layout.addWidget(self.amount_input)
        
        comp_name = next((c["name"] for c in getattr(self, "all_companies", []) if c["id"] == self.company_id), "") if getattr(self, "all_companies", None) else getattr(self.parent(), "active_company_name", "")
        self.w_tax_input = QDoubleSpinBox()
        self.w_tax_input.setRange(0, 100)
        self.w_tax_input.setDecimals(1)
        self.w_tax_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        if comp_name.find("K Dynamics") >= 0:
            self.w_tax_input.setValue(5.0)
            layout.addWidget(_label("W. Tax (%)"))
            layout.addWidget(self.w_tax_input)
        else:
            self.w_tax_input.setValue(0.0)
            self.w_tax_input.hide()
            
        layout.addWidget(_label("Date *"))'''

if "w_tax_input" not in vd:
    vd = vd.replace(old_amount, new_amount)
    
old_get_data = '''    def get_data(self) -> dict:
        return {
            "vendor_id": self.vendor_cb.currentData(),
            "amount": self.amount_input.value(),
            "bill_date": self.date_edit.date().toPython(),
            "description": self.description_input.toPlainText().strip(),
            "company_id": getattr(self, "company_id", None)
        }'''

new_get_data = '''    def get_data(self) -> dict:
        return {
            "vendor_id": self.vendor_cb.currentData(),
            "amount": self.amount_input.value(),
            "withholding_tax_percentage": getattr(self, "w_tax_input", None).value() if hasattr(self, "w_tax_input") else 0.0,
            "bill_date": self.date_edit.date().toPython(),
            "description": self.description_input.toPlainText().strip(),
            "company_id": getattr(self, "company_id", None)
        }'''

vd = vd.replace(old_get_data, new_get_data)

with open(vd_path, 'w', encoding='utf-8') as f:
    f.write(vd)


# 2. Patch vendor_bills_page.py
vb_path = r'd:\Account_System\ui\pages\vendor_bills_page.py'
with open(vb_path, 'r', encoding='utf-8') as f:
    vb = f.read()

old_create_bill = '''res = VendorBillService.create_bill(
                    company_id=self.active_company_id,
                    vendor_id=data["vendor_id"],
                    description=data["description"],
                    amount=data["amount"],
                    bill_date=data["bill_date"],
                    user_id=self.current_user["id"]
                )'''

new_create_bill = '''res = VendorBillService.create_bill(
                    company_id=self.active_company_id,
                    vendor_id=data["vendor_id"],
                    description=data["description"],
                    amount=data["amount"],
                    withholding_tax_percentage=data.get("withholding_tax_percentage", 0.0),
                    bill_date=data["bill_date"],
                    user_id=self.current_user["id"]
                )'''

old_update_bill = '''VendorBillService.update_bill(
                    bill_id,
                    vendor_id=data["vendor_id"],
                    description=data["description"],
                    amount=data["amount"]
                )'''

new_update_bill = '''VendorBillService.update_bill(
                    bill_id,
                    vendor_id=data["vendor_id"],
                    description=data["description"],
                    amount=data["amount"],
                    withholding_tax_percentage=data.get("withholding_tax_percentage", 0.0)
                )'''

vb = vb.replace(old_create_bill, new_create_bill)
vb = vb.replace(old_update_bill, new_update_bill)

with open(vb_path, 'w', encoding='utf-8') as f:
    f.write(vb)

print("Vendor UI patches applied.")
