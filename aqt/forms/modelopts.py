# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object,unused-import
from anki.lang import _
# Form implementation generated from reading ui file 'designer/modelopts.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui as QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(374, 344)
        Dialog.setWindowTitle("")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.qtabwidget = QtWidgets.QTabWidget(Dialog)
        self.qtabwidget.setObjectName("qtabwidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab)
        self.label_6 = QtWidgets.QLabel(self.tab)
        self.label_6.setObjectName("label_6")
        self.verticalLayout.addWidget(self.label_6)
        self.latexHeader = QtWidgets.QTextEdit(self.tab)
        self.latexHeader.setTabChangesFocus(True)
        self.latexHeader.setObjectName("latexHeader")
        self.verticalLayout.addWidget(self.latexHeader)
        self.label_7 = QtWidgets.QLabel(self.tab)
        self.label_7.setObjectName("label_7")
        self.verticalLayout.addWidget(self.label_7)
        self.latexFooter = QtWidgets.QTextEdit(self.tab)
        self.latexFooter.setTabChangesFocus(True)
        self.latexFooter.setObjectName("latexFooter")
        self.verticalLayout.addWidget(self.latexFooter)
        self.qtabwidget.addTab(self.tab, "")
        self.verticalLayout_2.addWidget(self.qtabwidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.qtabwidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.qtabwidget, self.buttonBox)
        Dialog.setTabOrder(self.buttonBox, self.latexHeader)
        Dialog.setTabOrder(self.latexHeader, self.latexFooter)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        self.label_6.setText(_("Header"))
        self.label_7.setText(_("Footer"))
        self.qtabwidget.setTabText(self.qtabwidget.indexOf(self.tab), _("LaTeX"))

