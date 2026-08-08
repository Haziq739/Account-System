from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QRadioButton, QButtonGroup, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from ui.design_system import COLORS, set_theme_preference, get_theme_preference

class SettingsPage(QWidget):
    theme_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"QWidget {{ background-color: {COLORS['bg_app']}; }}")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        # Appearance Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        section_title = QLabel("Appearance")
        section_title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;")
        card_layout.addWidget(section_title)

        desc = QLabel("Choose how the application looks to you.")
        desc.setStyleSheet(f"font-size: 13px; color: {COLORS['text_muted']}; background: transparent;")
        card_layout.addWidget(desc)

        # Theme Radio Buttons
        self.theme_group = QButtonGroup(self)
        
        self.light_btn = QRadioButton("Light Mode (Professional White)")
        self.light_btn.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; background: transparent;")
        
        self.dark_btn = QRadioButton("Dark Mode (Slate)")
        self.dark_btn.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; background: transparent;")

        self.theme_group.addButton(self.light_btn)
        self.theme_group.addButton(self.dark_btn)

        # Set initial checked based on preference
        current_theme = get_theme_preference()
        if current_theme == "dark":
            self.dark_btn.setChecked(True)
        else:
            self.light_btn.setChecked(True)

        card_layout.addWidget(self.light_btn)
        card_layout.addWidget(self.dark_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primary_btn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']}; 
                color: white; 
                border: 2px solid transparent; 
                border-radius: 6px; 
                font-weight: bold;
            }}
            QPushButton:focus {{
                border: 2px solid #60A5FA;
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        save_btn.clicked.connect(self._save_settings)
        card_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(card)
        layout.addStretch()

    def _save_settings(self):
        new_theme = "dark" if self.dark_btn.isChecked() else "light"
        current_theme = get_theme_preference()
        
        if new_theme != current_theme:
            set_theme_preference(new_theme)
            from ui.design_system import init_theme
            init_theme()
            self.theme_changed.emit()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Settings")
            msg.setText("Settings saved.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
