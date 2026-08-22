import os, platform, subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QDateEdit, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QThread, Signal
from ui.design_system import COLORS
from services.daybook_service import DayBookService
from ui.components.add_expense_dialog import AddExpenseDialog
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
        QPushButton:disabled {{ opacity: 0.5; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class DayBookPDFWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, company_id, target_date, data_dict):
        super().__init__()
        self.company_id = company_id
        self.target_date = target_date
        self.data_dict = data_dict
        
    def run(self):
        try:
            from services.pdf_generator import PDFGenerator
            filepath = PDFGenerator.generate_daybook_pdf(
                self.company_id, self.target_date, self.data_dict
            )
            self.finished.emit(filepath)
        except Exception as e:
            self.error.emit(str(e))

class DayBookPage(QWidget):
    def __init__(self, company_id: int, current_user: dict):
        super().__init__()
        self.active_company_id = company_id
        self.current_user = current_user
        self.data = None
        self._build()
        self.refresh_data()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(20)

        # Header Area
        header = QHBoxLayout()
        title_lbl = QLabel("Daily Cash Book")
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: bold;")
        header.addWidget(title_lbl)
        
        header.addStretch()
        
        header.addWidget(QLabel("Date: ", styleSheet=f"color: {COLORS['text_secondary']};"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet(f"""
            QDateEdit {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; 
            border-radius: 6px; padding: 6px; color: {COLORS['text_primary']}; font-weight: bold; font-size: 14px;}}
        """)
        self.date_edit.dateChanged.connect(self.refresh_data)
        header.addWidget(self.date_edit)
        
        root.addLayout(header)
        
        # Summary Cards Area
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(20)
        
        self.lbl_opening_balance = self._build_card(summary_layout, "Opening Balance", "0.00", COLORS['text_secondary'])
        self.lbl_income = self._build_card(summary_layout, "Total Income", "0.00", "#10B981") # Green
        self.lbl_expense = self._build_card(summary_layout, "Total Expenses", "0.00", "#EF4444") # Red
        self.lbl_balance = self._build_card(summary_layout, "Closing Balance", "0.00", COLORS['primary'])
        
        root.addLayout(summary_layout)
        
        # Warning label
        self.warning_lbl = QLabel("⚠️ Warning: Today's expenses exceed today's income.")
        self.warning_lbl.setStyleSheet("color: #DC2626; font-weight: bold; background-color: #FEF2F2; padding: 8px; border-radius: 4px; border: 1px solid #F87171;")
        self.warning_lbl.setVisible(False)
        root.addWidget(self.warning_lbl)
        
        # Actions Area
        actions_layout = QHBoxLayout()
        
        self.btn_add_exp = _btn("Add Expense", primary=True)
        self.btn_add_exp.clicked.connect(self._on_add_expense)
        actions_layout.addWidget(self.btn_add_exp)
        
        actions_layout.addStretch()
        
        self.btn_pdf = _btn("Download Day Book PDF")
        self.btn_pdf.clicked.connect(self._on_download_pdf)
        actions_layout.addWidget(self.btn_pdf)
        
        root.addLayout(actions_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Time", "Type", "Description", "Customer/Vendor/Employee", "Ref No.", "Income", "Expense", "Balance"
        ])
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_input']};
                padding: 12px; border: none;
                border-bottom: 1px solid {COLORS['border_card']};
                font-weight: 600; color: {COLORS['text_secondary']};
            }}
            QTableWidget::item {{ color: {COLORS['text_primary']}; }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setCursor(Qt.CursorShape.PointingHandCursor)
        self.table.cellClicked.connect(self._on_row_clicked)
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        root.addWidget(self.table)

    def _build_card(self, parent_layout, title, value, color) -> QLabel:
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
            }}
        """)
        clayout = QVBoxLayout(card)
        clayout.setContentsMargins(20, 20, 20, 20)
        
        t = QLabel(title)
        t.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        clayout.addWidget(t)
        
        val = QLabel(value)
        val.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        clayout.addWidget(val)
        
        parent_layout.addWidget(card)
        return val

    def set_company(self, company_id: int):
        self.active_company_id = company_id
        self.refresh_data()

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        target_date = self.date_edit.date().toPython()
        self.data = DayBookService.get_daybook_transactions(self.active_company_id, target_date)
        
        self.lbl_opening_balance.setText(f"{self.data.get('opening_balance', 0.0):,.2f}")
        self.lbl_income.setText(f"{self.data['total_income']:,.2f}")
        self.lbl_expense.setText(f"{self.data['total_expense']:,.2f}")
        self.lbl_balance.setText(f"{self.data['balance']:,.2f}")
        
        if self.data['balance'] < 0:
            self.warning_lbl.setVisible(True)
        else:
            self.warning_lbl.setVisible(False)
            
        self._populate_table()
        
    def _populate_table(self):
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        if not self.data: 
            self.table.setUpdatesEnabled(True)
            self.table.setSortingEnabled(True)
            return
        
        from datetime import timezone
        for t in self.data['transactions']:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            time_str = ""
            if t['timestamp']:
                # Convert from UTC to local system timezone (e.g. PKT)
                dt = t['timestamp']
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                local_dt = dt.astimezone()
                time_str = local_dt.strftime("%I:%M %p")
                
            time_item = QTableWidgetItem(time_str)
            time_item.setData(Qt.ItemDataRole.UserRole, t['id'])
            self.table.setItem(row, 0, time_item)
            
            type_item = QTableWidgetItem(t['type'])
            if "Expense" in t['type']:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            elif "Payment" in t['type']:
                type_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 1, type_item)
            
            self.table.setItem(row, 2, QTableWidgetItem(t['description']))
            self.table.setItem(row, 3, QTableWidgetItem(t['customer_or_title']))
            self.table.setItem(row, 4, QTableWidgetItem(t['invoice_number']))
            
            inc_val = f"{t['income']:,.2f}" if t['income'] > 0 else "-"
            exp_val = f"{t['expense']:,.2f}" if t['expense'] > 0 else "-"
            
            inc_item = QTableWidgetItem(inc_val)
            inc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, inc_item)
            
            exp_item = QTableWidgetItem(exp_val)
            exp_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 6, exp_item)
            
            bal_item = QTableWidgetItem(f"{t['running_balance']:,.2f}")
            bal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 7, bal_item)

        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)

    def _on_row_clicked(self, row, col):
        t_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not t_id or not t_id.startswith("exp_"):
            return
            
        expense_id = int(t_id.split("_")[1])
        
        from ui.pages.employees_page import RowActionDialog
        dlg = RowActionDialog(self, f"Expense")
        # Hide delete and history buttons since we only want edit for now
        dlg.btn_del.setVisible(False)
        dlg.btn_history.setVisible(False)
        
        res = dlg.exec()
        if res == 2: # Edit
            exp_data = DayBookService.get_expense(expense_id)
            if not exp_data:
                show_message(self, "error", "Error", "Expense not found.")
                return
                
            from ui.components.add_expense_dialog import AddExpenseDialog
            edit_dlg = AddExpenseDialog(self, self.active_company_id, self.current_user, expense_data=exp_data)
            if edit_dlg.exec():
                self.refresh_data()

    def _on_add_expense(self):
        if not self.active_company_id:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        from ui.components.add_expense_dialog import AddExpenseDialog
        dlg = AddExpenseDialog(self, self.active_company_id, self.current_user)
        if dlg.exec():
            # Only refresh if the date of the expense matches the current view date
            # But just calling refresh_data is safe and robust
            if dlg.date_edit.date() == self.date_edit.date():
                self.refresh_data()

    def _on_download_pdf(self):
        if not self.active_company_id or not self.data:
            return
            
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.setText("Generating PDF...")
        
        target_date = self.date_edit.date().toPython()
        
        self.pdf_worker = DayBookPDFWorker(self.active_company_id, target_date, self.data)
        self.pdf_worker.finished.connect(self._on_pdf_ready)
        self.pdf_worker.error.connect(self._on_pdf_error)
        self.pdf_worker.start()
        
    def _on_pdf_ready(self, filepath: str):
        self.btn_pdf.setEnabled(True)
        self.btn_pdf.setText("Download Day Book PDF")
        
        show_message(self, "success", "PDF Downloaded", f"Day Book PDF saved successfully at:\n{filepath}")
            
    def _on_pdf_error(self, err: str):
        self.btn_pdf.setEnabled(True)
        self.btn_pdf.setText("Download Day Book PDF")
        show_message(self, "error", "PDF Generation Failed", str(err))
