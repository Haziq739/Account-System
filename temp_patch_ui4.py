import os
import re

inv_path = r'd:\Account_System\ui\components\create_invoice_dialog.py'
with open(inv_path, 'r', encoding='utf-8') as f:
    inv = f.read()

# Replace _save method entirely for invoice
start = inv.find('def _save(self):')
end = inv.find('def _auto_save_invoice_pdf')

new_save = '''def _save(self):
        cust_id = self.customer_cb.currentData()
        if not cust_id:
            show_message(self, "error", "Error", "Please select a customer.")
            return
            
        if not self.items_data:
            show_message(self, "error", "Error", "Please add at least one item.")
            return
            
        disc = self._get_float(self.discount_input.text())
        tax = self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0
        w_tax = self._get_float(self.w_tax_input.text()) if hasattr(self, 'w_tax_input') else 0.0
        paid = self._get_float(self.paid_input.text())
        net = self._get_float(self.net_total_lbl.text())
        
        if paid > net:
            show_message(self, "error", "Error", "Advance payment cannot exceed the Net Total.")
            return
            
        method = self.pay_method_cb.currentText()
        notes = self.notes_input.toPlainText().strip()
        
        try:
            if self.invoice_id:
                InvoiceService.update_invoice(
                    invoice_id=self.invoice_id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    paid_amount=paid,
                    payment_method=method,
                    notes=notes
                )
                show_message(self, "success", "Success", "Invoice updated successfully!")
                self._auto_save_invoice_pdf(self.invoice_id)
            else:
                inv_res = InvoiceService.create_invoice(
                    company_id=self.company_id,
                    customer_id=cust_id,
                    issue_date=date.today(),
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    paid_amount=paid,
                    payment_method=method,
                    notes=notes,
                    user_id=self.current_user["id"]
                )
                show_message(self, "success", "Success", "Invoice generated successfully!")
                
                # Check if advance payment was made, to show receipt
                if "payment" in inv_res:
                    self.advance_payment_id = inv_res["payment"]["id"]
                    
                # Auto-save PDF in background
                self._auto_save_invoice_pdf(inv_res["id"])
                    
            self._force_accept()
        except Exception as e:
            show_message(self, "error", "Error", f"Failed to save invoice:\\n{str(e)}")

    '''
inv = inv[:start] + new_save + inv[end:]
with open(inv_path, 'w', encoding='utf-8') as f: f.write(inv)


quot_path = r'd:\Account_System\ui\components\create_quotation_dialog.py'
with open(quot_path, 'r', encoding='utf-8') as f:
    quot = f.read()

start_q = quot.find('def _save(self):')
end_q = quot.find('def _auto_save_quotation_pdf')

new_save_q = '''def _save(self):
        cust_id = self.customer_cb.currentData()
        if not cust_id:
            show_message(self, "error", "Error", "Please select a customer.")
            return
            
        if not self.items_data:
            show_message(self, "error", "Error", "Please add at least one item.")
            return
            
        disc = self._get_float(self.discount_input.text())
        tax = self._get_float(self.tax_input.text()) if self.tax_enabled else 0.0
        w_tax = self._get_float(self.w_tax_input.text()) if hasattr(self, 'w_tax_input') else 0.0
        valid_date = self.validity_input.date().toPython()
        notes = self.notes_input.toPlainText().strip()
        
        try:
            if self.quotation_data:
                QuotationService.update_quotation(
                    quotation_id=self.quotation_data.id,
                    company_id=self.company_id,
                    customer_id=cust_id,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    valid_until=valid_date,
                    notes=notes
                )
                show_message(self, "success", "Success", "Quotation updated successfully!")
                self._auto_save_quotation_pdf(self.quotation_data.id)
            else:
                q_res = QuotationService.create_quotation(
                    company_id=self.company_id,
                    customer_id=cust_id,
                    issue_date=date.today(),
                    valid_until=valid_date,
                    items=self.items_data,
                    discount=disc,
                    tax_percentage=tax,
                    withholding_tax_percentage=w_tax,
                    notes=notes,
                    user_id=self.current_user["id"]
                )
                show_message(self, "success", "Success", "Quotation generated successfully!")
                self._auto_save_quotation_pdf(q_res["id"])
                    
            self._force_accept()
        except Exception as e:
            show_message(self, "error", "Error", f"Failed to save quotation:\\n{str(e)}")

    '''
quot = quot[:start_q] + new_save_q + quot[end_q:]
with open(quot_path, 'w', encoding='utf-8') as f: f.write(quot)

print("UI save methods rewritten!")
