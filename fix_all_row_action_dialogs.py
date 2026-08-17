import glob
import re

def fix_all_row_action_dialogs():
    files = glob.glob(r'd:\Account_System\ui\pages\*.py')
    
    # We will search for class RowActionDialog(QDialog):
    # and replace its setWindowFlags call to self.setWindowFlags(Qt.WindowType.Dialog)
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "class RowActionDialog(QDialog):" in content:
            # It has a RowActionDialog. Let's find the window flags.
            # It could be Popup | FramelessWindowHint OR Dialog | CustomizeWindowHint | WindowTitleHint OR just Dialog
            content = re.sub(
                r'self\.setWindowFlags\([^)]+\)',
                r'self.setWindowFlags(Qt.WindowType.Dialog)',
                content
            )
            
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    fix_all_row_action_dialogs()
    print("Fixed all RowActionDialogs")
