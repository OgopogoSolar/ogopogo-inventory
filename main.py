# main.py

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from modules.auth.login_controller import LoginController
from modules.main_window import MainWindow

from PyQt6.QtGui import QIcon
app = QApplication(sys.argv)
app.setWindowIcon(QIcon("icon.ico"))

def main():
    app = QApplication(sys.argv)

    check_for_update()

    login = LoginController()
    # PyQt6 uses exec() on QDialog
    if not login.exec():
        sys.exit(0)

    user = login.logged_in_user
    main_win = MainWindow(user)
    main_win.show()
    sys.exit(app.exec())

import pkg_resources, subprocess, sys
import urllib.request, json

def check_for_update():
    try:
        with urllib.request.urlopen("https://rfmtl.org/version.json", timeout=3) as resp:
            meta = json.load(resp)
        current = pkg_resources.get_distribution("your-package-name").version
        if meta["version"] != current:
            ans = QMessageBox.question(
                None, "Update Available",
                f"v{meta['version']} is available. Download & install?"
            )
            if ans == QMessageBox.StandardButton.Yes:
                # download new installer via urllib
                fn = "update.exe"
                with urllib.request.urlopen(meta["url"]) as src, open(fn, "wb") as dst:
                    dst.write(src.read())
                subprocess.Popen([fn])
                sys.exit(0)
    except Exception:
        pass

if __name__ == "__main__":
    main()
