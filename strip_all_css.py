import os
import re

def strip_buggy_css(directory):
    # Match any QComboBox QAbstractItemView blocks and item selectors
    pattern = r'QComboBox QAbstractItemView\s*\{[^}]*\}\s*(QComboBox QAbstractItemView::item\s*\{[^}]*\}\s*)?(QComboBox QAbstractItemView::item:hover,\s*QComboBox QAbstractItemView::item:selected\s*\{[^}]*\})?'
    
    # Also match local view stylesheets
    local_pattern = r'self\.[a-zA-Z0-9_]+\.view\(\)\.setStyleSheet\(f\"\"\"[\s\S]*?\"\"\"\)'
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = re.sub(pattern, '', content)
                new_content = re.sub(local_pattern, '', new_content)
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Cleaned {path}")

if __name__ == '__main__':
    strip_buggy_css('d:/Account_System/ui')
    strip_buggy_css('d:/Account_System')
    print("Done cleaning all combobox CSS!")
