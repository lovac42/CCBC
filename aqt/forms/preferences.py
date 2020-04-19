# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object,unused-import
from anki.lang import _
# Form implementation generated from reading ui file 'designer/preferences.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui as QtWidgets
from aqt.sound import getMics

class Ui_Preferences(object):
    def setupUi(self, Preferences):
        Preferences.setObjectName("Preferences")
        Preferences.resize(423, 508)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Preferences)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtWidgets.QTabWidget(Preferences)
        self.tabWidget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.tabWidget.setObjectName("tabWidget")

        #####################################################
        # Basic tab
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab_1)
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.tab_1)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lang = QtWidgets.QComboBox(self.tab_1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lang.sizePolicy().hasHeightForWidth())
        self.lang.setSizePolicy(sizePolicy)
        self.lang.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.lang.setObjectName("lang")
        self.horizontalLayout_2.addWidget(self.lang)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        # self.hwAccel = QtWidgets.QCheckBox(self.tab_1)
        # self.hwAccel.setObjectName("hwAccel")
        # self.verticalLayout.addWidget(self.hwAccel)
        self.showEstimates = QtWidgets.QCheckBox(self.tab_1)
        self.showEstimates.setObjectName("showEstimates")
        self.verticalLayout.addWidget(self.showEstimates)
        self.showProgress = QtWidgets.QCheckBox(self.tab_1)
        self.showProgress.setObjectName("showProgress")
        self.verticalLayout.addWidget(self.showProgress)
        self.pastePNG = QtWidgets.QCheckBox(self.tab_1)
        self.pastePNG.setObjectName("pastePNG")
        self.verticalLayout.addWidget(self.pastePNG)

        # self.nightMode = QtWidgets.QCheckBox(self.tab_1)
        # self.nightMode.setObjectName("nightMode")
        # self.verticalLayout.addWidget(self.nightMode)
        self.dayLearnFirst = QtWidgets.QCheckBox(self.tab_1)
        self.dayLearnFirst.setObjectName("dayLearnFirst")
        self.verticalLayout.addWidget(self.dayLearnFirst)
        self.newSched = QtWidgets.QCheckBox(self.tab_1)
        self.newSched.setObjectName("newSched")
        self.verticalLayout.addWidget(self.newSched)
        self.useCurrent = QtWidgets.QComboBox(self.tab_1)
        self.useCurrent.setObjectName("useCurrent")
        self.useCurrent.addItem("")
        self.useCurrent.addItem("")
        self.verticalLayout.addWidget(self.useCurrent)
        self.newSpread = QtWidgets.QComboBox(self.tab_1)
        self.newSpread.setObjectName("newSpread")
        self.verticalLayout.addWidget(self.newSpread)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setSpacing(12)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label_23 = QtWidgets.QLabel(self.tab_1)
        self.label_23.setObjectName("label_23")
        self.gridLayout_4.addWidget(self.label_23, 0, 0, 1, 1)
        self.dayOffset = QtWidgets.QSpinBox(self.tab_1)
        self.dayOffset.setMaximumSize(QtCore.QSize(60, 16777215))
        self.dayOffset.setMaximum(23)
        self.dayOffset.setObjectName("dayOffset")
        self.gridLayout_4.addWidget(self.dayOffset, 0, 1, 1, 1)
        self.label_24 = QtWidgets.QLabel(self.tab_1)
        self.label_24.setObjectName("label_24")
        self.gridLayout_4.addWidget(self.label_24, 1, 0, 1, 1)
        self.lrnCutoff = QtWidgets.QSpinBox(self.tab_1)
        self.lrnCutoff.setMaximumSize(QtCore.QSize(60, 16777215))
        self.lrnCutoff.setMaximum(999)
        self.lrnCutoff.setObjectName("lrnCutoff")
        self.gridLayout_4.addWidget(self.lrnCutoff, 1, 1, 1, 1)
        self.label_29 = QtWidgets.QLabel(self.tab_1)
        self.label_29.setObjectName("label_29")
        self.gridLayout_4.addWidget(self.label_29, 1, 2, 1, 1)
        self.label_30 = QtWidgets.QLabel(self.tab_1)
        self.label_30.setObjectName("label_30")
        self.gridLayout_4.addWidget(self.label_30, 2, 0, 1, 1)
        self.timeLimit = QtWidgets.QSpinBox(self.tab_1)
        self.timeLimit.setMaximum(9999)
        self.timeLimit.setObjectName("timeLimit")
        self.gridLayout_4.addWidget(self.timeLimit, 2, 1, 1, 1)
        self.label_39 = QtWidgets.QLabel(self.tab_1)
        self.label_39.setObjectName("label_39")
        self.gridLayout_4.addWidget(self.label_39, 2, 2, 1, 1)
        self.label_40 = QtWidgets.QLabel(self.tab_1)
        self.label_40.setObjectName("label_40")
        self.gridLayout_4.addWidget(self.label_40, 0, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_4)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.tabWidget.addTab(self.tab_1, _("Basic"))




        #####################################################
        # Create Advanced Tab
        self.tab_adv=QtWidgets.QWidget()
        self.tab_adv.setObjectName("tab_adv")
        self.advancedVLayout=QtWidgets.QVBoxLayout(self.tab_adv)
        self.advancedVLayout.addLayout(QtWidgets.QGridLayout())

        # Grading button configs
        gbLayout=QtWidgets.QVBoxLayout()
        hLayout=QtWidgets.QHBoxLayout()
        # ans keys
        hLayout.addWidget(QtWidgets.QLabel(_("Answer keys:")))
        self.ansKeysLEdit = QtWidgets.QLineEdit(self.tab_adv)
        self.ansKeysLEdit.setObjectName("ansKeysLEdit")
        hLayout.addWidget(self.ansKeysLEdit)
        gbLayout.addLayout(hLayout)
        # button action
        hLayout=QtWidgets.QHBoxLayout()
        hLayout.addWidget(QtWidgets.QLabel(
            _("Action on quesiton side:")))
        self.ansKeyActNothing = QtWidgets.QRadioButton(self.tab_adv)
        self.ansKeyActNothing.setObjectName("ansKeyActNothing")
        self.ansKeyActNothing.setChecked(True)
        hLayout.addWidget(self.ansKeyActNothing)
        self.ansKeyActFlip = QtWidgets.QRadioButton(self.tab_adv)
        self.ansKeyActFlip.setObjectName("ansKeyActFlip")
        hLayout.addWidget(self.ansKeyActFlip)
        self.ansKeyActGrade = QtWidgets.QRadioButton(self.tab_adv)
        self.ansKeyActGrade.setObjectName("ansKeyActGrade")
        self.ansKeyActGrade.setSizePolicy(sizePolicy)
        hLayout.addWidget(self.ansKeyActGrade)
        gbLayout.addLayout(hLayout)

        hLayout=QtWidgets.QHBoxLayout()
        # colorize review buttons
        self.colorGradeBtns = QtWidgets.QCheckBox(self.tab_adv)
        self.colorGradeBtns.setObjectName("colorGradeBtns")
        hLayout.addWidget(self.colorGradeBtns)
        # large review buttons
        self.bigGradeBtns = QtWidgets.QCheckBox(self.tab_adv)
        self.bigGradeBtns.setObjectName("bigGradeBtns")
        self.bigGradeBtns.setSizePolicy(sizePolicy)
        hLayout.addWidget(self.bigGradeBtns)
        gbLayout.addLayout(hLayout)

        groupBox = QtWidgets.QGroupBox('Grade Buttons')
        groupBox.setLayout(gbLayout)
        self.advancedVLayout.addWidget(groupBox)

        self.advancedVLayout.addItem(
            QtWidgets.QSpacerItem(10,10,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Fixed
        ))

        # formatting buttons for editor
        self.showFormatBtns = QtWidgets.QCheckBox(self.tab_adv)
        self.showFormatBtns.setObjectName("showFormatBtns")
        self.advancedVLayout.addWidget(self.showFormatBtns)
        # autoCompleter feature for addCard
        self.autoCompleter = QtWidgets.QCheckBox(self.tab_adv)
        self.autoCompleter.setObjectName("autoCompleter")
        self.advancedVLayout.addWidget(self.autoCompleter)

        # powerUser Mode
        self.powerUserMode = QtWidgets.QCheckBox(self.tab_adv)
        self.powerUserMode.setObjectName("powerUserMode")
        self.advancedVLayout.addWidget(self.powerUserMode)

        self.advancedVLayout.addItem(
            QtWidgets.QSpacerItem(5,5,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Fixed
        ))

        # For localizing media
        self.importMedia = QtWidgets.QCheckBox(self.tab_adv)
        self.importMedia.setObjectName("importMedia")
        self.advancedVLayout.addWidget(self.importMedia)
        # For TidyTags to clean up when editing HTML
        self.noScript = QtWidgets.QCheckBox(self.tab_adv)
        self.noScript.setObjectName("noScript")
        self.advancedVLayout.addWidget(self.noScript)

        # spacer to push everything up
        spacerItem=QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.advancedVLayout.addItem(spacerItem)


        # External editor group box
        gbLayout=QtWidgets.QGridLayout()
        gbLayout.addWidget(QtWidgets.QLabel('Image:'), 0, 0, 1, 1)
        self.extImgCmdLEdit = QtWidgets.QLineEdit(self.tab_adv)
        self.extImgCmdLEdit.setObjectName("extImgCmdLEdit")

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.extImgCmdLEdit.sizePolicy().hasHeightForWidth())
        self.extImgCmdLEdit.setSizePolicy(sizePolicy)
        gbLayout.addWidget(self.extImgCmdLEdit, 0, 1, 1, 1)

        gbLayout.addWidget(QtWidgets.QLabel('Text:'), 1, 0, 1, 1)
        self.extTxtCmdLEdit = QtWidgets.QLineEdit(self.tab_adv)
        self.extTxtCmdLEdit.setObjectName("extTxtCmdLEdit")
        gbLayout.addWidget(self.extTxtCmdLEdit, 1, 1, 1, 1)

        groupBox = QtWidgets.QGroupBox('External Editor')
        groupBox.setLayout(gbLayout)
        self.advancedVLayout.addWidget(groupBox)
        self.tabWidget.addTab(self.tab_adv, _("Advanced"))


        #####################################################
        # Create Audio Tab
        self.tab_audio=QtWidgets.QWidget()
        self.tab_audio.setObjectName("tab_audio")
        self.audioVLayout=QtWidgets.QVBoxLayout(self.tab_audio)
        self.audioVLayout.addLayout(QtWidgets.QGridLayout())
        # disable autoplay
        self.noAutoPlay = QtWidgets.QCheckBox(self.tab_audio)
        self.noAutoPlay.setObjectName("noAutoPlay")
        self.audioVLayout.addWidget(self.noAutoPlay)
        # mpv direct access to audio files
        self.mpvDA = QtWidgets.QCheckBox(self.tab_audio)
        self.mpvDA.setObjectName("mpvDA")
        self.audioVLayout.addWidget(self.mpvDA)
        # show play btn on card
        self.showAudPlayBtn = QtWidgets.QCheckBox(self.tab_audio)
        self.showAudPlayBtn.setObjectName("showAudPlayBtn")
        self.audioVLayout.addWidget(self.showAudPlayBtn)
        # stop audio on show answer
        self.stpAudOnShwAns = QtWidgets.QCheckBox(self.tab_audio)
        self.stpAudOnShwAns.setObjectName("stpAudOnShwAns")
        self.audioVLayout.addWidget(self.stpAudOnShwAns)
        # spacer to push everything up
        spacerItem=QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.audioVLayout.addItem(spacerItem)


        # microphone group box
        micLayout=QtWidgets.QGridLayout()
        micLayout.addWidget(QtWidgets.QLabel('Device:'), 0, 0, 1, 1)
        self.micDevice = QtWidgets.QComboBox(self.tab_audio)
        self.micDevice.setObjectName("micDevice")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.micDevice.sizePolicy().hasHeightForWidth())
        self.micDevice.setSizePolicy(sizePolicy)
        self.micDevice.addItems(getMics())
        micLayout.addWidget(self.micDevice, 0, 1, 1, 1)
        micLayout.addWidget(QtWidgets.QLabel('Channel:'), 1, 0, 1, 1)
        self.micChannel = QtWidgets.QComboBox(self.tab_audio)
        self.micChannel.setObjectName("micChannel")
        self.micChannel.addItems(["Mono Input","Stereo Input"])
        micLayout.addWidget(self.micChannel, 1, 1, 1, 1)

        groupBox = QtWidgets.QGroupBox('Microphone')
        groupBox.setLayout(micLayout)
        self.audioVLayout.addWidget(groupBox)
        self.tabWidget.addTab(self.tab_audio, _("Audio"))

        #####################################################
        # Network tab
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.tab_2)
        self.verticalLayout_4.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout_4.setSpacing(12)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setSpacing(10)
        self.hboxlayout.setObjectName("hboxlayout")
        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.setObjectName("vboxlayout")
        self.syncLabel = QtWidgets.QLabel(self.tab_2)
        self.syncLabel.setWordWrap(True)
        self.syncLabel.setOpenExternalLinks(True)
        self.syncLabel.setObjectName("syncLabel")
        self.vboxlayout.addWidget(self.syncLabel)
        self.syncMedia = QtWidgets.QCheckBox(self.tab_2)
        self.syncMedia.setObjectName("syncMedia")
        self.vboxlayout.addWidget(self.syncMedia)
        self.syncOnProgramOpen = QtWidgets.QCheckBox(self.tab_2)
        self.syncOnProgramOpen.setObjectName("syncOnProgramOpen")
        self.vboxlayout.addWidget(self.syncOnProgramOpen)
        self.fullSync = QtWidgets.QCheckBox(self.tab_2)
        self.fullSync.setObjectName("fullSync")
        self.vboxlayout.addWidget(self.fullSync)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.syncDeauth = QtWidgets.QPushButton(self.tab_2)
        self.syncDeauth.setAutoDefault(False)
        self.syncDeauth.setObjectName("syncDeauth")
        self.horizontalLayout.addWidget(self.syncDeauth)
        self.syncUser = QtWidgets.QLabel(self.tab_2)
        self.syncUser.setText("")
        self.syncUser.setObjectName("syncUser")
        self.horizontalLayout.addWidget(self.syncUser)
        spacerItem1 = QtWidgets.QSpacerItem(40, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.vboxlayout.addLayout(self.horizontalLayout)
        self.hboxlayout.addLayout(self.vboxlayout)
        self.verticalLayout_4.addLayout(self.hboxlayout)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem2)
        self.tabWidget.addTab(self.tab_2, _("Network"))

        #####################################################
        # Backup tab
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_3.setContentsMargins(12, 12, 12, 12)
        self.verticalLayout_3.setSpacing(12)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_9 = QtWidgets.QLabel(self.tab)
        self.label_9.setWordWrap(True)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_3.addWidget(self.label_9)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_10 = QtWidgets.QLabel(self.tab)
        self.label_10.setObjectName("label_10")
        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)
        self.numBackups = QtWidgets.QSpinBox(self.tab)
        self.numBackups.setMinimumSize(QtCore.QSize(60, 0))
        self.numBackups.setMaximumSize(QtCore.QSize(60, 16777215))
        self.numBackups.setObjectName("numBackups")
        self.gridLayout_2.addWidget(self.numBackups, 0, 1, 1, 1)
        self.label_11 = QtWidgets.QLabel(self.tab)
        self.label_11.setObjectName("label_11")
        self.gridLayout_2.addWidget(self.label_11, 0, 2, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem3, 0, 3, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_2)
        self.openBackupFolder = QtWidgets.QLabel(self.tab)
        self.openBackupFolder.setObjectName("openBackupFolder")
        self.verticalLayout_3.addWidget(self.openBackupFolder)
        self.label_4 = QtWidgets.QLabel(self.tab)
        self.label_4.setWordWrap(True)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_3.addWidget(self.label_4)
        spacerItem4 = QtWidgets.QSpacerItem(20, 59, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem4)
        self.label_21 = QtWidgets.QLabel(self.tab)
        self.label_21.setAlignment(QtCore.Qt.AlignCenter)
        self.label_21.setObjectName("label_21")
        self.verticalLayout_3.addWidget(self.label_21)
        self.tabWidget.addTab(self.tab, _("Backups"))

        #####################################################
        # Muffins tab
        self.lrnStage=QtWidgets.QWidget()
        self.tabWidget.addTab(self.lrnStage, "Muffins")
        self.lrnStageGLayout=QtWidgets.QGridLayout()
        self.lrnStageVLayout=QtWidgets.QVBoxLayout(self.lrnStage)
        self.lrnStageVLayout.addLayout(self.lrnStageGLayout)
        spacerItem=QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.lrnStageVLayout.addItem(spacerItem)

        # Addon: Final Drill
        self.skipFinalDrill=QtWidgets.QCheckBox(self.lrnStage)
        self.lrnStageGLayout.addWidget(self.skipFinalDrill, 1, 0, 1, 3)
        self.skipFinalDrill.setTristate(True)

        #####################################################
        # Close button
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(Preferences)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(Preferences)
        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(Preferences.accept)
        self.buttonBox.rejected.connect(Preferences.reject)
        QtCore.QMetaObject.connectSlotsByName(Preferences)
        # Preferences.setTabOrder(self.lang, self.hwAccel)
        # Preferences.setTabOrder(self.hwAccel, self.showEstimates)
        Preferences.setTabOrder(self.lang, self.showProgress)
        Preferences.setTabOrder(self.showProgress, self.pastePNG)
        # Preferences.setTabOrder(self.pastePNG, self.nightMode)
        # Preferences.setTabOrder(self.nightMode, self.dayLearnFirst)
        Preferences.setTabOrder(self.pastePNG, self.noScript)
        Preferences.setTabOrder(self.noScript, self.newSched)
        Preferences.setTabOrder(self.newSched, self.useCurrent)
        Preferences.setTabOrder(self.useCurrent, self.newSpread)
        Preferences.setTabOrder(self.newSpread, self.dayOffset)
        Preferences.setTabOrder(self.dayOffset, self.lrnCutoff)
        Preferences.setTabOrder(self.lrnCutoff, self.timeLimit)
        Preferences.setTabOrder(self.timeLimit, self.numBackups)
        Preferences.setTabOrder(self.numBackups, self.syncOnProgramOpen)
        Preferences.setTabOrder(self.syncOnProgramOpen, self.tabWidget)
        Preferences.setTabOrder(self.tabWidget, self.fullSync)
        Preferences.setTabOrder(self.fullSync, self.syncMedia)
        Preferences.setTabOrder(self.syncMedia, self.syncDeauth)

        Preferences.setTabOrder(self.syncDeauth, self.showFormatBtns)
        Preferences.setTabOrder(self.showFormatBtns, self.autoCompleter)
        Preferences.setTabOrder(self.autoCompleter, self.powerUserMode)
        Preferences.setTabOrder(self.powerUserMode, self.noAutoPlay)
        Preferences.setTabOrder(self.noAutoPlay, self.mpvDA)
        Preferences.setTabOrder(self.mpvDA, self.showAudPlayBtn)
        Preferences.setTabOrder(self.showAudPlayBtn, self.stpAudOnShwAns)
        Preferences.setTabOrder(self.stpAudOnShwAns, self.importMedia)
        Preferences.setTabOrder(self.importMedia, self.noScript)


    def retranslateUi(self, Preferences):
        _translate = QtCore.QCoreApplication.translate
        Preferences.setWindowTitle(_("Preferences"))
        self.label.setText(_("Interface language:"))
        # self.hwAccel.setText(_("Hardware acceleration (faster, may cause display issues)"))
        self.showEstimates.setText(_("Show next review time above answer buttons"))
        self.showProgress.setText(_("Show remaining card count during review"))
        self.pastePNG.setText(_("Paste clipboard images as PNG"))
        # self.nightMode.setText(_("Show cards as white on black (night mode)"))
        self.dayLearnFirst.setText(_("Show learning cards with larger steps before reviews"))
        self.newSched.setText(_("Anki 2.1 V2 scheduler (beta)"))
        self.useCurrent.setItemText(0, _("When adding, default to current deck"))
        self.useCurrent.setItemText(1, _("Change deck depending on note type"))
        self.label_23.setText(_("Next day starts at"))
        self.label_24.setText(_("Learn ahead limit"))
        self.label_29.setText(_("mins"))
        self.label_30.setText(_("Timebox time limit"))
        self.label_39.setText(_("mins"))
        self.label_40.setText(_("hours past midnight"))
        # self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _("Basic"))
        self.syncLabel.setText(_("<b>Synchronisation</b>"))
        self.syncMedia.setText(_("Synchronize audio and images too"))
        self.syncOnProgramOpen.setText(_("Automatically sync on profile open/close"))
        self.fullSync.setText(_("On next sync, force changes in one direction"))
        self.syncDeauth.setText(_("Deauthorize"))
        # self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _("Network"))
        self.label_9.setText(_("<b>Backups</b><br>Anki will create a backup of your collection each time it is closed or synchronized."))
        self.label_10.setText(_("Keep"))
        self.label_11.setText(_("backups"))
        self.openBackupFolder.setText(_("<a href=\"backups\">Open backup folder</a>"))
        self.label_4.setText(_("Note: Media is not backed up. Please create a periodic backup of your Anki folder to be safe."))
        self.label_21.setText(_("Some settings will take effect after you restart Anki."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _("Backups"))

        # Advanced tab
        self.ansKeyActNothing.setText(_("Nothing"))
        self.ansKeyActFlip.setText(_("Flip"))
        self.ansKeyActGrade.setText(_("Grade"))
        self.colorGradeBtns.setText(_("Colorize Buttons"))
        self.bigGradeBtns.setText(_("Enlarge Buttons"))
        self.showFormatBtns.setText(_("Show extra formatting buttons in editor"))
        self.autoCompleter.setText(_("Use auto complete when adding card?"))
        self.powerUserMode.setText(_("Power User Mode (req. lots of ram)"))
        self.noAutoPlay.setText(_("Disable autoplay (Global)"))
        self.mpvDA.setText(_("MPlayer direct access (no cache)(posible unicode err)"))
        self.showAudPlayBtn.setText(_("Show play buttons on cards with audio"))
        self.stpAudOnShwAns.setText(_("Stop media playback before show answer"))
        self.importMedia.setText(_("Import and localize media during edits (e.g. src=http...)"))
        self.noScript.setText(_("Remove <script> when editing HTML (add more conf later)"))

        # Muffins tab
        self.skipFinalDrill.setText(_('Skip Final Drill'))
