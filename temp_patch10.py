import re

with open('d:/Account_System/ui/components/payment_dialogs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove BoundedComboBox class
content = re.sub(r'class BoundedComboBox\(QComboBox\):.*?(?=class AddPaymentDialog\(QDialog\):)', '', content, flags=re.DOTALL)

# 2. Add QStyledItemDelegate import
content = re.sub(r'from PySide6\.QtWidgets import \(', 'from PySide6.QtWidgets import (\n    QStyledItemDelegate,', content, count=1)

# 3. Replace BoundedComboBox() with QComboBox() + delegate
def replace_cb(match):
    name = match.group(1)
    return f"self.{name} = QComboBox()\n        self.{name}.setItemDelegate(QStyledItemDelegate())"

content = re.sub(r'self\.([a-z_]+_cb)\s*=\s*BoundedComboBox\(\)', replace_cb, content)

with open('d:/Account_System/ui/components/payment_dialogs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied: replaced BoundedComboBox with QComboBox+QStyledItemDelegate')
