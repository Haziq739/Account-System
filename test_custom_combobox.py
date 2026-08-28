import sys
from PySide6.QtWidgets import QApplication, QComboBox, QListWidget, QWidget, QVBoxLayout, QFrame, QListWidgetItem
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QSize
from PySide6.QtGui import QColor, QPalette

import os
sys.path.append('d:/Account_System')

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup = None
        
    def hidePopup(self):
        super().hidePopup()
        if self.popup:
            self.popup.hide()
            
    def showPopup(self):
        # We DO NOT call super().showPopup()! We show our own!
        if not self.popup:
            self.popup = QWidget(self, Qt.Popup | Qt.FramelessWindowHint)
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
                QListWidget::item:hover, QListWidget::item:selected {{
                    background-color: {COLORS['primary']};
                    color: white;
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
            
        # Calculate height
        count = self.count()
        visible = min(count, 8)
        list_h = (visible * 35) + 2
        
        # Calculate width
        w = self.width()
        
        self.popup.setFixedSize(w, list_h)
        
        # Position below the combobox
        cb_rect = self.rect()
        bl = self.mapToGlobal(cb_rect.bottomLeft())
        tl = self.mapToGlobal(cb_rect.topLeft())
        
        screen = QApplication.screenAt(bl)
        if screen:
            geom = screen.geometry()
            space_below = geom.bottom() - bl.y()
            if space_below < list_h:
                # Place above if no space
                bl = QPoint(tl.x(), tl.y() - list_h)
                
        self.popup.move(bl)
        self.popup.show()
        
    def _on_item_clicked(self, item):
        row = self.list_widget.row(item)
        self.setCurrentIndex(row)
        self.popup.hide()

def run_test():
    app = QApplication.instance() or QApplication(sys.argv)
    
    from ui.design_system import COLORS, init_theme
    from ui.components.payment_dialogs import AddPaymentDialog
    init_theme()
    
    dialog = AddPaymentDialog(None, company_id=1, current_user={'id': 1, 'role': 'Admin'})
    
    # Inject our CustomComboBox
    layout = dialog.layout()
    cb = CustomComboBox()
    cb.setStyleSheet(f"""
        QComboBox {{
            background-color: {COLORS['bg_input']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px; padding: 8px;
            color: {COLORS['text_primary']};
        }}
    """)
    for i in range(25):
        cb.addItem(f"Real Customer {i}", i)
    layout.addWidget(cb)
    
    def grab_screen():
        screen = app.primaryScreen()
        artifact_dir = r"C:\Users\Muhammad Haziq Naeem\.gemini\antigravity-ide\brain\8b6d8335-21f4-46ac-aa39-61ad7ed463e7"
        screenshot_path = os.path.join(artifact_dir, "popup_screenshot_custom.png")
        pixmap = screen.grabWindow(0)
        pixmap.save(screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")
        dialog.close()
        app.quit()

    QTimer.singleShot(1000, lambda: cb.showPopup())
    QTimer.singleShot(2000, grab_screen)
    
    dialog.show()
    app.exec()

if __name__ == '__main__':
    run_test()
