from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from ui.design_system import COLORS
from config.settings import LOGO_RN_SCANNER


def center_window(widget):
    screen = QApplication.primaryScreen().availableGeometry()
    x = (screen.width() - widget.width()) // 2
    y = (screen.height() - widget.height()) // 2
    widget.move(x, y)


class SplashScreen(QWidget):
    """Welcome/Branding splash screen shown at startup."""
    splash_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RN Scanner and Digital Print House")
        self.setMinimumSize(700, 400)
        self.resize(740, 420)
        # Normal window with min/max/close buttons
        center_window(self)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        self._build_ui()
        QTimer.singleShot(3000, self.on_done)

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # ── LEFT (blue) ──────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(240)
        left.setStyleSheet("background-color: #FFFFFF; border-right: 1px solid #E2E8F0;")
        lv = QVBoxLayout(left)
        lv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lv.setContentsMargins(24, 0, 24, 0)
        lv.setSpacing(10)

        # Try to show logo; fallback to text
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(LOGO_RN_SCANNER))
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(160, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("🖨️")
            logo_label.setStyleSheet("font-size: 48px; background: transparent;")
        logo_label.setStyleSheet("background: transparent;")
        lv.addWidget(logo_label)

        side_title = QLabel("RN Scanner")
        side_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_title.setStyleSheet("color: #0f172a; font-size: 18px; font-weight: 700; background: transparent;")
        lv.addWidget(side_title)

        side_sub = QLabel("Business Suite")
        side_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_sub.setStyleSheet("color: #1e293b; font-size: 12px; font-weight: 600; background: transparent;")
        lv.addWidget(side_sub)

        h.addWidget(left)

        # ── RIGHT (white) ────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background-color: {COLORS['bg_card']};")
        rv = QVBoxLayout(right)
        rv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rv.setContentsMargins(44, 36, 44, 28)
        rv.setSpacing(0)

        brand = QLabel("RN Scanner & Digital Print House")
        brand.setStyleSheet(f"color: {COLORS['primary']}; font-size: 22px; font-weight: 800; background: transparent;")
        brand.setWordWrap(True)
        brand.setAlignment(Qt.AlignmentFlag.AlignLeft)
        rv.addWidget(brand)

        tagline = QLabel("Professional Print, Scanning & Digital Services")
        tagline.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; background: transparent; margin-top: 4px;")
        tagline.setWordWrap(True)
        rv.addWidget(tagline)

        rv.addSpacing(22)
        div1 = QLabel(); div1.setFixedHeight(1)
        div1.setStyleSheet(f"background-color: {COLORS['divider']};")
        rv.addWidget(div1)
        rv.addSpacing(18)

        for dot_col, name, detail in [
            (COLORS['primary'], "RN Scanner and Digital Print House",
             "Professional Print & Scanning Services"),
            (COLORS['primary'], "K Dynamics (PRIVATE) LIMITED",
             "Digital Printing  •  Pana Flex  •  Giveaways  •  Wedding Cards"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {dot_col}; font-size: 9px; background: transparent;")
            dot.setFixedWidth(14)
            row.addWidget(dot)
            nm = QLabel(name)
            nm.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600; background: transparent;")
            nm.setWordWrap(True)
            row.addWidget(nm)
            row.addStretch()
            rv.addLayout(row)

            dt = QLabel(detail)
            dt.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; margin-left: 22px; margin-bottom: 10px;")
            dt.setWordWrap(True)
            rv.addWidget(dt)

        rv.addSpacing(8)
        div2 = QLabel(); div2.setFixedHeight(1)
        div2.setStyleSheet(f"background-color: {COLORS['divider']};")
        rv.addWidget(div2)
        rv.addSpacing(12)

        bottom = QHBoxLayout()
        loading = QLabel("Initializing, please wait…")
        loading.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        version = QLabel("v1.0.0")
        version.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        bottom.addWidget(loading)
        bottom.addStretch()
        bottom.addWidget(version)
        rv.addLayout(bottom)

        h.addWidget(right)

    def on_done(self):
        self.splash_done.emit()
        self.close()
