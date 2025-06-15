from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox,
    QLabel, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt

class SafetyView(QWidget):
    def __init__(self, controller, current_user):
        super().__init__()
        self.controller   = controller
        self.current_user = current_user
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Safety Management")
        layout = QHBoxLayout(self)

        # — Left: Permit-Type List & Buttons ——————————
        left = QVBoxLayout()
        left.addWidget(QLabel("Permit Types:"))
        self.type_table = QTableWidget(0, 1)
        self.type_table.setHorizontalHeaderLabels(["Type Name"])
        self.type_table.horizontalHeader().setStretchLastSection(True)
        left.addWidget(self.type_table)

        btns = QHBoxLayout()
        self.add_type_btn    = QPushButton("Add Type")
        self.edit_type_btn   = QPushButton("Edit Type")
        self.delete_type_btn = QPushButton("Delete Type")
        btns.addWidget(self.add_type_btn)
        btns.addWidget(self.edit_type_btn)
        btns.addWidget(self.delete_type_btn)
        left.addLayout(btns)

        layout.addLayout(left, 2)

        # — Right panel: employee assignment above, item requirements below —
        right = QVBoxLayout()

        # Employee Scan & Permit Assignment
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Scan Employee Code…")
        self.scan_input.setEchoMode(QLineEdit.EchoMode.Password)
        right.addWidget(self.scan_input)

        self.employee_label = QLabel("Employee: [None scanned]", self)
        right.addWidget(self.employee_label)

        right.addWidget(QLabel("Assign Permit:"))
        self.assign_type_combo = QComboBox()
        right.addWidget(self.assign_type_combo)

        dur = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 8760)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Hours", "Days", "Months"])
        dur.addWidget(self.duration_spin)
        dur.addWidget(self.unit_combo)
        right.addLayout(dur)

        self.assign_btn = QPushButton("Assign Permit")
        right.addWidget(self.assign_btn)
        right.addStretch()

        # Item Safety Requirement Configuration
        self.bottom_label   = QLabel("Item Safety Requirements:")
        right.addWidget(self.bottom_label)

        self.scan_item_input = QLineEdit()
        self.scan_item_input.setPlaceholderText("Scan Item Code…")
        self.scan_item_input.setEchoMode(QLineEdit.EchoMode.Password)
        right.addWidget(self.scan_item_input)

        self.item_label     = QLabel("Item: [None scanned]")
        right.addWidget(self.item_label)

        self.req_type_combo = QComboBox()
        right.addWidget(self.req_type_combo)

        h_req = QHBoxLayout()
        self.add_req_btn    = QPushButton("Add Requirement")
        self.delete_req_btn = QPushButton("Remove Requirement")
        h_req.addWidget(self.add_req_btn)
        h_req.addWidget(self.delete_req_btn)
        right.addLayout(h_req)

        self.req_list = QTableWidget(0, 1)
        self.req_list.setHorizontalHeaderLabels(["Permit Type"])
        self.req_list.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self.req_list)

        # Connect signals
        self.scan_input.returnPressed.connect(self.controller.on_scan)
        self.assign_btn.clicked.connect(self.controller.on_assign)
        self.scan_item_input.returnPressed.connect(self.controller.on_scan_item)
        self.add_req_btn.clicked.connect(self.controller.on_add_item_req)
        self.delete_req_btn.clicked.connect(self.controller.on_delete_item_req)

        layout.addLayout(right, 2)

        # — Signal Wiring —  
        self.add_type_btn.clicked.connect   (self.controller.on_add_type)
        self.edit_type_btn.clicked.connect  (self.controller.on_edit_type)
        self.delete_type_btn.clicked.connect(self.controller.on_delete_type)

    def reset_form(self):
        """Clear any pending scans or form state."""
        self.scan_input.clear()
        self.scan_item_input.clear()
        self.employee_label.setText("Employee: [None scanned]")
        self.item_label.setText("Item: [None scanned]")
        self.req_list.setRowCount(0)
        self.assign_type_combo.setCurrentIndex(0)
        self.req_type_combo.setCurrentIndex(0)

    def show_types(self, types: list[tuple[int,str]]):
        """types = list of (type_id, name)"""
        self.type_table.setRowCount(len(types))
        for r, (tid, name) in enumerate(types):
            item = QTableWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, tid)
            self.type_table.setItem(r, 0, item)

    def show_employees(self, users):
        """users = list of User objects"""
        self.employee_combo.clear()
        for u in users:
            label = f"{u.user_id}: {u.first_name} {u.last_name}"
            self.employee_combo.addItem(label, u.user_id)

    def show_assign_types(self, types: list[tuple[int,str]]):
        """Populate the right-hand permit picker."""
        self.assign_type_combo.clear()
        for tid, name in types:
            self.assign_type_combo.addItem(name, tid)

    def clear_scan(self):
        """Clear and refocus the hidden scan box."""
        self.scan_input.clear()
        self.scan_input.setFocus()
