from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QDoubleSpinBox, QDateEdit, QComboBox, QCompleter, QListView,
    QGridLayout
)
from PySide6.QtCore import Qt, QDate
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from ui.components.dynamic_add_dialog import DynamicAddDialog

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
        self.phone_input.setPlaceholderText("Phone Number (Optional)")
        
        self.address_input = QTextEdit(self.vendor_data.get("address", ""))
        self.address_input.setPlaceholderText("Full Address")
        self.address_input.setFixedHeight(100)
        
        self._build()


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

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
        
        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Vendor", primary=True)
        save_btn.clicked.connect(self._validate_and_accept)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        
        cancel_btn.setFixedSize(160, 38)
        save_btn.setFixedSize(160, 38)
        
        btn_layout.addWidget(cancel_btn, 0, 0)
        btn_layout.addWidget(save_btn, 0, 1)
        
        layout.addLayout(btn_layout)


    def _on_vendor_entered(self):
        text = self.vendor_cb.lineEdit().text().strip()
        if not text: return
        
        idx = self.vendor_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.vendor_cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, "Add Vendor", f"Vendor '{text}' not found.\nDo you want to add this vendor?", "Phone Number (Optional)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                from services.vendor_service import VendorService
                comp_id = self.parent().active_company_id
                user_id = self.parent().current_user["id"]
                new_vend = VendorService.create_vendor(comp_id, text, phone, "", user_id)
                
                self.vendor_cb.blockSignals(True)
                display_name = f"{new_vend['name']} ({new_vend['phone']})" if new_vend.get('phone') else new_vend['name']
                self.vendor_cb.addItem(display_name, new_vend['id'])
                idx = self.vendor_cb.findData(new_vend["id"])
                if idx >= 0: self.vendor_cb.setCurrentIndex(idx)
                self.vendor_cb.blockSignals(False)
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.vendor_cb.lineEdit().clear()

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip()
        }

    def _validate_and_accept(self):
        name = self.name_input.text().strip()
        
        if not name:
            show_message(self, "error", "Validation Error", "Vendor Name is required.")
            return
            
            
        self.accept()


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
            QLineEdit, QTextEdit, QComboBox, QCompleter, QListView, QDoubleSpinBox, QDateEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox, QCompleter, QListView:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                outline: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px;
                border: none;
                color: {COLORS['text_primary']};
                background-color: transparent;
            }}
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        
        self.vendor_cb = QComboBox()
        self.vendor_cb.setEditable(True)
        self.vendor_cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.vendor_cb.lineEdit().setPlaceholderText("Search or enter new vendor...")

        for v in self.vendors:
            self.vendor_cb.addItem(v['name'], v['id'])
        self.vendor_cb.setCurrentIndex(-1)
            
        completer = self.vendor_cb.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        popup = completer.popup()
        from PySide6.QtWidgets import QFrame
        popup.setFrameShape(QFrame.Shape.NoFrame)
        popup.setStyleSheet(f"""
            QListView {{ outline: 0px; padding-top: 3px; padding-bottom: 0px; padding-left: 1px; padding-right: 1px; margin: 0px; background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 0px; }}
            QListView::item {{ padding: 8px; border: none; }}
            QListView::item:selected, QListView::item:hover {{ background-color: {COLORS['primary']}; color: white; border: none; }}
        """)
        
        self.vendor_cb.lineEdit().returnPressed.connect(self._on_vendor_entered)
            
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


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

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
        
        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Bill", primary=True)
        save_btn.clicked.connect(self._validate_and_accept)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        
        cancel_btn.setFixedSize(160, 38)
        save_btn.setFixedSize(160, 38)
        
        btn_layout.addWidget(cancel_btn, 0, 0)
        btn_layout.addWidget(save_btn, 0, 1)
        
        layout.addLayout(btn_layout)


    def _validate_and_accept(self):
        vendor_id = self.vendor_cb.currentData()
        amount = self.amount_input.value()
        
        if not vendor_id:
            show_message(self, "error", "Validation Error", "Please select a vendor.")
            return
            
        if amount <= 0:
            show_message(self, "error", "Validation Error", "Amount must be greater than 0.")
            return
            
        self.accept()

    def _on_vendor_entered(self):
        text = self.vendor_cb.lineEdit().text().strip()
        if not text: return
        
        idx = self.vendor_cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self.vendor_cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, "Add Vendor", f"Vendor '{text}' not found.\nDo you want to add this vendor?", "Phone Number (Optional)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                from services.vendor_service import VendorService
                comp_id = self.parent().active_company_id
                user_id = self.parent().current_user["id"]
                new_vend = VendorService.create_vendor(comp_id, text, phone, "", user_id)
                
                self.vendor_cb.blockSignals(True)
                display_name = f"{new_vend['name']} ({new_vend['phone']})" if new_vend.get('phone') else new_vend['name']
                self.vendor_cb.addItem(display_name, new_vend['id'])
                idx = self.vendor_cb.findData(new_vend["id"])
                if idx >= 0: self.vendor_cb.setCurrentIndex(idx)
                self.vendor_cb.blockSignals(False)
            except ValueError as e:
                from ui.auth.setup_window import handle_duplicate_error
                if not handle_duplicate_error(self, e):
                    show_message(self, "error", "Error", str(e))
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            self.vendor_cb.lineEdit().clear()

    def get_data(self) -> dict:
        return {
            "vendor_id": self.vendor_cb.currentData(),
            "amount": self.amount_input.value(),
            "bill_date": self.date_edit.date().toPython(),
            "description": self.description_input.toPlainText().strip()
        }
