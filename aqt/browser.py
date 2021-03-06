# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

import sre_constants
import cgi
import time
import re
from operator import  itemgetter
from anki.lang import ngettext, _
# from bs4 import BeautifulSoup
from anki.sound import play

from aqt.qt import *
import anki
import aqt.forms
import anki.find
from anki.utils import fmtTimeSpan, ids2str, htmlToTextLine, stripHTMLMedia, isWin, intTime, isMac, stripAccentChars, noOpTxtSearch
from aqt.utils import saveGeom, restoreGeom, saveSplitter, restoreSplitter, \
    saveHeader, restoreHeader, saveState, restoreState, applyStyles, getTag, \
    showInfo, askUser, tooltip, showWarning, shortcut, getBase, mungeQA, \
    qtMenuShortcutWorkaround, getText
from anki.hooks import runHook, addHook, remHook, runFilter
from aqt.webview import AnkiWebView
from aqt.toolbar import Toolbar
from anki.consts import *
from anki.sound import playFromText, clearAudioQueue
import ccbc.css

from aqt.sidebar import TagTreeWidget, SidebarTreeView, SidebarItem, SidebarModel
from aqt.tagedit import TagEdit
# from ccbc.utils import getIcon


# Data model
##########################################################################

class DataModel(QAbstractTableModel):

    def __init__(self, browser):
        QAbstractTableModel.__init__(self)
        self.browser = browser
        self.col = browser.col
        self.sortKey = None
        self.activeCols = self.col.conf.get(
            "activeCols", ["noteFld", "template", "cardDue", "deck"])
        self.cards = []
        self.cardObjs = {}

    def getCard(self, index):
        id = self.cards[index.row()]
        if not id in self.cardObjs:
            self.cardObjs[id] = self.col.getCard(id)
        return self.cardObjs[id]

    def refreshNote(self, note):
        refresh = False
        for c in note.cards():
            if c.id in self.cardObjs:
                del self.cardObjs[c.id]
                refresh = True
        if refresh:
            self.layoutChanged.emit()

    # Model interface
    ######################################################################

    def rowCount(self, parent):
        if parent and parent.isValid():
            return 0
        return len(self.cards)

    def columnCount(self, parent):
        if parent and parent.isValid():
            return 0
        return len(self.activeCols)

    def data(self, index, role):
        if not index.isValid():
            return
        if role == Qt.FontRole:
            if self.activeCols[index.column()] not in (
                "question", "answer", "noteFld"):
                return
            row = index.row()
            c = self.getCard(index)
            t = c.template()
            if not t.get("bfont"):
                return
            f = QFont()
            f.setFamily(t.get("bfont", "arial"))
            f.setPixelSize(t.get("bsize", 12))
            return f
                                   
        elif role == Qt.TextAlignmentRole:
            align = Qt.AlignVCenter
            if self.activeCols[index.column()] not in ("question", "answer",
               "template", "deck", "noteFld", "note"):
                align |= Qt.AlignHCenter
            return align
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            return self.columnData(index)
        else:
            return

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical:
            return
        elif role == Qt.DisplayRole and section < len(self.activeCols):
            type = self.columnType(section)
            txt = None
            for stype, name in self.browser.columns:
                if type == stype:
                    txt = name
                    break
            # give the user a hint an invalid column was added by an add-on
            if not txt:
                txt = _("Add-on")
            return txt
        else:
            return

    def flags(self, index):
        return Qt.ItemFlag(Qt.ItemIsEnabled |
                           Qt.ItemIsSelectable)

    # Filtering
    ######################################################################

    def search(self, txt, reset=True):
        self.beginReset()
        # t = time.time()
        # the db progress handler may cause a refresh, so we need to zero out
        # old data first
        self.cards = []
        # invalid = False
        try:
            self.cards = self.col.findCards(txt, order=True)
        except Exception as e:
            if str(e) == "invalidSearch":
                self.cards = []
                # invalid = True
            else:
                raise
        #print "fetch cards in %dms" % ((time.time() - t)*1000)
        self.endReset()

        # if invalid:
            # showWarning(_("Invalid search - please check for typing mistakes."))


    def reset(self):
        self.beginReset()
        self.endReset()

    # caller must have called editor.saveNow() before calling this or .reset()
    def beginReset(self):
        self.browser.editor.setNote(None, hide=False)
        self.browser.mw.progress.start()
        self.saveSelection()
        self.beginResetModel()
        self.cardObjs = {}

    def endReset(self):
        t = time.time()
        self.endResetModel()
        self.restoreSelection()
        self.browser.mw.progress.finish()

    def reverse(self):
        self.browser.editor.saveNow(self._reverse)

    def _reverse(self):
        self.beginReset()
        self.cards.reverse()
        self.endReset()

    def saveSelection(self):
        cards = self.browser.selectedCards()
        self.selectedCards = dict([(id, True) for id in cards])
        if getattr(self.browser, 'card', None):
            self.focusedCard = self.browser.card.id
        else:
            self.focusedCard = None

    def restoreSelection(self):
        if not self.cards:
            return
        sm = self.browser.form.tableView.selectionModel()
        sm.clear()
        # restore selection
        items = QItemSelection()
        count = 0
        firstIdx = None
        focusedIdx = None
        for row, id in enumerate(self.cards):
            # if the id matches the focused card, note the index
            if self.focusedCard == id:
                focusedIdx = self.index(row, 0)
                items.select(focusedIdx, focusedIdx)
                self.focusedCard = None
            # if the card was previously selected, select again
            if id in self.selectedCards:
                count += 1
                idx = self.index(row, 0)
                items.select(idx, idx)
                # note down the first card of the selection, in case we don't
                # have a focused card
                if not firstIdx:
                    firstIdx = idx
        # focus previously focused or first in selection
        idx = focusedIdx or firstIdx
        tv = self.browser.form.tableView
        if idx:
            tv.selectRow(idx.row())
            # scroll if the selection count has changed
            if count != len(self.selectedCards):
                # we save and then restore the horizontal scroll position because
                # scrollTo() also scrolls horizontally which is confusing
                h = tv.horizontalScrollBar().value()
                tv.scrollTo(idx, tv.PositionAtCenter)
                tv.horizontalScrollBar().setValue(h)
            if count < 500:
                # discard large selections; they're too slow
                sm.select(items, QItemSelectionModel.SelectCurrent |
                          QItemSelectionModel.Rows)
        else:
            tv.selectRow(0)

    # Column data
    ######################################################################

    def columnType(self, column):
        return self.activeCols[column]

    def columnData(self, index):
        row = index.row()
        col = index.column()
        type = self.columnType(col)
        c = self.getCard(index)
        if type == "question":
            return self.question(c)
        elif type == "answer":
            return self.answer(c)
        elif type == "noteFld":
            f = c.note()
            return htmlToTextLine(f.fields[self.col.models.sortIdx(f.model())])
        elif type == "template":
            t = c.template()['name']
            if c.model()['type'] == MODEL_CLOZE:
                t += " %d" % (c.ord+1)
            return t
        elif type == "cardDue":
            # catch invalid dates
            try:
                t = self.nextDue(c, index)
            except:
                t = ""
            if c.queue < 0:
                t = "(" + t + ")"
            return t
        elif type == "noteCrt":
            return time.strftime("%Y-%m-%d", time.localtime(c.note().id/1000))
        elif type == "noteMod":
            return time.strftime("%Y-%m-%d", time.localtime(c.note().mod))
        elif type == "cardMod":
            return time.strftime("%Y-%m-%d", time.localtime(c.mod))
        elif type == "cardReps":
            return str(c.reps)
        elif type == "cardLapses":
            return str(c.lapses)
        elif type == "noteTags":
            return " ".join(c.note().tags)
        elif type == "note":
            return c.model()['name']
        elif type == "cardIvl":
            if c.type == 0:
                return _("(new)")
            elif c.type == 1:
                return _("(learning)")
            return fmtTimeSpan(c.ivl*86400)
        elif type == "cardEase":
            if c.type == 0:
                return _("(new)")
            return "%d%%" % (c.factor/10)
        elif type == "deck":
            if c.odid:
                # in a cram deck
                return "%s (%s)" % (
                    self.browser.mw.col.decks.name(c.did),
                    self.browser.mw.col.decks.name(c.odid))
            # normal deck
            return self.browser.mw.col.decks.name(c.did)

    def question(self, c):
        return htmlToTextLine(c.q(browser=True))

    def answer(self, c):
        if c.template().get('bafmt'):
            # they have provided a template, use it verbatim
            c.q(browser=True)
            return htmlToTextLine(c.a())
        # need to strip question from answer
        q = self.question(c)
        a = htmlToTextLine(c.a())
        if a.startswith(q):
            return a[len(q):].strip()
        return a

    def formatQA(self, txt):
        return htmlToTextLine(txt)

    def nextDue(self, c, index):
        if c.odid:
            return _("(filtered)")
        elif c.queue == 1:
            date = c.due
        elif c.queue == 0 or c.type == 0:
            return str(c.due)
        elif c.queue in (2,3) or (c.type == 2 and c.queue < 0):
            date = time.time() + ((c.due - self.col.sched.today)*86400)
        else:
            return ""
        return time.strftime("%Y-%m-%d", time.localtime(date))

    def isRTL(self, index):
        col = index.column()
        type = self.columnType(col)
        if type != "noteFld":
            return False

        row = index.row()
        c = self.getCard(index)
        nt = c.note().model()
        return nt['flds'][self.col.models.sortIdx(nt)]['rtl']


# Line painter
######################################################################

COLOUR_SUSPENDED = "#FFFFB2"
COLOUR_MARKED = "yellow"

flagColours = {
    1: "#ffaaaa",
    2: "#ffb347",
    3: "#82E0AA",
    4: "#85C1E9",
}

