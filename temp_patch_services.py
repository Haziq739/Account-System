import os
import re

# --- Patch invoice_service.py ---
invoice_path = r'd:\Account_System\services\invoice_service.py'
with open(invoice_path, 'r', encoding='utf-8') as f:
    inv_content = f.read()

# 1. Add generate sequence logic for KD
old_gen = '''            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RN"
                elif "K Dynamics" in comp.name:
                    prefix = "KD"
            
            invoices = s.query(Invoice.invoice_number).filter(Invoice.invoice_number.like(f"{prefix}-%")).all()
            max_seq = 0'''
new_gen = '''            is_kd = False
            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RN"
                elif "K Dynamics" in comp.name:
                    prefix = "KD"
                    is_kd = True
            
            invoices = s.query(Invoice.invoice_number).filter(Invoice.invoice_number.like(f"{prefix}-%")).all()
            max_seq = 49 if is_kd else 0'''
inv_content = inv_content.replace(old_gen, new_gen)

# 2. Add withholding_tax to create_invoice args
inv_content = inv_content.replace(
    'tax_percentage: float,',
    'tax_percentage: float,\n        withholding_tax_percentage: float = 0.0,'
)

# 3. Add withholding_tax to create_invoice calculations
old_calc = '''            total_amount = sum([item["quantity"] * item["price"] for item in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
            
            inv = Invoice(
                company_id=company_id,
                customer_id=customer_id,
                invoice_number=InvoiceService.generate_invoice_number(company_id),
                category=items[0]["category"] if items else "Other",
                total_amount=total_amount,
                discount=discount,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                net_amount=net_amount,
                notes=notes
            )'''
new_calc = '''            total_amount = sum([item["quantity"] * item["price"] for item in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            withholding_tax_amount = (total_amount - discount) * (withholding_tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount + withholding_tax_amount
            
            inv = Invoice(
                company_id=company_id,
                customer_id=customer_id,
                invoice_number=InvoiceService.generate_invoice_number(company_id),
                category=items[0]["category"] if items else "Other",
                total_amount=total_amount,
                discount=discount,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                withholding_tax_percentage=withholding_tax_percentage,
                withholding_tax_amount=withholding_tax_amount,
                net_amount=net_amount,
                notes=notes
            )'''
inv_content = inv_content.replace(old_calc, new_calc)

# 4. Add withholding_tax to update_invoice args
inv_content = inv_content.replace(
    '        tax_percentage: float,\n        notes: str,',
    '        tax_percentage: float,\n        withholding_tax_percentage: float,\n        notes: str,'
)

# 5. Add withholding_tax to update_invoice calculations
old_upd_calc = '''            total_amount = sum([i["quantity"] * i["price"] for i in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
            
            inv.total_amount = total_amount
            inv.discount = discount
            inv.tax_percentage = tax_percentage
            inv.tax_amount = tax_amount
            inv.net_amount = net_amount
            inv.notes = notes'''
new_upd_calc = '''            total_amount = sum([i["quantity"] * i["price"] for i in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            withholding_tax_amount = (total_amount - discount) * (withholding_tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount + withholding_tax_amount
            
            inv.total_amount = total_amount
            inv.discount = discount
            inv.tax_percentage = tax_percentage
            inv.tax_amount = tax_amount
            inv.withholding_tax_percentage = withholding_tax_percentage
            inv.withholding_tax_amount = withholding_tax_amount
            inv.net_amount = net_amount
            inv.notes = notes'''
inv_content = inv_content.replace(old_upd_calc, new_upd_calc)

# 6. Include withholding_tax in get_invoices list
inv_content = inv_content.replace(
    '"tax_percentage": float(inv.tax_percentage),',
    '"tax_percentage": float(inv.tax_percentage),\n                "withholding_tax_percentage": float(getattr(inv, "withholding_tax_percentage", 0.0)),'
)

with open(invoice_path, 'w', encoding='utf-8') as f:
    f.write(inv_content)

print('invoice_service.py patched')

