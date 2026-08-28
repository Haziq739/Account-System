import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import os

sys.path.append('d:/Account_System')
from ui.components.payment_dialogs import AddPaymentDialog

def take_screenshot():
    app = QApplication.instance() or QApplication(sys.argv)
    
    from ui.design_system import COLORS, init_theme
    init_theme()
    app.setStyleSheet(f"""
        ;
            color: {COLORS['text_primary']};
            selection-background-color: {COLORS['primary']};
            selection-color: {COLORS['text_on_primary']};
            border: 1px solid {COLORS['border']};
            outline: none;
            padding: 0px;
        }}
    """)

    dialog = AddPaymentDialog(None, company_id=1, current_user={'id': 1, 'role': 'Admin'})
    
    # Add dummy items to force scrollbar
    for i in range(15):
        dialog.customer_cb.addItem(f"Dummy Customer {i}", i)
        
    dialog.show()
    
    def grab_screen():
        screen = app.primaryScreen()
        artifact_dir = r"C:\Users\Muhammad Haziq Naeem\.gemini\antigravity-ide\brain\8b6d8335-21f4-46ac-aa39-61ad7ed463e7"
        screenshot_path = os.path.join(artifact_dir, "popup_screenshot_many.png")
        pixmap = screen.grabWindow(0)
        pixmap.save(screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")
        dialog.close()
        app.quit()

    QTimer.singleShot(1000, lambda: dialog.customer_cb.showPopup())
    QTimer.singleShot(2000, grab_screen)
    
    app.exec()

if __name__ == '__main__':
    take_screenshot()
