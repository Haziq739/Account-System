import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QComboBox, 
    QVBoxLayout, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from ui.design_system import COLORS
from config.settings import ASSETS_DIR
from database.session import SessionLocal
from models.company import Company


class Header(QFrame):
    """Top header bar containing active company selection and user profile."""
    company_changed = Signal(int)  # Emits company ID when changed

    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.setObjectName("header")
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QFrame#header {{
                background-color: {COLORS['bg_card']};
                border-bottom: 1px solid {COLORS['border_card']};
            }}
            QComboBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                color: {COLORS['text_primary']};
                min-width: 240px;
            }}
            QComboBox:drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_card']};
                selection-background-color: {COLORS['bg_input']};
                selection-color: {COLORS['primary']};
                border: 1px solid {COLORS['border_card']};
                outline: none;
            }}
        """)
        
        self.companies = []
        self._load_companies()
        self._build()
        self._update_logo()

    def _load_companies(self):
        with SessionLocal() as s:
            # Load all companies into memory
            rows = s.query(Company).all()
            for r in rows:
                self.companies.append({
                    "id": r.id,
                    "name": r.name,
                    "logo_path": r.logo_path
                })

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # ── Left: Logo ──────────────────────────────────────────────────
        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(60, 44)
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self.logo_lbl)
        
        # ── Middle: Company Dropdown ────────────────────────────────────
        col = QVBoxLayout()
        col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        col.setSpacing(2)
        
        lbl = QLabel("Active Company:")
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        col.addWidget(lbl)
        
        self.company_combo = QComboBox()
        for comp in self.companies:
            self.company_combo.addItem(comp["name"], userData=comp)
            
        self.company_combo.currentIndexChanged.connect(self._on_combo_change)
        col.addWidget(self.company_combo)
        
        layout.addLayout(col)
        layout.addStretch()

        # ── Right: User Info ────────────────────────────────────────────
        user_col = QVBoxLayout()
        user_col.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        user_col.setSpacing(2)
        
        u_name = QLabel(self.current_user.get("username", "Admin"))
        u_name.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 13px; background: transparent;")
        u_name.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_col.addWidget(u_name)
        
        role = QLabel(self.current_user.get("role", "Owner").capitalize())
        role.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        role.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_col.addWidget(role)
        
        layout.addLayout(user_col)

    def _on_combo_change(self, index: int):
        self._update_logo()
        comp = self.company_combo.currentData()
        if comp:
            self.company_changed.emit(comp["id"])

    def _update_logo(self):
        comp = self.company_combo.currentData()
        if not comp or not comp.get("logo_path"):
            self.logo_lbl.setText("🏢")
            self.logo_lbl.setStyleSheet("font-size: 24px; background: transparent;")
            return
            
        logo_file = ASSETS_DIR / comp["logo_path"]
        pix = QPixmap(str(logo_file))
        if not pix.isNull():
            self.logo_lbl.setPixmap(pix.scaled(60, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.logo_lbl.setStyleSheet("background: transparent;")
        else:
            self.logo_lbl.setText("🏢")
            self.logo_lbl.setStyleSheet("font-size: 24px; background: transparent;")
