"""
Backup Service — Copies individual PDF documents into a timestamped backup folder.
For modules with individual PDFs (Invoices, Quotations, Day Book, Vendor Bills,
Employee Salaries): copies the actual individual files.
For reference-only modules (Customers, Vendors, Ledger, Payments, etc.): generates
a readable summary PDF.
Never inserts, updates, or deletes any database records.
"""
import os
import shutil
from datetime import datetime, date
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from database.session import SessionLocal
from utils.logger import logger


def _desktop() -> Path:
    return Path.home() / "Desktop"


def _backup_root() -> Path:
    return _desktop() / "K_Dynamics_Backups"


def _safe_str(v) -> str:
    return "" if v is None else str(v)


def _fmt_date(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v)


def _fmt_num(v) -> str:
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return _safe_str(v)


def _styles():
    return getSampleStyleSheet()


def _build_doc(filepath: str, elements: list, landscape_mode: bool = False):
    pagesize = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(
        filepath, pagesize=pagesize,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
    )
    doc.build(elements)


def _header_style():
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FF")]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ])


def _para(text, styles, style='Normal') -> Paragraph:
    """Wraps text in Paragraph so long strings word-wrap inside their column."""
    return Paragraph(_safe_str(text), styles[style])


# ──────────────────────────────────────────────────────────────────────────────
# PART 1 — COPY INDIVIDUAL PDFs
# ──────────────────────────────────────────────────────────────────────────────

def _copy_folder(src_folder: Path, dst_folder: Path) -> tuple:
    """
    Copies all .pdf files from src_folder into dst_folder.
    Returns (files_copied: int, errors: list[str])
    """
    errors = []
    copied = 0
    if not src_folder.exists():
        return 0, []
    dst_folder.mkdir(parents=True, exist_ok=True)
    for pdf_file in src_folder.glob("*.pdf"):
        try:
            shutil.copy2(str(pdf_file), str(dst_folder / pdf_file.name))
            copied += 1
        except Exception as e:
            errors.append(f"{pdf_file.name}: {e}")
    return copied, errors


def _backup_invoices(company_id: int, company_name: str, backup_folder: Path) -> tuple:
    """Copy all individual invoice PDFs from both old and Desktop paths. Regenerate if missing."""
    safe = company_name.replace(" ", "_")
    dst = backup_folder / "Invoices" / safe
    dst.mkdir(parents=True, exist_ok=True)
    
    errors = []
    copied = 0
    
    from models.invoice import Invoice
    from services.pdf_generator import PDFGenerator
    with SessionLocal() as s:
        invoices = s.query(Invoice.id, Invoice.invoice_number).filter(
            Invoice.company_id == company_id, 
            Invoice.is_deleted == False
        ).all()
        
    # Check old path: D:/Account_System/invoices
    old_src = Path("D:/Account_System/invoices")
    new_src = _desktop() / "invoices"
    
    for inv_id, inv_num in invoices:
        filename = f"Invoice_{inv_num}.pdf"
        copied_this = False
        
        # 1. Try to copy from existing locations
        if old_src.exists():
            pdf_file = old_src / filename
            if pdf_file.exists():
                try:
                    shutil.copy2(str(pdf_file), str(dst / filename))
                    copied += 1
                    copied_this = True
                except Exception as e:
                    errors.append(f"{filename} (copy old): {e}")
                    
        if not copied_this and new_src.exists():
            pdf_file = new_src / filename
            if pdf_file.exists():
                try:
                    shutil.copy2(str(pdf_file), str(dst / filename))
                    copied += 1
                    copied_this = True
                except Exception as e:
                    errors.append(f"{filename} (copy new): {e}")
                    
        # 2. If it still doesn't exist anywhere, regenerate it retroactively!
        if not copied_this:
            try:
                gen_path = PDFGenerator.generate_invoice_pdf(inv_id)
                if gen_path and Path(gen_path).exists():
                    shutil.copy2(gen_path, str(dst / filename))
                    copied += 1
                else:
                    errors.append(f"{filename}: Regeneration returned invalid path")
            except Exception as e:
                errors.append(f"{filename} (regeneration failed): {e}")
                
    return copied > 0, errors


