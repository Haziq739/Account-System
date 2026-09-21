import os

# --- Fix invoice_service.py ---
invoice_path = r'd:\Account_System\services\invoice_service.py'
with open(invoice_path, 'r', encoding='utf-8') as f:
    inv_content = f.read()
inv_content = inv_content.replace(
    'tax_percentage: float,\n        withholding_tax_percentage: float = 0.0,',
    'tax_percentage: float,\n        withholding_tax_percentage: float,'
)
with open(invoice_path, 'w', encoding='utf-8') as f:
    f.write(inv_content)

# --- Fix quotation_service.py ---
quot_path = r'd:\Account_System\services\quotation_service.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot_content = f.read()
quot_content = quot_content.replace(
    'tax_percentage: float,\n        withholding_tax_percentage: float = 0.0,',
    'tax_percentage: float,\n        withholding_tax_percentage: float,'
)
with open(quot_path, 'w', encoding='utf-8') as f:
    f.write(quot_content)

# --- Fix vendor_bill_service.py ---
bill_path = r'd:\Account_System\services\vendor_bill_service.py'
with open(bill_path, 'r', encoding='utf-8') as f:
    bill_content = f.read()
# For create_bill:
# original was: amount: float,
# we replaced with: amount: float,\n        withholding_tax_percentage: float = 0.0,
# BUT there are no positional args after it in create_bill?
# Let's check: user_id is passed as keyword arg with default sometimes, but let's just make it without default
bill_content = bill_content.replace(
    'amount: float,\n        withholding_tax_percentage: float = 0.0,',
    'amount: float,\n        withholding_tax_percentage: float,'
)
with open(bill_path, 'w', encoding='utf-8') as f:
    f.write(bill_content)

print('Syntax errors fixed')
