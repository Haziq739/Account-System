import os
import re

def fix_services_page(page_file, dialog_file):
    with open(page_file, "r", encoding="utf-8") as f:
        p_content = f.read()

    # 1. Add RowActionDialog class
    row_action_code = """class RowActionDialog(QDialog):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.setWindowTitle("Action")
        self.setFixedSize(320, 160)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 1px solid {COLORS['border_card']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        layout.addSpacing(20)
        
        btn_layout = QHBoxLayout()
        self.edit_btn = _btn("Edit", primary=True)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet(f"background-color: #FEE2E2; color: #EF4444; border: 1px solid #FCA5A5; padding: 8px 16px; border-radius: 6px; font-weight: 600;")
        self.cancel_btn = _btn("Cancel")
        
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.cancel_btn.clicked.connect(self.reject)
        self.edit_btn.clicked.connect(lambda: self.done(1))
        self.del_btn.clicked.connect(lambda: self.done(2))

class ServicesPage"""
    
    if "class RowActionDialog" not in p_content:
        p_content = p_content.replace("class ServicesPage", row_action_code)

    # 2. Modify _build: column count, headers, connecting itemClicked, and focus color
    p_content = p_content.replace('self.table.setColumnCount(5)', 'self.table.setColumnCount(4)')
    p_content = p_content.replace('self.table.setHorizontalHeaderLabels(["S.No", "Service Name", "Description", "Price", "Actions"])', 'self.table.setHorizontalHeaderLabels(["S.No", "Service Name", "Description", "Price"])')
    
    # 3. Modify table header resize modes
    p_content = p_content.replace('header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)', '')
    p_content = p_content.replace('self.table.setColumnWidth(4, 140)', '')
    
    # Replace itemDoubleClicked with itemClicked and focus color styles
    old_style = "QTableWidget::item:selected {{\n                background-color: #E2E8F0;\n                color: {COLORS['text_primary']};\n            }}"
    new_style = "QTableWidget::item:selected {{\n                background-color: #EFF6FF;\n                color: {COLORS['primary']};\n            }}"
    p_content = p_content.replace(old_style, new_style)
    p_content = p_content.replace('self.table.itemDoubleClicked.connect(self._on_row_double_clicked)', 'self.table.itemClicked.connect(self._on_row_clicked)')

    # 4. Remove _create_action_widget
    # Using regex to remove the method
    p_content = re.sub(r'    def _create_action_widget\(self, sid: int\) -> QWidget:[\s\S]*?return action_widget\n\n', '', p_content)

    # 5. Modify _populate_row
    old_populate = """        action_widget = self._create_action_widget(s["id"])
        self.table.setCellWidget(row_idx, 4, action_widget)"""
    p_content = p_content.replace(old_populate, '')

    # 6. Replace _on_row_double_clicked with _on_row_clicked
    on_row_clicked_code = """    def _on_row_clicked(self, item):
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
                    self._on_delete(sid)"""
    p_content = re.sub(r'    def _on_row_double_clicked\(self, item\):[\s\S]*?self\._on_edit\(sid\)', on_row_clicked_code, p_content)


    # Write back to file
    with open(page_file, "w", encoding="utf-8") as f:
        f.write(p_content)


    # --- Modify ServiceFormDialog ---
    with open(dialog_file, "r", encoding="utf-8") as f:
        d_content = f.read()
        
    old_btns = """        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Service", primary=True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)"""
        
    new_btns = """        btn_layout = QHBoxLayout()
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_text = "Update" if self.is_edit else "Save Service"
        save_btn = _btn(save_text, primary=True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(save_btn, 1)"""
        
    d_content = d_content.replace(old_btns, new_btns)
    
    with open(dialog_file, "w", encoding="utf-8") as f:
        f.write(d_content)

if __name__ == "__main__":
    page = r"d:\Account_System\ui\pages\services_page.py"
    dialog = r"d:\Account_System\ui\components\service_dialogs.py"
    fix_services_page(page, dialog)