def _backup_quotations(company_id: int, company_name: str, backup_folder: Path) -> tuple:
    """Copy individual quotation PDFs for this company. Regenerate if missing."""
    safe = company_name.replace(" ", "_")
    dst = backup_folder / "Quotations" / safe
    dst.mkdir(parents=True, exist_ok=True)
    
    errors = []
    copied = 0
    
    from models.quotation import Quotation
    from services.pdf_generator import PDFGenerator
    with SessionLocal() as s:
        quotations = s.query(Quotation.id, Quotation.quotation_number).filter(
            Quotation.company_id == company_id, 
            Quotation.is_deleted == False
        ).all()
        
    # Old path might be in D:/Account_System/Quotations
    old_src = Path("D:/Account_System/Quotations") / safe
    new_src = _desktop() / "Quotations" / safe
    
    for q_id, q_num in quotations:
        filename = f"{q_num}.pdf"
        copied_this = False
        
        # 1. Try existing paths
        if old_src.exists():
            pdf_file = old_src / filename
            if pdf_file.exists():
                try:
                    shutil.copy2(str(pdf_file), str(dst / filename))
                    copied += 1
                    copied_this = True
                except Exception as e:
                    errors.append(f"{filename} (copy old): {e}")
                    
        if not copied_this and new_src.exists():
            pdf_file = new_src / filename
            if pdf_file.exists():
                try:
                    shutil.copy2(str(pdf_file), str(dst / filename))
                    copied += 1
                    copied_this = True
                except Exception as e:
                    errors.append(f"{filename} (copy new): {e}")
                    
        # 2. Retroactively generate if missing
        if not copied_this:
            try:
                gen_path = PDFGenerator.generate_quotation_pdf(q_id)
                if gen_path and Path(gen_path).exists():
                    shutil.copy2(gen_path, str(dst / filename))
                    copied += 1
                else:
                    errors.append(f"{filename}: Regeneration returned invalid path")
            except Exception as e:
                errors.append(f"{filename} (regeneration failed): {e}")
    
    return copied > 0, errors


def _backup_daybook(company_id: int, company_name: str, backup_folder: Path) -> tuple:
    """Copy individual Day Book PDFs for this company and generate today's if missing."""
    safe = company_name.replace(" ", "_")
    dst = backup_folder / "day_book" / safe
    
    # Force creation of the backup directory even if empty
    dst.mkdir(parents=True, exist_ok=True)
    
    c1, e1 = _copy_folder(Path.home() / "Documents" / "Day_Book" / safe, dst)
    c2, e2 = _copy_folder(_desktop() / "Day_Book" / safe, dst)
    
    # Also explicitly generate "Today's" Day Book on the fly and put it in the backup
    # just in case the midnight cron hasn't fired yet
    try:
        from datetime import date
        from services.daybook_service import DayBookService
        from services.pdf_generator import PDFGenerator
        import shutil
        
        today = date.today()
        data = DayBookService.get_daybook_transactions(company_id, today)
        gen_path = PDFGenerator.generate_daybook_pdf(company_id, today, data)
        if gen_path and Path(gen_path).exists():
            shutil.copy2(gen_path, str(dst / Path(gen_path).name))
            c2 += 1
    except Exception as e:
        e2.append(f"Failed to auto-generate today's day book during backup: {e}")
    
    return c1 + c2 > 0, e1 + e2


