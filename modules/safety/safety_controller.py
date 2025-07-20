# modules/safety/safety_controller.py

import re
import datetime
from dateutil.relativedelta import relativedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMessageBox, QInputDialog, QTableWidgetItem
)

from modules.safety.safety_view import SafetyView, PermitDurationDialog
from data.access_dao import (
    SafetyDAO, EmployeeDAO,
    ItemSafetyRequirementDAO, InventoryDAO
)

class SafetyController:
    def __init__(self, main_window, current_user):
        self.main_window   = main_window
        self.current_user  = current_user
        self.view          = SafetyView(self, current_user)
        self._connect_signals()
        self.load_types()

    def _connect_signals(self):
        # Permit‐type management
        self.view.add_type_btn.clicked.connect(self.on_add_type)
        self.view.edit_type_btn.clicked.connect(self.on_edit_type)
        self.view.delete_type_btn.clicked.connect(self.on_delete_type)

        # Scanner
        self.view.scan_input.returnPressed.connect(self.on_scan)

        # Employee panel
        self.view.emp_add_btn.clicked.connect(self.on_add_employee_permit)
        self.view.emp_edit_btn.clicked.connect(self.on_edit_employee_permit)
        self.view.emp_delete_btn.clicked.connect(self.on_delete_employee_permit)

        # Item panel
        self.view.req_add_btn.clicked.connect(self.on_add_item_requirement)
        self.view.req_delete_btn.clicked.connect(self.on_delete_item_requirement)

    def load_types(self):
        """
        Populate the left‐side permit types table.
        """
        types = SafetyDAO.fetch_all_types()
        tbl = self.view.type_table
        tbl.setRowCount(len(types))
        for r, t in enumerate(types):
            item = QTableWidgetItem(t.name)
            item.setData(Qt.ItemDataRole.UserRole, t.permission_id)
            tbl.setItem(r, 0, item)

    # ─── Permit‐Type Handlers ─────────────────────────────────────

    def on_add_type(self):
        name, ok = QInputDialog.getText(
            self.view, "Add Permit Type", "Type name:"
        )
        if ok and name.strip():
            SafetyDAO.add_type(name.strip())
            self.load_types()

    def on_edit_type(self):
        row = self.view.type_table.currentRow()
        if row < 0:
            return
        item = self.view.type_table.item(row, 0)
        pid  = item.data(Qt.ItemDataRole.UserRole)
        current = item.text()

        name, ok = QInputDialog.getText(
            self.view, "Edit Permit Type", "Type name:", text=current
        )
        if ok and name.strip():
            SafetyDAO.update_type(pid, name.strip())
            self.load_types()

    def on_delete_type(self):
        row = self.view.type_table.currentRow()
        if row < 0:
            return
        item = self.view.type_table.item(row, 0)
        pid  = item.data(Qt.ItemDataRole.UserRole)

        if QMessageBox.question(
            self.view, "Delete Type", "Delete this permit type?"
        ) == QMessageBox.StandardButton.Yes:
            SafetyDAO.delete_type(pid)
            self.load_types()

    # ─── Scan Handler ────────────────────────────────────────────

    def on_scan(self):
        code = self.view.scan_input.text().strip()
        self.view.scan_input.clear()

        # Employee code format: Alptraum<digits>Technologies
        m = re.fullmatch(r"Alptraum(\d+)Technologies", code)
        if m:
            uid = int(m.group(1))
        elif code.isdigit():
            uid = int(code)
        else:
            uid = None

        if uid is not None:
            emp = EmployeeDAO.fetch_by_id(uid)
            if emp:
                self._show_employee(emp)
                return

        # Otherwise try item
        itm = InventoryDAO.fetch_by_id(code)
        if itm:
            self._show_item(itm)
            return

        QMessageBox.warning(self.view, "Scan Failed", "No matching employee or item.")

    # ─── Employee Panel ─────────────────────────────────────────

    def _show_employee(self, emp):
        self.current_emp = emp
        self.view.stack.setCurrentIndex(0)
        self.view.info_label.setText(
            f"Employee: {emp.user_id} – {emp.first_name} {emp.last_name}"
        )
        rows = SafetyDAO.fetch_by_user(emp.user_id)
        tbl = self.view.emp_table
        tbl.setRowCount(len(rows))
        for r, p in enumerate(rows):
            # Permit Type
            tbl.setItem(r, 0, QTableWidgetItem(p.permit_name))

            # Issued On (store the real datetime in UserRole)
            issue_item = QTableWidgetItem(p.issue_date.strftime("%Y-%m-%d %H:%M"))
            issue_item.setData(Qt.ItemDataRole.UserRole, p.issue_date)
            tbl.setItem(r, 1, issue_item)

            # Expires On
            exp = "Permanent" if p.expire_date is None \
                  else p.expire_date.strftime("%Y-%m-%d %H:%M")
            tbl.setItem(r, 2, QTableWidgetItem(exp))

            # Issued By
            issuer = f"{p.issuer_first} {p.issuer_last}"
            tbl.setItem(r, 3, QTableWidgetItem(issuer))

    # ─── Employee permit CRUD ─────────────────────────────────
    def on_add_employee_permit(self):
        if not hasattr(self, 'current_emp'):
            return

        # ① Pick permit type
        types = [(t.permission_id, t.name) for t in SafetyDAO.fetch_all_types()]
        names = [nm for _, nm in types]
        name, ok = QInputDialog.getItem(
            self.view,
            "Select Permit Type",
            "Permit Type:",
            names,
            0,
            False
        )
        if not ok:
            return
        pid = next(pid for pid, nm in types if nm == name)

        # ② Unified duration dialog (hours/days/months/permanent)
        dlg = PermitDurationDialog(self.view)
        if not dlg.exec():
            return
        now  = datetime.datetime.now()
        val  = dlg.value
        unit = dlg.unitText

        # Compute a relativedelta or None for permanent
        if unit == "Permanent":
            delta = None
        elif unit == "Hours":
            delta = relativedelta(hours=val)
        elif unit == "Days":
            delta = relativedelta(days=val)
        else:  # "Months"
            delta = relativedelta(months=val)

        # ③ Check for an existing permit of this type
        existing = SafetyDAO.fetch_by_user(self.current_emp.user_id)
        match = next((p for p in existing if p.permit_id     == pid), None)

        if match:
            # Extend the existing one
            old_issue  = match.issue_date
            old_expire = match.expire_date

            if old_expire is None:
                # Already permanent – nothing to do
                QMessageBox.information(
                    self.view,
                    "Already Permanent",
                    "This permit is already permanent."
                )
                return

            # Start from the later of now vs old_expire
            base = old_expire if old_expire > now else now
            new_expire = base + delta if delta else None

            SafetyDAO.update_permit(
                self.current_emp.user_id,
                pid,
                old_issue,
                new_expire,
                self.current_user.user_id
            )
        else:
            # No existing permit – insert a new one
            expire = None if delta is None else now + delta
            SafetyDAO.add_permit(
                self.current_emp.user_id,
                pid,
                self.current_user.user_id,
                now,
                expire
            )

        # ④ Refresh the table
        self._show_employee(self.current_emp)

    def on_edit_employee_permit(self):
        if not hasattr(self, 'current_emp'):
            return
        tbl = self.view.emp_table
        row = tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Edit Failed", "Please select a permit to edit.")
            return

        # Identify permit
        permit_name = tbl.item(row, 0).text()
        types = [(t.permission_id, t.name) for t in SafetyDAO.fetch_all_types()]
        pid = next(pid for pid, nm in types if nm == permit_name)

        # Pull the exact issue_date object we stored
        issue = tbl.item(row, 1).data(Qt.ItemDataRole.UserRole)

        # Figure out current duration for the dialog
        expires_text = tbl.item(row, 2).text()
        if expires_text == "Permanent":
            current_unit = "Permanent"
            current_days = 1
        else:
            exp_dt = datetime.datetime.strptime(expires_text, "%Y-%m-%d %H:%M")
            delta = exp_dt - issue
            if delta.days >= 30 and delta.days % 30 == 0:
                current_unit = "Months"
                current_days = delta.days // 30
            elif delta.days >= 1:
                current_unit = "Days"
                current_days = delta.days
            else:
                current_unit = "Hours"
                current_days = max(delta.seconds // 3600, 1)

        dlg = PermitDurationDialog(self.view, current_days, current_unit)
        if not dlg.exec():
            return

        val = dlg.value
        unit = dlg.unitText

        if unit == "Permanent":
            new_expire = None
        elif unit == "Hours":
            new_expire = issue + relativedelta(hours=val)
        elif unit == "Days":
            new_expire = issue + relativedelta(days=val)
        else:
            new_expire = issue + relativedelta(months=val)

        SafetyDAO.update_permit(
            self.current_emp.user_id,
            pid,
            issue,
            new_expire,
            self.current_user.user_id
        )
        self._show_employee(self.current_emp)

    def on_delete_employee_permit(self):
        if not hasattr(self, 'current_emp'):
            return
        tbl = self.view.emp_table
        row = tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Delete Failed", "Please select a permit to delete.")
            return

        if QMessageBox.question(
            self.view,
            "Delete Permit",
            "Are you sure you want to delete this permit?"
        ) != QMessageBox.StandardButton.Yes:
            return

        # Identify permit & exact issue_date
        permit_name = tbl.item(row, 0).text()
        types = [(t.permission_id, t.name) for t in SafetyDAO.fetch_all_types()]
        pid = next(pid for pid, nm in types if nm == permit_name)
        issue = tbl.item(row, 1).data(Qt.ItemDataRole.UserRole)

        # Delete in DB and remove row in UI
        SafetyDAO.delete_permit(self.current_emp.user_id, pid, issue)
        tbl.removeRow(row)

    # ─── Item requirement CRUD ───────────────────────────────
    def on_add_item_requirement(self):
        """
        Add a safety‐permit requirement to the currently displayed item.
        If the permit is already required, show a warning instead of crashing.
        """
        if not hasattr(self, "current_item"):
            return

        # 1) Let user pick a permit type
        types = [(t.permission_id, t.name) for t in SafetyDAO.fetch_all_types()]
        names = [nm for _, nm in types]
        name, ok = QInputDialog.getItem(
            self.view,
            "Select Permit Type",
            "Permit Type:",
            names,
            0,
            False
        )
        if not ok:
            return
        pid = next(pid for pid, nm in types if nm == name)

        # 2) Check if it already exists
        existing_ids = ItemSafetyRequirementDAO.fetch_by_item(self.current_item.item_id)
        if pid in existing_ids:
            QMessageBox.warning(
                self.view,
                "Already Required",
                f"Item '{self.current_item.item_id}' already requires permit '{name}'."
            )
            return

        # 3) Insert the new requirement
        ItemSafetyRequirementDAO.add_requirement(self.current_item.item_id, pid)

        # 4) Refresh the item‐detail panel
        self._show_item(self.current_item)
        
    def on_delete_item_requirement(self):
        if not hasattr(self,'current_item'): return
        tbl = self.view.item_req_table; row=tbl.currentRow()
        if row<0: return

        name = tbl.item(row,0).text()
        type_map = {t.name:t.permission_id for t in SafetyDAO.fetch_all_types()}
        pid = type_map.get(name)
        if pid is None: return

        ItemSafetyRequirementDAO.delete_requirement(self.current_item.item_id, pid)
        self._show_item(self.current_item)

    def _show_item(self, itm):
        # keep a reference if you need to edit/delete later
        self.current_item = itm

        # switch the stacked widget to the item‐detail page (index 1)
        self.view.stack.setCurrentIndex(1)
        self.view.info_label.setText(f"Item: {itm.item_id}")

        # 1) Populate the key/value table
        tbl = self.view.item_info_table
        rows = [
            ("Category", itm.category_code),
            ("SubCategory", itm.subcategory_code),
            ("Location", itm.location),
            ("Quantity", str(itm.quantity)),
            ("Status", itm.status),
            ("Description", itm.description or ""),
            ("Price", f"{itm.price:.2f}" if itm.price is not None else ""),
        ]
        tbl.setRowCount(len(rows))
        for r, (field, val) in enumerate(rows):
            tbl.setItem(r, 0, QTableWidgetItem(field))
            tbl.setItem(r, 1, QTableWidgetItem(val))

        # 2) Populate the “requirements” list
        req_ids = ItemSafetyRequirementDAO.fetch_by_item(itm.item_id)
        type_map = {t.permission_id: t.name for t in SafetyDAO.fetch_all_types()}
        tbl2 = self.view.item_req_table
        tbl2.setRowCount(len(req_ids))
        for r, pid in enumerate(req_ids):
            name = type_map.get(pid, str(pid))
            tbl2.setItem(r, 0, QTableWidgetItem(name))
