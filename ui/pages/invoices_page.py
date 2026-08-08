from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
import os, platform, subprocess
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.invoice_service import InvoiceService
from services.pdf_generator import PDFGenerator
from ui.components.create_invoice_dialog import CreateInvoiceDialog

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
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["S.No", "Invoice #", "Customer", "Date", "Total", "Paid", "Remaining", "Status", "Actions"])
        
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
                background-color: #E2E8F0;
                color: {COLORS['text_primary']};
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
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 150)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        
        root.addWidget(self.table)

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        self.invoices = InvoiceService.get_invoices(self.active_company_id, context=self.context)
        
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        
        for i, inv in enumerate(self.invoices):
            self.table.insertRow(i)
            self._populate_row(i, inv)
            
        self.table.setUpdatesEnabled(True)
        
    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))

    def _on_row_double_clicked(self, item):
        row = item.row()
        id_item = self.table.item(row, 0)
        if id_item:
            inv_id = id_item.data(Qt.ItemDataRole.UserRole)
            if inv_id:
                self._on_view_pdf(inv_id)

    def _create_action_widget(self, inv_id: int) -> QWidget:
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 2, 4, 2)
        action_layout.setSpacing(8)
        
        view_btn = QPushButton("📄")
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        view_btn.setToolTip("Generate / View PDF")
        view_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_view_pdf(i_id))
        
        down_btn = QPushButton("⬇️")
        down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        down_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        down_btn.setToolTip("Download Invoice")
        down_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_download(i_id))
        
        print_btn = QPushButton("🖨️")
        print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        print_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        print_btn.setToolTip("Print Invoice")
        print_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_print(i_id))
        
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        del_btn.setToolTip("Delete Invoice")
        del_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_delete(i_id))
        
        action_layout.addWidget(view_btn)
        action_layout.addWidget(down_btn)
        action_layout.addWidget(print_btn)
        action_layout.addWidget(del_btn)
        return action_widget

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
        
        action_widget = self._create_action_widget(inv["id"])
        self.table.setCellWidget(row_idx, 8, action_widget)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        inv_id_item = self.table.item(row, 0)
        if not inv_id_item: return
        
        inv_id = inv_id_item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        view_action = menu.addAction("📄 View Invoice")
        view_action.triggered.connect(lambda: self._on_view_pdf(inv_id))
        
        edit_action = menu.addAction("✏️ Edit Invoice")
        edit_action.triggered.connect(lambda: self._on_edit(inv_id, row))
        
        pay_action = menu.addAction("💵 Record Payment")
        pay_action.triggered.connect(lambda: self._on_record_payment(inv_id, row))
        
        history_action = menu.addAction("🕒 Payment History / Previous Transactions")
        history_action.triggered.connect(lambda: self._on_payment_history(inv_id))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))

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
