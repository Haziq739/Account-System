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

    # Clean slate: remove previous delegate hacks
    content = re.sub(r'\s+__d = __import__\(\'PySide6\.QtWidgets\'\)\.QtWidgets\.QStyledItemDelegate\(\)\n', '', content)
    content = re.sub(r'\s+self\.[a-zA-Z0-9_]+\.setItemDelegate\(__d\)\n', '', content)
    content = re.sub(r'\s+_fix_cb\(self\.[a-zA-Z0-9_]+\)\n', '', content)

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Inject helper inside _build
        if "def _build(self):" in line:
            new_lines.append(line)
            new_lines.append("        def _fix_cb(cb):")
            new_lines.append("            from PySide6.QtWidgets import QListView, QStyledItemDelegate")
            new_lines.append("            cb.setMaxVisibleItems(7)")
            new_lines.append("            v = QListView()")
            new_lines.append("            cb.setView(v)")
            new_lines.append("            cb.setItemDelegate(QStyledItemDelegate())")
            i += 1
            continue
            
        new_lines.append(line)
        
        # Apply fix to all QComboBoxes, except those handled by setup_searchable_cb
        match = re.search(r'(self\.[a-zA-Z0-9_]+) = QComboBox\(\)', line)
        if match:
            cb_name = match.group(1)
            indent = line[:len(line) - len(line.lstrip())]
            
            has_setup = False
            for j in range(1, 4):
                if i + j < len(lines) and 'setup_searchable_cb' in lines[i+j]:
                    has_setup = True
                    break
                    
            if not has_setup:
                new_lines.append(f"{indent}_fix_cb({cb_name})")
            
        i += 1

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

print("Applied ultimate combo box fix")
