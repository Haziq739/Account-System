import os
import re

# 1. Patch create_invoice_dialog.py save method
inv_path = r'd:\Account_System\ui\components\create_invoice_dialog.py'
with open(inv_path, 'r', encoding='utf-8') as f:
    inv = f.read()

# Invoice Save
old_inv_save = '''                InvoiceService.create_invoice(
                    self.company_id, cust_id, date.today(),
                    self.items_data, disc, tax, paid, method, notes, self.current_user["id"]
                )'''
new_inv_save = '''                w_tax = 0.0
                if hasattr(self, 'w_tax_input'):
                    try: w_tax = float(self.w_tax_input.text() or "0")
                    except: pass
                    
                InvoiceService.create_invoice(
                    company_id=self.company_id,
                    customer_id=cust_id,
                    issue_date=date.today(),
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    paid_amount=paid,
                    payment_method=method,
                    notes=notes,
                    user_id=self.current_user["id"]
                )'''
inv = inv.replace(old_inv_save, new_inv_save)

old_inv_upd = '''                InvoiceService.update_invoice(
                    self.invoice_data.id, self.company_id, cust_id,
                    self.items_data, disc, tax, paid, method, notes
                )'''
new_inv_upd = '''                w_tax = 0.0
                if hasattr(self, 'w_tax_input'):
                    try: w_tax = float(self.w_tax_input.text() or "0")
                    except: pass
                    
                InvoiceService.update_invoice(
                    invoice_id=self.invoice_data.id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    paid_amount=paid,
                    payment_method=method,
                    notes=notes
                )'''
inv = inv.replace(old_inv_upd, new_inv_upd)
with open(inv_path, 'w', encoding='utf-8') as f: f.write(inv)


# 2. Patch create_quotation_dialog.py save method
quot_path = r'd:\Account_System\ui\components\create_quotation_dialog.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot = f.read()

old_quot_save = '''                QuotationService.create_quotation(
                    self.company_id, cust_id, date.today(), valid_date,
                    self.items_data, disc, tax, notes, self.current_user["id"]
                )'''
new_quot_save = '''                w_tax = 0.0
                if hasattr(self, 'w_tax_input'):
                    try: w_tax = float(self.w_tax_input.text() or "0")
                    except: pass
                    
                QuotationService.create_quotation(
                    company_id=self.company_id,
                    customer_id=cust_id,
                    issue_date=date.today(),
                    valid_until=valid_date,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    notes=notes,
                    user_id=self.current_user["id"]
                )'''
quot = quot.replace(old_quot_save, new_quot_save)

old_quot_upd = '''                QuotationService.update_quotation(
                    self.quotation_data.id, self.company_id, cust_id,
                    self.items_data, disc, tax, valid_date, notes
                )'''
new_quot_upd = '''                w_tax = 0.0
                if hasattr(self, 'w_tax_input'):
                    try: w_tax = float(self.w_tax_input.text() or "0")
                    except: pass
                    
                QuotationService.update_quotation(
                    quotation_id=self.quotation_data.id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    valid_until=valid_date,
                    notes=notes
                )'''
quot = quot.replace(old_quot_upd, new_quot_upd)
with open(quot_path, 'w', encoding='utf-8') as f: f.write(quot)


# 3. Patch quotation_service.py to fix KD-Quotation
q_srv_path = r'd:\Account_System\services\quotation_service.py'
with open(q_srv_path, 'r', encoding='utf-8') as f: q_srv = f.read()
q_srv = q_srv.replace('prefix = "KD-Q"', 'prefix = "KD-Quotation-"')
with open(q_srv_path, 'w', encoding='utf-8') as f: f.write(q_srv)


# 4. Patch pdf_generator.py to include Bank Account Details for KD
pdf_path = r'd:\Account_System\services\pdf_generator.py'
with open(pdf_path, 'r', encoding='utf-8') as f: pdf_content = f.read()

bank_details = """            # Bank Account Details for KD
            if "K Dynamics" in comp.name:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("<b>BANK ACCOUNT DETAILS:</b>", styles['Normal']))
                
                bd_data = [
                    ["<b>Name of Firm:</b>", "<b>K Dynamics Pvt Ltd.</b>"],
                    ["<b>Banker Name:</b>", "<b>United Bank Limited</b>"],
                    ["<b>Address:</b>", "<b>Fazal e Haq Road Branch(1748)</b>"],
                    ["<b>IBAN Number:</b>", "<b>PK06 UNIL 0109 0003 2960 7942</b>"],
                    ["<b>Account Numbers:</b>", "<b>0109 0003 2960 7942</b>"],
                    ["<b>Branch Code:</b>", "<b>1748</b>"]
                ]
                
                bd_table = Table(bd_data, colWidths=[120, 300])
                bd_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,0), (-1,-1), 10),
                    ('ALIGN', (0,0), (0,-1), 'LEFT'),
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                    ('TOPPADDING', (0,0), (-1,-1), 2),
                ]))
                elements.append(bd_table)
                
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("<b>GST/NTN:</b> Sales Tax Reg. No. is 3277876363483 and Our NTN No .is G650435", styles['Normal']))
                elements.append(Spacer(1, 10))
            
"""

if "BANK ACCOUNT DETAILS:" not in pdf_content:
    # Insert before Thank you for your business
    pdf_content = pdf_content.replace(
        "elements.append(Paragraph(\"Thank you for your business!\", styles['Normal']))",
        bank_details + "elements.append(Paragraph(\"Thank you for your business!\", styles['Normal']))"
    )
    with open(pdf_path, 'w', encoding='utf-8') as f: f.write(pdf_content)
    
print("Successfully patched UI and PDF!")
