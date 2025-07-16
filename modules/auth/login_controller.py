# modules/auth/login_controller.py

from PyQt6.QtWidgets import QMessageBox, QInputDialog
from modules.auth.login_view import LoginDialog
from data.database import DatabaseManager
import hashlib, pymysql
from data.license_service import LicenceService
from data.access_dao import UserDAO
import urllib.request, urllib.parse, json, urllib.error
import wmi
import sys

BASE_URL = "https://rfmtl.org/license"


def get_device_id():
    """
    Collect hardware serials via WMI: DiskDrive, Processor, BaseBoard, BIOS.
    Returns a concatenated string as the device identifier.
    """
    c = wmi.WMI()
    parts = []
    for disk in c.Win32_DiskDrive():
        parts.append(disk.SerialNumber.strip() if disk.SerialNumber else '')
    for cpu in c.Win32_Processor():
        parts.append(cpu.ProcessorId.strip() if cpu.ProcessorId else '')
    for bb in c.Win32_BaseBoard():
        parts.append(bb.SerialNumber.strip() if bb.SerialNumber else '')
    for bios in c.Win32_BIOS():
        parts.append(bios.SerialNumber.strip() if bios.SerialNumber else '')
    return ''.join(parts)


class LoginController:
    """
    Handles login, license activation, first-time profile completion,
    and device registration.
    """

    def __init__(self):
        self.view = LoginDialog()
        self.view.loginButton.clicked.connect(self._on_login)
        self.logged_in_user = None

    def exec(self) -> int:
        return self.view.exec()

    def _on_login(self):
        user_input = self.view.userLineEdit.text().strip()
        raw_password = self.view.passLineEdit.text()
        if not user_input or not raw_password:
            QMessageBox.warning(self.view, "Login Failed", "Please enter username/email and password.")
            return

        pwd_hash = hashlib.md5(raw_password.encode("utf-8")).hexdigest()

        try:
            conn = DatabaseManager.mysql_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(
                    "SELECT * FROM Companies WHERE rootAdminEmail=%s AND rootAdminPassword=%s",
                    (user_input, pwd_hash)
                )
                row = cur.fetchone()
        except Exception as e:
            QMessageBox.critical(self.view, "Database Error", f"Connection fail: {e}")
            return

        if not row:
            QMessageBox.warning(self.view, "Login Fail", "Username/email or password is incorrect.")
            return

        if not LicenceService.is_company_licence_valid(row["CompanyID"]):
            key, ok = QInputDialog.getText(
                self.view, "License Expired", "Your license expired. Enter new license key:"
            )
            if not ok or not key:
                return
            data = urllib.parse.urlencode({'email': user_input, 'key': key}).encode()
            req = urllib.request.Request(
                f"{BASE_URL}/activate_license.php", data=data,
                headers={'Content-Type':'application/x-www-form-urlencoded'}
            )
            try:
                with urllib.request.urlopen(req, timeout=5):
                    pass
            except urllib.error.HTTPError as e:
                QMessageBox.critical(self.view, "Server Error", f"Activation failed: {e.code}")
                return
            except Exception as e:
                QMessageBox.critical(self.view, "Network Error", str(e))
                return

        local_user = UserDAO.get_by_id(1)
        if not local_user:
            QMessageBox.critical(self.view, "Login Error", "Local Admin user not found.")
            return

        # Attach remote attributes
        setattr(local_user, 'licence_type',        row['LicenceType'])
        setattr(local_user, 'company_name',        row.get('CompanyName'))
        setattr(local_user, 'licence_expire_date', row.get('LicenceExpireDate'))
        setattr(local_user, 'company_address',     row.get('CompanyAddress'))
        setattr(local_user, 'rootAdminEmail',      row['rootAdminEmail'])
        setattr(local_user, 'licence_code',        row['LicenceCode'])

        self.logged_in_user = local_user
        self.view.accept()
        self._post_login()

    def _post_login(self):
        user = self.logged_in_user

        # First-time profile
        if not user.company_name:
            name, ok = QInputDialog.getText(self.view, "Complete Profile", "Enter Company Name:")
            if not ok or not name:
                QMessageBox.warning(self.view, "Canceled", "You must enter a company name.")
                sys.exit(0)
            addr, ok = QInputDialog.getText(self.view, "Complete Profile", "Enter Company Address:")
            if not ok:
                addr = ''
            data = urllib.parse.urlencode({
                'email':          user.rootAdminEmail,
                'companyName':    name,
                'companyAddress': addr
            }).encode()
            req = urllib.request.Request(
                f"{BASE_URL}/update_company.php", data=data,
                headers={'Content-Type':'application/x-www-form-urlencoded'}
            )
            try:
                with urllib.request.urlopen(req, timeout=5): pass
            except urllib.error.HTTPError as e:
                QMessageBox.critical(self.view, "Server Error", f"Update profile failed: {e.code}")
                sys.exit(1)
            except Exception as e:
                QMessageBox.critical(self.view, "Network Error", str(e))
                sys.exit(1)

        # Device registration
        did = get_device_id()
        data = urllib.parse.urlencode({
            'email':    user.rootAdminEmail,
            'deviceID': did
        }).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/device_register.php", data=data,
            headers={'Content-Type':'application/x-www-form-urlencoded'}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.load(resp)
        except urllib.error.HTTPError as e:
            QMessageBox.critical(self.view, "Server Error", f"Device registration failed: {e.code}")
            sys.exit(1)
        except Exception as e:
            QMessageBox.critical(self.view, "Network Error", str(e))
            sys.exit(1)
        if result.get('status') != 'ok':
            QMessageBox.critical(self.view, "Device Limit", result.get('error'))
            sys.exit(1)
