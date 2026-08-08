from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt
from ui.design_system import COLORS

def _btn(text: str, primary: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFixedHeight(36)
    return b

def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 600; background: transparent;")
    return lbl

class CustomerFormDialog(QDialog):
    """Dialog to Add or Edit a customer."""
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.is_edit = bool(customer_data)
        self.customer_data = customer_data or {}
        
        self.setWindowTitle("Edit Customer" if self.is_edit else "Add New Customer")
        self.setFixedSize(460, 480)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QLineEdit, QTextEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        
        self.name_input = QLineEdit(self.customer_data.get("name", ""))
        self.name_input.setPlaceholderText("Customer Name (Required)")
        
        self.phone_input = QLineEdit(self.customer_data.get("phone", ""))
        self.phone_input.setPlaceholderText("Phone Number (Required)")
        
        self.address_input = QTextEdit(self.customer_data.get("address", ""))
        self.address_input.setPlaceholderText("Full Address")
        self.address_input.setFixedHeight(100)
        
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 700; background: transparent;")
        layout.addWidget(title)
        
        layout.addWidget(_label("Customer Name"))
        layout.addWidget(self.name_input)
        
        layout.addWidget(_label("Phone Number"))
        layout.addWidget(self.phone_input)
        
        layout.addWidget(_label("Address"))
        layout.addWidget(self.address_input)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Customer", primary=True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip()
        }


class CSVImportSummaryDialog(QDialog):
    """Dialog showing the results of a CSV import."""
    def __init__(self, parent=None, imported=0, skipped=0, failed=0):
        super().__init__(parent)
        self.setWindowTitle("Import Summary")
        self.setFixedSize(350, 300)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        icon = QLabel("📊")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        layout.addWidget(icon)
        
        title = QLabel("Import Summary")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 700; background: transparent;")
        layout.addWidget(title)
        
        layout.addSpacing(16)
        
        def _stat(label: str, count: int, color: str):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; background: transparent;")
            val = QLabel(str(count))
            val.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            layout.addLayout(row)
            
        _stat("Imported successfully:", imported, COLORS['success'])
        _stat("Skipped (duplicates):", skipped, "#F59E0B") # amber
        _stat("Failed (invalid row):", failed, "#EF4444")  # red
        
        layout.addStretch()
        
        ok_btn = _btn("Close", primary=True)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
