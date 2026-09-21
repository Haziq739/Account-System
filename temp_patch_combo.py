import os

files = [
    r'd:\Account_System\ui\components\create_invoice_dialog.py',
    r'd:\Account_System\ui\components\create_quotation_dialog.py'
]

old_code = '''        srv_cb = QComboBox()'''
new_code = '''        from PySide6.QtWidgets import QListView
        srv_cb = QComboBox()
        srv_cb.setMaxVisibleItems(5)
        v = QListView()
        v.setStyleSheet(f"""
            QListView {{ outline: 0px; background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }}
            QListView::item {{ padding: 8px; border: none; }}
            QListView::item:selected, QListView::item:hover {{ background-color: {COLORS['primary']}; color: white; border: none; }}
            QScrollBar:vertical {{ background: {COLORS['bg_input']}; width: 10px; border-radius: 5px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['text_secondary']}; border-radius: 5px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        srv_cb.setView(v)'''

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace(old_code, new_code)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
print('Patched ComboBox styling')
