import os

file_path = "services/pdf_generator.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "t_totals.setStyle(TableStyle([" in line:
        new_lines.append(line)
        break
    new_lines.append(line)

# Now append the rest of the original generate_quotation_pdf
rest = """                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ]))
            elements.append(t_totals)
            
            if q.notes:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("<b>Notes:</b>", styles['Normal']))
                elements.append(Paragraph(q.notes, styles['Normal']))
            
            doc.build(elements)
            return filepath

    @staticmethod
    def generate_daybook_pdf(company_id: int, target_date, data_dict: dict) -> str:
        from database.session import SessionLocal
        from models.company import Company
        from reportlab.lib.pagesizes import landscape, A4
        from pathlib import Path
        
        with SessionLocal() as s:
            comp = s.query(Company).filter(Company.id == company_id).first()
            if not comp:
                raise ValueError("Company not found.")
                
            # Create directory
            documents_dir = Path.home() / "Documents" / "Day_Book" / comp.name.replace(" ", "_")
            documents_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = target_date.strftime("%Y-%m-%d")
            filename = f"DayBook-{date_str}.pdf"
            filepath = str(documents_dir / filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            elements.append(Paragraph(f"<b>{comp.name}</b>", styles['Title']))
            elements.append(Paragraph(f"<b>Day Book</b> - {target_date.strftime('%d-%b-%Y')}", styles['Heading2']))
            elements.append(Spacer(1, 20))
            
            # Summary Table
            summary_data = [
                ["Total Income", "Total Expense", "Closing Balance"],
                [
                    f"{data_dict['total_income']:,.2f}",
                    f"{data_dict['total_expense']:,.2f}",
                    f"{data_dict['balance']:,.2f}"
                ]
            ]
            t_summary = Table(summary_data, colWidths=[200, 200, 200])
            t_summary.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ]))
            elements.append(t_summary)
            elements.append(Spacer(1, 30))
            
            # Transactions Table
            table_data = [["Time", "Type", "Description", "Customer / Title", "Ref No.", "Income", "Expense", "Balance"]]
            
            for t in data_dict['transactions']:
                time_str = t['timestamp'].strftime("%I:%M %p") if t['timestamp'] else ""
                table_data.append([
                    time_str,
                    t['type'],
                    t['description'][:50] + ("..." if len(t['description']) > 50 else ""),
                    t['customer_or_title'][:30] + ("..." if len(t['customer_or_title']) > 30 else ""),
                    t['invoice_number'],
                    f"{t['income']:,.2f}" if t['income'] > 0 else "-",
                    f"{t['expense']:,.2f}" if t['expense'] > 0 else "-",
                    f"{t['running_balance']:,.2f}"
                ])
                
            t_trans = Table(table_data, colWidths=[70, 100, 150, 120, 80, 80, 80, 90])
            t_trans.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F8FAFC")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1E293B")),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (5,1), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ]))
            elements.append(t_trans)
            
            doc.build(elements)
            return filepath
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
    f.write(rest)
