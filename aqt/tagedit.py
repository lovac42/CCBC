# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

import re
from aqt.qt import *
from anki.hooks import addHook


class TagEdit(QLineEdit):

    lostFocus = pyqtSignal()

    # 0 = tags, 1 = decks
    def __init__(self, parent, type=0):
        QLineEdit.__init__(self, parent)
        self.col = None
        self.model = QStringListModel()
        self.type = type
        if type == 0:
            self.completer = TagCompleter(self.model, parent, self)
        else:
            self.completer = QCompleter(self.model, parent)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)

        addHook("night_mode_state_changed", self.changeToNightMode)

    def changeToNightMode(self, b):
        pass

    def setCol(self, col):
        "Set the current col, updating list of available tags."
        self.col = col
        if self.type == 0:
            l = sorted(self.col.tags.all())
        else:
            l = sorted(self.col.decks.allNames())
        self.model.setStringList(l)

    def focusInEvent(self, evt):
        QLineEdit.focusInEvent(self, evt)

    def keyPressEvent(self, evt):
        if evt.key() in (Qt.Key_Up, Qt.Key_Down):
            # show completer on arrow key up/down
            if not self.completer.popup().isVisible():
                self.showCompleter()
            return
        if (evt.key() == Qt.Key_Tab and evt.modifiers() & Qt.ControlModifier):
            # select next completion
            if not self.completer.popup().isVisible():
                self.showCompleter()
            index = self.completer.currentIndex()
            self.completer.popup().setCurrentIndex(index)
            cur_row = index.row()
            if not self.completer.setCurrentRow(cur_row + 1):
                self.completer.setCurrentRow(0)
            return
        if evt.key() in (Qt.Key_Enter, Qt.Key_Return):
            # apply first completion if no suggestion selected
            selected_row = self.completer.popup().currentIndex().row()
            if selected_row == -1:
                self.completer.setCurrentRow(0)
                index = self.completer.currentIndex()
                self.completer.popup().setCurrentIndex(index)
            self.hideCompleter()
            QWidget.keyPressEvent(self, evt)
            return
        QLineEdit.keyPressEvent(self, evt)
        if not evt.text():
            # if it's a modifier, don't show
            return
        if evt.key() not in (
            Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Space,
            Qt.Key_Tab, Qt.Key_Backspace, Qt.Key_Delete):
            self.showCompleter()

    def showCompleter(self):
        self.completer.setCompletionPrefix(self.text())
        self.completer.complete()

    def focusOutEvent(self, evt):
        QLineEdit.focusOutEvent(self, evt)
        self.lostFocus.emit()
        self.completer.popup().hide()

    def hideCompleter(self):
        # Replaced with try-catch to fix a regression in PyQt v4.12.3; see issue #10
        # if sip.isdeleted(self.completer):
            # return
        try:
            self.completer.popup().hide()
        except RuntimeError:
            #Suppress errors when TagCompleter has been deleted, (not Qt4 related?).
            #https://github.com/dae/anki/commit/eca6ecf90faea01014fbe4f1a9d339a190ef97cb
            #https://anki.tenderapp.com/discussions/beta-testing/884
            return


class TagCompleter(QCompleter):

    def __init__(self, model, parent, edit, *args):
        QCompleter.__init__(self, model, parent)
        self.tags = []
        self.edit = edit
        self.cursor = None

    def splitPath(self, tags):
        stripped_tags = tags.strip()
        stripped_tags = re.sub("  +", " ", stripped_tags)
        self.tags = self.edit.col.tags.split(stripped_tags)
        self.tags.append("")
        p = self.edit.cursorPosition()
        if tags.endswith("  "):
            self.cursor = len(self.tags) - 1
        else:
            self.cursor = stripped_tags.count(" ", 0, p)
        return [self.tags[self.cursor]]

    def pathFromIndex(self, idx):
        if self.cursor is None:
            return self.edit.text()
        ret = QCompleter.pathFromIndex(self, idx)
        self.tags[self.cursor] = ret
        try:
            self.tags.remove("")
        except ValueError:
            pass
        return " ".join(self.tags) + " "