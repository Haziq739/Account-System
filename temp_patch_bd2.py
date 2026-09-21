import os

file_path = r'd:\Account_System\services\pdf_generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = 0

for line in lines:
    if skip > 0:
        skip -= 1
        continue
    if '# Bank Account Details for KD' in line:
        skip = 29
        continue
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("done")