def _backup_vendor_bills(company_id: int, company_name: str, backup_folder: Path) -> tuple:
    """Copy individual Vendor Bill PDFs for this company. Regenerate if missing."""
    safe = company_name.replace(" ", "_")
    dst = backup_folder / "Vendor_Bills" / safe
    dst.mkdir(parents=True, exist_ok=True)
    
    errors = []
    copied = 0
    
    from models.vendor_bill import VendorBill
    from services.pdf_generator import PDFGenerator
    with SessionLocal() as s:
        bills = s.query(VendorBill.id, VendorBill.bill_number).filter(
            VendorBill.company_id == company_id, 
            VendorBill.is_deleted == False
        ).all()
        
    old_src = Path.home() / "Documents" / "Vendor_Bills" / safe
    new_src = _desktop() / "Vendor_Bills" / safe
    
    for b_id, b_num in bills:
        filename = f"Vendor_Bill_{b_num}.pdf"
        copied_this = False
        
        # 1. Try existing paths
        if old_src.exists():
            pdf_file = old_src / filename
            if pdf_file.exists():
                try:
                    shutil.copy2(str(pdf_file), str(dst / filename))
                    copied += 1
                    copied_this = True
                except Exception as e:
                    errors.append(f"{filename} (copy old): {e}")
                    
        if not copied_this and new_src.exists():
            pdf_file = new_src / filename
            if pdf_file.exists():
                try:
                    shutil.copy2(str(pdf_file), str(dst / filename))
                    copied += 1
                    copied_this = True
                except Exception as e:
                    errors.append(f"{filename} (copy new): {e}")
                    
        # 2. Retroactively generate if missing
        if not copied_this:
            try:
                gen_path = PDFGenerator.generate_vendor_bill_pdf(b_id)
                if gen_path and Path(gen_path).exists():
                    shutil.copy2(gen_path, str(dst / filename))
                    copied += 1
                else:
                    errors.append(f"{filename}: Regeneration returned invalid path")
            except Exception as e:
                errors.append(f"{filename} (regeneration failed): {e}")
    
    return copied > 0, errors


def _backup_employee_salaries(company_name: str, backup_folder: Path) -> tuple:
    """Copy individual Employee Salary PDFs for this company."""
    safe = company_name.replace(" ", "_")
    dst = backup_folder / "employee_salaries" / safe
    
    c1, e1 = _copy_folder(Path.home() / "Documents" / "Employee_Salary_Reports" / safe, dst)
    c2, e2 = _copy_folder(_desktop() / "Employee_Salaries" / safe, dst)
    
    return c1 + c2 > 0, e1 + e2


# ──────────────────────────────────────────────────────────────────────────────
# PART 2 — GENERATE SUMMARY PDFs FOR REFERENCE MODULES
# (These don't have individual document PDFs — they are database records)
# ──────────────────────────────────────────────────────────────────────────────

