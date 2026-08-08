from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
import os, platform, subprocess
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.quotation_service import QuotationService
from services.pdf_generator import PDFGenerator
from ui.components.create_quotation_dialog import CreateQuotationDialog

class PDFWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, quotation_id: int):
        super().__init__()
        self.quotation_id = quotation_id
        
    def run(self):
        try:
            path = PDFGenerator.generate_quotation_pdf(self.quotation_id)
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class QuotationsPage(QWidget):
    """Main Quotations Management Page."""
    
    def __init__(self, current_user: dict, context: str = "regular", parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.context = context
        self.active_company_id = None
        self.quotations = []
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
        
        title = QLabel("Day Book Quotations" if self.context == "day_book" else "Quotations")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700; background: transparent;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        add_btn = _btn("Create Quotation", primary=True, icon="➕")
        add_btn.clicked.connect(self._on_add)
        top_bar.addWidget(add_btn)
        
        root.addLayout(top_bar)
        
        # ── Table ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["S.No", "Quotation #", "Customer", "Date", "Total", "Status", "Actions"])
        
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
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 150)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        
        root.addWidget(self.table)

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        self.quotations = QuotationService.get_quotations(self.active_company_id, context=self.context)
        
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        
        for i, inv in enumerate(self.quotations):
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
        down_btn.setToolTip("Download Quotation")
        down_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_download(i_id))
        
        print_btn = QPushButton("🖨️")
        print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        print_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        print_btn.setToolTip("Print Quotation")
        print_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_print(i_id))
        
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        del_btn.setToolTip("Delete Quotation")
        del_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_delete(i_id))
        
        convert_btn = QPushButton("🔄")
        convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        convert_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        convert_btn.setToolTip("Convert to Invoice")
        convert_btn.clicked.connect(lambda checked, i_id=inv_id: self._on_convert(i_id))
        
        action_layout.addWidget(view_btn)
        action_layout.addWidget(down_btn)
        action_layout.addWidget(print_btn)
        action_layout.addWidget(convert_btn)
        action_layout.addWidget(del_btn)
        return action_widget

    def _populate_row(self, row_idx: int, inv: dict):
        # S.No (Display Row Index + 1)
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        id_item.setData(Qt.ItemDataRole.UserRole, inv["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem(inv["quotation_number"]))
        self.table.setItem(row_idx, 2, QTableWidgetItem(inv["customer_name"]))
        self.table.setItem(row_idx, 3, QTableWidgetItem(inv["issue_date"].strftime("%Y-%m-%d")))
        self.table.setItem(row_idx, 4, QTableWidgetItem(f"{inv['net_amount']:.2f}"))
        
        status_item = QTableWidgetItem(inv["status"].upper())
        if inv["status"] == "converted":
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        elif inv["status"] == "pending":
            status_item.setForeground(Qt.GlobalColor.darkYellow)
        else:
            status_item.setForeground(Qt.GlobalColor.darkRed)
        self.table.setItem(row_idx, 5, status_item)
        
        action_widget = self._create_action_widget(inv["id"])
        self.table.setCellWidget(row_idx, 6, action_widget)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        inv_id_item = self.table.item(row, 0)
        if not inv_id_item: return
        
        inv_id = inv_id_item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        view_action = menu.addAction("📄 View Quotation")
        view_action.triggered.connect(lambda: self._on_view_pdf(inv_id))
        
        edit_action = menu.addAction("✏️ Edit Quotation")
        edit_action.triggered.connect(lambda: self._on_edit(inv_id, row))
        
        convert_action = menu.addAction("🔄 Convert to Invoice")
        convert_action.triggered.connect(lambda: self._on_convert(inv_id))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))



    def _on_edit(self, inv_id: int, row: int):
        from ui.components.create_quotation_dialog import CreateQuotationDialog
        dlg = CreateQuotationDialog(self, self.active_company_id, self.current_user, quotation_id=inv_id, context=self.context)
        if dlg.exec():
            # fetch specific quotation to update row inline
            from services.quotation_service import QuotationService
            inv = QuotationService.get_quotation(inv_id)
            if inv:
                self._populate_row(row, inv)

    def _on_convert(self, inv_id: int):
        from services.quotation_service import QuotationService
        reply = QMessageBox.question(self, "Confirm Conversion", "Convert this quotation to an invoice? This will create ledger entries.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = QuotationService.convert_to_invoice(inv_id, self.current_user["id"])
            if res.get("success"):
                inv_data = res.get("invoice_data")
                main_win = self.window()
                
                if hasattr(main_win, '_navigate_to'):
                    if self.context == "day_book":
                        target_page = "db_invoices"
                        target_page_obj = getattr(main_win, "db_invoices_page", None)
                    else:
                        target_page = "invoices"
                        target_page_obj = getattr(main_win, "invoices_page", None)
                        
                    if target_page_obj and inv_data:
                        target_page_obj.invoices.insert(0, inv_data)
                        target_page_obj.table.insertRow(0)
                        target_page_obj._populate_row(0, inv_data)
                        if hasattr(target_page_obj, '_update_serial_numbers'):
                            target_page_obj._update_serial_numbers()
                            
                    for r in range(self.table.rowCount()):
                        item = self.table.item(r, 0)
                        if item and item.data(Qt.ItemDataRole.UserRole) == inv_id:
                            status_item = QTableWidgetItem("CONVERTED")
                            status_item.setForeground(Qt.GlobalColor.darkGreen)
                            self.table.setItem(r, 5, status_item)
                            break
                            
                    show_message(self, "success", "Converted", "Quotation successfully converted to Invoice!")
                    main_win._navigate_to(target_page)
            else:
                show_message(self, "error", "Error", res.get("message", "Conversion failed."))

    def _on_add(self):
        if not self.active_company_id:
            show_message(self, "error", "Error", "No company selected.")
            return
            
        dlg = CreateQuotationDialog(self, self.active_company_id, self.current_user, context=self.context)
        if dlg.exec():
            self.refresh_data()

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
        from models.quotation import Quotation
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this quotation?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with SessionLocal() as s:
                inv = s.query(Quotation).filter(Quotation.id == inv_id).first()
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
            show_message(self, "success", "Deleted", "Quotation deleted successfully.")

    def _on_download(self, inv_id: int):
        self.pdf_worker = PDFWorker(inv_id)
        self.pdf_worker.finished.connect(self._on_pdf_ready_download)
        self.pdf_worker.error.connect(lambda e: show_message(self, "error", "PDF Error", str(e)))
        self.pdf_worker.start()
        
    def _on_pdf_ready_download(self, path: str):
        from PySide6.QtWidgets import QFileDialog
        import shutil
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Quotation", os.path.basename(path), "PDF Files (*.pdf)")
        if save_path:
            shutil.copy2(path, save_path)
            show_message(self, "success", "Success", "Quotation downloaded successfully.")

    def _on_print(self, inv_id: int):
        self.pdf_worker = PDFWorker(inv_id)
        self.pdf_worker.finished.connect(self._on_pdf_ready_print)
        self.pdf_worker.error.connect(lambda e: show_message(self, "error", "PDF Error", str(e)))
        self.pdf_worker.start()
        
    def _on_pdf_ready_print(self, path: str):
        if platform.system() == 'Windows':
            os.startfile(path, "print")
        else:
            subprocess.call(('lpr', path))
