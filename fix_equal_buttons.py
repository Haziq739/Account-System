import glob
import re

def fix_all_row_action_dialogs():
    files = glob.glob(r'd:\Account_System\ui\pages\*.py')
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "class RowActionDialog(QDialog):" in content:
            # We want to add setMinimumWidth(80) to edit, del, cancel
            
            old_btns = """        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)"""
            
            new_btns = """        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.edit_btn.setMinimumWidth(80)
        self.del_btn.setMinimumWidth(80)
        self.cancel_btn.setMinimumWidth(80)"""
            
            # if it was already updated by the previous script, it will have the old_btns block
            if old_btns in content:
                content = content.replace(old_btns, new_btns)
            else:
                # if for some reason it wasn't
                fallback_old = """        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.cancel_btn)"""
                fallback_new = """        self.edit_btn.setMinimumWidth(80)
        self.del_btn.setMinimumWidth(80)
        self.cancel_btn.setMinimumWidth(80)
        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_layout.addWidget(self.edit_btn, 1)
        btn_layout.addWidget(self.del_btn, 1)
        btn_layout.addWidget(self.cancel_btn, 1)"""
                content = content.replace(fallback_old, fallback_new)
            
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

def fix_service_form_dialog():
    fpath = r'd:\Account_System\ui\components\service_dialogs.py'
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    old_btns = """        cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)"""
        
    new_btns = """        cancel_btn.setMinimumWidth(120)
        save_btn.setMinimumWidth(120)
        cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)"""
        
    if old_btns in content:
        content = content.replace(old_btns, new_btns)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_all_row_action_dialogs()
    fix_service_form_dialog()
    print("Fixed button equality by applying setMinimumWidth")
