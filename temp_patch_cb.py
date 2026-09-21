import os
import glob

def remove_fix_cb():
    directories = [
        r'd:\Account_System\ui\components\*.py',
        r'd:\Account_System\ui\pages\*.py',
    ]
    
    count = 0
    for pattern in directories:
        for filepath in glob.glob(pattern):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # Remove _fix_cb for pay_method_cb
            content = content.replace("_fix_cb(self.pay_method_cb)", "")
            
            # Also remove for category_cb if present in add_expense_dialog
            content = content.replace("_fix_cb(self.category_cb)", "")
            
            # Remove for any non-editable ones if we know them
            # For now, pay_method_cb and category_cb are the main ones that aren't autocomplete completers
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                count += 1
                print(f"Removed _fix_cb from: {os.path.basename(filepath)}")

remove_fix_cb()
