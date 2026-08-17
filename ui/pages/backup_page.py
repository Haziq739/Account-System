"""
Backup Page — Full PDF backup interface.
Replaces the PlaceholderPage for the 'backup' sidebar slot.
Uses a background QThread so the UI never freezes during backup generation.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSizePolicy, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QColor

from ui.design_system import COLORS


# ──────────────────────────────────────────────────────────────────────────────
# Background worker
# ──────────────────────────────────────────────────────────────────────────────

class BackupWorker(QObject):
    finished = Signal(bool, str, list)   # success, folder_path, errors

    def __init__(self, company_id: int, company_name: str):
        super().__init__()
        self.company_id = company_id
        self.company_name = company_name

    def run(self):
        try:
            from services.backup_service import create_backup
            success, folder, errors = create_backup(self.company_id, self.company_name)
            self.finished.emit(success, folder, errors)
        except Exception as e:
            self.finished.emit(False, "", [str(e)])


class RestoreWorker(QObject):
    finished = Signal(bool, str)   # success, message

    def __init__(self, backup_dir: str, company_id: int, company_name: str):
        super().__init__()
        self.backup_dir = backup_dir
        self.company_id = company_id
        self.company_name = company_name

    def run(self):
        try:
            from services.backup_service import restore_backup
            success, message = restore_backup(self.backup_dir, self.company_id, self.company_name)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Backup Page
# ──────────────────────────────────────────────────────────────────────────────

def _btn(text: str, primary: bool = False) -> QPushButton:
    b = QPushButton(text)
    bg = COLORS['primary'] if primary else COLORS['bg_input']
    color = "white" if primary else COLORS['text_primary']
    border = "none" if primary else f"1px solid {COLORS['border']}"
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {color};
            border: {border};
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 13px;
            font-weight: 600;
            min-width: 160px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['primary_hover'] if primary else COLORS['bg_input']};
            {'opacity: 0.9;' if not primary else ''}
        }}
        QPushButton:pressed, QPushButton:focus {{
            border: 2px solid {COLORS['primary']};
        }}
        QPushButton:disabled {{
            background-color: {COLORS['border']};
            color: {COLORS['text_muted']};
        }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class BackupPage(QWidget):
    """Backup module page."""

    def __init__(self, current_company: dict = None, current_user: dict = None, parent=None):
        super().__init__(parent)
        self.current_company = current_company or {}
        self.current_user = current_user or {}
        self._history = []   # list of dicts: date, time, company, status, location
        self._thread = None
        self._worker = None
        self._build()

    # ── Build UI ────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 36)
        root.setSpacing(24)

        # ── Title ──────────────────────────────────────────────────────────
        title = QLabel("💾  System Backup")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 26px; font-weight: 700; background: transparent;"
        )
        root.addWidget(title)

        subtitle = QLabel(
            "Creates a complete PDF snapshot of all records for the currently selected company.\n"
            "Backups are stored on your Desktop and never overwrite previous backups."
        )
        subtitle.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; background: transparent;"
        )
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # ── Info Card ──────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 14px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 22, 28, 22)
        card_layout.setSpacing(14)

        # Active company row
        comp_row = QHBoxLayout()
        comp_lbl = QLabel("Active Company:")
        comp_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 600; background: transparent;"
        )
        self.company_value_lbl = QLabel(self._company_name())
        self.company_value_lbl.setStyleSheet(
            f"color: {COLORS['primary']}; font-size: 13px; font-weight: 700; background: transparent;"
        )
        comp_row.addWidget(comp_lbl)
        comp_row.addWidget(self.company_value_lbl)
        comp_row.addStretch()
        card_layout.addLayout(comp_row)

        # Backup location row
        loc_row = QHBoxLayout()
        loc_lbl = QLabel("Backup Location:")
        loc_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 600; background: transparent;"
        )
        from pathlib import Path
        desktop_path = str(Path.home() / "Desktop" / "K_Dynamics_Backups")
        loc_val = QLabel(desktop_path)
        loc_val.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 13px; background: transparent;"
        )
        loc_row.addWidget(loc_lbl)
        loc_row.addWidget(loc_val)
        loc_row.addStretch()
        card_layout.addLayout(loc_row)

        # ── Divider ───────────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['divider']}; border: none; max-height: 1px;")
        card_layout.addWidget(divider)

        # ── Status label ──────────────────────────────────────────────────
        self.status_lbl = QLabel("Ready to create backup.")
        self.status_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 13px; background: transparent;"
        )
        self.status_lbl.setWordWrap(True)
        card_layout.addWidget(self.status_lbl)

        # ── Button row ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.backup_btn = _btn("🛡️  Create Backup", primary=True)
        self.backup_btn.clicked.connect(self._on_create_backup)
        self.restore_btn = _btn("♻️  Restore Backup", primary=False)
        self.restore_btn.clicked.connect(self._on_restore_backup)
        btn_row.addWidget(self.backup_btn)
        btn_row.addWidget(self.restore_btn)
        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        root.addWidget(card)

        # ── Backup History ────────────────────────────────────────────────
        hist_lbl = QLabel("Backup History")
        hist_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 17px; font-weight: 700; background: transparent;"
        )
        root.addWidget(hist_lbl)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Time", "Company", "Status", "Location"])
        self.history_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setShowGrid(False)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 10px;
                color: {COLORS['text_primary']};
                gridline-color: transparent;
                font-size: 13px;
                alternate-background-color: {COLORS['bg_input']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid {COLORS['border_card']};
                font-weight: 600;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        hdr = self.history_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.history_table)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _company_name(self) -> str:
        if self.current_company:
            return self.current_company.get("name", "Unknown Company")
        return "No Company Selected"

    def _company_id(self):
        if self.current_company:
            return self.current_company.get("id")
        return None

    def set_company(self, company: dict):
        """Called by MainWindow when the active company changes."""
        self.current_company = company or {}
        self.company_value_lbl.setText(self._company_name())
        self.status_lbl.setText("Ready to create backup.")

    # ── Backup Logic ─────────────────────────────────────────────────────────

    def _on_create_backup(self):
        company_id = self._company_id()
        company_name = self._company_name()

        if not company_id:
            self.status_lbl.setText("⚠️  No company selected. Please select a company first.")
            self.status_lbl.setStyleSheet(
                f"color: {COLORS.get('danger', '#EF4444')}; font-size: 13px; background: transparent;"
            )
            return

        # Disable button during backup
        self.backup_btn.setEnabled(False)
        self.status_lbl.setStyleSheet(
            f"color: {COLORS['primary']}; font-size: 13px; background: transparent;"
        )
        self.status_lbl.setText(f"⏳  Creating backup for {company_name}... Please wait.")

        # Run in background thread
        self._thread = QThread()
        self._worker = BackupWorker(company_id, company_name)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_backup_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_backup_finished(self, success: bool, folder: str, errors: list):
        from datetime import datetime
        now = datetime.now()

        if success:
            self.status_lbl.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 13px; font-weight: 600; background: transparent;"
            )
            self.status_lbl.setText(
                f"✅  Backup created successfully!\n📁  Location: {folder}"
            )
            status_text = "✓ Success"
        else:
            failed = ", ".join(errors) if errors else "Unknown error"
            self.status_lbl.setStyleSheet(
                f"color: {COLORS.get('danger', '#EF4444')}; font-size: 13px; background: transparent;"
            )
            self.status_lbl.setText(
                f"⚠️  Backup completed with errors.\nFailed modules: {failed}\n📁  Partial backup: {folder}"
            )
            status_text = "⚠ Partial"

        # Add to history
        self._history.insert(0, {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "company": self._company_name(),
            "status": status_text,
            "location": folder,
        })
        self._refresh_history_table()

        # Re-enable button
        self.backup_btn.setEnabled(True)

    def _refresh_history_table(self):
        self.history_table.setRowCount(len(self._history))
        for row, entry in enumerate(self._history):
            status_item = QTableWidgetItem(entry["status"])
            if "Success" in entry["status"]:
                status_item.setForeground(QColor(COLORS['success']))
            else:
                status_item.setForeground(QColor(COLORS.get('danger', '#EF4444')))

            self.history_table.setItem(row, 0, QTableWidgetItem(entry["date"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry["time"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(entry["company"]))
            self.history_table.setItem(row, 3, status_item)
            self.history_table.setItem(row, 4, QTableWidgetItem(entry["location"]))

    # ── Restore Logic ────────────────────────────────────────────────────────

    def _on_restore_backup(self):
        company_id = self._company_id()
        company_name = self._company_name()

        if not company_id:
            self.status_lbl.setText("⚠️  No company selected. Please select a company first.")
            self.status_lbl.setStyleSheet(f"color: {COLORS.get('danger', '#EF4444')}; font-size: 13px; background: transparent;")
            return

        from pathlib import Path
        desktop_path = str(Path.home() / "Desktop" / "K_Dynamics_Backups")
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder to Restore",
            desktop_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if not folder:
            return

        # Show Confirmation Dialog
        msg = QMessageBox(self)
        msg.setWindowTitle("Restore Backup Confirmation")
        msg.setText(f"You selected a backup. {company_name} is currently selected.\n\n"
                    f"Restoring this backup will replace the current {company_name} data with the selected backup.\n"
                    f"A safety backup of the current database will be created first.\n\n"
                    f"Do you want to continue?")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return

        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.status_lbl.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px; background: transparent;")
        self.status_lbl.setText(f"⏳  Restoring backup... Please wait.")

        self._thread = QThread()
        self._worker = RestoreWorker(folder, company_id, company_name)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_restore_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_restore_finished(self, success: bool, message: str):
        if success:
            self.status_lbl.setStyleSheet(f"color: {COLORS['success']}; font-size: 13px; font-weight: 600; background: transparent;")
            self.status_lbl.setText(f"✅  Backup restored successfully!\n{message}")
            
            # Show a success popup to let them know it's done
            QMessageBox.information(self, "Restore Successful", "Backup restored successfully. Data has been reloaded.")
            
            # Force UI to reload everything and purge old SQLAlchemy connections
            main_win = self.window()
            if hasattr(main_win, '_on_company_changed'):
                main_win._on_company_changed(self._company_id())
            elif hasattr(main_win, 'refresh_theme'):
                main_win.refresh_theme()
        else:
            self.status_lbl.setStyleSheet(f"color: {COLORS.get('danger', '#EF4444')}; font-size: 13px; background: transparent;")
            self.status_lbl.setText(f"⚠️  Restore Failed.\n{message}")
            QMessageBox.critical(self, "Restore Failed", message)

        self.backup_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)

