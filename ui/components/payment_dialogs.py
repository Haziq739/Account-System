from ui.components.custom_combobox import CustomComboBox
from PySide6.QtWidgets import (
    QStyledItemDelegate,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QDateEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox,
    QGridLayout
)
from PySide6.QtCore import Qt, QDate
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.payment_service import PaymentService
from services.customer import CustomerService
from services.invoice_service import InvoiceService

def _btn(text: str, primary: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QStyle

class ComboBoxDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Draw custom blue background on hover/select
        if option.state & QStyle.State_Selected or option.state & QStyle.State_MouseOver:
            from ui.design_system import COLORS
            painter.fillRect(option.rect, QColor(COLORS['primary']))
            
            # Force text to white
            palette = option.palette
            palette.setColor(QPalette.Text, QColor("white"))
            palette.setColor(QPalette.WindowText, QColor("white"))
            palette.setColor(QPalette.HighlightedText, QColor("white"))
            option.palette = palette
            
        super().paint(painter, option, index)


class AddPaymentDialog(QDialog):
    def __init__(self, parent, company_id: int, current_user: dict):
        super().__init__(parent)
        self.company_id = company_id
        self.current_user = current_user

        self.customers = CustomerService.get_customers(company_id=self.company_id)
        self.invoices = InvoiceService.get_invoices(company_id)

        self.setWindowTitle("Add Payment")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_app']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: 500; font-size: 13px; }}
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px; padding: 8px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
            QRadioButton {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QFrame#type_frame {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        self._build()


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

    def _build(self):
        from PySide6.QtWidgets import QRadioButton, QButtonGroup, QFrame, QScrollArea, QWidget, QListView
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # Avoid transparent backgrounds in scroll areas; they cause severe rendering lag on Windows
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {COLORS['bg_app']}; border: none; }}")
        
        container = QWidget()
        container.setStyleSheet(f"QWidget {{ background-color: {COLORS['bg_app']}; }}")
        
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 10)

        # Payment Type
        type_lbl = QLabel("Payment Type *")
        type_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 700;")
        layout.addWidget(type_lbl)

        type_frame = QFrame()
        type_frame.setObjectName("type_frame")
        type_row = QHBoxLayout(type_frame)
        type_row.setContentsMargins(12, 6, 12, 6)

        self.manual_rb = QRadioButton("\U0001f4b5  Manual Payment")
        self.invoice_rb = QRadioButton("\U0001f9fe  Payment Against Invoice")
        self.manual_rb.setChecked(True)

        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.manual_rb, 1)
        self.btn_group.addButton(self.invoice_rb, 2)
        self.manual_rb.toggled.connect(self._on_type_toggled)

        type_row.addWidget(self.manual_rb)
        type_row.addSpacing(20)
        type_row.addWidget(self.invoice_rb)
        type_row.addStretch()
        layout.addWidget(type_frame)

        # Customer
        layout.addWidget(QLabel("Customer *"))
        self.customer_cb = CustomComboBox()
        
        
        self.customer_cb.addItem("-- Select Customer --", None)
        for c in self.customers:
            self.customer_cb.addItem(c['name'], c['id'])
        self.customer_cb.currentIndexChanged.connect(self._on_customer_changed)
        
        layout.addWidget(self.customer_cb)

        # Invoice section (shown only when Payment Against Invoice is selected)
        self.inv_label = QLabel("Select Invoice *")
        self.invoice_cb = CustomComboBox()
        
        
        self.invoice_cb.addItem("-- Select an Invoice --", None)
        self.invoice_cb.currentIndexChanged.connect(self._on_invoice_changed)
        

        self.inv_summary_lbl = QLabel("")
        self.inv_summary_lbl.setStyleSheet(
            f"color: {COLORS['primary']}; font-size: 12px; font-weight: 600; padding: 4px 0;"
        )
        self.inv_summary_lbl.setWordWrap(True)
        self.inv_summary_lbl.hide()

        layout.addWidget(self.inv_label)
        layout.addWidget(self.invoice_cb)
        layout.addWidget(self.inv_summary_lbl)

        # Invoice section hidden by default (manual payment mode)
        self.inv_label.hide()
        self.invoice_cb.hide()

        # Amount
        layout.addWidget(QLabel("Amount *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount")
        layout.addWidget(self.amount_input)

        # Payment Method
        layout.addWidget(QLabel("Payment Method *"))
        self.method_cb = CustomComboBox()
        
        
        self.method_cb.addItems(["Cash", "Bank Transfer", "Cheque", "Credit"])
        
        layout.addWidget(self.method_cb)

        # Payment Date
        layout.addWidget(QLabel("Payment Date"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        layout.addWidget(self.date_input)

        # Reference
        layout.addWidget(QLabel("Reference / Cheque Number (Optional)"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. Cheque No. 12345")
        layout.addWidget(self.ref_input)

        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QLineEdit()
        layout.addWidget(self.notes_input)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 10, 20, 20)
        btn_layout.setSpacing(15)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Payment", primary=True)
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self._save)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def _on_type_toggled(self, manual_checked: bool):
        """Show/hide invoice section based on payment type selection."""
        self.inv_label.setVisible(not manual_checked)
        self.invoice_cb.setVisible(not manual_checked)
        self.inv_summary_lbl.setVisible(False)
        if manual_checked:
            self.amount_input.clear()

    def _on_customer_changed(self):
        cust_id = self.customer_cb.currentData()
        self.invoice_cb.clear()
        self.invoice_cb.addItem("-- Select an Invoice --", None)
        self.inv_summary_lbl.hide()
        if not cust_id:
            return
        for inv in self.invoices:
            if inv.get("customer_id") == cust_id and inv.get("status") != "paid":
                remaining = inv['net_amount'] - inv['paid_amount']
                self.invoice_cb.addItem(
                    f"{inv['invoice_number']} — Total: {inv['net_amount']:.2f}  |  Remaining: {remaining:.2f}",
                    inv["id"]
                )

    def _on_invoice_changed(self):
        inv_id = self.invoice_cb.currentData()
        if not inv_id:
            self.inv_summary_lbl.hide()
            self.amount_input.clear()
            return
        for inv in self.invoices:
            if inv["id"] == inv_id:
                remaining = inv['net_amount'] - inv['paid_amount']
                self.inv_summary_lbl.setText(
                    f"Invoice Total: {inv['net_amount']:.2f}   |   "
                    f"Already Paid: {inv['paid_amount']:.2f}   |   "
                    f"Remaining: {remaining:.2f}"
                )
                self.inv_summary_lbl.show()
                self.amount_input.setText(f"{remaining:.2f}")
                break

    def _save(self):
        is_invoice_payment = self.invoice_rb.isChecked()

        cust_id = self.customer_cb.currentData()
        if not cust_id:
            show_message(self, "error", "Validation Error", "Please select a Customer.")
            return

        inv_id = None
        if is_invoice_payment:
            inv_id = self.invoice_cb.currentData()
            if not inv_id:
                show_message(self, "error", "Validation Error", "Please select an Invoice.")
                return

        try:
            amt = float(self.amount_input.text())
            if amt <= 0:
                raise ValueError
        except ValueError:
            show_message(self, "error", "Validation Error", "Please enter a valid amount greater than 0.")
            return

        # Validate that payment amount does not exceed the remaining invoice amount
        if is_invoice_payment and inv_id:
            remaining = 0
            for inv in self.invoices:
                if inv["id"] == inv_id:
                    remaining = inv['net_amount'] - inv['paid_amount']
                    break
            
            if amt > remaining:
                show_message(
                    self, 
                    "error", 
                    "Invalid Amount", 
                    f"Payment amount ({amt:,.2f}) cannot be greater than the invoice outstanding amount ({remaining:,.2f})."
                )
                return

        try:
            pay_result = PaymentService.create_payment(
                company_id=self.company_id,
                customer_id=cust_id,
                amount=amt,
                payment_method=self.method_cb.currentText(),
                payment_date=self.date_input.date().toPython(),
                reference_number=self.ref_input.text(),
                notes=self.notes_input.text(),
                invoice_id=inv_id,
                user_id=self.current_user["id"],
                is_advance=(not is_invoice_payment)
            )
            dlg = PaymentSuccessDialog(self, pay_result["id"])
            dlg.exec()
            self.accept()
        except Exception as e:
            show_message(self, "error", "Error", f"Failed to save payment: {e}")


class RecordInvoicePaymentDialog(QDialog):
    def __init__(self, parent, company_id: int, current_user: dict, invoice: dict):
        super().__init__(parent)
        self.company_id = company_id
        self.current_user = current_user
        self.invoice = invoice
        
        self.setWindowTitle(f"Record Payment - {self.invoice['invoice_number']}")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_app']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: 500; font-size: 13px; }}
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px; padding: 8px;
                color: {COLORS['text_primary']};
            }}
            .summary_val {{ font-weight: bold; color: {COLORS['primary']}; font-size: 14px; }}
        """)
        self._build()


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        rem = self.invoice['net_amount'] - self.invoice['paid_amount']
        
        # Summary
        layout.addWidget(QLabel(f"Customer: {self.invoice['customer_name']}"))
        layout.addWidget(QLabel(f"Total Amount: {self.invoice['net_amount']:.2f}"))
        layout.addWidget(QLabel(f"Already Paid: {self.invoice['paid_amount']:.2f}"))
        lbl = QLabel(f"Remaining Amount: {rem:.2f}")
        lbl.setProperty("class", "summary_val")
        layout.addWidget(lbl)
        
        layout.addWidget(QLabel("Amount Received *"))
        self.amount_input = QLineEdit(f"{rem:.2f}")
        layout.addWidget(self.amount_input)
        
        layout.addWidget(QLabel("Payment Method *"))
        self.method_cb = CustomComboBox()
        self.method_cb.addItems(["Cash", "Bank Transfer", "Cheque", "Credit"])
        layout.addWidget(self.method_cb)
        
        layout.addWidget(QLabel("Payment Date"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        layout.addWidget(self.date_input)
        
        layout.addWidget(QLabel("Reference / Cheque Number (Optional)"))
        self.ref_input = QLineEdit()
        layout.addWidget(self.ref_input)
        
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QLineEdit()
        layout.addWidget(self.notes_input)
        
        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = _btn("Save Payment", primary=True)
        save_btn.clicked.connect(self._save)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        
        cancel_btn.setFixedSize(160, 38)
        save_btn.setFixedSize(160, 38)
        
        btn_layout.addWidget(cancel_btn, 0, 0)
        btn_layout.addWidget(save_btn, 0, 1)
        layout.addLayout(btn_layout)

    def _save(self):
        try:
            amt = float(self.amount_input.text())
        except ValueError:
            show_message(self, "error", "Error", "Invalid amount.")
            return
            
        try:
            pay_result = PaymentService.create_payment(
                company_id=self.company_id,
                customer_id=self.invoice["customer_id"],
                amount=amt,
                payment_method=self.method_cb.currentText(),
                payment_date=self.date_input.date().toPython(),
                reference_number=self.ref_input.text(),
                notes=self.notes_input.text(),
                invoice_id=self.invoice["id"],
                user_id=self.current_user["id"]
            )
            
            dlg = PaymentSuccessDialog(self, pay_result["id"])
            dlg.exec()
                
            self.accept()
        except Exception as e:
            show_message(self, "error", "Error", f"Failed to save payment: {e}")

from PySide6.QtCore import QThread, Signal

class ReceiptPDFWorker(QThread):
    finished = Signal(str, str, str)
    error = Signal(str)
    
    def __init__(self, pay_id: int, action: str, save_path: str = "", hist_total: float = None, hist_rem: float = None):
        super().__init__()
        self.pay_id = pay_id
        self.action = action
        self.save_path = save_path
        self.hist_total = hist_total
        self.hist_rem = hist_rem
        
    def run(self):
        try:
            from services.pdf_generator import PDFGenerator
            path = PDFGenerator.generate_receipt_pdf(self.pay_id, self.hist_total, self.hist_rem)
            self.finished.emit(path, self.action, self.save_path)
        except Exception as e:
            self.error.emit(str(e))

class PaymentSuccessDialog(QDialog):
    def __init__(self, parent, pay_id: int):
        super().__init__(parent)
        self.pay_id = pay_id
        
        self.setWindowTitle("Payment Successful")
        self.setMinimumWidth(350)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_app']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-size: 14px; margin-bottom: 10px; }}
        """)
        self._build()


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        msg_lbl = QLabel("Payment recorded successfully.")
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_lbl)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        close_btn = _btn("Close")
        close_btn.clicked.connect(self.accept)
        
        self.download_btn = _btn("Download Receipt")
        self.download_btn.clicked.connect(self._on_download)
        
        self.print_btn = _btn("Print Receipt", primary=True)
        self.print_btn.clicked.connect(self._on_print)
        
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(self.download_btn)
        btn_layout.addWidget(self.print_btn)
        
        layout.addLayout(btn_layout)

    def _on_download(self):
        # Open file dialog immediately for zero perceived latency
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt", 
            f"Receipt_{self.pay_id}.pdf", 
            "PDF Files (*.pdf)"
        )
        if not save_path:
            return
            
        self.download_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.download_btn.setText("Generating...")
        
        self.worker = ReceiptPDFWorker(self.pay_id, 'download', save_path)
        self.worker.finished.connect(self._on_pdf_ready)
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()

    def _on_print(self):
        self.download_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.print_btn.setText("Generating...")
        
        self.worker = ReceiptPDFWorker(self.pay_id, 'print')
        self.worker.finished.connect(self._on_pdf_ready)
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()
        
    def _on_pdf_ready(self, path: str, action: str, save_path: str):
        self.download_btn.setText("Download Receipt")
        self.print_btn.setText("Print Receipt")
        self.download_btn.setEnabled(True)
        self.print_btn.setEnabled(True)
        
        import shutil, os, platform, subprocess
        if action == 'download':
            if save_path:
                shutil.copy2(path, save_path)
                show_message(self, "success", "Success", "Receipt downloaded successfully.")
        elif action == 'print':
            try:
                if platform.system() == 'Windows':
                    os.startfile(path, "print")
                else:
                    subprocess.call(('lpr', path))
            except Exception as e:
                show_message(self, "error", "Print Error", str(e))
                
    def _on_pdf_error(self, err: str):
        self.download_btn.setText("Download Receipt")
        self.print_btn.setText("Print Receipt")
        self.download_btn.setEnabled(True)
        self.print_btn.setEnabled(True)
        show_message(self, "error", "Error", f"Failed to generate receipt: {err}")

