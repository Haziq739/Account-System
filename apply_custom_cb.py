import re

with open('d:/Account_System/ui/components/payment_dialogs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace imports
content = content.replace("from PySide6.QtWidgets import (", "from ui.components.custom_combobox import CustomComboBox\nfrom PySide6.QtWidgets import (")

# 2. Replace QComboBox() instantiations with CustomComboBox()
# There are 4 comboboxes in this file.
content = content.replace("QComboBox()", "CustomComboBox()")

# 3. Remove ComboBoxDelegate entirely, we don't need it!
# Wait, I already removed sizeHint, but let's just strip the usage of it.
content = re.sub(r'self\.[a-zA-Z0-9_]+\.setItemDelegate\(ComboBoxDelegate\(\)\)', '', content)
content = re.sub(r'self\.[a-zA-Z0-9_]+\.setMaxVisibleItems\(\d+\)', '', content)

with open('d:/Account_System/ui/components/payment_dialogs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied CustomComboBox to payment_dialogs.py")
