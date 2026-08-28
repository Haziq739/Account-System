import os
import re

fpath = 'd:/Account_System/ui/components/payment_dialogs.py'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Clean slate: remove any QStyledItemDelegate
content = re.sub(r'\s+__d = __import__\(\'PySide6\.QtWidgets\'\)\.QtWidgets\.QStyledItemDelegate\(\)\n', '', content)
content = re.sub(r'\s+self\.[a-zA-Z0-9_]+\.setItemDelegate\(__d\)\n', '', content)

# Now, apply the bullet-proof combo box fix to customer_cb, invoice_cb, method_cb
# We will just inject a helper function and call it for each combo box

helper = """
        def _fix_cb(cb):
            from PySide6.QtWidgets import QListView, QStyledItemDelegate
            cb.setItemDelegate(QStyledItemDelegate())
            cb.setMaxVisibleItems(6)
"""

lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if "def _build(self):" in line:
        new_lines.append(line)
        # Inject helper inside _build
        new_lines.append("        def _fix_cb(cb):")
        new_lines.append("            from PySide6.QtWidgets import QListView, QStyledItemDelegate")
        new_lines.append("            cb.setMaxVisibleItems(6)")
        new_lines.append("            v = QListView()")
        new_lines.append("            cb.setView(v)")
        new_lines.append("            cb.setItemDelegate(QStyledItemDelegate())")
        i += 1
        continue
        
    new_lines.append(line)
    
    # Whenever a QComboBox is created, apply the fix
    match = re.search(r'(self\.[a-zA-Z0-9_]+) = QComboBox\(\)', line)
    if match:
        cb_name = match.group(1)
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(f"{indent}_fix_cb({cb_name})")
        
    i += 1

with open(fpath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Applied final robust combo box fix")
