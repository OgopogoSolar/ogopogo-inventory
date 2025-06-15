# modules/auth/login_view.py

from PyQt6.QtWidgets import QDialog, QMessageBox, QInputDialog, QLineEdit, QLabel
from PyQt6 import uic
from PyQt6.QtCore import Qt
from pathlib import Path
import urllib.request
import urllib.parse
import json

# ==== CONFIG ====  
# Point this to wherever your PHP lives:
BASE_URL = "https://rfmtl.org/license"

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        # Load your existing .ui file
        ui_file = Path(__file__).resolve().parents[2] / "ui" / "login.ui"
        uic.loadUi(ui_file, self)   # provides: self.userLineEdit, self.passLineEdit, self.loginButton

        # Mask password field
        self.passLineEdit.setEchoMode(self.passLineEdit.EchoMode.Password)

        # Add "Forgot Password?" link
        forgot = QLabel('<a href="#">Forgot Password?</a>', self)
        forgot.setTextFormat(Qt.TextFormat.RichText)
        forgot.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        forgot.linkActivated.connect(self._on_forgot)
        self.layout().addWidget(forgot)

    def _on_forgot(self):
        """
        1) Ask user for their admin email.
        2) Request a 6-digit reset code via reset_request.php.
        3) Prompt for code, then new password.
        4) Submit to reset_password.php and report success/failure.
        """
        from PyQt6.QtWidgets import QLineEdit
        # 1) Prompt for email
        email, ok = QInputDialog.getText(self, "Reset Password", "Enter your admin email:")
        if not ok or not email:
            return

        # 2) Request reset code
        url = f"{BASE_URL}/reset_request.php"
        data = urllib.parse.urlencode({'email': email}).encode('utf-8')
        req  = urllib.request.Request(
            url, data=data,
            headers={'Content-Type':'application/x-www-form-urlencoded'}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.load(resp)
        except urllib.error.HTTPError:
            # treat HTTP errors as success (to avoid disclosing existence)
            res = {'status':'ok'}
        except Exception as e:
            QMessageBox.critical(self, "Network Error", f"Could not send reset code:{e}")
            return

        # Always inform the user
        QMessageBox.information(
            self, "Reset Code Sent",
            "If that email exists in our system, a reset code has been sent."
        )

        # 3) Prompt for the 6-digit code
        code, ok = QInputDialog.getText(self, "Enter Reset Code", "Enter the 6-digit code:")
        if not ok or not code:
            return

        # 4) Prompt for new password
        new_pwd, ok = QInputDialog.getText(
            self, "New Password", "Enter your new password:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not new_pwd:
            return

        # 5) Submit password reset
        url2 = f"{BASE_URL}/reset_password.php"
        payload = urllib.parse.urlencode({
            'email':    email,
            'code':     code,
            'password': new_pwd
        }).encode('utf-8')
        req2 = urllib.request.Request(
            url2, data=payload,
            headers={'Content-Type':'application/x-www-form-urlencoded'}
        )
        try:
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                res2 = json.load(resp2)
        except urllib.error.HTTPError as e:
            # read error message from response body
            try:
                err = e.read().decode()
                msg = json.loads(err).get('error','Reset failed')
            except:
                msg = 'Reset failed'
            QMessageBox.warning(self, "Error", msg)
            return
        except Exception as e:
            QMessageBox.critical(self, "Network Error", f"Could not reset password:{e}")
            return

        # 6) Single popup for result
        if res2.get('status') == 'ok':
            QMessageBox.information(self, "Success", "Your password has been reset.")
        else:
            QMessageBox.warning(self, "Error", res2.get('error','Password reset failed.'))

