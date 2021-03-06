# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from aqt.qt import *
import aqt.forms
from aqt.utils import saveGeom, restoreGeom, showWarning, askUser, shortcut, \
    tooltip, addCloseShortcut, downArrow
from anki.sound import clearAudioQueue
from anki.hooks import addHook, remHook, runHook
from anki.utils import htmlToTextLine, ids2str, isMac
from anki.lang import _

import aqt.editor, aqt.modelchooser, aqt.deckchooser

import anki
import ccbc


class AddCards(QDialog):
    unique_id=0 #for multi instance

    def __init__(self, mw):
        QDialog.__init__(self, None, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self._UID = "AddCards_%d"%self.unique_id
        self.forceClose = False
        self.form = aqt.forms.addcards.Ui_Dialog()
        self.form.setupUi(self)

        self.setWindowTitle(_("Add"))
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)
        self.setupChoosers()
        self.setupEditor()
        self.setupButtons()
        self.setupHistory()
        self.onReset()

        restoreGeom(self, "add")
        addHook('reset', self.onReset)
        addCloseShortcut(self)

        if self.mw.viewmanager.cbOnTop.isChecked():
            windowFlags = self.windowFlags() | Qt.WindowStaysOnTopHint
            self.setWindowFlags(windowFlags)
        self.show()
        self.setupNewNote()

        addHook("night_mode_state_changed", self.changeToNightMode)

    def changeToNightMode(self, b):
        pass

    def resizeEvent(self, evt):
        super().resizeEvent(evt)
        width = evt.size().width()
        self.editor.toggleExtraFormatButtons(width)

    def setupEditor(self):
        self.editor = aqt.editor.Editor(
            self.mw, self.form.fieldsArea, self, True)

    def setupChoosers(self):
        self.modelChooser = aqt.modelchooser.ModelChooser(
            self.mw, self.form.modelArea)
        self.modelChooser.parent = self
        self.deckChooser = aqt.deckchooser.DeckChooser(
            self.mw, self.form.deckArea)

    def setupButtons(self):
        bb = self.form.buttonBox
        ar = QDialogButtonBox.ActionRole

        #Addon: AddOnlyOnce
        cbState = self.mw.pm.profile.get("AddOnceOnlyCKBOX", False)
        self.addOnceChkBox = QCheckBox(_("Once"))
        self.addOnceChkBox.setCheckState(cbState)
        self.addOnceChkBox.setTristate(False)
        self.form.buttonBox.addButton(self.addOnceChkBox,QDialogButtonBox.ActionRole)
        self.addOnceChkBox.clicked.connect(self.onAddOnceChange)
        self.addOnceChkBox.setShortcut(QKeySequence("Ctrl+o"))
        self.addOnceChkBox.setToolTip(shortcut(_("Add (shortcut: Ctrl+o)")))

        # add
        self.addButton = bb.addButton(_("Add"), ar)
        self.addButton.setShortcut(QKeySequence("Ctrl+Return"))
        self.addButton.setToolTip(shortcut(_("Add (shortcut: Ctrl+Enter)")))
        self.addButton.clicked.connect(self.addCards)

        # close
        self.closeButton = QPushButton(_("Close"))
        self.closeButton.setAutoDefault(False)
        bb.addButton(self.closeButton, QDialogButtonBox.RejectRole)

        # history
        b = bb.addButton(
            _("History")+ u" "+downArrow(), ar)
        if isMac:
            sc = "Ctrl+Shift+H"
        else:
            sc = "Ctrl+H"
        b.setShortcut(QKeySequence(sc))
        b.setToolTip(_("Shortcut: %s") % shortcut(sc))
        b.clicked.connect(self.onHistory)
        self.historyButton = b

    def setupHistory(self):
        self.historyButton.setEnabled(True)

    def setupNewNote(self, set=True):
        f = self.mw.col.newNote()
        if set:
            self.editor.setNote(f, focus=True)
        return f

    def onAddOnceChange(self):
        self.mw.pm.profile['AddOnceOnlyCKBOX'] = self.addOnceChkBox.isChecked()

    def onModelChange(self):
        oldNote = self.editor.note
        note = self.setupNewNote(set=False)
        if oldNote:
            oldFields = oldNote.keys()
            newFields = note.keys()
            for n, f in enumerate(note.model()['flds']):
                fieldName = f['name']
                try:
                    oldFieldName = oldNote.model()['flds'][n]['name']
                except IndexError:
                    oldFieldName = None
                # copy identical fields
                if fieldName in oldFields:
                    note[fieldName] = oldNote[fieldName]
                # set non-identical fields by field index
                elif oldFieldName and oldFieldName not in newFields:
                    try:
                        note.fields[n] = oldNote.fields[n]
                    except IndexError:
                        pass
        self.editor.currentField = 0
        self.editor.setNote(note, focus=True)

    def onReset(self, model=None, keep=False):
        oldNote = self.editor.note
        # copy fields from old note
        if oldNote:
            note = anki.notes.Note(self.mw.col, oldNote.model())
            flds = note.model()['flds']
            if not keep:
                self.removeTempNote(oldNote)
            for n in range(len(note.fields)):
                try:
                    if not keep or flds[n]['sticky']:
                        note.fields[n] = oldNote.fields[n]
                    else:
                        note.fields[n] = ""
                except IndexError:
                    break
        else:
            note = self.setupNewNote(set=False)
        self.editor.currentField = 0
        self.editor.setNote(note, focus=True)

    def removeTempNote(self, note):
        if not note or not note.id or not self.mw.col:
            return
        # we don't have to worry about cards; just the note
        self.mw.col._remNotes([note.id])

    def addHistory(self, note):
        ah = self.mw.pm.profile.get("addHistory",[])
        ah.insert(0, note.id)
        self.mw.pm.profile["addHistory"] = ah[:50]

    def onHistory(self):
        m = QMenu(self)
        ah = self.mw.pm.profile.get("addHistory",[])
        for nid in ah:
            if self.mw.col.findNotes("nid:%d" % nid):
                fields = self.mw.col.getNote(nid).fields
                txt = htmlToTextLine(", ".join(fields))
                if len(txt) > 50:
                    txt = txt[:20] + " ... " + txt[-25:]
                a = m.addAction(_("Edit \"%s\"") % txt)
                a.triggered.connect(lambda b, nid=nid: self.editHistory(nid))
        cnt = len(m.actions())
        if cnt < len(ah):
            a = m.addAction(_("[ Note(s) deleted ]"))
            a.setEnabled(False)
        a = m.addAction(_("[ Browse All ]"))
        a.triggered.connect(lambda b, nid=0: self.editHistory(nid))
        m.exec_(self.historyButton.mapToGlobal(QPoint(0,0)))

    def editHistory(self, nid):
        ah = self.mw.pm.profile.get("addHistory",[])
        sch = "nid:%s" % (str(nid) if nid else ids2str(ah))
        browser = aqt.dialogs.open("Browser", self.mw, False)
        browser.form.searchEdit.lineEdit().setText(sch)
        browser.onSearch()

    def addNote(self, note):
        note.model()['did'] = self.deckChooser.selectedId()
        ret = note.dupeOrEmpty()
        if ret == 1:
            showWarning(_(
                "The first field is empty."))
            return
        if '{{cloze:' in note.model()['tmpls'][0]['qfmt']:
            if not self.mw.col.models._availClozeOrds(
                    note.model(), note.joinedFields(), False):
                if not askUser(_("You have a cloze deletion note type "
                "but have not made any cloze deletions. Proceed?")):
                    return
        cards = self.mw.col.addNote(note)
        if not cards:
            showWarning(_("""\
The input you have provided would make an empty \
question on all cards."""))
            return
        self.mw.col.clearUndo() #in case of addons
        self.addHistory(note)
        if self.mw.state != 'review':
            self.mw.requireReset()
        return note

    def addCards(self):
        self.editor.saveNow()
        self.editor.saveAddModeVars()
        note = self.editor.note
        if self.addNote(note):
            tooltip(_("Added"), period=500)
            # stop anything playing
            clearAudioQueue()
            self.onReset(keep=True)
            self.mw.col.autosave()
            runHook("addedNote", note)
            if self.addOnceChkBox.isChecked():
                self.reject()

    def keyPressEvent(self, evt):
        "Show answer on RET or register answer."
        if evt.key() == Qt.Key_F1:
            self.mw.boss_key()
            return
        if (evt.key() in (Qt.Key_Enter, Qt.Key_Return)
            and self.editor.tags.hasFocus()):
            evt.accept()
            return
        return QDialog.keyPressEvent(self, evt)

    def reject(self):
        # This order is used to avoid a regression in Qt4.8
        # TypeError: invalid result from AddCards.reject()
        # reject() must not return any value
        if self.canClose():
            self._reject()

    def _reject(self):
        remHook('reset', self.onReset)
        clearAudioQueue()
        self.removeTempNote(self.editor.note)
        self.editor.setNote(None)
        self.modelChooser.cleanup()
        self.deckChooser.cleanup()
        self.mw.maybeReset()
        saveGeom(self, "add")
        aqt.dialogs.close(self._UID)
        if not self.forceClose: #not shutdown
            del aqt.dialogs._dialogs[self._UID]
        QDialog.reject(self)

    def canClose(self):
        self.editor.saveNow()
        blankField = self.editor.fieldsAreBlank()
        if blankField or self.forceClose or \
        (self.addOnceChkBox.isChecked() and blankField) or \
        askUser(_("Close and lose current input?")):
            return True
