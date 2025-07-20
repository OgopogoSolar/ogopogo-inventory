# # modules/inventory/inventory_view.py

# from PyQt6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
#     QTableWidget, QTableWidgetItem, QHeaderView,
#     QLineEdit, QLabel, QMessageBox, QFileDialog,
#     QDialog, QFormLayout, QComboBox, QSpinBox,
#     QDialogButtonBox
# )
# from data.access_dao import (
#     InventoryDAO, Item, EmployeeDAO,
#     CategoryDAO, SubCategoryDAO, ParameterDAO
# )
# from modules.inventory.inventory_controller import InventoryController


# class ItemDialog(QDialog):
#     """Dialog for adding or editing an inventory item with dynamic category/subcategory/parameters."""
#     def __init__(self, parent=None, item: Item | None = None):
#         super().__init__(parent)
#         self.setWindowTitle("Item")
#         self.setModal(True)

#         # --- Category & SubCategory Combos ---
#         self._cat_combo = QComboBox()
#         self._subcat_combo = QComboBox()
#         # load all categories: 显示 description，userData 存 code
#         self._categories = CategoryDAO.fetch_all()
#         for c in self._categories:
#             self._cat_combo.addItem(c.description, c.code)
#         # when category changes, reload subcategories
#         self._cat_combo.currentIndexChanged.connect(self._reload_subcategories)
#         self._reload_subcategories()

#         # when subcategory changes, reload parameters
#         self._subcat_combo.currentIndexChanged.connect(self._reload_parameters)

#         # --- Other static fields ---
#         self._desc     = QLineEdit()
#         self._qty      = QSpinBox()
#         self._qty.setRange(0, 1_000_000)
#         self._status   = QComboBox()
#         self._status.addItems(["In Stock", "In Use", "Damaged"])
#         self._location = QLineEdit()
#         self._manual   = QLineEdit()
#         self._sop      = QLineEdit()
#         self._image    = QLineEdit()
#         self._price    = QLineEdit()
#         self._price.setPlaceholderText("e.g. 12.34")

#         # --- Parameter fields area ---
#         # We'll create a FormLayout to hold them
#         self._param_layout = QFormLayout()
#         # position -> QLineEdit map
#         self._param_widgets: dict[int, QLineEdit] = {}
#         self._reload_parameters()

#         # --- Build form ---
#         form = QFormLayout(self)
#         form.addRow("Category:", self._cat_combo)
#         form.addRow("SubCategory:", self._subcat_combo)
#         form.addRow("Description:", self._desc)
#         form.addRow("Quantity:", self._qty)
#         form.addRow("Status:", self._status)
#         form.addRow("Location:", self._location)

#         # Manual path with browse
#         h1 = QHBoxLayout()
#         h1.addWidget(self._manual)
#         btn_m = QPushButton("Browse")
#         h1.addWidget(btn_m)
#         form.addRow("Manual Path:", h1)
#         btn_m.clicked.connect(lambda: self._browse_file(self._manual))

#         # SOP path with browse
#         h2 = QHBoxLayout()
#         h2.addWidget(self._sop)
#         btn_s = QPushButton("Browse")
#         h2.addWidget(btn_s)
#         form.addRow("SOP Path:", h2)
#         btn_s.clicked.connect(lambda: self._browse_file(self._sop))

#         # Image path with browse
#         h3 = QHBoxLayout()
#         h3.addWidget(self._image)
#         btn_i = QPushButton("Browse")
#         h3.addWidget(btn_i)
#         form.addRow("Image Path:", h3)
#         btn_i.clicked.connect(lambda: self._browse_file(self._image))

#         form.addRow("Price:", self._price)

#         # Parameter area
#         form.addRow(QLabel("Parameters:"), QLabel(""))  # spacer
#         form.addRow(self._param_layout)

