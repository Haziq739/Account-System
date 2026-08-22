from PySide6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
import os, platform, subprocess
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.invoice_service import InvoiceService
from services.pdf_generator import PDFGenerator
from ui.components.create_invoice_dialog import CreateInvoiceDialog


class RowActionDialog(QDialog):
    def __init__(self, parent=None, title_text="Action"):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            QDialog {{ 
                background-color: {COLORS['bg_card']}; 
                border-radius: 8px; 
                border: 2px solid {COLORS['primary']}; 
            }}
            QPushButton, QPushButton#outline_btn, QPushButton#primary_btn {{
                text-align: center;
                padding: 12px 16px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QPushButton:hover, QPushButton#outline_btn:hover, QPushButton#primary_btn:hover {{
                background-color: #EFF6FF;
                border: 1px solid {COLORS['primary']};
                color: {COLORS['primary']};
            }}
        """)
        self.setWindowFlags(Qt.WindowType.Dialog)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        self.btn_view = _btn("View Invoice")
        self.btn_edit = _btn("Edit Invoice")
        self.btn_pdf = _btn("Generate / View PDF")
        self.btn_down = _btn("Download Invoice")
        self.btn_print = _btn("Print Invoice")
        self.btn_pay = _btn("Record Payment", primary=True)
        self.btn_history = _btn("Payment History / Previous Transactions")
        self.btn_del = _btn("Delete Invoice")
        self.btn_del.setStyleSheet("""
            QPushButton, QPushButton#outline_btn {
                background-color: #FEF2F2; 
                color: #DC2626; 
                border: 1px solid #FECACA; 
                text-align: center;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover, QPushButton#outline_btn:hover {
                background-color: #FEE2E2;
                border: 1px solid #EF4444;
                color: #B91C1C;
            }
        """)
        self.btn_cancel = _btn("Cancel")
        
        self.btn_view.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_pdf.clicked.connect(lambda: self.done(1)) # Same as view
        self.btn_down.clicked.connect(lambda: self.done(4))
        self.btn_print.clicked.connect(lambda: self.done(5))
        self.btn_pay.clicked.connect(lambda: self.done(6))
        self.btn_history.clicked.connect(lambda: self.done(7))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_view)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_pdf)
        layout.addWidget(self.btn_down)
        layout.addWidget(self.btn_print)
        layout.addWidget(self.btn_pay)
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)

class PDFWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, invoice_id: int):
        super().__init__()
        self.invoice_id = invoice_id
        
    def run(self):
        try:
            path = PDFGenerator.generate_invoice_pdf(self.invoice_id)
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class InvoicesPage(QWidget):
    """Main Invoices Management Page."""
    
    def __init__(self, current_user: dict, context: str = "regular", parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.context = context
        self.active_company_id = None
        self.invoices = []
        self._build()
        
    def set_company(self, company_id: int):
        self.active_company_id = company_id
        self.refresh_data()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(20)
        
        # ── Top Bar ──────────────────────────────────────────────
        top_bar = QHBoxLayout()
        
        title = QLabel("Day Book Invoices" if self.context == "day_book" else "Invoices")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700; background: transparent;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        add_btn = _btn("Create Invoice", primary=True, icon="➕")
        add_btn.clicked.connect(self._on_add)
        top_bar.addWidget(add_btn)
        
        root.addLayout(top_bar)
        
        # ── Table ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["S.No", "Invoice #", "Customer", "Date", "Total", "Paid", "Remaining", "Status"])
        
        self.table.setStyleSheet(f"""
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
            QTableWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        
        
        
        
        
        self.table.cellClicked.connect(self._on_row_clicked)
        
        root.addWidget(self.table)

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        self.invoices = InvoiceService.get_invoices(self.active_company_id, context=self.context)
        
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for i, inv in enumerate(self.invoices):
            self.table.insertRow(i)
            self._populate_row(i, inv)
            
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)
        
    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))


    def _on_row_clicked(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item: return
        inv_id = id_item.data(Qt.ItemDataRole.UserRole)
        inv_num = self.table.item(row, 1).text()
        
        dlg = RowActionDialog(self, f"Invoice: {inv_num}")
        res = dlg.exec()
        
        if res == 1:
            self._on_view_pdf(inv_id)
        elif res == 2:
            self._on_edit(inv_id, row)
        elif res == 4:
            self._on_download(inv_id)
        elif res == 5:
            self._on_print(inv_id)
        elif res == 6:
            self._on_record_payment(inv_id, row)
        elif res == 7:
            self._on_payment_history(inv_id)
        elif res == 8:
            self._on_delete(inv_id)


    def _populate_row(self, row_idx: int, inv: dict):
        # S.No (Display Row Index + 1)
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        id_item.setData(Qt.ItemDataRole.UserRole, inv["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem(inv["invoice_number"]))
        self.table.setItem(row_idx, 2, QTableWidgetItem(inv["customer_name"]))
        self.table.setItem(row_idx, 3, QTableWidgetItem(inv["issue_date"].strftime("%Y-%m-%d")))
        self.table.setItem(row_idx, 4, QTableWidgetItem(f"{inv['net_amount']:.2f}"))
        
        paid = inv.get('paid_amount', 0.0)
        rem = inv['net_amount'] - paid
        
        self.table.setItem(row_idx, 5, QTableWidgetItem(f"{paid:.2f}"))
        self.table.setItem(row_idx, 6, QTableWidgetItem(f"{rem:.2f}"))
        
        status_item = QTableWidgetItem(inv["status"].upper())
        if inv["status"] == "paid":
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        elif inv["status"] == "partial":
            status_item.setForeground(Qt.GlobalColor.darkYellow)
        else:
            status_item.setForeground(Qt.GlobalColor.darkRed)
        self.table.setItem(row_idx, 7, status_item)
        




    def _on_payment_history(self, inv_id: int):
        from ui.components.payment_dialogs import PaymentHistoryDialog
        from services.invoice_service import InvoiceService
        inv = InvoiceService.get_invoice_by_id(inv_id)
        if not inv: return
        
        dlg = PaymentHistoryDialog(self, inv)
        dlg.exec()

    def _on_edit(self, inv_id: int, row: int):
        from ui.components.create_invoice_dialog import CreateInvoiceDialog
        dlg = CreateInvoiceDialog(self, self.active_company_id, self.current_user, invoice_id=inv_id)
        if dlg.exec():
            # fetch specific invoice to update row inline
            from services.invoice_service import InvoiceService
            inv = InvoiceService.get_invoice_by_id(inv_id)
            if inv:
                self._populate_row(row, inv)

    def _on_record_payment(self, inv_id: int, row: int):
        from ui.components.payment_dialogs import RecordInvoicePaymentDialog
        from services.invoice_service import InvoiceService
        inv = InvoiceService.get_invoice_by_id(inv_id)
        if not inv: return
        
        dlg = RecordInvoicePaymentDialog(self, self.active_company_id, self.current_user, inv)
        if dlg.exec():
            # Update row inline
            updated_inv = InvoiceService.get_invoice_by_id(inv_id)
            if updated_inv:
                self._populate_row(row, updated_inv)
                
            # Trigger Day Book sync
            main_window = self.window()
            if hasattr(main_window, 'day_book_page'):
                main_window.day_book_page.refresh_data()

    def _on_add(self):
        if not self.active_company_id:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        dlg = CreateInvoiceDialog(self, self.active_company_id, self.current_user, context=self.context)
        if dlg.exec():
            self.refresh_data()
            main_window = self.window()
            if hasattr(main_window, 'day_book_page'):
                main_window.day_book_page.refresh_data()
            if getattr(dlg, 'advance_payment_id', None):
                from PySide6.QtWidgets import QFileDialog
                from services.pdf_generator import PDFGenerator
                import os, platform, subprocess
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Advance Payment Receipt", 
                    f"Advance_Receipt_{dlg.advance_payment_id}.pdf", 
                    "PDF Files (*.pdf)"
                )
                if file_path:
                    try:
                        PDFGenerator.generate_payment_receipt(dlg.advance_payment_id, file_path)
                        if platform.system() == 'Windows':
                            os.startfile(file_path)
                        elif platform.system() == 'Darwin':
                            subprocess.call(('open', file_path))
                        else:
                            subprocess.call(('xdg-open', file_path))
                    except Exception as e:
                        show_message(self, "error", "PDF Error", f"Failed to generate receipt: {e}")

    def _on_view_pdf(self, inv_id: int):
        self.pdf_worker = PDFWorker(inv_id)
        self.pdf_worker.finished.connect(self._on_pdf_ready)
        self.pdf_worker.error.connect(lambda e: show_message(self, "error", "PDF Error", e))
        self.pdf_worker.start()
        
    def _on_pdf_ready(self, filepath: str):
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        else:
            subprocess.call(('xdg-open', filepath))

    def _on_delete(self, inv_id: int):
        from database.session import SessionLocal
        from models.invoice import Invoice
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this invoice?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with SessionLocal() as s:
                inv = s.query(Invoice).filter(Invoice.id == inv_id).first()
                if inv:
                    inv.is_deleted = True
                    s.commit()
            
            # Find and remove row instantly
            for r in range(self.table.rowCount()):
                item = self.table.item(r, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == inv_id:
                    self.table.removeRow(r)
                    self._update_serial_numbers()
                    break
            show_message(self, "success", "Deleted", "Invoice deleted successfully.")

    def _on_download(self, inv_id: int):
        from PySide6.QtWidgets import QFileDialog
        import shutil
        try:
            path = PDFGenerator.generate_invoice_pdf(inv_id)
            if os.path.exists(path):
                save_path, _ = QFileDialog.getSaveFileName(self, "Save Invoice", os.path.basename(path), "PDF Files (*.pdf)")
                if save_path:
                    shutil.copy2(path, save_path)
                    show_message(self, "success", "Success", "Invoice downloaded successfully.")
        except Exception as e:
            show_message(self, "error", "Error", str(e))

    def _on_print(self, inv_id: int):
        try:
            path = PDFGenerator.generate_invoice_pdf(inv_id)
            if platform.system() == 'Windows':
                os.startfile(path, "print")
            else:
                subprocess.call(('lpr', path))
        except Exception as e:
            show_message(self, "error", "Error", str(e))
