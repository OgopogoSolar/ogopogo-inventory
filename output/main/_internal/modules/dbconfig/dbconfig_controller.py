# modules/dbconfig/dbconfig_controller.py

from PyQt6.QtWidgets import QMessageBox, QTreeWidgetItem, QTableWidgetItem
from PyQt6.QtCore    import Qt
from data.access_dao import (
    CategoryDAO, SubCategoryDAO, ParameterDAO, InventoryDAO, Item
)
from data.database import DatabaseManager

class DBConfigController:
    def __init__(self, view: 'DBConfigView'):
        self.view = view

    def load_tree(self):
        """加载类别及其子类别到 TreeWidget。"""
        self.view.tree.clear()
        # Category 列表
        for cat in CategoryDAO.fetch_all():
            top = QTreeWidgetItem([f"{cat.code}: {cat.description}"])
            # 注意这里用 ItemDataRole.UserRole
            top.setData(0, Qt.ItemDataRole.UserRole, ("cat", cat.code))
            self.view.tree.addTopLevelItem(top)
            # SubCategory 列表
            for sub in SubCategoryDAO.fetch_by_category(cat.code):
                node = QTreeWidgetItem([f"{sub.code}: {sub.description}"])
                node.setData(0, Qt.ItemDataRole.UserRole, ("sub", sub.code))
                top.addChild(node)
        self.view.tree.expandAll()

    def on_tree_selection(self):
        """选中树节点后更新右侧参数表和按钮状态。"""
        item = self.view.tree.currentItem()
        tbl  = self.view.param_table
        if not item:
            tbl.setRowCount(0)
            self._enable_param_buttons(False)
            return

        # 获取 (“cat” or “sub”, code) 
        kind, code = item.data(0, Qt.ItemDataRole.UserRole)
        if kind == "sub":
            params = ParameterDAO.fetch_by_subcategory(code)
            tbl.setRowCount(len(params))
            for r, p in enumerate(params):
                tbl.setItem(r, 0, QTableWidgetItem(str(p.position)))
                tbl.setItem(r, 1, QTableWidgetItem(p.name))
            self._enable_param_buttons(True)
        else:
            tbl.setRowCount(0)
            self._enable_param_buttons(False)

    def _enable_param_buttons(self, en: bool):
        for btn in (
            self.view.btn_par_add,
            self.view.btn_par_edit,
            self.view.btn_par_delete
        ):
            btn.setEnabled(en)

    # ——— Category CRUD —————————————————————————————
    def add_category(self):
        from modules.dbconfig.dbconfig_view import CategoryDialog
        dlg = CategoryDialog(self.view)
        if dlg.exec():
            try:
                CategoryDAO.insert(dlg.code, dlg.desc)
                self.load_tree()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", str(e))

    def edit_category(self):
        from modules.dbconfig.dbconfig_view import CategoryDialog
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "cat":
            return
        old_code = item.data(0, Qt.ItemDataRole.UserRole)[1]
        cat = CategoryDAO.fetch_by_code(old_code)
        dlg = CategoryDialog(self.view, code=cat.code, desc=cat.description)
        if dlg.exec():
            new_code = dlg.code
            new_desc = dlg.desc
            try:
                if new_code != old_code:
                    # 1) Rename category record (safe, parameterized)
                    sql = "UPDATE [Categories] SET [CategoryCode]=?, [CategoryDescription]=? WHERE [CategoryCode]=?"
                    cur = DatabaseManager.access_connection().cursor()
                    cur.execute(sql, (new_code, new_desc, old_code))

                    # 2) Update all subcategories' parent code
                    subs = SubCategoryDAO.fetch_by_category(old_code)
                    for sub in subs:
                        SubCategoryDAO.update(sub.code, new_code, sub.description)

                    # 3) Rename each inventory item's ItemID and category_code
                    for itm in InventoryDAO.fetch_all():
                        if itm.category_code == old_code:
                            parts = itm.item_id.split("-", 1)
                            new_id = f"{new_code}-{parts[1]}"
                            new_item = Item(
                                new_id,
                                new_code,
                                itm.subcategory_code,
                                itm.description,
                                itm.quantity,
                                itm.status,
                                itm.holder_id,
                                itm.location,
                                itm.manual_path,
                                itm.sop_path,
                                itm.image_path,
                                itm.price
                            )
                            InventoryDAO.insert(new_item)
                            InventoryDAO.delete(itm.item_id)
                else:
                    # Only description changed
                    CategoryDAO.update(old_code, new_desc)

                self.load_tree()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", str(e))

    def delete_category(self):
        """
        Delete a Category and all related data:
        1) Inventory items under this category
        2) Parameters under all its subcategories
        3) All SubCategory records under it
        4) The category record itself
        """
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "cat":
            return

        cat_code = item.data(0, Qt.ItemDataRole.UserRole)[1]

        # Ask for confirmation
        reply = QMessageBox.question(
            self.view,
            "Delete Category",
            f"Are you sure you want to delete category '{cat_code}'\nand ALL related data?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 1) Delete all inventory items under this category
            for itm in InventoryDAO.fetch_all():
                if itm.category_code == cat_code:
                    InventoryDAO.delete(itm.item_id)

            # 2) Delete all parameters under each subcategory
            subs = SubCategoryDAO.fetch_by_category(cat_code)
            for sub in subs:
                params = ParameterDAO.fetch_by_subcategory(sub.code)
                for p in params:
                    ParameterDAO.delete(sub.code, p.position)

            # 3) Delete all subcategory records
            for sub in subs:
                SubCategoryDAO.delete(sub.code)

            # 4) Delete the category record
            CategoryDAO.delete(cat_code)

            # Refresh the tree view
            self.load_tree()

        except Exception as e:
            QMessageBox.critical(self.view, "Error Deleting Category", str(e))


    # ——— SubCategory CRUD ————————————————————————————
    def add_subcategory(self):
        from modules.dbconfig.dbconfig_view import SubCategoryDialog
        cats = CategoryDAO.fetch_all()
        dlg  = SubCategoryDialog(self.view, categories=cats)
        if dlg.exec():
            try:
                SubCategoryDAO.insert(dlg.code, dlg.parent, dlg.desc)
                self.load_tree()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", str(e))

    def edit_subcategory(self):
        from modules.dbconfig.dbconfig_view import SubCategoryDialog
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
            return
        old_sub_code = item.data(0, Qt.ItemDataRole.UserRole)[1]
        sub = SubCategoryDAO.fetch_by_code(old_sub_code)
        cats = CategoryDAO.fetch_all()
        dlg = SubCategoryDialog(
            self.view,
            categories=cats,
            code=sub.code,
            cat_code=sub.category_code,
            desc=sub.description
        )
        if dlg.exec():
            new_sub_code = dlg.code
            new_parent   = dlg.parent
            new_desc     = dlg.desc
            try:
                if new_sub_code != old_sub_code or new_parent != sub.category_code:
                    # 1) Rename subcategory record
                    sql = (
                        "UPDATE [SubCategories] "
                        "SET [SubCategoryCode]=?,[CategoryCode]=?," 
                        "[SubCategoryDescription]=? "
                        "WHERE [SubCategoryCode]=?"
                    )
                    cur = DatabaseManager.access_connection().cursor()
                    cur.execute(sql, (new_sub_code, new_parent, new_desc, old_sub_code))

                    # 2) Rename each inventory item's ID and subcategory_code
                    for itm in InventoryDAO.fetch_all():
                        if itm.subcategory_code == old_sub_code:
                            parts = itm.item_id.split("-", 2)
                            rest = parts[2] if len(parts) > 2 else ""
                            new_id = f"{parts[0]}-{new_sub_code}" + (f"-{rest}" if rest else "")
                            new_item = Item(
                                new_id,
                                itm.category_code,
                                new_sub_code,
                                itm.description,
                                itm.quantity,
                                itm.status,
                                itm.holder_id,
                                itm.location,
                                itm.manual_path,
                                itm.sop_path,
                                itm.image_path,
                                itm.price
                            )
                            InventoryDAO.insert(new_item)
                            InventoryDAO.delete(itm.item_id)
                else:
                    # Only parent or description changed
                    SubCategoryDAO.update(old_sub_code, new_parent, new_desc)

                self.load_tree()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", str(e))

    def delete_subcategory(self):
        """
        Delete a SubCategory and all related data:
        1) Inventory items under this subcategory
        2) Parameters under this subcategory
        3) The subcategory record itself
        """
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
            return

        sub_code = item.data(0, Qt.ItemDataRole.UserRole)[1]
        sub = SubCategoryDAO.fetch_by_code(sub_code)

        # Ask for confirmation
        reply = QMessageBox.question(
            self.view,
            "Delete SubCategory",
            f"Are you sure you want to delete subcategory '{sub_code}'\nand ALL related items and parameters?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 1) Delete all inventory items under this subcategory
            for itm in InventoryDAO.fetch_all():
                if itm.category_code == sub.category_code and itm.subcategory_code == sub_code:
                    InventoryDAO.delete(itm.item_id)

            # 2) Delete all parameters under this subcategory
            params = ParameterDAO.fetch_by_subcategory(sub_code)
            for p in params:
                ParameterDAO.delete(sub_code, p.position)

            # 3) Delete the subcategory record
            SubCategoryDAO.delete(sub_code)

            # Refresh the tree view
            self.load_tree()

        except Exception as e:
            QMessageBox.critical(self.view, "Error Deleting SubCategory", str(e))


    # ——— Parameter CRUD —————————————————————————————
    # def add_parameter(self):
    #     from modules.dbconfig.dbconfig_view import ParameterDialog
    #     item = self.view.tree.currentItem()
    #     if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
    #         return
    #     subcode = item.data(0, Qt.ItemDataRole.UserRole)[1]
    #     params  = ParameterDAO.fetch_by_subcategory(subcode)
    #     if len(params) >= 5:
    #         QMessageBox.warning(self.view, "Limit", "Max 5 parameters.")
    #         return
    #     dlg = ParameterDialog(self.view, pos=len(params)+1)
    #     if dlg.exec():
    #         try:
    #             ParameterDAO.insert(subcode, dlg.pos, dlg.name)
    #             self.on_tree_selection()
    #         except Exception as e:
    #             QMessageBox.critical(self.view, "Error", str(e))

    # def edit_parameter(self):
    #     from modules.dbconfig.dbconfig_view import ParameterDialog
    #     item = self.view.tree.currentItem()
    #     if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
    #         return
    #     subcode = item.data(0, Qt.ItemDataRole.UserRole)[1]
    #     row     = self.view.param_table.currentRow()
    #     if row < 0:
    #         return
    #     pos  = int(self.view.param_table.item(row, 0).text())
    #     name = self.view.param_table.item(row, 1).text()
    #     dlg  = ParameterDialog(self.view, pos=pos, name=name)
    #     if dlg.exec():
    #         try:
    #             ParameterDAO.update(subcode, dlg.pos, dlg.name)
    #             self.on_tree_selection()
    #         except Exception as e:
    #             QMessageBox.critical(self.view, "Error", str(e))

    # def delete_parameter(self):
    #     item = self.view.tree.currentItem()
    #     if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
    #         return
    #     subcode = item.data(0, Qt.ItemDataRole.UserRole)[1]
    #     row     = self.view.param_table.currentRow()
    #     if row < 0:
    #         return
    #     pos = int(self.view.param_table.item(row, 0).text())
    #     if InventoryDAO.has_items_using_param(subcode, pos):
    #         QMessageBox.warning(self.view, "Cannot delete",
    #                             "There are items using this parameter.")
    #         return
    #     if QMessageBox.question(
    #         self.view, "Delete Parameter", 
    #         f"Delete parameter position {pos}?"
    #     ) == QMessageBox.StandardButton.Yes:
    #         ParameterDAO.delete(subcode, pos)
    #         self.on_tree_selection()

    # ——— Parameter CRUD —————————————————————————————
    def add_parameter(self):
        from modules.dbconfig.dbconfig_view import ParameterDialog
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
            return
        subcode = item.data(0, Qt.ItemDataRole.UserRole)[1]
        params  = ParameterDAO.fetch_by_subcategory(subcode)
        if len(params) >= 5:
            QMessageBox.warning(self.view, "Limit", "Max 5 parameters.")
            return
        dlg = ParameterDialog(self.view, pos=len(params)+1)
        if dlg.exec():
            try:
                ParameterDAO.insert(subcode, dlg.pos, dlg.name)
                self.on_tree_selection()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", str(e))

    def edit_parameter(self):
        from modules.dbconfig.dbconfig_view import ParameterDialog
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
            return
        subcode = item.data(0, Qt.ItemDataRole.UserRole)[1]
        row     = self.view.param_table.currentRow()
        if row < 0:
            return

        # capture old values
        old_pos  = int(self.view.param_table.item(row, 0).text())
        old_name = self.view.param_table.item(row, 1).text()
        dlg = ParameterDialog(self.view, pos=old_pos, name=old_name)
        if dlg.exec():
            try:
                # now pass both old and new positions plus new name
                ParameterDAO.update(
                    subcode,
                    old_pos,
                    dlg.pos,
                    dlg.name
                )
                self.on_tree_selection()
            except Exception as e:
                QMessageBox.critical(self.view, "Error", str(e))

    def delete_parameter(self):
        item = self.view.tree.currentItem()
        if not item or item.data(0, Qt.ItemDataRole.UserRole)[0] != "sub":
            return
        subcode = item.data(0, Qt.ItemDataRole.UserRole)[1]
        row     = self.view.param_table.currentRow()
        if row < 0:
            return
        pos = int(self.view.param_table.item(row, 0).text())
        if InventoryDAO.has_items_using_param(subcode, pos):
            QMessageBox.warning(self.view, "Cannot delete",
                                "There are items using this parameter.")
            return
        if QMessageBox.question(
            self.view, "Delete Parameter",
            f"Delete parameter position {pos}?"
        ) == QMessageBox.StandardButton.Yes:
            ParameterDAO.delete(subcode, pos)
            self.on_tree_selection()