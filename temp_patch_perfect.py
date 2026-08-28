import re

# 1. Update main.py to remove the broken QComboBox QAbstractItemView CSS
with open('d:/Account_System/main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

# We need to remove the QComboBox QAbstractItemView block
# It starts at ".*?QComboBox QAbstractItemView::item:hover.*?\}'
main_content = re.sub(css_pattern, '', main_content, flags=re.DOTALL)

with open('d:/Account_System/main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)


# 2. Update payment_dialogs.py
with open('d:/Account_System/ui/components/payment_dialogs.py', 'r', encoding='utf-8') as f:
    pay_content = f.read()

# Replace BoundedComboBox class with the enhanced ComboBoxDelegate
new_delegate = """from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QStyle

class ComboBoxDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(35)
        return size
        
    def paint(self, painter, option, index):
        # Draw custom blue background on hover/select
        if option.state & QStyle.State_Selected or option.state & QStyle.State_MouseOver:
            from ui.design_system import COLORS
            painter.fillRect(option.rect, QColor(COLORS['primary']))
            
            # Force text to white
            palette = option.palette
            palette.setColor(QPalette.Text, QColor("white"))
            palette.setColor(QPalette.WindowText, QColor("white"))
            palette.setColor(QPalette.HighlightedText, QColor("white"))
            option.palette = palette
            
        super().paint(painter, option, index)"""

pay_content = re.sub(r'class BoundedComboBox\(QComboBox\):.*?super\(\)\.showPopup\(\)\s+class ComboBoxDelegate\(QStyledItemDelegate\):.*?return size', new_delegate, pay_content, flags=re.DOTALL)

# Revert BoundedComboBox instantiations back to QComboBox
pay_content = pay_content.replace('BoundedComboBox()', 'QComboBox()')

with open('d:/Account_System/ui/components/payment_dialogs.py', 'w', encoding='utf-8') as f:
    f.write(pay_content)

print("Applied perfect native combobox fix")
