import os
import glob

def clean_duplicate_fix_cb():
    pattern = r'd:\Account_System\ui\components\*.py'
    
    duplicate_fix_cb = '''        def _fix_cb(cb):
            from PySide6.QtWidgets import QListView, QStyledItemDelegate
            cb.setMaxVisibleItems(7)
            v = QListView()
            cb.setView(v)
            cb.setItemDelegate(QStyledItemDelegate())
'''

    for filepath in glob.glob(pattern):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if duplicate_fix_cb in content:
            # We want to remove ALL instances of this specific exact unstyled _fix_cb block.
            # But only if it's duplicated (i.e. another _fix_cb follows it or exists).
            # If we just replace this exact block with nothing, we might break it if it's the ONLY one.
            # However, I know I injected the styled one right after this one in my previous scripts.
            # Let's count how many _fix_cb exist.
            if content.count('def _fix_cb(cb):') > 1:
                content = content.replace(duplicate_fix_cb, "")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Cleaned duplicate _fix_cb in: {os.path.basename(filepath)}")

clean_duplicate_fix_cb()
