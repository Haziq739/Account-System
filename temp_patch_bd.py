import os

file_path = r'd:\Account_System\services\pdf_generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_totals_template = """            bd_container = ""
            if "K Dynamics" in comp.name:
                bd_elements = []
                bd_elements.append(Paragraph("<b>BANK ACCOUNT DETAILS:</b>", styles['Normal']))
                bd_data = [
                    ["Name of Firm:", "K Dynamics Pvt Ltd."],
                    ["Banker Name:", "United Bank Limited"],
                    ["Address:", "Fazal e Haq Road Branch(1748)"],
                    ["IBAN Number:", "PK06 UNIL 0109 0003 2960 7942"],
                    ["Account Numbers:", "0109 0003 2960 7942"],
                    ["Branch Code:", "1748"]
                ]
                bd_table = Table(bd_data, colWidths=[100, 150])
                bd_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('ALIGN', (0,0), (0,-1), 'LEFT'),
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                ]))
                bd_elements.append(bd_table)
                bd_elements.append(Spacer(1, 5))
                bd_elements.append(Paragraph("<font size=8><b>GST/NTN:</b> Sales Tax Reg. No. is 3277876363483 and Our NTN No .is G650435</font>", styles['Normal']))
                bd_container = bd_elements

            totals_outer = Table([[bd_container, t_totals]], colWidths=[250, 250])
            totals_outer.setStyle(TableStyle([
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP')
            ]))
            elements.append(totals_outer)"""

# -----------------
# 1. Invoice Patch
# -----------------
invoice_old_totals = """            totals_outer = Table([["", t_totals]], colWidths=[200, 300])
            totals_outer.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            elements.append(totals_outer)"""

old_bd = """            # Bank Account Details for KD
            if "K Dynamics" in comp.name:
                elements.append(Spacer(1, 5))
                elements.append(Paragraph("<b>BANK ACCOUNT DETAILS:</b>", styles['Normal']))
                
                bd_data = [
                    ["Name of Firm:", "K Dynamics Pvt Ltd."],
                    ["Banker Name:", "United Bank Limited"],
                    ["Address:", "Fazal e Haq Road Branch(1748)"],
                    ["IBAN Number:", "PK06 UNIL 0109 0003 2960 7942"],
                    ["Account Numbers:", "0109 0003 2960 7942"],
                    ["Branch Code:", "1748"]
                ]
                
                bd_table = Table(bd_data, colWidths=[110, 300])
                bd_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('ALIGN', (0,0), (0,-1), 'LEFT'),
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                ]))
                elements.append(bd_table)
                
                elements.append(Spacer(1, 5))
                elements.append(Paragraph("<b>GST/NTN:</b> Sales Tax Reg. No. is 3277876363483 and Our NTN No .is G650435", styles['Normal']))
                elements.append(Spacer(1, 5))"""

# Actually they are exactly the same in all three! So replacing them will replace all of them!
count = content.count(invoice_old_totals)
print(f"Found {count} old totals")
content = content.replace(invoice_old_totals, new_totals_template)

count_bd = content.count(old_bd)
print(f"Found {count_bd} old bd")
content = content.replace(old_bd, "")

# The code for vendor and quotation has exact same logic.
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
