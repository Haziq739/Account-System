from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt
from ui.design_system import get_auth_stylesheet, COLORS
from ui.auth.setup_window import show_message, _field


class ForgotPasswordDialog(QDialog):
    """Password reset via registered email — independent top-level dialog."""

    def __init__(self, parent=None):
        super().__init__(None)   # None → not constrained by any parent
        self.setWindowTitle("Reset Password")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setMinimumSize(400, 480)
        self.resize(420, 500)
        geo = QApplication.primaryScreen().availableGeometry()
        self.move((geo.width()-self.width())//2, (geo.height()-self.height())//2)
        self.setStyleSheet(get_auth_stylesheet())
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(12)

        icon = QLabel("🔑")
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon)

        h = QLabel("Reset Password")
        h.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;"
        )
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(h)

        sub = QLabel("Enter your email and choose a new password")
        sub.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        cl.addWidget(sub)
        cl.addSpacing(6)

        el,  self.email   = _field("Registered Email",   "Enter registered email")
        pl,  self.new_pw  = _field("New Password",       "Minimum 6 characters", True)
        cpl, self.conf_pw = _field("Confirm New Password","Re-enter new password", True)
        for lay in [el, pl, cpl]:
            cl.addLayout(lay)

        cl.addSpacing(6)
        btn = QPushButton("Reset Password")
        btn.setObjectName("primary_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.clicked.connect(self._reset)
        cl.addWidget(btn)

        root.addWidget(card)

    def _reset(self):
        from services.auth import AuthService
        email  = self.email.text().strip()
        new_pw = self.new_pw.text()
        conf   = self.conf_pw.text()

        if not email or not new_pw or not conf:
            show_message(self, "warning", "Validation", "All fields are required.")
            return
        if new_pw != conf:
            show_message(self, "warning", "Validation", "Passwords do not match.")
            return
        if len(new_pw) < 6:
            show_message(self, "warning", "Validation", "Password must be at least 6 characters.")
            return
        if not AuthService.verify_email(email):
            show_message(self, "error", "Not Found",
                         "No account found with that email.\nPlease check and try again.")
            return
        if AuthService.reset_password(email, new_pw):
            show_message(self, "info", "Password Reset",
                         "Password reset successfully.\nYou can now sign in with the new password.")
            self.accept()
        else:
            show_message(self, "error", "Error", "Password reset failed. Please try again.")
