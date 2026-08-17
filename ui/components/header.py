import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QVBoxLayout, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from ui.design_system import COLORS
from config.settings import ASSETS_DIR
from database.session import SessionLocal
from models.company import Company


class CompanyWidget(QFrame):
    """Clickable logo + text container for a single company."""
    clicked = Signal(int)
    
    def __init__(self, comp_id: int, name: str, logo_path: str):
        super().__init__()
        self.comp_id = comp_id
        self.setObjectName("comp_widget")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(56)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        
        # Logo
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(50, 44)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if logo_path:
            full_path = ASSETS_DIR / logo_path
            pix = QPixmap(str(full_path))
            if not pix.isNull():
                logo_lbl.setPixmap(pix.scaled(50, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_lbl)
        
        # Text
        text_lbl = QLabel(name)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(text_lbl)
        
        # Default inactive state
        self.set_active(False)
        
    def set_active(self, is_active: bool):
        if is_active:
            self.setStyleSheet(f"""
                QFrame#comp_widget {{
                    background-color: {COLORS['bg_input']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#comp_widget {{
                    background-color: transparent;
                    border: 2px solid transparent;
                    border-radius: 8px;
                }}
                QFrame#comp_widget:hover {{
                    background-color: {COLORS['bg_card']};
                    border: 2px solid {COLORS['border_card']};
                }}
            """)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.comp_id)
        super().mousePressEvent(event)


class Header(QFrame):
    """Top header bar containing horizontal company switcher and user profile."""
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
        """)
        
        self.companies = []
        self.company_widgets = {}
        
        self._load_companies()
        self._build()

    def _load_companies(self):
        with SessionLocal() as s:
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
        layout.setSpacing(24)

        # ── Left/Middle: Horizontal Company Switcher ────────────────────
        comps_layout = QHBoxLayout()
        comps_layout.setSpacing(24)
        
        # Determine explicit ordering: RN Scanner first
        rn_comp = next((c for c in self.companies if "RN Scanner" in c["name"]), None)
        k_comp = next((c for c in self.companies if "K Dynamics" in c["name"]), None)
        
        sorted_comps = []
        if rn_comp: sorted_comps.append(rn_comp)
        if k_comp: sorted_comps.append(k_comp)
        for c in self.companies:
            if c not in sorted_comps:
                sorted_comps.append(c)

        # Build custom clickable widgets
        for comp in sorted_comps:
            cw = CompanyWidget(comp["id"], comp["name"], comp["logo_path"])
            cw.clicked.connect(self._on_company_clicked)
            comps_layout.addWidget(cw)
            self.company_widgets[comp["id"]] = cw
            
        layout.addLayout(comps_layout)
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

    def _on_company_clicked(self, comp_id: int):
        """User clicked a company logo/text."""
        self.set_active_company(comp_id)
        self.company_changed.emit(comp_id)

    def set_active_company(self, comp_id: int):
        """Visually updates the active company without emitting signals."""
        for cid, widget in self.company_widgets.items():
            widget.set_active(cid == comp_id)