#         # Buttons: Apply / Cancel
#         btns = QDialogButtonBox(
#             QDialogButtonBox.StandardButton.Apply |
#             QDialogButtonBox.StandardButton.Cancel,
#             parent=self
#         )
#         apply_btn  = btns.button(QDialogButtonBox.StandardButton.Apply)
#         cancel_btn = btns.button(QDialogButtonBox.StandardButton.Cancel)
#         apply_btn.setText("Apply")
#         cancel_btn.setText("Cancel")
#         apply_btn.clicked.connect(self.accept)
#         cancel_btn.clicked.connect(self.reject)
#         form.addRow(btns)

#         self.resize(450, 400)

#         if item:
#             parts = item.item_id.split("-")
#             if len(parts) >= 2:
#                 category_code, subcategory_code = parts[0], parts[1]

#                 # Select category by its code (stored in userData)
#                 cat_index = self._cat_combo.findData(category_code)
#                 if cat_index != -1:
#                     self._cat_combo.setCurrentIndex(cat_index)

#                 # Reload subcategories for this category
#                 self._reload_subcategories()

#                 # Select subcategory by its code
#                 sub_index = self._subcat_combo.findData(subcategory_code)
#                 if sub_index != -1:
#                     self._subcat_combo.setCurrentIndex(sub_index)

#                 # Reload parameter fields for the selected subcategory
#                 self._reload_parameters()

#                 # Fill parameter values
#                 parameter_values = parts[2:]
#                 for position, line_edit in self._param_widgets.items():
#                     if 1 <= position <= len(parameter_values):
#                         line_edit.setText(parameter_values[position - 1])

#             # Fill remaining static fields
#             self._desc.setText(item.description)
#             self._qty.setValue(item.quantity)
#             self._status.setCurrentText(item.status)
#             self._location.setText(item.location)
#             self._manual.setText(item.manual_path)
#             self._sop.setText(item.sop_path)
#             self._image.setText(item.image_path)
#             self._price.setText("" if item.price is None else str(item.price))

#     def _reload_subcategories(self):
#         """Reload subcategory combo when category changes."""
#         # 从 combo 的 userData 读回 code
#         cat_code = self._cat_combo.currentData()
#         subs = SubCategoryDAO.fetch_by_category(cat_code)
#         self._subcat_combo.clear()
#         # 显示 description，userData 存 code
#         for s in subs:
#             self._subcat_combo.addItem(s.description, s.code)

#     def _reload_parameters(self):
#         """Reload parameter input fields when subcategory changes."""
#         # Clear old rows
#         while self._param_layout.rowCount() > 0:
#             self._param_layout.removeRow(0)
#         self._param_widgets.clear()

#         # Use currentData() to get the subcategory code
#         subcategory_code = self._subcat_combo.currentData()
#         parameters = ParameterDAO.fetch_by_subcategory(subcategory_code)

#         for param in parameters:
#             le = QLineEdit()
#             self._param_layout.addRow(f"{param.name}:", le)
#             self._param_widgets[param.position] = le

#     def _browse_file(self, line_edit: QLineEdit):
#         path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
#         if path:
#             line_edit.setText(path)

#     @property
#     def item_id(self) -> str:
#         # combine category-subcategory-params → e.g. "EC-Resistor-0805-100k"
#         parts = [self._cat_combo.currentData(), self._subcat_combo.currentData()]
#         for pos in sorted(self._param_widgets):
#             parts.append(self._param_widgets[pos].text().strip())
#         return "-".join(parts)

#     @property
#     def category_code(self) -> str:
#         return self._cat_combo.currentData()

#     @property
#     def subcategory_code(self) -> str:
#         return self._subcat_combo.currentData()

#     @property
#     def desc(self) -> str:
#         return self._desc.text().strip()

#     @property
#     def qty(self) -> int:
#         return self._qty.value()

#     @property
#     def status(self) -> str:
#         return self._status.currentText()

#     @property
#     def location(self) -> str:
#         return self._location.text().strip()

