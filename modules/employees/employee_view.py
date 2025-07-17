# # modules/employees/employee_view.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
    QMessageBox, QLineEdit, QLabel, QComboBox,
    QCheckBox, QDialog, QFormLayout, QDialogButtonBox,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from data.access_dao import EmployeeDAO, User
from modules.employees.employee_controller import EmployeeController


def styled_lineedit(text="") -> QLineEdit:
    le = QLineEdit(text)
    le.setFont(QFont("Segoe UI", 12))
    le.setMinimumHeight(35)
    return le


def styled_combobox() -> QComboBox:
    cb = QComboBox()
    cb.setFont(QFont("Segoe UI", 12))
    cb.setMinimumHeight(35)
    return cb


def styled_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setFont(QFont("Segoe UI", 12))
    btn.setMinimumHeight(40)
    btn.setMinimumWidth(120)
    return btn


class _EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee: User | None = None):
        super().__init__(parent)
        self.setWindowTitle("Employee Details")
        self.setMinimumWidth(500)

        font = QFont("Segoe UI", 12)

        # --- Fields ---
        self._last = QLineEdit()
        self._last.setFont(font)
        self._last.setMinimumHeight(35)

        self._first = QLineEdit()
        self._first.setFont(font)
        self._first.setMinimumHeight(35)

        self._type = QComboBox()
        self._type.setFont(font)
        self._type.setMinimumHeight(35)
        self._type.addItems(["EMPLOYEE", "SUPERVISOR"])

        self._sup = QComboBox()
        self._sup.setFont(font)
        self._sup.setMinimumHeight(35)

        # self._active = QCheckBox("Active")
        # self._active.setFont(font)

        # Load supervisor options (only SUPERVISORs you manage, or yourself)
        sup_list: list = []
        user = parent._current_user

        if user.user_type == "ADMIN":
            # Admin can assign any SUPERVISOR
            sup_list = [u for u in EmployeeDAO.fetch_all() if u.user_type == "SUPERVISOR"]
        else:
            # Supervisor can only assign themselves or SUPERVISORs under them
            sup_list = [user] + [
                u for u in EmployeeDAO.fetch_by_supervisor(user.user_id)
                if u.user_type == "SUPERVISOR"
            ]

        for s in sup_list:
            self._sup.addItem(f"{s.first_name} {s.last_name}", s.user_id)

        # Fill if editing
        if employee:
            self._last.setText(employee.last_name)
            self._first.setText(employee.first_name)
            self._type.setCurrentText(employee.user_type)
            idx = self._sup.findData(getattr(employee, "supervisor_id", None))
            if idx != -1:
                self._sup.setCurrentIndex(idx)
            # self._active.setChecked(getattr(employee, "is_active", False))

        # --- Layout ---
        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow("Last Name:", self._last)
        form.addRow("First Name:", self._first)
        form.addRow("User Type:", self._type)
        form.addRow("Supervisor:", self._sup)
        # form.addRow("", self._active)

        # --- Buttons with correct connections ---
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel
        )
        apply_btn = btns.button(QDialogButtonBox.StandardButton.Apply)
        cancel_btn = btns.button(QDialogButtonBox.StandardButton.Cancel)

        apply_btn.setText("Apply")
        cancel_btn.setText("Cancel")

        # Explicitly connect clicks → accept/reject
        apply_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        # --- Final assembly ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addWidget(btns)

    @property
    def last(self) -> str:
        return self._last.text().strip()

    @property
    def first(self) -> str:
        return self._first.text().strip()

    @property
    def user_type(self) -> str:
        return self._type.currentText()

    # @property
    # def is_active(self) -> bool:
    #     return self._active.isChecked()

    @property
    def supervisor(self) -> int | None:
        return self._sup.currentData()


