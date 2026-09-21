import os

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Imports
    if "from ui.components.service_details_dialog import ServiceDetailsDialog" not in content:
        content = content.replace(
            "from ui.components.dynamic_add_dialog import DynamicAddDialog",
            "from ui.components.dynamic_add_dialog import DynamicAddDialog\nfrom ui.components.service_details_dialog import ServiceDetailsDialog"
        )
    
    # 2. __init__ flags
    if "self._is_loading = False" not in content:
        content = content.replace(
            "self.advance_payment_id = None",
            "self.advance_payment_id = None\n        self._is_loading = False\n        self._suppress_popup = False"
        )
        
    # 3. _load_existing_invoice flags
    content = content.replace(
        "for item in inv[\"items\"]:",
        "self._is_loading = True\n        for item in inv[\"items\"]:"
    )
    content = content.replace(
        "self._calculate_totals()",
        "self._is_loading = False\n        self._calculate_totals()",
        1 # Only replace the first occurrence (inside _load_existing_invoice)
    )

    # 4. Table Columns
    content = content.replace(
        "self.table.setColumnCount(7)",
        "self.table.setColumnCount(8)"
    )
    content = content.replace(
        "[\"S.No\", \"Service\", \"Description\", \"Qty\", \"Price\", \"Amount\", \"\"]",
        "[\"S.No\", \"Service\", \"Description\", \"Qty\", \"Price\", \"Amount\", \"\", \"\"]"
    )
    content = content.replace(
        "h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)\n        self.table.setColumnWidth(6, 40)",
        "h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)\n        h.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)\n        self.table.setColumnWidth(6, 32)\n        self.table.setColumnWidth(7, 32)"
    )

    # 5. _on_service_entered replacement
    if "dlg = ServiceDetailsDialog(" not in content:
        old_code = '''        dlg = DynamicAddDialog(self, "Add Service", f"Service '{text}' not found.\\nDo you want to add this service?", "Default Price (Required)", "Description (Required)")
        if dlg.exec():
            price_text, desc_text = dlg.get_inputs()
            try:
                price = float(price_text)
                new_srv = ServiceCatalogue.create_service(self.company_id, "General", text, desc_text, price, self.current_user["id"])'''
        
        old_code_alt = old_code.replace("\\n", "<br>") # For invoice dialog HTML <br>
        
        new_code = '''        dlg = ServiceDetailsDialog(self, is_new_service=True, service_name=text)
        if dlg.exec():
            price, final_desc = dlg.get_inputs()
            try:
                new_srv = ServiceCatalogue.create_service(self.company_id, "General", text, final_desc, price, self.current_user["id"])'''
        
        content = content.replace(old_code, new_code)
        content = content.replace(old_code_alt, new_code)
        
        # Suppress popup for new item
        content = content.replace(
            "self._populate_service_cb()\n                self._add_item_row()\n",
            "self._populate_service_cb()\n                self._suppress_popup = True\n                self._add_item_row()\n                self._suppress_popup = False\n"
        )
        
    # 6. _add_item_row (add edit button, existing item load)
    # Existing item handling
    old_existing = '''        if existing_item:
            idx = srv_cb.findData(existing_item["service_id"])
            if idx >= 0: srv_cb.setCurrentIndex(idx)
            desc_input.setText(existing_item.get("description", ""))
            qty_input.setText(str(existing_item.get("quantity", 1)))
            price_input.setText(str(existing_item.get("unit_price", 0)))
        else:
            self._on_service_selected(row)'''
            
    new_existing = '''        if existing_item:
            self._is_loading = True
            idx = srv_cb.findData(existing_item["service_id"])
            if idx >= 0: srv_cb.setCurrentIndex(idx)
            desc_input.setText(existing_item.get("description", ""))
            qty_input.setText(str(existing_item.get("quantity", 1)))
            price_input.setText(str(existing_item.get("unit_price", 0)))
            self._is_loading = False
        else:
            if not self._suppress_popup:
                self._on_service_selected(row)'''
    content = content.replace(old_existing, new_existing)
    
    # Edit & Delete Buttons
    old_del = '''        # Delete btn
        del_btn = QPushButton("❌")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 12px; color: #E53E3E;")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda _, r=row: self._remove_item_row(r))
        self.table.setCellWidget(row, 6, del_btn)'''
        
    new_del = '''        # Edit btn
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(24, 24)
        edit_btn.setStyleSheet("border: none; background: transparent; font-size: 12px;")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda _, r=row: self._edit_item_row(r))
        self.table.setCellWidget(row, 6, edit_btn)
        
        # Delete btn
        del_btn = QPushButton("❌")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("border: none; background: transparent; font-size: 12px; color: #E53E3E;")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda _, r=row: self._remove_item_row(r))
        self.table.setCellWidget(row, 7, del_btn)'''
    content = content.replace(old_del, new_del)
    
    # update remove_item_row button index mapping
    content = content.replace("del_btn = self.table.cellWidget(r, 6)", "del_btn = self.table.cellWidget(r, 7)")
    content = content.replace("edit_btn = self.table.cellWidget(r, 6)", "edit_btn = self.table.cellWidget(r, 6)") # just in case
    # wait, remove_item_row needs to reconnect both edit and delete buttons!
    
    old_reconnect = '''            del_btn = self.table.cellWidget(r, 6)
            if del_btn:
                del_btn.clicked.disconnect()
                del_btn.clicked.connect(lambda _, current_r=r: self._remove_item_row(current_r))'''
    
    new_reconnect = '''            edit_btn = self.table.cellWidget(r, 6)
            if edit_btn:
                try: edit_btn.clicked.disconnect()
                except: pass
                edit_btn.clicked.connect(lambda _, current_r=r: self._edit_item_row(current_r))
                
            del_btn = self.table.cellWidget(r, 7)
            if del_btn:
                try: del_btn.clicked.disconnect()
                except: pass
                del_btn.clicked.connect(lambda _, current_r=r: self._remove_item_row(current_r))'''
    content = content.replace(
        '''            del_btn = self.table.cellWidget(r, 7)
            if del_btn:
                del_btn.clicked.disconnect()
                del_btn.clicked.connect(lambda _, current_r=r: self._remove_item_row(current_r))''',
        new_reconnect
    )
    
    # 7. _on_service_selected logic
    old_selected = '''    def _on_service_selected(self, row: int):
        srv_cb = self.table.cellWidget(row, 1)
        desc_input = self.table.cellWidget(row, 2)
        price_input = self.table.cellWidget(row, 4)
        if srv_cb and price_input and desc_input:
            sid = srv_cb.currentData()
            srv = next((s for s in self.filtered_services if s["id"] == sid), None)
            if srv:
                price_input.setText(str(srv["price"]))
                desc_input.setText(srv.get("description", ""))
        self._calculate_totals()'''
        
    new_selected = '''    def _on_service_selected(self, row: int):
        if self._is_loading or self._suppress_popup: return
        srv_cb = self.table.cellWidget(row, 1)
        desc_input = self.table.cellWidget(row, 2)
        price_input = self.table.cellWidget(row, 4)
        if srv_cb and price_input and desc_input:
            sid = srv_cb.currentData()
            srv = next((s for s in self.filtered_services if s["id"] == sid), None)
            if srv:
                # Pop up the details dialog for existing service
                dlg = ServiceDetailsDialog(self, is_new_service=False, service_name=srv["name"], 
                                           default_price=srv["price"], default_desc=srv.get("description", ""))
                if dlg.exec():
                    price, final_desc = dlg.get_inputs()
                    price_input.setText(str(price))
                    desc_input.setText(final_desc)
                else:
                    # Cancelled, fallback to defaults but no popup
                    price_input.setText(str(srv["price"]))
                    desc_input.setText(srv.get("description", ""))
        self._calculate_totals()
        
    def _edit_item_row(self, row: int):
        srv_cb = self.table.cellWidget(row, 1)
        desc_input = self.table.cellWidget(row, 2)
        price_input = self.table.cellWidget(row, 4)
        if srv_cb and price_input and desc_input:
            current_price = price_input.text()
            current_desc = desc_input.text()
            
            dlg = ServiceDetailsDialog(self, is_new_service=False, service_name=srv_cb.currentText(), 
                                       default_price=float(current_price) if current_price else 0.0, 
                                       default_desc=current_desc)
            if dlg.exec():
                price, final_desc = dlg.get_inputs()
                price_input.setText(str(price))
                desc_input.setText(final_desc)
                self._calculate_totals()'''
    content = content.replace(old_selected, new_selected)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {filepath}")

patch_file(r"d:\Account_System\ui\components\create_invoice_dialog.py")
patch_file(r"d:\Account_System\ui\components\create_quotation_dialog.py")
