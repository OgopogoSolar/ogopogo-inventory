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
        LoginDialog.setMinimumSize(QSize(300, 200))
        self.verticalLayout = QVBoxLayout(LoginDialog)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setContentsMargins(30, 30, 30, 30)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.titleLabel = QLabel(LoginDialog)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.titleLabel.setStyleSheet(u"\n"
"        font-size: 20px;\n"
"        font-weight: bold;\n"
"      ")

        self.verticalLayout.addWidget(self.titleLabel)

        self.userLineEdit = QLineEdit(LoginDialog)
        self.userLineEdit.setObjectName(u"userLineEdit")
        self.userLineEdit.setStyleSheet(u"\n"
"        padding: 8px;\n"
"        border: 1px solid #ccc;\n"
"        border-radius: 8px;\n"
"        font-size: 14px;\n"
"      ")

        self.verticalLayout.addWidget(self.userLineEdit)

        self.passLineEdit = QLineEdit(LoginDialog)
        self.passLineEdit.setObjectName(u"passLineEdit")
        self.passLineEdit.setEchoMode(QLineEdit.Password)
        self.passLineEdit.setStyleSheet(u"\n"
"        padding: 8px;\n"
"        border: 1px solid #ccc;\n"
"        border-radius: 8px;\n"
"        font-size: 14px;\n"
"      ")

        self.verticalLayout.addWidget(self.passLineEdit)

        self.loginButton = QPushButton(LoginDialog)
        self.loginButton.setObjectName(u"loginButton")
        self.loginButton.setStyleSheet(u"\n"
"        padding: 10px;\n"
"        background-color: #3498db;\n"
"        color: white;\n"
"        border: none;\n"
"        border-radius: 8px;\n"
"        font-size: 14px;\n"
"      ")

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

