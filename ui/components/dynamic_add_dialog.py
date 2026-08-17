from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt
from ui.design_system import COLORS
from ui.auth.setup_window import show_message

class DynamicAddDialog(QDialog):
    def __init__(self, parent, title, prompt, input_label, second_label=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(350)
        self.setObjectName("DynamicAddDialog")
        
        self.setStyleSheet(f"""
            QDialog#DynamicAddDialog {{ background-color: {COLORS['bg_card']}; border-radius: 8px; border: 2px solid {COLORS['primary']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: bold; font-size: 14px; }}
            QLineEdit {{ background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 8px; color: {COLORS['text_primary']}; }}
            QLineEdit:focus {{ border: 1px solid {COLORS['primary']}; }}
            QPushButton {{ padding: 12px; border-radius: 6px; font-weight: bold; font-size: 13px; }}
            QPushButton#outline_btn {{ background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; color: {COLORS['text_primary']}; }}
            QPushButton#outline_btn:hover {{ background-color: #EFF6FF; border: 1px solid {COLORS['primary']}; color: {COLORS['primary']}; }}
            QPushButton#primary_btn {{ background-color: {COLORS['primary']}; color: white; border: none; }}
            QPushButton#primary_btn:hover {{ opacity: 0.9; }}
        """)
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel(prompt))
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(input_label)
        layout.addWidget(self.input_field)
        
        self.second_field = None
        if second_label:
            self.second_field = QLineEdit()
            self.second_field.setPlaceholderText(second_label)
            layout.addWidget(self.second_field)
        
        # Equal sized buttons
        btn_layout = QGridLayout()
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("outline_btn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("primary_btn")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.clicked.connect(self.validate_and_accept)
        
        self.btn_cancel.setFixedSize(140, 38)
        self.btn_ok.setFixedSize(140, 38)
        
        btn_layout.addWidget(self.btn_cancel, 0, 0)
        btn_layout.addWidget(self.btn_ok, 0, 1)
        layout.addLayout(btn_layout)

    def validate_and_accept(self):
        if "Optional" not in self.input_field.placeholderText() and not self.input_field.text().strip():
            show_message(self, "error", "Validation Error", f"{self.input_field.placeholderText().replace(' (Required)', '')} is required.")
            return
        if self.second_field and "Optional" not in self.second_field.placeholderText() and not self.second_field.text().strip():
            show_message(self, "error", "Validation Error", f"{self.second_field.placeholderText().replace(' (Required)', '')} is required.")
            return
        self.accept()
        
    def get_inputs(self):
        val1 = self.input_field.text().strip()
        val2 = self.second_field.text().strip() if self.second_field else None
        return val1, val2
