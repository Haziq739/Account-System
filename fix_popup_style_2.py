import os

def fix_style(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace setFixedSize with setFixedWidth
    content = content.replace('self.setFixedSize(320, 420)', 'self.setFixedWidth(320)')

    # Provide highly specific CSS to override the global `#outline_btn` and `#primary_btn` IDs
    # Add a prominent blue border to the QDialog so it doesn't blend in
    new_style = '''self.setStyleSheet(f"""
            QDialog {{ 
                background-color: {COLORS['bg_card']}; 
                border-radius: 8px; 
                border: 2px solid {COLORS['primary']}; 
            }}
            QPushButton, QPushButton#outline_btn, QPushButton#primary_btn {{
                text-align: center;
                padding: 12px 16px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QPushButton:hover, QPushButton#outline_btn:hover, QPushButton#primary_btn:hover {{
                background-color: #EFF6FF;
                border: 1px solid {COLORS['primary']};
                color: {COLORS['primary']};
            }}
        """)'''

    import re
    # Strip the old setStyleSheet completely and replace it
    content = re.sub(r'self\.setStyleSheet\(f"""[\s\S]*?QPushButton:hover \{[\s\S]*?\}\s*"""\)', new_style, content)

    # Make the delete button also perfectly match the hover colors without getting squished
    new_del_style = '''self.btn_del.setStyleSheet("""
            QPushButton, QPushButton#outline_btn {
                background-color: #FEF2F2; 
                color: #DC2626; 
                border: 1px solid #FECACA; 
                text-align: center;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover, QPushButton#outline_btn:hover {
                background-color: #FEE2E2;
                border: 1px solid #EF4444;
                color: #B91C1C;
            }
        """)'''
        
    content = re.sub(r'self\.btn_del\.setStyleSheet\("""[\s\S]*?\}\s*"""\)', new_del_style, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_style(r"d:\Account_System\ui\pages\invoices_page.py")
    fix_style(r"d:\Account_System\ui\pages\quotations_page.py")
