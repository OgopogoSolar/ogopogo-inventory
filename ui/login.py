# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        if not LoginDialog.objectName():
            LoginDialog.setObjectName(u"LoginDialog")
        LoginDialog.setStyleSheet(u"\n"
"    QWidget {\n"
"        background-color: #f4f4f4;\n"
"        font-family: 'Segoe UI', sans-serif;\n"
"        font-size: 14px;\n"
"    }\n"
"    QLabel#titleLabel {\n"
"        font-size: 22px;\n"
"        font-weight: bold;\n"
"        color: #2c3e50;\n"
"        margin-bottom: 20px;\n"
"    }\n"
"    QLineEdit {\n"
"        padding: 8px 12px;\n"
"        border: 1px solid #ccc;\n"
"        border-radius: 8px;\n"
"        background-color: white;\n"
"    }\n"
"    QLineEdit:focus {\n"
"        border: 1px solid #2980b9;\n"
"    }\n"
"    QPushButton {\n"
"        padding: 10px 15px;\n"
"        border: none;\n"
"        border-radius: 8px;\n"
"        background-color: #2980b9;\n"
"        color: white;\n"
"        font-weight: bold;\n"
"    }\n"
"    QPushButton:hover {\n"
"        background-color: #3498db;\n"
"    }\n"
"    QPushButton:pressed {\n"
"        background-color: #2471a3;\n"
"    }\n"
"   ")
        self.verticalLayout = QVBoxLayout(LoginDialog)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(40, 40, 40, 40)
        self.titleLabel = QLabel(LoginDialog)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)

        self.verticalLayout.addWidget(self.titleLabel)

        self.userLineEdit = QLineEdit(LoginDialog)
        self.userLineEdit.setObjectName(u"userLineEdit")

        self.verticalLayout.addWidget(self.userLineEdit)

        self.passLineEdit = QLineEdit(LoginDialog)
        self.passLineEdit.setObjectName(u"passLineEdit")
        self.passLineEdit.setEchoMode(QLineEdit.Password)

        self.verticalLayout.addWidget(self.passLineEdit)

        self.loginButton = QPushButton(LoginDialog)
        self.loginButton.setObjectName(u"loginButton")

        self.verticalLayout.addWidget(self.loginButton)


        self.retranslateUi(LoginDialog)

        QMetaObject.connectSlotsByName(LoginDialog)
    # setupUi

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QCoreApplication.translate("LoginDialog", u"Login", None))
        self.titleLabel.setText(QCoreApplication.translate("LoginDialog", u"Lab Management System", None))
        self.userLineEdit.setPlaceholderText(QCoreApplication.translate("LoginDialog", u"Username", None))
        self.passLineEdit.setPlaceholderText(QCoreApplication.translate("LoginDialog", u"Password", None))
        self.loginButton.setText(QCoreApplication.translate("LoginDialog", u"Login", None))
    # retranslateUi

