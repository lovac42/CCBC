# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import sys
from aqt.qt import *
from aqt.utils import openLink
from anki.hooks import runHook
from anki.utils import isMac, isWin
from anki.lang import _

import ccbc.js


# Bridge for Qt<->JS
##########################################################################

class Bridge(QObject):
    @pyqtSlot(str, result=str)
    def run(self, str):
        return self._bridge(str)
    @pyqtSlot(str)
    def link(self, str):
        self._linkHandler(str)
    def setBridge(self, func):
        self._bridge = func
    def setLinkHandler(self, func):
        self._linkHandler = func

# Page for debug messages
##########################################################################

class AnkiWebPage(QWebPage):

    def __init__(self, jsErr):
        QWebPage.__init__(self)
        self._jsErr = jsErr
    def javaScriptConsoleMessage(self, msg, line, srcID):
        self._jsErr(msg, line, srcID)

# Main web view
##########################################################################

class AnkiWebView(QWebView):

    DEFAULT_JS = ccbc.js.jquery + ccbc.js.browserSel

    def __init__(self, canFocus=True):
        QWebView.__init__(self)
        self.setRenderHints(
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.HighQualityAntialiasing)
        self.setObjectName("mainText")
        self._bridge = Bridge()
        self._page = AnkiWebPage(self._jsErr)
        self._loadFinishedCB = None
        self.setPage(self._page)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.setLinkHandler()
        self.setKeyHandler()
        self.setMouseBtnHandler()
        self.setWheelHandler()
        self.connect(self, SIGNAL("linkClicked(QUrl)"), self._linkHandler)
        self.connect(self, SIGNAL("loadFinished(bool)"), self._loadFinished)
        self.allowDrops = False
        # reset each time new html is set; used to detect if still in same state
        self.key = None
        self.setCanFocus(canFocus)

    def keyPressEvent(self, evt):
        if evt.matches(QKeySequence.Copy):
            self.triggerPageAction(QWebPage.Copy)
            evt.accept()
        # work around a bug with windows qt where shift triggers buttons
        if isWin and evt.modifiers() & Qt.ShiftModifier and not evt.text():
            evt.accept()
            return
        QWebView.keyPressEvent(self, evt)

    def keyReleaseEvent(self, evt):
        if self._keyHandler:
            if self._keyHandler(evt):
                evt.accept()
                return
        QWebView.keyReleaseEvent(self, evt)

    def wheelEvent(self, evt):
        if self._wheelHandler:
            if self._wheelHandler(evt):
                evt.accept()
                return
        QWebView.wheelEvent(self, evt)

    def mouseReleaseEvent(self, evt):
        if self._mouseBtnHandler:
            if self._mouseBtnHandler(evt):
                evt.accept()
                return
        QWebView.mouseReleaseEvent(self, evt)

    def contextMenuEvent(self, evt):
        if not self._canFocus:
            return
        m = QMenu(self)
        a = m.addAction(_("Copy"))
        a.connect(a, SIGNAL("triggered()"),
                  lambda: self.triggerPageAction(QWebPage.Copy))
        runHook("AnkiWebView.contextMenuEvent", self, m)
        m.popup(QCursor.pos())

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if not mime.hasUrls():
            # dragged text
            event.acceptProposedAction()
            return

        from aqt import mw
        # exclude file ext
        for url in mime.urls():
            f = url.toLocalFile()
            _,ext = os.path.splitext(f)
            ext = ext.lower()
            if ext in (
                mw.addonManager.ext, ".ankiaddon", # filter addon packages
                ".anki", ".anki2" #old apkg files, see aqt.importing.onImport
            ):
                return
        # allows pdf, epub, mobi, etc...
        event.acceptProposedAction()

    def dropEvent(self, evt):
        from aqt import mw
        if mw.state == 'review':
            #TODO: allow image drops for incremental writing
            return
        import aqt.importing
        mime = evt.mimeData()
        get = aqt.importing.importFile
        for url in mime.urls():
            get(mw, url.toLocalFile())

    def setLinkHandler(self, handler=None):
        if handler:
            self.linkHandler = handler
        else:
            self.linkHandler = self._openLinksExternally
        self._bridge.setLinkHandler(self.linkHandler)

    def setKeyHandler(self, handler=None):
        # handler should return true if event should be swallowed
        self._keyHandler = handler

    def setMouseBtnHandler(self, handler=None):
        # handler should return true if event should be swallowed
        self._mouseBtnHandler = handler

    def setWheelHandler(self, handler=None):
        # handler should return true if event should be swallowed
        self._wheelHandler = handler

    def setHtml(self, html, loadCB=None):
        self.key = None
        self._loadFinishedCB = loadCB
        QWebView.setHtml(self, html)

    def stdHtml(self, body, css="", bodyClass="", loadCB=None, js=None, head=""):
        if isMac:
            button = "font-weight: bold; height: 24px;"
        else:
            button = "font-weight: normal;"
        self.setHtml("""
<!doctype html>
<html><head><style>
button {
%s
}
%s</style>
<script>%s</script>
<script>var pycmd=function(arg){return py.link(arg);}</script>
%s

</head>
<body class="%s">%s</body></html>""" % (
    button, css, js or self.DEFAULT_JS,
    head, bodyClass, body), loadCB)

    def setBridge(self, bridge):
        self._bridge.setBridge(bridge)

    def setCanFocus(self, canFocus=False):
        self._canFocus = canFocus
        if self._canFocus:
            self.setFocusPolicy(Qt.WheelFocus)
        else:
            self.setFocusPolicy(Qt.NoFocus)

    def eval(self, js):
        self.page().mainFrame().evaluateJavaScript(js)

    def _openLinksExternally(self, url):
        openLink(url)

    def _jsErr(self, msg, line, srcID):
        sys.stdout.write(
            (_("JS error on line %(a)d: %(b)s") %
              dict(a=line, b=msg+"\n")))

    def _linkHandler(self, url):
        self.linkHandler(url.toString())

    def _loadFinished(self):
        self.page().mainFrame().addToJavaScriptWindowObject("py", self._bridge)
        if self._loadFinishedCB:
            self._loadFinishedCB(self)
            self._loadFinishedCB = None

    def bundledCSS(self, fname):
        return ""

    def bundledScript(self, fname):
        return ""

    def webBundlePath(self, path):
        return "file:///%s" % path.replace('\\','/')
