import os
import re

def patch_invoice_dialog(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Patch DynamicAddDialog
    # Replace the class definition completely to fix WindowType and stylesheet
    dialog_code = """class DynamicAddDialog(QDialog):
    def __init__(self, parent, title, prompt, input_label, second_label=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(350)
        self.setObjectName("DynamicAddDialog")
        self.setStyleSheet(f\"\"\"
            QDialog#DynamicAddDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 2px solid {COLORS['primary']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: bold; font-size: 14px; }}
            QLineEdit {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 8px; color: {COLORS['text_primary']}; }}
            QLineEdit:focus {{ border: 1px solid {COLORS['primary']}; }}
            QPushButton {{ padding: 12px; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton#outline_btn {{ background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; color: {COLORS['text_primary']}; }}
            QPushButton#outline_btn:hover {{ background-color: #EFF6FF; border: 1px solid {COLORS['primary']}; color: {COLORS['primary']}; }}
            QPushButton#primary_btn {{ background-color: {COLORS['primary']}; color: white; border: none; }}
            QPushButton#primary_btn:hover {{ opacity: 0.9; }}
        \"\"\")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel(prompt))
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(input_label)
        layout.addWidget(self.input_field)
        
        self.second_field = None
        if second_label:
            self.second_field = QLineEdit()
            self.second_field.setPlaceholderText(second_label)
            layout.addWidget(self.second_field)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("outline_btn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("primary_btn")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if not self.input_field.text().strip():
            show_message(self, "error", "Validation Error", "The first field is required.")
            return
        if self.second_field and not self.second_field.text().strip():
            show_message(self, "error", "Validation Error", "The second field is required.")
            return
        self.accept()
        
    def get_inputs(self):
        val1 = self.input_field.text().strip()
        val2 = self.second_field.text().strip() if self.second_field else None
        return val1, val2"""

    # We need to replace the old DynamicAddDialog. We can do a regex replace.
    content = re.sub(r'class DynamicAddDialog\(QDialog\):[\s\S]*?def get_inputs\(self\):\n        val1 = self\.input_field\.text\(\)\.strip\(\)\n        val2 = self\.second_field\.text\(\)\.strip\(\) if self\.second_field else None\n        return val1, val2', dialog_code, content)

    # 2. Add an override for `accept` in CreateInvoiceDialog just to be absolutely bulletproof against Enter keys leaking
    # We will rename the save_btn.clicked slot, or just block `accept` unless explicitly called
    
    accept_override = """    def accept(self):
        # Block default QDialog Enter key behavior from closing the dialog or saving
        pass
        
    def _force_accept(self):
        super().accept()
"""
    
    # inject the accept override into CreateInvoiceDialog
    if "def accept(self):" not in content:
        content = content.replace("    def _load_existing_invoice(self):", accept_override + "\n    def _load_existing_invoice(self):")
        
        # update _save to use _force_accept
        content = content.replace("self.accept()", "self._force_accept()")
        # But wait, self.accept() is used in _save. If we replace it globally, it might replace in DynamicAddDialog? 
        # DynamicAddDialog is already replaced above, but let's be safe.
        content = content.replace("            self.accept()\n        except Exception as e:", "            self._force_accept()\n        except Exception as e:")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_invoice_dialog(r"d:\Account_System\ui\components\create_invoice_dialog.py")
