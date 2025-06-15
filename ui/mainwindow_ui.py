# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QLineEdit, QMainWindow, QMenuBar,
    QSizePolicy, QStackedWidget, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(720, 540)
        self.actionInventory = QAction(MainWindow)
        self.actionInventory.setObjectName(u"actionInventory")
        self.actionEmployees = QAction(MainWindow)
        self.actionEmployees.setObjectName(u"actionEmployees")
        self.actionShowDBConfig = QAction(MainWindow)
        self.actionShowDBConfig.setObjectName(u"actionShowDBConfig")
        self.actionShowLabelEditor = QAction(MainWindow)
        self.actionShowLabelEditor.setObjectName(u"actionShowLabelEditor")
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 720, 23))
        MainWindow.setMenuBar(self.menubar)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.inventoryPage = QWidget()
        self.inventoryPage.setObjectName(u"inventoryPage")
        self.stackedWidget.addWidget(self.inventoryPage)
        self.employeesPage = QWidget()
        self.employeesPage.setObjectName(u"employeesPage")
        self.stackedWidget.addWidget(self.employeesPage)
        self.dbconfigPage = QWidget()
        self.dbconfigPage.setObjectName(u"dbconfigPage")
        self.stackedWidget.addWidget(self.dbconfigPage)
        self.labelEditorPage = QWidget()
        self.labelEditorPage.setObjectName(u"labelEditorPage")
        self.stackedWidget.addWidget(self.labelEditorPage)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.barcodeLineEdit = QLineEdit(self.centralwidget)
        self.barcodeLineEdit.setObjectName(u"barcodeLineEdit")
        self.barcodeLineEdit.setVisible(False)

        self.verticalLayout.addWidget(self.barcodeLineEdit)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.actionInventory)
        self.menubar.addAction(self.actionEmployees)
        self.menubar.addAction(self.actionShowDBConfig)
        self.menubar.addAction(self.actionShowLabelEditor)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Lab Management System", None))
        self.actionInventory.setText(QCoreApplication.translate("MainWindow", u"Inventory", None))
        self.actionEmployees.setText(QCoreApplication.translate("MainWindow", u"Employees", None))
        self.actionShowDBConfig.setText(QCoreApplication.translate("MainWindow", u"DB Config", None))
        self.actionShowLabelEditor.setText(QCoreApplication.translate("MainWindow", u"Label Editor", None))
    # retranslateUi

