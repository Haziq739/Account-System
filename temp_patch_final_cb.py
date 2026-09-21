import os
import re

path = r'd:\Account_System\ui\components\create_invoice_dialog.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove duplicate _fix_cb
duplicate_fix_cb = '''        def _fix_cb(cb):
            from PySide6.QtWidgets import QListView, QStyledItemDelegate
            cb.setMaxVisibleItems(7)
            v = QListView()
            cb.setView(v)
            cb.setItemDelegate(QStyledItemDelegate())
'''
content = content.replace(duplicate_fix_cb, "")

# 2. Fix the pay_method_cb implementation
old_pay_method = '''        self.pay_method_cb.addItems(["Cash", "Bank Transfer", "Cheque", "Credit"])
        _fix_cb(self.pay_method_cb)'''

new_pay_method = '''        self.pay_method_cb.addItems(["Cash", "Bank Transfer", "Cheque", "Credit"])
        self.pay_method_cb.setMaxVisibleItems(3) # Forces scrollbar
        self.pay_method_cb.setStyleSheet(f"""
            QComboBox QAbstractItemView {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                outline: 0px;
                border-radius: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 28px;
                padding: 4px 8px;
            }}
        """)'''

content = content.replace(old_pay_method, new_pay_method)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched create_invoice_dialog.py")
