# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

from aqt.qt import *
from anki.lang import _
import ccbc


class Toolbar:
    _css = ccbc.css.toolbar
    _body = """
<center id=outer>
<table id=header width=100%%>
<tr>

<td class=tdcenter align=center>%s</td>

</tr></table>
</center>
"""

    def __init__(self, mw, web):
        self.mw = mw
        self.web = web
        self.web.page().mainFrame().setScrollBarPolicy(
            Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.web.setLinkHandler(self._linkHandler)
        self.link_handlers = {
            "decks": self._deckLinkHandler,
            "study": self._studyLinkHandler,
            "add": self._addLinkHandler,
            "browse": self._browseLinkHandler,
            "stats": self._statsLinkHandler,
            "sync": self._syncLinkHandler,
        }

    def draw(self):
        self.web.stdHtml(self._body % (
            self._centerLinks() ), self._css)

    # Available links
    ######################################################################

    def _centerLinks(self):
        links = [
            ["decks", _("Decks"), _("Shortcut key: %s") % "D"],
            ["add", _("Add"), _("Shortcut key: %s") % "A"],
            ["browse", _("Browse"), _("Shortcut key: %s") % "B"],
            ["stats", _("Stats"), _("Shortcut key: %s") % "Shift+S"],
            ["sync", _("Sync"), _("Shortcut key: %s") % "Y"],
        ]
        return self._linkHTML(links)

    def _linkHTML(self, links):
        buf = ""
        for ln, name, title in links:
            buf += '<a class=hitem title="%s" href="%s">%s</a>' % (
                title, ln, name)
            buf += "&nbsp;"*3
        return buf

    # Link handling
    ######################################################################

    def _linkHandler(self, link):
        # first set focus back to main window, or we're left with an ugly
        # focus ring around the clicked item
        self.mw.web.setFocus()
        if link in self.link_handlers:
          self.link_handlers[link]()

    def _deckLinkHandler(self):
        self.mw.moveToState("deckBrowser")

    def _studyLinkHandler(self):
        # if overview already shown, switch to review
        if self.mw.state == "overview":
            self.mw.col.startTimebox()
            self.mw.moveToState("review")
        else:
          self.mw.onOverview()

    def _addLinkHandler(self):
        self.mw.onAddCard()

    def _browseLinkHandler(self):
        self.mw.onBrowse()

    def _statsLinkHandler(self):
        self.mw.onStats()

    def _syncLinkHandler(self):
        self.mw.onSync()
















class BottomBar(Toolbar):
    _css = ccbc.css.toolbar+ccbc.css.bottombar
    _centerBody = """
<center id=outer><table width=100%% id=header><tr><td align=center>
%s</td></tr></table></center>
"""

    def draw(self, buf):
        self.web.show()
        self.web.stdHtml(
            self._centerBody % buf,
            self._css)

