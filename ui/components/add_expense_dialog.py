from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QDateEdit, QTextEdit, QDoubleSpinBox, QComboBox, QCompleter, QListView, QCompleter,
    QScrollArea, QWidget, QGridLayout
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator

from ui.design_system import COLORS
from services.daybook_service import DayBookService
from services.customer import CustomerService
from services.vendor_service import VendorService
from services.employee_service import EmployeeService
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

class AddExpenseDialog(QDialog):
    def __init__(self, parent, company_id: int, current_user: dict, expense_data: dict = None):
        super().__init__(parent)
        self.company_id = company_id
        self.current_user = current_user
        self.expense_data = expense_data
        
        self.customers = CustomerService.get_customers(company_id=self.company_id)
        self.vendors = VendorService.get_vendors(company_id=self.company_id)
        self.employees = EmployeeService.get_employees(company_id=self.company_id)
        
        title = "Edit Expense" if expense_data else "Add Expense"
        self.setWindowTitle(title)
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
        self._build()


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

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
        lbl = "Edit Daily Expense" if self.expense_data else "Record Daily Expense"
        title_lbl = QLabel(lbl)
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
        
        def setup_searchable_cb(cb, items, placeholder, callback):
            cb.setEditable(True)
            cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            cb.lineEdit().setPlaceholderText(placeholder)
            for item in items:
                display_name = f"{item['name']} ({item['phone']})" if item.get('phone') else item['name']
                cb.addItem(display_name, item['id'])
            cb.setCurrentIndex(-1)
            
            completer = cb.completer()
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
            cb.lineEdit().returnPressed.connect(callback)

        # Customer
        layout.addWidget(QLabel("Customer (Optional)"))
        self.customer_cb = QComboBox()
        setup_searchable_cb(self.customer_cb, self.customers, "Search or enter new customer...", self._on_customer_entered)
        layout.addWidget(self.customer_cb)
        
        # Vendor
        layout.addWidget(QLabel("Vendor (Optional)"))
        self.vendor_cb = QComboBox()
        setup_searchable_cb(self.vendor_cb, self.vendors, "Search or enter new vendor...", self._on_vendor_entered)
        layout.addWidget(self.vendor_cb)

        # Employee
        layout.addWidget(QLabel("Employee (Optional)"))
        self.employee_cb = QComboBox()
        setup_searchable_cb(self.employee_cb, self.employees, "Search or enter new employee...", self._on_employee_entered)
        layout.addWidget(self.employee_cb)
        
        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any additional details...")
        self.notes_input.setFixedHeight(80)
        layout.addWidget(self.notes_input)
        
        if self.expense_data:
            self.title_input.setText(self.expense_data.get("title", ""))
            self.amount_input.setValue(self.expense_data.get("amount", 0.0))
            if self.expense_data.get("expense_date"):
                self.date_edit.setDate(self.expense_data["expense_date"])
            self.notes_input.setText(self.expense_data.get("notes", ""))
            
            c_id = self.expense_data.get("customer_id")
            if c_id:
                idx = self.customer_cb.findData(c_id)
                if idx >= 0: self.customer_cb.setCurrentIndex(idx)
                
            v_id = self.expense_data.get("vendor_id")
            if v_id:
                idx = self.vendor_cb.findData(v_id)
                if idx >= 0: self.vendor_cb.setCurrentIndex(idx)
                
            e_id = self.expense_data.get("employee_id")
            if e_id:
                idx = self.employee_cb.findData(e_id)
                if idx >= 0: self.employee_cb.setCurrentIndex(idx)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Buttons
        btn_widget = QWidget()
        btn_layout = QGridLayout(btn_widget)
        btn_layout.setContentsMargins(24, 8, 24, 24)
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_txt = "Save Changes" if self.expense_data else "Save Expense"
        save_btn = _btn(btn_txt, primary=True)
        save_btn.clicked.connect(self._save)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        
        cancel_btn.setFixedSize(160, 38)
        save_btn.setFixedSize(160, 38)
        
        btn_layout.addWidget(cancel_btn, 0, 0, Qt.AlignmentFlag.AlignRight)
        btn_layout.addWidget(save_btn, 0, 1, Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(btn_widget)


    def _on_customer_entered(self):
        self._handle_dynamic_add(self.customer_cb, "Customer", "regular", "CustomerService", "create_customer")
        
    def _on_vendor_entered(self):
        self._handle_dynamic_add(self.vendor_cb, "Vendor", None, "VendorService", "create_vendor")
        
    def _on_employee_entered(self):
        self._handle_dynamic_add(self.employee_cb, "Employee", None, "EmployeeService", "create_employee")
        
    def _handle_dynamic_add(self, cb, type_name, context, service_name, method_name):
        text = cb.lineEdit().text().strip()
        if not text: return
        
        idx = cb.findText(text, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            cb.setCurrentIndex(idx)
            return
            
        dlg = DynamicAddDialog(self, f"Add {type_name}", f"{type_name} '{text}' not found.\nDo you want to add this {type_name.lower()}?", "Phone Number (Optional)")
        if dlg.exec():
            phone, _ = dlg.get_inputs()
            try:
                import importlib
                module_name = f"services.{type_name.lower()}"
                if type_name == "Vendor": module_name = "services.vendor_service"
                if type_name == "Employee": module_name = "services.employee_service"
                
                module = importlib.import_module(module_name)
                service_class = getattr(module, service_name)
                method = getattr(service_class, method_name)
                
                if type_name == "Employee":
                    new_item = method(company_id=self.company_id, name=text, salary=0.0, phone=phone, address="", user_id=self.current_user["id"])
                elif context:
                    new_item = method(self.company_id, text, phone, "", self.current_user["id"], context)
                else:
                    new_item = method(self.company_id, text, phone, "", self.current_user["id"])
                
                cb.blockSignals(True)
                display_name = f"{new_item['name']} ({new_item['phone']})" if new_item.get('phone') else new_item['name']
                cb.addItem(display_name, new_item['id'])
                idx = cb.findData(new_item["id"])
                if idx >= 0: cb.setCurrentIndex(idx)
                cb.blockSignals(False)
            except ValueError as e:
                from ui.auth.setup_window import handle_duplicate_error
                if not handle_duplicate_error(self, e):
                    show_message(self, "error", "Error", str(e))
            except Exception as e:
                show_message(self, "error", "Error", str(e))
        else:
            cb.lineEdit().clear()

    def _save(self):
        title = self.title_input.text().strip()
        amount = self.amount_input.value()
        expense_date = self.date_edit.date().toPython()
        notes = self.notes_input.toPlainText().strip()
        def _get_id_or_error(cb, entity_name):
            text = cb.lineEdit().text().strip()
            if not text:
                return None
            idx = cb.findText(text, Qt.MatchFlag.MatchStartsWith)
            if idx >= 0:
                return cb.itemData(idx)
            return -1 # Indicates typed text doesn't match any existing entity

        customer_id = _get_id_or_error(self.customer_cb, "Customer")
        if customer_id == -1:
            show_message(self, "error", "Validation Error", "Please press 'Enter' to add the new Customer, or clear the box.")
            return
            
        vendor_id = _get_id_or_error(self.vendor_cb, "Vendor")
        if vendor_id == -1:
            show_message(self, "error", "Validation Error", "Please press 'Enter' to add the new Vendor, or clear the box.")
            return
            
        employee_id = _get_id_or_error(self.employee_cb, "Employee")
        if employee_id == -1:
            show_message(self, "error", "Validation Error", "Please press 'Enter' to add the new Employee, or clear the box.")
            return
        
        if not title:
            show_message(self, "error", "Validation Error", "Please enter an Expense Title.")
            return
            
        if amount <= 0:
            show_message(self, "error", "Validation Error", "Expense amount must be greater than zero.")
            return
            
            
        try:
            if self.expense_data:
                DayBookService.update_expense(
                    expense_id=self.expense_data["id"],
                    title=title,
                    amount=amount,
                    expense_date=expense_date,
                    notes=notes,
                    user_id=self.current_user["id"],
                    customer_id=customer_id,
                    vendor_id=vendor_id,
                    employee_id=employee_id
                )
                show_message(self, "success", "Success", "Expense updated successfully!")
            else:
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
