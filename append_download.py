import os

def append_download_method(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # The new method to append at the end of the file
    new_method = """
    def _on_download(self, bill_id: int):
        from PySide6.QtWidgets import QFileDialog
        import shutil
        import os
        try:
            path = PDFGenerator.generate_vendor_bill_pdf(bill_id)
            if os.path.exists(path):
                save_path, _ = QFileDialog.getSaveFileName(self, "Save Bill", os.path.basename(path), "PDF Files (*.pdf)")
                if save_path:
                    shutil.copy2(path, save_path)
                    show_message(self, "success", "Success", "Bill downloaded successfully.")
        except Exception as e:
            show_message(self, "error", "Error", str(e))
"""

    if "def _on_download(self," not in content:
        content += new_method

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    append_download_method(r"d:\Account_System\ui\pages\vendor_bills_page.py")
