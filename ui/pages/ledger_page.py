from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QDateEdit, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QDate
from ui.design_system import COLORS
from services.customer import CustomerService
from services.ledger_service import LedgerService
from utils.logger import logger
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
        QPushButton:disabled {{ background-color: {COLORS['border']}; color: #888; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class StatementPDFWorker(QThread):
    finished = Signal(str, str, str)
    error = Signal(str)
    
    def __init__(self, comp_id, cust_id, start_date, end_date, action, save_path="", ledger_data=None):
        super().__init__()
        self.comp_id = comp_id
        self.cust_id = cust_id
        self.start_date = start_date
        self.end_date = end_date
        self.action = action
        self.save_path = save_path
        self.ledger_data = ledger_data
        
    def run(self):
        try:
            from services.pdf_generator import PDFGenerator
            path = PDFGenerator.generate_customer_statement_pdf(
                self.comp_id, self.cust_id, self.start_date, self.end_date, self.ledger_data
            )
            self.finished.emit(path, self.action, self.save_path)
        except Exception as e:
            self.error.emit(str(e))

class LedgerPage(QWidget):
    def __init__(self, company_id: int, context: str = "regular"):
        super().__init__()
        self.company_id = company_id
        self.context = context
        self.ledger_entries = []
        self._build()
        self._load_customers()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(20)
        root.setContentsMargins(30, 30, 30, 30)

        # Header Area
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Day Book Ledger" if self.context == "day_book" else "Customer Ledger")
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: bold; background: transparent;")
        header_layout.addWidget(title_lbl)
        
        header_layout.addStretch()
        
        self.balance_lbl = QLabel("Outstanding Balance: 0.00")
        self.balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['primary']};")
        header_layout.addWidget(self.balance_lbl)
        
        root.addLayout(header_layout)

        # Controls Filter
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Customer:", styleSheet=f"color: {COLORS['text_primary']};"))
        
        self.customer_cb = QComboBox()
        self.customer_cb.currentIndexChanged.connect(self._load_ledger)
        self.customer_cb.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px; padding: 8px 12px;
                color: {COLORS['text_primary']};
                min-width: 200px;
            }}
        """)
        ctrl_layout.addWidget(self.customer_cb)
        
        ctrl_layout.addSpacing(15)
        ctrl_layout.addWidget(QLabel("From:", styleSheet=f"color: {COLORS['text_primary']};"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        # Default to first day of current month
        d = QDate.currentDate()
        self.start_date_edit.setDate(QDate(d.year(), d.month(), 1))
        self.start_date_edit.setStyleSheet(f"""
            QDateEdit {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; 
            border-radius: 6px; padding: 6px; color: {COLORS['text_primary']}; }}
        """)
        ctrl_layout.addWidget(self.start_date_edit)
        
        ctrl_layout.addSpacing(10)
        ctrl_layout.addWidget(QLabel("To:", styleSheet=f"color: {COLORS['text_primary']};"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setStyleSheet(f"""
            QDateEdit {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; 
            border-radius: 6px; padding: 6px; color: {COLORS['text_primary']}; }}
        """)
        ctrl_layout.addWidget(self.end_date_edit)
        
        refresh_btn = _btn("Filter", primary=True)
        refresh_btn.clicked.connect(self._load_ledger)
        ctrl_layout.addWidget(refresh_btn)
        
        ctrl_layout.addStretch()
        
        self.down_btn = _btn("Download Statement")
        self.down_btn.clicked.connect(self._on_download)
        self.down_btn.setEnabled(False)
        
        self.print_btn = _btn("Print Statement")
        self.print_btn.clicked.connect(self._on_print)
        self.print_btn.setEnabled(False)
        
        ctrl_layout.addWidget(self.down_btn)
        ctrl_layout.addWidget(self.print_btn)
        
        root.addLayout(ctrl_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Type", "Ref / Receipt", "Description", "Debit", "Credit", "Balance"
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
            QTableWidget::item {{
                background-color: transparent;
                color: {COLORS['text_primary']};
            }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        root.addWidget(self.table)

    def set_company(self, company_id: int):
        self.company_id = company_id
        self._load_customers()

    def refresh_data(self):
        self._load_customers()

    def _load_customers(self):
        self.customer_cb.blockSignals(True)
        self.customer_cb.clear()
        self.customer_cb.addItem("-- Select a Customer --", None)
        
        customers = CustomerService.get_customers_with_ledger(self.company_id, customer_type=self.context)
        for c in customers:
            self.customer_cb.addItem(c['name'], c['id'])
            
        self.customer_cb.blockSignals(False)
        self._load_ledger()

    def _get_dates(self):
        s_date = self.start_date_edit.date().toPython()
        e_date = self.end_date_edit.date().toPython()
        return s_date, e_date

    def _load_ledger(self):
        cust_id = self.customer_cb.currentData()
        
        if not cust_id:
            self.table.setRowCount(0)
            self.balance_lbl.setText("Outstanding Balance: 0.00")
            self.balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
            self.down_btn.setEnabled(False)
            self.print_btn.setEnabled(False)
            return
            
        self.down_btn.setEnabled(True)
        self.print_btn.setEnabled(True)
            
        s_date, e_date = self._get_dates()
        self.ledger_entries = LedgerService.get_customer_ledger(self.company_id, cust_id, s_date, e_date)
        
        self.table.setRowCount(0)
        
        if self.ledger_entries:
            # Last entry in UI is the latest (since it is sorted chronologically)
            latest = self.ledger_entries[-1]
            bal = latest['balance']
            if bal > 0:
                self.balance_lbl.setText(f"Outstanding Balance (Owed to you): {bal:.2f}")
                self.balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #E53E3E;")
            elif bal < 0:
                self.balance_lbl.setText(f"Advance Balance (Owed to Customer): {abs(bal):.2f}")
                self.balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['primary']};")
            else:
                self.balance_lbl.setText("Outstanding Balance: 0.00")
                self.balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        else:
            self.balance_lbl.setText("Outstanding Balance: 0.00")
            self.balance_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
            
        for entry in self.ledger_entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Format opening balance nicely
            if entry["type"] == "opening balance":
                dt_str = entry["date"].strftime("%Y-%m-%d")
                self.table.setItem(row, 0, QTableWidgetItem(dt_str))
                
                type_item = QTableWidgetItem("Opening Balance")
                f = type_item.font()
                f.setBold(True)
                type_item.setFont(f)
                
                self.table.setItem(row, 1, type_item)
                
                self.table.setItem(row, 2, QTableWidgetItem(entry["ref"] or ""))
                self.table.setItem(row, 3, QTableWidgetItem(entry["desc"] or ""))
                self.table.setItem(row, 4, QTableWidgetItem(f"{entry['debit']:.2f}"))
                self.table.setItem(row, 5, QTableWidgetItem(f"{entry['credit']:.2f}"))
                
                self.table.setItem(row, 6, QTableWidgetItem(f"{entry['row_balance']:.2f}"))
                continue
                
            dt_val = entry["date"].strftime("%Y-%m-%d") if hasattr(entry["date"], 'strftime') else str(entry["date"])
            self.table.setItem(row, 0, QTableWidgetItem(dt_val))
            self.table.setItem(row, 1, QTableWidgetItem(entry["type"].capitalize()))
            self.table.setItem(row, 2, QTableWidgetItem(entry["ref"] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(entry["desc"] or ""))
            
            deb = QTableWidgetItem(f"{entry['debit']:.2f}")
            if entry['debit'] > 0: deb.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 4, deb)
            
            cre = QTableWidgetItem(f"{entry['credit']:.2f}")
            if entry['credit'] > 0: cre.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 5, cre)
            
            bal = QTableWidgetItem(f"{entry['row_balance']:.2f}")
            self.table.setItem(row, 6, bal)

    def _on_download(self):
        cust_id = self.customer_cb.currentData()
        if not cust_id: return
        
        s_date, e_date = self._get_dates()
        cust_name = self.customer_cb.currentText().replace(" ", "_")
        default_name = f"Statement_{cust_name}_{s_date.strftime('%Y%m%d')}_to_{e_date.strftime('%Y%m%d')}.pdf"
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Statement", default_name, "PDF Files (*.pdf)")
        if not save_path: return
        
        self._start_worker('download', save_path, cust_id, s_date, e_date)
        
    def _on_print(self):
        cust_id = self.customer_cb.currentData()
        if not cust_id: return
        
        s_date, e_date = self._get_dates()
        self._start_worker('print', "", cust_id, s_date, e_date)
        
    def _start_worker(self, action, save_path, cust_id, s_date, e_date):
        self.down_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.down_btn.setText("Generating...")
        
        self.worker = StatementPDFWorker(self.company_id, cust_id, s_date, e_date, action, save_path, self.ledger_entries)
        self.worker.finished.connect(self._on_pdf_ready)
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()
        
    def _on_pdf_ready(self, path: str, action: str, save_path: str):
        self.down_btn.setText("Download Statement")
        self.print_btn.setText("Print Statement")
        self.down_btn.setEnabled(True)
        self.print_btn.setEnabled(True)
        
        import shutil, os, platform, subprocess
        if action == 'download':
            if save_path:
                try:
                    shutil.copy2(path, save_path)
                    show_message(self, "success", "Success", "Statement downloaded successfully.")
                except Exception as e:
                    show_message(self, "error", "Error", f"Failed to save statement: {e}")
        elif action == 'print':
            try:
                if platform.system() == 'Windows':
                    os.startfile(path, "print")
                else:
                    subprocess.call(('lpr', path))
            except Exception as e:
                show_message(self, "error", "Print Error", str(e))
                
    def _on_pdf_error(self, err: str):
        self.down_btn.setText("Download Statement")
        self.print_btn.setText("Print Statement")
        self.down_btn.setEnabled(True)
        self.print_btn.setEnabled(True)
        show_message(self, "error", "Error", f"Failed to generate statement: {err}")
