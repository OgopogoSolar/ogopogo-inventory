# # modules/labels/template_manager_view.py

# from pathlib import Path
# from PyQt6.QtWidgets import (
#     QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QPushButton,
#     QLabel, QComboBox
# )
# from modules.labels.template_manager_controller import TemplateManagerController

# class TemplateManagerView(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Label Template Manager")

#         # 整体左右布局
#         main_layout = QHBoxLayout(self)

#         # — 左侧：所有模板列表 + 增删按钮 —
#         left_layout = QVBoxLayout()
#         left_layout.addWidget(QLabel("All Templates:"))
#         self.listWidget = QListWidget()
#         left_layout.addWidget(self.listWidget)
#         btn_layout = QHBoxLayout()
#         self.addButton = QPushButton("Add")
#         self.deleteButton = QPushButton("Delete")
#         btn_layout.addWidget(self.addButton)
#         btn_layout.addWidget(self.deleteButton)
#         left_layout.addLayout(btn_layout)
#         main_layout.addLayout(left_layout)

#         # — 右侧：按用途分类选择模板 —
#         right_layout = QVBoxLayout()
#         right_layout.addWidget(QLabel("Assign Templates by Category:"))

#         # 你可以根据实际需要增删或重命名这些类别
#         categories = ["Employee", "Item", "Product", "Document"]
#         self.category_combos: dict[str, QComboBox] = {}

#         for cat in categories:
#             row = QHBoxLayout()
#             row.addWidget(QLabel(f"{cat} Template:"))
#             combo = QComboBox()
#             row.addWidget(combo)
#             right_layout.addLayout(row)
#             self.category_combos[cat] = combo

#         # 保存设置按钮
#         self.saveButton = QPushButton("Save Settings")
#         right_layout.addWidget(self.saveButton)
#         right_layout.addStretch()
#         main_layout.addLayout(right_layout)

#         # — 控制器 & 初始加载 —
#         self.controller = TemplateManagerController(self)
#         self.controller.load_templates()
#         self.controller.load_settings()

#         # — 信号绑定 —
#         self.addButton.clicked.connect(self.controller.add_template)
#         self.deleteButton.clicked.connect(self.controller.delete_template)
#         self.saveButton.clicked.connect(self.controller.save_settings)


# modules/labels/template_manager_view.py

# modules/labels/template_manager_view.py

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QSplitter, QListWidget, QPushButton,
    QLabel, QComboBox, QSizePolicy, QSpacerItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from modules.labels.template_manager_controller import TemplateManagerController

# ─────────────────────────────────────────────
# Styled Helpers
# ─────────────────────────────────────────────
def styled_label(text: str, bold: bool = False, size: int = 12) -> QLabel:
    lbl = QLabel(text)
    weight = QFont.Weight.Bold if bold else QFont.Weight.Normal
    lbl.setFont(QFont("Segoe UI", size, weight))
    return lbl

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


class TemplateManagerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label Template Manager")
        self.setMinimumSize(900, 600)

        # Instantiate controller first so _init_ui can bind to it
        self.controller = TemplateManagerController(self)

        # Build UI
        self._init_ui()

        # Load data
        self.controller.load_templates()
        self.controller.load_settings()

    def _init_ui(self):
        # Main splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # ── Left Pane: All Templates ────────
        left_group = QGroupBox("All Templates")
        left_group.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        left_layout.addWidget(styled_label("Templates:", size=12))
        self.listWidget = QListWidget()
        self.listWidget.setFont(QFont("Segoe UI", 11))
        left_layout.addWidget(self.listWidget)

        btn_layout = QHBoxLayout()
        self.addButton = styled_button("Add")
        self.deleteButton = styled_button("Delete")
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.deleteButton)
        btn_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        left_layout.addLayout(btn_layout)

        left_group.setLayout(left_layout)
        splitter.addWidget(left_group)

        # ── Right Pane: Assign by Category ──
        right_group = QGroupBox("Assign Templates by Category")
        right_group.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)

        right_layout.addWidget(styled_label("Select template for each category:", size=12))

        categories = ["Employee", "Item", "Product", "Document"]
        self.category_combos: dict[str, QComboBox] = {}

        for cat in categories:
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(styled_label(f"{cat} Template:", size=12))
            combo = styled_combobox()
            row.addWidget(combo, stretch=1)
            right_layout.addLayout(row)
            self.category_combos[cat] = combo

        # Save Settings Button
        self.saveButton = styled_button("Save Settings")
        right_layout.addWidget(self.saveButton, alignment=Qt.AlignmentFlag.AlignLeft)
        right_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        right_group.setLayout(right_layout)
        splitter.addWidget(right_group)

        # Main layout with consistent margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.addWidget(splitter)

        # Signal bindings (now safe since controller exists)
        self.addButton.clicked.connect(self.controller.add_template)
        self.deleteButton.clicked.connect(self.controller.delete_template)
        self.saveButton.clicked.connect(self.controller.save_settings)

