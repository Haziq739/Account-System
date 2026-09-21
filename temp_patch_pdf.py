import re

file_path = r'd:\Account_System\services\pdf_generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update min_rows in all three functions
content = content.replace(
    'min_rows = 12\n            while len(data) <= min_rows:',
    'min_rows = 8 if "K Dynamics" in comp.name else 12\n            while len(data) <= min_rows:'
)

# 2. Re-arrange the Bank Details for Invoice
# We need to find the totals_outer and Bank Details section.
# We will use regex to capture the notes logic and remove the old Bank Details logic.

invoice_regex = re.compile(
    r'(# wrap it inside an outer table to align it to the right.*?)(if inv\.notes:.*?elements\.append\(notes_table\))(\s*# Bank Account Details for KD.*?elements\.append\(Spacer\(1, 5\)\))', 
    re.DOTALL
)

invoice_replacement = r"""# Build Bank Details Container for KD
            bd_container = ""
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
                bd_table = Table(bd_data, colWidths=[100, 180])
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

            # wrap it inside an outer table to align it to the right
            totals_outer = Table([[bd_container, t_totals]], colWidths=[250, 250])
            totals_outer.setStyle(TableStyle([
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP')
            ]))
            elements.append(totals_outer)
            
            \2"""

content = invoice_regex.sub(invoice_replacement, content)


# 3. Re-arrange the Bank Details for Quotation
quotation_regex = re.compile(
    r'(totals_outer = Table\(\[\["", t_totals\]\], colWidths=\[200, 300\]\)\s*totals_outer\.setStyle.*?elements\.append\(totals_outer\))(\s*if quot\.notes:.*?elements\.append\(notes_table\))(\s*# Bank Account Details for KD.*?elements\.append\(Spacer\(1, 5\)\))', 
    re.DOTALL
)

quotation_replacement = r"""# Build Bank Details Container for KD
            bd_container = ""
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
                bd_table = Table(bd_data, colWidths=[100, 180])
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
            elements.append(totals_outer)
            \2"""

content = quotation_regex.sub(quotation_replacement, content)


# 4. Re-arrange the Bank Details for Vendor Bill
vendor_regex = re.compile(
    r'(totals_outer = Table\(\[\["", t_totals\]\], colWidths=\[200, 300\]\)\s*totals_outer\.setStyle.*?elements\.append\(totals_outer\))(\s*if bill\.description:.*?elements\.append\(notes_table\))(\s*# Bank Account Details for KD.*?elements\.append\(Spacer\(1, 5\)\))', 
    re.DOTALL
)

vendor_replacement = r"""# Build Bank Details Container for KD
            bd_container = ""
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
                bd_table = Table(bd_data, colWidths=[100, 180])
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
            elements.append(totals_outer)
            \2"""

content = vendor_regex.sub(vendor_replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
