# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object,unused-import
from anki.lang import _
# Form implementation generated from reading ui file 'designer/about.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui as QtWidgets

class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(410, 664)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(About.sizePolicy().hasHeightForWidth())
        About.setSizePolicy(sizePolicy)
        self.vboxlayout = QtWidgets.QVBoxLayout(About)
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout.setObjectName("vboxlayout")
        self.label = AnkiWebView(About)
        self.label.setProperty("url", QtCore.QUrl("about:blank"))
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)
        self.buttonBox = QtWidgets.QDialogButtonBox(About)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(About)
        self.buttonBox.accepted.connect(About.accept)
        self.buttonBox.rejected.connect(About.reject)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_("About Anki"))

from aqt.webview import AnkiWebView
from . import icons_rc
