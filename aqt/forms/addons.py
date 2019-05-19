# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object,unused-import
from anki.lang import _
# Form implementation generated from reading ui file 'designer/addons.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui as QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(577, 379)
        Dialog.setModal(True)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.addonList = QtWidgets.QListWidget(Dialog)
        self.addonList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.addonList.setObjectName("addonList")
        self.verticalLayout_2.addWidget(self.addonList)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.getAddons = QtWidgets.QPushButton(Dialog)
        self.getAddons.setObjectName("getAddons")
        self.verticalLayout.addWidget(self.getAddons)
        self.installFromFile = QtWidgets.QPushButton(Dialog)
        self.installFromFile.setObjectName("installFromFile")
        self.verticalLayout.addWidget(self.installFromFile)
        self.checkForUpdates = QtWidgets.QPushButton(Dialog)
        self.checkForUpdates.setObjectName("checkForUpdates")
        self.verticalLayout.addWidget(self.checkForUpdates)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.viewPage = QtWidgets.QPushButton(Dialog)
        self.viewPage.setObjectName("viewPage")
        self.verticalLayout.addWidget(self.viewPage)
        self.viewFiles = QtWidgets.QPushButton(Dialog)
        self.viewFiles.setObjectName("viewFiles")
        self.verticalLayout.addWidget(self.viewFiles)
        self.delete_2 = QtWidgets.QPushButton(Dialog)
        self.delete_2.setObjectName("delete_2")
        self.verticalLayout.addWidget(self.delete_2)
        self.toggleEnabled = QtWidgets.QPushButton(Dialog)
        self.toggleEnabled.setObjectName("toggleEnabled")
        self.verticalLayout.addWidget(self.toggleEnabled)
        self.config = QtWidgets.QPushButton(Dialog)
        self.config.setObjectName("config")
        self.verticalLayout.addWidget(self.config)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_("Add-ons Configuration"))
        self.label.setText(_("Changes will take effect when Anki is restarted."))
        self.getAddons.setText(_("Get Add-ons..."))
        self.installFromFile.setText(_("Install from file..."))
        self.checkForUpdates.setText(_("Check for Updates"))
        self.viewPage.setText(_("View Add-on Page"))
        self.config.setText(_("Config"))
        self.viewFiles.setText(_("View Files"))
        self.toggleEnabled.setText(_("Toggle Enabled"))
        self.delete_2.setText(_("Delete"))

