import sys
import time
from PySide6.QtWidgets import QApplication, QListView
from PySide6.QtCore import QTimer

import os
sys.path.append('d:/Account_System')
from ui.components.payment_dialogs import AddPaymentDialog

def run_test():
    app = QApplication.instance() or QApplication(sys.argv)
    
    from ui.design_system import COLORS
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
    
    cb = dialog.customer_cb
    
    # Try forcing the view height
    view = QListView()
    # 8 items * 35px = 280px
    view.setMinimumHeight(280)
    view.setMaximumHeight(280)
    cb.setView(view)
    
    def check_popup():
        print("--- COMBOBOX TEST RESULTS ---")
        
        v = cb.view()
        popup_window = v.window()
        if popup_window:
            print(f"Popup Window Height: {popup_window.height()}px")
            print(f"Popup Window Y pos: {popup_window.y()}")
            print(f"Combobox Y pos (global): {cb.mapToGlobal(cb.rect().topLeft()).y()}")
            
            if 250 <= popup_window.height() <= 300:
                print("SUCCESS: Popup height is bounded to exactly 8 items!")
            else:
                print(f"WARNING: Popup height seems wrong ({popup_window.height()}px).")
        
        dialog.close()
        app.quit()

    QTimer.singleShot(500, lambda: cb.showPopup())
    QTimer.singleShot(1000, check_popup)
    
    dialog.show()
    app.exec()

if __name__ == '__main__':
    run_test()
