# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

from aqt.qt import *
import os, time
from anki.hooks import addHook
from aqt.utils import saveGeom, restoreGeom, maybeHideClose, showInfo, addCloseShortcut, tooltip, getSaveFile
from anki.lang import _
import aqt
import ccbc.js
import ccbc.css


# Deck Stats
######################################################################

class DeckStats(QDialog):

    def __init__(self, mw):
        QDialog.__init__(self, mw, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.name = "deckStats"
        self.period = 0
        self.form = aqt.forms.stats.Ui_Dialog()
        self.oldPos = QPoint(0,0)
        self.wholeCollection = False
        self.setMinimumWidth(700)
        self.refreshLock = False
        self.setStyleSheet(ccbc.css.stats)
        f = self.form
        f.setupUi(self)
        restoreGeom(self, self.name)

        b = f.buttonBox.addButton(_("Save Image"),
                                          QDialogButtonBox.ActionRole)
        b.clicked.connect(self.saveImage)
        b.setAutoDefault(False)

        b = f.buttonBox.addButton(_("Save PDF"),
                                          QDialogButtonBox.ActionRole)
        b.clicked.connect(self.savePDF)
        b.setAutoDefault(False)

        f.groups.clicked.connect(lambda: self.changeScope("deck"))
        f.groups.setShortcut("g")
        f.all.clicked.connect(lambda: self.changeScope("collection"))
        f.month.clicked.connect(lambda: self.changePeriod(0))
        f.year.clicked.connect(lambda: self.changePeriod(1))
        f.life.clicked.connect(lambda: self.changePeriod(2))
        f.web.loadFinished.connect(self.loadFin)

        maybeHideClose(self.form.buttonBox)
        addCloseShortcut(self)
        self.show()
        self.refresh()
        self.activateWindow()

        addHook("night_mode_state_changed", self.changeToNightMode)

    def changeToNightMode(self, b):
        pass

    def show(self):
        super().show()

    def reject(self):
        saveGeom(self, self.name)
        aqt.dialogs.markClosed("DeckStats")
        QDialog.reject(self)

    def closeWithCallback(self, callback):
        self.reject()
        callback()

    def _imagePath(self, ext=".pdf"):
        name = time.strftime("-%Y-%m-%d@%H-%M-%S"+ext,
                             time.localtime(time.time()))
        name = "anki-"+_("stats")+name
        file = getSaveFile(self, title=_("Save File"),
                           dir_description="stats",
                           key="stats",
                           ext=ext,
                           fname=name)
        return file

    def savePDF(self):
        path = self._imagePath(".pdf")
        if not path:
            return
        printer=QPrinter(1) #0=scr, 1=pnt, 2=high resolution
        printer.setOutputFileName(path)
        self.form.web.print(printer)
        tooltip(_("Saved PDF."))

    def saveImage(self):
        path = self._imagePath(".png")
        if not path:
            return
        p = self.form.web.page()
        oldsize = p.viewportSize()
        p.setViewportSize(p.mainFrame().contentsSize())
        image = QImage(p.viewportSize(), QImage.Format_ARGB32)

        # Noisy output:
        #   Warning "QPainter::end: Painter ended with 2 saved states"
        #   https://bugreports.qt.io/browse/QTBUG-13524
        painter = QPainter(image)
        p.mainFrame().render(painter)
        painter.end()

        isOK = image.save(path, "png")
        if isOK:
            tooltip(_("Saved PNG."))
        else:
            showInfo(_("""\
Anki could not save the image. Please check that you have permission to write \
to your desktop."""))
        p.setViewportSize(oldsize)

    def changePeriod(self, n):
        self.period = n
        self.refresh()

    def changeScope(self, type):
        self.wholeCollection = type == "collection"
        self.refresh()

    def loadFin(self, b):
        self.form.web.page().mainFrame().setScrollPosition(self.oldPos)

    def refresh(self):
        self.mw.progress.start(immediate=True)
        try:
            self._refresh()
        finally:
            self.refreshLock = False
            self.mw.progress.finish()

    def _refresh(self):
        if not self.refreshLock:
            self.refreshLock = True
            self.oldPos = self.form.web.page().mainFrame().scrollPosition()
            stats = self.mw.col.stats()
            stats.wholeCollection = self.wholeCollection
            txt = stats.report(type=self.period)
            self.report="<style>%s</style><script>%s\n</script>%s"%(
                    ccbc.css.stats,
                    ccbc.js.jquery+ccbc.js.plot,txt)
            self.form.web.setHtml(self.report)
            klass=self.mw.web.page().mainFrame().evaluateJavaScript(
                                            'document.body.className')
            self.form.web.eval('document.body.className += "%s";'%klass)

    def canClose(self):
        return True
