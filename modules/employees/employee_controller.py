# modules/employees/employee_controller.py

from pathlib import Path
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from utils.label_printer import print_label
from data.access_dao import EmployeeDAO, UserDAO

class EmployeeController:
    def __init__(self, view, current_user):
        self.view = view
        self.current_user = current_user
        self._all_emps = []

    def load_employees(self):
        """Load all employees and render to the table."""
        self._all_emps = EmployeeDAO.fetch_all()
        self._render_table(self._all_emps)

    def on_search_text_changed(self, text: str):
        """Filter employee list as the user types."""
        t = text.strip().lower()
        filtered = (
            self._all_emps if not t else 
            [e for e in self._all_emps
             if t in str(e.user_id).lower()
                or t in e.last_name.lower()
                or t in e.first_name.lower()]
        )
        self._render_table(filtered)

    def _render_table(self, emps):
        """Populate the view’s table with a list of User objects."""
        tbl = self.view._table
        tbl.setRowCount(len(emps))
        for r, e in enumerate(emps):
            # Basic columns
            vals = [
                e.user_id,
                e.last_name,
                e.first_name,
                e.user_type,
                "Yes" if getattr(e, "is_active", True) else "No",
            ]
            for c, v in enumerate(vals):
                tbl.setItem(r, c, QTableWidgetItem(str(v)))
            # Supervisor name (col 5)
            sup_id = getattr(e, "supervisor_id", None)
            if sup_id:
                sup = UserDAO.get_by_id(sup_id)
                sup_name = f"{sup.first_name} {sup.last_name}"
            else:
                sup_name = ""
            tbl.setItem(r, 5, QTableWidgetItem(sup_name))

    def on_print_label(self):
        """Print the selected employee’s label via the shared print_label()."""
        tbl = self.view._table
        row = tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Warning", "Please select an employee first.")
            return

        # 1) Build placeholder dict from header names → cell texts
        headers = [
            tbl.horizontalHeaderItem(c).text()
            for c in range(tbl.columnCount())
        ]
        placeholder_dict = {
            headers[i]: (tbl.item(row, i).text() or "")
            for i in range(len(headers))
        }

        # 2) Locate the template
        settings  = QSettings("AlptraumTech", "LMS")
        tpl_name  = settings.value("default_template_employee", "")
        if not tpl_name:
            QMessageBox.warning(
                self.view,
                "Print Failed",
                "Please configure an Employee label template first."
            )
            return

        tpl_path = (
            Path(__file__).resolve().parents[1]
            / "Templates"
            / tpl_name
        )
        if not tpl_path.exists():
            QMessageBox.critical(
                self.view,
                "Print Failed",
                f"Template file not found:\n{tpl_path}"
            )
            return

        # 3) Delegate to the shared printer function
        try:
            print_label(tpl_path, placeholder_dict)
            QMessageBox.information(self.view, "Success", "Label printed.")
        except Exception as e:
            QMessageBox.critical(self.view, "Print Failed", str(e))
