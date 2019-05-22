# -*- coding: utf-8 -*-

# This file has been modified by lovac42 for CCBC, and may not be the same as the original.

"""
Anki Add-on: Advanced Copy Fields for version 2.1.x

Updated May 3, 2019

Replace, copy or swap field content from among field(s) to
another field, batch processing several notes at a time.

Copyright: (c) Ambriel Angel 2019 (http://www.ambrielnet.com)
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
import string,re,uuid
from aqt.qt import *
from aqt.utils import tooltip, askUser
from anki.hooks import addHook
from PyQt4 import QtCore, QtGui as QtWidgets
from PyQt4 import QtGui


class CAdvCopy(object):
    """
    Generates a universally unique ID. args make it more random,
    if used.
    """
    fieldlist = {'xxx': 999}
    template = ""
    
    def __init__(self,fieldlist,template):
        #clear out the uuid array. this just sets up a ready array
        self.fieldlist.clear()
        ##self.template = template.decode('utf-8')
        self.template = template
        #Generate uuid for each field name in record
        for field in fieldlist:
            u = uuid.uuid4()
            suuid = str(u.hex)
            self.fieldlist[field] = suuid

    def _get_uuid(self,field_name):
        try:
            return self.fieldlist[field_name]
        except IndexError:
            return ""

    def _get_name(self,uuid_str):
        for key,value in self.fieldlist:
            if value == uuid_str:
                return key
        return ""

    def process(self,record):
        result = "";

        #step 1, replace {{field}} with {{uuid}}
        #this extra steps prevents field values posing a possible issue when converting templates
        result = self.template #should already be utf-8

        for key,value in self.fieldlist.items():
            result = result.replace("{{"+key+"}}",self._get_uuid(key))
                    
        #step 2, replace {{uuid}} with value
        for (key,value) in list(record.items()):
            if key in self.fieldlist:
                suuid_tag = self._get_uuid(key)
                result = result.replace(suuid_tag,value)
                     
        return result


class UAdvancedCopy(QDialog):
    """
    Allows copying/replacing/swapping of fields to another field, in bulk.
    """
    oldtemplate = ""

    #Browser batch editing dialog
    def __init__(self, browser, nids):
        QDialog.__init__(self, parent=browser)
        self.browser = browser
        self.nids = nids
        self._setupUi()

    def _setupUi(self):
        #------------------------------------------------------
        fields = self._getFields()
        AdvancedCopy = self
        #======================================================
        # Form Layout
        #======================================================
        AdvancedCopy.setObjectName("AdvancedCopy")
        AdvancedCopy.resize(330, 195)
        AdvancedCopy.setMinimumSize(QtCore.QSize(330, 195))
        AdvancedCopy.setSizeGripEnabled(False)
        self.vMainLayout = QtWidgets.QVBoxLayout(AdvancedCopy)
        self.vMainLayout.setObjectName("vMainLayout")
        #======================================================
        # Action/Source/Destination widget
        #======================================================
        self.widgetPrimaryCtrls = QtWidgets.QWidget(AdvancedCopy)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widgetPrimaryCtrls.sizePolicy().hasHeightForWidth())
        self.widgetPrimaryCtrls.setSizePolicy(sizePolicy)
        self.widgetPrimaryCtrls.setMaximumSize(QtCore.QSize(640, 16777215))
        self.widgetPrimaryCtrls.setObjectName("widgetPrimaryCtrls")
        self.vlWidgetSource = QtWidgets.QVBoxLayout(self.widgetPrimaryCtrls)
        self.vlWidgetSource.setContentsMargins(0, 0, 0, 0)
        self.vlWidgetSource.setObjectName("vlWidgetSource")
        #======================================================
        # Action Widget
        #======================================================
        self.hlAction = QtWidgets.QHBoxLayout()
        self.hlAction.setObjectName("hlAction")
        self.lblAction = QtWidgets.QLabel(self.widgetPrimaryCtrls)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblAction.sizePolicy().hasHeightForWidth())
        #Setup label
        self.lblAction.setSizePolicy(sizePolicy)
        self.lblAction.setMinimumSize(QtCore.QSize(100, 0))
        self.lblAction.setMaximumSize(QtCore.QSize(150, 16777215))
        self.lblAction.setBaseSize(QtCore.QSize(100, 0))
        self.lblAction.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.lblAction.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblAction.setObjectName("lblAction")
        self.hlAction.addWidget(self.lblAction)
        #Setup combobox
        self.cmbAction = QtWidgets.QComboBox(self.widgetPrimaryCtrls)
        self.cmbAction.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbAction.sizePolicy().hasHeightForWidth())
        self.cmbAction.setSizePolicy(sizePolicy)
        self.cmbAction.setMinimumSize(QtCore.QSize(150, 26))
        self.cmbAction.setMaximumSize(QtCore.QSize(250, 16777215))
        self.cmbAction.setBaseSize(QtCore.QSize(160, 0))
        self.cmbAction.setObjectName("cmbAction")
        self.cmbAction.addItem("") #0 Replace
        self.cmbAction.addItem("") #1 After
        self.cmbAction.addItem("") #2 Before
        self.cmbAction.addItem("") #3 Move
        self.cmbAction.addItem("") #4 Swap
        self.cmbAction.addItem("") #5 Custom
        self.hlAction.addWidget(self.cmbAction)
        spacerItem = QtWidgets.QSpacerItem(175, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hlAction.addItem(spacerItem)
        self.vlWidgetSource.addLayout(self.hlAction)
        #======================================================
        # Source Widget
        #======================================================
        self.hlSource = QtWidgets.QHBoxLayout()
        self.hlSource.setObjectName("hlSource")
        self.lblSource = QtWidgets.QLabel(self.widgetPrimaryCtrls)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblSource.sizePolicy().hasHeightForWidth())
        #Setup label
        self.lblSource.setSizePolicy(sizePolicy)
        self.lblSource.setMinimumSize(QtCore.QSize(100, 0))
        self.lblSource.setMaximumSize(QtCore.QSize(150, 16777215))
        self.lblSource.setBaseSize(QtCore.QSize(100, 0))
        self.lblSource.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.lblSource.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblSource.setObjectName("lblSource")
        self.hlSource.addWidget(self.lblSource)
        #Set up combobox
        self.cmbSource = QtWidgets.QComboBox(self.widgetPrimaryCtrls)
        self.cmbSource.setEnabled(True)
        sizePolicySD = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        sizePolicySD.setHorizontalStretch(0)
        sizePolicySD.setVerticalStretch(0)
        sizePolicySD.setHeightForWidth(self.cmbSource.sizePolicy().hasHeightForWidth())
        self.cmbSource.setSizePolicy(sizePolicySD)
        self.cmbSource.setMinimumSize(QtCore.QSize(200, 26))
        self.cmbSource.setMaximumSize(QtCore.QSize(250, 16777215))
        self.cmbSource.setBaseSize(QtCore.QSize(200, 26))
        self.cmbSource.setObjectName("cmbSource")
        #------------------------------------------------------
        self.cmbSource.addItems(fields)
        #------------------------------------------------------
        self.hlSource.addWidget(self.cmbSource)
        #Setup Insert button
        self.btnInsert = QtWidgets.QPushButton(self.widgetPrimaryCtrls)
        self.btnInsert.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnInsert.sizePolicy().hasHeightForWidth())
        self.btnInsert.setSizePolicy(sizePolicy)
        self.btnInsert.setMaximumSize(QtCore.QSize(50, 16777215)) #HELLO THERE (w, h)
        self.btnInsert.setMinimumSize(QtCore.QSize(50, 0))
        self.btnInsert.setFlat(False)
        self.btnInsert.setObjectName("btnInsert")
        self.hlSource.addWidget(self.btnInsert)

        spacerItem_cmbSource = QtWidgets.QSpacerItem(50, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hlSource.addItem(spacerItem_cmbSource)
        self.vlWidgetSource.addLayout(self.hlSource)
        #======================================================
        # Destination Widget
        #======================================================
        self.hlDestinaton = QtWidgets.QHBoxLayout()
        self.hlDestinaton.setObjectName("hlDestinaton")
        self.lblDestination = QtWidgets.QLabel(self.widgetPrimaryCtrls)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDestination.sizePolicy().hasHeightForWidth())
        #Setup label
        self.lblDestination.setSizePolicy(sizePolicy)
        self.lblDestination.setMinimumSize(QtCore.QSize(100, 0))
        self.lblDestination.setMaximumSize(QtCore.QSize(150, 16777215))
        self.lblDestination.setBaseSize(QtCore.QSize(100, 0))
        self.lblDestination.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.lblDestination.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblDestination.setObjectName("lblDestination")
        self.hlDestinaton.addWidget(self.lblDestination)
        # Set up combobox
        self.cmbDestination = QtWidgets.QComboBox(self.widgetPrimaryCtrls)
        self.cmbDestination.setSizePolicy(sizePolicySD)
        self.cmbDestination.setMinimumSize(QtCore.QSize(200, 0))
        self.cmbDestination.setMaximumSize(QtCore.QSize(250, 16777215))
        self.cmbDestination.setBaseSize(QtCore.QSize(200, 26))
        #self.cmbDestination.setBaseSize(QtCore.QSize(150, 26))
        self.cmbDestination.setObjectName("cmbDestination")
        #------------------------------------------------------
        self.cmbDestination.addItems(fields)
        #------------------------------------------------------
        self.hlDestinaton.addWidget(self.cmbDestination)
        spacerItem1 = QtWidgets.QSpacerItem(50, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum) #HELLO HERE
        self.hlDestinaton.addItem(spacerItem1)
        self.vlWidgetSource.addLayout(self.hlDestinaton)
        #------------------------------------------------------
        # END Action/Source/Destination widget:
        #------------------------------------------------------
        self.vMainLayout.addWidget(self.widgetPrimaryCtrls)
        #======================================================
        # 'Custom' Widget
        #======================================================
        self.groupTemplate = QtWidgets.QGroupBox(AdvancedCopy)
        self.groupTemplate.setObjectName("groupTemplate")
        self.vlGroupTemplate = QtWidgets.QVBoxLayout(self.groupTemplate)
        self.vlGroupTemplate.setObjectName("vlGroupTemplate")
        self.txtCustom = QtWidgets.QPlainTextEdit(self.groupTemplate)
        self.txtCustom.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtCustom.sizePolicy().hasHeightForWidth())
        self.txtCustom.setSizePolicy(sizePolicy)
        self.txtCustom.setMinimumSize(QtCore.QSize(0, 45))
        self.txtCustom.setSizeIncrement(QtCore.QSize(0, 0))
        self.txtCustom.setBaseSize(QtCore.QSize(0, 50))
        self.txtCustom.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.txtCustom.setFrameShadow(QtWidgets.QFrame.Plain)
        self.txtCustom.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.txtCustom.setPlainText("")
        self.txtCustom.setObjectName("txtCustom")
        self.vlGroupTemplate.addWidget(self.txtCustom)
        self.vMainLayout.addWidget(self.groupTemplate)
        #======================================================
        # Main Buttons Widget
        #======================================================
        self.widgetMainButtons = QtWidgets.QWidget(AdvancedCopy)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widgetMainButtons.sizePolicy().hasHeightForWidth())
        self.widgetMainButtons.setSizePolicy(sizePolicy)
        self.widgetMainButtons.setMinimumSize(QtCore.QSize(250, 0))
        self.widgetMainButtons.setMaximumSize(QtCore.QSize(0, 60))
        self.widgetMainButtons.setObjectName("widgetMainButtons")
        self.vlWidgetMainButtons = QtWidgets.QVBoxLayout(self.widgetMainButtons)
        self.vlWidgetMainButtons.setContentsMargins(0, 0, 0, 0)
        self.vlWidgetMainButtons.setObjectName("vlWidgetMainButtons")
        self.hlMainButtons = QtWidgets.QHBoxLayout()
        self.hlMainButtons.setObjectName("hlMainButtons")

        # Cancel Button setup
        self.btnCancel = QtWidgets.QPushButton(self.widgetMainButtons)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnCancel.sizePolicy().hasHeightForWidth())
        self.btnCancel.setSizePolicy(sizePolicy)
        self.btnCancel.setMinimumSize(QtCore.QSize(0, 32))
        self.btnCancel.setMaximumSize(QtCore.QSize(16777215, 40))
        self.btnCancel.setObjectName("btnCancel")
        self.hlMainButtons.addWidget(self.btnCancel)

        # OK Button setup
        self.btnOK = QtWidgets.QPushButton(self.widgetMainButtons)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnOK.sizePolicy().hasHeightForWidth())
        self.btnOK.setSizePolicy(sizePolicy)
        self.btnOK.setMinimumSize(QtCore.QSize(0, 32))
        self.btnOK.setMaximumSize(QtCore.QSize(16777215, 40))
        self.btnOK.setObjectName("btnOK")
        self.hlMainButtons.addWidget(self.btnOK)

        # Add OK and Cancel Buttons to parent group/widget
        self.vlWidgetMainButtons.addLayout(self.hlMainButtons)
        self.vMainLayout.addWidget(self.widgetMainButtons)
        #------------------------------------------------------
        self._retranslateUi()
        #------------------------------------------------------
        QtCore.QMetaObject.connectSlotsByName(AdvancedCopy)
        #======================================================
        # Setup/Process form
        #======================================================
        self.cmbAction.currentIndexChanged.connect(self.onActionIndexChange)
        self.cmbSource.currentIndexChanged.connect(self.onSourceIndexChange)
        self.cmbDestination.currentIndexChanged.connect(self.onDestinationIndexChange)
        self.btnInsert.clicked.connect(self.onInsert)
        #------------------------------------------------------
        self.onCustom()
        self._processTemplate("<br>")
        #------------------------------------------------------
        if self.cmbDestination.count() > 1:
            self.cmbDestination.setCurrentIndex(1)
        #------------------------------------------------------
        self.btnOK.clicked.connect(self.onConfirm)
        self.btnCancel.clicked.connect(self.close)
        #------------------------------------------------------


    def _retranslateUi(self):
        AdvancedCopy = self
        AdvancedCopy.setWindowTitle(QtCore.QCoreApplication.translate("AdvancedCopy", "Advanced Copy Fields", None))
        self.lblAction.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Action:", None))
        self.cmbAction.setItemText(0, QtCore.QCoreApplication.translate("AdvancedCopy", "Replace", None))
        self.cmbAction.setItemText(1, QtCore.QCoreApplication.translate("AdvancedCopy", "Copy After", None))
        self.cmbAction.setItemText(2, QtCore.QCoreApplication.translate("AdvancedCopy", "Copy Before", None))
        self.cmbAction.setItemText(3, QtCore.QCoreApplication.translate("AdvancedCopy", "Move", None))
        self.cmbAction.setItemText(4, QtCore.QCoreApplication.translate("AdvancedCopy", "Swap", None))
        self.cmbAction.setItemText(5, QtCore.QCoreApplication.translate("AdvancedCopy", "Custom", None))
        self.btnInsert.setText(QtCore.QCoreApplication.translate("AdvancedCopy", ">>", None))
        self.groupTemplate.setTitle(QtCore.QCoreApplication.translate("AdvancedCopy", "Template:", None))
        self.btnCancel.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Cancel", None))
        self.btnOK.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "OK", None))

        idx = self.cmbAction.currentIndex()

        if idx == 0:   # If Replace
            self.lblSource.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Source Field:", None))
            self.lblDestination.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Replace:", None))
        elif idx == 1: # Copy After_get_name
            self.lblSource.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Copy Field:", None))
            self.lblDestination.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "After:", None))
        elif idx == 2: # Copy Before
            self.lblSource.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Copy Field:", None))
            self.lblDestination.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Before:", None))
        elif idx == 3: # Move
            self.lblSource.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Move Field:", None))
            self.lblDestination.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "To:", None))
        elif idx == 4: # Swap
            self.lblSource.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Swap Field:", None))
            self.lblDestination.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "With:", None))
        elif idx == 5: # Custom
            self.lblSource.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Insert:", None))
            self.lblDestination.setText(QtCore.QCoreApplication.translate("AdvancedCopy", "Destination:", None))
        #------------------------------------------------------

    def _processTemplate(self,spacer):
        idx = self.cmbAction.currentIndex()
        fldSource =  self.cmbSource.currentText()
        fld2 = self.cmbDestination.currentText() #itemText(idx), currentText, currentIndex
        if idx != 5:
            #current_template = self.txtCustom.toPlainText()
            new_template = self._getTemplate(idx, fldSource, fld2, spacer)
            self.txtCustom.setPlainText( new_template )

    def _getFields(self):
        nid = self.nids[0]
        mw = self.browser.mw
        model = mw.col.getNote(nid).model()
        fields = mw.col.models.fieldNames(model)
        return fields

    def _getTemplate(self,idx, fldSource, fld2, spacer):
        if idx == 1: #Copy After
            return "{{" + fld2 + "}}" + spacer + "{{" + fldSource + "}}"
        elif idx == 2: #Copy Before
            return "{{" + fldSource + "}}" + spacer + "{{" + fld2 + "}}"
        else: #Default is Replace (0), Move (3), Swap (4), Custom (5)
            return "{{" + fldSource + "}}"

    def onInsert(self):
        cursor = self.txtCustom.textCursor()
        cursor.insertText("{{" + self.cmbSource.currentText() +  "}}")

    def onCustom(self):
        isCustom =  self.cmbAction.currentText() == "Custom"
        if not isCustom:
            self.setMinimumSize(QtCore.QSize(350, 190))
            self.setMaximumSize(QtCore.QSize(350, 250))
            self.btnInsert.hide()
            self.txtCustom.hide()
            self.groupTemplate.hide()
            #-------------------------------------
            self.txtCustom.setDisabled(True)
            self.btnInsert.setDisabled(True)
        else:
            #-------------------------------------
            self.btnInsert.show()
            self.txtCustom.show()
            self.groupTemplate.show()
            #-------------------------------------
            self.txtCustom.setEnabled(True)
            self.btnInsert.setEnabled(True)
            self.txtCustom.setFocus()
            cursor = self.txtCustom.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.txtCustom.setTextCursor(cursor)
            self.setMinimumSize(QtCore.QSize(390, 350))
            self.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self._retranslateUi()
        return isCustom

    def onSourceIndexChange(self,idx):
        self._processTemplate("<br>")

    def onDestinationIndexChange(self,idx):
        self._processTemplate("<br>")

    def onActionIndexChange(self,idx):
        self.onCustom()
        self._processTemplate("<br>")

    def onConfirm(self):
        browser = self.browser
        nids = self.nids
        idx = self.cmbAction.currentIndex()
        fld1 = self.cmbSource.currentText()
        fld2 = self.cmbDestination.currentText()

        if idx == 0:   # If Replace
            q = ("The contents of the field '{1}' will be replaced. The field '{0}' will replace it in {2} selected note(s).<br><br>Is this okay?").format(fld1, fld2, len(nids))
        elif idx == 1: # Copy After
            q = ("The contents of the field '{1}' will change. The field '{0}' will be appended to it in {2} selected note(s).<br><br>Is this okay?").format(fld1, fld2, len(nids))
        elif idx == 2: # Copy Before
            q = ("The contents of the field '{1}' will change. The field '{0}' will be prepended to it in {2} selected note(s).<br><br>Is this okay?").format(fld1, fld2, len(nids))
        elif idx == 3: # Move
            q = ("The contents of the field '{0}' will move to field '{1}'. This will replace out field '{1}' but also empty out field '{0}' in {2} selected note(s).<br><br>Is this okay?").format(fld1, fld2, len(nids))
        elif idx == 4: # Swap
            if fld1 == fld2:
                QMessageBox.warning(self, "Swap Error", ("You must select two different fields in order to swap them. You selected '{0}' in both boxes.").format(fld1))
                return
            q = ("The contents of the fields '{0}' and '{1}' will be swapped. The contents of '{0}' will become '{1}' and '{1}' will become '{0}', in {2} selected note(s).<br><br>Is this okay?").format(fld1, fld2, len(nids))
        elif idx == 5: # Custom
            q = ("The contents of the field '{1}' will be replaced with the processed contents of the custom template in {2} selected note(s).<br><br>Is this okay?").format(fld1, fld2, len(nids))
        #if idx between 0 and 4
        if 0 <= idx <= 5:
            if not askUser(q, parent=self):
                return

        template = self.txtCustom.toPlainText()
        flds = self._getFields()
        processIt( browser,idx,nids,flds,fld1,fld2,template )
        self.close()


def processIt(browser, idx, nids, flds, fld1, fld2, template):
    mw = browser.mw
    mw.checkpoint("AdvancedCopy")
    mw.progress.start()
    browser.model.beginReset()
    cnt = 0

    #If custom template:
    if idx == 5:
        AdvCopy = CAdvCopy(flds,template)

    for nid in nids:
        note = mw.col.getNote(nid)
        #if 0 not in (self.a, self.b) :
        if (fld1 in note) and (fld2 in note):
            if idx == 0: #Replace
                note[fld2] = note[fld1]
            elif idx == 1: #Copy After
                note[fld2] += "<br/>" + note[fld1]
            elif idx == 2: #Copy Before
                note[fld2] = note[fld1] + "<br/>" + note[fld2]
            elif idx == 3: #Move
                note[fld2] = note[fld1]
                note[fld1] = ""
            elif idx == 4: #Swap
                swap = note[fld2]
                note[fld2] = note[fld1]
                note[fld1] = swap
            elif idx == 5: #Custom
                note[fld2] = AdvCopy.process(note)

            cnt += 1
            note.flush()

    browser.model.endReset()
    mw.requireReset()
    mw.progress.finish()
    mw.reset()
    #self.cleanup()
    tooltip("Processed {0} notes.".format(cnt), parent=browser)

def onAdvCopyEdit(browser):
    nids = browser.selectedNotes()
    if not nids:
        tooltip("No cards selected.")
        return
    dialog = UAdvancedCopy(browser, nids)
    dialog.exec_()

def setupMenu(browser):
    menu = browser.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Advanced Copy...')
    a.setShortcut(QKeySequence("Ctrl+Alt+C"))
    a.triggered.connect(lambda _, b=browser: onAdvCopyEdit(b))


addHook("browser.setupMenus", setupMenu)
