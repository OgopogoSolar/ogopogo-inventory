import sys
import subprocess
import urllib.request
import json
import time
import os
import tempfile

from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from modules.auth.login_controller import LoginController
from modules.main_window import MainWindow
from utils.version import CURRENT_VERSION

VERSION_URL = "https://rfmtl.org/version.json"

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    speed = pyqtSignal(str)
    eta = pyqtSignal(str)
    finished = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, url, output_path):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self._cancel = False

    def run(self):
        try:
            req = urllib.request.Request(self.url)
            with urllib.request.urlopen(req) as response:
                total_size = int(response.getheader('Content-Length').strip())
                downloaded = 0
                start_time = time.time()
                chunk_size = 8192

                with open(self.output_path, 'wb') as f:
                    while not self._cancel:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = time.time() - start_time
                        percent = int((downloaded / total_size) * 100)
                        self.progress.emit(percent)
                        speed_kbps = downloaded / elapsed / 1024
                        self.speed.emit(f"Speed: {speed_kbps:.1f} KB/s")

                        remaining = total_size - downloaded
                        if speed_kbps > 0:
                            seconds_left = remaining / (speed_kbps * 1024)
                            mins, secs = divmod(int(seconds_left), 60)
                            self.eta.emit(f"ETA: {mins}m {secs}s")
                        else:
                            self.eta.emit("ETA: Calculating...")

                if self._cancel:
                    self.cancelled.emit()
                else:
                    self.finished.emit()
        except Exception as e:
            print(f"[Download Failed] {e}")
            self.cancelled.emit()

    def cancel(self):
        self._cancel = True

class DownloadDialog(QDialog):
    def __init__(self, url, output_path):
        super().__init__()
        self.setWindowTitle("Downloading Update")
        self.setFixedSize(420, 160)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.label = QLabel("Downloading update...")
        self.progress_bar = QProgressBar()
        self.speed_label = QLabel("Speed: 0 KB/s")
        self.eta_label = QLabel("ETA: --")

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.eta_label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.thread = DownloadThread(url, output_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.speed.connect(self.speed_label.setText)
        self.thread.eta.connect(self.eta_label.setText)
        self.thread.finished.connect(self.accept)
        self.thread.cancelled.connect(self.reject)
        self.thread.start()

    def cancel_download(self):
        self.thread.cancel()
        self.cancel_button.setEnabled(False)
        self.label.setText("Cancelling...")

def compare_versions(version1, version2):
    """
    Compare two semantic version strings.
    Returns:
        1 if version1 > version2
        0 if version1 == version2
        -1 if version1 < version2
    """
    def parse_version(version):
        # Remove any 'v' prefix and split by dots
        clean_version = version.lstrip('v')
        return [int(x) for x in clean_version.split('.')]
    
    try:
        v1_parts = parse_version(version1)
        v2_parts = parse_version(version2)
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        # Compare each part
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0  # Versions are equal
    except (ValueError, AttributeError):
        # Fallback to string comparison if parsing fails
        if version1 == version2:
            return 0
        elif version1 > version2:
            return 1
        else:
            return -1

def check_for_update():
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=5) as resp:
            meta = json.load(resp)

        latest_version = meta.get("version")
        download_url = meta.get("url")

        # Only show update dialog if latest version is actually newer
        if latest_version and compare_versions(latest_version, CURRENT_VERSION) > 0:
            reply = QMessageBox.question(
                None, "Update Available",
                f"Version {latest_version} is available (you have {CURRENT_VERSION}).\nDo you want to update now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes and download_url:
                temp_path = os.path.join(tempfile.gettempdir(), "LMS_Update.exe")
                dialog = DownloadDialog(download_url, temp_path)
                if dialog.exec():  # Only proceed if download finishes
                    subprocess.Popen(f'start "" "{temp_path}"', shell=True)
                    sys.exit(0)
    except Exception as e:
        # Silently handle update check failures - app should continue to work
        pass

def main():
    app = QApplication(sys.argv)

    check_for_update()

    login = LoginController()
    if not login.exec():
        sys.exit(0)

    user = login.logged_in_user
    main_win = MainWindow(user)
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
