# from PyQt6.QtWidgets import (
#     QWidget, QHBoxLayout, QVBoxLayout,
#     QTableWidget, QTableWidgetItem,
#     QPushButton, QLineEdit, QComboBox,
#     QLabel, QSpinBox, QMessageBox
# )
# from PyQt6.QtCore import Qt

# class SafetyView(QWidget):
#     def __init__(self, controller, current_user):
#         super().__init__()
#         self.controller   = controller
#         self.current_user = current_user
#         self._init_ui()

#     def _init_ui(self):
#         self.setWindowTitle("Safety Management")
#         layout = QHBoxLayout(self)

#         # — Left: Permit-Type List & Buttons ——————————
#         left = QVBoxLayout()
#         left.addWidget(QLabel("Permit Types:"))
#         self.type_table = QTableWidget(0, 1)
#         self.type_table.setHorizontalHeaderLabels(["Type Name"])
#         self.type_table.horizontalHeader().setStretchLastSection(True)
#         left.addWidget(self.type_table)

#         btns = QHBoxLayout()
#         self.add_type_btn    = QPushButton("Add Type")
#         self.edit_type_btn   = QPushButton("Edit Type")
#         self.delete_type_btn = QPushButton("Delete Type")
#         btns.addWidget(self.add_type_btn)
#         btns.addWidget(self.edit_type_btn)
#         btns.addWidget(self.delete_type_btn)
#         left.addLayout(btns)

#         layout.addLayout(left, 2)

#         # — Right panel: employee assignment above, item requirements below —
#         right = QVBoxLayout()

#         # Employee Scan & Permit Assignment
#         self.scan_input = QLineEdit()
#         self.scan_input.setPlaceholderText("Scan Employee Code…")
#         self.scan_input.setEchoMode(QLineEdit.EchoMode.Password)
#         right.addWidget(self.scan_input)

#         self.employee_label = QLabel("Employee: [None scanned]", self)
#         right.addWidget(self.employee_label)

#         right.addWidget(QLabel("Assign Permit:"))
#         self.assign_type_combo = QComboBox()
#         right.addWidget(self.assign_type_combo)

#         dur = QHBoxLayout()
#         self.duration_spin = QSpinBox()
#         self.duration_spin.setRange(1, 8760)
#         self.unit_combo = QComboBox()
#         self.unit_combo.addItems(["Hours", "Days", "Months"])
#         dur.addWidget(self.duration_spin)
#         dur.addWidget(self.unit_combo)
#         right.addLayout(dur)

#         self.assign_btn = QPushButton("Assign Permit")
#         right.addWidget(self.assign_btn)
#         right.addStretch()

#         # Item Safety Requirement Configuration
#         self.bottom_label   = QLabel("Item Safety Requirements:")
#         right.addWidget(self.bottom_label)

#         self.scan_item_input = QLineEdit()
#         self.scan_item_input.setPlaceholderText("Scan Item Code…")
#         self.scan_item_input.setEchoMode(QLineEdit.EchoMode.Password)
#         right.addWidget(self.scan_item_input)

#         self.item_label     = QLabel("Item: [None scanned]")
#         right.addWidget(self.item_label)

#         self.req_type_combo = QComboBox()
#         right.addWidget(self.req_type_combo)

#         h_req = QHBoxLayout()
#         self.add_req_btn    = QPushButton("Add Requirement")
#         self.delete_req_btn = QPushButton("Remove Requirement")
#         h_req.addWidget(self.add_req_btn)
#         h_req.addWidget(self.delete_req_btn)
#         right.addLayout(h_req)

#         self.req_list = QTableWidget(0, 1)
#         self.req_list.setHorizontalHeaderLabels(["Permit Type"])
#         self.req_list.horizontalHeader().setStretchLastSection(True)
#         right.addWidget(self.req_list)

#         # Connect signals
#         self.scan_input.returnPressed.connect(self.controller.on_scan)
#         self.assign_btn.clicked.connect(self.controller.on_assign)
#         self.scan_item_input.returnPressed.connect(self.controller.on_scan_item)
#         self.add_req_btn.clicked.connect(self.controller.on_add_item_req)
#         self.delete_req_btn.clicked.connect(self.controller.on_delete_item_req)

#         layout.addLayout(right, 2)

