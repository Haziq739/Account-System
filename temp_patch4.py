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
        
    # 1. Strip the broken QAbstractItemView styles from the stylesheets
    # The files are currently in their git checkout state (with the padding/bad hover colors intact)
    content = re.sub(r'QComboBox QAbstractItemView\s*\{\{.*?\}\}', '', content, flags=re.DOTALL)
    content = re.sub(r'QComboBox QAbstractItemView::item\s*\{\{.*?\}\}', '', content, flags=re.DOTALL)
    content = re.sub(r'QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover\s*\{\{.*?\}\}', '', content, flags=re.DOTALL)
    
    # Also strip the single bracket versions if they exist
    content = re.sub(r'QComboBox QAbstractItemView\s*\{[^}]+\}', '', content)
    content = re.sub(r'QComboBox QAbstractItemView::item\s*\{[^}]+\}', '', content)
    content = re.sub(r'QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover\s*\{[^}]+\}', '', content)

    # 2. Add QStyledItemDelegate
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        match = re.search(r'(self\.[a-zA-Z0-9_]+) = QComboBox\(\)', line)
        if match:
            cb_name = match.group(1)
            indent = line[:len(line) - len(line.lstrip())]
            
            # Don't add if it's already using setup_searchable_cb
            has_setup = False
            for j in range(1, 4):
                if i + j < len(lines) and 'setup_searchable_cb' in lines[i+j]:
                    has_setup = True
                    break
                    
            # Avoid duplicate __d additions
            has_delegate = False
            for j in range(1, 4):
                if i + j < len(lines) and 'setItemDelegate' in lines[i+j]:
                    has_delegate = True
                    break
                    
            if not has_setup and not has_delegate:
                new_lines.append(f"{indent}__d = __import__('PySide6.QtWidgets').QtWidgets.QStyledItemDelegate()")
                new_lines.append(f"{indent}{cb_name}.setItemDelegate(__d)")
                
        i += 1

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

print("Applied MASTER fix")
