from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt
from ui.design_system import COLORS

def _btn(text: str, primary: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("primary_btn" if primary else "outline_btn")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

class ServiceFormDialog(QDialog):
    """Dialog for Adding or Editing a Service."""
    
    # Removed CATEGORIES

    def __init__(self, parent=None, service_data=None):
        super().__init__(parent)
        self.is_edit = service_data is not None
        self.service_data = service_data or {}
        
        title = "Edit Service" if self.is_edit else "Add New Service"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['bg_card']}; }}
            QLabel {{ color: {COLORS['text_primary']}; font-weight: 500; font-size: 13px; }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        
        self._build()
        if self.is_edit:
            self._populate()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Name
        layout.addWidget(QLabel("Service Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Standard Panaflex")
        layout.addWidget(self.name_input)
        
        # Price
        layout.addWidget(QLabel("Default Price *"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("0.00")
        layout.addWidget(self.price_input)
        
        # Description
        layout.addWidget(QLabel("Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional details...")
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = _btn("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = _btn("Save Service", primary=True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def _populate(self):
        self.name_input.setText(self.service_data.get("name", ""))
        self.price_input.setText(str(self.service_data.get("price", "0.0")))
        self.desc_input.setText(self.service_data.get("description", ""))

    def get_data(self) -> dict:
        price_str = self.price_input.text().strip()
        try:
            price = float(price_str)
        except ValueError:
            price = 0.0
            
        return {
            "category": "GENERAL",
            "name": self.name_input.text().strip(),
            "price": price,
            "description": self.desc_input.toPlainText().strip()
        }
