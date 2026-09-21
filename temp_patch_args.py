import os

def patch_invoice_dialog():
    path = r'd:\Account_System\ui\components\create_invoice_dialog.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_call = """                InvoiceService.update_invoice(
                    invoice_id=self.invoice_id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    paid_amount=paid,
                    payment_method=method,
                    notes=notes
                )"""
                
    new_call = """                InvoiceService.update_invoice(
                    inv_id=self.invoice_id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    notes=notes,
                    user_id=self.current_user["id"]
                )"""
    
    if old_call in content:
        content = content.replace(old_call, new_call)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched create_invoice_dialog.py")
    else:
        print("Could not find invoice old_call")

def patch_quotation_dialog():
    path = r'd:\Account_System\ui\components\create_quotation_dialog.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_call = """                QuotationService.update_quotation(
                    quotation_id=self.quotation_data.id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    valid_until=valid_date,
                    notes=notes
                )"""
                
    new_call = """                QuotationService.update_quotation(
                    quotation_id=self.quotation_data.id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    notes=notes,
                    user_id=self.current_user["id"]
                )"""
    
    if old_call in content:
        content = content.replace(old_call, new_call)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched create_quotation_dialog.py")
    else:
        print("Could not find quotation old_call")

patch_invoice_dialog()
patch_quotation_dialog()
