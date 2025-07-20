# modules/labels/template_manager_controller.py

import shutil
from pathlib import Path
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMessageBox, QFileDialog

class TemplateManagerController:
    def __init__(self, view):
        self.view = view
        # 用 QSettings 存储各类别的默认模板
        # 组织名和应用名可自定义
        self.settings = QSettings("AlptraumTech", "LMS")

        # 定位到 modules/labels/Templates
        self.templates_dir = (
            Path(__file__).resolve().parents[1]  # modules/labels
            / "Templates"
        )
        # 确保目录存在（包括 parents）
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def load_templates(self):
        """刷新左侧列表 & 右侧所有下拉框的选项"""
        names = [f.name for f in sorted(self.templates_dir.iterdir()) if f.is_file()]

        # 左侧列表
        self.view.listWidget.clear()
        self.view.listWidget.addItems(names)

        # 右侧每个类别下拉
        for combo in self.view.category_combos.values():
            combo.clear()
            combo.addItems(names)

    def add_template(self):
        """添加新模板文件到目录，然后刷新"""
        src, _ = QFileDialog.getOpenFileName(
            self.view, "Select Template File", str(Path.home()), "All Files (*)"
        )
        if not src:
            return
        dest = self.templates_dir / Path(src).name
        try:
            shutil.copy(src, dest)
            QMessageBox.information(self.view, "Success", f"Added '{dest.name}'.")
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Failed to add:\n{e}")
        self.load_templates()

    def delete_template(self):
        """删除左侧选中的模板，并清理相关设置"""
        item = self.view.listWidget.currentItem()
        if not item:
            QMessageBox.warning(self.view, "Warning", "No template selected.")
            return
        name = item.text()
        if QMessageBox.question(
            self.view, "Confirm Delete", f"Delete template '{name}'?"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            (self.templates_dir / name).unlink()
            QMessageBox.information(self.view, "Deleted", f"Deleted '{name}'.")
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Failed to delete:\n{e}")
        # 如果某类别的默认值是被删文件，要清除配置
        for cat in self.view.category_combos:
            key = f"default_template_{cat.lower()}"
            if self.settings.value(key, "") == name:
                self.settings.remove(key)
        self.load_templates()

    def load_settings(self):
        """将各类别的已保存默认模板，设置到对应下拉框"""
        for cat, combo in self.view.category_combos.items():
            key = f"default_template_{cat.lower()}"
            val = self.settings.value(key, "")
            idx = combo.findText(val)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def save_settings(self):
        """保存当前所有类别下拉框的选中值到 QSettings"""
        for cat, combo in self.view.category_combos.items():
            tpl = combo.currentText()
            key = f"default_template_{cat.lower()}"
            self.settings.setValue(key, tpl)
        QMessageBox.information(self.view, "Saved", "Template settings saved.")

    def reset_form(self):
        """Reload templates & clear any in-progress selections."""
        self.controller.load_templates()
        self.controller.load_settings()
        self.listWidget.clearSelection()
        for combo in self.category_combos.values():
            combo.setCurrentIndex(0)