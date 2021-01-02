# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from aqt.qt import *
from anki.hooks import addHook


class Lightbox:
    def __init__(self, mw):
        self.mw = mw
        self.setupMenu()
        addHook('profileLoaded', self.onProfileLoaded)
        addHook('showQuestion', self._wrapLightbox)
        addHook('showAnswer', self._wrapLightbox)

    def setupMenu(self):
        menu = self.mw.form.menuView
        self.cbLightbox = QAction("Lightbox", menu)
        self.cbLightbox.setCheckable(True)
        self.cbLightbox.triggered.connect(self._toggleLightbox)
        menu.addAction(self.cbLightbox)

    def onProfileLoaded(self):
        b = self.mw.pm.profile.get('viewm.lightbox',False)
        self.cbLightbox.setChecked(b)
        self._toggleLightbox()

    def _wrapLightbox(self):
        if self.cbLightbox.isChecked():
            self.mw.web.eval("lightbox_wrap();")

    def _toggleLightbox(self):
        isOn = self.mw.pm.profile['viewm.lightbox'] = self.cbLightbox.isChecked()
        if self.mw.state == "review":
            if isOn:
                b = self.mw.web.page().mainFrame().evaluateJavaScript("lightbox_loaded")
                if b == None: #js not loaded
                    self.mw.reviewer.cardQueue.append(self.mw.reviewer.card)
                    self.mw.reset(guiOnly=True)
                self.mw.web.eval("lightbox_wrap();")
            else:
                self.mw.web.eval("lightbox_unwrap();")

    def isChecked(self):
        return self.cbLightbox.isChecked()
