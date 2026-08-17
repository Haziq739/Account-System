from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialog, QApplication, QFrame,
    QHBoxLayout, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from ui.design_system import get_auth_stylesheet, COLORS
import re


# ── Helpers ───────────────────────────────────────────────────────────────────

def center_window(widget):
    """Center widget on the primary screen."""
    geo = QApplication.primaryScreen().availableGeometry()
    widget.move(
        (geo.width()  - widget.width())  // 2,
        (geo.height() - widget.height()) // 2,
    )


def _field(label_text: str, placeholder: str, is_password: bool = False):
    """Returns (QVBoxLayout, QLineEdit) — a labelled input."""
    col = QVBoxLayout()
    col.setSpacing(5)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(
        f"color: {COLORS['text_secondary']}; font-size: 12px; "
        f"font-weight: 600; background: transparent;"
    )
    col.addWidget(lbl)
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    inp.setFixedHeight(40)
    inp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    if is_password:
        inp.setEchoMode(QLineEdit.EchoMode.Password)
    col.addWidget(inp)
    return col, inp


# Keep old name for compatibility
_make_field = _field


def show_message(parent, kind: str, title: str, text: str):
    """
    Show a compact, properly-styled notification dialog.
    Replaces QMessageBox to avoid the wide/misaligned default.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dlg.setMinimumWidth(320)
    dlg.setMaximumWidth(400)
    dlg.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    dlg.setStyleSheet(f"""
        QDialog {{
            background-color: {COLORS['bg_card']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QLabel#icon_lbl {{
            font-size: 28px;
            background: transparent;
        }}
        QLabel#msg_lbl {{
            color: {COLORS['text_primary']};
            font-size: 13px;
            background: transparent;
        }}
        QPushButton {{
            background-color: {COLORS['primary']};
            color: #FFFFFF;
            border: none;
            border-radius: 7px;
            padding: 9px 28px;
            font-size: 13px;
            font-weight: 600;
            min-width: 80px;
        }}
        QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}
    """)

    icons = {"info": "✅", "warning": "⚠️", "error": "❌"}
    icon_str = icons.get(kind, "ℹ️")

    root = QVBoxLayout(dlg)
    root.setContentsMargins(24, 20, 24, 20)
    root.setSpacing(14)

    # Icon
    icon_lbl = QLabel(icon_str)
    icon_lbl.setObjectName("icon_lbl")
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    root.addWidget(icon_lbl)

    # Message
    msg_lbl = QLabel(text)
    msg_lbl.setObjectName("msg_lbl")
    msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    msg_lbl.setWordWrap(True)
    root.addWidget(msg_lbl)

    # OK button
    ok_btn = QPushButton("OK")
    ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    ok_btn.clicked.connect(dlg.accept)
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    btn_row.addWidget(ok_btn)
    btn_row.addStretch()
    root.addLayout(btn_row)

    dlg.adjustSize()
    center_window(dlg)
    dlg.exec()

def show_duplicate_message(parent):
    """
    Shows a 'Duplicates found' message with only a Cancel button.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle("Duplicates found")
    dlg.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dlg.setMinimumWidth(320)
    dlg.setMaximumWidth(400)
    
    dlg.setStyleSheet(f"""
        QDialog {{
            background-color: {COLORS['bg_card']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QLabel#icon_lbl {{
            font-size: 28px;
            background: transparent;
        }}
        QLabel#msg_lbl {{
            color: {COLORS['text_primary']};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
        }}
        QPushButton {{
            background-color: {COLORS['bg_input']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 7px;
            padding: 9px 28px;
            font-size: 13px;
            font-weight: 600;
            min-width: 80px;
        }}
        QPushButton:hover {{ background-color: #E2E8F0; }}
    """)
    
    root = QVBoxLayout(dlg)
    root.setContentsMargins(24, 20, 24, 20)
    root.setSpacing(14)
    
    icon_lbl = QLabel("⚠️")
    icon_lbl.setObjectName("icon_lbl")
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    root.addWidget(icon_lbl)
    
    msg_lbl = QLabel("Duplicates found")
    msg_lbl.setObjectName("msg_lbl")
    msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    root.addWidget(msg_lbl)
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel_btn.clicked.connect(dlg.reject)
    
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    btn_row.addWidget(cancel_btn)
    btn_row.addStretch()
    root.addLayout(btn_row)
    
    dlg.adjustSize()
    center_window(dlg)
    dlg.exec()

def handle_duplicate_error(parent, e: Exception) -> bool:
    """Checks if exception is a duplicate error, shows the dialog if so, and returns True."""
    if isinstance(e, ValueError) and str(e) == "Duplicates found":
        show_duplicate_message(parent)
        return True
    return False

# ── Setup Window (First-run) ───────────────────────────────────────────────────

class SetupWindow(QWidget):
    """First-time owner account creation (shown only when DB is empty)."""
    setup_successful = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RN Scanner – Initial Setup")
        self.setMinimumSize(460, 560)
        self.resize(460, 580)
        center_window(self)
        self.setStyleSheet(get_auth_stylesheet())
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(36, 30, 36, 30)
        cl.setSpacing(12)

        icon = QLabel("🔐")
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon)

        h = QLabel("Create Admin Account")
        h.setStyleSheet(f"font-size: 19px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(h)

        sub = QLabel("One-time setup — you can add more users later")
        sub.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(sub)

        cl.addSpacing(6)

        ul, self.u = _field("Username", "Choose a username")
        cl.addLayout(ul)
        el, self.e = _field("Email Address", "e.g. owner@company.com")
        cl.addLayout(el)
        pl, self.p = _field("Password", "Minimum 6 characters", True)
        cl.addLayout(pl)
        cpl, self.cp = _field("Confirm Password", "Re-enter password", True)
        cl.addLayout(cpl)

        cl.addSpacing(6)
        btn = QPushButton("Create Account")
        btn.setObjectName("success_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.clicked.connect(self._submit)
        cl.addWidget(btn)

        outer.addWidget(card)

    def _submit(self):
        from services.auth import AuthService
        username = self.u.text().strip()
        email    = self.e.text().strip()
        pw       = self.p.text()
        cpw      = self.cp.text()

        if not all([username, email, pw, cpw]):
            show_message(self, "warning", "Validation", "All fields are required.")
            return
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            show_message(self, "warning", "Validation", "Please enter a valid email address.")
            return
        if pw != cpw:
            show_message(self, "warning", "Validation", "Passwords do not match.")
            return
        if len(pw) < 6:
            show_message(self, "warning", "Validation", "Password must be at least 6 characters.")
            return
        try:
            AuthService.create_user(username, email, pw)
            show_message(self, "info", "Success", "Account created successfully!\nYou can now sign in.")
            self.setup_successful.emit()
        except ValueError as e:
            show_message(self, "error", "Error", str(e))
