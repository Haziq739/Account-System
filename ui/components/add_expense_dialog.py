from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QDateEdit, QTextEdit, QDoubleSpinBox, QComboBox,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator

from ui.design_system import COLORS
from services.daybook_service import DayBookService
from services.customer import CustomerService
from services.vendor_service import VendorService
from services.employee_service import EmployeeService
from ui.auth.setup_window import show_message

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

class AddExpenseDialog(QDialog):
    def __init__(self, parent, company_id: int, current_user: dict):
        super().__init__(parent)
        self.company_id = company_id
        self.current_user = current_user
        
        self.customers = CustomerService.get_customers()
        self.vendors = VendorService.get_vendors(company_id=self.company_id)
        self.employees = EmployeeService.get_employees(company_id=self.company_id)
        
        self.setWindowTitle("Add Expense")
        self.setMinimumSize(450, 500)
        self.resize(450, 650)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-size: 13px; font-weight: bold; }}
            QLineEdit, QDateEdit, QTextEdit, QDoubleSpinBox, QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px; padding: 8px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border: 1px solid {COLORS['primary']}; }}
        """)
        self._build()

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)
        
        # Title
        title_lbl = QLabel("Record Daily Expense")
        title_lbl.setStyleSheet(f"font-size: 18px; color: {COLORS['text_primary']};")
        layout.addWidget(title_lbl)
        
        # Expense Title
        layout.addWidget(QLabel("Expense Title *"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Petrol, Office Supplies, Tea...")
        layout.addWidget(self.title_input)
        
        # Amount
        layout.addWidget(QLabel("Amount *"))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        layout.addWidget(self.amount_input)
        
        # Date
        layout.addWidget(QLabel("Date *"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)
        
        # Customer
        layout.addWidget(QLabel("Customer (Optional)"))
        self.customer_cb = QComboBox()
        self.customer_cb.addItem("-- None --", None)
        for c in self.customers:
            self.customer_cb.addItem(c['name'], c['id'])
        layout.addWidget(self.customer_cb)
        
        # Vendor
        layout.addWidget(QLabel("Vendor (Optional)"))
        self.vendor_cb = QComboBox()
        self.vendor_cb.addItem("-- None --", None)
        for v in self.vendors:
            self.vendor_cb.addItem(v['name'], v['id'])
        layout.addWidget(self.vendor_cb)

        # Employee
        layout.addWidget(QLabel("Employee (Optional)"))
        self.employee_cb = QComboBox()
        self.employee_cb.addItem("-- None --", None)
        for e in self.employees:
            self.employee_cb.addItem(e['name'], e['id'])
        layout.addWidget(self.employee_cb)
        
        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any additional details...")
        self.notes_input.setFixedHeight(80)
        layout.addWidget(self.notes_input)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Buttons
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(24, 8, 24, 24)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Expense", primary=True)
        save_btn.clicked.connect(self._save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addWidget(btn_widget)

    def _save(self):
        title = self.title_input.text().strip()
        amount = self.amount_input.value()
        expense_date = self.date_edit.date().toPython()
        notes = self.notes_input.toPlainText().strip()
        customer_id = self.customer_cb.currentData()
        vendor_id = self.vendor_cb.currentData()
        employee_id = self.employee_cb.currentData()
        
        if not title:
            show_message(self, "error", "Validation Error", "Please enter an Expense Title.")
            return
            
        if amount <= 0:
            show_message(self, "error", "Validation Error", "Expense amount must be greater than zero.")
            return
            
        try:
            DayBookService.add_expense(
                company_id=self.company_id,
                title=title,
                amount=amount,
                expense_date=expense_date,
                notes=notes,
                user_id=self.current_user["id"],
                customer_id=customer_id,
                vendor_id=vendor_id,
                employee_id=employee_id
            )
            show_message(self, "success", "Success", "Expense added successfully!")
            self.accept()
        except Exception as e:
            show_message(self, "error", "Database Error", f"Failed to save expense: {e}")