def _gen_customers_summary(company_id: int, company_name: str, folder: Path) -> bool:
    try:
        from models.invoice import Invoice
        from models.payment import Payment
        from models.customer import Customer
        from sqlalchemy import distinct, or_
        styles = _styles()
        elements = [
            _para(f"<b>Customers — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            Spacer(1, 10),
        ]
        with SessionLocal() as s:
            sub1 = s.query(distinct(Invoice.customer_id)).filter(
                Invoice.company_id == company_id, Invoice.is_deleted == False
            ).subquery()
            sub2 = s.query(distinct(Payment.customer_id)).filter(
                Payment.company_id == company_id, Payment.is_deleted == False
            ).subquery()
            from sqlalchemy import select
            customers = s.query(Customer).filter(
                Customer.is_deleted == False,
                or_(Customer.id.in_(select(sub1)), Customer.id.in_(select(sub2)))
            ).order_by(Customer.id.asc()).all()

            data = [["Sr.", "Customer Name", "Phone", "Address", "Type", "Date Added"]]
            for i, c in enumerate(customers, 1):
                data.append([
                    str(i),
                    _para(c.name, styles),
                    _para(c.phone, styles),
                    _para(c.address, styles),
                    _safe_str(c.customer_type),
                    _fmt_date(c.created_at),
                ])

        if len(data) == 1:
            elements.append(_para("No records found.", styles))
        else:
            t = Table(data, colWidths=[28, 140, 80, 160, 65, 75])
            t.setStyle(_header_style())
            elements.append(t)

        folder.mkdir(parents=True, exist_ok=True)
        _build_doc(str(folder / "Customers.pdf"), elements)
        return True
    except Exception as e:
        logger.error(f"Gen Customers summary error: {e}")
        return False


def _gen_vendors_summary(company_id: int, company_name: str, folder: Path) -> bool:
    try:
        from models.vendor import Vendor
        styles = _styles()
        elements = [
            _para(f"<b>Vendors — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            Spacer(1, 10),
        ]
        with SessionLocal() as s:
            vendors = s.query(Vendor).filter(
                Vendor.company_id == company_id, Vendor.is_deleted == False
            ).order_by(Vendor.id.asc()).all()

            data = [["Sr.", "Vendor Name", "Phone", "Address", "Date Added"]]
            for i, v in enumerate(vendors, 1):
                data.append([
                    str(i),
                    _para(v.name, styles),
                    _para(v.phone, styles),
                    _para(v.address, styles),
                    _fmt_date(v.created_at),
                ])

        if len(data) == 1:
            elements.append(_para("No records found.", styles))
        else:
            t = Table(data, colWidths=[30, 150, 90, 200, 80])
            t.setStyle(_header_style())
            elements.append(t)

        folder.mkdir(parents=True, exist_ok=True)
        _build_doc(str(folder / "Vendors.pdf"), elements)
        return True
    except Exception as e:
        logger.error(f"Gen Vendors summary error: {e}")
        return False


def _gen_ledger_summary(company_id: int, company_name: str, folder: Path) -> bool:
    try:
        from models.ledger import CustomerLedger
        from sqlalchemy.orm import joinedload
        styles = _styles()
        elements = [
            _para(f"<b>Customer Ledger — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            Spacer(1, 10),
        ]
        with SessionLocal() as s:
            entries = s.query(CustomerLedger).options(
                joinedload(CustomerLedger.customer)
            ).filter(CustomerLedger.company_id == company_id).order_by(
                CustomerLedger.transaction_date.asc()
            ).all()

            data = [["Date", "Customer", "Type", "Reference", "Debit", "Credit", "Balance", "Description"]]
            for e in entries:
                data.append([
                    _fmt_date(e.transaction_date),
                    _para(e.customer.name if e.customer else "", styles),
                    _safe_str(e.transaction_type),
                    _safe_str(e.reference_id),
                    _fmt_num(e.debit),
                    _fmt_num(e.credit),
                    _fmt_num(e.balance),
                    _para(e.description, styles),
                ])

        if len(data) == 1:
            elements.append(_para("No records found.", styles))
        else:
            t = Table(data, colWidths=[55, 100, 65, 75, 58, 58, 65, 130])
            t.setStyle(_header_style())
            elements.append(t)

        folder.mkdir(parents=True, exist_ok=True)
        _build_doc(str(folder / "Customer_Ledger.pdf"), elements, landscape_mode=True)
        return True
    except Exception as e:
        logger.error(f"Gen Ledger summary error: {e}")
        return False


def _gen_payments_summary(company_id: int, company_name: str, folder: Path) -> bool:
    try:
        from models.payment import Payment
        from sqlalchemy.orm import joinedload
        styles = _styles()
        elements = [
            _para(f"<b>Payment History — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            Spacer(1, 10),
        ]
        with SessionLocal() as s:
            payments = s.query(Payment).options(
                joinedload(Payment.customer), joinedload(Payment.invoice)
            ).filter(
                Payment.company_id == company_id, Payment.is_deleted == False
            ).order_by(Payment.payment_date.desc()).all()

            data = [["Receipt #", "Date", "Customer", "Type", "Amount", "Method", "Invoice #"]]
            for p in payments:
                ptype = "Advance" if p.is_advance else "Payment"
                data.append([
                    _safe_str(p.receipt_number),
                    _fmt_date(p.payment_date),
                    _para(p.customer.name if p.customer else "", styles),
                    ptype,
                    _fmt_num(p.amount),
                    _safe_str(p.payment_method),
                    _safe_str(p.invoice.invoice_number if p.invoice else ""),
                ])

        if len(data) == 1:
            elements.append(_para("No records found.", styles))
        else:
            t = Table(data, colWidths=[75, 60, 120, 58, 68, 75, 80])
            t.setStyle(_header_style())
            elements.append(t)

        folder.mkdir(parents=True, exist_ok=True)
        _build_doc(str(folder / "Payment_History.pdf"), elements, landscape_mode=True)
        return True
    except Exception as e:
        logger.error(f"Backup Payments summary error: {e}")
        return False


def _gen_statements_summary(company_id: int, company_name: str, folder: Path) -> bool:
    try:
        from models.customer import Customer
        from models.ledger import CustomerLedger
        from models.invoice import Invoice
        from models.payment import Payment
        from sqlalchemy import distinct, or_, select
        from sqlalchemy.orm import joinedload
        styles = _styles()
        elements = [
            _para(f"<b>Customer Statements — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            Spacer(1, 10),
        ]
        with SessionLocal() as s:
            sub1 = s.query(distinct(Invoice.customer_id)).filter(
                Invoice.company_id == company_id, Invoice.is_deleted == False
            ).subquery()
            sub2 = s.query(distinct(Payment.customer_id)).filter(
                Payment.company_id == company_id, Payment.is_deleted == False
            ).subquery()
            customers = s.query(Customer).filter(
                Customer.is_deleted == False,
                or_(Customer.id.in_(select(sub1)), Customer.id.in_(select(sub2)))
            ).order_by(Customer.name.asc()).all()

            folder.mkdir(parents=True, exist_ok=True)

            for cust in customers:
                elements = [
                    _para(f"<b>Customer Statement — {cust.name}</b>", styles, 'Heading2'),
                    _para(f"Company: {company_name}", styles),
                    _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
                    Spacer(1, 10),
                ]
                
                rows = s.query(CustomerLedger).filter(
                    CustomerLedger.company_id == company_id,
                    CustomerLedger.customer_id == cust.id
                ).order_by(CustomerLedger.transaction_date.asc()).all()

                data = [["Date", "Type", "Reference", "Debit", "Credit", "Balance", "Description"]]
                for row in rows:
                    data.append([
                        _fmt_date(row.transaction_date),
                        _safe_str(row.transaction_type),
                        _safe_str(row.reference_id),
                        _fmt_num(row.debit),
                        _fmt_num(row.credit),
                        _fmt_num(row.balance),
                        _para(row.description, styles),
                    ])

                if len(data) == 1:
                    elements.append(_para("  No transactions.", styles))
                else:
                    t = Table(data, colWidths=[65, 75, 85, 65, 65, 75, 185])
                    t.setStyle(_header_style())
                    elements.append(t)
                
                cust_filename = f"{cust.name.replace(' ', '_')}_Statement.pdf"
                _build_doc(str(folder / cust_filename), elements, landscape_mode=True)
                
        return True
    except Exception as e:
        logger.error(f"Backup Statements summary error: {e}")
        return False


def _gen_employee_data_summary(company_id: int, company_name: str, folder: Path) -> bool:
    """Generates Employee Salaries and Advances summary PDFs."""
    try:
        from services.employee_service import EmployeeService
        from models.employee_advance import EmployeeAdvance
        from sqlalchemy.orm import joinedload
        styles = _styles()

        # — Employee Salaries Summary —
        elements = [
            _para(f"<b>Employee Salaries — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            _para(f"Month: {datetime.now().strftime('%B %Y')}", styles),
            Spacer(1, 10),
        ]
        employees = EmployeeService.get_employees(company_id)
        data = [["Sr.", "Employee Name", "Monthly Salary", "Current Advance", "Net Salary"]]
        for i, e in enumerate(employees, 1):
            data.append([
                str(i),
                _para(e["name"], styles),
                _fmt_num(e["salary"]),
                _fmt_num(e["current_advance"]),
                _fmt_num(e["net_salary"]),
            ])
        if len(data) == 1:
            elements.append(_para("No records found.", styles))
        else:
            t = Table(data, colWidths=[30, 200, 100, 110, 100])
            t.setStyle(_header_style())
            elements.append(t)

        folder.mkdir(parents=True, exist_ok=True)
        _build_doc(str(folder / "Employee_Salaries.pdf"), elements)

        # — Employee Advances Summary —
        elements2 = [
            _para(f"<b>Employee Advances — {company_name}</b>", styles, 'Heading2'),
            _para(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles),
            Spacer(1, 10),
        ]
        with SessionLocal() as s:
            advances = s.query(EmployeeAdvance).options(
                joinedload(EmployeeAdvance.employee)
            ).filter(
                EmployeeAdvance.company_id == company_id
            ).order_by(EmployeeAdvance.advance_date.desc()).all()

            data2 = [["Employee", "Amount", "Date", "Month", "Status", "Description"]]
            for a in advances:
                data2.append([
                    _para(a.employee.name if a.employee else "", styles),
                    _fmt_num(a.amount),
                    _fmt_date(a.advance_date),
                    _safe_str(a.month),
                    "Cleared" if a.is_cleared else "Active",
                    _para(a.description, styles),
                ])

        if len(data2) == 1:
            elements2.append(_para("No records found.", styles))
        else:
            t2 = Table(data2, colWidths=[120, 70, 70, 70, 70, 70, 70])
            t2.setStyle(_header_style())
            elements2.append(t2)

        _build_doc(str(folder / "Employee_Advances.pdf"), elements2, landscape_mode=True)
        return True
    except Exception as e:
        logger.error(f"Backup Employee data summary error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Backup Summary PDF
# ──────────────────────────────────────────────────────────────────────────────

def _gen_backup_summary(backup_folder: Path, company_name: str, stats: dict) -> bool:
    try:
        styles = _styles()
        now = datetime.now()
        elements = [
            _para("<b>System Backup Summary</b>", styles, 'Title'),
            Spacer(1, 14),
        ]

        info_data = [
            ["Application", "RN Scanner / K Dynamics Business Management System"],
            ["Company Backed Up", company_name],
            ["Backup Date", now.strftime("%Y-%m-%d")],
            ["Backup Time", now.strftime("%H:%M:%S")],
            ["Backup Location", str(backup_folder)],
            ["Backup Type", "Individual PDF Documents + Reference Summaries"],
        ]
        info_table = Table(info_data, colWidths=[140, 370])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor("#F5F8FF"), colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 18))
        elements.append(_para("<b>Backup Contents</b>", styles, 'Heading2'))
        elements.append(Spacer(1, 6))

        mod_data = [["Module", "Type", "Files/Status"]]
        for name, typ, status in stats["modules"]:
            mod_data.append([name, typ, status])

        mod_style = _header_style()
        mod_table = Table(mod_data, colWidths=[180, 150, 180])
        mod_table.setStyle(mod_style)
        elements.append(mod_table)

        elements.append(Spacer(1, 14))
        elements.append(_para(
            "<b>Note:</b> Individual document PDFs (Invoices, Quotations, Vendor Bills, Day Book, "
            "Employee Salaries) are copied from your Desktop storage folders as-is. "
            "Summary PDFs are generated for database reference records (Customers, Vendors, Ledger, etc.).",
            styles
        ))

        _build_doc(str(backup_folder / "Backup_Summary.pdf"), elements)
        return True
    except Exception as e:
        logger.error(f"Backup Summary PDF error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Main Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def create_backup(company_id: int, company_name: str) -> tuple:
    """
    Create a full backup for ONE company.
    - Copies individual PDF files from Desktop storage folders.
    - Generates reference summary PDFs for database-only modules.
    Returns: (success: bool, backup_folder_path: str, errors: list[str])
    """
    try:
        root = _backup_root()
        root.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        safe = company_name.replace(" ", "_").replace("/", "_")
        folder_name = f"Backup_{now.strftime('%Y-%m-%d_%H-%M-%S')}_{safe}"
        backup_folder = root / folder_name
        backup_folder.mkdir(parents=True, exist_ok=True)

        # Copy Database
        from config.settings import DATABASE_PATH
        if DATABASE_PATH.exists():
            shutil.copy2(DATABASE_PATH, backup_folder / "K_Dynamics_System.db")

        # Write Metadata
        import json
        with open(backup_folder / "backup_metadata.json", "w") as f:
            json.dump({
                "company_id": company_id,
                "company_name": company_name,
                "timestamp": now.isoformat()
            }, f)

        errors = []
        modules_status = []

        # ── Individual PDF modules (COPY from Desktop/Old paths) ───────────────

        ok, errs = _backup_invoices(company_id, company_name, backup_folder)
        count = len(list((backup_folder / "Invoices" / company_name.replace(" ", "_")).glob("*.pdf"))) if (backup_folder / "Invoices" / company_name.replace(" ", "_")).exists() else 0
        modules_status.append(("Invoices", "Individual PDFs (copied)", f"{count} files copied" if ok or count > 0 else f"Failed: {errs}"))
        if errs:
            errors.extend(errs)

        ok, errs = _backup_quotations(company_id, company_name, backup_folder)
        count = len(list((backup_folder / "Quotations" / company_name.replace(" ", "_")).glob("*.pdf"))) if (backup_folder / "Quotations" / company_name.replace(" ", "_")).exists() else 0
        modules_status.append(("Quotations", "Individual PDFs (copied)", f"{count} files copied" if ok or count > 0 else f"Failed: {errs}"))
        if errs:
            errors.extend(errs)

        ok, errs = _backup_daybook(company_id, company_name, backup_folder)
        count = len(list((backup_folder / "day_book" / company_name.replace(" ", "_")).glob("*.pdf"))) if (backup_folder / "day_book" / company_name.replace(" ", "_")).exists() else 0
        modules_status.append(("Day Book", "Individual PDFs (copied)", f"{count} files copied" if ok or count > 0 else f"Failed: {errs}"))
        if errs:
            errors.extend(errs)

        ok, errs = _backup_vendor_bills(company_id, company_name, backup_folder)
        count = len(list((backup_folder / "Vendor_Bills" / company_name.replace(" ", "_")).glob("*.pdf"))) if (backup_folder / "Vendor_Bills" / company_name.replace(" ", "_")).exists() else 0
        modules_status.append(("Vendor Bills", "Individual PDFs (copied)", f"{count} files copied" if ok or count > 0 else f"Failed: {errs}"))
        if errs:
            errors.extend(errs)

        ok, errs = _backup_employee_salaries(company_name, backup_folder)
        count = len(list((backup_folder / "employee_salaries" / company_name.replace(" ", "_")).glob("*.pdf"))) if (backup_folder / "employee_salaries" / company_name.replace(" ", "_")).exists() else 0
        modules_status.append(("Employee Salary Reports", "Individual PDFs (copied)", f"{count} files copied" if ok or count > 0 else f"Failed: {errs}"))
        if errs:
            errors.extend(errs)

        # ── Reference summary PDFs (generated from database) ───────────────

        # Create separate folders for each reference module to match user expectations
        cust_folder = backup_folder / "Customers"
        cust_folder.mkdir(parents=True, exist_ok=True)
        ok = _gen_customers_summary(company_id, company_name, cust_folder)
        modules_status.append(("Customers", "Reference Summary PDF", "✓ Generated" if ok else "✗ Failed"))
        if not ok:
            errors.append("Customers.pdf")

        vend_folder = backup_folder / "Vendors"
        vend_folder.mkdir(parents=True, exist_ok=True)
        ok = _gen_vendors_summary(company_id, company_name, vend_folder)
        modules_status.append(("Vendors", "Reference Summary PDF", "✓ Generated" if ok else "✗ Failed"))
        if not ok:
            errors.append("Vendors.pdf")

        ledger_folder = backup_folder / "Customer_Ledger"
        ledger_folder.mkdir(parents=True, exist_ok=True)
        ok = _gen_ledger_summary(company_id, company_name, ledger_folder)
        modules_status.append(("Customer Ledger", "Reference Summary PDF", "✓ Generated" if ok else "✗ Failed"))
        if not ok:
            errors.append("Customer_Ledger.pdf")

        payment_folder = backup_folder / "Payment_History"
        payment_folder.mkdir(parents=True, exist_ok=True)
        ok = _gen_payments_summary(company_id, company_name, payment_folder)
        modules_status.append(("Payment History", "Reference Summary PDF", "✓ Generated" if ok else "✗ Failed"))
        if not ok:
            errors.append("Payment_History.pdf")

        statement_folder = backup_folder / "Statements"
        statement_folder.mkdir(parents=True, exist_ok=True)
        ok = _gen_statements_summary(company_id, company_name, statement_folder)
        modules_status.append(("Statements", "Reference Summary PDF", "✓ Generated" if ok else "✗ Failed"))
        if not ok:
            errors.append("Statements.pdf")

        employee_data_folder = backup_folder / "Employee_Data"
        employee_data_folder.mkdir(parents=True, exist_ok=True)
        ok = _gen_employee_data_summary(company_id, company_name, employee_data_folder)
        modules_status.append(("Employee Data", "Reference Summary PDF", "✓ Generated" if ok else "✗ Failed"))
        if not ok:
            errors.append("Employee_Data.pdf")

        # ── Backup Summary ──────────────────────────────────────────────────
        _gen_backup_summary(backup_folder, company_name, {"modules": modules_status})

        return len(errors) == 0, str(backup_folder), errors

    except Exception as e:
        logger.error(f"Backup orchestration error: {e}")
        return False, "", [str(e)]


def restore_backup(backup_dir_str: str, target_company_id: int, target_company_name: str) -> tuple:
    import json
    import sqlite3
    
    backup_folder = Path(backup_dir_str)
    if not backup_folder.exists():
        return False, "Selected backup folder does not exist."
        
    # ── Validation 1: Metadata & Company Check ───────────────────────
    meta_file = backup_folder / "backup_metadata.json"
    if not meta_file.exists():
        has_rn = (backup_folder / "Invoices" / "RN_Scanner").exists() or (backup_folder / "Invoices" / "RN Scanner").exists()
        has_k = (backup_folder / "Invoices" / "K_Dynamics").exists() or (backup_folder / "Invoices" / "K Dynamics").exists()
        deduced = None
        if has_rn and not has_k:
            deduced = "RN Scanner"
        elif has_k and not has_rn:
            deduced = "K Dynamics"
            
        if not deduced:
            return False, "Unable to verify the company for this backup. Restore was cancelled for safety."
        if deduced != target_company_name:
            return False, f"Wrong company backup selected. The current company is {target_company_name}, but the selected backup belongs to {deduced}. Please select the correct backup."
    else:
        with open(meta_file, "r") as f:
            meta = json.load(f)
        if meta.get("company_name") != target_company_name:
            return False, f"Wrong company backup selected. The current company is {target_company_name}, but the selected backup belongs to {meta.get('company_name')}. Please select the correct backup."

    # ── Validation 2: Database exists ──────────────────────────────────
    backup_db_path = backup_folder / "K_Dynamics_System.db"
    if not backup_db_path.exists():
        return False, "Invalid backup. K_Dynamics_System.db not found in backup."
        
    # ── Pre-Restore Safety Backup ──────────────────────────────────────
    from config.settings import DATABASE_PATH
    if DATABASE_PATH.exists():
        from database.connection import engine
        engine.dispose()
        
        safe_name = f"PreRestore_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        safe_dir = _backup_root() / safe_name
        safe_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DATABASE_PATH, safe_dir / "K_Dynamics_System.db")

    # ── Replace Database ───────────────────────────────────────────────
    try:
        # Overwrite the live database file directly with the backed-up database
        shutil.copy2(backup_db_path, DATABASE_PATH)
    except Exception as e:
        return False, f"Database restore failed: {e}"

    # ── Restore Documents ──────────────────────────────────────────────
    for base_dir, desktop_sub in [
        ("Invoices", "invoices"), 
        ("Quotations", "Quotations"), 
        ("day_book", "Day_Book"), 
        ("Vendor_Bills", "Vendor_Bills"), 
        ("employee_salaries", "Employee_Salaries")
    ]:
        src_comp_dir = backup_folder / base_dir / target_company_name.replace(" ", "_")
        if not src_comp_dir.exists():
            src_comp_dir = backup_folder / base_dir / target_company_name
            
        if src_comp_dir.exists():
            dst_comp_dir = _desktop() / desktop_sub / target_company_name.replace(" ", "_")
            dst_comp_dir.mkdir(parents=True, exist_ok=True)
            for pdf in src_comp_dir.glob("*.pdf"):
                shutil.copy2(pdf, dst_comp_dir / pdf.name)

    return True, "Data has been successfully isolated and restored."

