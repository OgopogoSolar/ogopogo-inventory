# modules/safety/safety_view.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QStackedWidget, QComboBox, QSpinBox, QSplitter, QGroupBox,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class SafetyView(QWidget):
    def __init__(self, controller, current_user):
        super().__init__()
        self.controller   = controller
        self.current_user = current_user
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Safety Management")
        self.setMinimumSize(1000, 600)
        font = QFont("Segoe UI", 12)

        # ─── Left Pane: Permit Type Management ─────────────────
        left_group = QGroupBox("Permit Types")
        lg_layout = QVBoxLayout(left_group)
        lg_layout.setContentsMargins(10,10,10,10)
        lg_layout.setSpacing(10)

        self.type_table = QTableWidget(0,1)
        self.type_table.setHorizontalHeaderLabels(["Type Name"])
        self.type_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lg_layout.addWidget(self.type_table)

        btn_layout = QHBoxLayout()
        self.add_type_btn    = QPushButton("Add Type")
        self.edit_type_btn   = QPushButton("Edit Type")
        self.delete_type_btn = QPushButton("Delete Type")
        for b in (self.add_type_btn, self.edit_type_btn, self.delete_type_btn):
            b.setFont(font)
            btn_layout.addWidget(b)
        lg_layout.addLayout(btn_layout)

        # ─── Right Pane: Scanner + Details ────────────────────
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10,10,10,10)
        right_layout.setSpacing(15)

        # Scanner input
        scan_h = QHBoxLayout()
        scan_lbl = QLabel("Scan Code:")
        scan_lbl.setFont(font)
        self.scan_input = QLineEdit()
        self.scan_input.setFont(font)
        self.scan_input.setPlaceholderText("Scan Employee or Item Code…")
        scan_h.addWidget(scan_lbl)
        scan_h.addWidget(self.scan_input)
        right_layout.addLayout(scan_h)

        # Info label (for employee or item)
        self.info_label = QLabel("No record scanned")
        self.info_label.setFont(font)
        right_layout.addWidget(self.info_label)

        # Stacked widget for Employee vs Item
        self.stack = QStackedWidget()

        # --- Employee Panel ---
        emp_page = QWidget()
        emp_v = QVBoxLayout(emp_page)

        # 1. Table of employee permits
        self.emp_table = QTableWidget(0, 4)
        self.emp_table.setHorizontalHeaderLabels(
            ["Permit Type", "Issued On", "Expires On", "Issued By"]
        )
        self.emp_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        emp_v.addWidget(self.emp_table)

        # 2. Buttons for Add / Edit / Delete
        emp_btn_h = QHBoxLayout()
        self.emp_add_btn    = QPushButton("Add Permit")
        self.emp_edit_btn   = QPushButton("Edit Permit")
        self.emp_delete_btn = QPushButton("Delete Permit")
        for btn in (self.emp_add_btn, self.emp_edit_btn, self.emp_delete_btn):
            btn.setFont(font)
            emp_btn_h.addWidget(btn)
        emp_v.addLayout(emp_btn_h)

        self.stack.addWidget(emp_page)

        # --- Item Panel ---
        item_page = QWidget()
        itm_v = QVBoxLayout(item_page)
        # Key/value table for item details
        self.item_info_table = QTableWidget(0,2)
        self.item_info_table.setHorizontalHeaderLabels(["Field","Value"])
        self.item_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        itm_v.addWidget(self.item_info_table)
        # Table of item requirements
        self.item_req_table = QTableWidget(0,1)
        self.item_req_table.setHorizontalHeaderLabels(["Permit Type"])
        self.item_req_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        itm_v.addWidget(self.item_req_table)
        # Buttons
        item_btn_h = QHBoxLayout()
        self.req_add_btn    = QPushButton("Add Requirement")
        self.req_delete_btn = QPushButton("Remove Requirement")
        for b in (self.req_add_btn, self.req_delete_btn):
            b.setFont(font)
            item_btn_h.addWidget(b)
        itm_v.addLayout(item_btn_h)

        self.stack.addWidget(item_page)

        right_layout.addWidget(self.stack)

        # ─── Combine Left & Right ─────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_group.setMinimumWidth(250)
        splitter.addWidget(left_group)
        right_container = QWidget()
        right_container.setLayout(right_layout)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(1, 3)

        # Final root layout
        root = QVBoxLayout(self)
        root.addWidget(splitter)

    def reset_form(self):
        """Clear scan/input, tables, and return to left‐scan state."""
        self.scan_input.clear()
        self.info_label.setText("No record scanned")

        self.type_table.clearSelection()
        self.emp_table.setRowCount(0)
        self.item_info_table.setRowCount(0)
        self.item_req_table.setRowCount(0)

        self.stack.setCurrentIndex(0)

class PermitDurationDialog(QDialog):
    """
    Dialog to pick an hours/days/months/permanent duration.
    """
    def __init__(self, parent=None, current_days: int = 1, current_unit: str = "Days"):
        super().__init__(parent)
        self.setWindowTitle("Edit Permit Duration")
        self.setMinimumWidth(300)

        font = QFont("Segoe UI", 12)
        layout = QFormLayout(self)

        self.spin = QSpinBox()
        self.spin.setRange(1, 3650)
        self.spin.setFont(font)
        self.spin.setValue(current_days)

        self.unit = QComboBox()
        self.unit.setFont(font)
        self.unit.addItems(["Hours", "Days", "Months", "Permanent"])
        idx = self.unit.findText(current_unit)
        if idx >= 0:
            self.unit.setCurrentIndex(idx)

        layout.addRow("Duration:", self.spin)
        layout.addRow("Unit:", self.unit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Disable spin when “Permanent” is selected
        self.unit.currentTextChanged.connect(self._on_unit_changed)
        self._on_unit_changed(self.unit.currentText())

    def _on_unit_changed(self, txt: str):
        self.spin.setEnabled(txt != "Permanent")

    @property
    def value(self) -> int:
        return self.spin.value()

    @property
    def unitText(self) -> str:
        return self.unit.currentText()