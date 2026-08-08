from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView
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

class ServicesPage(QWidget):
    """Main Services Catalogue Management Page."""
    
    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.services = []
        self._build()
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["S.No", "Service Name", "Description", "Price", "Actions"])
        
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 140)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        
        root.addWidget(self.table)

    def _on_search_changed(self):
        self.search_timer.start(300)

    def refresh_data(self):
        term = self.search_input.text().strip()
        self.services = ServiceCatalogue.get_services(term)
        
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

    def _on_row_double_clicked(self, item):
        row = item.row()
        id_item = self.table.item(row, 0)
        if id_item:
            sid = id_item.data(Qt.ItemDataRole.UserRole)
            if sid:
                self._on_edit(sid)

    def _create_action_widget(self, sid: int) -> QWidget:
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 2, 4, 2)
        action_layout.setSpacing(8)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        edit_btn.setToolTip("Edit Service")
        edit_btn.clicked.connect(lambda checked, s_id=sid: self._on_edit(s_id))
        
        del_btn = QPushButton("🗑️")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        del_btn.setToolTip("Delete Service")
        del_btn.clicked.connect(lambda checked, s_id=sid: self._on_delete(s_id))
        
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(del_btn)
        return action_widget

    def _populate_row(self, row_idx: int, s: dict):
        id_item = QTableWidgetItem(str(row_idx + 1))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        id_item.setData(Qt.ItemDataRole.UserRole, s["id"])
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem(s["name"]))
        self.table.setItem(row_idx, 2, QTableWidgetItem(s["description"]))
        self.table.setItem(row_idx, 3, QTableWidgetItem(f"{s['price']:.2f}"))
        
        action_widget = self._create_action_widget(s["id"])
        self.table.setCellWidget(row_idx, 4, action_widget)

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
                    data["category"], data["name"], data["description"], data["price"], self.current_user["id"]
                )
                show_message(self, "success", "Success", "Service created successfully.")
                
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                self.services.append(new_s)
                self._populate_row(row_idx, new_s)
                
            except ValueError as e:
                show_message(self, "error", "Error", str(e))

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
