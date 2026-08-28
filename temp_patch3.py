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
        
    # Remove all the messy setView(QListView()) hacks we added
    content = re.sub(r'from PySide6\.QtWidgets import QListView, QFrame\n', '', content)
    content = re.sub(r'\s+v[0-9] = QListView\(\)\n', '', content)
    content = re.sub(r'\s+v[0-9]\.setFrameShape\(QFrame\.Shape\.NoFrame\)\n', '', content)
    content = re.sub(r'\s+self\.[a-zA-Z0-9_]+\.setView\(v[0-9]\)\n', '', content)
    
    # Remove the generic __v hacks from temp_patch2.py
    content = re.sub(r'\s+__v = __import__\(\'PySide6\.QtWidgets\'\)\.QtWidgets\.QListView\(\)\n', '', content)
    content = re.sub(r'\s+__v\.setFrameShape\(__import__\(\'PySide6\.QtWidgets\'\)\.QtWidgets\.QFrame\.Shape\.NoFrame\)\n', '', content)
    content = re.sub(r'\s+self\.[a-zA-Z0-9_]+\.setView\(__v\)\n', '', content)

    # Now, explicitly find every self.xxx = QComboBox() and add a QStyledItemDelegate
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
            
            # Don't add if it's already using setup_searchable_cb which does completer stuff
            has_setup = False
            for j in range(1, 4):
                if i + j < len(lines) and 'setup_searchable_cb' in lines[i+j]:
                    has_setup = True
                    break
                    
            if not has_setup:
                new_lines.append(f"{indent}__d = __import__('PySide6.QtWidgets').QtWidgets.QStyledItemDelegate()")
                new_lines.append(f"{indent}{cb_name}.setItemDelegate(__d)")
                
        i += 1

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

print("Applied QStyledItemDelegate fix")
