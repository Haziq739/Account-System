import os
import re

path = r'd:\Account_System\ui\components\service_details_dialog.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Change Label
content = content.replace('Base Description *', 'Base Description (Optional)')

# Remove Validation
old_validation = '''        if not self.desc_input.toPlainText().strip():
            show_message(self, "error", "Validation Error", "Description is required.")
            return'''
content = content.replace(old_validation, '')

# Fix concatenation if base_desc is empty
old_concat = '''        final_desc = base_desc
        if extra_lines:
            final_desc += "\\n" + "\\n".join(extra_lines)'''
            
new_concat = '''        final_desc = base_desc
        if extra_lines:
            if final_desc:
                final_desc += "\\n" + "\\n".join(extra_lines)
            else:
                final_desc = "\\n".join(extra_lines)'''
                
content = content.replace(old_concat, new_concat)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully')
