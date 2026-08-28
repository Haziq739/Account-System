import os
import re

ui_dir = 'd:/Account_System/ui/components'
files_to_fix = [
    'vendor_dialogs.py',
    'payment_dialogs.py',
    'create_quotation_dialog.py',
    'create_invoice_dialog.py',
    'add_expense_dialog.py'
]

for fname in files_to_fix:
    fpath = os.path.join(ui_dir, fname)
    if not os.path.exists(fpath): continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Remove ANY line containing .setView(QListView())
    lines = content.split('\n')
    new_lines = [line for line in lines if '.setView(QListView())' not in line]

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

print("Removed setView")
