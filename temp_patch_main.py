import re

with open('d:/Account_System/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix QComboBox QAbstractItemView: add border to remove black background
content = content.replace(
    'border: none;\n            outline: none;\n            padding: 0px;\n        }',
    'border: 1px solid {COLORS[\'border\']};\n            outline: none;\n            padding: 0px;\n        }'
)

# Remove min-height: 35px from item to avoid Qt size calculation bugs
content = content.replace(
    'min-height: 35px;\n            padding: 4px 8px;',
    'padding: 4px 8px;'
)

with open('d:/Account_System/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Patched main.py')
