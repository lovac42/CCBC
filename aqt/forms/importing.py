# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object,unused-import
from anki.lang import _
# Form implementation generated from reading ui file 'designer/importing.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui as QtWidgets
from aqt.tagedit import TagEdit

class Ui_ImportDialog(object):
    def setupUi(self, ImportDialog):
        ImportDialog.setObjectName("ImportDialog")
        ImportDialog.resize(553, 466)
        self.vboxlayout = QtWidgets.QVBoxLayout(ImportDialog)
        self.vboxlayout.setObjectName("vboxlayout")
        self.groupBox = QtWidgets.QGroupBox(ImportDialog)
        self.groupBox.setObjectName("groupBox")
        self.toplayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.toplayout.setObjectName("toplayout")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.deckArea = QtWidgets.QWidget(self.groupBox)
        self.deckArea.setObjectName("deckArea")
        self.gridLayout_2.addWidget(self.deckArea, 0, 3, 1, 1)
        self.modelArea = QtWidgets.QWidget(self.groupBox)
        self.modelArea.setObjectName("modelArea")
        self.gridLayout_2.addWidget(self.modelArea, 0, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 0, 2, 1, 1)
        self.toplayout.addLayout(self.gridLayout_2)
        self.autoDetect = QtWidgets.QPushButton(self.groupBox)
        self.autoDetect.setText("")
        self.autoDetect.setObjectName("autoDetect")
        self.toplayout.addWidget(self.autoDetect)
        self.importMode = QtWidgets.QComboBox(self.groupBox)
        self.importMode.setObjectName("importMode")
        self.importMode.addItem("")
        self.importMode.addItem("")
        self.importMode.addItem("")

        self.toplayout.addWidget(self.importMode)
        self.allowHTML = QtWidgets.QCheckBox(self.groupBox)
        self.allowHTML.setObjectName("allowHTML")
        self.toplayout.addWidget(self.allowHTML)

        self.tagModifiedLayout = QtWidgets.QHBoxLayout(self.groupBox)
        self.tagModifiedLabel = QtWidgets.QLabel(self.groupBox)
        self.tagModifiedLabel.setObjectName("tagModifiedLabel")
        self.tagModifiedLayout.addWidget(self.tagModifiedLabel)
        self.tagModified = TagEdit(self.groupBox)
        self.tagModified.setObjectName("tagModified")
        self.tagModifiedLayout.addWidget(self.tagModified)
        self.toplayout.addLayout(self.tagModifiedLayout)
        self.vboxlayout.addWidget(self.groupBox)

        self.mappingGroup = QtWidgets.QGroupBox(ImportDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mappingGroup.sizePolicy().hasHeightForWidth())
        self.mappingGroup.setSizePolicy(sizePolicy)
        self.mappingGroup.setObjectName("mappingGroup")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.mappingGroup)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.mappingArea = QtWidgets.QScrollArea(self.mappingGroup)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mappingArea.sizePolicy().hasHeightForWidth())
        self.mappingArea.setSizePolicy(sizePolicy)
        self.mappingArea.setMinimumSize(QtCore.QSize(400, 150))
        self.mappingArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.mappingArea.setWidgetResizable(True)
        self.mappingArea.setObjectName("mappingArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 529, 251))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.mappingArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.mappingArea, 0, 0, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.vboxlayout.addWidget(self.mappingGroup)
        self.buttonBox = QtWidgets.QDialogButtonBox(ImportDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(ImportDialog)
        self.buttonBox.accepted.connect(ImportDialog.accept)
        self.buttonBox.rejected.connect(ImportDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ImportDialog)

    def retranslateUi(self, ImportDialog):
        _translate = QtCore.QCoreApplication.translate
        ImportDialog.setWindowTitle(_("Import"))
        self.groupBox.setTitle(_("Import options"))
        self.label.setText(_("Type"))
        self.label_2.setText(_("Deck"))
        self.importMode.setItemText(0, _("Update existing notes when first field matches"))
        self.importMode.setItemText(1, _("Ignore lines where first field matches existing note"))
        self.importMode.setItemText(2, _("Import even if existing note has same first field"))
        self.allowHTML.setText(_("Allow HTML in fields"))
        self.tagModifiedLabel.setText(_("Tag modified notes:"))
        self.mappingGroup.setTitle(_("Field mapping"))

