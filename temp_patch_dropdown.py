import os
import glob

def fix_black_border():
    directories = [
        r'd:\Account_System\ui\components\*.py',
        r'd:\Account_System\ui\pages\*.py',
    ]
    
    # We replace the exact padding string that exposes the black background
    old_padding = 'padding-top: 3px; padding-bottom: 0px; padding-left: 1px; padding-right: 1px;'
    new_padding = 'padding: 0px;'
    
    # Also, we might have some variations like padding-top:3px
    # Let's just use replace
    
    count = 0
    for pattern in directories:
        for filepath in glob.glob(pattern):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if old_padding in content:
                content = content.replace(old_padding, new_padding)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                count += 1
                print(f"Patched padding in: {os.path.basename(filepath)}")
                
    # Also fix global styles if necessary for QComboBox QAbstractItemView
    print(f"Total files patched: {count}")

fix_black_border()
