import os
import re

# 1. Patch invoice_service.py
inv_path = r'd:\Account_System\services\invoice_service.py'
with open(inv_path, 'r', encoding='utf-8') as f:
    inv = f.read()

# Replace calculate totals for create_invoice
old_inv_calc = '''            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount'''
new_inv_calc = '''            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            withholding_tax_amount = (total_amount - discount) * (withholding_tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount + withholding_tax_amount'''
inv = inv.replace(old_inv_calc, new_inv_calc)

# Replace inv = Invoice(...)
old_inv_create = '''                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                net_amount=net_amount,'''
new_inv_create = '''                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                withholding_tax_percentage=withholding_tax_percentage,
                withholding_tax_amount=withholding_tax_amount,
                net_amount=net_amount,'''
inv = inv.replace(old_inv_create, new_inv_create)

# Replace update_invoice totals
old_inv_upd_create = '''            inv.tax_percentage = tax_percentage
            inv.tax_amount = tax_amount
            inv.net_amount = net_amount'''
new_inv_upd_create = '''            inv.tax_percentage = tax_percentage
            inv.tax_amount = tax_amount
            inv.withholding_tax_percentage = withholding_tax_percentage
            inv.withholding_tax_amount = withholding_tax_amount
            inv.net_amount = net_amount'''
inv = inv.replace(old_inv_upd_create, new_inv_upd_create)

with open(inv_path, 'w', encoding='utf-8') as f: f.write(inv)


# 2. Patch quotation_service.py
quot_path = r'd:\Account_System\services\quotation_service.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot = f.read()

quot = quot.replace(old_inv_calc, new_inv_calc)
quot = quot.replace(old_inv_create, new_inv_create)

old_quot_upd_create = '''            q.tax_percentage = tax_percentage
            q.tax_amount = tax_amount
            q.net_amount = net_amount'''
new_quot_upd_create = '''            q.tax_percentage = tax_percentage
            q.tax_amount = tax_amount
            q.withholding_tax_percentage = withholding_tax_percentage
            q.withholding_tax_amount = withholding_tax_amount
            q.net_amount = net_amount'''
quot = quot.replace(old_quot_upd_create, new_quot_upd_create)

with open(quot_path, 'w', encoding='utf-8') as f: f.write(quot)


# 3. Patch vendor_bill_service.py
bill_path = r'd:\Account_System\services\vendor_bill_service.py'
with open(bill_path, 'r', encoding='utf-8') as f:
    bill = f.read()

# For create
old_bill_create = '''            new_bill = VendorBill(
                company_id=company_id,
                vendor_id=vendor_id,
                bill_number=bill_number,
                description=description,
                amount=amount,
                bill_date=bill_date
            )'''
new_bill_create = '''            withholding_tax_amount = amount * (withholding_tax_percentage / 100.0)
            new_bill = VendorBill(
                company_id=company_id,
                vendor_id=vendor_id,
                bill_number=bill_number,
                description=description,
                amount=amount,
                withholding_tax_percentage=withholding_tax_percentage,
                withholding_tax_amount=withholding_tax_amount,
                bill_date=bill_date
            )'''
bill = bill.replace(old_bill_create, new_bill_create)

# For update
old_bill_update = '''            bill.vendor_id = vendor_id
            bill.description = description
            bill.amount = amount'''
new_bill_update = '''            withholding_tax_amount = amount * (withholding_tax_percentage / 100.0)
            bill.vendor_id = vendor_id
            bill.description = description
            bill.amount = amount
            bill.withholding_tax_percentage = withholding_tax_percentage
            bill.withholding_tax_amount = withholding_tax_amount'''
bill = bill.replace(old_bill_update, new_bill_update)

with open(bill_path, 'w', encoding='utf-8') as f: f.write(bill)


# 4. Patch pdf_generator.py to fix Bank Details style
pdf_path = r'd:\Account_System\services\pdf_generator.py'
with open(pdf_path, 'r', encoding='utf-8') as f: pdf = f.read()

old_bd = """bd_data = [
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
                ]))"""
                
new_bd = """bd_data = [
                    ["Name of Firm:", "K Dynamics Pvt Ltd."],
                    ["Banker Name:", "United Bank Limited"],
                    ["Address:", "Fazal e Haq Road Branch(1748)"],
                    ["IBAN Number:", "PK06 UNIL 0109 0003 2960 7942"],
                    ["Account Numbers:", "0109 0003 2960 7942"],
                    ["Branch Code:", "1748"]
                ]
                
                bd_table = Table(bd_data, colWidths=[110, 300])
                bd_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('ALIGN', (0,0), (0,-1), 'LEFT'),
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                ]))"""
pdf = pdf.replace(old_bd, new_bd)

old_bd_head = '''elements.append(Spacer(1, 20))
                elements.append(Paragraph("<b>BANK ACCOUNT DETAILS:</b>", styles['Normal']))'''
new_bd_head = '''elements.append(Spacer(1, 5))
                elements.append(Paragraph("<b>BANK ACCOUNT DETAILS:</b>", styles['Normal']))'''
pdf = pdf.replace(old_bd_head, new_bd_head)

old_bd_foot = '''elements.append(Spacer(1, 15))
                elements.append(Paragraph("<b>GST/NTN:</b> Sales Tax Reg. No. is 3277876363483 and Our NTN No .is G650435", styles['Normal']))
                elements.append(Spacer(1, 10))'''
new_bd_foot = '''elements.append(Spacer(1, 5))
                elements.append(Paragraph("<b>GST/NTN:</b> Sales Tax Reg. No. is 3277876363483 and Our NTN No .is G650435", styles['Normal']))
                elements.append(Spacer(1, 5))'''
pdf = pdf.replace(old_bd_foot, new_bd_foot)

with open(pdf_path, 'w', encoding='utf-8') as f: f.write(pdf)
print("Finished patching services and PDF.")
