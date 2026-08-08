from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget, QGridLayout
)
from PySide6.QtCore import Qt
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from services.invoice_service import InvoiceService
from services.customer import CustomerService
from services.service_catalogue import ServiceCatalogue
from database.session import SessionLocal
from models.company import Company
from datetime import date

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class CreateInvoiceDialog(QDialog):
    """Full screen dialog to create a new invoice."""
    
    # Removed CATEGORIES dict

    def __init__(self, parent, company_id: int, current_user: dict, invoice_id: int = None, context: str = "regular"):
        super().__init__(parent)
        self.company_id = company_id
        self.current_user = current_user
        self.invoice_id = invoice_id
        self.context = context
        
        self.customers = []
        self.all_services = []
        self.filtered_services = []
        self.items_data = [] # list of dicts
        self.advance_payment_id = None
        
        self.tax_enabled = False
        self.tax_rate = 0.0
        
        self.setWindowTitle("Edit Invoice" if self.invoice_id else "Create New Invoice")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_app']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: 500; font-size: 13px; }}
            QLineEdit, QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {COLORS['text_primary']};
                min-height: 22px;
            }}
            QLineEdit:focus, QComboBox:focus {{ 
                border: 1px solid {COLORS['primary']}; 
                color: {COLORS['text_primary']}; 
                background-color: {COLORS['bg_input']}; 
            }}
        """)
        
        self._load_data()
        self._build()
        self.filtered_services = self.all_services
        
        if self.invoice_id:
            self._load_existing_invoice()
        else:
            self._calculate_totals()

    def _load_existing_invoice(self):
        inv = InvoiceService.get_invoice_by_id(self.invoice_id)
        if not inv: return
        
        idx = self.customer_cb.findData(inv["customer_id"])
        if idx >= 0: self.customer_cb.setCurrentIndex(idx)
        
        self.discount_input.setText(str(inv["discount"]))
        self.tax_input.setText(str(inv["tax_percentage"]))
        self.paid_input.setText(str(inv["paid_amount"]))
        self.paid_input.setEnabled(False) # Payments managed via Record Payment dialog
        self.pay_method_cb.setEnabled(False)
        self.notes_input.setText(inv["notes"] or "")
        
        for item in inv["items"]:
            self._add_item_row(item)
            
        self._calculate_totals()

    def _load_data(self):
        with SessionLocal() as s:
            comp = s.query(Company).filter(Company.id == self.company_id).first()
            if comp:
                self.tax_enabled = comp.tax_enabled
                self.tax_rate = float(comp.default_tax_rate)
                
        self.customers = CustomerService.get_customers(customer_type=self.context)
        self.all_services = ServiceCatalogue.get_services()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(15)
        root.setContentsMargins(20, 20, 20, 20)
        
        # ── Top Section: Customer & Category ───────────────────────
        top_layout = QHBoxLayout()
        
        # Customer
        cust_layout = QVBoxLayout()
        cust_layout.addWidget(QLabel("Customer *"))
        self.customer_cb = QComboBox()
        self.customer_cb.addItem("-- Select Customer --", None)
        for c in self.customers:
            display_name = f"{c['name']} ({c['phone']})" if c.get('phone') else c['name']
            self.customer_cb.addItem(display_name, c['id'])
        cust_layout.addWidget(self.customer_cb)
        top_layout.addLayout(cust_layout)
        
        root.addLayout(top_layout)
        
        # ── Items Table ────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["S.No", "Service", "Description", "Qty", "Price", "Amount", ""])
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_input']};
                padding: 8px; border: none;
                border-bottom: 1px solid {COLORS['border_card']};
                text-align: left;
            }}
            QTableWidget::item {{
                background-color: transparent;
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:selected, QTableWidget::item:focus {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                outline: none;
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 40)
        
        root.addWidget(self.table)
        
        # Add Item Button
        add_item_btn = _btn("Add Service Item", icon="➕")
        add_item_btn.clicked.connect(self._add_item_row)
        root.addWidget(add_item_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # ── Bottom Section: Totals & Payments ──────────────────────
        bottom_layout = QHBoxLayout()
        
        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QLineEdit()
        notes_layout.addWidget(self.notes_input)
        bottom_layout.addLayout(notes_layout, stretch=1)
        
        # Totals Panel
        totals_panel = QWidget()
        totals_grid = QGridLayout(totals_panel)
        row = 0
        
        totals_grid.addWidget(QLabel("Subtotal:"), row, 0)
        self.subtotal_lbl = QLabel("0.00")
        totals_grid.addWidget(self.subtotal_lbl, row, 1)
        row += 1
        
        totals_grid.addWidget(QLabel("Discount:"), row, 0)
        self.discount_input = QLineEdit("0.00")
        self.discount_input.setFixedWidth(100)
        self.discount_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.discount_input, row, 1)
        row += 1
        
        # Tax fields - only visible if tax_enabled
        self.tax_label_ui = QLabel("Tax (%):")
        totals_grid.addWidget(self.tax_label_ui, row, 0)
        self.tax_input = QLineEdit(str(self.tax_rate))
        self.tax_input.setFixedWidth(100)
        self.tax_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.tax_input, row, 1)
        row += 1
        
        self.tax_amt_lbl_ui = QLabel("Tax Amount:")
        totals_grid.addWidget(self.tax_amt_lbl_ui, row, 0)
        self.tax_amt_lbl = QLabel("0.00")
        totals_grid.addWidget(self.tax_amt_lbl, row, 1)
        row += 1
        
        if not self.tax_enabled:
            self.tax_label_ui.hide()
            self.tax_input.hide()
            self.tax_amt_lbl_ui.hide()
            self.tax_amt_lbl.hide()
            self.tax_input.setText("0.0")

        totals_grid.addWidget(QLabel("Net Total:", styleSheet="font-weight: bold;"), row, 0)
        self.net_total_lbl = QLabel("0.00", styleSheet="font-weight: bold; font-size: 16px;")
        totals_grid.addWidget(self.net_total_lbl, row, 1)
        row += 1
        
        totals_grid.addWidget(QLabel("Advance Payment:"), row, 0)
        self.paid_input = QLineEdit("0.00")
        self.paid_input.setFixedWidth(100)
        self.paid_input.textChanged.connect(self._calculate_totals)
        totals_grid.addWidget(self.paid_input, row, 1)
        row += 1
        
        totals_grid.addWidget(QLabel("Payment Method:"), row, 0)
        self.pay_method_cb = QComboBox()
        self.pay_method_cb.addItems(["Cash", "Bank Transfer", "Cheque", "Credit"])
        totals_grid.addWidget(self.pay_method_cb, row, 1)
        row += 1
        
        totals_grid.addWidget(QLabel("Remaining:", styleSheet="color: #E53E3E; font-weight: bold;"), row, 0)
        self.remaining_lbl = QLabel("0.00", styleSheet="color: #E53E3E; font-weight: bold;")
        totals_grid.addWidget(self.remaining_lbl, row, 1)
        
        bottom_layout.addWidget(totals_panel)
        root.addLayout(bottom_layout)
        
        # Save btn
        save_btn = _btn("Save and Generate Invoice", primary=True)
        save_btn.clicked.connect(self._save)
        root.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_item_row(self, existing_item: dict = None):
        if not self.filtered_services:
            show_message(self, "warning", "No Services", "No services available for this category.")
            return
            
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # S.No
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        
        # Service CB
        srv_cb = QComboBox()
        for s in self.filtered_services:
            srv_cb.addItem(s["name"], s["id"])
        self.table.setCellWidget(row, 1, srv_cb)
        
        # Desc
        desc_input = QLineEdit()
        self.table.setCellWidget(row, 2, desc_input)
        
        # Qty
        qty_input = QLineEdit("1")
        self.table.setCellWidget(row, 3, qty_input)
        
        # Price
        price_input = QLineEdit()
        price_input.setMinimumWidth(80)
        self.table.setCellWidget(row, 4, price_input)
        
        # Amount
        amt_lbl = QLabel("0.00")
        amt_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        self.table.setCellWidget(row, 5, amt_lbl)
        
        # Delete btn
        del_btn = QPushButton("❌")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 12px; color: #E53E3E;")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda _, r=row: self._remove_item_row(r))
        self.table.setCellWidget(row, 6, del_btn)
        
        # Connections for live calculations
        srv_cb.currentIndexChanged.connect(lambda: self._on_service_selected(row))
        qty_input.textChanged.connect(self._calculate_totals)
        price_input.textChanged.connect(self._calculate_totals)
        
        if existing_item:
            idx = srv_cb.findData(existing_item["service_id"])
            if idx >= 0: srv_cb.setCurrentIndex(idx)
            desc_input.setText(existing_item["description"] or "")
            qty_input.setText(str(existing_item["quantity"]))
            price_input.setText(str(existing_item["unit_price"]))
        else:
            self._on_service_selected(row)

    def _on_service_selected(self, row: int):
        srv_cb = self.table.cellWidget(row, 1)
        desc_input = self.table.cellWidget(row, 2)
        price_input = self.table.cellWidget(row, 4)
        if srv_cb and price_input and desc_input:
            sid = srv_cb.currentData()
            srv = next((s for s in self.filtered_services if s["id"] == sid), None)
            if srv:
                price_input.setText(str(srv["price"]))
                desc_input.setText(srv.get("description", ""))
        self._calculate_totals()

    def _remove_item_row(self, row_idx: int):
        self.table.removeRow(row_idx)
        # Update S.No
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setText(str(r + 1))
            # update delete button lambda to match new row index
            del_btn = self.table.cellWidget(r, 6)
            if del_btn:
                del_btn.clicked.disconnect()
                del_btn.clicked.connect(lambda _, current_r=r: self._remove_item_row(current_r))
                
        self._calculate_totals()

    def _get_float(self, text: str) -> float:
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _calculate_totals(self):
        subtotal = 0.0
        self.items_data.clear()
        
        for r in range(self.table.rowCount()):
            srv_cb = self.table.cellWidget(r, 1)
            desc_input = self.table.cellWidget(r, 2)
            qty_input = self.table.cellWidget(r, 3)
            price_input = self.table.cellWidget(r, 4)
            amt_lbl = self.table.cellWidget(r, 5)
            
            if srv_cb and qty_input and price_input and amt_lbl:
                qty = self._get_float(qty_input.text())
                price = self._get_float(price_input.text())
                amt = qty * price
                amt_lbl.setText(f"{amt:.2f}")
                subtotal += amt
                
                self.items_data.append({
                    "service_id": srv_cb.currentData(),
                    "description": desc_input.text(),
                    "quantity": qty,
                    "unit_price": price
                })
                
        self.subtotal_lbl.setText(f"{subtotal:.2f}")
        
        discount = self._get_float(self.discount_input.text())
        after_disc = max(0.0, subtotal - discount)
        
        tax_pct = self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0
        tax_amt = after_disc * (tax_pct / 100.0)
        self.tax_amt_lbl.setText(f"{tax_amt:.2f}")
        
        net = after_disc + tax_amt
        self.net_total_lbl.setText(f"{net:.2f}")
        
        paid = self._get_float(self.paid_input.text())
            
        rem = net - paid
        self.remaining_lbl.setText(f"{rem:.2f}")

    def _save(self):
        cust_id = self.customer_cb.currentData()
        if not cust_id:
            show_message(self, "error", "Error", "Please select a customer.")
            return
            
        if not self.items_data:
            show_message(self, "error", "Error", "Please add at least one item.")
            return
            
        disc = self._get_float(self.discount_input.text())
        tax = self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0
        paid = self._get_float(self.paid_input.text())
        net = self._get_float(self.net_total_lbl.text())
        
        if paid > net:
            show_message(self, "error", "Error", "Advance payment cannot exceed the Net Total.")
            return
            
        method = self.pay_method_cb.currentText()
        notes = self.notes_input.text().strip()
        
        try:
            if self.invoice_id:
                InvoiceService.update_invoice(
                    self.invoice_id, cust_id, self.items_data, disc, tax, notes, self.current_user["id"]
                )
                show_message(self, "success", "Success", "Invoice updated successfully!")
                self._auto_save_invoice_pdf(self.invoice_id)
            else:
                inv_res = InvoiceService.create_invoice(
                    self.company_id, cust_id, date.today(),
                    self.items_data, disc, tax, paid, method, notes, self.current_user["id"]
                )
                show_message(self, "success", "Success", "Invoice generated successfully!")
                
                # Check if advance payment was made, to show receipt
                if "payment" in inv_res:
                    self.advance_payment_id = inv_res["payment"]["id"]
                    
                # Auto-save PDF in background
                self._auto_save_invoice_pdf(inv_res["id"])
                    
            self.accept()
        except Exception as e:
            show_message(self, "error", "Error", f"Failed to save invoice:\n{str(e)}")

    def _auto_save_invoice_pdf(self, inv_id: int):
        from PySide6.QtCore import QThread
        from services.pdf_generator import PDFGenerator
        from utils.logger import logger
        
        class InvoicePDFWorker(QThread):
            def __init__(self, invoice_id):
                super().__init__()
                self.invoice_id = invoice_id
                
            def run(self):
                try:
                    PDFGenerator.generate_invoice_pdf(self.invoice_id)
                except Exception as e:
                    logger.error(f"Failed to auto-save invoice PDF: {e}")
                    
        # keep a reference to prevent garbage collection
        self._pdf_worker = InvoicePDFWorker(inv_id)
        self._pdf_worker.start()