class PaymentHistoryDialog(QDialog):
    def __init__(self, parent, invoice: dict):
        super().__init__(parent)
        self.invoice = invoice
        
        self.setWindowTitle(f"Payment History - {self.invoice['invoice_number']}")
        self.setMinimumSize(800, 400)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_app']}; }}
            QLabel {{ color: {COLORS['text_primary']}; }}
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
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
            QTableWidget::item:selected {{
                background-color: #E2E8F0;
                color: {COLORS['text_primary']};
            }}
        """)
        self._build()
        self._load_data()


    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        info = QLabel(f"<b>Invoice Total:</b> {self.invoice['net_amount']:.2f}")
        layout.addWidget(info)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Receipt Number", "Payment Date", "Payment Type", "Amount", 
            "Total Paid", "Remaining", "Status"
        ])
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.down_btn = _btn("Download Receipt")
        self.down_btn.setEnabled(False)
        self.down_btn.clicked.connect(self._on_download)
        
        self.print_btn = _btn("Print Receipt", primary=True)
        self.print_btn.setEnabled(False)
        self.print_btn.clicked.connect(self._on_print)
        
        close_btn = _btn("Close")
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.down_btn)
        btn_layout.addWidget(self.print_btn)
        
        layout.addLayout(btn_layout)

    def _load_data(self):
        payments = PaymentService.get_payments_by_invoice(self.invoice["id"])
        
        self.table.setRowCount(0)
        total_paid = 0.0
        invoice_total = self.invoice['net_amount']
        
        for p in payments:
            amt = p['amount']
            total_paid += amt
            remaining = invoice_total - total_paid
            
            if total_paid >= invoice_total:
                status = "PAID"
            elif total_paid > 0:
                status = "PARTIAL"
            else:
                status = "UNPAID"
                
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            r_item = QTableWidgetItem(p["receipt_number"])
            r_item.setData(Qt.ItemDataRole.UserRole, p["id"])
            
            self.table.setItem(row, 0, r_item)
            self.table.setItem(row, 1, QTableWidgetItem(p["payment_date"].strftime("%Y-%m-%d")))
            
            type_display = "Advance Payment" if p.get("is_advance") else "Payment"
            self.table.setItem(row, 2, QTableWidgetItem(type_display))
            
            self.table.setItem(row, 3, QTableWidgetItem(f"{amt:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{total_paid:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{remaining:.2f}"))
            
            s_item = QTableWidgetItem(status)
            if status == "PAID": s_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "PARTIAL": s_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(row, 6, s_item)

    def _on_selection_changed(self):
        has_sel = len(self.table.selectedItems()) > 0
        self.down_btn.setEnabled(has_sel)
        self.print_btn.setEnabled(has_sel)
        
    def _get_selected_pay_data(self):
        row = self.table.currentRow()
        if row < 0: return None, None, None
        pay_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        total_paid = float(self.table.item(row, 4).text())
        remaining = float(self.table.item(row, 5).text())
        return pay_id, total_paid, remaining
        
    def _on_download(self):
        pay_id, hist_total, hist_rem = self._get_selected_pay_data()
        if not pay_id: return
        
        # Open file dialog immediately for zero perceived latency
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt", 
            f"Receipt_{pay_id}.pdf", 
            "PDF Files (*.pdf)"
        )
        if not save_path:
            return
            
        self.down_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.down_btn.setText("Generating...")
        
        self.worker = ReceiptPDFWorker(pay_id, 'download', save_path, hist_total, hist_rem)
        self.worker.finished.connect(self._on_pdf_ready)
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()

    def _on_print(self):
        pay_id, hist_total, hist_rem = self._get_selected_pay_data()
        if not pay_id: return
        
        self.down_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.print_btn.setText("Generating...")
        
        self.worker = ReceiptPDFWorker(pay_id, 'print', "", hist_total, hist_rem)
        self.worker.finished.connect(self._on_pdf_ready)
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()
        
    def _on_pdf_ready(self, path: str, action: str, save_path: str):
        self.down_btn.setText("Download Receipt")
        self.print_btn.setText("Print Receipt")
        self._on_selection_changed()
        
        import shutil, os, platform, subprocess
        if action == 'download':
            if save_path:
                shutil.copy2(path, save_path)
                show_message(self, "success", "Success", "Receipt downloaded successfully.")
        elif action == 'print':
            try:
                if platform.system() == 'Windows':
                    os.startfile(path, "print")
                else:
                    subprocess.call(('lpr', path))
            except Exception as e:
                show_message(self, "error", "Print Error", str(e))
                
    def _on_pdf_error(self, err: str):
        self.down_btn.setText("Download Receipt")
        self.print_btn.setText("Print Receipt")
        self._on_selection_changed()
        show_message(self, "error", "Error", f"Failed to generate receipt: {err}")
