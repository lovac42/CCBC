# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from aqt.qt import *
import aqt.editor
from aqt.utils import saveGeom, restoreGeom
from anki.hooks import addHook, remHook
from anki.utils import isMac
from anki.lang import _


class EditCurrent(QDialog):

    def __init__(self, mw):
        QDialog.__init__(self, None, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.form = aqt.forms.editcurrent.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle(_("Edit Current"))
        self.setMinimumHeight(250)
        self.setMinimumWidth(400)
        self.rejected.connect(self.onSave)
        self.form.buttonBox.button(QDialogButtonBox.Close).setShortcut(
                QKeySequence("Ctrl+Return"))
        self.editor = aqt.editor.Editor(self.mw, self.form.fieldsArea, self)
        self.editor.card = self.mw.reviewer.card
        self.editor.setNote(self.mw.reviewer.card.note(), focus=True)
        restoreGeom(self, "editcurrent")
        addHook("reset", self.onReset)
        self.mw.requireReset()
        self.show()
        # reset focus after open
        # reset focus after open, taking care not to retain webview
        # pylint: disable=unnecessary-lambda
        self.mw.progress.timer(100, lambda: self.editor.web.setFocus(), False)

        addHook("night_mode_state_changed", self.changeToNightMode)

    def changeToNightMode(self, b):
        pass

    def onReset(self):
        # lazy approach for now: throw away edits
        try:
            n = self.mw.reviewer.card.note()
            n.load()
        except:
            # card's been deleted
            remHook("reset", self.onReset)
            self.editor.setNote(None)
            self.mw.reset(guiOnly=True)
            aqt.dialogs.close("EditCurrent")
            self.close()
            return
        self.editor.setNote(n)

    def onSave(self):
        remHook("reset", self.onReset)
        self.editor.saveNow()
        r = self.mw.reviewer
        try:
            r.card.load()
        except:
            pass # card was removed by clayout
        else:
            r.cardQueue.append(self.mw.reviewer.card)
        self.mw.moveToState("review")
        saveGeom(self, "editcurrent")
        aqt.dialogs.close("EditCurrent")

    def canClose(self):
        self.close()
        self.reject()
        return True

    def resizeEvent(self, evt):
        super().resizeEvent(evt)
        width = evt.size().width()
        self.editor.toggleExtraFormatButtons(width)

    def keyPressEvent(self, evt):
        "Show answer on RET or register answer."
        if evt.key() == Qt.Key_F1:
            self.mw.boss_key()
            return
        return QDialog.keyPressEvent(self, evt)
