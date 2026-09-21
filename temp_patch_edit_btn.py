import os

files = [
    r'd:\Account_System\ui\components\create_invoice_dialog.py',
    r'd:\Account_System\ui\components\create_quotation_dialog.py'
]

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Change Edit button text
    content = content.replace('edit_btn = QPushButton("✏️")', 'edit_btn = QPushButton("Edit")')
    
    # Change Edit button style
    old_style = 'edit_btn.setStyleSheet("color: orange; font-weight: bold; background: transparent; border: none;")'
    new_style = 'edit_btn.setStyleSheet("color: #d97706; font-weight: bold; background: #fffbeb; border: 1px solid #fcd34d; border-radius: 4px; padding: 2px 8px;")'
    content = content.replace(old_style, new_style)

    # Adjust column width for Edit
    old_col_width = 'self.table.setColumnWidth(6, 40)'
    new_col_width = 'self.table.setColumnWidth(6, 60)'
    content = content.replace(old_col_width, new_col_width)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
print('Patched Edit buttons')
