import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet

class BottomSpacer(Flowable):
    def __init__(self, target_flowable):
        Flowable.__init__(self)
        self.target = target_flowable

    def wrap(self, availWidth, availHeight):
        w, h = self.target.wrap(availWidth, availHeight)
        self.width = availWidth
        self.height = max(0, availHeight - h - 30) # Push to bottom, leave 30pt padding
        return (self.width, self.height)

    def draw(self):
        pass
from reportlab.lib import colors
from database.session import SessionLocal
from models.invoice import Invoice
from models.company import Company

class PDFGenerator:
    @staticmethod
    def _draw_page_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.setLineWidth(1)
        width, height = doc.pagesize
        canvas.rect(20, 20, width - 40, height - 40)
        canvas.restoreState()

    @staticmethod
    def generate_invoice_pdf(invoice_id: int) -> str:
        with SessionLocal() as s:
            inv = s.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not inv:
                raise ValueError("Invoice not found.")
                
            comp = inv.company
            cust = inv.customer
            
            # Directory — store on Desktop
            from pathlib import Path
            desktop = Path.home() / "Desktop"
            pdf_dir = desktop / "invoices"
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
                
            filename = f"Invoice_{inv.invoice_number}.pdf"
            filepath = os.path.join(pdf_dir, filename)
            from reportlab.lib.pagesizes import A4
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            logo_file = None
            if comp.logo_path and os.path.exists(comp.logo_path):
                logo_file = comp.logo_path
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if "RN Scanner" in comp.name:
                    fallback_path = os.path.join(base_dir, "assets", "rn_scanner_logo.png")
                    if os.path.exists(fallback_path):
                        logo_file = fallback_path
                elif "K Dynamics" in comp.name:
                    fallback_path = os.path.join(base_dir, "assets", "k_dynamics_logo.png")
                    if os.path.exists(fallback_path):
                        logo_file = fallback_path

            from reportlab.lib.styles import ParagraphStyle
            comp_style = ParagraphStyle('CompStyle', parent=styles['Normal'], fontSize=18, leading=22, spaceAfter=4)
            doc_style = ParagraphStyle('DocStyle', parent=styles['Normal'], fontSize=14, leading=18, spaceAfter=4)
            
            # --- Header Table (Company & Logo) ---
            comp_info = []
            comp_info.append(Paragraph(f"<b>{comp.name}</b>", comp_style))
            if comp.address: comp_info.append(Paragraph(comp.address, styles['Normal']))
            if comp.phone: comp_info.append(Paragraph(f"Phone: {comp.phone}", styles['Normal']))
            
            logo_element = ""
            if logo_file:
                from reportlab.platypus import Image
                try:
                    logo_element = Image(logo_file)
                    try:
                        aspect = logo_element.imageWidth / float(logo_element.imageHeight)
                        logo_element.drawHeight = 60
                        logo_element.drawWidth = 60 * aspect
                    except AttributeError:
                        logo_element.drawHeight = 60
                        logo_element.drawWidth = 100
                except Exception as e:
                    print(f"Error loading logo: {e}")

            header_table = Table([[comp_info, logo_element]], colWidths=[350, 150])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (1,0), (1,0), 'RIGHT')
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 20))
            
            # --- Document Info & Bill To Table ---
            bill_info = []
            bill_info.append(Paragraph("<b>BILL TO:</b>", styles['Heading4']))
            bill_info.append(Paragraph(f"<b>Name:</b> {cust.name}", styles['Normal']))
            if cust.phone: bill_info.append(Paragraph(f"<b>Phone:</b> {cust.phone}", styles['Normal']))
            if cust.address: bill_info.append(Paragraph(f"<b>Address:</b> {cust.address}", styles['Normal']))
            
            doc_info = []
            doc_info.append(Paragraph(f"<b>INVOICE</b>", doc_style))
            
            detail_data = [
                [Paragraph("<b>Invoice #</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(inv.invoice_number, styles['Normal'])],
                [Paragraph("<b>Date</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(inv.issue_date.strftime('%d-%m-%Y'), styles['Normal'])]
            ]
            detail_table = Table(detail_data, colWidths=[60, 10, 150])
            detail_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            doc_info.append(detail_table)
            
            info_table = Table([[bill_info, "", doc_info]], colWidths=[240, 20, 240])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F8FAFC")),
                ('BACKGROUND', (2,0), (2,0), colors.HexColor("#F8FAFC")),
                ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#E2E8F0")),
                ('BOX', (2,0), (2,0), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Items Table
            data = [["S.No", "Description", "Qty", "Price", "Amount"]]
            
            for idx, item in enumerate(inv.items):
                service_name = item.service.name if item.service else "Service"
                desc_html = f"<b>{service_name}</b>"
                if item.description:
                    desc_html += f"<br/>{item.description}"
                    
                desc_p = Paragraph(desc_html, styles['Normal'])
                
                data.append([
                    str(idx + 1),
                    desc_p,
                    str(item.quantity),
                    f"{float(item.unit_price):.2f}",
                    f"{float(item.total_price):.2f}"
                ])
            # Pad with empty rows for standard table size
            min_rows = 12
            while len(data) <= min_rows:
                data.append(["", "", "", "", ""])
                
            t = Table(data, colWidths=[40, 250, 50, 70, 80])
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
                ('LINEAFTER', (0,0), (-2,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t)
            
            elements.append(Spacer(1, 20))
            
            # Totals Table
            totals = [
                ["Subtotal:", f"{float(inv.total_amount):.2f}"],
                ["Discount:", f"{float(inv.discount):.2f}"]
            ]
            
            if comp.tax_enabled:
                totals.append([f"Tax ({float(inv.tax_percentage)}%):", f"{float(inv.tax_amount):.2f}"])
                
            totals.append(["Net Total:", f"{float(inv.net_amount):.2f}"])
            totals.append(["Paid:", f"{float(inv.paid_amount):.2f}"])
            remaining = float(inv.net_amount) - float(inv.paid_amount)
            totals.append(["Remaining:", f"{remaining:.2f}"])
            
            t_totals = Table(totals, colWidths=[200, 100])
            t_totals.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#F8FAFC")),
                ('BOX', (0, -3), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            
            # wrap it inside an outer table to align it to the right
            totals_outer = Table([["", t_totals]], colWidths=[200, 300])
            totals_outer.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            elements.append(totals_outer)
            
            if inv.notes:
                elements.append(Spacer(1, 20))
                notes_html = str(inv.notes).replace('\n', '<br/>')
                p = Paragraph(notes_html, styles['Normal'])
                notes_table = Table([[p]], colWidths=[500])
                notes_table.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                    ('TOPPADDING', (0,0), (-1,-1), 12),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ]))
                elements.append(BottomSpacer(notes_table))
                elements.append(notes_table)
            
            doc.build(elements, onFirstPage=PDFGenerator._draw_page_border, onLaterPages=PDFGenerator._draw_page_border)
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
                
            # Create directory — store on Desktop
            from pathlib import Path
            documents_dir = Path.home() / "Desktop" / "Day_Book" / comp.name.replace(" ", "_")
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
                ["Opening Balance", "Total Income", "Total Expense", "Closing Balance"],
                [
                    f"{data_dict.get('opening_balance', 0.0):,.2f}",
                    f"{data_dict['total_income']:,.2f}",
                    f"{data_dict['total_expense']:,.2f}",
                    f"{data_dict['balance']:,.2f}"
                ]
            ]
            t_summary = Table(summary_data, colWidths=[160, 160, 160, 160])
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
            table_data = [["Time", "Type", "Description", "Customer", "Ref No.", "Income", "Expense", "Balance"]]
            
            for t in data_dict['transactions']:
                time_str = ""
                if t['timestamp']:
                    from datetime import timezone
                    dt = t['timestamp']
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    time_str = dt.astimezone().strftime("%I:%M %p")
                
                desc_para = Paragraph(t['description'], styles['Normal'])
                cust_para = Paragraph(t['customer_or_title'], styles['Normal'])
                
                table_data.append([
                    time_str,
                    t['type'],
                    desc_para,
                    cust_para,
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
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ]))
            elements.append(t_trans)
            
            doc.build(elements)
            return filepath

    @staticmethod
    def generate_vendor_bill_pdf(bill_id: int) -> str:
        from database.session import SessionLocal
        from models.vendor_bill import VendorBill
        from models.company import Company
        from pathlib import Path
        
        with SessionLocal() as s:
            bill = s.query(VendorBill).filter(VendorBill.id == bill_id).first()
            if not bill:
                raise ValueError("Vendor Bill not found.")
                
            comp = bill.company
            vend = bill.vendor
            
            # Directory — store on Desktop
            from pathlib import Path
            pdf_dir = Path.home() / "Desktop" / "Vendor_Bills" / comp.name.replace(" ", "_")
            pdf_dir.mkdir(parents=True, exist_ok=True)
                
            filename = f"Vendor_Bill_{bill.bill_number}.pdf"
            filepath = str(pdf_dir / filename)
            from reportlab.lib.pagesizes import A4
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            logo_file = None
            if comp.logo_path and os.path.exists(comp.logo_path):
                logo_file = comp.logo_path
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if "RN Scanner" in comp.name:
                    fallback_path = os.path.join(base_dir, "assets", "rn_scanner_logo.png")
                    if os.path.exists(fallback_path):
                        logo_file = fallback_path
                elif "K Dynamics" in comp.name:
                    fallback_path = os.path.join(base_dir, "assets", "k_dynamics_logo.png")
                    if os.path.exists(fallback_path):
                        logo_file = fallback_path


            
            from reportlab.lib.styles import ParagraphStyle
            comp_style = ParagraphStyle('CompStyle', parent=styles['Normal'], fontSize=18, leading=22, spaceAfter=4)
            doc_style = ParagraphStyle('DocStyle', parent=styles['Normal'], fontSize=14, leading=18, spaceAfter=4)
            
            # --- Header Table (Company & Logo) ---
            comp_info = []
            comp_info.append(Paragraph(f"<b>{comp.name}</b>", comp_style))
            if comp.address: comp_info.append(Paragraph(comp.address, styles['Normal']))
            if comp.phone: comp_info.append(Paragraph(f"Phone: {comp.phone}", styles['Normal']))
            
            logo_element = ""
            if logo_file:
                from reportlab.platypus import Image
                try:
                    logo_element = Image(logo_file)
                    try:
                        aspect = logo_element.imageWidth / float(logo_element.imageHeight)
                        logo_element.drawHeight = 60
                        logo_element.drawWidth = 60 * aspect
                    except AttributeError:
                        logo_element.drawHeight = 60
                        logo_element.drawWidth = 100
                except Exception as e:
                    print(f"Error loading logo: {e}")

            header_table = Table([[comp_info, logo_element]], colWidths=[350, 150])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (1,0), (1,0), 'RIGHT')
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 20))
            
            # --- Document Info & Vendor Details Table ---
            vend_info = []
            vend_info.append(Paragraph("<b>VENDOR DETAILS:</b>", styles['Heading4']))
            vend_info.append(Paragraph(f"<b>Name:</b> {vend.name}", styles['Normal']))
            if vend.phone: vend_info.append(Paragraph(f"<b>Phone:</b> {vend.phone}", styles['Normal']))
            if vend.address: vend_info.append(Paragraph(f"<b>Address:</b> {vend.address}", styles['Normal']))
            
            doc_info = []
            doc_info.append(Paragraph(f"<b>VENDOR BILL</b>", doc_style))
            
            detail_data = [
                [Paragraph("<b>Bill #</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(bill.bill_number, styles['Normal'])],
                [Paragraph("<b>Date</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(bill.bill_date.strftime('%d-%m-%Y'), styles['Normal'])]
            ]
            detail_table = Table(detail_data, colWidths=[60, 10, 150])
            detail_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            doc_info.append(detail_table)
            
            info_table = Table([[vend_info, "", doc_info]], colWidths=[240, 20, 240])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F8FAFC")),
                ('BACKGROUND', (2,0), (2,0), colors.HexColor("#F8FAFC")),
                ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#E2E8F0")),
                ('BOX', (2,0), (2,0), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Items Table
            data = [["Description", "Amount"]]
            
            desc_p = Paragraph(bill.description or "N/A", styles['Normal'])
            
            data.append([
                desc_p,
                f"{float(bill.amount):.2f}"
            ])
            # Pad with empty rows for standard table size
            min_rows = 12
            while len(data) <= min_rows:
                data.append(["", ""])
                
            t = Table(data, colWidths=[350, 100])
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
                ('LINEAFTER', (0,0), (-2,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t)
            
            elements.append(Spacer(1, 20))
            
            # Totals Table
            totals = [
                ["Total Amount:", f"{float(bill.amount):.2f}"]
            ]
            
            t_totals = Table(totals, colWidths=[200, 100])
            t_totals.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            totals_outer = Table([["", t_totals]], colWidths=[200, 300])
            totals_outer.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            elements.append(totals_outer)
            
            if bill.description:
                elements.append(Spacer(1, 20))
                desc_html = str(bill.description).replace('\n', '<br/>')
                p = Paragraph(desc_html, styles['Normal'])
                notes_table = Table([[p]], colWidths=[450])
                notes_table.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                    ('TOPPADDING', (0,0), (-1,-1), 12),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ]))
                elements.append(BottomSpacer(notes_table))
                elements.append(notes_table)

            doc.build(elements, onFirstPage=PDFGenerator._draw_page_border, onLaterPages=PDFGenerator._draw_page_border)
            return filepath

    @staticmethod
    def generate_employee_salary_pdf(company_id: int) -> str:
        from database.session import SessionLocal
        from models.company import Company
        from services.employee_service import EmployeeService
        from datetime import datetime
        from pathlib import Path
        from reportlab.lib.pagesizes import landscape, A4
        
        with SessionLocal() as s:
            comp = s.query(Company).filter(Company.id == company_id).first()
            if not comp:
                raise ValueError("Company not found.")
                
            employees = EmployeeService.get_employees(company_id)
                
            # Directory — store on Desktop
            from pathlib import Path
            pdf_dir = Path.home() / "Desktop" / "Employee_Salaries" / comp.name.replace(" ", "_")
            pdf_dir.mkdir(parents=True, exist_ok=True)
                
            report_date = datetime.now()
            month_str = report_date.strftime("%B %Y")
            filename = f"Employee_Salary_Report_{month_str.replace(' ', '_')}.pdf"
            filepath = str(pdf_dir / filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            logo_file = None
            if comp.logo_path and os.path.exists(comp.logo_path):
                logo_file = comp.logo_path
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if "RN Scanner" in comp.name:
                    fallback_path = os.path.join(base_dir, "assets", "rn_scanner_logo.png")
                    if os.path.exists(fallback_path):
                        logo_file = fallback_path
                elif "K Dynamics" in comp.name:
                    fallback_path = os.path.join(base_dir, "assets", "k_dynamics_logo.png")
                    if os.path.exists(fallback_path):
                        logo_file = fallback_path

            if logo_file:
                from reportlab.platypus import Image
                try:
                    logo = Image(logo_file)
                    try:
                        aspect = logo.imageWidth / float(logo.imageHeight)
                        logo.drawHeight = 60
                        logo.drawWidth = 60 * aspect
                    except AttributeError:
                        logo.drawHeight = 60
                        logo.drawWidth = 100
                    elements.append(logo)
                except Exception as e:
                    print(f"Error loading logo: {e}")
            
            elements.append(Paragraph(f"<b>{comp.name}</b>", styles['Heading1']))
            elements.append(Spacer(1, 10))
            
            elements.append(Paragraph(f"<b>Report Title:</b> Employee Salary Report", styles['Heading3']))
            elements.append(Paragraph(f"<b>Report Generation Date:</b> {report_date.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            
            elements.append(Spacer(1, 20))
            
            # Items Table
            data = [["Sr. No", "Employee Name", "Monthly Salary", "Current Advance", "Net Salary Payable", "Month"]]
            
            for idx, e in enumerate(employees):
                data.append([
                    str(idx + 1),
                    e["name"],
                    f"{e['salary']:,.2f}",
                    f"{e['current_advance']:,.2f}",
                    f"{e['net_salary']:,.2f}",
                    month_str
                ])
                
            t = Table(data, colWidths=[50, 200, 100, 100, 120, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1E293B")),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (2,1), (4,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(t)
            
            doc.build(elements)
            return filepath

    @staticmethod
    def generate_quotation_pdf(quotation_id: int) -> str:
        from database.session import SessionLocal
        from models.quotation import Quotation
        from models.company import Company
        from pathlib import Path

        with SessionLocal() as s:
            quot = s.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not quot:
                raise ValueError("Quotation not found.")

            comp = quot.company
            cust = quot.customer

            # Directory — Desktop\Quotations\{Company}\
            pdf_dir = Path.home() / "Desktop" / "Quotations" / comp.name.replace(" ", "_")
            pdf_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{quot.quotation_number}.pdf"
            filepath = str(pdf_dir / filename)

            from reportlab.lib.pagesizes import A4
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # Header / Logo
            logo_file = None
            if comp.logo_path and os.path.exists(comp.logo_path):
                logo_file = comp.logo_path
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if "RN Scanner" in comp.name:
                    fallback = os.path.join(base_dir, "assets", "rn_scanner_logo.png")
                    if os.path.exists(fallback):
                        logo_file = fallback
                elif "K Dynamics" in comp.name:
                    fallback = os.path.join(base_dir, "assets", "k_dynamics_logo.png")
                    if os.path.exists(fallback):
                        logo_file = fallback



            from reportlab.lib.styles import ParagraphStyle
            comp_style = ParagraphStyle('CompStyle', parent=styles['Normal'], fontSize=18, leading=22, spaceAfter=4)
            doc_style = ParagraphStyle('DocStyle', parent=styles['Normal'], fontSize=14, leading=18, spaceAfter=4)

            # --- Header Table (Company & Logo) ---
            comp_info = []
            comp_info.append(Paragraph(f"<b>{comp.name}</b>", comp_style))
            if comp.address:
                comp_info.append(Paragraph(comp.address, styles['Normal']))
            if comp.phone:
                comp_info.append(Paragraph(f"Phone: {comp.phone}", styles['Normal']))

            logo_element = ""
            if logo_file:
                from reportlab.platypus import Image
                try:
                    logo_element = Image(logo_file)
                    try:
                        aspect = logo_element.imageWidth / float(logo_element.imageHeight)
                        logo_element.drawHeight = 60
                        logo_element.drawWidth = 60 * aspect
                    except AttributeError:
                        logo_element.drawHeight = 60
                        logo_element.drawWidth = 100
                except Exception as e:
                    print(f"Error loading logo: {e}")

            header_table = Table([[comp_info, logo_element]], colWidths=[350, 150])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (1,0), (1,0), 'RIGHT')
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 20))

            # --- Document Info & Bill To Table ---
            bill_info = []
            bill_info.append(Paragraph("<b>QUOTATION FOR:</b>", styles['Heading4']))
            bill_info.append(Paragraph(f"<b>Name:</b> {cust.name}", styles['Normal']))
            if cust.phone:
                bill_info.append(Paragraph(f"<b>Phone:</b> {cust.phone}", styles['Normal']))
            if cust.address:
                bill_info.append(Paragraph(f"<b>Address:</b> {cust.address}", styles['Normal']))

            doc_info = []
            doc_info.append(Paragraph(f"<b>QUOTATION</b>", doc_style))
            
            detail_data = [
                [Paragraph("<b>Quotation #</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(quot.quotation_number, styles['Normal'])],
                [Paragraph("<b>Date</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(quot.issue_date.strftime('%d-%m-%Y'), styles['Normal'])]
            ]
            if quot.valid_until:
                detail_data.append([Paragraph("<b>Valid Until</b>", styles['Normal']), Paragraph("<b>:</b>", styles['Normal']), Paragraph(quot.valid_until.strftime('%d-%m-%Y'), styles['Normal'])])
                
            detail_table = Table(detail_data, colWidths=[70, 10, 140])
            detail_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            doc_info.append(detail_table)

            info_table = Table([[bill_info, "", doc_info]], colWidths=[240, 20, 240])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F8FAFC")),
                ('BACKGROUND', (2,0), (2,0), colors.HexColor("#F8FAFC")),
                ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#E2E8F0")),
                ('BOX', (2,0), (2,0), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))

            # Items Table — use Paragraph for description to prevent overflow
            data = [["S.No", "Description", "Qty", "Price", "Amount"]]
            for idx, item in enumerate(quot.items):
                service_name = item.service.name if item.service else "Service"
                desc_html = f"<b>{service_name}</b>"
                if item.description:
                    desc_html += f"<br/>{item.description}"
                desc_p = Paragraph(desc_html, styles['Normal'])
                data.append([
                    str(idx + 1),
                    desc_p,
                    str(item.quantity),
                    f"{float(item.unit_price):.2f}",
                    f"{float(item.total_price):.2f}",
                ])

            min_rows = 12
            while len(data) <= min_rows:
                data.append(["", "", "", "", ""])

            t = Table(data, colWidths=[40, 250, 50, 70, 80])
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
                ('LINEAFTER', (0,0), (-2,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))

            totals = [
                ["Subtotal:", f"{float(quot.total_amount):.2f}"],
                ["Discount:", f"{float(quot.discount):.2f}"],
            ]
            if comp.tax_enabled:
                totals.append([f"Tax ({float(quot.tax_percentage)}%):", f"{float(quot.tax_amount):.2f}"])
            totals.append(["Net Total:", f"{float(quot.net_amount):.2f}"])

            t_totals = Table(totals, colWidths=[200, 100])
            t_totals.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
                ('BOX', (0, -1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            totals_outer = Table([["", t_totals]], colWidths=[200, 300])
            totals_outer.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            elements.append(totals_outer)

            if quot.notes:
                elements.append(Spacer(1, 20))
                notes_html = str(quot.notes).replace('\n', '<br/>')
                p = Paragraph(notes_html, styles['Normal'])
                notes_table = Table([[p]], colWidths=[500])
                notes_table.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                    ('TOPPADDING', (0,0), (-1,-1), 12),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ]))
                elements.append(BottomSpacer(notes_table))
                elements.append(notes_table)

            doc.build(elements, onFirstPage=PDFGenerator._draw_page_border, onLaterPages=PDFGenerator._draw_page_border)
            return filepath

    @staticmethod
    def generate_customer_statement_pdf(company_id: int, customer_id: int, start_date, end_date, ledger_data) -> str:
        with SessionLocal() as s:
            comp = s.query(Company).filter(Company.id == company_id).first()
            from models.customer import Customer
            cust = s.query(Customer).filter(Customer.id == customer_id).first()
            if not comp or not cust:
                raise ValueError("Company or Customer not found.")

            from pathlib import Path
            safe = comp.name.replace(" ", "_").replace("/", "_")
            desktop = Path.home() / "Desktop"
            pdf_dir = desktop / "Statements" / safe
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)

            s_date_str = start_date.strftime("%Y%m%d") if hasattr(start_date, 'strftime') else str(start_date)
            e_date_str = end_date.strftime("%Y%m%d") if hasattr(end_date, 'strftime') else str(end_date)
            
            cust_name = cust.name.replace(" ", "_")
            filename = f"Statement_{cust_name}_{s_date_str}_to_{e_date_str}.pdf"
            filepath = os.path.join(pdf_dir, filename)

            from reportlab.lib.pagesizes import A4
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=36, bottomMargin=36)
            elements = []
            styles = getSampleStyleSheet()

            # Header
            elements.append(Paragraph(f"<b>Customer Statement — {cust.name}</b>", styles['Heading2']))
            elements.append(Paragraph(f"Company: {comp.name}", styles['Normal']))
            
            s_print = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date)
            e_print = end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else str(end_date)
            elements.append(Paragraph(f"Period: {s_print} to {e_print}", styles['Normal']))

            from datetime import datetime
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 15))

            data = [["Date", "Type", "Ref", "Desc", "Debit", "Credit", "Balance"]]
            
            for row in ledger_data:
                dt_val = row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], 'strftime') else str(row["date"])
                
                # Reportlab requires strings
                def _safe_str(val):
                    return str(val) if val else ""
                    
                def _para(text):
                    return Paragraph(text, styles['Normal'])

                desc_text = _safe_str(row.get("desc", ""))
                type_text = _safe_str(row.get("type", "")).capitalize()
                
                data.append([
                    dt_val,
                    _para(type_text),
                    _para(_safe_str(row.get("ref", ""))),
                    _para(desc_text),
                    f"{row['debit']:.2f}",
                    f"{row['credit']:.2f}",
                    f"{row['row_balance']:.2f}",
                ])

            if len(data) == 1:
                elements.append(Paragraph("No transactions for this period.", styles['Normal']))
            else:
                t = Table(data, colWidths=[65, 65, 105, 120, 60, 60, 70])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(t)
                
            elements.append(Spacer(1, 20))
            if ledger_data:
                last_bal = ledger_data[-1]['balance']
                elements.append(Paragraph(f"<b>Closing Balance: {last_bal:.2f}</b>", styles['Heading3']))

            doc.build(elements)
            return filepath

    @staticmethod
    def generate_individual_salary_slip(company_id: int, employee: dict) -> str:
        from database.session import SessionLocal
        from models.company import Company
        from datetime import datetime
        from reportlab.lib.pagesizes import A5, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from pathlib import Path
        import os
        
        with SessionLocal() as s:
            comp = s.query(Company).filter(Company.id == company_id).first()
            if not comp:
                raise ValueError("Company not found.")
                
            pdf_dir = Path.home() / "Desktop" / "Employee_Salaries" / "Slips" / comp.name.replace(" ", "_")
            pdf_dir.mkdir(parents=True, exist_ok=True)
                
            report_date = datetime.now()
            month_str = report_date.strftime("%B %Y")
            emp_name_safe = employee['name'].replace(" ", "_")
            filename = f"Salary_Slip_{emp_name_safe}_{month_str.replace(' ', '_')}.pdf"
            filepath = str(pdf_dir / filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A5), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            elements.append(Paragraph(f"<b>{comp.name}</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            elements.append(Paragraph(f"<b>Salary Slip</b> - {month_str}", styles['Heading3']))
            elements.append(Spacer(1, 15))
            
            # Employee Details
            elements.append(Paragraph(f"<b>Employee Name:</b> {employee['name']}", styles['Normal']))
            elements.append(Spacer(1, 15))
            
            # Salary Table
            data = [
                ["Description", "Amount"],
                ["Basic Monthly Salary", f"{employee['salary']:.2f}"],
                ["Advance Taken", f"{employee['current_advance']:.2f}"],
                ["Net Salary Payable", f"{employee['net_salary']:.2f}"]
            ]
            
            t = Table(data, colWidths=[250, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # bold net salary
            ]))
            elements.append(t)
            
            elements.append(Spacer(1, 30))
            elements.append(Paragraph("Generated by K Dynamics System", styles['Normal']))
            
            doc.build(elements)
            return filepath

