import os
import re

ui_dir = 'd:/Account_System/ui/components'
files_to_fix = [
    'vendor_dialogs.py',
    'create_quotation_dialog.py',
    'create_invoice_dialog.py',
    'add_expense_dialog.py'
]

for fname in files_to_fix:
    fpath = os.path.join(ui_dir, fname)
    if not os.path.exists(fpath): continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace QComboBox() assignments with a wrapper that also sets the view
    # But only if it doesn't already have setView right after
    
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Look for something like: self.some_cb = QComboBox()
        match = re.search(r'(self\.[a-zA-Z0-9_]+) = QComboBox\(\)', line)
        if match:
            cb_name = match.group(1)
            # check if next lines already have setView
            has_setview = False
            for j in range(1, 4):
                if i + j < len(lines) and 'setView' in lines[i+j]:
                    has_setview = True
                    break
            
            if not has_setview and 'AddExpenseDialog' not in fname: 
                # AddExpenseDialog handles most via setup_searchable_cb
                # Let's just do it broadly but safely
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f"{indent}__v = __import__('PySide6.QtWidgets').QtWidgets.QListView()")
                new_lines.append(f"{indent}__v.setFrameShape(__import__('PySide6.QtWidgets').QtWidgets.QFrame.Shape.NoFrame)")
                new_lines.append(f"{indent}{cb_name}.setView(__v)")
                
        i += 1

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

print("Applied QListView fix")
