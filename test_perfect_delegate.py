import sys
from PySide6.QtWidgets import QApplication, QComboBox, QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPalette

import os
sys.path.append('d:/Account_System')
from ui.components.payment_dialogs import AddPaymentDialog

def run_test():
    app = QApplication.instance() or QApplication(sys.argv)
    
    from ui.design_system import COLORS, init_theme
    init_theme()
    # NO STYLESHEET FOR QCOMBOBOX VIEW!
    
    dialog = AddPaymentDialog(None, company_id=1, current_user={'id': 1, 'role': 'Admin'})
    
    class HoverDelegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(35)
            return size
            
        def paint(self, painter, option, index):
            if option.state & QStyle.State_Selected or option.state & QStyle.State_MouseOver:
                painter.fillRect(option.rect, QColor(COLORS['primary']))
                # Force text color white
                option.palette.setColor(QPalette.Text, QColor("white"))
                option.palette.setColor(QPalette.WindowText, QColor("white"))
                option.palette.setColor(QPalette.HighlightedText, QColor("white"))
            super().paint(painter, option, index)

    layout = dialog.layout()
    cb = QComboBox()
    cb.setMaxVisibleItems(8)
    cb.setItemDelegate(HoverDelegate())
    
    for i in range(15):
        cb.addItem(f"Dummy {i}", i)
    layout.addWidget(cb)
    
    def grab_screen():
        screen = app.primaryScreen()
        artifact_dir = r"C:\Users\Muhammad Haziq Naeem\.gemini\antigravity-ide\brain\8b6d8335-21f4-46ac-aa39-61ad7ed463e7"
        screenshot_path = os.path.join(artifact_dir, "popup_screenshot_perfect.png")
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
