import sys
from PySide6.QtWidgets import QApplication, QComboBox
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
    
    class TestCombo(QComboBox):
        def showPopup(self):
            count = self.count()
            visible = min(count, 8)
            h = visible * 35
            
            # Forcing the view height before showing the popup
            self.view().setMinimumHeight(h)
            self.view().setMaximumHeight(h)
            super().showPopup()

    # Create and swap in the test combo
    layout = dialog.layout()
    cb = TestCombo()
    cb.addItems(["Item 1", "Item 2", "Item 3", "Item 4"])
    layout.addWidget(cb)
    
    def check_popup():
        print("--- DYNAMIC COMBOBOX TEST RESULTS ---")
        
        v = cb.view()
        popup_window = v.window()
        if popup_window:
            print(f"Popup Window Height: {popup_window.height()}px")
            if popup_window.height() == 4 * 35:
                print("SUCCESS: Popup height bounded to 4 items!")
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
