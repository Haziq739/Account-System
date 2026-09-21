import os

pdf_path = r'd:\Account_System\services\pdf_generator.py'
with open(pdf_path, 'r', encoding='utf-8') as f:
    content = f.read()

bank_details = """
            # Bank Account Details for KD
            if "K Dynamics" in comp.name:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("<b>BANK ACCOUNT DETAILS:</b>", styles['Normal']))
                
                bd_data = [
                    ["<b>Name of Firm:</b>", "<b>K Dynamics Pvt Ltd.</b>"],
                    ["<b>Banker Name:</b>", "<b>United Bank Limited</b>"],
                    ["<b>Address:</b>", "<b>Fazal e Haq Road Branch(1748)</b>"],
                    ["<b>IBAN Number:</b>", "<b>PK06 UNIL 0109 0003 2960 7942</b>"],
                    ["<b>Account Numbers:</b>", "<b>0109 0003 2960 7942</b>"],
                    ["<b>Branch Code:</b>", "<b>1748</b>"]
                ]
                
                bd_table = Table(bd_data, colWidths=[120, 300])
                bd_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,0), (-1,-1), 10),
                    ('ALIGN', (0,0), (0,-1), 'LEFT'),
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                    ('TOPPADDING', (0,0), (-1,-1), 2),
                ]))
                elements.append(bd_table)
                
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("<b>GST/NTN:</b> Sales Tax Reg. No. is 3277876363483 and Our NTN No .is G650435", styles['Normal']))
                elements.append(Spacer(1, 10))
            
            doc.build(elements, onFirstPage=PDFGenerator._draw_page_border, onLaterPages=PDFGenerator._draw_page_border)"""

if "BANK ACCOUNT DETAILS:" not in content:
    content = content.replace("            doc.build(elements, onFirstPage=PDFGenerator._draw_page_border, onLaterPages=PDFGenerator._draw_page_border)", bank_details)
    with open(pdf_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("PDF bank details added successfully!")
