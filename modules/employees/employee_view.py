# modules/employees/employee_view.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QLineEdit, QLabel, QComboBox,
    QCheckBox, QDialog, QFormLayout, QDialogButtonBox
)
from data.access_dao import EmployeeDAO, User
from modules.employees.employee_controller import EmployeeController

class _EmployeeDialog(QDialog):
    """Dialog for adding or editing an employee."""
    def __init__(self, parent=None, employee: User | None = None):
        super().__init__(parent)
        self.setWindowTitle("Employee")
        self.setModal(True)

        # Fields
        self._last  = QLineEdit()
        self._first = QLineEdit()
        self._type  = QComboBox()
        self._type.addItems(["EMPLOYEE", "SUPERVISOR", "ADMIN"])
        self._active = QCheckBox("Active")
        # Supervisor selector
        self._sup    = QComboBox()
        # Populate with all supervisors
        from data.access_dao import EmployeeDAO
        all_users   = EmployeeDAO.fetch_all()
        supervisors = [u for u in all_users if u.user_type == "SUPERVISOR"]
        for s in supervisors:
            label = f"{s.first_name} {s.last_name}"
            self._sup.addItem(label, s.user_id)

        # Pre-fill when editing
        if employee:
            self._last.setText(employee.last_name)
            self._first.setText(employee.first_name)
            self._type.setCurrentText(employee.user_type)
            if hasattr(employee, "supervisor_id") and employee.supervisor_id:
                idx = self._sup.findData(employee.supervisor_id)
                if idx != -1:
                    self._sup.setCurrentIndex(idx)
            if hasattr(employee, "is_active"):
                self._active.setChecked(employee.is_active)

        # Layout
        form = QFormLayout(self)
        form.addRow("Last Name:", self._last)
        form.addRow("First Name:", self._first)
        form.addRow("User Type:", self._type)
        form.addRow("Supervisor:",  self._sup)
        form.addRow("", self._active)

        # Buttons: Apply / Cancel
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        apply_btn = btns.button(QDialogButtonBox.StandardButton.Apply)
        cancel_btn = btns.button(QDialogButtonBox.StandardButton.Cancel)
        apply_btn.setText("Apply")
        cancel_btn.setText("Cancel")
        # 直接连接 clicked 信号，保证 Apply 按钮能触发 accept()
        apply_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        form.addRow(btns)

        self.resize(300, 180)

    def reset_form(self):
        """Clear search & reset table selection."""
        self.searchEdit.clear()
        self._btn_add.setEnabled(self._current_user.user_type=="EMPLOYEE")
        self._btn_edit.setEnabled(self._current_user.user_type=="EMPLOYEE")
        self._btn_del.setEnabled(self._current_user.user_type=="EMPLOYEE")
        self._table.clearSelection()
        self.printBtn.setEnabled(False)
        # reload employees
        self.controller.load_employees()

    @property
    def last(self) -> str:
        return self._last.text().strip()

    @property
    def first(self) -> str:
        return self._first.text().strip()

    @property
    def user_type(self) -> str:
        return self._type.currentText()

    @property
    def is_active(self) -> bool:
        return self._active.isChecked()
    
    @property
    def supervisor(self) -> int | None:
        """Return selected supervisor's user_id."""
        return self._sup.currentData()


class EmployeeView(QWidget):
    """员工管理：支持搜索、增删改 和 打印标签"""
    def __init__(self, current_user: User):
        super().__init__()
        self._current_user = current_user
        self.setWindowTitle("Employee Management")

        # 控制器
        self.controller = EmployeeController(self, current_user)

        # —— 搜索栏 —— 
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("ID, last or first name…")
        search_layout.addWidget(self.searchEdit)

        # —— 按钮区 —— 
        btn_bar = QHBoxLayout()
        self._btn_add  = QPushButton("Add")
        self._btn_edit = QPushButton("Edit")
        self._btn_del  = QPushButton("Delete")
        self.printBtn  = QPushButton("Print Label")
        self.printBtn.setEnabled(False)  # 默认锁死

        for btn in (self._btn_add, self._btn_edit, self._btn_del, self.printBtn):
            btn_bar.addWidget(btn)
        btn_bar.addStretch()

        # 仅 ADMIN 可用增删改
        if self._current_user.user_type != "ADMIN":
            for btn in (self._btn_add, self._btn_edit, self._btn_del):
                btn.setDisabled(True)

        # —— 表格 —— 
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Last Name", "First Name", "User Type", "Status", "Supervisor"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # —— 主布局 —— 
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(search_layout)
        main_layout.addLayout(btn_bar)
        main_layout.addWidget(self._table)

        # —— 信号连接 —— 
        self.searchEdit.textChanged.connect(self.controller.on_search_text_changed)
        self._btn_add.clicked.connect(self._add)
        self._btn_edit.clicked.connect(self._edit)
        self._btn_del.clicked.connect(self._delete)
        self.printBtn.clicked.connect(self.controller.on_print_label)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        # —— 初始加载员工 —— 
        self.controller.load_employees()

    def _on_selection_changed(self):
        """表格行选中变化时，启用/禁用打印按钮"""
        has = self._table.currentRow() >= 0
        self.printBtn.setEnabled(has)

    def _add(self):
        dlg = _EmployeeDialog(self)
        if dlg.exec():
            EmployeeDAO.insert(dlg.last, dlg.first, dlg.user_type, dlg.supervisor)  # :contentReference[oaicite:0]{index=0}
            self.controller.load_employees()

    def _edit(self):
        row = self._table.currentRow()
        if row < 0:
            return
        uid = int(self._table.item(row, 0).text())
        emp = EmployeeDAO.fetch_by_id(uid)
        dlg = _EmployeeDialog(self, emp)
        if dlg.exec():
            emp.last_name  = dlg.last
            emp.first_name = dlg.first
            emp.user_type  = dlg.user_type
            emp.supervisor_id = dlg.supervisor
            if hasattr(emp, "is_active"):
                emp.is_active = dlg.is_active
            EmployeeDAO.update(emp)
            self.controller.load_employees()

    def _delete(self):
        row = self._table.currentRow()
        if row < 0:
            return
        uid = int(self._table.item(row, 0).text())
        if QMessageBox.question(
            self, "Delete", f"Delete employee {uid}?"
        ) == QMessageBox.StandardButton.Yes:
            EmployeeDAO.delete(uid)
            self.controller.load_employees()
