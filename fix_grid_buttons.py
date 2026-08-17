import glob
import re

def fix_all_row_action_dialogs():
    files = glob.glob(r'd:\Account_System\ui\pages\*.py')
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "class RowActionDialog(QDialog):" in content:
            # First, ensure QGridLayout is imported
            if "QGridLayout" not in content:
                content = content.replace("from PySide6.QtWidgets import (", "from PySide6.QtWidgets import (\n    QGridLayout,")
                
            # Replace the QHBoxLayout and button additions
            # We need a robust regex to find the button layout block
            
            # The start is: btn_layout = QHBoxLayout()
            # The end is: layout.addLayout(btn_layout)
            
            pattern = re.compile(r'        btn_layout = QHBoxLayout\(\).*?layout\.addLayout\(btn_layout\)', re.DOTALL)
            
            new_block = """        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        btn_layout.setColumnStretch(2, 1)
        
        self.edit_btn = _btn("Edit", primary=True)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet(f"background-color: #FEE2E2; color: #EF4444; border: 1px solid #FCA5A5; padding: 8px 16px; border-radius: 6px; font-weight: 600;")
        self.cancel_btn = _btn("Cancel")
        
        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_layout.addWidget(self.edit_btn, 0, 0)
        btn_layout.addWidget(self.del_btn, 0, 1)
        btn_layout.addWidget(self.cancel_btn, 0, 2)
        
        layout.addLayout(btn_layout)"""
            
            content = pattern.sub(new_block, content)
            
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

def fix_service_form_dialog():
    fpath = r'd:\Account_System\ui\components\service_dialogs.py'
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "QGridLayout" not in content:
        content = content.replace("from PySide6.QtWidgets import (", "from PySide6.QtWidgets import (\n    QGridLayout,")
        
    pattern = re.compile(r'        btn_layout = QHBoxLayout\(\).*?layout\.addLayout\(btn_layout\)', re.DOTALL)
    
    new_block = """        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_text = "Update" if self.is_edit else "Save Service"
        save_btn = _btn(save_text, primary=True)
        save_btn.clicked.connect(self.accept)
        
        cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_layout.addWidget(cancel_btn, 0, 0)
        btn_layout.addWidget(save_btn, 0, 1)
        
        layout.addLayout(btn_layout)"""
        
    content = pattern.sub(new_block, content)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_all_row_action_dialogs()
    fix_service_form_dialog()
    print("Fixed button equality using QGridLayout")
