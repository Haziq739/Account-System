import os
import re

path = r'd:\Account_System\ui\components\service_details_dialog.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove QComboBox custom arrow styling to revert to native arrow
content = re.sub(r'QComboBox::drop-down\s*\{.*?\}(?=\s*QComboBox::down-arrow)', '', content, flags=re.DOTALL)
content = re.sub(r'QComboBox::down-arrow\s*\{.*?\}(?=\s*QPushButton)', '', content, flags=re.DOTALL)

# Remove custom checkbox indicator styling to revert to native tick
content = re.sub(r'QCheckBox::indicator\s*\{.*?\}(?=\s*QCheckBox::indicator:checked)', '', content, flags=re.DOTALL)
content = re.sub(r'QCheckBox::indicator:checked\s*\{.*?\}(?=\s*QCheckBox::indicator:hover)', '', content, flags=re.DOTALL)
content = re.sub(r'QCheckBox::indicator:hover\s*\{.*?\}(?=\s*""")', '', content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched stylesheet')
