# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/browser.ui'
#
# Created: Thu Dec 22 13:02:38 2016
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui as QtWidgets, QtGui
from anki.lang import _
from aqt.sidebar import SidebarTreeWidget
import ccbc.plugins.Card_Info_Bar_for_Browser.browser


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(750, 400)
        Dialog.setMinimumSize(QtCore.QSize(750, 400))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/find.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(Dialog)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setMargin(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.splitter_2 = QtGui.QSplitter(self.centralwidget)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.tree = SidebarTreeWidget(self.splitter_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tree.sizePolicy().hasHeightForWidth())
        self.tree.setSizePolicy(sizePolicy)
        self.tree.setFrameShape(QtGui.QFrame.NoFrame)
        self.tree.setObjectName("tree")
        self.tree.headerItem().setText(0, "1")
        self.tree.header().setVisible(False)
        self.splitter = QtGui.QSplitter(self.splitter_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.widget = QtGui.QWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setContentsMargins(0, 0, 0, -1)
        self.gridLayout.setHorizontalSpacing(6)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.searchEdit = QtGui.QComboBox(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(9)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchEdit.sizePolicy().hasHeightForWidth())
        self.searchEdit.setSizePolicy(sizePolicy)
        self.searchEdit.setEditable(True)
        self.searchEdit.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.searchEdit.setObjectName("searchEdit")
        self.gridLayout.addWidget(self.searchEdit, 0, 0, 1, 1)
        self.searchButton = QtGui.QPushButton(self.widget)
        self.searchButton.setObjectName("searchButton")
        self.gridLayout.addWidget(self.searchButton, 0, 1, 1, 1)
        self.previewButton = QtGui.QPushButton(self.widget)
        self.previewButton.setCheckable(True)
        self.previewButton.setObjectName("previewButton")
        self.gridLayout.addWidget(self.previewButton, 0, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.tableView = QtGui.QTableView(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(9)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy)
        self.tableView.setMinimumSize(QtCore.QSize(0, 150))
        self.tableView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tableView.setFrameShape(QtGui.QFrame.NoFrame)
        self.tableView.setFrameShadow(QtGui.QFrame.Plain)
        self.tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tableView.setTabKeyNavigation(False)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setObjectName("tableView")
        self.tableView.horizontalHeader().setCascadingSectionResizes(False)
        self.tableView.horizontalHeader().setHighlightSections(False)
        self.tableView.horizontalHeader().setMinimumSectionSize(20)
        self.tableView.horizontalHeader().setSortIndicatorShown(True)
        self.verticalLayout_2.addWidget(self.tableView)
        self.verticalLayoutWidget = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 1, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout2 = QtGui.QHBoxLayout()
        self.horizontalLayout2.setSpacing(0)
        self.horizontalLayout2.setMargin(0)
        self.horizontalLayout2.setObjectName("horizontalLayout2")
        self.fieldsArea = QtGui.QWidget(self.verticalLayoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.fieldsArea.sizePolicy().hasHeightForWidth())
        self.fieldsArea.setSizePolicy(sizePolicy)
        self.fieldsArea.setMinimumSize(QtCore.QSize(50, 200))
        self.fieldsArea.setObjectName("fieldsArea")
        self.horizontalLayout2.addWidget(self.fieldsArea)
        self.verticalLayout.addLayout(self.horizontalLayout2)
        self.verticalLayout_3.addWidget(self.splitter_2)
        Dialog.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(Dialog)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 750, 22))
        self.menubar.setObjectName("menubar")
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menu_Notes = QtGui.QMenu(self.menubar)
        self.menu_Notes.setObjectName("menu_Notes")
        self.menu_Cards = QtGui.QMenu(self.menubar)
        self.menu_Cards.setObjectName("menu_Cards")
        self.menuFlag = QtGui.QMenu(self.menu_Cards)
        self.menuFlag.setObjectName("menuFlag")
        self.menuJump = QtGui.QMenu(self.menubar)
        self.menuJump.setObjectName("menuJump")
        Dialog.setMenuBar(self.menubar)
        self.actionReschedule = QtGui.QAction(Dialog)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/view-pim-calendar.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReschedule.setIcon(icon1)
        self.actionReschedule.setObjectName("actionReschedule")
        self.actionSelectAll = QtGui.QAction(Dialog)
        self.actionSelectAll.setObjectName("actionSelectAll")
        self.actionUndo = QtGui.QAction(Dialog)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/edit-undo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionUndo.setIcon(icon2)
        self.actionUndo.setObjectName("actionUndo")
        self.actionInvertSelection = QtGui.QAction(Dialog)
        self.actionInvertSelection.setObjectName("actionInvertSelection")
        self.actionFind = QtGui.QAction(Dialog)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/document-preview.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFind.setIcon(icon3)
        self.actionFind.setObjectName("actionFind")
        self.actionNote = QtGui.QAction(Dialog)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/Anki_Fact.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionNote.setIcon(icon4)
        self.actionNote.setObjectName("actionNote")
        self.actionSidebar = QtGui.QAction(Dialog)
        self.actionSidebar.setObjectName("actionSidebar")
        # Flags
        self.actionClear_Flag = QtGui.QAction(Dialog)
        self.actionClear_Flag.setObjectName("actionClear_Flag")
        self.actionRed_Flag = QtGui.QAction(Dialog)
        self.actionRed_Flag.setCheckable(True)
        self.actionRed_Flag.setObjectName("actionRed_Flag")
        self.actionOrange_Flag = QtGui.QAction(Dialog)
        self.actionOrange_Flag.setCheckable(True)
        self.actionOrange_Flag.setObjectName("actionOrange_Flag")
        self.actionGreen_Flag = QtGui.QAction(Dialog)
        self.actionGreen_Flag.setCheckable(True)
        self.actionGreen_Flag.setObjectName("actionGreen_Flag")
        self.actionBlue_Flag = QtGui.QAction(Dialog)
        self.actionBlue_Flag.setCheckable(True)
        self.actionBlue_Flag.setObjectName("actionBlue_Flag")

        self.actionNextCard = QtGui.QAction(Dialog)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/go-next.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionNextCard.setIcon(icon5)
        self.actionNextCard.setObjectName("actionNextCard")
        self.actionPreviousCard = QtGui.QAction(Dialog)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/go-previous.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPreviousCard.setIcon(icon6)
        self.actionPreviousCard.setObjectName("actionPreviousCard")
        self.actionChangeModel = QtGui.QAction(Dialog)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icons/system-software-update.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionChangeModel.setIcon(icon8)
        self.actionChangeModel.setObjectName("actionChangeModel")
        self.actionSelectNotes = QtGui.QAction(Dialog)
        self.actionSelectNotes.setObjectName("actionSelectNotes")
        self.actionFindReplace = QtGui.QAction(Dialog)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/icons/edit-find-replace.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFindReplace.setIcon(icon9)
        self.actionFindReplace.setObjectName("actionFindReplace")
        self.actionCram = QtGui.QAction(Dialog)
        self.actionCram.setIcon(icon1)
        self.actionCram.setObjectName("actionCram")
        self.actionTags = QtGui.QAction(Dialog)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/icons/anki-tag.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTags.setIcon(icon10)
        self.actionTags.setObjectName("actionTags")
        self.actionCardList = QtGui.QAction(Dialog)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/icons/generate_07.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCardList.setIcon(icon11)
        self.actionCardList.setObjectName("actionCardList")
        self.actionFindDuplicates = QtGui.QAction(Dialog)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(":/icons/edit-find 2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFindDuplicates.setIcon(icon12)
        self.actionFindDuplicates.setObjectName("actionFindDuplicates")
        self.actionReposition = QtGui.QAction(Dialog)
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap(":/icons/view-sort-ascending.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReposition.setIcon(icon13)
        self.actionReposition.setObjectName("actionReposition")
        self.actionFirstCard = QtGui.QAction(Dialog)
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap(":/icons/arrow-up.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFirstCard.setIcon(icon14)
        self.actionFirstCard.setObjectName("actionFirstCard")
        self.actionLastCard = QtGui.QAction(Dialog)
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap(":/icons/arrow-down.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLastCard.setIcon(icon15)
        self.actionLastCard.setObjectName("actionLastCard")
        self.actionClose = QtGui.QAction(Dialog)
        self.actionClose.setObjectName("actionClose")
        self.menuEdit.addAction(self.actionUndo)

        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addAction(self.actionSelectNotes)
        self.menuEdit.addAction(self.actionInvertSelection)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionClose)

        # Go menu
        self.menuJump.addAction(self.actionFind)
        self.menuJump.addAction(self.actionTags) #filter
        self.menuJump.addAction(self.actionNote)
        self.menuJump.addAction(self.actionSidebar)
        self.menuJump.addAction(self.actionCardList)
        self.menuJump.addSeparator()
        self.menuJump.addAction(self.actionFirstCard)
        self.menuJump.addAction(self.actionPreviousCard)
        self.menuJump.addAction(self.actionNextCard)
        self.menuJump.addAction(self.actionLastCard)

        # View menu
        self.actionShowEdit = QtGui.QAction(Dialog)
        self.actionShowEdit.setObjectName("actionShowEdit")
        self.actionShowEdit.setCheckable(True)
        self.actionShowEdit.setChecked(True)
        self.menuView.addAction(self.actionShowEdit)

        #Addon: Card Info Bar for Browser, https://ankiweb.net/shared/info/2140680811
        ccbc.plugins.Card_Info_Bar_for_Browser.browser.menu(self)

        # Notes menu
        self.menu_Notes.addAction(self.actionChangeModel)
        self.menu_Notes.addAction(self.actionFindDuplicates)
        self.menu_Notes.addAction(self.actionFindReplace)
        # Cards menu
        self.menu_Cards.addAction(self.actionReschedule)
        self.menu_Cards.addAction(self.actionReposition)
        # Flag submenu
        self.menuFlag.addAction(self.actionClear_Flag)
        self.menuFlag.addSeparator()
        self.menuFlag.addAction(self.actionRed_Flag)
        self.menuFlag.addAction(self.actionOrange_Flag)
        self.menuFlag.addAction(self.actionGreen_Flag)
        self.menuFlag.addAction(self.actionBlue_Flag)
        self.menu_Cards.addAction(self.menuFlag.menuAction())

        # main menubar
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menu_Notes.menuAction())
        self.menubar.addAction(self.menu_Cards.menuAction())
        self.menubar.addAction(self.menuJump.menuAction())

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.actionSelectAll, QtCore.SIGNAL("triggered()"), self.tableView.selectAll)
        QtCore.QObject.connect(self.actionClose, QtCore.SIGNAL("activated()"), Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("Browser"))
        self.searchButton.setText(_("Search"))
        self.previewButton.setText(_("Preview"))
        self.previewButton.setShortcut(_("Ctrl+Shift+P"))
        self.menuEdit.setTitle(_("&Edit"))
        self.menuJump.setTitle(_("&Go"))
        self.menuView.setTitle(_("&View"))
        self.menu_Cards.setTitle(_("&Cards"))
        self.menu_Notes.setTitle(_("&Notes"))
        self.actionReschedule.setText(_("&Reschedule..."))
        self.actionSelectAll.setText(_("Select &All"))
        self.actionSelectAll.setShortcut(_("Ctrl+A"))
        self.actionUndo.setText(_("&Undo"))
        self.actionUndo.setShortcut(_("Ctrl+Z"))
        self.actionInvertSelection.setText(_("&Invert Selection"))
        self.actionFind.setText(_("&Find"))
        self.actionFind.setShortcut(_("Ctrl+F"))
        self.actionNote.setText(_("N&ote"))
        self.actionNote.setShortcut(_("Ctrl+Shift+N"))
        self.actionSidebar.setText(_("Sidebar"))
        self.actionSidebar.setShortcut(_("Ctrl+Shift+R"))
        self.actionNextCard.setText(_("&Next Card"))
        self.actionNextCard.setShortcut(_("Ctrl+N"))
        self.actionPreviousCard.setText(_("&Previous Card"))
        self.actionPreviousCard.setShortcut(_("Ctrl+P"))
        self.actionChangeModel.setText(_("Change Note Type..."))
        self.actionChangeModel.setShortcut(_("Ctrl+Shift+M"))
        self.actionSelectNotes.setText(_("Select &Notes"))
        self.actionSelectNotes.setShortcut(_("Ctrl+Shift+A"))
        self.actionFindReplace.setText(_("Find and Re&place..."))
        self.actionFindReplace.setShortcut(_("Ctrl+Alt+F"))
        self.actionCram.setText(_("&Cram..."))
        self.actionTags.setText(_("Fil&ters"))
        self.actionTags.setShortcut(_("Ctrl+Shift+F"))
        self.actionCardList.setText(_("Card List"))
        self.actionCardList.setShortcut(_("Ctrl+Shift+L"))
        self.actionFindDuplicates.setText(_("Find &Duplicates..."))
        self.actionReposition.setText(_("Reposition..."))
        self.actionReposition.setShortcut(_("Ctrl+Shift+S"))
        self.actionFirstCard.setText(_("First Card"))
        self.actionFirstCard.setShortcut(_("Home"))
        self.actionLastCard.setText(_("Last Card"))
        self.actionLastCard.setShortcut(_("End"))
        self.actionClose.setText(_("Close"))
        self.actionClose.setShortcut(_("Ctrl+W"))

        self.actionShowEdit.setText(_("Show Editor"))
        self.actionShowEdit.setShortcut(_("Ctrl+Shift+E"))

        self.menuFlag.setTitle(_("Flag"))
        self.actionClear_Flag.setText(_("Clear Flags"))
        self.actionClear_Flag.setShortcut(_("Ctrl+0"))
        self.actionRed_Flag.setText(_("Red Flag"))
        self.actionRed_Flag.setShortcut(_("Ctrl+1"))
        self.actionOrange_Flag.setText(_("Orange Flag"))
        self.actionOrange_Flag.setShortcut(_("Ctrl+2"))
        self.actionGreen_Flag.setText(_("Green Flag"))
        self.actionGreen_Flag.setShortcut(_("Ctrl+3"))
        self.actionBlue_Flag.setText(_("Blue Flag"))
        self.actionBlue_Flag.setShortcut(_("Ctrl+4"))

from . import icons_rc
