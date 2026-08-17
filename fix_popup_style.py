import os

def fix_style(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the dialog definition block
    # We want to replace the old self.setStyleSheet with the new comprehensive one
    old_style_invoices = 'self.setStyleSheet(f"background-color: {COLORS[\'bg_card\']}; border-radius: 8px;")'
    
    new_style = '''self.setStyleSheet(f"""
            QDialog { 
                background-color: {COLORS['bg_card']}; 
                border-radius: 8px; 
                border: 1px solid {COLORS['border_card']}; 
            }
            QPushButton {
                text-align: center;
                padding: 10px 16px;
                border: 1px solid {COLORS['border_card']};
                border-radius: 6px;
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
                border: 1px solid #93C5FD;
                color: #1D4ED8;
            }
        """)'''

    if old_style_invoices in content:
        content = content.replace(old_style_invoices, new_style)
        
    # Let's also fix the delete button explicit style so it hovers correctly
    old_del_style = 'self.btn_del.setStyleSheet("background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; padding: 8px; border-radius: 4px; font-weight: 500;")'
    new_del_style = '''self.btn_del.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2; 
                color: #DC2626; 
                border: 1px solid #FECACA; 
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                border: 1px solid #F87171;
            }
        """)'''
    
    if old_del_style in content:
        content = content.replace(old_del_style, new_del_style)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_style(r"d:\Account_System\ui\pages\invoices_page.py")
    fix_style(r"d:\Account_System\ui\pages\quotations_page.py")
