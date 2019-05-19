# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/profiles.ui'
#
# Created: Thu Dec 22 13:02:41 2016
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from anki.lang import _

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(352, 283)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/anki.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayout_3 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_3.addWidget(self.label_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.profiles = QtGui.QListWidget(Dialog)
        self.profiles.setObjectName(_fromUtf8("profiles"))
        self.verticalLayout_2.addWidget(self.profiles)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.login = QtGui.QPushButton(Dialog)
        self.login.setObjectName(_fromUtf8("login"))
        self.verticalLayout.addWidget(self.login)
        self.add = QtGui.QPushButton(Dialog)
        self.add.setObjectName(_fromUtf8("add"))
        self.verticalLayout.addWidget(self.add)
        self.rename = QtGui.QPushButton(Dialog)
        self.rename.setObjectName(_fromUtf8("rename"))
        self.verticalLayout.addWidget(self.rename)
        self.delete_2 = QtGui.QPushButton(Dialog)
        self.delete_2.setObjectName(_fromUtf8("delete_2"))
        self.verticalLayout.addWidget(self.delete_2)
        self.quit = QtGui.QPushButton(Dialog)
        self.quit.setObjectName(_fromUtf8("quit"))
        self.verticalLayout.addWidget(self.quit)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.login, self.add)
        Dialog.setTabOrder(self.add, self.rename)
        Dialog.setTabOrder(self.rename, self.delete_2)
        Dialog.setTabOrder(self.delete_2, self.quit)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("Profiles"))
        self.label_2.setText(_("Profile:"))
        self.login.setText(_("Open"))
        self.add.setText(_("Add"))
        self.rename.setText(_("Rename"))
        self.delete_2.setText(_("Delete"))
        self.quit.setText(_("Quit"))

from . import icons_rc