class StatusDelegate(QItemDelegate):

    def __init__(self, browser, model):
        QItemDelegate.__init__(self, browser)
        self.browser = browser
        self.model = model

    def paint(self, painter, option, index):
        self.browser.mw.progress.blockUpdates = True
        try:
            c = self.model.getCard(index)
        except:
            # in the the middle of a reset; return nothing so this row is not
            # rendered until we have a chance to reset the model
            return
        finally:
            self.browser.mw.progress.blockUpdates = True

        if self.model.isRTL(index):
            option.direction = Qt.RightToLeft

        col = None
        if c.userFlag() > 0:
            col = flagColours[c.userFlag()]
        elif c.note().hasTag("Marked"):
            col = COLOUR_MARKED
        elif c.queue == -1:
            col = COLOUR_SUSPENDED
        if col:
            brush = QBrush(QColor(col))
            painter.save()
            painter.fillRect(option.rect, brush)
            painter.restore()

        return QItemDelegate.paint(self, painter, option, index)

# Browser window
######################################################################

# fixme: respond to reset+edit hooks

class Browser(QMainWindow):

    _searchPrompt = _("<type here to search; hit enter to show current deck>")

    cb_shown = {
        "editor": True,
        "sidebar": True
    }

    def __init__(self, mw, sidebar=True):
        QMainWindow.__init__(self, None, Qt.Window) #Use None to prevent addCard being pushed to the bg
        # mw.setupDialogGC(self) #AttributeError: 'Browser' object has no attribute 'finished'
        self.setAttribute(Qt.WA_DeleteOnClose, True) #gc stuff, replaces above line
        applyStyles(self)
        self.mw = mw
        self.col = self.mw.col
        self.lastFilter = ""
        self._previewWindow = None
        self.form = aqt.forms.browser.Ui_Dialog()
        self.form.setupUi(self)
        restoreGeom(self, "editor", 0)
        restoreState(self, "editor")
        restoreSplitter(self.form.splitter_2, "editor2")
        restoreSplitter(self.form.splitter, "editor3")

        self.setWindowState(self.mw.windowState())
        self.wasMaxState = self.isMaximized()
        self.normalState = self.normalGeometry()

        self.form.splitter_2.setChildrenCollapsible(False)
        self.form.splitter.setChildrenCollapsible(False)
        self.card = None
        self.dropItem = None
        self.showSidebar = sidebar and self.cb_shown['sidebar']
        self.lockedSearch = ""

        self.mw.col.tags.registerNotes() #clean up tags
        self.setupToolbar()
        self.setupColumns()
        self.setupTable()
        self.setupMenus()
        self.setupSearch()
        self.setupSidebar()
        self.setupHeaders()
        self.setupHooks()
        self.setupEditor()
        self.updateFont()
        self.onUndoState(self.mw.form.actionUndo.isEnabled())

        self.form.searchEdit.setFocus()
        self.form.searchEdit.lineEdit().setText("is:current")
        self.form.searchEdit.lineEdit().selectAll()
        self.onSearch()

        if self.mw.viewmanager.cbOnTop.isChecked():
            windowFlags = self.windowFlags() | Qt.WindowStaysOnTopHint
            self.setWindowFlags(windowFlags)
        self.show()

        addHook("night_mode_state_changed", self.changeToNightMode)

    def changeToNightMode(self, b):
        pass

    def toggleFullScreen(self):
        toFS = self.windowState() ^ Qt.WindowFullScreen
        if toFS:
            self.wasMaxState = self.isMaximized()
            self.normalState = self.normalGeometry()
            self.showFullScreen()
        elif self.wasMaxState:
            self.setGeometry(self.normalState)
            self.showMaximized()
        else:
            self.setGeometry(self.normalState)
        self.form.actionFullScreen.setChecked(toFS)

    def toggleSidebar(self):
        b = not self.showSidebar
        self.showSidebar = self.cb_shown["sidebar"] = b
        self.form.sidebarDockWidget.setVisible(b)
        if b:
            self.maybeRefreshSidebar()

    def toggleEditor(self):
        self.cb_shown["editor"] = not self.cb_shown["editor"]
        self.onRowChanged()

    def toggleSplitOrientation(self):
        b = self.form.toRSideEditor.isChecked()
        self.mw.pm.profile["browser.splitterOrientation"] = b
        ori = Qt.Horizontal if b else Qt.Vertical
        self.form.splitter.setOrientation(ori)

    def setupToolbar(self):
        self.toolbarWeb = AnkiWebView()
        self.toolbarWeb.setFixedHeight(25 + self.mw.fontHeightDelta)
        self.toolbar = BrowserToolbar(self.mw, self.toolbarWeb, self)
        self.form.verticalLayout_3.insertWidget(0, self.toolbarWeb)
        self.toolbar.draw()

    def setupMenus(self):
        # actions
        c = self.connect
        f = self.form
        s = SIGNAL("triggered()")

        if not isMac:
            f.actionClose.setVisible(False)
        c(f.actionReposition, s, self.reposition)
        c(f.actionReschedule, s, self.reschedule)
        # c(f.actionCram, s, self.cram)
        c(f.actionChangeModel, s, self.onChangeModel)

        # edit
        c(f.actionUndo, s, self.mw.onUndo)
        # c(f.previewButton, SIGNAL("clicked()"), self.onTogglePreview)
        # f.previewButton.setToolTip(_("Preview Selected Card (%s)") %
            # shortcut(_("Ctrl+Shift+P")))
        c(f.actionInvertSelection, s, self.invertSelection)
        c(f.actionSelectNotes, s, self.selectNotes)
        c(f.actionFindReplace, s, self.onFindReplace)
        c(f.actionFindDuplicates, s, self.onFindDupes)

        # Go
        c(f.actionPreviousCard, s, self.onPreviousCard)
        c(f.actionNextCard, s, self.onNextCard)
        c(f.actionFirstCard, s, self.onFirstCard)
        c(f.actionLastCard, s, self.onLastCard)
        c(f.actionFind, s, self.onFind)
        c(f.actionNote, s, self.onNote)
        c(f.actionSidebar, s, self.focusSidebar)
        c(f.actionCardList, s, self.onCardList)

        # view
        f.actionFullScreen.triggered.connect(self.toggleFullScreen)
        f.actionFullScreen.setChecked(self.windowState()==Qt.WindowFullScreen)
        f.actionShowSidebar.setChecked(self.showSidebar)
        f.actionShowSidebar.toggled.connect(self.toggleSidebar)
        f.actionShowEdit.setChecked(self.cb_shown["editor"])
        f.actionShowEdit.toggled.connect(self.toggleEditor)
        f.toRSideEditor.toggled.connect(self.toggleSplitOrientation)
        vert = self.mw.pm.profile.get("browser.splitterOrientation", False)
        if vert:
            f.splitter.setOrientation(Qt.Vertical)
            f.toRSideEditor.setChecked(True)

        # Search menu
        f.actionLockSearch.setChecked(not not self.lockedSearch)
        f.actionLockSearch.toggled.connect(self.setSearchLock)
        b = self.mw.pm.profile.get('ccbc.ignoreAccentSearch', False)
        f.ignoreAccentSearch.toggled.connect(self.onIgnoreAccentSearch)
        f.ignoreAccentSearch.setChecked(b)

        # keyboard shortcut for shift+home/end
        self.pgUpCut = QShortcut(QKeySequence("Shift+Home"), self)
        c(self.pgUpCut, SIGNAL("activated()"), self.onFirstCard)
        self.pgDownCut = QShortcut(QKeySequence("Shift+End"), self)
        c(self.pgDownCut, SIGNAL("activated()"), self.onLastCard)
        # add note
        self.addCut = QShortcut(QKeySequence("Ctrl+E"), self)
        c(self.addCut, SIGNAL("activated()"), self.mw.onAddCard)
        # card info
        self.infoCut = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        c(self.infoCut, SIGNAL("activated()"), self.showCardInfo)
        # set flags
        c(f.actionClear_Flag, s, lambda: self.onSetFlag(0))
        c(f.actionRed_Flag, s, lambda: self.onSetFlag(1))
        c(f.actionOrange_Flag, s, lambda: self.onSetFlag(2))
        c(f.actionGreen_Flag, s, lambda: self.onSetFlag(3))
        c(f.actionBlue_Flag, s, lambda: self.onSetFlag(4))
        # set deck
        self.changeDeckCut = QShortcut(QKeySequence("Ctrl+D"), self)
        c(self.changeDeckCut, SIGNAL("activated()"), self.setDeck)
        # add/remove tags
        self.tagCut1 = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        c(self.tagCut1, SIGNAL("activated()"), self.addTags)
        self.tagCut2 = QShortcut(QKeySequence("Ctrl+Alt+T"), self)
        c(self.tagCut2, SIGNAL("activated()"), self.deleteTags)
        self.tagCut3 = QShortcut(QKeySequence("Ctrl+K"), self)
        c(self.tagCut3, SIGNAL("activated()"), self.onMark)
        # suspending
        self.susCut1 = QShortcut(QKeySequence("Ctrl+J"), self)
        c(self.susCut1, SIGNAL("activated()"), self.onSuspend)
        # deletion
        self.delCut1 = QShortcut(QKeySequence("Delete"), self)
        self.delCut1.setAutoRepeat(False)
        c(self.delCut1, SIGNAL("activated()"), self.deleteNotes)
        # add-on hook
        runHook('browser.setupMenus', self)
        self.mw.maybeHideAccelerators(self)

        # context menu
        self.form.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.form.tableView.customContextMenuRequested.connect(self.onContextMenu)

    def onIgnoreAccentSearch(self):
        b = self.form.ignoreAccentSearch.isChecked()
        self.mw.pm.profile['ccbc.ignoreAccentSearch'] = b

    def onContextMenu(self, _point):
        m = QMenu()

        act = QAction("Card Info", self)
        act.triggered.connect(self.showCardInfo)
        m.addAction(act)

        for act in self.form.menuEdit.actions()[2:5]:
            m.addAction(act)
        m.addSeparator()
        for act in self.form.menu_Cards.actions():
            m.addAction(act)
        # m.addSeparator()
        # for act in self.form.menu_Notes.actions():
            # m.addAction(act)
        runHook("browser.onContextMenu", self, m)
        # qtMenuShortcutWorkaround(m)
        m.exec_(QCursor.pos())

    def updateFont(self):
        # we can't choose different line heights efficiently, so we need
        # to pick a line height big enough for any card template
        curmax = 16
        for m in self.col.models.all():
            for t in m['tmpls']:
                bsize = t.get("bsize", 0)
                if bsize > curmax:
                    curmax = bsize
        self.form.tableView.verticalHeader().setDefaultSectionSize(
            curmax + 6)

    def closeEvent(self, evt):
        saveSplitter(self.form.splitter_2, "editor2")
        saveSplitter(self.form.splitter, "editor3")
        self.editor.saveNow()
        self.editor.setNote(None)
        saveGeom(self, "editor")
        saveState(self, "editor")
        saveHeader(self.form.tableView.horizontalHeader(), "editor")
        self.col.conf['activeCols'] = self.model.activeCols
        self.col.setMod()
        self.hide()
        aqt.dialogs.close("Browser")
        self.teardownHooks()
        self.mw.maybeReset()
        evt.accept()

    def canClose(self):
        return True

    def keyPressEvent(self, evt):
        "Show answer on RET or register answer."
        if evt.key() == Qt.Key_F1:
            self.mw.boss_key()
        elif evt.key() == Qt.Key_Escape:
            self.close()
        elif self.mw.app.focusWidget() == self.sidebarTree:
            if evt.key() in (Qt.Key_Return, Qt.Key_Enter):
                item = self.sidebarTree.currentItem()
                self.onTreeClick(item, 0)

    def setupColumns(self):
        self.columns = [
            ('question', _("Question")),
            ('answer', _("Answer")),
            ('template', _("Card")),
            ('deck', _("Deck")),
            ('noteFld', _("Sort Field")),
            ('noteCrt', _("Created")),
            ('noteMod', _("Edited")),
            ('cardMod', _("Changed")),
            ('cardDue', _("Due")),
            ('cardIvl', _("Interval")),
            ('cardEase', _("Ease")),
            ('cardReps', _("Reviews")),
            ('cardLapses', _("Lapses")),
            ('noteTags', _("Tags")),
            ('note', _("Note")),
        ]
        self.columns.sort(key=itemgetter(1))

    # Searching
    ######################################################################

    def setupSearch(self):
        self.filterTimer = None
        self.form.searchEdit.setLineEdit(FavouritesLineEdit(self.mw, self))
        self.form.searchButton.clicked.connect(self.onSearch)
        self.form.searchEdit.lineEdit().returnPressed.connect(self.onSearch)
        self.form.searchEdit.setCompleter(None)
        self.form.searchEdit.addItems(self.mw.pm.profile['searchHistory'])

    def onSearchActivated(self): #v2.1
        return self.onSearch()

    def onSearch(self, reset=True):
        """Careful: if reset is true, the current note is saved."""
        txt = self.form.searchEdit.lineEdit().text().strip()
        # update search history
        sh = self.mw.pm.profile['searchHistory']
        if txt not in sh:
            sh.insert(0, txt)
            sh = sh[:50]
        self.form.searchEdit.clear()
        self.form.searchEdit.addItems(sh)
        self.mw.pm.profile['searchHistory'] = sh

        if self.mw.state == "review" and "is:current" in txt:
            # search for current card, but set search to easily display whole deck
            if reset:
                self.model.beginReset()
                self.model.focusedCard = self.mw.reviewer.card.id
            self.model.search("nid:%d"%self.mw.reviewer.card.nid, False)
            if reset:
                self.model.endReset()
            self.form.searchEdit.lineEdit().setText(self._searchPrompt)
            self.form.searchEdit.lineEdit().selectAll()
            return
        elif "is:current" in txt:
            self.form.searchEdit.lineEdit().setText(self._searchPrompt)
            self.form.searchEdit.lineEdit().selectAll()
        elif txt == self._searchPrompt:
            txt = "deck:current "
            txt = "%s %s"%(self.lockedSearch, txt)
            self.form.searchEdit.lineEdit().setText(txt)
        else:
            txt = "%s %s"%(self.lockedSearch, txt)
            self.form.searchEdit.lineEdit().setText(txt)

        if self.form.ignoreAccentSearch.isChecked():
            self.col.db._db.create_function("filterTxtSearch",1,stripAccentChars)
            txt = stripAccentChars(txt)
            self.model.search(txt, reset)
            self.col.db._db.create_function("filterTxtSearch",1,noOpTxtSearch)
        else:
            self.model.search(txt, reset)
        if not self.model.cards:
            # no row change will fire
            self.onRowChanged(None, None)
        elif self.mw.state == "review":
            self.focusCid(self.mw.reviewer.card.id)

    def setSearchLock(self):
        txt,ok = getText(
            _("""Auto include search (e.g. is:new)"""),
            default=self.lockedSearch
        )
        if ok:
            self.lockedSearch = txt

    def updateTitle(self):
        selected = len(self.form.tableView.selectionModel().selectedRows())
        cur = len(self.model.cards)
        self.setWindowTitle(ngettext("Browser (%(cur)d card shown; %(sel)s)",
                                     "Browser (%(cur)d cards shown; %(sel)s)",
                                 cur) % {
            "cur": cur,
            "sel": ngettext("%d selected", "%d selected", selected) % selected
            })
        return selected

    def onReset(self, *args, **kwargs):
        self.editor.setNote(None)
        self.onSearch()

    # Table view & editor
    ######################################################################

    def setupTable(self):
        self.model = DataModel(self)
        self.form.tableView.setSortingEnabled(True)
        self.form.tableView.setModel(self.model)
        self.form.tableView.selectionModel()
        self.form.tableView.doubleClicked.connect(self._openPreview)
        self.form.tableView.setItemDelegate(StatusDelegate(self, self.model))
        sm=self.form.tableView.selectionModel()
        sm.selectionChanged.connect(self.onRowChanged)

    def setupEditor(self):
        import aqt.editor
        self.editor = aqt.editor.Editor(
            self.mw, self.form.fieldsArea, self)
        self.editor.stealFocus = False
        self.form.fieldsArea.setEditor(self.editor) #for resizeEvent

    def onRowChanged(self, current=None, previous=None):
        "Update current note and hide/show editor."
        update = self.updateTitle()
        chk = self.form.actionShowEdit.isChecked()
        show = chk and self.model.cards and update == 1
        self.form.splitter.widget(1).setVisible(not not show) #bool
        if not show:
            self.editor.setNote(None)
            self.singleCard = False
        else:
            self.toggleSplitOrientation()
            self.card = self.model.getCard(
                self.form.tableView.selectionModel().currentIndex())
            self.editor.setNote(self.card.note(reload=True))
            self.editor.card = self.card
            self.singleCard = True
        self._updateFlagsMenu()
        runHook("browser.rowChanged", self)
        self._renderPreview(True)
        self.toolbar.draw()

    def refreshCurrentCard(self, note):
        self.model.refreshNote(note)
        self._renderPreview(False)

    def refreshCurrentCardFilter(self, flag, note, fidx):
        self.refreshCurrentCard(note)
        return flag

    def currentRow(self):
        idx = self.form.tableView.selectionModel().currentIndex()
        return idx.row()

    # Headers & sorting
    ######################################################################

    def setupHeaders(self):
        vh = self.form.tableView.verticalHeader()
        hh = self.form.tableView.horizontalHeader()
        if not isWin:
            vh.hide()
            hh.show()
        restoreHeader(hh, "editor")
        hh.setHighlightSections(False)
        hh.setMinimumSectionSize(50)
        hh.setMovable(True)
        self.setColumnSizes()
        hh.setContextMenuPolicy(Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self.onHeaderContext)
        self.setSortIndicator()
        hh.sortIndicatorChanged.connect(self.onSortChanged)
        hh.sectionMoved.connect(self.onColumnMoved)

    def onSortChanged(self, idx, ord):
        ord = not not ord #enforce boolean value for ankidroid, https://github.com/ankitects/anki/pull/347
        type = self.model.activeCols[idx]
        noSort = ("question", "answer", "template", "deck", "note", "noteTags")
        if type in noSort:
            if type == "template":
                # fixme: change to 'card:1' to be clearer in future dev round
                showInfo(_("""\
This column can't be sorted on, but you can search for individual card types, \
such as 'card:Card 1'."""))
            elif type == "deck":
                showInfo(_("""\
This column can't be sorted on, but you can search for specific decks \
by clicking on one on the left."""))
            else:
                showInfo(_("Sorting on this column is not supported. Please "
                           "choose another."))
            type = self.col.conf['sortType']
        if self.col.conf['sortType'] != type:
            self.col.conf['sortType'] = type
            # default to descending for non-text fields
            if type == "noteFld":
                ord = not ord
            self.col.conf['sortBackwards'] = ord
            self.onSearch()
        else:
            if self.col.conf['sortBackwards'] != ord:
                self.col.conf['sortBackwards'] = ord
                self.model.reverse()
        self.setSortIndicator()

    def setSortIndicator(self):
        hh = self.form.tableView.horizontalHeader()
        type = self.col.conf['sortType']
        if type not in self.model.activeCols:
            hh.setSortIndicatorShown(False)
            return
        idx = self.model.activeCols.index(type)
        if self.col.conf['sortBackwards']:
            ord = Qt.DescendingOrder
        else:
            ord = Qt.AscendingOrder
        hh.blockSignals(True)
        hh.setSortIndicator(idx, ord)
        hh.blockSignals(False)
        hh.setSortIndicatorShown(True)

    def onHeaderContext(self, pos):
        gpos = self.form.tableView.mapToGlobal(pos)
        m = QMenu()
        for type, name in self.columns:
            a = m.addAction(name)
            a.setCheckable(True)
            a.setChecked(type in self.model.activeCols)
            a.toggled.connect(lambda b, t=type: self.toggleField(t))
        m.exec_(gpos)


    def toggleField(self, type):
        self.model.beginReset()
        if type in self.model.activeCols:
            if len(self.model.activeCols) < 2:
                return showInfo(_("You must have at least one column."))
            self.model.activeCols.remove(type)
            adding=False
        else:
            self.model.activeCols.append(type)
            adding=True
        # sorted field may have been hidden
        self.setSortIndicator()
        self.setColumnSizes()
        self.model.endReset()
        # if we added a column, scroll to it
        if adding:
            row = self.currentRow()
            idx = self.model.index(row, len(self.model.activeCols) - 1)
            self.form.tableView.scrollTo(idx)

    def setColumnSizes(self):
        hh = self.form.tableView.horizontalHeader()
        hh.setResizeMode(QHeaderView.Interactive)
        hh.setResizeMode(hh.logicalIndex(len(self.model.activeCols)-1),
                         QHeaderView.Stretch)
        # this must be set post-resize or it doesn't work
        hh.setCascadingSectionResizes(False)

    def onColumnMoved(self, a, b, c):
        self.setColumnSizes()

    # Filter tree
    ######################################################################

    def focusSidebar(self):
        self.sidebarTree.setFocus()

    def setupSidebar(self):
        # def onSidebarItemExpanded(idx):
            # item = idx.internalPointer()
        p = QPalette()
        p.setColor(QPalette.Base, p.window().color() or QColor("#d6dde0"))
        self.sidebarTree = SidebarTreeView(self.mw, self)
        self.sidebarTree.setPalette(p)
        self.sidebarTree.setUniformRowHeights(True)
        self.sidebarTree.setHeaderHidden(True)
        self.sidebarTree.setIndentation(15)
        # self.sidebarTree.expanded.connect(onSidebarItemExpanded) # type: ignore
        dw = self.form.sidebarDockWidget
        dw.setWidget(self.sidebarTree)
        dw.setFloating(False)
        dw.visibilityChanged.connect(self.onSidebarVisChanged) # type: ignore
        dw.setTitleBarWidget(QWidget())

    def onSidebarVisChanged(self, _visible):
        self.maybeRefreshSidebar()

    def maybeRefreshSidebar(self):
        if not self.showSidebar:
            self.form.sidebarDockWidget.setVisible(False)
        elif self.form.sidebarDockWidget.isVisible():
            # add slight delay to allow browser window to appear first
            def deferredDisplay():
                try:
                    root = self.buildTree()
                    model = SidebarModel(root)
                    self.sidebarTree.setModel(model)
                    model.expandWhereNeccessary(self.sidebarTree)
                except RuntimeError:
                    pass
            self.mw.progress.timer(5, deferredDisplay, False)

    def buildTree(self) -> SidebarItem:
        root = SidebarItem("", "")
        self._stdTree(root)
        self._favTree(root)
        self._decksTree(root)
        self._modelTree(root)
        self._userTagTree(root)
        return root

    def setFilter(self, *args):
        if len(args) == 1:
            txt = args[0]
        else:
            txt = ""
            items = []
            for c, a in enumerate(args):
                if c % 2 == 0:
                    txt += a + ":"
                else:
                    txt += a
                    if " " in txt or "(" in txt or ")" in txt:
                        txt = '"%s"' % txt
                    items.append(txt)
                    txt = ""
            txt = " ".join(items)
        if self.mw.app.keyboardModifiers() & Qt.AltModifier:
            txt = "-"+txt
        if self.mw.app.keyboardModifiers() & Qt.ControlModifier:
            cur = str(self.form.searchEdit.lineEdit().text())
            if cur and cur != self._searchPrompt:
                        txt = cur + " " + txt
        elif self.mw.app.keyboardModifiers() & Qt.ShiftModifier:
            cur = self.form.searchEdit.lineEdit().text()
            if cur:
                txt = cur + " or " + txt
        self.form.searchEdit.lineEdit().setText(txt)
        self.onSearch()

    def _filterFunc(self, *args):
        return lambda *, f=args: self.setFilter(*f)

    def _stdTree(self, root) -> None:
        tags = (
            (_("Whole Collection"), "ankibw", ""),
            (_("Current Deck"), "deck16", "deck:current"),
            (_("Added Today"), "view-pim-calendar.png", "added:1"),
            (_("Studied Today"), "view-pim-calendar.png", "rated:1"),
            (_("Again Today"), "view-pim-calendar.png", "rated:1:1"),
            (_("New"), "plus16.png", "is:new"),
            (_("Learning"), "stock_new_template_red.png", "is:learn"),
            (_("Review"), "clock16.png", "is:review"),
            (_("Due"), "clock16.png", "is:due"),
            (_("Marked"), "star16.png", "tag:marked"),
            (_("Suspended"), "media-playback-pause.png", "is:suspended"),
            (_("Leech"), "emblem-important.png", "tag:leech"))
        for name, icon, filt in tags:
            item = SidebarItem(
                name, ":/icons/{}".format(icon), self._filterFunc(filt))
            item.type="sys"
            item.fullname = name
            root.addChild(item)

    def _favTree(self, root):
        assert self.col
        tree=self.sidebarTree
        ico = ":/icons/anki-tag.png"
        icoOpt = self.col.conf.get('Blitzkrieg.icon_fav',True)

        saved = self.col.conf.get('savedFilters', {})
        if not saved:
            return
        favs_tree = {}
        for fav, filt in sorted(saved.items()):
            node = fav.split('::')
            lstIdx = len(node)-1
            ico = "emblem-favorite-dark.png"
            type = "fav"
            fname = color = None
            for idx, name in enumerate(node):
                if node[0]=='Pinned':
                    if idx==0:
                        type = "pin"
                    elif filt.startswith('"tag:'):
                        type = "pinTag"
                        ico = "anki-tag.png"
                        fname = filt[5:-1]
                    elif filt.startswith('"deck:'):
                        type = "pinDeck"
                        ico = "deck16.png"
                        fname = filt[6:-1]
                    elif filt.startswith('"dyn:'):
                        type = "pinDyn"
                        ico = "deck16.png"
                        fname = filt[5:-1]
                        filt='"deck'+filt[4:]

                item = None
                leaf_tag = '::'.join(node[0:idx + 1])
                if not favs_tree.get(leaf_tag):
                    parent = favs_tree['::'.join(node[0:idx])] if idx else root
                    exp = tree.node_state.get(type).get(leaf_tag,False)
                    item = SidebarItem(
                        name,
                        (":/icons/"+ico) if icoOpt or not idx or idx==lstIdx else None,
                        self._filterFunc(filt),
                        expanded=exp
                    )
                    parent.addChild(item)

                    item.type = type
                    item.fullname = fname or leaf_tag
                    item.favname = leaf_tag
                    if tree.marked[type].get(leaf_tag, False):
                        item.background=QBrush(Qt.yellow)
                    favs_tree[leaf_tag] = item

    def _userTagTree(self, root) -> None:
        assert self.col
        tree=self.sidebarTree
        ico = ":/icons/anki-tag.png"
        # ico = getIcon("tag.svg")
        icoOpt = self.col.conf.get('Blitzkrieg.icon_tag',True)
        rootNode = SidebarItem(
            "Tags", ico,
            expanded=tree.node_state.get("group").get('tag',True)
        )
        rootNode.type = "group"
        rootNode.fullname = "tag"
        root.addChild(rootNode)

        tags_tree = {}
        SORT = self.col.conf.get('Blitzkrieg.sort_tag',False)
        TAGS = sorted(self.col.tags.all(),
                key=lambda t: t.lower() if SORT else t)
        for t in TAGS:
            if t.lower() == "marked" or t.lower() == "leech":
                continue
            node = t.split('::')
            lstIdx = len(node)-1
            for idx, name in enumerate(node):
                leaf_tag = '::'.join(node[0:idx + 1])
                if not tags_tree.get(leaf_tag):
                    parent = tags_tree['::'.join(node[0:idx])] if idx else rootNode
                    exp = tree.node_state.get('tag').get(leaf_tag,False)
                    item = SidebarItem(
                        name, ico if icoOpt or idx==lstIdx else None,
                        self._filterFunc("tag",leaf_tag),
                        expanded=exp
                    )
                    parent.addChild(item)

                    item.type = "tag"
                    item.fullname = leaf_tag
                    if tree.found.get(item.type,{}).get(leaf_tag, False):
                        item.background=QBrush(Qt.cyan)
                    elif tree.marked['tag'].get(leaf_tag, False):
                        item.background=QBrush(Qt.yellow)
                    elif exp and '::' not in leaf_tag:
                        item.background=QBrush(QColor(0,0,10,10))
                    tags_tree[leaf_tag] = item

        rootNode.tooltip="Total: %d tags"%len(TAGS)

    def _decksTree(self, root) -> None:
        assert self.col
        tree=self.sidebarTree
        ico = ":/icons/deck16.png"
        # ico = getIcon("deck.svg")
        rootNode = SidebarItem(
            _("Decks"), ico,
            expanded=tree.node_state.get("group").get('deck',True)
        )
        rootNode.type = "group"
        rootNode.fullname = "deck"
        root.addChild(rootNode)

        SORT = self.col.conf.get('Blitzkrieg.sort_deck',False)
        grps = sorted(self.col.sched.deckDueTree(),
                key=lambda g: g[0].lower() if SORT else g[0])
        def fillGroups(rootNode, grps, head=""):
            for g in grps:
                item = SidebarItem(
                    g[0], ico,
                    lambda g=g: self.setFilter("deck", head+g[0]),
                    lambda expanded, g=g: self.mw.col.decks.collapseBrowser(g[1]),
                    not self.mw.col.decks.get(g[1]).get('browserCollapsed', False))
                rootNode.addChild(item)
                item.fullname = head + g[0] #name
                if self.mw.col.decks.isDyn(g[1]): #id
                    item.foreground = QBrush(Qt.blue)
                    item.type = "dyn"
                else:
                    if g[1]==1: #default deck
                        item.foreground = QBrush(Qt.darkRed)
                    item.type = "deck"
                if tree.found.get(item.type,{}).get(item.fullname, False):
                    item.background=QBrush(Qt.cyan)
                elif tree.marked[item.type].get(item.fullname, False):
                    item.background=QBrush(Qt.yellow)
                newhead = head + g[0]+"::"
                fillGroups(item, g[5], newhead)
        fillGroups(rootNode, grps)
        rootNode.tooltip="Total: %d decks"%self.col.decks.count()

    def _modelTree(self, root):
        assert self.col
        tree=self.sidebarTree
        ico = ":/icons/product_design.png"
        # ico = getIcon("notetype.svg")
        icoOpt = self.col.conf.get('Blitzkrieg.icon_model',True)
        rootNode = SidebarItem(
            _("Models"), ico,
            expanded=tree.node_state.get("group").get('model',False)
        )
        rootNode.type = "group"
        rootNode.fullname = "model"
        root.addChild(rootNode)

        models_tree = {}
        SORT = self.col.conf.get('Blitzkrieg.sort_model',False)
        MODELS = sorted(self.col.models.all(),
                key=lambda m: m["name"].lower() if SORT else m["name"])
        for m in MODELS:
            item = None
            mid=str(m['id'])
            node = m['name'].split('::')
            lstIdx = len(node)-1
            for idx, name in enumerate(node):
                leaf_model = '::'.join(node[0:idx + 1])
                if not models_tree.get(leaf_model) or idx==lstIdx: #last element, model names are not unique
                    parent = models_tree['::'.join(node[0:idx])] if idx else rootNode
                    exp = tree.node_state.get('model').get(leaf_model,False)

                    item = SidebarItem(
                        name, ico if icoOpt or idx==lstIdx else None,
                        self._filterFunc("mid", str(m['id'])),
                        expanded=exp
                    )
                    parent.addChild(item)
                    item.type = "model"
                    item.fullname = leaf_model
                    item.mid = mid

                    if tree.found.get(item.type,{}).get(leaf_model, False):
                        item.background=QBrush(Qt.cyan)
                    elif tree.marked['model'].get(leaf_model, False):
                        item.background=QBrush(Qt.yellow)
                    models_tree[leaf_model] = item

        rootNode.tooltip="Total: %d models"%len(MODELS)

    # Info
    ######################################################################

    def showCardInfo(self):
        html = []
        cids = self.selectedCards()
        if cids:
            for cid in cids[:25]:
                card = self.col.getCard(cid)
                s = self._getCardInfoHtml(card)
                html.append(s)
        elif self.card:
            s = self._getCardInfoHtml(self.card)
            html.append(s)
        else:
            return

        d = QDialog(self)
        l = QVBoxLayout()
        l.setMargin(0)
        w = AnkiWebView()
        l.addWidget(w)
        w.stdHtml("<br><hr><br>".join(html))
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        l.addWidget(bb)
        bb.rejected.connect(d.reject)
        d.setLayout(l)
        d.setWindowModality(Qt.WindowModal)
        d.resize(500, 400)
        restoreGeom(d, "revlog")
        d.exec_()
        saveGeom(d, "revlog")


    def _getCardInfoHtml(self, card):
        info, cs = self._cardInfoData(card)
        reps = self._revlogData(cs)
        return "<div>" + info + "<p>" + reps + "</div>"


    def _cardInfoData(self, card=None):
        if not card:
            card = self.card
        from anki.stats import CardStats
        cs = CardStats(self.col, card)
        rep = cs.report()
        m = card.model()
        rep = """
<div style='width: 400px; margin: 0 auto 0;
border: 1px solid #000; padding: 3px; '>%s</div>""" % rep
        return rep, cs

    def _revlogData(self, cs, card=None):
        if not card:
            card = self.card
        entries = self.mw.col.db.all(
            "select id/1000.0, ease, ivl, factor, time/1000.0, type "
            "from revlog where cid = ?", card.id)
        if not entries:
            return ""
        s = "<table width=100%%><tr><th align=left>%s</th>" % _("Date")
        s += ("<th align=right>%s</th>" * 5) % (
            _("Type"), _("Rating"), _("Interval"), _("Ease"), _("Time"))
        cnt = 0
        for (date, ease, ivl, factor, taken, type) in reversed(entries):
            cnt += 1
            s += "<tr><td>%s</td>" % time.strftime(_("<b>%Y-%m-%d</b> @ %H:%M"),
                                                   time.localtime(date))
            tstr = [_("Learn"), _("Review"), _("Relearn"), _("Filtered"),
                    _("Resched")][type]
            import anki.stats as st
            fmt = "<span style='color:%s'>%s</span>"
            if type == 0:
                tstr = fmt % (st.colLearn, tstr)
            elif type == 1:
                tstr = fmt % (st.colMature, tstr)
            elif type == 2:
                tstr = fmt % (st.colRelearn, tstr)
            elif type == 3:
                tstr = fmt % (st.colCram, tstr)
            else:
                tstr = fmt % ("#000", tstr)
            if ease == 1:
                ease = fmt % (st.colRelearn, ease)
            if ivl == 0:
                ivl = _("0d")
            elif ivl > 0:
                ivl = fmtTimeSpan(ivl*86400, short=True)
            else:
                ivl = cs.time(-ivl)
            s += ("<td align=right>%s</td>" * 5) % (
                tstr,
                ease, ivl,
                "%d%%" % (factor/10) if factor else "",
                cs.time(taken)) + "</tr>"
        s += "</table>"
        if cnt < card.reps:
            s += _("""\
Note: Some of the history is missing. For more information, \
please see the browser documentation.""")
        return s

    # Menu helpers
    ######################################################################

    def selectedCards(self):
        return [self.model.cards[idx.row()] for idx in
                self.form.tableView.selectionModel().selectedRows()]

    def selectedNotes(self):
        return self.col.db.list("""
select distinct nid from cards
where id in %s""" % ids2str(
    [self.model.cards[idx.row()] for idx in
    self.form.tableView.selectionModel().selectedRows()]))

    def selectedNotesAsCards(self):
        return self.col.db.list(
            "select id from cards where nid in (%s)" %
            ",".join([str(s) for s in self.selectedNotes()]))

    def oneModelNotes(self):
        sf = self.selectedNotes()
        if not sf:
            return
        mods = self.col.db.scalar("""
select count(distinct mid) from notes
where id in %s""" % ids2str(sf))
        if mods > 1:
            showInfo(_("Please select cards from only one note type."))
            return
        return sf

    # Misc menu options
    ######################################################################

    def onChangeModel(self):
        nids = self.oneModelNotes()
        if nids:
            ChangeModel(self, nids)

    # def cram(self):
        # return showInfo("not yet implemented")
        # self.close()
        # self.mw.onCram(self.selectedCards())

    # Preview
    ######################################################################

    # def onTogglePreview(self):
        # if self._previewWindow:
            # self._closePreview()
        # else:
            # self._openPreview()

    def _openPreview(self):
        if self._previewWindow:
            return

        c = self.connect
        self._previewState = "question"
        self._previewWindow = QDialog(self, Qt.Window)
        self._previewWindow.setWindowTitle(_("Preview"))

        c(self._previewWindow, SIGNAL("finished(int)"), self._onPreviewFinished)
        vbox = QVBoxLayout()
        vbox.setMargin(0)
        self._previewWeb = AnkiWebView()
        vbox.addWidget(self._previewWeb)
        bbox = QDialogButtonBox()

        self._previewReplay = bbox.addButton(_("Replay"), QDialogButtonBox.ActionRole)
        self._previewReplay.setAutoDefault(False)
        self._previewReplay.setShortcut(QKeySequence("R"))
        self._previewReplay.setToolTip(_("Shortcut key: %s" % "R"))

        self._previewStop = bbox.addButton(_("Stop"), QDialogButtonBox.ActionRole)
        self._previewStop.setAutoDefault(False)

        self._previewPrev = bbox.addButton("<", QDialogButtonBox.ActionRole)
        self._previewPrev.setAutoDefault(False)
        self._previewPrev.setShortcut(QKeySequence("Left"))
        self._previewPrev.setToolTip(_("Shortcut key: Left arrow"))

        self._previewNext = bbox.addButton(">", QDialogButtonBox.ActionRole)
        self._previewNext.setAutoDefault(True)
        self._previewNext.setShortcut(QKeySequence("Right"))
        self._previewNext.setToolTip(_("Shortcut key: Right arrow or Enter"))

        c(self._previewPrev, SIGNAL("clicked()"), self._onPreviewPrev)
        c(self._previewNext, SIGNAL("clicked()"), self._onPreviewNext)
        c(self._previewStop, SIGNAL("clicked()"), clearAudioQueue)
        c(self._previewReplay, SIGNAL("clicked()"), self._onReplayAudio)

        vbox.addWidget(bbox)
        self._previewWindow.setLayout(vbox)
        self._previewWindow.setMinimumSize(QSize(250, 200))
        if self.mw.pm.profile.get("previewGeom"):
            restoreGeom(self._previewWindow, "preview")
        else:
            self._previewWindow.resize(400, 300)
        self._previewWindow.show()
        self._renderPreview(True)
        self._previewWeb.setLinkHandler(self._linkHandler)

    def _linkHandler(self, url):
        if url.startswith("ankiplay:"):
            (cmd, arg) = url.split(":", 1)
            clearAudioQueue()
            play(arg)

    def _onPreviewFinished(self, ok):
        try:
            saveGeom(self._previewWindow, "preview")
            self.mw.progress.timer(100, self._onClosePreview, False)
            # self.form.previewButton.setChecked(False)
        except TypeError: pass

    def _onPreviewPrev(self):
        if self._previewState == "question":
            self._previewState = "answer"
            self._renderPreview()
        else:
            self.onPreviousCard()
        self._updatePreviewButtons()

    def _onPreviewNext(self):
        if self._previewState == "question":
            self._previewState = "answer"
            self._renderPreview()
        else:
            self.onNextCard()
        self._updatePreviewButtons()

    def _onReplayAudio(self):
        self.mw.reviewer.replayAudio(self)

    def _updatePreviewButtons(self):
        if not self._previewWindow:
            return
        canBack = self.currentRow() >  0 or self._previewState == "question"
        self._previewPrev.setEnabled(not not (self.singleCard and canBack))
        canForward = self.currentRow() < self.model.rowCount(None) - 1 or \
                     self._previewState == "question"
        self._previewNext.setEnabled(not not (self.singleCard and canForward))

    def _closePreview(self):
        if self._previewWindow:
            self._previewWindow.close()
            self._onClosePreview()

    def _onClosePreview(self):
        self._previewWindow = self._previewPrev = self._previewNext = None

    def _renderPreview(self, cardChanged=False):
        if not self._previewWindow:
            return
        c = self.model.getCard(
            self.form.tableView.selectionModel().currentIndex())
        if not c:
            txt = _("(please select 1 card)")
            self._previewWeb.stdHtml(txt)
            self._updatePreviewButtons()
            return
        self._updatePreviewButtons()
        if cardChanged:
            self._previewState = "question"
        # need to force reload even if answer
        txt = c.q(reload=True)
        if self._previewState == "answer":
            txt = c.a()
        txt = re.sub("\[\[type:[^]]+\]\]", "", txt)
        ti = lambda x: x
        txt = ti(mungeQA(self.col, txt))
        txt = runFilter("prepareQA", txt, c,
                        "preview"+self._previewState.capitalize())
        base = getBase(self.mw.col)
        self._previewWeb.stdHtml(
            txt, self.mw.reviewer._styles(),
            bodyClass="card card%d" % (c.ord+1), head=base)
        clearAudioQueue()
        # if self.mw.reviewer.autoplay(c):
            # playFromText(txt)

    # Card deletion
    ######################################################################

    def deleteNotes(self):
        nids = self.selectedNotes()
        self._deleteNotes(nids)

    def _deleteNotes(self, nids):
        if not nids:
            return
        self.mw.checkpoint(_("Delete Notes"))
        self.model.beginReset()
        # figure out where to place the cursor after the deletion
        curRow = self.form.tableView.selectionModel().currentIndex().row()
        selectedRows = [i.row() for i in
                self.form.tableView.selectionModel().selectedRows()]
        if min(selectedRows) < curRow < max(selectedRows):
            # last selection in middle; place one below last selected item
            move = sum(1 for i in selectedRows if i > curRow)
            newRow = curRow - move
        elif max(selectedRows) <= curRow:
            # last selection at bottom; place one below bottommost selection
            newRow = max(selectedRows) - len(nids) + 1
        else:
            # last selection at top; place one above topmost selection
            newRow = min(selectedRows) - 1
        self.col.remNotes(nids)
        self.onSearch(reset=False)
        if len(self.model.cards):
            newRow = min(newRow, len(self.model.cards) - 1)
            newRow = max(newRow, 0)
            self.model.focusedCard = self.model.cards[newRow]
        self.model.endReset()
        self.mw.requireReset()
        tooltip(ngettext("%d note deleted.", "%d notes deleted.", len(nids)) % len(nids))

    # Deck change
    ######################################################################

    def setDeck(self):
        from aqt.studydeck import StudyDeck
        cids = self.selectedCards()
        if not cids:
            return
        did = self.mw.col.db.scalar(
            "select did from cards where id = ?", cids[0])
        current=self.mw.col.decks.get(did)['name']
        ret = StudyDeck(
            self.mw, current=current, accept=_("Move Cards"),
            title=_("Change Deck"), parent=self)
        if not ret.name:
            return
        did = self.col.decks.id(ret.name)
        deck = self.col.decks.get(did)
        if deck['dyn']:
            showWarning(_("Cards can't be manually moved into a filtered deck."))
            return
        self.model.beginReset()
        self.mw.checkpoint(_("Change Deck"))
        mod = intTime()
        usn = self.col.usn()
        # normal cards
        scids = ids2str(cids)
        # remove any cards from filtered deck first
        self.col.sched.remFromDyn(cids)
        # then move into new deck
        self.col.db.execute("""
update cards set usn=?, mod=?, did=? where id in """ + scids,
                            usn, mod, did)
        self.model.endReset()
        self.mw.requireReset()

    # Tags
    ######################################################################

    def addTags(self, tags=None, label=None, prompt=None, func=None):
        nids = self.selectedNotes()
        if not nids:
            showInfo("No card selected")
            return
        if label is None:
            label = _("Add Tags")
        if not tags:
            d = QDialog(self)
            d.setObjectName("DeleteTags")
            d.setWindowTitle(label)
            d.resize(360, 340)
            tagTree = TagTreeWidget(self,d)
            tagTree.addTags(nids)
            line = TagEdit(d)
            line.setCol(self.col)
            layout = QVBoxLayout(d)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(QLabel(_("""\
Select tags and close dialog: \
Yellow is for existing tags. \
Green items will be added.""")))
            layout.addWidget(tagTree)
            layout.addWidget(QLabel(_("Add Extra Tags:")))
            layout.addWidget(line)
            d.exec_()

            txt=line.text()
            tags=[txt] if txt else []
            for k,v in tagTree.node.items():
                if v: tags.append(k)
            tags=" ".join(tags)

        if tags:
            self.mw.checkpoint(label)
            self.model.beginReset()
            self.col.tags.bulkAdd(nids,tags)
            self.model.endReset()
            self.mw.requireReset()

    def deleteTags(self, tags=None, label=None):
        nids = self.selectedNotes()
        if not nids:
            showInfo("No card selected")
            return
        if label is None:
            label = _("Delete Tags")
        if not tags:
            d = QDialog(self)
            d.setObjectName("DeleteTags")
            d.setWindowTitle(label)
            d.resize(360, 340)
            tagTree = TagTreeWidget(self,d)
            tagTree.removeTags(nids)
            layout = QVBoxLayout(d)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(QLabel(_("""\
Select tags and close dialog. \
Red items will be deleted.""")))
            layout.addWidget(tagTree)
            d.exec_()

            tags=[]
            for k,v in tagTree.node.items():
                if v:
                    # tags.append(k+'::*') #inc subtags?
                    tags.append(k)
            tags=" ".join(tags)

        if tags:
            self.mw.checkpoint(label)
            self.model.beginReset()
            self.col.tags.bulkRem(nids,tags)
            self.col.tags.registerNotes()
            self.model.endReset()
            self.mw.requireReset()

    # Flags, Suspending and marking
    ######################################################################

    def onSetFlag(self, n):
        cids = self.selectedCards()
        if not cids:
            showInfo("No card selected")
            return
        try:
            card = self.model.getCard(
                self.form.tableView.selectionModel().currentIndex())
        except IndexError:
            return
        # flag needs toggling off?
        if n == card.userFlag():
            n = 0
        self.col.setUserFlag(n, cids)
        self.model.reset()
        self.form.tableView.clearSelection()

    def _updateFlagsMenu(self):
        flag = self.card and self.card.userFlag()
        flag = flag or 0

        f = self.form
        flagActions = [f.actionRed_Flag,
                       f.actionOrange_Flag,
                       f.actionGreen_Flag,
                       f.actionBlue_Flag]

        for c, act in enumerate(flagActions):
            act.setChecked(flag == c+1)

        # qtMenuShortcutWorkaround(self.form.menuFlag)

    def isSuspended(self):
        return not not (self.card and self.card.queue == -1)

    def onSuspend(self, sus=None):
        if sus is None:
            sus = not self.isSuspended()
        # focus lost hook may not have chance to fire
        self.editor.saveNow()
        c = self.selectedCards()
        if sus:
            self.col.sched.suspendCards(c)
        else:
            self.col.sched.unsuspendCards(c)
        self.model.reset()
        self.mw.requireReset()

    def isMarked(self):
        return not not (self.card and self.card.note().hasTag("Marked"))

    def onMark(self, mark=None):
        if mark is None:
            self.card = self.model.getCard(
                self.form.tableView.selectionModel().currentIndex())
            mark = not self.isMarked()
        if mark:
            self.addTags(tags="marked", label=False)
        else:
            self.deleteTags(tags="marked", label=False)

    # Repositioning
    ######################################################################

    def reposition(self):
        cids = self.selectedCards()
        cids2 = self.col.db.list(
            "select id from cards where type = 0 and id in " + ids2str(cids))
        if not cids2:
            return showInfo(_("Only new cards can be repositioned."))
        d = QDialog(self)
        d.setWindowModality(Qt.WindowModal)
        frm = aqt.forms.reposition.Ui_Dialog()
        frm.setupUi(d)
        (pmin, pmax) = self.col.db.first(
            "select min(due), max(due) from cards where type=0 and odid=0")
        pmin = pmin or 0
        pmax = pmax or 0
        txt = _("Queue top: %d") % pmin
        txt += "\n" + _("Queue bottom: %d") % pmax
        frm.label.setText(txt)
        if not d.exec_():
            return
        self.model.beginReset()
        self.mw.checkpoint(_("Reposition"))
        self.col.sched.sortCards(
            cids, start=frm.start.value(), step=frm.step.value(),
            shuffle=frm.randomize.isChecked(), shift=frm.shift.isChecked())
        self.onSearch(reset=False)
        self.mw.requireReset()
        self.model.endReset()

    # Rescheduling
    ######################################################################

    def reschedule(self):
        d = QDialog(self)
        d.setWindowModality(Qt.WindowModal)
        frm = aqt.forms.reschedule.Ui_Dialog()
        frm.setupUi(d)
        if not d.exec_():
            return
        self.model.beginReset()
        self.mw.checkpoint(_("Reschedule"))
        if frm.asNew.isChecked():
            self.col.sched.forgetCards(self.selectedCards())
        else:
            fmin = frm.min.value()
            fmax = frm.max.value()
            fmax = max(fmin, fmax)
            self.col.sched.reschedCards(
                self.selectedCards(), fmin, fmax)
        self.onSearch(reset=False)
        self.mw.requireReset()
        self.model.endReset()

    # Edit: selection
    ######################################################################

    def selectNotes(self):
        nids = self.selectedNotes()
        self.form.searchEdit.lineEdit().setText("nid:"+",".join([str(x) for x in nids]))
        # clear the selection so we don't waste energy preserving it
        tv = self.form.tableView
        tv.selectionModel().clear()
        self.onSearch()
        tv.selectAll()

    def invertSelection(self):
        sm = self.form.tableView.selectionModel()
        items = sm.selection()
        self.form.tableView.selectAll()
        sm.select(items, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)

    # Edit: undo
    ######################################################################

    def setupHooks(self):
        addHook("undoState", self.onUndoState)
        addHook("reset", self.onReset)
        addHook("addedNote", self.onReset)
        addHook("editTimer", self.refreshCurrentCard)
        addHook("editFocusLost", self.refreshCurrentCardFilter)
        for t in "newTag", "newModel", "newDeck":
            addHook(t, self.maybeRefreshSidebar)

    def teardownHooks(self):
        remHook("reset", self.onReset)
        remHook("addedNote", self.onReset)
        remHook("editTimer", self.refreshCurrentCard)
        remHook("editFocusLost", self.refreshCurrentCardFilter)
        remHook("undoState", self.onUndoState)
        for t in "newTag", "newModel", "newDeck":
            remHook(t, self.maybeRefreshSidebar)

    def onUndoState(self, on):
        self.form.actionUndo.setEnabled(on)
        if on:
            self.form.actionUndo.setText(self.mw.form.actionUndo.text())
        # self.maybeRefreshSidebar()



    # Edit: replacing
    ######################################################################

    def onFindReplace(self):
        sf = self.selectedNotes()
        if not sf:
            return
        fields = anki.find.fieldNamesForNotes(self.col, sf)
        d = QDialog(self)
        frm = aqt.forms.findreplace.Ui_Dialog()
        frm.setupUi(d)
        d.setWindowModality(Qt.WindowModal)
        frm.field.addItems([_("All Fields")] + fields)
        restoreGeom(d, "findreplace")
        r = d.exec_()
        saveGeom(d, "findreplace")
        if not r:
            return
        if frm.field.currentIndex() == 0:
            field = None
        else:
            field = fields[frm.field.currentIndex()-1]
        self.mw.checkpoint(_("Find and Replace"))
        self.mw.progress.start()
        self.model.beginReset()
        try:
            changed = self.col.findReplace(sf,
                                            frm.find.text(),
                                            frm.replace.text(),
                                            frm.re.isChecked(),
                                            field,
                                            frm.ignoreCase.isChecked())
        except sre_constants.error:
            showInfo(_("Invalid regular expression."), parent=self)
            return
        else:
            self.onSearch()
            self.mw.requireReset()
        finally:
            self.model.endReset()
            self.mw.progress.finish()
        showInfo(ngettext(
            "%(a)d of %(b)d note updated",
            "%(a)d of %(b)d notes updated", len(sf)) % {
                'a': changed,
                'b': len(sf),
            })

    # Edit: finding dupes
    ######################################################################

    def onFindDupes(self):
        d = QDialog(self)
        frm = aqt.forms.finddupes.Ui_Dialog()
        frm.setupUi(d)
        restoreGeom(d, "findDupes")
        fields = anki.find.fieldNames(self.col, downcase=False)
        fields = sorted(fields, key=lambda x: x.lower())
        frm.fields.addItems(fields)
        self._dupesButton = None
        self._delDupesButton = None
        # links
        frm.webView.page().setLinkDelegationPolicy(
            QWebPage.DelegateAllLinks)
        self.connect(frm.webView,
                     SIGNAL("linkClicked(QUrl)"),
                     self.dupeLinkClicked)
        def onFin(code):
            saveGeom(d, "findDupes")
        d.finished.connect(onFin)
        def onClick():
            field = fields[frm.fields.currentIndex()]
            self.duplicatesReport(frm.webView, field, frm.search.text(), frm)
        search = frm.buttonBox.addButton(
            _("Search"), QDialogButtonBox.ActionRole)
        search.clicked.connect(onClick)
        d.show()

    def duplicatesReport(self, web, fname, search, frm):
        self.mw.progress.start()
        try:
            res = self.mw.col.findDupes(fname, search)
            if not self._dupesButton:
                self._dupesButton = frm.buttonBox.addButton(
                    _("Tag Duplicates"), QDialogButtonBox.ActionRole)
                self._delDupesButton = frm.buttonBox.addButton(
                    _("Del All Dups"), QDialogButtonBox.ActionRole)
            self._dupesButton.clicked.connect(lambda: self._onTagDupes(res))
            self._delDupesButton.clicked.connect(lambda: self._onDelDupes(res))

            t = "<html><body>"
            groups = len(res)
            notes = sum(len(r[1]) for r in res)
            part1 = ngettext("%d group", "%d groups", groups) % groups
            part2 = ngettext("%d note", "%d notes", notes) % notes
            t += _("Found %(a)s across %(b)s.") % dict(a=part1, b=part2)
            t += "<p><ol>"
            for val, nids in res:
                n = ",".join(str(id) for id in nids)
                t += '<li><a href="%s">%s</a>: %s &nbsp; [<a href="%s">del dups</a>]</li>' % (
                    "nid:" + n,
                    ngettext("%d note", "%d notes", len(nids)) % len(nids),
                    cgi.escape(val),
                    "del:" + n,
                )
            t += "</ol>"
            t += "</body></html>"
            web.setHtml(t)
        finally:
            self.mw.progress.finish()

    def _onDelDupes(self, res):
        if not res:
            return
        toDelArr = []
        for _, nids in res:
            toDelArr.extend(nids[1:])
        self._deleteNotes(toDelArr)

    def _onTagDupes(self, res):
        if not res:
            return
        self.mw.checkpoint(_("Tag Duplicates"))
        self.mw.progress.start()
        self.model.beginReset()
        try:
            nids = set()
            for s, nidlist in res:
                nids.update(nidlist)
            self.col.tags.bulkAdd(nids, _("duplicate"))
        finally:
            self.model.endReset()
            self.mw.progress.finish()
            self.mw.requireReset()
        tooltip(_("Notes tagged."))

    def dupeLinkClicked(self, link):
        link = link.toString()
        if link.startswith("del:"):
            toDelArr = link.split(",")[1:]
            self._deleteNotes(toDelArr)
        else: #starts w/ nid:
            self.form.searchEdit.lineEdit().setText(link)
            self.onSearch()
            self.onNote()

    # Jumping
    ######################################################################

    def _moveCur(self, dir=None, idx=None):
        if not self.model.cards:
            return
        self.editor.saveNow()
        tv = self.form.tableView
        if idx is None:
            idx = tv.moveCursor(dir, self.mw.app.keyboardModifiers())
        tv.selectionModel().clear()
        tv.setCurrentIndex(idx)

    def onPreviousCard(self):
        f = self.editor.currentField
        self._moveCur(QAbstractItemView.MoveUp)
        self.editor.web.setFocus()
        self.editor.web.eval("focusField(%d)" % f)

    def onNextCard(self):
        f = self.editor.currentField
        self._moveCur(QAbstractItemView.MoveDown)
        self.editor.web.setFocus()
        self.editor.web.eval("focusField(%d)" % f)

    def onFirstCard(self):
        sm = self.form.tableView.selectionModel()
        idx = sm.currentIndex()
        self._moveCur(None, self.model.index(0, 0))
        if not self.mw.app.keyboardModifiers() & Qt.ShiftModifier:
            return
        idx2 = sm.currentIndex()
        item = QItemSelection(idx2, idx)
        sm.select(item, QItemSelectionModel.SelectCurrent|
                  QItemSelectionModel.Rows)

    def onLastCard(self):
        sm = self.form.tableView.selectionModel()
        idx = sm.currentIndex()
        self._moveCur(
            None, self.model.index(len(self.model.cards) - 1, 0))
        if not self.mw.app.keyboardModifiers() & Qt.ShiftModifier:
            return
        idx2 = sm.currentIndex()
        item = QItemSelection(idx, idx2)
        sm.select(item, QItemSelectionModel.SelectCurrent|
                  QItemSelectionModel.Rows)

    def onFind(self):
        self.form.searchEdit.setFocus()
        self.form.searchEdit.lineEdit().selectAll()

    def onNote(self):
        self.editor.focus()
        self.editor.web.setFocus()
        self.editor.web.eval("focusField(0);")

    def onCardList(self):
        self.form.tableView.setFocus()

    def focusCid(self, cid):
        try:
            row = self.model.cards.index(cid)
        except:
            return
        self.form.tableView.selectRow(row)

