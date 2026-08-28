import re

with open('d:/Account_System/ui/components/payment_dialogs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all blocks that look like:
# 
pattern = r'self\.[a-zA-Z0-9_]+\.view\(\)\.setStyleSheet\(f\"\"\"[\s\S]*?\"\"\"\)'
content = re.sub(pattern, '', content)

with open('d:/Account_System/ui/components/payment_dialogs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed all local QComboBox view stylesheets from payment_dialogs.py")