class EmployeeView(QWidget):
    def __init__(self, current_user: User):
        super().__init__()
        self._current_user = current_user
        self.setWindowTitle("Employee Management")
        self.setMinimumSize(950, 600)

        self.controller = EmployeeController(self, current_user)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.searchEdit = styled_lineedit()
        self.searchEdit.setPlaceholderText("ID, last or first name…")
        search_layout.addWidget(self.searchEdit)

        # Button row
        btn_bar = QHBoxLayout()
        self._btn_add = styled_button("Add")
        self._btn_edit = styled_button("Edit")
        self._btn_del = styled_button("Delete")
        self.printBtn = styled_button("Print Label")
        self.printBtn.setEnabled(False)

        for btn in [self._btn_add, self._btn_edit, self._btn_del, self.printBtn]:
            btn_bar.addWidget(btn)
        btn_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Permission-based visibility: only pure EMPLOYEEs cannot modify
        if current_user.user_type == "EMPLOYEE":
            for btn in (self._btn_add, self._btn_edit, self._btn_del):
                btn.setVisible(False)
        # Tree
        self._tree = QTreeWidget()
        self._tree.setColumnCount(5)
        self._tree.setHeaderLabels([
            "ID", "Last Name", "First Name", "User Type", "Supervisor"
        ])
        # Stretch all columns
        for col in range(6):
            self._tree.header().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self._tree.setFont(QFont("Segoe UI", 11))

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.addLayout(search_layout)
        main_layout.addLayout(btn_bar)
        main_layout.addWidget(self._tree)

        # Signals
        self.searchEdit.textChanged.connect(self.controller.on_search_text_changed)
        self._btn_add.clicked.connect(self._add)
        self._btn_edit.clicked.connect(self._edit)
        self._btn_del.clicked.connect(self._delete)
        self.printBtn.clicked.connect(self.controller.on_print_label)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)

        self.controller.load_employees()

    def _on_selection_changed(self, current=None, previous=None):
        self.printBtn.setEnabled(self._tree.currentItem() is not None)

    def _add(self):
        dlg = _EmployeeDialog(self)
        if dlg.exec():
            EmployeeDAO.insert(dlg.last, dlg.first, dlg.user_type, dlg.supervisor)
            self.controller.load_employees()

    def _edit(self):
        item = self._tree.currentItem()
        if not item:
            return
        uid = int(item.text(0))
        emp = EmployeeDAO.fetch_by_id(uid)
        dlg = _EmployeeDialog(self, emp)
        if dlg.exec():
            emp.last_name = dlg.last
            emp.first_name = dlg.first
            emp.user_type = dlg.user_type
            emp.supervisor_id = dlg.supervisor
            # emp.is_active = dlg.is_active
            EmployeeDAO.update(emp)
            self.controller.load_employees()

    def _delete(self):
        item = self._tree.currentItem()
        if not item:
            return
        uid = int(item.text(0))
        if QMessageBox.question(self, "Delete", f"Delete employee {uid}?") == QMessageBox.StandardButton.Yes:
            EmployeeDAO.delete(uid)
            self.controller.load_employees()

    def populate_tree(self, report_tree: dict[int, list[User]], root_sup_id: int | None):
        """
        report_tree: mapping supervisor_id -> list of Users.
        root_sup_id: int user_id to start from, or None for top-level.
        """
        # Clear any existing items
        self._tree.clear()
        visited = set()

        def add_subs(parent, sup_id):
            if sup_id in visited:
                return
            visited.add(sup_id)

            for emp in report_tree.get(sup_id, []):
                # lookup supervisor name
                sup_name = ""
                if emp.supervisor_id:
                    manager = EmployeeDAO.fetch_by_id(emp.supervisor_id)
                    if manager:
                        sup_name = f"{manager.first_name} {manager.last_name}"

                # add this employee under parent with 5 columns
                node = QTreeWidgetItem(parent, [
                    str(emp.user_id),
                    emp.last_name,
                    emp.first_name,
                    emp.user_type,
                    sup_name
                ])
                add_subs(node, emp.user_id)

        # seed at the logged-in user’s ID
        add_subs(self._tree, root_sup_id)
        self._tree.expandAll()