#         # — Signal Wiring —  
#         self.add_type_btn.clicked.connect   (self.controller.on_add_type)
#         self.edit_type_btn.clicked.connect  (self.controller.on_edit_type)
#         self.delete_type_btn.clicked.connect(self.controller.on_delete_type)

#     def reset_form(self):
#         """Clear any pending scans or form state."""
#         self.scan_input.clear()
#         self.scan_item_input.clear()
#         self.employee_label.setText("Employee: [None scanned]")
#         self.item_label.setText("Item: [None scanned]")
#         self.req_list.setRowCount(0)
#         self.assign_type_combo.setCurrentIndex(0)
#         self.req_type_combo.setCurrentIndex(0)

#     def show_types(self, types: list[tuple[int,str]]):
#         """types = list of (type_id, name)"""
#         self.type_table.setRowCount(len(types))
#         for r, (tid, name) in enumerate(types):
#             item = QTableWidgetItem(name)
#             item.setData(Qt.ItemDataRole.UserRole, tid)
#             self.type_table.setItem(r, 0, item)

#     def show_employees(self, users):
#         """users = list of User objects"""
#         self.employee_combo.clear()
#         for u in users:
#             label = f"{u.user_id}: {u.first_name} {u.last_name}"
#             self.employee_combo.addItem(label, u.user_id)

#     def show_assign_types(self, types: list[tuple[int,str]]):
#         """Populate the right-hand permit picker."""
#         self.assign_type_combo.clear()
#         for tid, name in types:
#             self.assign_type_combo.addItem(name, tid)

#     def clear_scan(self):
#         """Clear and refocus the hidden scan box."""
#         self.scan_input.clear()
#         self.scan_input.setFocus()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QSplitter, QLabel, QLineEdit, QComboBox,
    QSpinBox, QTableWidget, QTableWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Utility functions for consistent styling
def styled_lineedit(placeholder: str = "") -> QLineEdit:
    le = QLineEdit()
    le.setFont(QFont("Segoe UI", 12))
    le.setMinimumHeight(35)
    le.setPlaceholderText(placeholder)
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

