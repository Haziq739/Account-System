from PySide6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
import os, platform, subprocess
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.vendor_bill_service import VendorBillService
from services.vendor_service import VendorService
from services.pdf_generator import PDFGenerator
from ui.components.vendor_dialogs import CreateBillDialog


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
        
        self.btn_view = _btn("View Bill")
        self.btn_edit = _btn("Edit Bill")
        self.btn_download = _btn("Download Bill")
        self.btn_del = _btn("Delete Bill")
        self.btn_cancel = _btn("Cancel")
        
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
        
        self.btn_view.clicked.connect(lambda: self.done(1))
        self.btn_edit.clicked.connect(lambda: self.done(2))
        self.btn_download.clicked.connect(lambda: self.done(3))
        self.btn_del.clicked.connect(lambda: self.done(8))
        self.btn_cancel.clicked.connect(lambda: self.reject())
        
        layout.addWidget(self.btn_view)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_download)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_cancel)

class PDFWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, bill_id: int):
        super().__init__()
        self.bill_id = bill_id
        
    def run(self):
        try:
            path = PDFGenerator.generate_vendor_bill_pdf(self.bill_id)
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class VendorBillsPage(QWidget):
    """Page for managing vendor bills."""
    
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.active_company_id = None
        self.bills = []
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
        
        title = QLabel("Vendor Bills")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700; background: transparent;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        add_btn = _btn("Create Bill", primary=True, icon="➕")
        add_btn.clicked.connect(self._on_add)
        top_bar.addWidget(add_btn)
        
        root.addLayout(top_bar)
        
        # ── Table ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["S.No", "Bill #", "Vendor", "Date", "Description", "Amount"])
        
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
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        
        
        
        
        
        self.table.cellClicked.connect(self._on_row_clicked)
        
        root.addWidget(self.table)

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        self.bills = VendorBillService.get_bills(self.active_company_id)
        
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        
        for i, bill in enumerate(self.bills):
            self.table.insertRow(i)
            self._populate_row(i, bill)
            
        self.table.setUpdatesEnabled(True)
        
    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))


    def _on_row_clicked(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item: return
        bill_id = id_item.data(Qt.ItemDataRole.UserRole)
        bill_num = self.table.item(row, 1).text()
        
        dlg = RowActionDialog(self, f"Bill: {bill_num}")
        res = dlg.exec()
        
        if res == 1:
            self._on_view_pdf(bill_id)
        elif res == 2:
            self._on_edit(bill_id)
        elif res == 3:
            self._on_download(bill_id)
        elif res == 8:
            self._on_delete(bill_id)


    def _populate_row(self, row_idx: int, bill: dict):
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        id_item.setData(Qt.ItemDataRole.UserRole, bill["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem(bill["bill_number"]))
        self.table.setItem(row_idx, 2, QTableWidgetItem(bill["vendor_name"]))
        self.table.setItem(row_idx, 3, QTableWidgetItem(bill["bill_date"].strftime("%Y-%m-%d")))
        self.table.setItem(row_idx, 4, QTableWidgetItem(bill["description"]))
        self.table.setItem(row_idx, 5, QTableWidgetItem(f"{bill['amount']:.2f}"))
        




    def _on_add(self):
        if not self.active_company_id:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        vendors = VendorService.get_vendors(self.active_company_id)
        if not vendors:
            show_message(self, "warning", "No Vendors", "Please add a vendor first before creating a bill.")
            return
            
        dlg = CreateBillDialog(self, vendors=vendors)
        if dlg.exec():
            data = dlg.get_data()
            try:
                res = VendorBillService.create_bill(
                    company_id=self.active_company_id,
                    vendor_id=data["vendor_id"],
                    description=data["description"],
                    amount=data["amount"],
                    bill_date=data["bill_date"],
                    user_id=self.current_user["id"]
                )
                show_message(self, "success", "Success", "Bill created successfully.")
                self.refresh_data()
                return True
                if "id" in res:
                    self._auto_save_vendor_bill_pdf(res["id"])
            except Exception as e:
                show_message(self, "error", "Error", str(e))

    def _on_edit(self, bill_id: int):
        bill = next((b for b in self.bills if b["id"] == bill_id), None)
        if not bill:
            return
            
        vendors = VendorService.get_vendors(self.active_company_id)
        dlg = CreateBillDialog(self, vendors=vendors, bill_data=bill)
        
        if dlg.exec():
            data = dlg.get_data()
            if not data["vendor_id"]:
                show_message(self, "error", "Validation Error", "Please select a vendor.")
                return
            if data["amount"] <= 0:
                show_message(self, "error", "Validation Error", "Amount must be greater than 0.")
                return
                
            try:
                success = VendorBillService.update_bill(
                    company_id=self.active_company_id,
                    bill_id=bill_id,
                    vendor_id=data["vendor_id"],
                    description=data["description"],
                    amount=data["amount"],
                    user_id=self.current_user["id"]
                )
                if success:
                    show_message(self, "success", "Success", "Bill updated successfully.")
                    self.refresh_data()
                    self._auto_save_vendor_bill_pdf(bill_id)
                else:
                    show_message(self, "error", "Error", "Failed to update bill.")
            except Exception as e:
                show_message(self, "error", "Error", str(e))

    def _on_view_pdf(self, bill_id: int):
        self.pdf_worker = PDFWorker(bill_id)
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

    def _on_delete(self, bill_id: int):
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this bill?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success = VendorBillService.delete_bill(self.active_company_id, bill_id, self.current_user["id"])
            if success:
                show_message(self, "success", "Deleted", "Bill deleted successfully.")
                self.refresh_data()
            else:
                show_message(self, "error", "Error", "Failed to delete bill.")

    def _auto_save_vendor_bill_pdf(self, bill_id: int):
        from PySide6.QtCore import QThread
        from services.pdf_generator import PDFGenerator
        from utils.logger import logger
        
        class BillPDFWorker(QThread):
            def __init__(self, b_id):
                super().__init__()
                self.b_id = b_id
                
            def run(self):
                try:
                    PDFGenerator.generate_vendor_bill_pdf(self.b_id)
                except Exception as e:
                    logger.error(f"Failed to auto-save vendor bill PDF: {e}")
                    
        self._pdf_worker = BillPDFWorker(bill_id)
        self._pdf_worker.start()

    def _on_download(self, bill_id: int):
        from PySide6.QtWidgets import QFileDialog
        import shutil
        import os
        try:
            path = PDFGenerator.generate_vendor_bill_pdf(bill_id)
            if os.path.exists(path):
                save_path, _ = QFileDialog.getSaveFileName(self, "Save Bill", os.path.basename(path), "PDF Files (*.pdf)")
                if save_path:
                    shutil.copy2(path, save_path)
                    show_message(self, "success", "Success", "Bill downloaded successfully.")
        except Exception as e:
            show_message(self, "error", "Error", str(e))