# --- Patch quotation_service.py ---
quot_path = r'd:\Account_System\services\quotation_service.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot_content = f.read()

# 1. Add generate sequence logic for KD
old_gen_q = '''            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RN-Q"
                elif "K Dynamics" in comp.name:
                    prefix = "KD-Q"
            
            quotations = s.query(Quotation.quotation_number).filter(Quotation.quotation_number.like(f"{prefix}-%")).all()
            max_seq = 0'''
new_gen_q = '''            is_kd = False
            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RN-Q"
                elif "K Dynamics" in comp.name:
                    prefix = "KD-Q"
                    is_kd = True
            
            quotations = s.query(Quotation.quotation_number).filter(Quotation.quotation_number.like(f"{prefix}-%")).all()
            max_seq = 49 if is_kd else 0'''
quot_content = quot_content.replace(old_gen_q, new_gen_q)

# 2. Add withholding_tax to create_quotation args
quot_content = quot_content.replace(
    'tax_percentage: float,',
    'tax_percentage: float,\n        withholding_tax_percentage: float = 0.0,'
)

# 3. Add withholding_tax to create_quotation calculations
old_calc_q = '''            total_amount = sum([item["quantity"] * item["price"] for item in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
            
            q = Quotation(
                company_id=company_id,
                customer_id=customer_id,
                quotation_number=QuotationService.generate_quotation_number(company_id),
                category=items[0]["category"] if items else "Other",
                total_amount=total_amount,
                discount=discount,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                net_amount=net_amount,
                notes=notes
            )'''
new_calc_q = '''            total_amount = sum([item["quantity"] * item["price"] for item in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            withholding_tax_amount = (total_amount - discount) * (withholding_tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount + withholding_tax_amount
            
            q = Quotation(
                company_id=company_id,
                customer_id=customer_id,
                quotation_number=QuotationService.generate_quotation_number(company_id),
                category=items[0]["category"] if items else "Other",
                total_amount=total_amount,
                discount=discount,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                withholding_tax_percentage=withholding_tax_percentage,
                withholding_tax_amount=withholding_tax_amount,
                net_amount=net_amount,
                notes=notes
            )'''
quot_content = quot_content.replace(old_calc_q, new_calc_q)

# 4. Add withholding_tax to update_quotation args
quot_content = quot_content.replace(
    '        tax_percentage: float,\n        notes: str,',
    '        tax_percentage: float,\n        withholding_tax_percentage: float,\n        notes: str,'
)

# 5. Add withholding_tax to update_quotation calculations
old_upd_calc_q = '''            total_amount = sum([i["quantity"] * i["price"] for i in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
            
            q.total_amount = total_amount
            q.discount = discount
            q.tax_percentage = tax_percentage
            q.tax_amount = tax_amount
            q.net_amount = net_amount
            q.notes = notes'''
new_upd_calc_q = '''            total_amount = sum([i["quantity"] * i["price"] for i in items])
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            withholding_tax_amount = (total_amount - discount) * (withholding_tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount + withholding_tax_amount
            
            q.total_amount = total_amount
            q.discount = discount
            q.tax_percentage = tax_percentage
            q.tax_amount = tax_amount
            q.withholding_tax_percentage = withholding_tax_percentage
            q.withholding_tax_amount = withholding_tax_amount
            q.net_amount = net_amount
            q.notes = notes'''
quot_content = quot_content.replace(old_upd_calc_q, new_upd_calc_q)

# 6. convert to invoice logic (needs withholing_tax_percentage added to `create_invoice` call)
old_conv_q = '''            return InvoiceService.create_invoice(
                company_id=q.company_id,
                customer_id=q.customer_id,
                items=invoice_items,
                discount=float(q.discount),
                tax_percentage=float(q.tax_percentage),
                notes=q.notes,
                user_id=1
            )'''
new_conv_q = '''            return InvoiceService.create_invoice(
                company_id=q.company_id,
                customer_id=q.customer_id,
                items=invoice_items,
                discount=float(q.discount),
                tax_percentage=float(q.tax_percentage),
                withholding_tax_percentage=float(getattr(q, "withholding_tax_percentage", 0.0)),
                notes=q.notes,
                user_id=1
            )'''
