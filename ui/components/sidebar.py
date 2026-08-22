from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSizePolicy, QLabel, QWidget
from PySide6.QtCore import Qt, Signal
from ui.design_system import COLORS


class SidebarBtn(QPushButton):
    """Custom sidebar navigation button."""
    def __init__(self, icon: str, text: str, page_name: str, is_subitem: bool = False):
        super().__init__(f"{icon}   {text}")
        self.page_name = page_name
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        # Left-align text with padding
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 0px;
                padding-left: {32 if is_subitem else 16}px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['primary']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['primary']};
                color: #FFFFFF;
                font-weight: 600;
            }}
        """)


class CollapsibleSection(QWidget):
    toggled = Signal()

    def __init__(self, title: str, icon: str, items: list, parent=None):
        super().__init__(parent)
        self.items = items
        self.buttons = []
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        self.toggle_btn = QPushButton(f"{icon}   {title}  ▼")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedHeight(44)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 0px;
                padding-left: 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['primary']};
            }}
            QPushButton:checked {{
                color: {COLORS['primary']};
            }}
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        self.layout.addWidget(self.toggle_btn)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)
        
        for icon_str, text, page in self.items:
            btn = SidebarBtn(icon_str, text, page, is_subitem=True)
            self.buttons.append(btn)
            self.content_layout.addWidget(btn)
            
        self.layout.addWidget(self.content_widget)
        
        self.is_expanded = False
        self.content_widget.setVisible(False)
        
    def toggle(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        if self.is_expanded:
            self.toggle_btn.setText(self.toggle_btn.text().replace("▼", "▲"))
        else:
            self.toggle_btn.setText(self.toggle_btn.text().replace("▲", "▼"))
        self.toggled.emit()

    def collapse(self):
        if self.is_expanded:
            self.toggle()


class Sidebar(QFrame):
    """Application Sidebar Navigation."""
    nav_clicked = Signal(str)  # Emits the page_name to navigate to

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {COLORS['bg_card']};
                border-right: 1px solid {COLORS['border_card']};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QWidget#scroll_content {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 0px;
                background: transparent;
            }}
        """)
        self._buttons = []
        self._sections = []
        self._build()

    def _build(self):
        from PySide6.QtWidgets import QScrollArea

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("scroll_content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 24, 16, 8)
        layout.setSpacing(6)

        # Title / Brand area in sidebar
        brand = QLabel("Main Menu")
        brand.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 700; text-transform: uppercase; padding-left: 8px;")
        layout.addWidget(brand)
        layout.addSpacing(12)

        # Standalone items
        dash_btn = SidebarBtn("📊", "Dashboard", "dashboard")
        dash_btn.clicked.connect(lambda checked, b=dash_btn: self._on_nav_click(b))
        self._buttons.append(dash_btn)
        layout.addWidget(dash_btn)
        
        serv_btn = SidebarBtn("🏷️", "Services", "services")
        serv_btn.clicked.connect(lambda checked, b=serv_btn: self._on_nav_click(b))
        self._buttons.append(serv_btn)
        layout.addWidget(serv_btn)

        # Customers Section
        cust_items = [
            ("👥", "Customers", "customers"),
            ("📄", "Invoices", "invoices"),
            ("📖", "Customer Ledger", "ledger"),
            ("📝", "Quotations", "quotations")
        ]
        cust_section = CollapsibleSection("Customers", "👥", cust_items)
        for b in cust_section.buttons:
            b.clicked.connect(lambda checked, btn=b: self._on_nav_click(btn))
            self._buttons.append(b)
        self._sections.append(cust_section)
        layout.addWidget(cust_section)

        # Vendors Section
        vend_items = [
            ("🏢", "Vendors", "vendors"),
            ("🧾", "Bills", "vendor_bills")
        ]
        vend_section = CollapsibleSection("Vendors", "🏢", vend_items)
        for b in vend_section.buttons:
            b.clicked.connect(lambda checked, btn=b: self._on_nav_click(btn))
            self._buttons.append(b)
        self._sections.append(vend_section)
        layout.addWidget(vend_section)
        
        # Employees Section
        emp_items = [
            ("👤", "Employee Salaries", "employees")
        ]
        emp_section = CollapsibleSection("Employees", "👤", emp_items)
        for b in emp_section.buttons:
            b.clicked.connect(lambda checked, btn=b: self._on_nav_click(btn))
            self._buttons.append(b)
        self._sections.append(emp_section)
        layout.addWidget(emp_section)

        # Day Book Section
        db_btn = SidebarBtn("📓", "Day Book", "day_book")
        db_btn.clicked.connect(lambda checked, b=db_btn: self._on_nav_click(b))
        self._buttons.append(db_btn)
        layout.addWidget(db_btn)

        def on_section_toggled(active_sec):
            if active_sec.is_expanded:
                for sec in self._sections:
                    if sec != active_sec:
                        sec.collapse()

        cust_section.toggled.connect(lambda: on_section_toggled(cust_section))
        vend_section.toggled.connect(lambda: on_section_toggled(vend_section))
        emp_section.toggled.connect(lambda: on_section_toggled(emp_section))

        # Removed History section

        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Bottom Items (Fixed at bottom)
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(16, 8, 16, 24)
        bottom_layout.setSpacing(6)
        
        bottom_items = [
            ("💾", "Backup", "backup"),
            ("⚙️", "Settings", "settings"),
        ]
        
        for icon, text, page in bottom_items:
            btn = SidebarBtn(icon, text, page)
            btn.clicked.connect(lambda checked, b=btn: self._on_nav_click(b))
            self._buttons.append(btn)
            bottom_layout.addWidget(btn)
            
        main_layout.addLayout(bottom_layout)
            
        # Select first item by default
        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_nav_click(self, clicked_btn: SidebarBtn):
        # Uncheck all other buttons
        for btn in self._buttons:
            if btn != clicked_btn:
                btn.setChecked(False)
            else:
                btn.setChecked(True)
        self.nav_clicked.emit(clicked_btn.page_name)
        
    def set_active(self, page_name: str):
        """Programmatically set the active sidebar button."""
        for btn in self._buttons:
            if btn.page_name == page_name:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
