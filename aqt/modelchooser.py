# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from aqt.qt import *
from anki.hooks import addHook, remHook, runHook
from aqt.utils import  shortcut
from anki.lang import _
from PyQt4 import QtCore

class ModelChooser(QHBoxLayout):

    def __init__(self, mw, widget, label=True):
        QHBoxLayout.__init__(self)
        self.widget = widget
        self.mw = mw
        self.deck = mw.col
        self.label = label
        self.setMargin(0)
        self.setSpacing(8)
        self.setupModels()
        addHook('reset', self.onReset)
        self.widget.setLayout(self)

    def setupModels(self):
        if self.label:
            self.modelLabel = QLabel(_("Type"))
            self.addWidget(self.modelLabel)
        # models box
        self.models = QPushButton()
        self.models.setCursor(QtCore.Qt.PointingHandCursor)
        #self.models.setStyleSheet("* { text-align: left; }")
        self.models.setToolTip(shortcut(_("Change Note Type (Ctrl+N)")))
        s = QShortcut(QKeySequence(_("Ctrl+N")), self.widget, activated=self.onModelChange)
        self.models.setAutoDefault(False)
        self.addWidget(self.models)
        self.models.clicked.connect(self.onModelChange)
        # layout
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy(7),
            QSizePolicy.Policy(0))
        self.models.setSizePolicy(sizePolicy)
        self.updateModels()

    def cleanup(self):
        remHook('reset', self.onReset)

    def onReset(self):
        self.updateModels()

    def show(self):
        self.widget.show()

    def hide(self):
        self.widget.hide()

    def onEdit(self):
        import aqt.models
        aqt.models.Models(self.mw, self.widget)

    def onModelChange(self):
        from aqt.studydeck import StudyDeck
        current = self.deck.models.current()['name']
        # edit button
        edit = QPushButton(_("Manage"), clicked=self.onEdit)
        def nameFunc():
            return sorted(self.deck.models.allNames())
        ret = StudyDeck(
            self.mw, names=nameFunc,
            accept=_("Choose"), title=_("Choose Note Type"),
            current=current, parent=self.widget,
            buttons=[edit], cancel=True, geomKey="selectModel")
        if not ret.name:
            return
        m = self.deck.models.byName(ret.name)
        self.deck.conf['curModel'] = m['id']
        cdeck = self.deck.decks.current()
        cdeck['mid'] = m['id']
        self.deck.decks.save(cdeck)
        try:
            self.parent.onModelChange()
        except AttributeError:
            pass #no parent
        runHook("currentModelChanged")
        self.mw.reset() #calls updateModels

    def updateModels(self):
        try:
            m = self.parent.editor.note._model
        except AttributeError:
            m = self.deck.models.current()
        self.models.setText(m["name"])
