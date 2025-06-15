# modules/main_window.py

import re, io
import xml.etree.ElementTree as ET
from pathlib import Path

from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QStackedWidget,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QMenuBar, QStatusBar, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem, QMenu,
)
from PyQt6.QtGui import QAction, QPixmap, QImage, QColor, QPalette

from modules.auth.login_controller        import LoginController, get_device_id
from modules.inventory.inventory_view     import InventoryView
from modules.employees.employee_view      import EmployeeView
from modules.dbconfig.dbconfig_view       import DBConfigView
from modules.labels.template_manager_view import TemplateManagerView
from data.access_dao                      import EmployeeDAO
from modules.safety.safety_controller      import SafetyController
from data.access_dao                      import SafetyDAO

import pdf417gen as pdf417  # pip install pdf417gen
from PIL import Image

BASE_URL = "https://rfmtl.org/license"

class MainWindow(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user   = current_user
        self.scanner_buffer = ""
        self.setWindowTitle("Lab Management System")
        self.resize(1000, 700)

        # --- Menu Bar & Actions ---
        menubar = self.menuBar()
        self.actions = {}
 
        # everyone
        self.actions['home'] = QAction("Home",      self); menubar.addAction(self.actions['home'])
        self.actions['inv']  = QAction("Inventory", self); menubar.addAction(self.actions['inv'])
        # admin only
        self.actions['emp']  = QAction("Employees", self); menubar.addAction(self.actions['emp'])
        # supervisor+admin only
        self.actions['db']   = QAction("DB Config", self); menubar.addAction(self.actions['db'])
        self.actions['tpl']  = QAction("Templates", self); menubar.addAction(self.actions['tpl'])
        self.actions['safety'] = QAction("Safety", self); menubar.addAction(self.actions['safety'])
        # Load saved theme
        self.settings = QSettings("YourOrg", "LMSApp")
        if self.settings.value("theme","light") == "dark":
            self._apply_dark()
        # logout
        menubar.addSeparator()
        self.actions['logout'] = QAction("Logout", self); menubar.addAction(self.actions['logout'])
        # Theme menu (on hover, choose Light/Dark)
        themeMenu = QMenu("Theme", self)
        menubar.insertMenu(self.actions['logout'], themeMenu)
        lightAct = themeMenu.addAction("Light Mode")
        darkAct  = themeMenu.addAction("Dark Mode")
        lightAct.triggered.connect(self._apply_light)
        darkAct .triggered.connect(self._apply_dark)
        themeMenu.setToolTip("Hover to choose Light or Dark theme")
        

        # --- Pages & Stack ---
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.stack.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.stack.setFocus()

        # instantiate all pages (we'll only add permitted ones)
        self.pages = {}
        self.pages['home'] = self._make_home_page()
        self.safety_ctrl      = SafetyController(self, self.current_user)
        self.pages['safety']  = self.safety_ctrl.view
        self.pages['inv']  = InventoryView(self.current_user)
        self.pages['emp']  = EmployeeView(self.current_user)
        self.pages['db']   = DBConfigView()
        self.pages['tpl']  = TemplateManagerView()

        # wire actions to switch
        self.actions['home'].triggered.connect(lambda: self._switch('home'))
        self.actions['safety'].triggered.connect(lambda: self._switch('safety'))
        self.actions['inv'] .triggered.connect(lambda: self._switch('inv'))
        self.actions['emp'] .triggered.connect(lambda: self._switch('emp'))
        self.actions['db']  .triggered.connect(lambda: self._switch('db'))
        self.actions['tpl'] .triggered.connect(lambda: self._switch('tpl'))
        self.actions['logout'].triggered.connect(self._on_logout)

        # status bar
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self._update_status_bar()

        # apply initial permissions & show home
        self._apply_permissions()
        self.actions['home'].trigger()

        # schedule daily license check
        self._lic_timer = QTimer(self)
        self._lic_timer.timeout.connect(self._check_license)
        self._lic_timer.start(24*3600*1000)  # every 24h

        # daily check
        self._daily_timer = QTimer(self)
        self._daily_timer.timeout.connect(self._daily_register)
        self._daily_timer.start(24*3600*1000)
        # first-run today:
        self._daily_register()

    def _daily_register(self):
        # Register this machine once per day
        import urllib.request, urllib.parse, json
        email = self.current_user.rootAdminEmail
        did   = get_device_id()
        data  = urllib.parse.urlencode({
            'email':    email,
            'deviceID': did
        }).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/device_register.php",
            data=data,
            headers={'Content-Type':'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.load(resp)
        if res.get('status') != 'ok':
            QMessageBox.critical(self, "Device Limit", res.get('error'))
            sys.exit(1)

    def _apply_permissions(self):
        """根据 current_user.user_type 动态添加/移除页面与菜单项"""
        ut = self.current_user.user_type
        stack = self.stack

        # clear all pages from stack
        for i in range(stack.count()-1, -1, -1):
            stack.removeWidget(stack.widget(i))

        # home always
        stack.addWidget(self.pages['home'])
        self.actions['home'].setVisible(True)

        # inventory always
        stack.addWidget(self.pages['inv'])
        self.actions['inv'].setVisible(True)

        # safety tab: SUPERVISOR & ADMIN only
        if ut in ("SUPERVISOR", "ADMIN"):
            stack.addWidget(self.pages['safety'])
            self.actions['safety'].setVisible(True)
        else:
            self.actions['safety'].setVisible(False)

        # employees: ADMIN only
        if ut == "ADMIN":
            stack.addWidget(self.pages['emp'])
            self.actions['emp'].setVisible(True)
        else:
            self.actions['emp'].setVisible(False)

        # dbconfig & templates: SUPERVISOR or ADMIN
        if ut in ("SUPERVISOR", "ADMIN"):
            stack.addWidget(self.pages['db'])
            stack.addWidget(self.pages['tpl'])
            self.actions['db'].setVisible(True)
            self.actions['tpl'].setVisible(True)
        else:
            self.actions['db'].setVisible(False)
            self.actions['tpl'].setVisible(False)

        # logout always
        self.actions['logout'].setVisible(True)

    def _switch(self, key: str):
        """切换到 pages[key]"""
        self.scanner_buffer = ""
        page = self.pages.get(key)
        if page:
            if hasattr(self, "safety_ctrl"):
                self.safety_ctrl.view.reset_form()
            # reset the old page’s form (if supported)
            old = self.stack.currentWidget()
            if hasattr(old, "reset_form"):
                old.reset_form()

            # switch
            self.stack.setCurrentWidget(page)
            self.stack.setFocus()

            # reset the new page’s form (if supported)
            new = page
            if hasattr(new, "reset_form"):
                new.reset_form()
            # whenever we go back to Home, refresh the permit list
            if key == 'home':
                self._refresh_home_labels()

    def _make_home_page(self) -> QWidget:
        """构造 Home 页面"""
        w = QWidget()
        layout = QHBoxLayout(w)
        # left: user info
        left = QVBoxLayout()
        self.lbl_welcome = QLabel()
        self.lbl_id      = QLabel()
        self.lbl_type    = QLabel()
        # license and company info
        self.lbl_license_type      = QLabel()
        self.lbl_expire_date       = QLabel()
        self.lbl_company_address   = QLabel()
        
        left.addWidget(self.lbl_welcome)
        left.addWidget(self.lbl_id)
        left.addWidget(self.lbl_type)
        left.addWidget(self.lbl_license_type)
        left.addWidget(self.lbl_expire_date)
        left.addWidget(self.lbl_company_address)

        # show Safety Permits for current user
        left.addWidget(QLabel("Safety Permits:", self))
        self.permitTable = QTableWidget(self)
        self.permitTable.setColumnCount(3)
        self.permitTable.setHorizontalHeaderLabels(
            ["Permit Type", "Expire Date", "Issued By"]
        )
        self.permitTable.horizontalHeader().setStretchLastSection(True)
        left.addWidget(self.permitTable)

        left.addStretch()

        self._refresh_home_labels()
        layout.addLayout(left, 1)
        # right: barcode
        right = QVBoxLayout()
        right.addWidget(QLabel("Select Barcode:"))
        self.codeCombo = QComboBox()
        self.codeCombo.addItems([
            "Scanner Bluetooth Connection",
            "Scanner 2.4GHz Connection",
            "Scanner Power Off",
        ])
        right.addWidget(self.codeCombo)
        self.barcodeLabel = QLabel()
        self.barcodeLabel.setFixedSize(300, 150)
        self.barcodeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.barcodeLabel)
        right.addStretch()
        layout.addLayout(right, 1)
        self.codeCombo.currentIndexChanged.connect(self._on_code_changed)
        self._on_code_changed(self.codeCombo.currentIndex())
        return w

    def _refresh_home_labels(self):
        u = self.current_user
        # refresh basic user info
        self.lbl_welcome.setText(f"Welcome, {u.first_name} {u.last_name}")
        self.lbl_id.setText(f"User ID: {u.user_id}")
        self.lbl_type.setText(f"User Type: {u.user_type}")
        # refresh license & company info
        licence_type = getattr(u, "licence_type", "")
        expire_date  = getattr(u, "licence_expire_date", "")
        address      = getattr(u, "company_address", "")
        self.lbl_license_type.setText(f"License Type: {licence_type}")
        self.lbl_expire_date.setText(f"License Expiration: {expire_date}")
        self.lbl_company_address.setText(f"Company Address: {address}")
        # refresh Safety Permits table
        permits = SafetyDAO.fetch_by_user(u.user_id)
        self.permitTable.setRowCount(len(permits))
        for r, p in enumerate(permits):
            self.permitTable.setItem(r, 0, QTableWidgetItem(p.permit_name))
            self.permitTable.setItem(r, 1, QTableWidgetItem(p.expire_date.strftime("%Y-%m-%d")))
            issuer = f"{p.issuer_first} {p.issuer_last}"
            self.permitTable.setItem(r, 2, QTableWidgetItem(issuer))

    def _update_status_bar(self):
        u = self.current_user
        self.status.showMessage(f"Logged in as: {u.first_name} {u.last_name} ({u.user_type})")

    def _on_code_changed(self, idx:int):
        mapping = {
            "Scanner Bluetooth Connection":"%%BLE-HID",
            "Scanner 2.4GHz Connection":   "%%CQT-CH",
            "Scanner Power Off":           "%%POWEROFF"
        }
        data = mapping.get(self.codeCombo.currentText(),"")
        codes = pdf417.encode(data, columns=6, security_level=5)
        img   = pdf417.render_image(codes, scale=3, ratio=3)
        buf   = io.BytesIO()
        img.save(buf,format="PNG")
        qimg  = QImage.fromData(buf.getvalue(),"PNG")
        pix   = QPixmap.fromImage(qimg)
        self.barcodeLabel.setPixmap(
            pix.scaled(self.barcodeLabel.size(),
                       Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        )

    def keyPressEvent(self, event):
        text = event.text()
        # only treat an “Alptraum...Technologies” scan as a user switch on Home
        if (self.stack.currentWidget() is self.pages['home'] and
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):
            code = self.scanner_buffer; self.scanner_buffer=""
            m = re.fullmatch(r"Alptraum(\d+)Technologies", code)
            if m:
                emp = EmployeeDAO.fetch_by_id(int(m.group(1)))
                if emp:
                    # --- Fetch and attach company license info for the new user ---
                    from data.database import DatabaseManager
                    import pymysql
                    try:
                        conn = DatabaseManager.mysql_connection()
                        with conn.cursor(pymysql.cursors.DictCursor) as cur:
                            cur.execute(
                                "SELECT CompanyAddress, LicenceType, LicenceExpireDate "
                                "FROM Companies WHERE CompanyID=%s",
                                (emp.company_id,)
                            )
                            comp = cur.fetchone()
                        setattr(emp, "company_address",     comp["CompanyAddress"])
                        setattr(emp, "licence_type",        comp["LicenceType"])
                        setattr(emp, "licence_expire_date", comp["LicenceExpireDate"])
                    except Exception:
                        # if remote fetch fails, we'll at least avoid missing-attribute errors
                        pass

                    # Now switch
                    self.current_user = emp
                    self._refresh_home_labels()
                    self._update_status_bar()
                    # rebuild pages with new user
                    self.pages['inv'] = InventoryView(emp)
                    self.pages['emp'] = EmployeeView(emp)
                    self._apply_permissions()
                    QMessageBox.information(self, "Switched",
                                            f"Switched to {emp.first_name} {emp.last_name}")
                else:
                    QMessageBox.warning(self, "Error", f"No employee #{m.group(1)}")
            return
        elif text:
            self.scanner_buffer += text
        super().keyPressEvent(event)

    def _on_logout(self):
        self.close()
        from main import main
        main()

    def _toggle_theme(self):
        if self.settings.value("theme","light")=="light":
            self._apply_dark()
            self.settings.setValue("theme","dark")
        else:
            self._apply_light()
            self.settings.setValue("theme","light")

    # def _apply_dark(self):
    #     pal = QPalette()
    #     pal.setColor(QPalette.ColorRole.Window, QColor(53,53,53))
    #     pal.setColor(QPalette.ColorRole.WindowText, QColor(255,255,255))
    #     pal.setColor(QPalette.ColorRole.Base, QColor(25,25,25))
    #     pal.setColor(QPalette.ColorRole.AlternateBase, QColor(53,53,53))
    #     pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(255,255,255))
    #     pal.setColor(QPalette.ColorRole.ToolTipText, QColor(255,255,255))
    #     pal.setColor(QPalette.ColorRole.Text, QColor(255,255,255))
    #     pal.setColor(QPalette.ColorRole.Button, QColor(53,53,53))
    #     pal.setColor(QPalette.ColorRole.ButtonText, QColor(255,255,255))
    #     self.setPalette(pal)

    # def _apply_light(self):
    #     self.setPalette(self.style().standardPalette())\

    def _apply_dark(self):
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window,         QColor("#191919"))  
        pal.setColor(QPalette.ColorRole.WindowText,     QColor("#FFFFFF")) 
        pal.setColor(QPalette.ColorRole.Base,           QColor("#353535"))  
        pal.setColor(QPalette.ColorRole.AlternateBase,  QColor("#191919"))  
        pal.setColor(QPalette.ColorRole.ToolTipBase,    QColor("#FFFFFF"))  
        pal.setColor(QPalette.ColorRole.ToolTipText,    QColor("#FFFFFF"))  
        pal.setColor(QPalette.ColorRole.Text,           QColor("#FFFFFF"))  
        pal.setColor(QPalette.ColorRole.Button,         QColor("#353535"))  
        pal.setColor(QPalette.ColorRole.ButtonText,     QColor("#FFFFFF"))  
        self.setPalette(pal)

    def _apply_light(self):
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window,        QColor("#E6E6E6"))
        pal.setColor(QPalette.ColorRole.WindowText,    QColor("#000000"))
        pal.setColor(QPalette.ColorRole.Base,          QColor("#d9d9d9"))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#E6E6E6"))
        pal.setColor(QPalette.ColorRole.ToolTipBase,   QColor("#000000"))
        pal.setColor(QPalette.ColorRole.ToolTipText,   QColor("#000000"))
        pal.setColor(QPalette.ColorRole.Text,          QColor("#000000"))
        pal.setColor(QPalette.ColorRole.Button,        QColor("#d9d9d9"))
        pal.setColor(QPalette.ColorRole.ButtonText,    QColor("#000000"))
        self.setPalette(pal)

    def _check_license(self):
        from data.license_service import LicenceService
        cid = self.current_user.company_id
        if not LicenceService.is_company_licence_valid(cid):
            QMessageBox.critical(
                self, "License Expired",
                "Your license has expired. Please re-activate."
            )
            # force logout / exit or re-invoke login flow:
            QApplication.quit()



if __name__=="__main__":
    import sys
    app = QApplication(sys.argv)
    login = LoginController()
    if not login.exec():
        sys.exit(0)
    w = MainWindow(login.logged_in_user)
    w.show()
    sys.exit(app.exec())
