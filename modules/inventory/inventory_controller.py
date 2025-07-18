import csv

from utils.label_printer import print_label

from PyQt6.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QLabel, QPushButton, QDialogButtonBox, QFormLayout
)
from PyQt6.QtGui     import QPixmap, QDesktopServices
from PyQt6.QtCore    import Qt, QUrl, QSettings
from pathlib         import Path
from data.access_dao import InventoryDAO, Item, ItemSafetyRequirementDAO, SafetyDAO, EmployeeDAO


def open_file(path: str):
    if Path(path).exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    else:
        QMessageBox.critical(None, "Error", f"File not found: {path}")

class InventoryController:
    def __init__(self, view):
        # When user double‐clicks a cell, show all item details
        self.view = view
        self.view.table.cellDoubleClicked.connect(self.on_show_details)
        self._all = []  # 缓存所有物品列表
        # QSettings 用于读取用户在 Templates 页面中保存的默认模板
        self.settings = QSettings("AlptraumTech", "LMS")
        # Templates 目录（请根据项目目录结构确认路径）
        self.templates_dir = (
            Path(__file__).resolve().parents[2] / "modules" / "Templates"
        )

    def load_items(self):
        """从数据库获取所有物品并刷新视图"""
        self._all = InventoryDAO.fetch_all()
        self.view.refresh(self._all)

    def on_search(self, text: str):
        """根据搜索框文本过滤物品"""
        t = text.strip().lower()
        if not t:
            filtered = self._all
        else:
            filtered = [
                itm for itm in self._all
                if t in itm.item_id.lower() or t in itm.description.lower()
            ]
        self.view.refresh(filtered)

    def on_add(self):
        from modules.inventory.inventory_view import ItemDialog
        dlg = ItemDialog(self.view)
        if dlg.exec():
            new = Item(
                item_id=dlg.item_id,
                category_code=dlg.category_code,
                subcategory_code=dlg.subcategory_code,
                description=dlg.desc,
                quantity=dlg.qty,
                status=dlg.status,
                holder_id=None,
                location=dlg.location,
                manual_path=dlg.manual,
                sop_path=dlg.sop,
                image_path=dlg.image,
                price=dlg.price
            )
            InventoryDAO.insert(new)
            self.load_items()

    def on_edit(self):
        from modules.inventory.inventory_view import ItemDialog
        iid = self.view._current_item_id()
        if not iid:
            return
        existing = InventoryDAO.fetch_by_id(iid)
        dlg = ItemDialog(self.view, existing)
        if dlg.exec():
            new_id = dlg.item_id
            if new_id != existing.item_id:
                if InventoryDAO.fetch_by_id(new_id):
                    QMessageBox.warning(self.view, "Error", f"ItemID '{new_id}' already exists.")
                    return
                # 更换主键：插入新记录，删除旧记录
                new_item = Item(
                    item_id=new_id,
                    category_code=dlg.category_code,
                    subcategory_code=dlg.subcategory_code,
                    description=dlg.desc,
                    quantity=dlg.qty,
                    status=dlg.status,
                    holder_id=existing.holder_id,
                    location=dlg.location,
                    manual_path=dlg.manual,
                    sop_path=dlg.sop,
                    image_path=dlg.image,
                    price=dlg.price
                )
                InventoryDAO.insert(new_item)
                InventoryDAO.delete(existing.item_id)
            else:
                # 更新除主键以外的字段
                existing.category_code    = dlg.category_code
                existing.subcategory_code = dlg.subcategory_code
                existing.description      = dlg.desc
                existing.quantity         = dlg.qty
                existing.status           = dlg.status
                existing.location         = dlg.location
                existing.manual_path      = dlg.manual
                existing.sop_path         = dlg.sop
                existing.image_path       = dlg.image
                existing.price            = dlg.price
                InventoryDAO.update(existing)
            self.load_items()

    def on_delete(self):
        iid = self.view._current_item_id()
        if not iid:
            return
        if QMessageBox.question(self.view, "Delete", f"Delete item {iid}?") == QMessageBox.StandardButton.Yes:
            InventoryDAO.delete(iid)
            self.load_items()

    def on_checkout(self):
        iid = self.view._current_item_id()
        if not iid:
            return
        itm = InventoryDAO.fetch_by_id(iid)
        # ❶ Verify user has all required safety permits
        user_perms = [p.permission_id for p in SafetyDAO.fetch_by_user(self.view._current_user.user_id)]
        reqs      = ItemSafetyRequirementDAO.fetch_by_item(iid)
        missing   = [str(pid) for pid in reqs if pid not in user_perms]
        if missing:
            QMessageBox.warning(self.view, "Error",
                f"Cannot check out. Missing permits: {', '.join(missing)}")
            return
        if itm.status != "In Stock":
            QMessageBox.warning(self.view, "Error", "Item not in stock.")
            return
        itm.status    = "In Use"
        itm.holder_id = self.view._current_user.user_id
        InventoryDAO.update(itm)
        self.load_items()

    def on_return(self):
        iid = self.view._current_item_id()
        if not iid:
            return
        itm = InventoryDAO.fetch_by_id(iid)
        if itm.status != "In Use":
            QMessageBox.warning(self.view, "Error", "Item not checked out.")
            return
        itm.status    = "In Stock"
        itm.holder_id = None
        InventoryDAO.update(itm)
        self.load_items()

    def on_export(self):
        """导出当前列表为 CSV"""
        path, _ = QFileDialog.getSaveFileName(self.view, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        header = [
            "Item ID", "Category", "Subcategory", "Location", "Quantity", "Status",
            "Param1", "Param2", "Param3", "Param4", "Param5", "Price"
        ]
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for itm in self._all:
                parts  = itm.item_id.split('-')
                params = parts[2:2+5] + [""] * (5 - max(0, len(parts)-2))
                row = [itm.item_id, itm.category_code, itm.subcategory_code,
                       itm.location, itm.quantity, itm.status, *params, itm.price or ""]
                writer.writerow(row)
        QMessageBox.information(self.view, "Exported", f"Saved to {path}.")

    def open_check_dialog(self):
        """Open the Check-In/Out dialog for continuous scanning."""
        from modules.inventory.inventory_view import CheckDialog
        dlg = CheckDialog(self.view)
        # When Enter (or scanner newline) is detected, process and stay open
        dlg.id_input.returnPressed.connect(lambda: self.process_check(dlg))
        dlg.exec()

    def process_check(self, dlg):
        """Process check-in/check-out input continuously and update database immediately."""
        item_id = dlg.id_input.text().strip()
        dlg.clear_info()
        itm = InventoryDAO.fetch_by_id(item_id)
        if not itm:
            dlg.status_label.setText(f"Item '{item_id}' not found.")
            dlg.status_label.setStyleSheet("color: red;")
            # prepare for next scan
            dlg.id_input.clear()
            dlg.id_input.setFocus()
            return
        # fill info fields (including Description + Price)
        dlg.info_fields['category'].setText(itm.category_code)
        dlg.info_fields['subcategory'].setText(itm.subcategory_code)
        dlg.info_fields['location'].setText(itm.location)
        dlg.info_fields['quantity'].setText(str(itm.quantity))
        dlg.info_fields['status'].setText(itm.status)
        # holder name
        holder = ""
        if itm.holder_id:
            usr = EmployeeDAO.fetch_by_id(itm.holder_id)
            holder = f"{usr.first_name} {usr.last_name}" if usr else ""
        dlg.info_fields['holder'].setText(holder)
        dlg.info_fields['parameters'].setText(" ".join(itm.item_id.split('-')[2:]))
        dlg.info_fields['description'].setText(itm.description)
        dlg.info_fields['price'].setText(str(itm.price) if itm.price else "")

        # Manual button
        if itm.manual_path and Path(itm.manual_path).exists():
            dlg.manual_btn.show()
            dlg.manual_btn.clicked.connect(lambda _, p=itm.manual_path: open_file(p))
        else:
            dlg.manual_btn.hide()

        # SOP button
        if itm.sop_path and Path(itm.sop_path).exists():
            dlg.sop_btn.show()
            dlg.sop_btn.clicked.connect(lambda _, p=itm.sop_path: open_file(p))
        else:
            dlg.sop_btn.hide()

        # Image
        if itm.image_path and Path(itm.image_path).exists():
            # Use the correct AspectRatioMode enum
            pix = QPixmap(itm.image_path).scaled(
                256, 256, Qt.AspectRatioMode.KeepAspectRatio
            )
            dlg.image_label.setPixmap(pix)
        else:
            dlg.image_label.clear()

        # Safety Requirements (AND logic: user must have _all_ reqs)
        req_ids    = ItemSafetyRequirementDAO.fetch_by_item(item_id)
        # each UserSafetyPermit has .permit_id, not .permission_id
        user_perms = [p.permit_id for p in SafetyDAO.fetch_by_user(self.view._current_user.user_id)]
        missing    = [pid for pid in req_ids if pid not in user_perms]

        # Display all requirements
        type_map   = {t.permission_id: t.name for t in SafetyDAO.fetch_all_types()}
        req_names  = [type_map.get(pid, str(pid)) for pid in req_ids]
        dlg.req_label.setText("\n".join(req_names))

        # If any are missing, block the operation
        if missing:
            missing_names = [type_map.get(pid, str(pid)) for pid in missing]
            # show each missing permit on its own line
            text = "Cannot check out. Missing permits:\n" + "\n".join(missing_names)
            dlg.status_label.setText(text)
            dlg.status_label.setStyleSheet("color: red;")
            # prepare for next scan
            dlg.id_input.clear()
            dlg.id_input.setFocus()
            return

        # Now switch status
        if itm.holder_id is None:
            itm.holder_id = self.view._current_user.user_id
            itm.status    = "In Use"
            action        = "checked out"
        else:
            itm.holder_id = None
            itm.status    = "In Stock"
            action        = "returned"
        # update database record
        InventoryDAO.update(itm)
        # refresh main inventory view immediately
        self.load_items()

        # update dialog to show new status
        dlg.info_fields['status'].setText(itm.status)
        dlg.info_fields['holder'].setText(str(itm.holder_id or ""))
        dlg.status_label.setText(f"Item {action} successfully.")
        dlg.status_label.setStyleSheet("color: green;")
        # clear input and set focus for next scan
        dlg.id_input.clear()
        dlg.id_input.setFocus()

    def on_print_item_label(self):
        """打印选中行的标签"""
        indexes = self.view.table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self.view, "提示", "请先选择一行")
            return
        row = indexes[0].row()
        # 构建占位符字典
        headers = [
            self.view.table.horizontalHeaderItem(i).text()
            for i in range(self.view.table.columnCount())
        ]
        placeholder_dict = {}
        for i in range(len(headers)):
            key = headers[i]
            val = self.view.table.item(row, i).text() or ""
        if key == "Parameters":
            # Split by newlines or commas, strip spaces, and join with single space
            parts = [p.strip() for p in re.split(r"[,\n]+", val) if p.strip()]
            val = " ".join(parts)


        # 读取模板名称
        cat     = self.view.labelTypeCombo.currentText().lower()
        key     = f"default_template_{cat}"
        tpl_name= self.settings.value(key, "")
        if not tpl_name:
            QMessageBox.warning(self.view, "打印失败", f"请先在 Templates 页面为 '{cat}' 配置模板。")
            return
        template_path = self.templates_dir / tpl_name
        if not template_path.exists():
            QMessageBox.critical(self.view, "打印失败", f"找不到模板文件: {template_path}")
            return
        # 调用通用打印
        try:
            print_label(template_path, placeholder_dict)
        except Exception as e:
            QMessageBox.critical(self.view, "打印失败", str(e))

    def on_show_details(self, row: int, col: int):
        """Pop up a dialog showing every field for the selected item."""
        iid = self.view.table.item(row, 0).text()
        itm = InventoryDAO.fetch_by_id(iid)
        if not itm:
            QMessageBox.warning(self.view, "Error", f"Item {iid} not found.")
            return

        dlg = QDialog(self.view)
        dlg.setWindowTitle(f"Details — {iid}")
        form = QFormLayout(dlg)

        # Basic fields
        form.addRow("Item ID:",       QLabel(itm.item_id))
        form.addRow("Category:",      QLabel(itm.category_code))
        form.addRow("SubCategory:",   QLabel(itm.subcategory_code))
        form.addRow("Description:",   QLabel(itm.description))
        form.addRow("Quantity:",      QLabel(str(itm.quantity)))
        form.addRow("Status:",        QLabel(itm.status))

        # Holder name
        holder = ""
        if itm.holder_id:
            usr = EmployeeDAO.fetch_by_id(itm.holder_id)
            holder = f"{usr.first_name} {usr.last_name}" if usr else ""
        form.addRow("Holder:",        QLabel(holder))

        form.addRow("Location:",      QLabel(itm.location))
        form.addRow("Price:",         QLabel(str(itm.price) if itm.price else ""))

        # Manual & SOP buttons
        if itm.manual_path:
            btn = QPushButton("Open Manual")
            btn.clicked.connect(lambda _, p=itm.manual_path: open_file(p))
            form.addRow("Manual:", btn)
        if itm.sop_path:
            btn = QPushButton("Open SOP")
            btn.clicked.connect(lambda _, p=itm.sop_path: open_file(p))
            form.addRow("SOP:", btn)

        # Image preview (256×256)
        if itm.image_path and Path(itm.image_path).exists():
            # Use the correct AspectRatioMode enum
            pix = QPixmap(itm.image_path).scaled(
                256, 256, Qt.AspectRatioMode.KeepAspectRatio
            )
            img_lbl = QLabel()
            img_lbl.setPixmap(pix)
            form.addRow("Image:", img_lbl)
        
        # Safety Requirements
        req_ids = ItemSafetyRequirementDAO.fetch_by_item(iid)
        type_map = {t.permission_id: t.name for t in SafetyDAO.fetch_all_types()}
        req_names = [type_map.get(pid, str(pid)) for pid in req_ids]
        form.addRow("Safety Requirements:", QLabel("\n".join(req_names)))

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        dlg.exec()


