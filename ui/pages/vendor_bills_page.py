from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal
import os, platform, subprocess
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.vendor_bill_service import VendorBillService
from services.vendor_service import VendorService
from services.pdf_generator import PDFGenerator
from ui.components.vendor_dialogs import CreateBillDialog

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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["S.No", "Bill #", "Vendor", "Date", "Description", "Amount", "Actions"])
        
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
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 120)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        
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

    def _on_row_double_clicked(self, item):
        row = item.row()
        id_item = self.table.item(row, 0)
        if id_item:
            bill_id = id_item.data(Qt.ItemDataRole.UserRole)
            if bill_id:
                self._on_view_pdf(bill_id)

    def _create_action_widget(self, bill_id: int) -> QWidget:
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 2, 4, 2)
        action_layout.setSpacing(8)
        
        view_btn = QPushButton("📄")
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        view_btn.setToolTip("Generate / View PDF")
        view_btn.clicked.connect(lambda checked, b_id=bill_id: self._on_view_pdf(b_id))
        
        edit_btn = QPushButton("✏️")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        edit_btn.setToolTip("Edit Bill")
        edit_btn.clicked.connect(lambda checked, b_id=bill_id: self._on_edit(b_id))
        
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        del_btn.setToolTip("Delete Bill")
        del_btn.clicked.connect(lambda checked, b_id=bill_id: self._on_delete(b_id))
        
        action_layout.addWidget(view_btn)
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(del_btn)
        return action_widget

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
        
        action_widget = self._create_action_widget(bill["id"])
        self.table.setCellWidget(row_idx, 6, action_widget)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        id_item = self.table.item(row, 0)
        if not id_item: return
        
        bill_id = id_item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        view_action = menu.addAction("📄 View PDF")
        view_action.triggered.connect(lambda: self._on_view_pdf(bill_id))
        
        edit_action = menu.addAction("✏️ Edit Bill")
        edit_action.triggered.connect(lambda: self._on_edit(bill_id))
        
        del_action = menu.addAction("🗑️ Delete Bill")
        del_action.triggered.connect(lambda: self._on_delete(bill_id))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))

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
            if not data["vendor_id"]:
                show_message(self, "error", "Validation Error", "Please select a vendor.")
                return
            if data["amount"] <= 0:
                show_message(self, "error", "Validation Error", "Amount must be greater than 0.")
                return
                
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
