from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QDoubleSpinBox, QDateEdit, QComboBox
)
from PySide6.QtCore import Qt, QDate
from ui.design_system import COLORS

def _btn(text: str, primary: bool = False) -> QPushButton:
    b = QPushButton(text)
    bg = COLORS['primary'] if primary else COLORS['bg_input']
    color = "white" if primary else COLORS['text_primary']
    border = "none" if primary else f"1px solid {COLORS['border']}"
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg}; color: {color};
            border: {border}; border-radius: 6px;
            padding: 8px 16px; font-weight: bold;
        }}
        QPushButton:hover {{ opacity: 0.9; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 600; background: transparent;")
    return lbl

class VendorFormDialog(QDialog):
    """Dialog to Add or Edit a vendor."""
    def __init__(self, parent=None, vendor_data=None):
        super().__init__(parent)
        self.is_edit = bool(vendor_data)
        self.vendor_data = vendor_data or {}
        
        self.setWindowTitle("Edit Vendor" if self.is_edit else "Add New Vendor")
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
        
        self.name_input = QLineEdit(self.vendor_data.get("name", ""))
        self.name_input.setPlaceholderText("Vendor Name (Required)")
        
        self.phone_input = QLineEdit(self.vendor_data.get("phone", ""))
        self.phone_input.setPlaceholderText("Phone Number (Required)")
        
        self.address_input = QTextEdit(self.vendor_data.get("address", ""))
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
        
        layout.addWidget(_label("Vendor Name"))
        layout.addWidget(self.name_input)
        
        layout.addWidget(_label("Phone Number"))
        layout.addWidget(self.phone_input)
        
        layout.addWidget(_label("Address"))
        layout.addWidget(self.address_input)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Vendor", primary=True)
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


class CreateBillDialog(QDialog):
    """Dialog to Create or Edit a Vendor Bill."""
    def __init__(self, parent=None, vendors=None, bill_data=None):
        super().__init__(parent)
        self.vendors = vendors or []
        self.is_edit = bool(bill_data)
        self.bill_data = bill_data or {}
        
        self.setWindowTitle("Edit Bill" if self.is_edit else "Create New Bill")
        self.setFixedSize(460, 560)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        
        self.vendor_cb = QComboBox()
        self.vendor_cb.addItem("-- Select Vendor --", None)
        for v in self.vendors:
            self.vendor_cb.addItem(v['name'], v['id'])
            
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Bill Description / Details")
        self.description_input.setFixedHeight(80)
        
        if self.is_edit:
            idx = self.vendor_cb.findData(self.bill_data.get("vendor_id"))
            if idx >= 0:
                self.vendor_cb.setCurrentIndex(idx)
            self.amount_input.setValue(self.bill_data.get("amount", 0.0))
            if "bill_date" in self.bill_data and self.bill_data["bill_date"]:
                self.date_edit.setDate(self.bill_data["bill_date"])
            self.description_input.setPlainText(self.bill_data.get("description", ""))
            
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 700; background: transparent;")
        layout.addWidget(title)
        
        layout.addWidget(_label("Vendor *"))
        layout.addWidget(self.vendor_cb)
        
        layout.addWidget(_label("Amount *"))
        layout.addWidget(self.amount_input)
        
        layout.addWidget(_label("Date *"))
        layout.addWidget(self.date_edit)
        
        layout.addWidget(_label("Description (Optional)"))
        layout.addWidget(self.description_input)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Bill", primary=True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            "vendor_id": self.vendor_cb.currentData(),
            "amount": self.amount_input.value(),
            "bill_date": self.date_edit.date().toPython(),
            "description": self.description_input.toPlainText().strip()
        }
