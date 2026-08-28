from PySide6.QtWidgets import QComboBox, QListWidget, QWidget, QVBoxLayout, QFrame, QListWidgetItem, QApplication
from PySide6.QtCore import Qt, QPoint

class CustomComboBox(QComboBox):
    """
    A custom combo box that implements its own popup window to completely bypass 
    PySide6/Qt's broken native Windows 11 dropdown layout engine when using CSS.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup = None
        self._items = []
        self._data = []
        
        # Override native addItem/addItems so we can track data natively
        
    def addItem(self, text, userData=None):
        super().addItem(text, userData)
        self._items.append(text)
        self._data.append(userData)
        
    def addItems(self, texts):
        super().addItems(texts)
        for t in texts:
            self._items.append(t)
            self._data.append(None)
            
    def clear(self):
        super().clear()
        self._items.clear()
        self._data.clear()
        
    def hidePopup(self):
        super().hidePopup()
        if self.popup:
            self.popup.hide()
            
    def showPopup(self):
        if self.count() == 0:
            return
            
        if not self.popup:
            self.popup = QWidget(self.window(), Qt.Popup | Qt.FramelessWindowHint)
            self.popup.setAttribute(Qt.WA_TranslucentBackground)
            
            layout = QVBoxLayout(self.popup)
            layout.setContentsMargins(0, 0, 0, 0)
            
            self.frame = QFrame(self.popup)
            from ui.design_system import COLORS
            self.frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                }}
            """)
            frame_layout = QVBoxLayout(self.frame)
            frame_layout.setContentsMargins(0, 0, 0, 0)
            
            self.list_widget = QListWidget(self.frame)
            self.list_widget.setStyleSheet(f"""
                QListWidget {{
                    border: none;
                    background-color: transparent;
                    outline: none;
                }}
                QListWidget::item {{
                    min-height: 35px;
                    padding: 0px 8px;
                    color: {COLORS['text_primary']};
                }}
                QListWidget::item:hover {{
                    background-color: {COLORS['primary']};
                    color: white;
                }}
                QListWidget::item:selected {{
                    background-color: transparent;
                    color: {COLORS['text_primary']};
                }}
                QScrollBar:vertical {{
                    border: none;
                    background: {COLORS['bg_app']};
                    width: 10px;
                    margin: 0px 0px 0px 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: #CBD5E1;
                    min-height: 20px;
                    border-radius: 5px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)
            self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            self.list_widget.itemClicked.connect(self._on_item_clicked)
            frame_layout.addWidget(self.list_widget)
            layout.addWidget(self.frame)
            
        # Populate list
        self.list_widget.clear()
        for i in range(self.count()):
            item = QListWidgetItem(self.itemText(i))
            self.list_widget.addItem(item)
            
        # Select current
        if self.currentIndex() >= 0:
            self.list_widget.setCurrentRow(self.currentIndex())
            
        # Calculate height exactly based on visible items
        max_visible = 8
        count = self.count()
        visible = min(count, max_visible)
        list_h = (visible * 35) + 2 # +2 for borders
        
        # Calculate width
        w = self.width() - 2
        
        self.popup.setFixedSize(w, list_h)
        
        # Position perfectly below the combobox
        cb_rect = self.rect()
        bl = self.mapToGlobal(cb_rect.bottomLeft())
        tl = self.mapToGlobal(cb_rect.topLeft())
        
        # Screen constraints
        screen = QApplication.screenAt(bl)
        if screen:
            geom = screen.geometry()
            space_below = geom.bottom() - bl.y()
            if space_below < list_h:
                # Place above combobox if there is no space below
                bl = QPoint(tl.x(), tl.y() - list_h)
                
        self.popup.move(bl)
        self.popup.show()
        
    def _on_item_clicked(self, item):
        row = self.list_widget.row(item)
        self.setCurrentIndex(row)
        self.popup.hide()
