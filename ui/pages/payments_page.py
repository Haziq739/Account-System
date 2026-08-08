from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QLineEdit
)
from PySide6.QtCore import Qt
from ui.design_system import COLORS
from services.payment_service import PaymentService
from ui.components.payment_dialogs import AddPaymentDialog
from ui.auth.setup_window import show_message

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class PaymentsPage(QWidget):
    def __init__(self, company_id: int, current_user: dict):
        super().__init__()
        self.company_id = company_id
        self.current_user = current_user
        self._build()
        self.load_data()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(20)
        root.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QHBoxLayout()
        title = QLabel("Payments")
        title.setStyleSheet(f"font-size: 24px; font-weight: 600; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()

        add_btn = _btn("Receive Payment", primary=True, icon="➕")
        add_btn.clicked.connect(self._add_payment)
        header.addWidget(add_btn)
        root.addLayout(header)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search payments by receipt, customer, or invoice...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px; padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(self.search_input)
        root.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Receipt #", "Customer", "Date", "Invoice", "Method", "Amount", "Actions"
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
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 60)
        
        root.addWidget(self.table)

    def load_data(self):
        self.payments = PaymentService.get_payments(self.company_id)
        self._populate_table(self.payments)

    def set_company(self, company_id: int):
        self.company_id = company_id
        self.load_data()

    def _populate_table(self, data):
        self.table.setRowCount(0)
        for p in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(p["receipt_number"]))
            self.table.setItem(row, 1, QTableWidgetItem(p["customer_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(p["payment_date"].strftime("%Y-%m-%d")))
            self.table.setItem(row, 3, QTableWidgetItem(p["invoice_number"]))
            self.table.setItem(row, 4, QTableWidgetItem(p["payment_method"]))
            
            amt_item = QTableWidgetItem(f"{p['amount']:.2f}")
            amt_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 5, amt_item)
            
            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(30, 30)
            del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, pid=p["id"]: self._delete_payment(pid))
            
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            l.addWidget(del_btn)
            self.table.setCellWidget(row, 6, w)

    def _filter_table(self, text):
        text = text.lower()
        filtered = []
        for p in self.payments:
            if (text in p["receipt_number"].lower() or 
                text in p["customer_name"].lower() or 
                text in p["invoice_number"].lower()):
                filtered.append(p)
        self._populate_table(filtered)

    def _add_payment(self):
        dlg = AddPaymentDialog(self, self.company_id, self.current_user)
        if dlg.exec():
            self.load_data()

    def _delete_payment(self, payment_id: int):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Confirm Reversal",
            "Are you sure you want to delete and reverse this payment? This will affect the ledger.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            PaymentService.soft_delete_payment(payment_id, self.current_user["id"])
            show_message(self, "success", "Success", "Payment reversed.")
            self.load_data()
