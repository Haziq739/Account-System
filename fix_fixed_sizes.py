import glob

def fix_all_row_action_dialogs():
    files = glob.glob(r'd:\Account_System\ui\pages\*.py')
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "class RowActionDialog(QDialog):" in content:
            old_btns = """        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)"""
            
            new_btns = """        self.edit_btn.setFixedSize(84, 38)
        self.del_btn.setFixedSize(84, 38)
        self.cancel_btn.setFixedSize(84, 38)"""
            
            if old_btns in content:
                content = content.replace(old_btns, new_btns)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)

if __name__ == "__main__":
    fix_all_row_action_dialogs()
    print("Fixed button sizes with setFixedSize")
