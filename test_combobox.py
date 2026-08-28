import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Import the necessary modules from the app
import os
sys.path.append('d:/Account_System')
from ui.components.payment_dialogs import AddPaymentDialog

def run_test():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Apply the global stylesheet as done in main.py
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
        QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {{
            background-color: {COLORS['primary']};
            color: {COLORS['text_on_primary']};
            border: none;
        }}
    """)

    # Create the dialog with dummy data
    dialog = AddPaymentDialog(None, company_id=1, current_user={'id': 1, 'role': 'Admin'})
    
    # Function to check the popup after it opens
    def check_popup():
        print("--- COMBOBOX TEST RESULTS ---")
        cb = dialog.customer_cb
        print(f"Max Visible Items property: {cb.maxVisibleItems()}")
        
        view = cb.view()
        if not view:
            print("Error: No view found.")
            app.quit()
            return
            
        popup_window = view.window()
        if popup_window:
            print(f"Popup Window Height: {popup_window.height()}px")
            print(f"Popup Window Y pos: {popup_window.y()}")
            print(f"Combobox Y pos (global): {cb.mapToGlobal(cb.rect().topLeft()).y()}")
            
            # Check the height against the expected (8 items * 35px = 280px approx)
            if 250 <= popup_window.height() <= 300:
                print("SUCCESS: Popup height is bounded to exactly 8 items!")
            else:
                print(f"WARNING: Popup height seems wrong ({popup_window.height()}px).")
                
        else:
            print("Error: No popup window found.")
            
        # Close and quit
        dialog.close()
        app.quit()

    # Show the dialog, wait a tiny bit, open the combobox, wait a tiny bit, then check
    QTimer.singleShot(500, lambda: dialog.customer_cb.showPopup())
    QTimer.singleShot(1000, check_popup)
    
    dialog.show()
    app.exec()

if __name__ == '__main__':
    run_test()
