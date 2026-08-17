from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QGridLayout, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, Signal
from ui.design_system import COLORS


class DashboardCard(QFrame):
    """Reusable card for displaying summary statistics."""
    def __init__(self, title: str, value: str, icon: str, color_theme: str):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header (Title + Icon)
        h_layout = QHBoxLayout()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 600; background: transparent;")
        
        i_lbl = QLabel(icon)
        i_lbl.setStyleSheet(f"color: {color_theme}; font-size: 20px; background: transparent;")
        i_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        h_layout.addWidget(t_lbl)
        h_layout.addStretch()
        h_layout.addWidget(i_lbl)
        
        layout.addLayout(h_layout)
        
        # Value
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 28px; font-weight: 800; background: transparent;")
        layout.addWidget(v_lbl)
        
        # Footer / subtitle could go here if needed
        layout.addStretch()


class DashboardPage(QWidget):
    """Main dashboard content view."""
    action_requested = Signal(str)
    
    def __init__(self, company_id: int):
        super().__init__()
        self.company_id = company_id
        self._build()
        
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)
        
        # Page Title
        title = QLabel("Dashboard Overview")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700;")
        root.addWidget(title)
        
        # Summary cards have been removed as per requirement
        
        # Quick Actions Section
        root.addSpacing(16)
        qa_title = QLabel("Quick Actions")
        qa_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: 600;")
        root.addWidget(qa_title)
        
        qa_grid = QGridLayout()
        qa_grid.setSpacing(20)
        
        # Row 1
        qa_grid.addWidget(self._create_quick_btn("📄 Create Invoice", "create_invoice"), 0, 0)
        qa_grid.addWidget(self._create_quick_btn("👥 Add Customer", "add_customer"), 0, 1)
        qa_grid.addWidget(self._create_quick_btn("📝 Create Quotation", "create_quotation"), 0, 2)
        qa_grid.addWidget(self._create_quick_btn("📖 Day Book", "open_day_book"), 0, 3)
        
        # Row 2
        qa_grid.addWidget(self._create_quick_btn("💳 Add Expense", "add_expense"), 1, 0)
        qa_grid.addWidget(self._create_quick_btn("🏢 Create Vendor Bill", "create_vendor_bill"), 1, 1)
        qa_grid.addWidget(self._create_quick_btn("👷 Add Employee", "add_employee"), 1, 2)
        qa_grid.addWidget(self._create_quick_btn("💾 Create Backup", "create_backup"), 1, 3)
        
        # Row 3
        qa_grid.addWidget(self._create_quick_btn("💰 Add Payment", "add_payment"), 2, 0)
        qa_grid.addWidget(self._create_quick_btn("📦 Add Service", "add_service"), 2, 1)
        qa_grid.addWidget(self._create_quick_btn("🤝 Add Vendor", "add_vendor"), 2, 2)
        
        root.addLayout(qa_grid)
        
        # Push everything to the top
        root.addStretch()
        
    def _create_quick_btn(self, text: str, action: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(70)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
                padding: 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: white;
                border: 1px solid {COLORS['primary']};
            }}
        """)
        btn.clicked.connect(lambda _, a=action: self.action_requested.emit(a))
        return btn
        
    def set_company(self, company_id: int):
        """Called when company dropdown changes in the header."""
        self.company_id = company_id
        # In the future, this will refresh the dashboard stats by querying the DB
