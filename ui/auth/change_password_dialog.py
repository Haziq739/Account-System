from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal
from ui.design_system import get_auth_stylesheet, COLORS
from ui.auth.setup_window import show_message, _field


class ChangePasswordDialog(QDialog):
    """Change password for a currently logged-in user."""
    password_changed = Signal()

    def __init__(self, user_id: int, parent=None):
        super().__init__(None)
        self.user_id = user_id
        self.setWindowTitle("Change Password")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setMinimumSize(400, 460)
        self.resize(420, 480)
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

        icon = QLabel("🔒")
        icon.setStyleSheet("font-size: 32px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon)

        h = QLabel("Change Password")
        h.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;"
        )
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(h)

        sub = QLabel("Enter your current password and choose a new one")
        sub.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        cl.addWidget(sub)
        cl.addSpacing(6)

        ol,  self.old_pw  = _field("Current Password",   "Enter current password", True)
        pl,  self.new_pw  = _field("New Password",       "Minimum 6 characters",  True)
        cpl, self.conf_pw = _field("Confirm New Password","Re-enter new password", True)
        for lay in [ol, pl, cpl]:
            cl.addLayout(lay)

        cl.addSpacing(6)
        btn = QPushButton("Update Password")
        btn.setObjectName("primary_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.clicked.connect(self._change)
        cl.addWidget(btn)

        root.addWidget(card)

    def _change(self):
        from services.auth import AuthService
        old = self.old_pw.text()
        new = self.new_pw.text()
        conf = self.conf_pw.text()

        if not old or not new or not conf:
            show_message(self, "warning", "Validation", "All fields are required.")
            return
        if new != conf:
            show_message(self, "warning", "Validation", "New passwords do not match.")
            return
        if len(new) < 6:
            show_message(self, "warning", "Validation", "New password must be at least 6 characters.")
            return
        if AuthService.change_password(self.user_id, old, new):
            show_message(self, "info", "Success", "Password changed successfully!\nPlease sign in with your new password.")
            self.password_changed.emit()
            self.accept()
        else:
            show_message(self, "error", "Failed", "Current password is incorrect.")