class SafetyView(QWidget):
    def __init__(self, controller, current_user):
        super().__init__()
        self.controller   = controller
        self.current_user = current_user
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Safety Management")
        self.setMinimumSize(1000, 600)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # ── Left: Permit Types ─────────────────────
        left_group = QGroupBox("Permit Types")
        left_group.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        self.type_table = QTableWidget(0, 1)
        self.type_table.setHorizontalHeaderLabels(["Type Name"])
        self.type_table.horizontalHeader().setStretchLastSection(True)
        self.type_table.setFont(QFont("Segoe UI", 11))
        self.type_table.verticalHeader().setFont(QFont("Segoe UI", 9))
        left_layout.addWidget(self.type_table)

        btns = QHBoxLayout()
        self.add_type_btn    = styled_button("Add Type")
        self.edit_type_btn   = styled_button("Edit Type")
        self.delete_type_btn = styled_button("Delete Type")
        btns.addWidget(self.add_type_btn)
        btns.addWidget(self.edit_type_btn)
        btns.addWidget(self.delete_type_btn)
        btns.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        left_layout.addLayout(btns)

        left_group.setLayout(left_layout)
        splitter.addWidget(left_group)

        # ── Right: Assignment & Requirements ────────
        right_group = QGroupBox("Assignments & Requirements")
        right_group.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(20)

        # Employee Scan & Permit Assignment
        assign_group = QGroupBox("Employee Permit Assignment")
        assign_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        ag_layout = QFormLayout()
        ag_layout.setSpacing(15)
        ag_layout.setContentsMargins(10, 10, 10, 10)

        self.scan_input = styled_lineedit("Scan Employee Code…")
        self.scan_input.setEchoMode(QLineEdit.EchoMode.Password)
        ag_layout.addRow("Scan:", self.scan_input)

        self.employee_label = QLabel("Employee: [None scanned]")
        self.employee_label.setFont(QFont("Segoe UI", 12))
        ag_layout.addRow("", self.employee_label)

        self.assign_type_combo = styled_combobox()
        ag_layout.addRow("Permit Type:", self.assign_type_combo)

        dur_layout = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 8760)
        self.duration_spin.setFont(QFont("Segoe UI", 12))
        self.duration_spin.setMinimumHeight(35)
        self.unit_combo = styled_combobox()
        self.unit_combo.addItems(["Hours", "Days", "Months", "Permanent"])
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        dur_layout.addWidget(self.duration_spin)
        dur_layout.addWidget(self.unit_combo)
        ag_layout.addRow("Duration:", dur_layout)

        self.assign_btn = styled_button("Assign Permit")
        ag_layout.addRow("", self.assign_btn)

        assign_group.setLayout(ag_layout)
        right_layout.addWidget(assign_group)

        # Item Safety Requirement Configuration
        req_group = QGroupBox("Item Safety Requirements")
        req_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        rg_layout = QFormLayout()
        rg_layout.setSpacing(15)
        rg_layout.setContentsMargins(10, 10, 10, 10)

        self.scan_item_input = styled_lineedit("Scan Item Code…")
        self.scan_item_input.setEchoMode(QLineEdit.EchoMode.Password)
        rg_layout.addRow("Scan:", self.scan_item_input)

        self.item_label = QLabel("Item: [None scanned]")
        self.item_label.setFont(QFont("Segoe UI", 12))
        rg_layout.addRow("", self.item_label)

        self.req_type_combo = styled_combobox()
        rg_layout.addRow("Permit Type:", self.req_type_combo)

        h_req = QHBoxLayout()
        self.add_req_btn    = styled_button("Add Requirement")
        self.delete_req_btn = styled_button("Remove Requirement")
        h_req.addWidget(self.add_req_btn)
        h_req.addWidget(self.delete_req_btn)
        h_req.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        rg_layout.addRow("", h_req)

        self.req_list = QTableWidget(0, 1)
        self.req_list.setHorizontalHeaderLabels(["Permit Type"])
        self.req_list.horizontalHeader().setStretchLastSection(True)
        self.req_list.setFont(QFont("Segoe UI", 11))
        self.req_list.verticalHeader().setFont(QFont("Segoe UI", 9))
        rg_layout.addRow("Requirements:", self.req_list)

        req_group.setLayout(rg_layout)
        right_layout.addWidget(req_group)
        right_layout.addStretch()

        right_group.setLayout(right_layout)
        splitter.addWidget(right_group)

        # Main layout with consistent margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.addWidget(splitter)

        # Signal wiring
        self.scan_input.returnPressed.connect(self.controller.on_scan)
        self.assign_btn.clicked.connect(self.controller.on_assign)
        self.scan_item_input.returnPressed.connect(self.controller.on_scan_item)
        self.add_req_btn.clicked.connect(self.controller.on_add_item_req)
        self.delete_req_btn.clicked.connect(self.controller.on_delete_item_req)
        self.add_type_btn.clicked.connect(self.controller.on_add_type)
        self.edit_type_btn.clicked.connect(self.controller.on_edit_type)
        self.delete_type_btn.clicked.connect(self.controller.on_delete_type)

    def reset_form(self):
        """Clear form state."""
        self.scan_input.clear()
        self.scan_item_input.clear()
        self.employee_label.setText("Employee: [None scanned]")
        self.item_label.setText("Item: [None scanned]")
        self.req_list.setRowCount(0)
        self.assign_type_combo.setCurrentIndex(0)
        self.req_type_combo.setCurrentIndex(0)

    def show_types(self, types: list[tuple[int, str]]):
        self.type_table.setRowCount(len(types))
        for r, (tid, name) in enumerate(types):
            item = QTableWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, tid)
            self.type_table.setItem(r, 0, item)

    def show_assign_types(self, types: list[tuple[int, str]]):
        self.assign_type_combo.clear()
        for tid, name in types:
            self.assign_type_combo.addItem(name, tid)

    def show_item_req_types(self, types: list[tuple[int, str]]):
        self.req_type_combo.clear()
        for tid, name in types:
            self.req_type_combo.addItem(name, tid)

    def clear_scan(self):
        self.scan_input.clear()
        self.scan_input.setFocus()

    def _on_unit_changed(self, text):
        if text == "Permanent":
            self.duration_spin.setEnabled(False)
            self.duration_spin.setSpecialValueText("∞")
            self.duration_spin.setValue(self.duration_spin.minimum())  # ensure text shows
        else:
            self.duration_spin.setEnabled(True)
            self.duration_spin.setSpecialValueText("")  # remove special text


