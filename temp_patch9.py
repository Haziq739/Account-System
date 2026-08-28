import re

with open('d:/Account_System/ui/components/payment_dialogs.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_style = '''f"""
            QListView {{
                background-color: {COLORS['bg_card']};
                border: none;
                outline: 0;
                padding: 0px;
            }}
            QListView::item {{
                min-height: 32px;
                padding: 0px 8px;
                border: none;
                color: {COLORS['text_primary']};
            }}
            QListView::item:hover, QListView::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
            }}
        """'''

pattern = r'\.view\(\)\.setStyleSheet\(f\"\"\"\n.*?\"\"\"\)'
new_content, count = re.subn(pattern, '.view().setStyleSheet(' + new_style + ')', content, flags=re.DOTALL)

with open('d:/Account_System/ui/components/payment_dialogs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Replaced {count} stylesheets')
