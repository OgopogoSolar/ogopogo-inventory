# modules/dbconfig/dbconfig_view.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QFormLayout, QLineEdit, QDialog, QDialogButtonBox,
    QMessageBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt

# Dialog classes 留在视图模块
# class CategoryDialog(QDialog):
#     def __init__(self, parent=None, code: str = "", desc: str = ""):
#         super().__init__(parent)
#         self.setWindowTitle("Category")
#         self._code = QLineEdit(code)
#         self._desc = QLineEdit(desc)
#         form = QFormLayout(self)
#         form.addRow("Code:", self._code)
#         form.addRow("Description:", self._desc)
#         btns = QDialogButtonBox(
#             QDialogButtonBox.StandardButton.Apply |
#             QDialogButtonBox.StandardButton.Cancel,
#             parent=self
#         )
#         btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
#         btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
#         btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
#         btns.rejected.connect(self.reject)
#         form.addRow(btns)
#         self.resize(300, 150)

#     @property
#     def code(self) -> str:
#         return self._code.text().strip()

#     @property
#     def desc(self) -> str:
#         return self._desc.text().strip()


# class SubCategoryDialog(QDialog):
#     def __init__(self, parent=None, categories: list[str]=None,
#                  code: str = "", cat_code: str = "", desc: str = ""):
#         super().__init__(parent)
#         self.setWindowTitle("SubCategory")
#         self._code   = QLineEdit(code)
#         self._parent = QComboBox()
#         # Populate with "code: description", store code as userData
#         for cat in categories or []:
#             display = f"{cat.code}: {cat.description}"
#             self._parent.addItem(display, cat.code)
#         # Pre-select by the category code
#         if cat_code:
#             idx = self._parent.findData(cat_code)
#             if idx != -1:
#                 self._parent.setCurrentIndex(idx)
#         self._desc   = QLineEdit(desc)
#         form = QFormLayout(self)
#         form.addRow("Code:", self._code)
#         form.addRow("Belongs to:", self._parent)
#         form.addRow("Description:", self._desc)
#         btns = QDialogButtonBox(
#             QDialogButtonBox.StandardButton.Apply |
#             QDialogButtonBox.StandardButton.Cancel,
#             parent=self
#         )
#         btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
#         btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
#         btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
#         btns.rejected.connect(self.reject)
#         form.addRow(btns)
#         self.resize(350, 180)

#     @property
#     def code(self) -> str:
#         return self._code.text().strip()

#     @property
#     def parent(self) -> str:
#         return self._parent.currentData()

#     @property
#     def desc(self) -> str:
#         return self._desc.text().strip()


# class ParameterDialog(QDialog):
#     def __init__(self, parent=None, pos: int=1, name: str=""):
#         super().__init__(parent)
#         self.setWindowTitle("Parameter")
#         self._pos  = QLabel(str(pos))
#         self._name = QLineEdit(name)
#         form = QFormLayout(self)
#         form.addRow("Position:", self._pos)
#         form.addRow("Name:", self._name)
#         btns = QDialogButtonBox(
#             QDialogButtonBox.StandardButton.Apply |
#             QDialogButtonBox.StandardButton.Cancel,
#             parent=self
#         )
#         btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
#         btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
#         btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
#         btns.rejected.connect(self.reject)
#         form.addRow(btns)
#         self.resize(300, 150)

#     @property
#     def pos(self) -> int:
#         return int(self._pos.text())

#     @property
#     def name(self) -> str:
#         return self._name.text().strip()

# # Dialog classes stay in the view module
class CategoryDialog(QDialog):
    def __init__(self, parent=None, code: str = "", desc: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Category")
        self._code = QLineEdit(code)
        self._desc = QLineEdit(desc)
        form = QFormLayout(self)
        form.addRow("Code:", self._code)
        form.addRow("Description:", self._desc)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)
        self.resize(300, 150)

    @property
    def code(self) -> str:
        return self._code.text().strip()

    @property
    def desc(self) -> str:
        return self._desc.text().strip()