# Change model dialog
######################################################################

class ChangeModel(QDialog):

    def __init__(self, browser, nids):
        QDialog.__init__(self, browser)
        self.browser = browser
        self.nids = nids
        self.oldModel = browser.card.note().model()
        self.form = aqt.forms.changemodel.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowModality(Qt.WindowModal)
        self.setup()
        restoreGeom(self, "changeModel")
        addHook("reset", self.onReset)
        addHook("currentModelChanged", self.onReset)
        self.exec_()

    def setup(self):
        # maps
        self.flayout = QHBoxLayout()
        self.flayout.setMargin(0)
        self.fwidg = None
        self.form.fieldMap.setLayout(self.flayout)
        self.tlayout = QHBoxLayout()
        self.tlayout.setMargin(0)
        self.twidg = None
        self.form.templateMap.setLayout(self.tlayout)
        if self.style().objectName() == "gtk+":
            # gtk+ requires margins in inner layout
            self.form.verticalLayout_2.setContentsMargins(0, 11, 0, 0)
            self.form.verticalLayout_3.setContentsMargins(0, 11, 0, 0)
        # model chooser
        import aqt.modelchooser
        self.oldModel = self.browser.col.models.get(
            self.browser.col.db.scalar(
                "select mid from notes where id = ?", self.nids[0]))
        self.form.oldModelLabel.setText(self.oldModel['name'])
        self.modelChooser = aqt.modelchooser.ModelChooser(
            self.browser.mw, self.form.modelChooserWidget, label=False)
        self.modelChooser.models.setFocus()
        self.modelChanged(self.browser.mw.col.models.current())
        self.pauseUpdate = False

    def onReset(self):
        self.modelChanged(self.browser.col.models.current())

    def modelChanged(self, model):
        self.targetModel = model
        self.rebuildTemplateMap()
        self.rebuildFieldMap()

    def rebuildTemplateMap(self, key=None, attr=None):
        if not key:
            key = "t"
            attr = "tmpls"
        map = getattr(self, key + "widg")
        lay = getattr(self, key + "layout")
        src = self.oldModel[attr]
        dst = self.targetModel[attr]
        if map:
            lay.removeWidget(map)
            map.deleteLater()
            setattr(self, key + "MapWidget", None)
        map = QWidget()
        l = QGridLayout()
        combos = []
        targets = [x['name'] for x in dst] + [_("Nothing")]
        indices = {}
        for i, x in enumerate(src):
            l.addWidget(QLabel(_("Change %s to:") % x['name']), i, 0)
            cb = QComboBox()
            cb.addItems(targets)
            idx = min(i, len(targets)-1)
            cb.setCurrentIndex(idx)
            indices[cb] = idx
            cb.currentIndexChanged.connect(
                lambda i, cb=cb, key=key: self.onComboChanged(i, cb, key))
            combos.append(cb)
            l.addWidget(cb, i, 1)
        map.setLayout(l)
        lay.addWidget(map)
        setattr(self, key + "widg", map)
        setattr(self, key + "layout", lay)
        setattr(self, key + "combos", combos)
        setattr(self, key + "indices", indices)

    def rebuildFieldMap(self):
        return self.rebuildTemplateMap(key="f", attr="flds")

    def onComboChanged(self, i, cb, key):
        indices = getattr(self, key + "indices")
        if self.pauseUpdate:
            indices[cb] = i
            return
        combos = getattr(self, key + "combos")
        if i == cb.count() - 1:
            # set to 'nothing'
            return
        # find another combo with same index
        for c in combos:
            if c == cb:
                continue
            if c.currentIndex() == i:
                self.pauseUpdate = True
                c.setCurrentIndex(indices[cb])
                self.pauseUpdate = False
                break
        indices[cb] = i

    def getTemplateMap(self, old=None, combos=None, new=None):
        if not old:
            old = self.oldModel['tmpls']
            combos = self.tcombos
            new = self.targetModel['tmpls']
        map = {}
        for i, f in enumerate(old):
            idx = combos[i].currentIndex()
            if idx == len(new):
                # ignore
                map[f['ord']] = None
            else:
                f2 = new[idx]
                map[f['ord']] = f2['ord']
        return map

    def getFieldMap(self):
        return self.getTemplateMap(
            old=self.oldModel['flds'],
            combos=self.fcombos,
            new=self.targetModel['flds'])

    def cleanup(self):
        remHook("reset", self.onReset)
        remHook("currentModelChanged", self.onReset)
        self.modelChooser.cleanup()
        saveGeom(self, "changeModel")

    def reject(self):
        self.cleanup()
        return QDialog.reject(self)

    def accept(self):
        # check maps
        fmap = self.getFieldMap()
        cmap = self.getTemplateMap()
        if any(True for c in cmap.values() if c is None):
            if not askUser(_("""\
Any cards mapped to nothing will be deleted. \
If a note has no remaining cards, it will be lost. \
Are you sure you want to continue?""")):
                return
        QDialog.accept(self)
        self.browser.mw.checkpoint(_("Change Note Type"))
        b = self.browser
        b.mw.progress.start()
        b.model.beginReset()
        mm = b.mw.col.models
        mm.change(self.oldModel, self.nids, self.targetModel, fmap, cmap)
        b.onSearch(reset=False)
        b.model.endReset()
        b.mw.progress.finish()
        b.mw.reset()
        self.cleanup()