#     @property
#     def manual(self) -> str:
#         return self._manual.text().strip()

#     @property
#     def sop(self) -> str:
#         return self._sop.text().strip()

#     @property
#     def image(self) -> str:
#         return self._image.text().strip()

#     @property
#     def price(self) -> float | None:
#         txt = self._price.text().strip()
#         try:
#             return float(txt) if txt else None
#         except ValueError:
#             return None


# class InventoryView(QWidget):
#     """仓库管理：搜索 + 增删改 + 出入库 + 导出清单"""
#     def __init__(self, current_user):
#         super().__init__()
#         self._current_user = current_user
#         self.setWindowTitle("Inventory Management")
        
#         # 搜索栏
#         search_layout = QHBoxLayout()
#         search_layout.addWidget(QLabel("Search:"))
#         self.searchEdit = QLineEdit()
#         self.searchEdit.setPlaceholderText("ItemID or Description…")
#         search_layout.addWidget(self.searchEdit)

#         # 按钮区
#         btn_bar = QHBoxLayout()
#         self.btn_add      = QPushButton("Add")
#         self.btn_edit     = QPushButton("Edit")
#         self.btn_delete   = QPushButton("Delete")
#         self.btn_check    = QPushButton("Check-In/Out")
#         self.btn_export   = QPushButton("Export List")
#         self.labelTypeCombo = QComboBox()
#         self.labelTypeCombo.addItems(["Item", "Product", "Documentation"])
#         self.printBtn     = QPushButton("Print Label")
#         self.printBtn.setEnabled(False)  # 默认无选中时禁用
#         for w in (
#             self.btn_add, self.btn_edit, self.btn_delete,
#             self.btn_check, self.btn_export,
#             self.labelTypeCombo, self.printBtn
#         ):
#             btn_bar.addWidget(w)

#         # 表格
#         self.table = QTableWidget(0, 9)
#         self.table.setHorizontalHeaderLabels([
#             "ID",        # 不显示，但要存在以供打印调用
#             "Category",
#             "Subcategory",
#             "Location",
#             "Quantity",
#             "Status",
#             "Holder",
#             "Parameters",
#             "Safety Requirements"
#         ])
#         # 隐藏 ID 列
#         self.table.hideColumn(0)

#         self.table.horizontalHeader().setSectionResizeMode(
#             # make Parameters column stretch & wrap
#             QHeaderView.ResizeMode.Stretch
#         )

#         self.table.setEditTriggers(
#             QTableWidget.EditTrigger.NoEditTriggers
#         )
        
#         # 主布局
#         layout = QVBoxLayout(self)
#         layout.addLayout(search_layout)
#         layout.addLayout(btn_bar)
#         layout.addWidget(self.table)

#         # 信号连接
#         from modules.inventory.inventory_controller import InventoryController
#         self.controller = InventoryController(self)
#         self.searchEdit.textChanged.connect(self.controller.on_search)
#         self.btn_add.clicked.connect(self.controller.on_add)
#         self.btn_edit.clicked.connect(self.controller.on_edit)
#         self.btn_delete.clicked.connect(self.controller.on_delete)
#         self.btn_check.clicked.connect(self.controller.open_check_dialog)
#         self.btn_export.clicked.connect(self.controller.on_export)
#         self.printBtn.clicked.connect(self.controller.on_print_item_label)
#         self.table.itemSelectionChanged.connect(self._on_selection_changed)

#         # 初始加载
#         self.controller.load_items()

#     def reset_form(self):
#         """Clear search & reset all combos/buttons to default."""
#         self.searchEdit.clear()
#         self.labelTypeCombo.setCurrentIndex(0)
#         self.printBtn.setEnabled(False)
#         # reload full list
#         self.controller.load_items()

#     def _current_item_id(self) -> str | None:
#         r = self.table.currentRow()
#         if r < 0:
#             return None
#         return self.table.item(r, 0).text()

