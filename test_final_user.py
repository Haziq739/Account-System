import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

import os
sys.path.append('d:/Account_System')
from ui.components.payment_dialogs import AddPaymentDialog

def run_test():
    app = QApplication.instance() or QApplication(sys.argv)
    
    from ui.design_system import COLORS, init_theme
    init_theme()
    
    # We populate dummy customers for the dialog
    dummy_customers = [{"id": i, "name": f"Real Customer {i}"} for i in range(25)]
    
    dialog = AddPaymentDialog(None, company_id=1, current_user={'id': 1, 'role': 'Admin'})
    
    # Override customers to simulate large list
    dialog.customers = dummy_customers
    dialog.customer_cb.clear()
    dialog.customer_cb.addItem("-- Select Customer --", None)
    for c in dummy_customers:
        dialog.customer_cb.addItem(c['name'], c['id'])
    
    def grab_screen():
        screen = app.primaryScreen()
        artifact_dir = r"C:\Users\Muhammad Haziq Naeem\.gemini\antigravity-ide\brain\8b6d8335-21f4-46ac-aa39-61ad7ed463e7"
        screenshot_path = os.path.join(artifact_dir, "popup_screenshot_final_user.png")
        pixmap = screen.grabWindow(0)
        pixmap.save(screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")
        dialog.close()
        app.quit()

    QTimer.singleShot(1000, lambda: dialog.customer_cb.showPopup())
    QTimer.singleShot(2000, grab_screen)
    
    dialog.show()
    app.exec()

if __name__ == '__main__':
    run_test()