# Toolbar
######################################################################

class BrowserToolbar(Toolbar):
    _css = ccbc.css.browser_toolbar

    def __init__(self, mw, web, browser):
        self.browser = browser
        Toolbar.__init__(self, mw, web)

    def draw(self):
        mark = self.browser.isMarked()
        pause = self.browser.isSuspended()
        def borderImg(link, icon, on, title, tooltip=None):
            if icon:
                icon = '<img style="padding: 1px;" valign=bottom src="qrc:/icons/%s.png">'%icon
            else:
                icon = '<span id="%s">%s</span>'%(link, ccbc.html.flag)
            if on:
                fmt = '''\
<a class=hitem title="%s" href="%s">%s %s</a>'''
            else:
                fmt = '''\
<a class=hitem title="%s" href="%s">%s %s</a>'''
            return fmt % (tooltip or title, link, icon, title)
        right = "<div>"
        right += borderImg("add", "add16", False, "",
                       shortcut(_("Add Note (Ctrl+E)")))
        right += borderImg("info", "info", False, "",
                       shortcut(_("Card Info (Ctrl+Shift+I)")))
        right += borderImg("mark", "star16", mark, "",
                       shortcut(_("Mark Note (Ctrl+K)")))
        right += borderImg("pause", "pause16", pause, "",
                       shortcut(_("Suspend Card (Ctrl+J)")))
        right += borderImg("flag1", "", False, "",
                       shortcut(_("Flag Card Red (Ctrl+1)")))
        right += borderImg("flag2", "", False, "",
                       shortcut(_("Flag Card Orange (Ctrl+2)")))
        right += borderImg("flag3", "", False, "",
                       shortcut(_("Flag Card Green (Ctrl+3)")))
        right += borderImg("flag4", "", False, "",
                       shortcut(_("Flag Card Blue (Ctrl+4)")))
        right += borderImg("setDeck", "deck16", False, _("Change Deck"),
                           shortcut(_("Move To Deck (Ctrl+D)")))
        right += borderImg("addtag", "addtag16", False, _("Add Tags"),
                       shortcut(_("Bulk Add Tags (Ctrl+Shift+T)")))
        right += borderImg("deletetag", "deletetag16", False,
                           _("Remove Tags"), shortcut(_(
                               "Bulk Remove Tags (Ctrl+Alt+T)")))
        right += borderImg("delete", "delete16", False, _("Delete"))
        right += "</div>"
        self.web.page().currentFrame().setScrollBarPolicy(
            Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.web.stdHtml(self._body%right, self._css)

    # Link handling
    ######################################################################

    def _linkHandler(self, l):
        if l == "anki":
            self.showMenu()
        elif l  == "add":
            self.browser.mw.onAddCard()
        elif l  == "delete":
            self.browser.deleteNotes()
        elif l  == "setDeck":
            self.browser.setDeck()
        # icons
        elif l  == "info":
            self.browser.showCardInfo()
        elif l == "mark":
            self.browser.onMark()
        elif l == "pause":
            self.browser.onSuspend()
        elif l == "flag1":
            self.browser.onSetFlag(1)
        elif l == "flag2":
            self.browser.onSetFlag(2)
        elif l == "flag3":
            self.browser.onSetFlag(3)
        elif l == "flag4":
            self.browser.onSetFlag(4)
        elif l == "addtag":
            self.browser.addTags()
        elif l == "deletetag":
            self.browser.deleteTags()
        elif l.startswith("ankiplay:"):
            (cmd, arg) = l.split(":", 1)
            clearAudioQueue()
            play(arg)

# Favourites button
######################################################################
class FavouritesLineEdit(QLineEdit):
    buttonClicked = pyqtSignal(bool)

    def __init__(self, mw, browser, parent=None):
        super(FavouritesLineEdit, self).__init__(parent)
        self.mw = mw
        self.browser = browser
        # add conf if missing
        if 'savedFilters' not in self.mw.col.conf:
            self.mw.col.conf['savedFilters'] = {}
        self.button = QToolButton(self)
        self.button.setStyleSheet('border: 0px;')
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.buttonClicked.emit)
        self.setIcon(':/icons/emblem-favorite-off.png')
        # flag to raise save or delete dialog on button click
        self.doSave = True
        # name of current saved filter (if query matches)
        self.name = None
        self.buttonClicked.connect(self.onClicked)
        self.textChanged.connect(self.updateButton)

    def resizeEvent(self, event):
        buttonSize = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.button.move(self.rect().right() - frameWidth - buttonSize.width(),
                         (self.rect().bottom() - buttonSize.height() + 1) / 2)
        self.setTextMargins(0, 0, buttonSize.width() * 1.5, 0)
        super(FavouritesLineEdit, self).resizeEvent(event)

    def setIcon(self, path):
        self.button.setIcon(QIcon(path))

    def setText(self, txt):
        super(FavouritesLineEdit, self).setText(txt)
        self.updateButton()
        
    def updateButton(self, reset=True):
        # If search text is a saved query, switch to the delete button.
        # Otherwise show save button.
        txt = self.text().strip()
        for key, value in self.mw.col.conf['savedFilters'].items():
            if txt == value:
                self.doSave = False
                self.name = key
                self.setIcon(QIcon(":/icons/emblem-favorite.png"))
                return
        self.doSave = True
        self.setIcon(QIcon(":/icons/emblem-favorite-off.png"))
    
    def onClicked(self):
        if self.doSave:
            self.saveClicked()
        else:
            self.deleteClicked()
    
    def saveClicked(self):
        txt = self.text().strip()
        dlg = QInputDialog(self)
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setLabelText(_("The current search terms will be added as a new "
                           "item in the sidebar.\n"
                           "Search name:"))
        dlg.setWindowTitle(_("Save search"))
        ok = dlg.exec_()
        name = dlg.textValue()
        if ok:
            self.mw.col.conf['savedFilters'][name] = txt
            self.mw.col.setMod()

        self.updateButton()
        self.browser.maybeRefreshSidebar()
    
    def deleteClicked(self):
        msg = _('Remove "%s" from your saved searches?') % self.name
        ok = QMessageBox.question(self, _('Remove search'),
                         msg, QMessageBox.Yes, QMessageBox.No)
    
        if ok == QMessageBox.Yes:
            self.mw.col.conf['savedFilters'].pop(self.name, None)
            self.mw.col.setMod()
            self.updateButton()
            self.browser.maybeRefreshSidebar()