#     def refresh(self, items: list[Item]):
#         """由 Controller 调用以刷新表格显示"""
#         self.table.setRowCount(len(items))
#         for r, itm in enumerate(items):
#             # 从 item_id 中拆出 parameters 部分
#             params = itm.item_id.split('-')[2:]
#             params_text = " ".join(params).strip()

#             # ID is hidden; display holder’s FirstName LastName if set
#             holder_text = ""
#             if itm.holder_id:
#                 usr = EmployeeDAO.fetch_by_id(itm.holder_id)
#                 holder_text = f"{usr.first_name} {usr.last_name}" if usr else ""
#             from data.access_dao import ItemSafetyRequirementDAO, SafetyDAO
#             req_ids   = ItemSafetyRequirementDAO.fetch_by_item(itm.item_id)
#             type_map  = {t.permission_id:t.name for t in SafetyDAO.fetch_all_types()}
#             req_names = [type_map.get(pid, str(pid)) for pid in req_ids]
#             req_text  = "\n".join(req_names)
#             row_vals = [
#                 itm.item_id,
#                 itm.category_code,
#                 itm.subcategory_code,
#                 itm.location,
#                 itm.quantity,
#                 itm.status,
#                 holder_text,
#                 params_text,
#                 req_text
#             ]
#             for c, v in enumerate(row_vals):
#                 self.table.setItem(r, c, QTableWidgetItem(str(v)))
#         if items:
#             self.table.selectRow(0)

#     def open_check_dialog(self):
#         from modules.inventory.inventory_controller import CheckDialog
#         dlg = CheckDialog(self)
#         dlg.id_input.returnPressed.connect(lambda: self.controller.process_check(dlg))
#         dlg.exec()
        
#     def _on_selection_changed(self):
#         """表格行选中变化时，启用/禁用打印按钮"""
#         has = self.table.currentRow() >= 0
#         self.printBtn.setEnabled(has)

# class CheckDialog(QDialog):
#     """Modal dialog to scan/type an Item ID and perform check-in/out."""
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Inventory Check-In/Out")
#         self.id_input = QLineEdit()
#         # Hide raw code
#         self.id_input.setEchoMode(QLineEdit.EchoMode.Password)
#         self.id_input.setPlaceholderText("Scan or enter Item ID and press Enter")

#         form = QFormLayout(self)
#         form.addRow("Item ID:", self.id_input)

#         # Info fields
#         self.info_fields: dict[str, QLabel] = {}
#         for label in (
#             "Category", "Subcategory", "Location",
#             "Quantity", "Status", "Holder", "Parameters",
#             "Description", "Price"
#         ):
#             fld = QLabel()
#             fld.setWordWrap(True)
#             form.addRow(f"{label}:", fld)
#             self.info_fields[label.lower()] = fld

#         # Manual & SOP controls
#         from PyQt6.QtWidgets import QPushButton
#         self.manual_btn = QPushButton("Open Manual", self)
#         self.sop_btn    = QPushButton("Open SOP", self)
#         form.addRow("Manual:", self.manual_btn)
#         form.addRow("SOP:", self.sop_btn)

#         # Image preview
#         self.image_label = QLabel(self)
#         self.image_label.setFixedSize(256, 256)
#         self.image_label.setScaledContents(True)
#         form.addRow("Image:", self.image_label)

#         # Safety Requirements display
#         self.req_label = QLabel(self)
#         form.addRow("Safety Requirements:", self.req_label)

#         # Embedded status message (green/red)
#         self.status_label = QLabel()
#         self.status_label.setStyleSheet("color: green;")
#         form.addRow("", self.status_label)

#     def clear_info(self):
#         """Clear all info fields and status message before new lookup."""
#         for fld in self.info_fields.values():
#             fld.clear()
#         self.manual_btn.hide()
#         self.sop_btn.hide()
#         self.image_label.clear()
#         self.status_label.clear()
#         self.req_label.clear()

