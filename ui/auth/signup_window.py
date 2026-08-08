from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QApplication, QFrame, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from ui.design_system import get_auth_stylesheet, COLORS
from ui.auth.setup_window import show_message, center_window, _field
import re


class SignupWindow(QWidget):
    """
    New-user registration screen.
    Can be reached from the Login screen at any time.
    """
    signup_successful = Signal()    # redirects to login
    back_to_login    = Signal()     # cancel → back

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RN Scanner – Create Account")
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

        icon = QLabel("👤")
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon)

        h = QLabel("Create New Account")
        h.setStyleSheet(
            f"font-size: 19px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;"
        )
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(h)

        sub = QLabel("Fill in the details below to register a new user")
        sub.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;"
        )
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(sub)
        cl.addSpacing(6)

        ul, self.u  = _field("Username",         "Choose a username")
        el, self.e  = _field("Email Address",    "e.g. user@company.com")
        pl, self.p  = _field("Password",         "Minimum 6 characters", True)
        cpl, self.cp = _field("Confirm Password","Re-enter password",    True)

        for lay in [ul, el, pl, cpl]:
            cl.addLayout(lay)

        cl.addSpacing(6)
        btn = QPushButton("Create Account")
        btn.setObjectName("success_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.clicked.connect(self._submit)
        cl.addWidget(btn)

        back = QPushButton("Back to Sign In")
        back.setObjectName("outline_btn")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setFixedHeight(40)
        back.clicked.connect(self.back_to_login.emit)
        cl.addWidget(back)

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
            show_message(self, "info", "Account Created",
                         f"Account '{username}' created successfully!\nYou can now sign in.")
            self.signup_successful.emit()
        except ValueError as ex:
            show_message(self, "error", "Registration Failed", str(ex))
