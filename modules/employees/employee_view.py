# # modules/employees/employee_view.py

import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSizePolicy,
                             QSpacerItem, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QWidget)

from data.access_dao import EmployeeDAO, User, UserDAO
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
    def __init__(self, parent=None, employee: User | None = None, current_user: User | None = None):
        super().__init__(parent)
        self.setWindowTitle("Employee Details")
        self.setMinimumWidth(500)
        self.scanner_buffer = ""
        self.employee_to_edit = employee  # Store for potential user switching
        self.current_user = current_user

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
        
        # Conditionally add user types based on whether admin is editing themselves
        user_types = ["EMPLOYEE", "SUPERVISOR"]
        if (current_user and current_user.user_type == "ADMIN" and 
            employee and employee.user_id == current_user.user_id):
            # Admin editing themselves - allow ADMIN option
            user_types.append("ADMIN")
        
        self._type.addItems(user_types)

        self._sup = QComboBox()
        self._sup.setFont(font)
        self._sup.setMinimumHeight(35)

        # RFID field and controls
        self._rfid = QLineEdit()
        self._rfid.setFont(font)
        self._rfid.setMinimumHeight(35)
        self._rfid.setPlaceholderText("Scan RFID card or enter manually...")
        
        # RFID buttons layout (below the text field)
        rfid_buttons_layout = QHBoxLayout()
        
        self._scan_rfid_btn = QPushButton("Scan RFID")
        self._scan_rfid_btn.setFont(font)
        self._scan_rfid_btn.setMinimumWidth(120)
        self._scan_rfid_btn.setMinimumHeight(35)
        self._scan_rfid_btn.clicked.connect(self._scan_rfid)
        rfid_buttons_layout.addWidget(self._scan_rfid_btn)
        
        self._clear_rfid_btn = QPushButton("Clear")
        self._clear_rfid_btn.setFont(font)
        self._clear_rfid_btn.setMinimumWidth(100)
        self._clear_rfid_btn.setMinimumHeight(35)
        self._clear_rfid_btn.clicked.connect(self._clear_rfid)
        rfid_buttons_layout.addWidget(self._clear_rfid_btn)
        
        rfid_buttons_layout.addStretch()  # Push buttons to the left

        # Load supervisor options (only SUPERVISORs you manage, or yourself)
        sup_list: list = []
        user = parent._current_user

        if user.user_type == "ADMIN":
            # Admin may choose any SUPERVISOR or themselves
            sup_list = [user] + [
                u for u in EmployeeDAO.fetch_all()
                if u.user_type == "SUPERVISOR" and u.user_id != user.user_id
            ]
        else:
            # Supervisor may choose themselves or SUPERVISORs under them
            sup_list = [user] + [
                u for u in EmployeeDAO.fetch_by_supervisor(user.user_id)
                if u.user_type == "SUPERVISOR"
            ]

        # Populate the combo
        for s in sup_list:
            self._sup.addItem(f"{s.first_name} {s.last_name}", s.user_id)

        # Fill if editing
        if employee:
            self._last.setText(employee.last_name)
            self._first.setText(employee.first_name)
            self._type.setCurrentText(employee.user_type)
            self._rfid.setText(employee.rfid_uid or "")
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
        form.addRow("RFID UID:", self._rfid)
        form.addRow("", rfid_buttons_layout)  # Buttons below RFID field
        
        # Instructions label
        instructions = QLabel(
            "<i>Tip: Focus on the RFID field and scan a card to auto-populate. "
            "Scanning will also allow switching to that user's profile.</i>"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 10px;")

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
        layout.addWidget(instructions)
        layout.addWidget(btns)

    def keyPressEvent(self, event):
        """Handle RFID scanning and user switching."""
        text = event.text()
        
        # Handle Enter key when scanner buffer has content
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.scanner_buffer.strip():
            code = self.scanner_buffer.strip()
            self.scanner_buffer = ""
            
            # Try barcode pattern first
            barcode_match = re.fullmatch(r"Alptraum(\d+)Technologies", code)
            if barcode_match:
                # Barcode scanned - look up user by ID
                uid = int(barcode_match.group(1))
                user = EmployeeDAO.fetch_by_id(uid)
                if user:
                    self._handle_user_found(user, f"barcode scan (ID: {uid})")
                else:
                    QMessageBox.warning(self, "User Not Found", f"No employee found with ID {uid}")
            elif code:
                # RFID scanned - look up user by RFID UID
                user = UserDAO.get_by_rfid_uid(code)
                if user:
                    self._handle_user_found(user, f"RFID scan ({code})")
                else:
                    # No existing user - just populate the RFID field
                    self._rfid.setText(code)
                    QMessageBox.information(
                        self, "RFID Assigned", 
                        f"RFID UID '{code}' has been assigned to this employee."
                    )
            return
        
        # Append text to scanner buffer
        if text:
            self.scanner_buffer += text
        
        super().keyPressEvent(event)

    def _handle_user_found(self, user: User, scan_type: str):
        """Handle when a user is found via barcode or RFID scan."""
        msg = f"User found via {scan_type}:\n{user.first_name} {user.last_name}\n\nWhat would you like to do?"
        
        reply = QMessageBox.question(
            self, "User Found",
            msg + "\n\n• Yes: Switch to this user's profile\n• No: Assign this RFID to current employee",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Switch to the found user's profile
            self._switch_to_found_user(user)
        elif reply == QMessageBox.StandardButton.No:
            # Assign the RFID to current employee
            if hasattr(user, 'rfid_uid') and user.rfid_uid:
                self._rfid.setText(user.rfid_uid)
                QMessageBox.information(
                    self, "RFID Assigned", 
                    f"RFID UID '{user.rfid_uid}' has been assigned to this employee."
                )

    def _switch_to_found_user(self, user: User):
        """Switch to editing the found user's profile."""
        # Update all fields with the found user's data
        self._last.setText(user.last_name)
        self._first.setText(user.first_name)
        self._type.setCurrentText(user.user_type)
        self._rfid.setText(user.rfid_uid or "")
        
        # Update supervisor
        idx = self._sup.findData(user.supervisor_id)
        if idx != -1:
            self._sup.setCurrentIndex(idx)
        
        # Update the stored employee reference
        self.employee_to_edit = user
        
        # Show the switch button and update window title
        self._switch_btn.setVisible(True)
        self.setWindowTitle(f"Employee Details - {user.first_name} {user.last_name}")
        
        QMessageBox.information(
            self, "User Switched", 
            f"Now editing profile for {user.first_name} {user.last_name}"
        )

    def _scan_rfid(self):
        """Start RFID scanning to capture a tag using the global scanner."""
        try:
            from PyQt6.QtCore import QObject, pyqtSignal
            
            # Get the main window instance to access the global RFID scanner
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'rfid_scanner'):
                    main_window = parent
                    break
                parent = parent.parent()
            
            if not main_window or not main_window.rfid_scanner:
                QMessageBox.warning(self, "RFID Scanner", 
                                  "RFID scanner is not connected. Please connect the scanner from the main window first.")
                return
            
            # Create a signal handler for thread-safe communication
            class RFIDSignalHandler(QObject):
                rfid_detected = pyqtSignal(str)
                
                def __init__(self):
                    super().__init__()
                    self.original_callback = None
                    
                def handle_scan(self, rfid_uid):
                    # This will be called from the scanner thread
                    self.rfid_detected.emit(rfid_uid)
            
            # Create signal handler
            signal_handler = RFIDSignalHandler()
            
            # Create a simple dialog to show scanning status
            scan_dialog = QDialog(self)
            scan_dialog.setWindowTitle("RFID Scanning")
            scan_dialog.setModal(True)
            scan_dialog.resize(300, 150)
            
            layout = QVBoxLayout()
            status_label = QLabel("Scanning for RFID tag...\nPresent your RFID tag to the scanner.")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(status_label)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(scan_dialog.reject)
            layout.addWidget(cancel_btn)
            
            scan_dialog.setLayout(layout)
            
            # Connect signal to UI update (this runs in main thread)
            def on_rfid_detected_safe(rfid_uid):
                self._rfid.setText(rfid_uid)
                scan_dialog.accept()
                
            signal_handler.rfid_detected.connect(on_rfid_detected_safe)
            
            # Temporarily replace the main window's RFID callback
            scanner = main_window.rfid_scanner
            signal_handler.original_callback = scanner.on_scan_callback
            scanner.on_scan_callback = signal_handler.handle_scan
            
            try:
                # Show dialog and wait for result
                result = scan_dialog.exec()
                
                if result == QDialog.DialogCode.Accepted:
                    QMessageBox.information(self, "RFID Scanned", 
                                          f"RFID tag captured: {self._rfid.text()}")
            finally:
                # Restore the original callback
                scanner.on_scan_callback = signal_handler.original_callback
            
        except Exception as e:
            QMessageBox.critical(self, "RFID Scanning Error", 
                               f"Failed to scan RFID: {str(e)}")

    def _clear_rfid(self):
        """Clear the RFID field."""
        self._rfid.clear()

    def _switch_to_user(self):
        """Switch the main application to this user (if editing existing employee)."""
        if self.employee_to_edit and hasattr(self.parent(), '_current_user'):
            # This would require access to the main window - we'll emit a signal or use a callback
            QMessageBox.information(
                self, "Switch User", 
                f"To switch to {self.employee_to_edit.first_name} {self.employee_to_edit.last_name}, "
                "scan their barcode or RFID on the home page."
            )

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
    def rfid_uid(self) -> str | None:
        text = self._rfid.text().strip()
        return text if text else None

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
        self._tree.setColumnCount(6)
        self._tree.setHeaderLabels([
            "ID", "Last Name", "First Name", "User Type", "Supervisor", "RFID UID"
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
        item = self._tree.currentItem()
        has = item is not None
        # You can always print any selected node
        self.printBtn.setEnabled(has)
        # But if the selected node is the root (current user), disable delete but allow edit for ADMINs
        if has and int(item.text(0)) == self._current_user.user_id:
            # Allow admins to edit themselves (for RFID assignment), but prevent deletion
            self._btn_edit.setEnabled(self._current_user.user_type == "ADMIN")
            self._btn_del.setEnabled(False)   # Still prevent self-deletion
        else:
            self._btn_edit.setEnabled(True)
            self._btn_del.setEnabled(True)

    def _add(self):
        dlg = _EmployeeDialog(self, current_user=self._current_user)
        if dlg.exec():
            EmployeeDAO.insert(dlg.last, dlg.first, dlg.user_type, dlg.supervisor, dlg.rfid_uid)
            self.controller.load_employees()

    def _edit(self):
        item = self._tree.currentItem()
        if not item:
            return
        uid = int(item.text(0))
        emp = EmployeeDAO.fetch_by_id(uid)
        if not emp:
            return

        # Capture original state
        orig_type = emp.user_type
        orig_sup  = emp.supervisor_id

        dlg = _EmployeeDialog(self, emp, current_user=self._current_user)
        if dlg.exec():
            # Determine which employee to update (might have switched during dialog)
            target_emp = dlg.employee_to_edit or emp
            
            # Apply changes
            target_emp.last_name     = dlg.last
            target_emp.first_name    = dlg.first
            target_emp.user_type     = dlg.user_type
            target_emp.supervisor_id = dlg.supervisor
            target_emp.rfid_uid      = dlg.rfid_uid
            EmployeeDAO.update(target_emp)

            # If we just DEMOTED them from SUPERVISOR → EMPLOYEE,
            # reassign their direct reports to their former supervisor
            if orig_type == "SUPERVISOR" and target_emp.user_type != "SUPERVISOR":
                for sub in EmployeeDAO.fetch_by_supervisor(target_emp.user_id):
                    sub.supervisor_id = orig_sup
                    EmployeeDAO.update(sub)

            # Refresh the tree
            self.controller.load_employees()

    def _delete(self):
        item = self._tree.currentItem()
        if not item:
            return
        uid = int(item.text(0))
        emp = EmployeeDAO.fetch_by_id(uid)
        if not emp:
            return

        # Confirm deletion
        answer = QMessageBox.question(
            self,
            "Delete",
            f"Delete employee {uid}?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        # Reassign any direct reports to this employee's supervisor
        sup_sup = emp.supervisor_id
        for sub in EmployeeDAO.fetch_by_supervisor(uid):
            sub.supervisor_id = sup_sup
            EmployeeDAO.update(sub)

        # Now delete
        EmployeeDAO.delete(uid)
        self.controller.load_employees()

    def populate_tree(self, report_tree: dict[int, list[User]], root_sup_id: int | None):
        """
        Show the current user as the single root node in the tree,
        then recurse to add all direct and indirect reports below.
        """
        # 1) Clear any existing items
        self._tree.clear()
        visited = set()

        # 2) Create a root item for the current user - fetch fresh data from DB
        me = EmployeeDAO.fetch_by_id(self._current_user.user_id) or self._current_user
        sup_name = ""
        if me.supervisor_id:
            mgr = EmployeeDAO.fetch_by_id(me.supervisor_id)
            if mgr:
                sup_name = f"{mgr.first_name} {mgr.last_name}"

        root_item = QTreeWidgetItem(self._tree, [
            str(me.user_id),
            me.last_name,
            me.first_name,
            me.user_type,
            sup_name,
            me.rfid_uid or ""
        ])
        # --- DO NOT disable the item itself, so it can be selected for printing ---
        # root_item.setDisabled(True)

        # 3) Recursive helper to add subordinates under any supervisor
        def add_subs(parent: QTreeWidgetItem, sup_id: int):
            if sup_id in visited:
                return
            visited.add(sup_id)

            for emp in report_tree.get(sup_id, []):
                # Skip adding the current user as a subordinate if they are already the root
                if emp.user_id == me.user_id:
                    continue
                # lookup this employee’s supervisor name
                name_sup = ""
                if emp.supervisor_id:
                    m = EmployeeDAO.fetch_by_id(emp.supervisor_id)
                    if m:
                        name_sup = f"{m.first_name} {m.last_name}"

                node = QTreeWidgetItem(parent, [
                    str(emp.user_id),
                    emp.last_name,
                    emp.first_name,
                    emp.user_type,
                    name_sup,
                    emp.rfid_uid or ""
                ])
                add_subs(node, emp.user_id)

        # 4) Populate the rest of the tree under our root
        add_subs(root_item, me.user_id)

        # 5) Expand everything
        self._tree.expandAll()