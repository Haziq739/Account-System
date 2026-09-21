from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QGridLayout, QComboBox, QCheckBox, QWidget, QTextEdit, QFrame, QListView
)
from PySide6.QtCore import Qt
from ui.design_system import COLORS
from ui.auth.setup_window import show_message

class ServiceDetailsDialog(QDialog):
    def __init__(self, parent, is_new_service: bool, service_name: str, default_price: float = 0.0, default_desc: str = ""):
        super().__init__(parent)
        self.is_new_service = is_new_service
        self.service_name = service_name
        
        self.setWindowTitle("Service Details")
        self.setMinimumWidth(850)
        self.setObjectName("ServiceDetailsDialog")
        
        self.setStyleSheet(f"""
            QDialog#ServiceDetailsDialog {{ 
                background-color: {COLORS['bg_app']}; 
                border-radius: 10px; 
                border: 1px solid {COLORS['border']}; 
            }}
            QFrame#HeaderFrame {{
                background-color: {COLORS['primary']}15; /* 15% opacity primary color */
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {COLORS['primary']}40;
            }}
            QFrame#CardFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 8px;
                border: 1px solid {COLORS['border_card']};
            }}
            QLabel {{ 
                color: {COLORS['text_primary']}; 
                font-weight: 600; 
                font-size: 13px; 
            }}
            QLabel#TitleLabel {{
                color: {COLORS['primary']}; 
                font-size: 18px; 
                font-weight: 800;
            }}
            QLabel#SectionHeader {{
                color: {COLORS['text_primary']}; 
                font-size: 15px; 
                font-weight: 700;
                margin-bottom: 5px;
            }}
            QLineEdit, QTextEdit, QComboBox {{ 
                background-color: {COLORS['bg_input']}; 
                border: 1px solid {COLORS['border']}; 
                border-radius: 6px; 
                padding: 8px 10px; 
                color: {COLORS['text_primary']}; 
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ 
                border: 1px solid {COLORS['primary']}; 
                background-color: {COLORS['bg_card']};
            }}
            
            
            QPushButton {{ 
                padding: 10px 20px; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 13px; 
            }}
            QPushButton#outline_btn {{ 
                background-color: {COLORS['bg_card']}; 
                border: 1px solid {COLORS['border']}; 
                color: {COLORS['text_primary']}; 
            }}
            QPushButton#outline_btn:hover {{ 
                background-color: #EFF6FF; 
                border: 1px solid {COLORS['primary']}; 
                color: {COLORS['primary']}; 
            }}
            QPushButton#primary_btn {{ 
                background-color: {COLORS['primary']}; 
                color: white; 
                border: none; 
            }}
            QPushButton#primary_btn:hover {{ 
                background-color: #1d4ed8; 
            }}
            QCheckBox {{ 
                color: {COLORS['text_primary']}; 
                font-weight: 500; 
                font-size: 13px; 
            }}
            
            
            
        """)
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- HEADER ---
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(25, 20, 25, 20)
        
        title_str = f"✨ Add New Service: {service_name}" if is_new_service else f"✏️ Edit Service Details: {service_name}"
        title = QLabel(title_str)
        title.setObjectName("TitleLabel")
        header_layout.addWidget(title)
        layout.addWidget(header_frame)
        
        # --- MAIN CONTENT AREA ---
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)
        
        # Main Split
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)
        
        # --- LEFT SIDE (Card) ---
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)
        
        basic_info_lbl = QLabel("Basic Information")
        basic_info_lbl.setObjectName("SectionHeader")
        left_layout.addWidget(basic_info_lbl)
        
        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border_card']}; border: none; max-height: 1px;")
        left_layout.addWidget(sep)
        
        left_layout.addWidget(QLabel("Default Price *" if is_new_service else "Unit Price *"))
        self.price_input = QLineEdit()
        self.price_input.setText(str(default_price) if default_price else "")
        self.price_input.setPlaceholderText("0.00")
        left_layout.addWidget(self.price_input)
        
        left_layout.addWidget(QLabel("Base Description (Optional)"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description here...")
        self.desc_input.setText(default_desc)
        left_layout.addWidget(self.desc_input)
        
        split_layout.addWidget(left_card, stretch=1)
        
        # --- RIGHT SIDE (Card) ---
        right_card = QFrame()
        right_card.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)
        
        print_info_lbl = QLabel("Printing Details (Optional)")
        print_info_lbl.setObjectName("SectionHeader")
        right_layout.addWidget(print_info_lbl)
        
        # Separator line
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background-color: {COLORS['border_card']}; border: none; max-height: 1px;")
        right_layout.addWidget(sep2)
        
        self.detail_controls = []
        
        details_config = [
            ("No of pages", [str(i) for i in range(1, 501)]),
            ("Paper Type", ["80gsm", "90gsm", "100gsm", "113gsm", "128gsm", "150gsm", "170gsm"]),
            ("Title", ["210gsm", "250gsm", "300gsm", "350gsm"]),
            ("Title Pages of Book", ["2", "4"]),
            ("Type of Bind", ["Side pin gum bind", "Gum bind", "Center pin", "Sewing bind", "Hard bond bind"]),
            ("Spot UV", ["Title", "All Pages"]),
            ("Lamination", ["Matt", "Shine"])
        ]
        
        def _fix_combo(cb):
            cb.setMaxVisibleItems(7)
            v = QListView()
            v.setStyleSheet(f"""
                QListView {{ outline: 0px; background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }}
                QListView::item {{ padding: 8px; border: none; }}
                QListView::item:selected, QListView::item:hover {{ background-color: {COLORS['primary']}; color: white; border: none; }}
            """)
            cb.setView(v)
        
        for label_text, options in details_config:
            row_layout = QHBoxLayout()
            cb = QCheckBox(label_text)
            cb.setFixedWidth(160)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(options)
            combo.setEnabled(False) # Disabled until checked
            _fix_combo(combo)
            
            cb.toggled.connect(combo.setEnabled)
            
            row_layout.addWidget(cb)
            row_layout.addWidget(combo, stretch=1)
            right_layout.addLayout(row_layout)
            
            self.detail_controls.append((label_text, cb, combo))
            
        right_layout.addStretch()
        split_layout.addWidget(right_card, stretch=1)
        
        content_layout.addLayout(split_layout)
        
        # --- BUTTONS ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("outline_btn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("OK, Save Details")
        self.btn_ok.setObjectName("primary_btn")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.clicked.connect(self.validate_and_accept)
        
        self.btn_cancel.setFixedSize(140, 42)
        self.btn_ok.setFixedSize(160, 42)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        content_layout.addLayout(btn_layout)
        
        layout.addLayout(content_layout)

    def validate_and_accept(self):
        if not self.price_input.text().strip():
            show_message(self, "error", "Validation Error", "Price is required.")
            return

        
        try:
            float(self.price_input.text().strip())
        except ValueError:
            show_message(self, "error", "Validation Error", "Invalid price amount.")
            return
            
        self.accept()
        
    def get_inputs(self):
        price = float(self.price_input.text().strip())
        
        base_desc = self.desc_input.toPlainText().strip()
        
        # Gather checked details
        extra_lines = []
        for label, cb, combo in self.detail_controls:
            if cb.isChecked():
                val = combo.currentText().strip()
                if val:
                    extra_lines.append(f"{label}: {val}")
                    
        final_desc = base_desc
        if extra_lines:
            if final_desc:
                final_desc += "\n" + "\n".join(extra_lines)
            else:
                final_desc = "\n".join(extra_lines)
            
        return price, final_desc
