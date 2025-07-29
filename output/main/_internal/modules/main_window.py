# modules/main_window.py

import re, io, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pymysql
from pymysql.err import OperationalError

from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QStackedWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QStatusBar, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem, QMenu, QSplitter, QPushButton
)
from PyQt6.QtGui import QAction, QPixmap, QImage, QColor, QPalette

from modules.auth.login_controller import LoginController, get_device_id
from modules.inventory.inventory_view     import InventoryView
from modules.employees.employee_view      import EmployeeView
from modules.dbconfig.dbconfig_view       import DBConfigView
from modules.labels.template_manager_view import TemplateManagerView
from modules.safety.safety_controller     import SafetyController
from data.access_dao import EmployeeDAO, SafetyDAO, UserDAO
from data.license_service import LicenceService
from utils.rfid_scanner import RFIDScannerManager, RFIDScannerConfig

import pdf417gen as pdf417
from PIL import Image
from data.database import DatabaseManager
import pymysql
from utils.version import CURRENT_VERSION

BASE_URL = "https://rfmtl.org/license"


class RFIDSignalHandler(QObject):
    """Signal handler to safely communicate RFID scans from background thread to main thread"""
    rfid_scanned = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user   = current_user
        self.cached_company_info = {
    "licence_type": getattr(self.current_user, "licence_type", "—"),
    "licence_expire_date": getattr(self.current_user, "licence_expire_date", "—"),
    "company_address": getattr(self.current_user, "company_address", "—")
}
        self.scanner_buffer = ""
        self.rfid_scanner = None
        self.rfid_signal_handler = RFIDSignalHandler()
        self.rfid_signal_handler.rfid_scanned.connect(self._process_rfid_scan_safe)
        self.setWindowTitle("Lab Management System")
        self.resize(1000, 700)

        # --- Menu Bar & Actions ---
        menubar = self.menuBar()
        self.actions = {}
        for key, label in [
            ('home', 'Home'),
            ('inv',  'Inventory'),
            ('emp',  'Employees'),
            ('db',   'DB Config'),
            ('tpl',  'Templates'),
            ('safety', 'Safety'),
        ]:
            act = QAction(label, self)
            self.actions[key] = act
            menubar.addAction(act)
        menubar.addSeparator()
        self.actions['logout'] = QAction("Logout", self)
        menubar.addAction(self.actions['logout'])

        # Theme Menu
        themeMenu = QMenu("Theme", self)
        menubar.insertMenu(self.actions['logout'], themeMenu)
        lightAct = themeMenu.addAction("Light Mode")
        darkAct  = themeMenu.addAction("Dark Mode")
        lightAct.triggered.connect(self._apply_light)
        darkAct .triggered.connect(self._apply_dark)
        themeMenu.setToolTip("Choose Light or Dark theme")

        # Load saved theme settings
        self.settings = QSettings("YourOrg", "LMSApp")

        # --- Central Stack inside a margin container ---
        self.stack = QStackedWidget()
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 20, 30, 20)
        container_layout.addWidget(self.stack)
        self.setCentralWidget(container)

        # Instantiate pages
        self.pages = {}
        self.pages['home']   = self._make_home_page()
        self.safety_ctrl     = SafetyController(self, self.current_user)
        self.pages['safety'] = self.safety_ctrl.view
        self.pages['inv']    = InventoryView(self.current_user)
        self.pages['emp']    = EmployeeView(self.current_user)
        try:
            self.pages['db'] = DBConfigView(self.current_user)
        except PermissionError:
            self.pages['db'] = QWidget()  # dummy placeholder
        # This should run **regardless**
        self.pages['tpl'] = TemplateManagerView()

        # Apply saved theme after pages are created
        if self.settings.value("theme","light") == "dark":
            self._apply_dark()


        # Wire menu actions
        for key in ('home','safety','inv','emp','db','tpl'):
            self.actions[key].triggered.connect(lambda _, k=key: self._switch(k))
        self.actions['logout'].triggered.connect(self._on_logout)

        # Status bar
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self._update_status_bar()

        # Apply permissions & show home
        self._apply_permissions()
        self.actions['home'].trigger()

        # Timers
        self._lic_timer = QTimer(self)
        self._lic_timer.timeout.connect(self._check_license)
        self._lic_timer.start(24*3600*1000)
        self._daily_timer = QTimer(self)
        self._daily_timer.timeout.connect(self._daily_register)
        self._daily_timer.start(24*3600*1000)
        self._daily_register()

    def _make_home_page(self) -> QWidget:
        """Construct the Home page"""
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Left panel: user & permits
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(10)
        self.lbl_welcome         = QLabel()
        self.lbl_app_version     = QLabel()
        self.lbl_id              = QLabel()
        self.lbl_type            = QLabel()
        self.lbl_license_type    = QLabel()
        self.lbl_expire_date     = QLabel()
        self.lbl_company_address = QLabel()
        for lbl in (self.lbl_welcome, self.lbl_app_version, self.lbl_id, self.lbl_type,
                    self.lbl_license_type, self.lbl_expire_date, self.lbl_company_address):
            left.addWidget(lbl)

        left.addWidget(QLabel("Safety Permits:"))
        self.permitTable = QTableWidget(0, 4)
        self.permitTable.setHorizontalHeaderLabels(
            ["Permit Type", "Issued On", "Expires On", "Issued By"]
        )
        self.permitTable.horizontalHeader().setStretchLastSection(True)
        left.addWidget(self.permitTable)
        left.addStretch()
        layout.addLayout(left, 1)

        # Right panel: scanner configuration and instructions
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        
        # RFID Scanner controls
        right.addWidget(QLabel("RFID Scanner Control:"))
        self.rfidStatusLabel = QLabel("🔴 RFID Scanner: Disconnected")
        self.rfidStatusLabel.setStyleSheet("color: red; font-weight: bold;")
        right.addWidget(self.rfidStatusLabel)
        
        rfid_controls = QHBoxLayout()
        self.rfidConnectBtn = QPushButton("Connect Scanner")
        self.rfidDisconnectBtn = QPushButton("Disconnect")
        self.rfidDisconnectBtn.setEnabled(False)
        rfid_controls.addWidget(self.rfidConnectBtn)
        rfid_controls.addWidget(self.rfidDisconnectBtn)
        right.addLayout(rfid_controls)
        
        # Scanner type selection
        right.addWidget(QLabel("Select Barcode Scanner:"))
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
        
        # Instructions for both barcode and RFID
        right.addWidget(QLabel(""))  # Spacer
        self.instructions = QLabel(
            "<b>Authentication Methods:</b><br>"
            "• <b>Barcode:</b> Scan employee barcode on this page<br>"
            "• <b>RFID:</b> Tap RFID card/tag on this page or use scanner above<br><br>"
            "<i>Both methods will switch to the scanned employee's profile</i>"
        )
        self.instructions.setWordWrap(True)
        self.instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        right.addWidget(self.instructions)
        
        right.addStretch()
        layout.addLayout(right, 1)

        # Signals & initial populate
        self.codeCombo.currentIndexChanged.connect(self._on_code_changed)
        self.rfidConnectBtn.clicked.connect(self._connect_rfid_scanner)
        self.rfidDisconnectBtn.clicked.connect(self._disconnect_rfid_scanner)
        self._on_code_changed(self.codeCombo.currentIndex())
        self._refresh_home_labels()

        return w

    def _switch(self, key: str):
        """Switch to the specified page key."""
        self.scanner_buffer = ""
        # reset old
        old = self.stack.currentWidget()
        if hasattr(old, "reset_form"):
            old.reset_form()

        # add & show new
        page = self.pages.get(key)
        if page:
            if hasattr(self, "safety_ctrl"):
                self.safety_ctrl.view.reset_form()
            self.stack.setCurrentWidget(page)
            if hasattr(page, "reset_form"):
                page.reset_form()
            if key == 'home':
                self._refresh_home_labels()
        self.stack.setFocus()

    def _apply_permissions(self):
        """Dynamically add/remove pages and menu items based on user_type and permissions."""
        ut = self.current_user.user_type

        # Clear stack
        for i in reversed(range(self.stack.count())):
            self.stack.removeWidget(self.stack.widget(i))

        # Always show: Home + Inventory
        self.stack.addWidget(self.pages['home'])
        self.actions['home'].setVisible(True)
        self.stack.addWidget(self.pages['inv'])
        self.actions['inv'].setVisible(True)

        # --- Safety page ---
        if ut == "ADMIN":
            self.stack.addWidget(self.pages['safety'])
            self.actions['safety'].setVisible(True)
        elif ut == "SUPERVISOR":
            self.stack.addWidget(self.pages['safety'])
            self.actions['safety'].setVisible(True)
        else:
            self.actions['safety'].setVisible(False)

        # --- Employees page ---
        if ut == "ADMIN":
            self.stack.addWidget(self.pages['emp'])
            self.actions['emp'].setVisible(True)
        elif ut == "SUPERVISOR":
            self.stack.addWidget(self.pages['emp'])
            self.actions['emp'].setVisible(True)
        else:
            self.actions['emp'].setVisible(False)

        # --- DB Config + Templates ---
        if ut == "ADMIN":
            self.stack.addWidget(self.pages['db'])
            self.stack.addWidget(self.pages['tpl'])
            self.actions['db'].setVisible(True)
            self.actions['tpl'].setVisible(True)
        else:
            self.actions['db'].setVisible(False)
            self.actions['tpl'].setVisible(False)

        # Logout always visible
        self.actions['logout'].setVisible(True)

    def _daily_register(self):
        """Register device once per day."""
        import urllib.request, urllib.parse, json
        email = self.current_user.rootAdminEmail
        did   = get_device_id()
        data  = urllib.parse.urlencode({'email': email, 'deviceID': did}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/device_register.php", data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.load(resp)
            if res.get('status') != 'ok':
                QMessageBox.critical(self, "Device Limit", res.get('error'))
                sys.exit(1)
        except Exception:
            pass

    def _refresh_home_labels(self):
        """Refresh the Home page labels and permit table."""
        u = self.current_user
        self.lbl_welcome.setText(f"Welcome, {u.first_name} {u.last_name}")
        self.lbl_app_version.setText(f"App Version: {CURRENT_VERSION}")
        self.lbl_id.setText(f"User ID: {u.user_id}")
        self.lbl_type.setText(f"User Type: {u.user_type}")

        lic_type = getattr(u, "licence_type", "—")
        lic_exp  = getattr(u, "licence_expire_date", "—")
        comp_addr = getattr(u, "company_address", "—")

        try:
            conn = DatabaseManager.mysql_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("""
                    SELECT LicenceType, LicenceExpireDate, CompanyAddress
                    FROM Companies WHERE CompanyID = %s
                """, (u.company_id,))
                comp = cur.fetchone()
                if comp:
                    lic_type = comp.get("LicenceType", lic_type)
                    lic_exp  = comp.get("LicenceExpireDate", lic_exp)
                    comp_addr = comp.get("CompanyAddress", comp_addr)
        except OperationalError as e:
            # Handle MySQL connection issues with reconnection
            if e.args and e.args[0] in (2006, 2013):
                print("⚠ MySQL connection lost, reconnecting...")
                try:
                    # Reset connection and retry
                    DatabaseManager._mysql_cnx = None
                    conn = DatabaseManager.mysql_connection()
                    with conn.cursor(pymysql.cursors.DictCursor) as cur:
                        cur.execute("""
                            SELECT LicenceType, LicenceExpireDate, CompanyAddress
                            FROM Companies WHERE CompanyID = %s
                        """, (u.company_id,))
                        comp = cur.fetchone()
                        if comp:
                            lic_type = comp.get("LicenceType", lic_type)
                            lic_exp  = comp.get("LicenceExpireDate", lic_exp)
                            comp_addr = comp.get("CompanyAddress", comp_addr)
                        print("✅ MySQL reconnection successful")
                except Exception as reconnect_error:
                    print(f"⚠ MySQL reconnection failed: {reconnect_error}")
            else:
                print("⚠ Error fetching company info:", e)
        except Exception as e:
            print("⚠ Error fetching company info:", e)


        self.lbl_license_type.setText(f"License Type: {lic_type}")
        self.lbl_expire_date.setText(f"License Expiration: {lic_exp}")
        self.lbl_company_address.setText(f"Company Address: {comp_addr}")

        try:
            permits = SafetyDAO.fetch_by_user(u.user_id)
        except Exception as e:
            print(f"⚠ Error fetching safety permits: {e}")
            permits = []  # Fallback to empty list
            
        self.permitTable.setRowCount(len(permits))
        for r, p in enumerate(permits):
            # Permit Type
            self.permitTable.setItem(r, 0, QTableWidgetItem(p.permit_name))
            # Start Time
            start_text = p.issue_date.strftime("%Y-%m-%d %H:%M")
            self.permitTable.setItem(r, 1, QTableWidgetItem(start_text))
            # Expire Time
            if p.expire_date is None:
                expire_text = "Permanent"
            else:
                expire_text = p.expire_date.strftime("%Y-%m-%d %H:%M")
            self.permitTable.setItem(r, 2, QTableWidgetItem(expire_text))
            # Issued By
            issuer = f"{p.issuer_first} {p.issuer_last}"
            self.permitTable.setItem(r, 3, QTableWidgetItem(issuer))

    def _on_code_changed(self, idx: int):
        """Generate and display a PDF417 barcode based on selection."""
        mapping = {
            "Scanner Bluetooth Connection": "%%BLE-HID",
            "Scanner 2.4GHz Connection":    "%%CQT-CH",
            "Scanner Power Off":            "%%POWEROFF"
        }
        data = mapping.get(self.codeCombo.currentText(), "")
        codes = pdf417.encode(data, columns=6, security_level=5)
        img   = pdf417.render_image(codes, scale=3, ratio=3)
        buf   = io.BytesIO()
        img.save(buf, format="PNG")
        qimg  = QImage.fromData(buf.getvalue(), "PNG")
        pix   = QPixmap.fromImage(qimg).scaled(
            self.barcodeLabel.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.barcodeLabel.setPixmap(pix)

    def _connect_rfid_scanner(self):
        """Connect to the RFID scanner."""
        try:
            # Create scanner with default COM17 config
            config = RFIDScannerConfig(port="COM17", baud_rate=9600)
            self.rfid_scanner = RFIDScannerManager.get_scanner(config)
            
            if self.rfid_scanner.connect():
                # Start continuous scanning with thread-safe callback
                self.rfid_scanner.start_continuous_scanning(self._on_rfid_scanned_thread_safe)
                self.rfidStatusLabel.setText("🟢 RFID Scanner: Connected (COM17)")
                self.rfidStatusLabel.setStyleSheet("color: green; font-weight: bold;")
                self.rfidConnectBtn.setEnabled(False)
                self.rfidDisconnectBtn.setEnabled(True)
            else:
                QMessageBox.warning(
                    self, "RFID Scanner", 
                    "Failed to connect to RFID scanner on COM17.\n"
                    "Please check that your scanner is connected and powered on."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "RFID Scanner Error", 
                f"Error connecting to RFID scanner: {e}"
            )

    def _disconnect_rfid_scanner(self):
        """Disconnect from the RFID scanner."""
        if self.rfid_scanner:
            self.rfid_scanner.disconnect()
            self.rfid_scanner = None
            
        self.rfidStatusLabel.setText("🔴 RFID Scanner: Disconnected")
        self.rfidStatusLabel.setStyleSheet("color: red; font-weight: bold;")
        self.rfidConnectBtn.setEnabled(True)
        self.rfidDisconnectBtn.setEnabled(False)

    def _on_rfid_scanned_thread_safe(self, rfid_uid: str):
        """Handle RFID scan from background thread - emit signal to main thread."""
        # Only process if we're on the home page
        if self.stack.currentWidget() == self.pages['home']:
            # Emit signal to be handled in main thread
            self.rfid_signal_handler.rfid_scanned.emit(rfid_uid)

    def _process_rfid_scan_safe(self, rfid_uid: str):
        """Process an RFID scan safely in the main thread."""
        try:
            self._process_rfid_scan(rfid_uid)
        except Exception as e:
            print(f"Error processing RFID scan: {e}")
            QMessageBox.critical(
                self, "RFID Error", 
                f"Error processing RFID scan: {e}"
            )

    def _on_rfid_scanned(self, rfid_uid: str):
        """Handle RFID scan from continuous scanner."""
        # Only process if we're on the home page
        if self.stack.currentWidget() != self.pages['home']:
            return
            
        try:
            # Process the RFID scan similar to keyboard input
            self._process_rfid_scan(rfid_uid)
        except Exception as e:
            print(f"Error processing RFID scan: {e}")

    def _process_rfid_scan(self, rfid_uid: str):
        """Process an RFID scan and switch users."""
        emp = UserDAO.get_by_rfid_uid(rfid_uid.strip())
        if not emp:
            QMessageBox.warning(
                self, "RFID Not Found", 
                f"No employee found with RFID: {rfid_uid}"
            )
            return

        # ─── Fix: override employee.company_id to the current admin's company ───
        emp.company_id = self.current_user.company_id

        # ── Fetch fresh company info with auto-reconnect ──
        try:
            conn = DatabaseManager.mysql_connection()
            # ensure connection is alive, reconnect if needed
            try:
                conn.ping(reconnect=True)
            except:
                # drop and recreate
                DatabaseManager._mysql_cnx = None
                conn = DatabaseManager.mysql_connection()

            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(
                    """
                    SELECT LicenceType, LicenceExpireDate, CompanyAddress
                    FROM Companies
                    WHERE CompanyID = %s
                    """,
                    (emp.company_id,)
                )
                comp = cur.fetchone()

        except OperationalError as e:
            # Error codes 2006 or 2013 mean "server has gone away" or "lost connection"
            if e.args and e.args[0] in (2006, 2013):
                print("⚠ MySQL connection lost during RFID processing, reconnecting...")
                try:
                    # reset connection and retry once
                    DatabaseManager._mysql_cnx = None
                    conn = DatabaseManager.mysql_connection()
                    with conn.cursor(pymysql.cursors.DictCursor) as cur:
                        cur.execute(
                            """
                            SELECT LicenceType, LicenceExpireDate, CompanyAddress
                            FROM Companies
                            WHERE CompanyID = %s
                            """,
                            (emp.company_id,)
                        )
                        comp = cur.fetchone()
                    print("✅ MySQL reconnection successful for RFID processing")
                except Exception as reconnect_error:
                    QMessageBox.warning(self, "Database Error", f"Failed to reconnect to database: {reconnect_error}")
                    return
            else:
                # rethrow if it's some other error
                raise

        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to fetch company info: {e}")
            return

        if not comp:
            QMessageBox.warning(self, "Warning", "Company info not found.")
            return

        emp.licence_type        = comp["LicenceType"]
        emp.licence_expire_date = comp["LicenceExpireDate"]
        emp.company_address     = comp["CompanyAddress"]

        # 2) Immediately enforce license validity
        if not LicenceService.is_company_licence_valid(emp.company_id):
            QMessageBox.critical(
                self, "License Expired",
                "Your license has expired. Please re-activate."
            )
            QApplication.quit()
            return

        # 3) Perform the UI switch
        self.current_user = emp
        self._refresh_home_labels()
        self._update_status_bar()
        self.pages['inv'] = InventoryView(emp)
        self.pages['emp'] = EmployeeView(emp)

        self.safety_ctrl     = SafetyController(self, emp)
        self.pages['safety'] = self.safety_ctrl.view
        
        self._apply_permissions()
        QMessageBox.information(
            self, "RFID Login",
            f"Switched to {emp.first_name} {emp.last_name} via RFID"
        )

    def keyPressEvent(self, event):
        text = event.text()
        current = self.stack.currentWidget()

        if (current is self.pages['home']
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):

            # Grab and clear the scanned buffer
            code, self.scanner_buffer = self.scanner_buffer, ""
            
            # Try to match barcode pattern first
            barcode_match = re.fullmatch(r"Alptraum(\d+)Technologies", code)
            
            if barcode_match:
                # Handle barcode scan
                uid = int(barcode_match.group(1))
                emp = EmployeeDAO.fetch_by_id(uid)
                if not emp:
                    QMessageBox.warning(self, "Error", f"No employee with ID #{uid}")
                    return
                    
                # ─── Fix: override employee.company_id to the current admin's company ───
                emp.company_id = self.current_user.company_id

                # ── Fetch fresh company info with auto-reconnect ──
                try:
                    conn = DatabaseManager.mysql_connection()
                    # ensure connection is alive, reconnect if needed
                    try:
                        conn.ping(reconnect=True)
                    except:
                        # drop and recreate
                        DatabaseManager._mysql_cnx = None
                        conn = DatabaseManager.mysql_connection()

                    with conn.cursor(pymysql.cursors.DictCursor) as cur:
                        cur.execute(
                            """
                            SELECT LicenceType, LicenceExpireDate, CompanyAddress
                            FROM Companies
                            WHERE CompanyID = %s
                            """,
                            (emp.company_id,)
                        )
                        comp = cur.fetchone()

                except OperationalError as e:
                    # Error codes 2006 or 2013 mean "server has gone away" or "lost connection"
                    if e.args and e.args[0] in (2006, 2013):
                        print("⚠ MySQL connection lost during barcode processing, reconnecting...")
                        try:
                            # reset connection and retry once
                            DatabaseManager._mysql_cnx = None
                            conn = DatabaseManager.mysql_connection()
                            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                                cur.execute(
                                    """
                                    SELECT LicenceType, LicenceExpireDate, CompanyAddress
                                    FROM Companies
                                    WHERE CompanyID = %s
                                    """,
                                    (emp.company_id,)
                                )
                                comp = cur.fetchone()
                            print("✅ MySQL reconnection successful for barcode processing")
                        except Exception as reconnect_error:
                            QMessageBox.warning(self, "Database Error", f"Failed to reconnect to database: {reconnect_error}")
                            return
                    else:
                        # rethrow if it's some other error
                        raise

                except Exception as e:
                    QMessageBox.warning(self, "Warning", f"Failed to fetch company info: {e}")
                    return

                if not comp:
                    QMessageBox.warning(self, "Warning", "Company info not found.")
                    return

                emp.licence_type        = comp["LicenceType"]
                emp.licence_expire_date = comp["LicenceExpireDate"]
                emp.company_address     = comp["CompanyAddress"]

                # 2) Immediately enforce license validity
                if not LicenceService.is_company_licence_valid(emp.company_id):
                    QMessageBox.critical(
                        self, "License Expired",
                        "Your license has expired. Please re-activate."
                    )
                    QApplication.quit()
                    return

                # 3) Perform the UI switch
                self.current_user = emp
                self._refresh_home_labels()
                self._update_status_bar()
                self.pages['inv'] = InventoryView(emp)
                self.pages['emp'] = EmployeeView(emp)

                self.safety_ctrl     = SafetyController(self, emp)
                self.pages['safety'] = self.safety_ctrl.view
                
                self._apply_permissions()
                QMessageBox.information(
                    self, "Barcode Login",
                    f"Switched to {emp.first_name} {emp.last_name}"
                )
                return
                
            elif code.strip():
                # Try to match as RFID UID (assuming RFID is any non-empty string that doesn't match barcode pattern)
                self._process_rfid_scan_safe(code.strip())
                return
            else:
                # Empty or invalid input
                super().keyPressEvent(event)
                return

        # Append any other keypresses to the scanner buffer
        if text:
            self.scanner_buffer += text

        super().keyPressEvent(event)

    def _update_status_bar(self):
        u = self.current_user
        self.status.showMessage(f"Logged in as: {u.first_name} {u.last_name} ({u.user_type})")

    def _on_logout(self):
        # Clean up RFID scanner
        if self.rfid_scanner:
            self._disconnect_rfid_scanner()
        
        # Clean up signal handler
        if hasattr(self, 'rfid_signal_handler'):
            self.rfid_signal_handler.rfid_scanned.disconnect()
            
        self.close()
        from main import main
        main()

    def _apply_dark(self):
        QApplication.setStyle("Fusion")  # 🔧 This line is missing in your current code!
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
        self.settings.setValue("theme", "dark")
        
        # Update instructions styling for dark theme
        if hasattr(self, 'instructions'):
            self.instructions.setStyleSheet("padding: 10px; background-color: #2a2a2a; border-radius: 5px; color: #ffffff;")

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
        self.settings.setValue("theme", "light")
        
        # Update instructions styling for light theme
        if hasattr(self, 'instructions'):
            self.instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px; color: #000000;")

    def _check_license(self):
        from data.license_service import LicenceService
        cid = self.current_user.company_id
        if not LicenceService.is_company_licence_valid(cid):
            QMessageBox.critical(
                self, "License Expired",
                "Your license has expired. Please re-activate."
            )
            QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginController()
    if not login.exec():
        sys.exit(0)
    w = MainWindow(login.logged_in_user)
    w.show()
    sys.exit(app.exec())
