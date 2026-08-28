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
        
    # 1. Fix black border (remove padding from QAbstractItemView)
    # Be careful to only remove padding from QAbstractItemView, but the regex I used before broke it.
    # Actually, in git checkout state, the QAbstractItemView is perfectly structured.
    # Let's cleanly remove it block by block via regex but correctly:
    content = re.sub(r'QComboBox QAbstractItemView\s*\{\{.*?\}\}', '', content, flags=re.DOTALL)
    content = re.sub(r'QComboBox QAbstractItemView::item\s*\{\{.*?\}\}', '', content, flags=re.DOTALL)
    content = re.sub(r'QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover\s*\{\{.*?\}\}', '', content, flags=re.DOTALL)
    
    # 3. Fix the QListView jumping bug by removing setView
    content = content.replace('self.customer_cb.setView(QListView())', '')
    content = content.replace('self.invoice_cb.setView(QListView())', '')
    content = content.replace('self.method_cb.setView(QListView())', '')
    content = content.replace('self.vendor_cb.setView(QListView())', '')
    content = content.replace('self.expense_type_cb.setView(QListView())', '')
    content = content.replace('self.employee_cb.setView(QListView())', '')
    content = content.replace('self.payment_method_cb.setView(QListView())', '')
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Fixed properly')