# modules/inventory/inventory_view.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QLabel, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QComboBox, QSpinBox,
    QDialogButtonBox, QSizePolicy, QSpacerItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from data.access_dao import (
    InventoryDAO, Item, EmployeeDAO,
    CategoryDAO, SubCategoryDAO, ParameterDAO
)
from modules.inventory.inventory_controller import InventoryController


# ─────────────────────────────────────────────
# Styled Components
# ─────────────────────────────────────────────
def styled_lineedit(text: str = "") -> QLineEdit:
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


# ─────────────────────────────────────────────
# Item Dialog
# ─────────────────────────────────────────────
class ItemDialog(QDialog):
    """Dialog for adding or editing an inventory item with dynamic fields."""
    def __init__(self, parent=None, item: Item | None = None):
        super().__init__(parent)
        self.setWindowTitle("Item Details")
        self.setMinimumWidth(500)

        # Main layout with margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(0, 0, 0, 0)

        # Category & SubCategory
        self._cat_combo = styled_combobox()
        self._subcat_combo = styled_combobox()
        for c in CategoryDAO.fetch_all():
            self._cat_combo.addItem(c.description, c.code)
        self._cat_combo.currentIndexChanged.connect(self._reload_subcategories)
        form.addRow("Category:", self._cat_combo)

        self._reload_subcategories()
        self._subcat_combo.currentIndexChanged.connect(self._reload_parameters)
        form.addRow("SubCategory:", self._subcat_combo)

        # Static fields
        self._desc     = styled_lineedit()
        form.addRow("Description:", self._desc)

        self._qty      = QSpinBox()
        self._qty.setFont(QFont("Segoe UI", 12))
        self._qty.setMinimumHeight(35)
        self._qty.setRange(0, 1_000_000)
        form.addRow("Quantity:", self._qty)

        self._status   = styled_combobox()
        self._status.addItems(["In Stock", "In Use", "Damaged"])
        form.addRow("Status:", self._status)

        self._location = styled_lineedit()
        form.addRow("Location:", self._location)

        # File paths with browse
        for attr, label in (("_manual", "Manual Path:"), ("_sop", "SOP Path:"), ("_image", "Image Path:")):
            le = styled_lineedit()
            setattr(self, attr, le)
            btn = styled_button("Browse")
            btn.setMinimumWidth(80)
            btn.clicked.connect(lambda _, le=le: self._browse_file(le))
            hl = QHBoxLayout()
            hl.setSpacing(10)
            hl.addWidget(le)
            hl.addWidget(btn)
            form.addRow(label, hl)

        # Price
        self._price = styled_lineedit()
        self._price.setPlaceholderText("e.g. 12.34")
        form.addRow("Price:", self._price)

        # Dynamic parameters
        form.addRow(QLabel("Parameters:"), QLabel(""))
        self._param_layout = QFormLayout()
        self._param_layout.setSpacing(15)
        self._param_widgets: dict[int, QLineEdit] = {}
        self._reload_parameters()
        form.addRow(self._param_layout)

        # Dialog buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        main_layout.addLayout(form)
        main_layout.addWidget(btns)

        # Populate if editing
        if item:
            parts = item.item_id.split("-")
            cat_code, sub_code = parts[0], parts[1]
            idx = self._cat_combo.findData(cat_code)
            if idx != -1:
                self._cat_combo.setCurrentIndex(idx)
            self._reload_subcategories()
            idx = self._subcat_combo.findData(sub_code)
            if idx != -1:
                self._subcat_combo.setCurrentIndex(idx)
            self._reload_parameters()
            for i, le in self._param_widgets.items():
                if i+2 < len(parts):
                    le.setText(parts[i+2])
            self._desc.setText(item.description)
            self._qty.setValue(item.quantity)
            self._status.setCurrentText(item.status)
            self._location.setText(item.location)
            self._manual.setText(item.manual_path)
            self._sop.setText(item.sop_path)
            self._image.setText(item.image_path)
            self._price.setText("" if item.price is None else str(item.price))

    def _reload_subcategories(self):
        self._subcat_combo.clear()
        code = self._cat_combo.currentData()
        for s in SubCategoryDAO.fetch_by_category(code):
            self._subcat_combo.addItem(s.description, s.code)

    def _reload_parameters(self):
        while self._param_layout.rowCount():
            self._param_layout.removeRow(0)
        self._param_widgets.clear()
        code = self._subcat_combo.currentData()
        for p in ParameterDAO.fetch_by_subcategory(code):
            le = styled_lineedit()
            self._param_layout.addRow(f"{p.name}:", le)
            self._param_widgets[p.position] = le

    def _browse_file(self, line_edit: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if path:
            line_edit.setText(path)

    @property
    def item_id(self) -> str:
        parts = [self._cat_combo.currentData(), self._subcat_combo.currentData()]
        for pos in sorted(self._param_widgets):
            parts.append(self._param_widgets[pos].text().strip())
        return "-".join(parts)

    @property
    def category_code(self) -> str:
        return self._cat_combo.currentData()

    @property
    def subcategory_code(self) -> str:
        return self._subcat_combo.currentData()

    @property
    def desc(self) -> str:
        return self._desc.text().strip()

    @property
    def qty(self) -> int:
        return self._qty.value()

    @property
    def status(self) -> str:
        return self._status.currentText()

    @property
    def location(self) -> str:
        return self._location.text().strip()

    @property
    def manual(self) -> str:
        return self._manual.text().strip()

    @property
    def sop(self) -> str:
        return self._sop.text().strip()

    @property
    def image(self) -> str:
        return self._image.text().strip()

    @property
    def price(self) -> float | None:
        t = self._price.text().strip()
        try:
            return float(t) if t else None
        except ValueError:
            return None


# ─────────────────────────────────────────────
# Main Inventory View
# ─────────────────────────────────────────────
class InventoryView(QWidget):
    """仓库管理：搜索 + 增删改 + 出入库 + 导出清单"""
    def __init__(self, current_user):
        super().__init__()
        self._current_user = current_user
        self.setWindowTitle("Inventory Management")
        self.setMinimumSize(1000, 600)

        # Controller will be created after UI elements exist

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.searchEdit = styled_lineedit()
        self.searchEdit.setPlaceholderText("ItemID or Description…")
        search_layout.addWidget(self.searchEdit)
        main_layout.addLayout(search_layout)

        # Button bar
        btn_bar = QHBoxLayout()
        self.btn_add    = styled_button("Add")
        self.btn_edit   = styled_button("Edit")
        self.btn_delete = styled_button("Delete")
        self.btn_check  = styled_button("Check-In/Out")
        self.btn_export = styled_button("Export List")
        self.labelTypeCombo = styled_combobox()
        self.labelTypeCombo.addItems(["Item", "Product", "Documentation"])
        self.printBtn   = styled_button("Print Label")
        self.printBtn.setEnabled(False)
        for w in (
            self.btn_add, self.btn_edit, self.btn_delete,
            self.btn_check, self.btn_export,
            self.labelTypeCombo, self.printBtn
        ):
            btn_bar.addWidget(w)
        btn_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(btn_bar)

        # Table (must exist before controller)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Category", "Subcategory",
            "Location", "Quantity", "Status",
            "Holder", "Parameters", "Safety Requirements"
        ])
        self.table.hideColumn(0)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setFont(QFont("Segoe UI", 11))
        self.table.verticalHeader().setFont(QFont("Segoe UI", 9))
        main_layout.addWidget(self.table)

        # Now safe to create controller
        self.controller = InventoryController(self)

        # Signals
        self.searchEdit.textChanged.connect(self.controller.on_search)
        self.btn_add.clicked.connect(self.controller.on_add)
        self.btn_edit.clicked.connect(self.controller.on_edit)
        self.btn_delete.clicked.connect(self.controller.on_delete)
        self.btn_check.clicked.connect(self.controller.open_check_dialog)
        self.btn_export.clicked.connect(self.controller.on_export)
        self.printBtn.clicked.connect(self.controller.on_print_item_label)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Initial load
        self.controller.load_items()

    def reset_form(self):
        self.searchEdit.clear()
        self.labelTypeCombo.setCurrentIndex(0)
        self.printBtn.setEnabled(False)
        self.controller.load_items()

    def refresh(self, items: list[Item]):
        self.table.setRowCount(len(items))
        for r, itm in enumerate(items):
            parts = itm.item_id.split('-')[2:]
            holder = ""
            if itm.holder_id:
                u = EmployeeDAO.fetch_by_id(itm.holder_id)
                holder = f"{u.first_name} {u.last_name}" if u else ""
            from data.access_dao import ItemSafetyRequirementDAO, SafetyDAO
            reqs = ItemSafetyRequirementDAO.fetch_by_item(itm.item_id)
            type_map = {t.permission_id: t.name for t in SafetyDAO.fetch_all_types()}
            req_text = "\n".join(type_map.get(pid, str(pid)) for pid in reqs)

            vals = [
                itm.item_id, itm.category_code, itm.subcategory_code,
                itm.location, itm.quantity, itm.status,
                holder, " ".join(parts).strip(), req_text
            ]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        if items:
            self.table.selectRow(0)

    def open_check_dialog(self):
        from modules.inventory.inventory_controller import CheckDialog
        dlg = CheckDialog(self)
        dlg.id_input.returnPressed.connect(lambda: self.controller.process_check(dlg))
        dlg.exec()

    def _on_selection_changed(self):
        self.printBtn.setEnabled(self.table.currentRow() >= 0)


