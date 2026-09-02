from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from ui.design_system import get_auth_stylesheet, COLORS
from ui.auth.setup_window import show_message, center_window, _field


class LoginWindow(QWidget):
    """Main login screen with Sign In, Forgot Password, and Sign Up options."""
    login_successful = Signal(object)   # emits user dict
    go_signup        = Signal()         # navigate to signup screen

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RN Scanner – Sign In")
        self.setMinimumSize(420, 500)
        self.resize(440, 520)
        center_window(self)
        self.setStyleSheet(get_auth_stylesheet())
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(0)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(36, 30, 36, 30)
        cl.setSpacing(12)

        # Header
        icon = QLabel("🖨️")
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon)

        h = QLabel("Welcome Back")
        h.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;"
        )
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(h)

        sub = QLabel("Sign in to RN Scanner Business System")
        sub.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']}; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(sub)
        cl.addSpacing(6)

        # Fields
        ul, self.username = _field("Username", "Enter your username")
        cl.addLayout(ul)
        cl.addSpacing(12)

        pl, self.password = _field("Password", "Enter your password", True)
        cl.addLayout(pl)
        cl.addSpacing(8)

        # Forgot password link (right-aligned)
        fp_row = QHBoxLayout()
        fp_row.addStretch()
        fp_btn = QPushButton("Forgot Password?")
        fp_btn.setObjectName("link_btn")
        fp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fp_btn.setFixedHeight(22)
        fp_btn.clicked.connect(self._forgot)
        fp_row.addWidget(fp_btn)
        cl.addLayout(fp_row)

        cl.addSpacing(4)

        # Sign In button
        sign_in = QPushButton("Sign In")
        sign_in.setObjectName("primary_btn")
        sign_in.setCursor(Qt.CursorShape.PointingHandCursor)
        sign_in.setFixedHeight(44)
        sign_in.clicked.connect(self._login)
        cl.addWidget(sign_in)

        # Divider
        div_row = QHBoxLayout()
        div_row.setSpacing(8)
        l1 = QLabel(); l1.setFixedHeight(1)
        l1.setStyleSheet(f"background: {COLORS['divider']};")
        or_lbl = QLabel("or")
        or_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        or_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l2 = QLabel(); l2.setFixedHeight(1)
        l2.setStyleSheet(f"background: {COLORS['divider']};")
        div_row.addWidget(l1, 1)
        div_row.addWidget(or_lbl)
        div_row.addWidget(l2, 1)
        cl.addLayout(div_row)

        # Sign Up button
        signup_btn = QPushButton("Create New Account")
        signup_btn.setObjectName("outline_btn")
        signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_btn.setFixedHeight(40)
        signup_btn.clicked.connect(self.go_signup.emit)
        cl.addWidget(signup_btn)

        outer.addWidget(card)

        footer = QLabel("RN Scanner and Digital Print House  •  v1.0.2")
        footer.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; background: transparent; margin-top: 10px;"
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(footer)

    def _login(self):
        from services.auth import AuthService
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            show_message(self, "warning", "Missing Fields",
                         "Please enter both username and password.")
            return
        user = AuthService.login(username, password)
        if user:
            show_message(self, "info", "Login Successful",
                         f"Welcome back, {user['username']}!")
            self.login_successful.emit(user)
        else:
            show_message(self, "error", "Login Failed",
                         "Invalid username or password.\nPlease try again.")

    def _forgot(self):
        from ui.auth.forgot_password_dialog import ForgotPasswordDialog
        dlg = ForgotPasswordDialog()   # no parent → independent window
        dlg.exec()
