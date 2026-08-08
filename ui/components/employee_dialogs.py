from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt
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

class EmployeeFormDialog(QDialog):
    """Dialog to Add or Edit an employee."""
    def __init__(self, parent=None, employee_data=None):
        super().__init__(parent)
        self.is_edit = bool(employee_data)
        self.employee_data = employee_data or {}
        
        self.setWindowTitle("Edit Employee" if self.is_edit else "Add New Employee")
        self.setFixedSize(460, 520)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QLineEdit, QTextEdit, QDoubleSpinBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        
        self.name_input = QLineEdit(self.employee_data.get("name", ""))
        self.name_input.setPlaceholderText("Employee Name (Required)")
        
        self.salary_input = QDoubleSpinBox()
        self.salary_input.setRange(0, 999999999)
        self.salary_input.setDecimals(2)
        self.salary_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        if self.is_edit:
            self.salary_input.setValue(self.employee_data.get("salary", 0.0))
        
        self.phone_input = QLineEdit(self.employee_data.get("phone", ""))
        self.phone_input.setPlaceholderText("Phone Number (Optional)")
        
        self.address_input = QTextEdit(self.employee_data.get("address", ""))
        self.address_input.setPlaceholderText("Address (Optional)")
        self.address_input.setFixedHeight(80)
        
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 700; background: transparent;")
        layout.addWidget(title)
        
        layout.addWidget(_label("Employee Name *"))
        layout.addWidget(self.name_input)
        
        layout.addWidget(_label("Salary *"))
        layout.addWidget(self.salary_input)
        
        layout.addWidget(_label("Phone Number"))
        layout.addWidget(self.phone_input)
        
        layout.addWidget(_label("Address"))
        layout.addWidget(self.address_input)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Employee", primary=True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "salary": self.salary_input.value(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip()
        }

class EmployeeAdvanceHistoryDialog(QDialog):
    def __init__(self, parent=None, employee_name=None, employee_id=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget
        self.setWindowTitle(f"Advance History - {employee_name}")
        self.setFixedSize(600, 450)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border_card']};
                font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS['border_card']};
                border-right: 1px solid {COLORS['border_card']};
                font-weight: 600;
                text-align: left;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Month", "Amount", "Description"])
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self._build()
        self._load_data(employee_id)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = _btn("Close", primary=True)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _load_data(self, employee_id: int):
        from services.employee_service import EmployeeService
        from PySide6.QtWidgets import QTableWidgetItem
        
        advances = EmployeeService.get_employee_advance_history(employee_id)
        self.table.setRowCount(len(advances))
        
        for i, adv in enumerate(advances):
            self.table.setItem(i, 0, QTableWidgetItem(adv['date']))
            self.table.setItem(i, 1, QTableWidgetItem(adv['month']))
            
            amount_item = QTableWidgetItem(f"{adv['amount']:,.2f}")
            if adv['is_cleared']:
                # visual indicator for cleared vs active advances
                amount_item.setText(f"{adv['amount']:,.2f} (Cleared)")
                amount_item.setForeground(Qt.GlobalColor.gray)
            
            self.table.setItem(i, 2, amount_item)
            self.table.setItem(i, 3, QTableWidgetItem(adv['description']))

class ResetAdvancesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset Monthly Advances")
        self.setFixedSize(380, 220)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
        """)
        
        from PySide6.QtWidgets import QComboBox
        self.month_combo = QComboBox()
        self._populate_months()
        
        self._build()

    def _populate_months(self):
        from datetime import datetime, date
        from dateutil.relativedelta import relativedelta
        # Show last 12 months as options
        current = date.today()
        for i in range(12):
            m_str = current.strftime("%B %Y")
            self.month_combo.addItem(m_str)
            current = current - relativedelta(months=1)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("Reset Advance History")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)
        
        desc = QLabel("Select the month to clear advances for. This will zero out the current advance balance for all employees for the selected month.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(desc)
        
        layout.addWidget(self.month_combo)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        reset_btn = _btn("Reset Advances", primary=True)
        reset_btn.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        reset_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(reset_btn)
        
        layout.addLayout(btn_layout)

    def get_selected_month(self) -> str:
        return self.month_combo.currentText()
