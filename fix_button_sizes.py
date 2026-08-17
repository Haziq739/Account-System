import glob
import re

def fix_all_row_action_dialogs():
    files = glob.glob(r'd:\Account_System\ui\pages\*.py')
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "class RowActionDialog(QDialog):" in content:
            # First, ensure QSizePolicy is imported
            if "QSizePolicy" not in content:
                content = content.replace("from PySide6.QtWidgets import (", "from PySide6.QtWidgets import (\n    QSizePolicy,")
                
            # Replace the button additions
            old_btns = """        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.cancel_btn)"""
        
            new_btns = """        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_layout.addWidget(self.edit_btn, 1)
        btn_layout.addWidget(self.del_btn, 1)
        btn_layout.addWidget(self.cancel_btn, 1)"""
            
            content = content.replace(old_btns, new_btns)
            
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

def fix_service_form_dialog():
    fpath = r'd:\Account_System\ui\components\service_dialogs.py'
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "QSizePolicy" not in content:
        content = content.replace("from PySide6.QtWidgets import (", "from PySide6.QtWidgets import (\n    QSizePolicy,")
        
    old_btns = """        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(save_btn, 1)"""
        
    new_btns = """        cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(save_btn, 1)"""
        
    content = content.replace(old_btns, new_btns)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_all_row_action_dialogs()
    fix_service_form_dialog()
    print("Fixed button sizes")
