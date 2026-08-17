from PySide6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt, QTimer
from ui.design_system import COLORS
from ui.auth.setup_window import show_message
from ui.components.service_dialogs import ServiceFormDialog
from services.service_catalogue import ServiceCatalogue

def _btn(text: str, primary: bool = False, icon: str = "") -> QPushButton:
    b = QPushButton(f"{icon} {text}".strip())
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class RowActionDialog(QDialog):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedSize(320, 160)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 1px solid {COLORS['border_card']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        layout.addSpacing(20)
        
        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        btn_layout.setColumnStretch(2, 1)
        
        self.edit_btn = _btn("Edit", primary=True)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet(f"background-color: #FEE2E2; color: #EF4444; border: 1px solid #FCA5A5; padding: 8px 16px; border-radius: 6px; font-weight: 600;")
        self.cancel_btn = _btn("Cancel")
        
        self.edit_btn.setFixedSize(84, 38)
        self.del_btn.setFixedSize(84, 38)
        self.cancel_btn.setFixedSize(84, 38)
        
        btn_layout.addWidget(self.edit_btn, 0, 0)
        btn_layout.addWidget(self.del_btn, 0, 1)
        btn_layout.addWidget(self.cancel_btn, 0, 2)
        
        layout.addLayout(btn_layout)
        
        self.cancel_btn.clicked.connect(self.reject)
        self.edit_btn.clicked.connect(lambda: self.done(1))
        self.del_btn.clicked.connect(lambda: self.done(2))

class ServicesPage(QWidget):
    """Main Services Catalogue Management Page."""
    
    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.active_company_id = None
        self.services = []
        self._build()
        
    def set_company(self, company_id: int):
        self.active_company_id = company_id
        self.refresh_data()
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(20)
        
        # ── Top Bar ──────────────────────────────────────────────
        top_bar = QHBoxLayout()
        
        title = QLabel("Service Catalogue")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by name or category...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 10px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.search_input)
        
        add_btn = _btn("Add Service", primary=True, icon="➕")
        add_btn.clicked.connect(self._on_add)
        top_bar.addWidget(add_btn)
        
        root.addLayout(top_bar)
        
        # ── Table ────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["S.No", "Service Name", "Description", "Price"])
        
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
                background-color: #EFF6FF;
                color: {COLORS['primary']};
            }}
        """)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        
        self.table.itemClicked.connect(self._on_row_clicked)
        
        root.addWidget(self.table)

    def _on_search_changed(self):
        self.search_timer.start(300)

    def refresh_data(self):
        if not self.active_company_id:
            return
            
        term = self.search_input.text().strip()
        self.services = ServiceCatalogue.get_services(self.active_company_id, term)
        
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        
        for i, s in enumerate(self.services):
            self.table.insertRow(i)
            self._populate_row(i, s)
            
        self.table.setUpdatesEnabled(True)

    def _update_serial_numbers(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setText(str(row + 1))

    def _on_row_clicked(self, item):
        row = item.row()
        id_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        if id_item and name_item:
            sid = id_item.data(Qt.ItemDataRole.UserRole)
            s_name = name_item.text()
            if sid:
                dlg = RowActionDialog(self, f"Service: {s_name}")
                res = dlg.exec()
                if res == 1:
                    self._on_edit(sid)
                elif res == 2:
                    self._on_delete(sid)

    def _populate_row(self, row_idx: int, s: dict):
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        id_item.setData(Qt.ItemDataRole.UserRole, s["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem(s["name"]))
        self.table.setItem(row_idx, 2, QTableWidgetItem(s["description"]))
        self.table.setItem(row_idx, 3, QTableWidgetItem(f"{s['price']:.2f}"))
        


    def _find_row_by_id(self, sid: int) -> int:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == sid:
                return row
        return -1

    def _on_add(self):
        dlg = ServiceFormDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                show_message(self, "error", "Validation Error", "Service Name is required.")
                return
            if data["price"] < 0:
                show_message(self, "error", "Validation Error", "Price cannot be negative.")
                return
                
            try:
                new_s = ServiceCatalogue.create_service(
                    self.active_company_id, data["category"], data["name"], data["description"], data["price"], self.current_user["id"]
                )
                show_message(self, "success", "Success", "Service created successfully.")
                
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                self.services.append(new_s)
                self._populate_row(row_idx, new_s)
                return True
                
            except ValueError as e:
                show_message(self, "error", "Error", str(e))
        return False

    def _on_edit(self, sid: int):
        srv = next((s for s in self.services if s["id"] == sid), None)
        if not srv:
            return
            
        dlg = ServiceFormDialog(self, service_data=srv)
        if dlg.exec():
            data = dlg.get_data()
            if not data["name"]:
                show_message(self, "error", "Validation Error", "Service Name is required.")
                return
                
            try:
                success = ServiceCatalogue.update_service(
                    sid, data["category"], data["name"], data["description"], data["price"], self.current_user["id"]
                )
                if success:
                    show_message(self, "success", "Success", "Service updated successfully.")
                    row_idx = self._find_row_by_id(sid)
                    if row_idx != -1:
                        srv["category"] = data["category"]
                        srv["name"] = data["name"]
                        srv["description"] = data["description"]
                        srv["price"] = data["price"]
                        self._populate_row(row_idx, srv)
                else:
                    show_message(self, "error", "Error", "Failed to update service.")
            except ValueError as e:
                show_message(self, "error", "Error", str(e))

    def _on_delete(self, sid: int):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this service? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = ServiceCatalogue.soft_delete_service(sid, self.current_user["id"])
            if success:
                show_message(self, "success", "Deleted", "Service deleted successfully.")
                row_idx = self._find_row_by_id(sid)
                if row_idx != -1:
                    self.table.removeRow(row_idx)
                    self.services = [s for s in self.services if s["id"] != sid]
                    self._update_serial_numbers()
            else:
                show_message(self, "error", "Error", "Failed to delete service.")
