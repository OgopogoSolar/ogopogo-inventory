# modules/labels/template_manager_view.py

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QPushButton,
    QLabel, QComboBox
)
from modules.labels.template_manager_controller import TemplateManagerController

class TemplateManagerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label Template Manager")

        # 整体左右布局
        main_layout = QHBoxLayout(self)

        # — 左侧：所有模板列表 + 增删按钮 —
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("All Templates:"))
        self.listWidget = QListWidget()
        left_layout.addWidget(self.listWidget)
        btn_layout = QHBoxLayout()
        self.addButton = QPushButton("Add")
        self.deleteButton = QPushButton("Delete")
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.deleteButton)
        left_layout.addLayout(btn_layout)
        main_layout.addLayout(left_layout)

        # — 右侧：按用途分类选择模板 —
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Assign Templates by Category:"))

        # 你可以根据实际需要增删或重命名这些类别
        categories = ["Employee", "Item", "Product", "Document"]
        self.category_combos: dict[str, QComboBox] = {}

        for cat in categories:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{cat} Template:"))
            combo = QComboBox()
            row.addWidget(combo)
            right_layout.addLayout(row)
            self.category_combos[cat] = combo

        # 保存设置按钮
        self.saveButton = QPushButton("Save Settings")
        right_layout.addWidget(self.saveButton)
        right_layout.addStretch()
        main_layout.addLayout(right_layout)

        # — 控制器 & 初始加载 —
        self.controller = TemplateManagerController(self)
        self.controller.load_templates()
        self.controller.load_settings()

        # — 信号绑定 —
        self.addButton.clicked.connect(self.controller.add_template)
        self.deleteButton.clicked.connect(self.controller.delete_template)
        self.saveButton.clicked.connect(self.controller.save_settings)