# ─────────────────────────────────────────────
# Check-In/Out Dialog
# ─────────────────────────────────────────────
class CheckDialog(QDialog):
    """Modal dialog to scan/type an Item ID and perform check-in/out."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Check-In/Out")
        self.setMinimumWidth(500)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(0, 0, 0, 0)

        self.id_input = styled_lineedit()
        self.id_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.id_input.setPlaceholderText("Scan or enter Item ID and press Enter")
        form.addRow("Item ID:", self.id_input)

        self.info_fields: dict[str, QLabel] = {}
        for label in (
            "Category", "Subcategory", "Location",
            "Quantity", "Status", "Holder", "Parameters",
            "Description", "Price"
        ):
            fld = QLabel()
            fld.setWordWrap(True)
            fld.setFont(QFont("Segoe UI", 12))
            form.addRow(f"{label}:", fld)
            self.info_fields[label.lower()] = fld

        self.manual_btn = styled_button("Open Manual")
        self.sop_btn    = styled_button("Open SOP")
        form.addRow("Manual:", self.manual_btn)
        form.addRow("SOP:", self.sop_btn)

        self.image_label = QLabel()
        self.image_label.setFixedSize(256, 256)
        self.image_label.setScaledContents(True)
        form.addRow("Image:", self.image_label)

        self.req_label = QLabel()
        self.req_label.setWordWrap(True)
        self.req_label.setFont(QFont("Segoe UI", 12))
        form.addRow("Safety Requirements:", self.req_label)

        self.status_label = QLabel()
        self.status_label.setFont(QFont("Segoe UI", 12))
        form.addRow("", self.status_label)

        main_layout.addLayout(form)

    def clear_info(self):
        """Clear all displayed info before a new scan."""
        for fld in self.info_fields.values():
            fld.clear()
        self.manual_btn.hide()
        self.sop_btn.hide()
        self.image_label.clear()
        self.req_label.clear()
        self.status_label.clear()