class SubCategoryDialog(QDialog):
    def __init__(self, parent=None, categories: list[str]=None,
                 code: str = "", cat_code: str = "", desc: str = ""):
        super().__init__(parent)
        self.setWindowTitle("SubCategory")
        self._code   = QLineEdit(code)
        self._parent = QComboBox()
        for cat in categories or []:
            display = f"{cat.code}: {cat.description}"
            self._parent.addItem(display, cat.code)
        if cat_code:
            idx = self._parent.findData(cat_code)
            if idx != -1:
                self._parent.setCurrentIndex(idx)
        self._desc   = QLineEdit(desc)
        form = QFormLayout(self)
        form.addRow("Code:", self._code)
        form.addRow("Belongs to:", self._parent)
        form.addRow("Description:", self._desc)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)
        self.resize(350, 180)

    @property
    def code(self) -> str:
        return self._code.text().strip()

    @property
    def parent(self) -> str:
        return self._parent.currentData()

    @property
    def desc(self) -> str:
        return self._desc.text().strip()


class ParameterDialog(QDialog):
    def __init__(self, parent=None, pos: int=1, name: str=""):
        super().__init__(parent)
        self.setWindowTitle("Parameter")
        # now editable spinbox instead of plain label
        self._pos  = QSpinBox()
        self._pos.setRange(1, 5)
        self._pos.setValue(pos)
        self._name = QLineEdit(name)
        form = QFormLayout(self)
        form.addRow("Position:", self._pos)
        form.addRow("Name:", self._name)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)
        self.resize(300, 150)

    @property
    def pos(self) -> int:
        return self._pos.value()

    @property
    def name(self) -> str:
        return self._name.text().strip()


class DBConfigView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Configuration")

        # 左侧树视图
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Categories ▶ SubCategories"])
        self.tree.setColumnCount(1)

        # Category 按钮
        self.btn_cat_add    = QPushButton("Add Category")
        self.btn_cat_edit   = QPushButton("Edit Category")
        self.btn_cat_delete = QPushButton("Delete Category")

        # SubCategory 按钮
        self.btn_sub_add    = QPushButton("Add SubCategory")
        self.btn_sub_edit   = QPushButton("Edit SubCategory")
        self.btn_sub_delete = QPushButton("Delete SubCategory")

        left_btns = QVBoxLayout()
        left_btns.addWidget(self.btn_cat_add)
        left_btns.addWidget(self.btn_cat_edit)
        left_btns.addWidget(self.btn_cat_delete)
        left_btns.addSpacing(20)
        left_btns.addWidget(self.btn_sub_add)
        left_btns.addWidget(self.btn_sub_edit)
        left_btns.addWidget(self.btn_sub_delete)
        left_btns.addStretch()

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.tree)
        left_layout.addLayout(left_btns)

        # 右侧参数表格
        self.param_table = QTableWidget(0, 2)
        self.param_table.setHorizontalHeaderLabels(["Position", "Name"])
        self.param_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.btn_par_add    = QPushButton("Add Parameter")
        self.btn_par_edit   = QPushButton("Edit Parameter")
        self.btn_par_delete = QPushButton("Delete Parameter")

        right_btns = QHBoxLayout()
        right_btns.addWidget(self.btn_par_add)
        right_btns.addWidget(self.btn_par_edit)
        right_btns.addWidget(self.btn_par_delete)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Parameters (1–5):"))
        right_layout.addWidget(self.param_table)
        right_layout.addLayout(right_btns)
        right_layout.addStretch()

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)

        # **在这里才导入控制器，避免循环**
        from modules.dbconfig.dbconfig_controller import DBConfigController
        self.controller = DBConfigController(self)

        # 信号绑定
        self.tree.currentItemChanged.connect(self.controller.on_tree_selection)
        self.btn_cat_add.clicked.connect(self.controller.add_category)
        self.btn_cat_edit.clicked.connect(self.controller.edit_category)
        self.btn_cat_delete.clicked.connect(self.controller.delete_category)
        self.btn_sub_add.clicked.connect(self.controller.add_subcategory)
        self.btn_sub_edit.clicked.connect(self.controller.edit_subcategory)
        self.btn_sub_delete.clicked.connect(self.controller.delete_subcategory)
        self.btn_par_add.clicked.connect(self.controller.add_parameter)
        self.btn_par_edit.clicked.connect(self.controller.edit_parameter)
        self.btn_par_delete.clicked.connect(self.controller.delete_parameter)

        # 初始化加载
        self.controller.load_tree()
        self.controller.on_tree_selection()

    def reset_form(self):
        """Collapse tree & clear any selection."""
        self.tree.collapseAll()
        self.tree.clearSelection()
        # any detail-pane widgets should also be cleared here.
