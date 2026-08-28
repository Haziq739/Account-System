import re

with open('d:/Account_System/ui/components/payment_dialogs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add BoundedComboBox
bounded_class = """
class BoundedComboBox(QComboBox):
    def showPopup(self):
        count = self.count()
        visible = min(count, 8)
        # 35px matches the delegate item height
        h = visible * 35
        v = self.view()
        if v:
            v.setMinimumHeight(h)
            v.setMaximumHeight(h)
        super().showPopup()

class ComboBoxDelegate"""

content = content.replace("class ComboBoxDelegate", bounded_class)

# 2. Change QComboBox back to BoundedComboBox
content = re.sub(r'self\.([a-z_]+_cb)\s*=\s*QComboBox\(\)', r'self.\1 = BoundedComboBox()', content)

with open('d:/Account_System/ui/components/payment_dialogs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied: added BoundedComboBox with dynamic height pre-calculation')
