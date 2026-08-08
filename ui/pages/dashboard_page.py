from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt
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
        
        # Grid for cards
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Currently using placeholders; will connect to DB in future phases
        c1 = DashboardCard("Total Sales", "Rs. 0", "💰", COLORS['primary'])
        c2 = DashboardCard("Today's Sales", "Rs. 0", "📈", COLORS['success'])
        c3 = DashboardCard("Total Customers", "0", "👥", "#F59E0B")  # amber
        c4 = DashboardCard("Pending Payments", "Rs. 0", "⏳", "#EF4444") # red
        
        grid.addWidget(c1, 0, 0)
        grid.addWidget(c2, 0, 1)
        grid.addWidget(c3, 1, 0)
        grid.addWidget(c4, 1, 1)
        
        root.addLayout(grid)
        
        # Recent Invoices Section (Placeholder)
        root.addSpacing(16)
        inv_title = QLabel("Recent Invoices")
        inv_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: 600;")
        root.addWidget(inv_title)
        
        empty_state = QFrame()
        empty_state.setObjectName("card")
        empty_state.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px dashed {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        empty_state.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        el = QVBoxLayout(empty_state)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel("No invoices found for this company yet.")
        msg.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; background: transparent;")
        el.addWidget(msg)
        
        root.addWidget(empty_state)
        
    def set_company(self, company_id: int):
        """Called when company dropdown changes in the header."""
        self.company_id = company_id
        # In the future, this will refresh the dashboard stats by querying the DB
