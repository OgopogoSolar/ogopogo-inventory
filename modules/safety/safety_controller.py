# modules/safety/safety_controller.py

from PyQt6.QtWidgets import QMessageBox, QInputDialog, QTableWidgetItem
from PyQt6.QtCore import Qt
from dateutil.relativedelta import relativedelta
import datetime

from modules.safety.safety_view import SafetyView
from data.access_dao import SafetyDAO, EmployeeDAO

class SafetyController:
    def __init__(self, main_window, current_user):
        self.main_window  = main_window
        self.current_user = current_user
        self.view         = SafetyView(self, self.current_user)
        self.load_types()

    def load_types(self):
        types = SafetyDAO.fetch_all_types()
        flat  = [(t.permission_id, t.name) for t in types]
        self.view.show_types(flat)
        self.view.show_assign_types(flat)
        self.view.req_type_combo.clear()
        for pid, name in flat:
            self.view.req_type_combo.addItem(name, pid)

    def load_users(self):
        role = self.current_user.user_type.upper()
        if role == "ADMIN":
            users = EmployeeDAO.fetch_all()
        elif role == "SUPERVISOR":
            users = EmployeeDAO.fetch_by_supervisor(self.current_user.user_id)
        else:
            users = [self.current_user]
        self.view.show_employees(users)

    def on_add_type(self):
        if self.current_user.user_type.upper() == "SUPERVISOR":
            QMessageBox.warning(self.view, "Permission Denied", "Supervisors cannot create permit types.")
            return

        name, ok = QInputDialog.getText(self.view, "Add Permit Type", "Type name:")
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
        pid = self.view.type_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(
            self.view, "Delete Type", "Delete this permit type?"
        ) == QMessageBox.StandardButton.Yes:
            SafetyDAO.delete_type(pid)
            self.load_types()

    def on_scan(self):
        code = self.view.scan_input.text().strip()
        self.view.clear_scan()
        prefix, suffix = "Alptraum", "Technologies"
        if not (code.startswith(prefix) and code.endswith(suffix)):
            QMessageBox.warning(self.view, "Scan Failed", "Invalid code format.")
            return
        num = code[len(prefix):-len(suffix)]
        try:
            uid = int(num)
        except ValueError:
            QMessageBox.warning(self.view, "Scan Failed", f"Bad employee number: {num}")
            return
        emp = EmployeeDAO.fetch_by_id(uid)
        if not emp:
            QMessageBox.warning(self.view, "Scan Failed", f"Employee {uid} not found.")
            return
        self.scanned_employee = emp
        self.view.employee_label.setText(
            f"Employee: {emp.user_id} – {emp.first_name} {emp.last_name}"
        )

    def on_assign(self):
        actor = self.current_user.user_type.upper()
        if not hasattr(self, "scanned_employee"):
            QMessageBox.warning(self.view, "Assign Failed", "Please scan an employee first.")
            return

        uid = self.scanned_employee.user_id
        pid = self.view.assign_type_combo.currentData()
        if uid is None or pid is None:
            QMessageBox.warning(self.view, "Assign Failed", "Select employee and permit type.")
            return

        # Cannot assign to self
        if uid == self.current_user.user_id:
            QMessageBox.warning(self.view, "Assign Failed", "You cannot assign a permit to yourself.")
            return

        target = EmployeeDAO.fetch_by_id(uid)
        if not target:
            QMessageBox.warning(self.view, "Assign Failed", "Employee not found.")
            return
        tlevel = target.user_type.upper()

        # Role-based restrictions
        if actor == "EMPLOYEE":
            QMessageBox.warning(self.view, "Permission Denied", "Employees cannot assign permits.")
            return

        if actor == "SUPERVISOR":
            if tlevel != "EMPLOYEE":
                QMessageBox.warning(self.view, "Permission Denied", "You can only assign to employees.")
                return
            if target.supervisor_id != self.current_user.user_id:
                QMessageBox.warning(
                    self.view,
                    "Permission Denied",
                    "You can only assign permits to employees under your supervision."
                )
                return

        if actor == "ADMIN" and tlevel == "ADMIN":
            QMessageBox.warning(self.view, "Assign Failed", "Cannot assign permits to other admins.")
            return

        # Issue and expire logic
        issue = datetime.datetime.now()
        val   = self.view.duration_spin.value()
        unit  = self.view.unit_combo.currentText()

        if unit == "Permanent":
            expire = None
        elif unit == "Hours":
            expire = issue + relativedelta(hours=val)
        elif unit == "Days":
            expire = issue + relativedelta(days=val)
        else:
            expire = issue + relativedelta(months=val)

        # Supervisor must hold the license and cannot assign beyond their expiry
        if actor != "ADMIN":
            held_permits = SafetyDAO.fetch_by_user(self.current_user.user_id)
            matching = next((p for p in held_permits if p.permit_id == pid), None)

            if not matching:
                QMessageBox.warning(
                    self.view,
                    "Permission Denied",
                    "You must hold this permit yourself before assigning it."
                )
                return

            if matching.expire_date is not None:
                if expire is None or expire > matching.expire_date:
                    QMessageBox.warning(
                        self.view,
                        "Assign Failed",
                        "You cannot assign this permit beyond your own expiration date."
                    )
                    return

        if expire is not None and (expire - issue).days > 366:
            QMessageBox.warning(
                self.view,
                "Assign Failed",
                "Permit duration cannot exceed 366 days."
            )
            return

        SafetyDAO.add_permit(
            employee_id=uid,
            safety_permission_id=pid,
            issuer_employee_id=self.current_user.user_id,
            issue_date=issue,
            expire_date=expire
        )
        QMessageBox.information(self.view, "Success", "Permit assigned.")

    def on_scan_item(self):
        code = self.view.scan_item_input.text().strip()
        self.view.scan_item_input.clear()
        from data.access_dao import InventoryDAO
        itm = InventoryDAO.fetch_by_id(code)
        if not itm:
            QMessageBox.warning(self.view, "Scan Failed", f"Item '{code}' not found.")
            return
        self.scanned_item = itm
        self.view.item_label.setText(f"Item: {itm.item_id} – {itm.description}")
        self.load_item_requirements(itm.item_id)

    def load_item_requirements(self, item_id: str):
        from data.access_dao import ItemSafetyRequirementDAO
        req_ids = ItemSafetyRequirementDAO.fetch_by_item(item_id)
        types = {t.permission_id: t.name for t in SafetyDAO.fetch_all_types()}
        self.view.req_list.setRowCount(len(req_ids))
        for r, pid in enumerate(req_ids):
            name = types.get(pid, str(pid))
            cell = QTableWidgetItem(name)
            cell.setData(Qt.ItemDataRole.UserRole, pid)
            self.view.req_list.setItem(r, 0, cell)

    def on_add_item_req(self):
        if not hasattr(self, "scanned_item"):
            QMessageBox.warning(self.view, "Error", "Please scan an item first.")
            return
        pid = self.view.req_type_combo.currentData()

        if not self._can_modify_requirement(pid):
            QMessageBox.warning(self.view, "Permission Denied", "You must hold a valid permit of this type to modify requirements.")
            return

        from data.access_dao import ItemSafetyRequirementDAO
        ItemSafetyRequirementDAO.add_requirement(self.scanned_item.item_id, pid)
        self.load_item_requirements(self.scanned_item.item_id)

    def on_delete_item_req(self):
        if not hasattr(self, "scanned_item"):
            QMessageBox.warning(self.view, "Error", "Please scan an item first.")
            return
        row = self.view.req_list.currentRow()
        if row < 0:
            return
        pid = self.view.req_list.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if not self._can_modify_requirement(pid):
            QMessageBox.warning(self.view, "Permission Denied", "You must hold a valid permit of this type to modify requirements.")
            return

        from data.access_dao import ItemSafetyRequirementDAO
        ItemSafetyRequirementDAO.delete_requirement(self.scanned_item.item_id, pid)
        self.load_item_requirements(self.scanned_item.item_id)