quot_content = quot_content.replace(old_conv_q, new_conv_q)

# 7. List quotation
quot_content = quot_content.replace(
    '"tax_percentage": float(q.tax_percentage),',
    '"tax_percentage": float(q.tax_percentage),\n                "withholding_tax_percentage": float(getattr(q, "withholding_tax_percentage", 0.0)),'
)

with open(quot_path, 'w', encoding='utf-8') as f:
    f.write(quot_content)

print('quotation_service.py patched')

# --- Patch vendor_bill_service.py ---
bill_path = r'd:\Account_System\services\vendor_bill_service.py'
with open(bill_path, 'r', encoding='utf-8') as f:
    bill_content = f.read()

# 1. create_bill args
bill_content = bill_content.replace(
    '        amount: float,',
    '        amount: float,\n        withholding_tax_percentage: float = 0.0,'
)

# 2. create_bill calculations
old_calc_b = '''            bill = VendorBill(
                company_id=company_id,
                vendor_id=vendor_id,
                bill_number=VendorBillService.generate_bill_number(company_id),
                description=description,
                amount=amount,
                bill_date=date.today()
            )
            s.add(bill)
            s.commit()
            
            # Post to Day Book
            from models.expense import Expense
            exp = Expense(
                company_id=company_id,
                vendor_id=vendor_id,
                title=f"Vendor Bill {bill.bill_number}",
                amount=amount,
                expense_date=date.today()
            )'''
new_calc_b = '''            w_amount = amount * (withholding_tax_percentage / 100.0)
            net_amt = amount + w_amount
            bill = VendorBill(
                company_id=company_id,
                vendor_id=vendor_id,
                bill_number=VendorBillService.generate_bill_number(company_id),
                description=description,
                amount=amount,
                withholding_tax_percentage=withholding_tax_percentage,
                withholding_tax_amount=w_amount,
                net_amount=net_amt,
                bill_date=date.today()
            )
            s.add(bill)
            s.commit()
            
            # Post to Day Book
            from models.expense import Expense
            exp = Expense(
                company_id=company_id,
                vendor_id=vendor_id,
                title=f"Vendor Bill {bill.bill_number}",
                amount=net_amt,
                expense_date=date.today()
            )'''
bill_content = bill_content.replace(old_calc_b, new_calc_b)

# 3. update_bill args
bill_content = bill_content.replace(
    '        amount: float,\n        user_id: int = None',
    '        amount: float,\n        withholding_tax_percentage: float = 0.0,\n        user_id: int = None'
)

# 4. update_bill calculations
old_upd_calc_b = '''            b.vendor_id = vendor_id
            b.description = description
            b.amount = amount
            s.commit()
            
            # Also update the corresponding Expense in Day Book
            from models.expense import Expense
            exp = s.query(Expense).filter(
                Expense.company_id == company_id,
                Expense.title == f"Vendor Bill {b.bill_number}",
                Expense.is_deleted == False
            ).first()
            
            if exp:
                exp.amount = amount'''
new_upd_calc_b = '''            w_amount = amount * (withholding_tax_percentage / 100.0)
            net_amt = amount + w_amount
            b.vendor_id = vendor_id
            b.description = description
            b.amount = amount
            b.withholding_tax_percentage = withholding_tax_percentage
            b.withholding_tax_amount = w_amount
            b.net_amount = net_amt
            s.commit()
            
            # Also update the corresponding Expense in Day Book
            from models.expense import Expense
            exp = s.query(Expense).filter(
                Expense.company_id == company_id,
                Expense.title == f"Vendor Bill {b.bill_number}",
                Expense.is_deleted == False
            ).first()
            
            if exp:
                exp.amount = net_amt'''
bill_content = bill_content.replace(old_upd_calc_b, new_upd_calc_b)

with open(bill_path, 'w', encoding='utf-8') as f:
    f.write(bill_content)

print('vendor_bill_service.py patched')
