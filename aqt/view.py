# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from aqt import mw
from aqt.qt import *
from anki.hooks import addHook


class ViewManager:
    def __init__(self, mw):
        self.fullscreen = FullScreenManager(mw)



class FullScreenManager:
    def __init__(self, mw):
        self.mw = mw
        self.mu_height = self.mw.height()
        self.tb_height = self.mw.toolbar.web.height()
        addHook('afterStateChange', self.stateChanged)
        addHook('profileLoaded', self.onProfileLoaded)
        self.setupMenu()
        self.mwCSS=mw.styleSheet()


    def setupMenu(self):
        menu=self.mw.form.menuView
        a = QAction("Full Screen", self.mw)
        a.triggered.connect(self.onFullScreen)
        a.setShortcut("F11")
        menu.addAction(a)

        self.menubar=QAction("FS: Hide Menubar", self.mw)
        self.menubar.setCheckable(True)
        self.menubar.triggered.connect(self.cb_toggle)
        menu.addAction(self.menubar)

        self.toolbar=QAction("FS: Hide Toolbar", self.mw)
        self.toolbar.setCheckable(True)
        self.toolbar.triggered.connect(self.cb_toggle)
        menu.addAction(self.toolbar)

        self.bottombar=QAction("FS: Hide Bottombar", self.mw)
        self.bottombar.setCheckable(True)
        self.bottombar.triggered.connect(self.cb_toggle)
        menu.addAction(self.bottombar)


    def cb_toggle(self):
        self.mw.pm.profile['fs_hide_menubar']=self.menubar.isChecked()
        self.mw.pm.profile['fs_hide_toolbar']=self.toolbar.isChecked()
        self.mw.pm.profile['fs_hide_bottombar']=self.bottombar.isChecked()
        self.stateChanged(self.mw.state,self.mw.state)


    def onProfileLoaded(self):
        b=self.mw.pm.profile.get('fs_hide_menubar',True)
        self.menubar.setChecked(b)
        b=self.mw.pm.profile.get('fs_hide_toolbar',True)
        self.toolbar.setChecked(b)
        b=self.mw.pm.profile.get('fs_hide_bottombar',False)
        self.bottombar.setChecked(b)


    def onFullScreen(self):
        toggle=self.mw.windowState() ^ Qt.WindowFullScreen
        self.mw.setWindowState(toggle)
        self.stateChanged(self.mw.state,self.mw.state)


    def stateChanged(self, newS, oldS, *args):
        self.mwCSS=mw.styleSheet().replace("QMenuBar{height:0 !important;}","")
        self.reset()

        #yikes
        g,h,b=('QMenuBar{height:0 !important;}',0,self.mw.bottomWeb.hide) if \
                    self.mw.isFullScreen() and newS=='review' else \
                    ('',self.tb_height,self.mw.bottomWeb.show)

        if self.menubar.isChecked():
            self.mw.setStyleSheet(self.mwCSS+g) #hide by css to keep hotkeys active
        if self.toolbar.isChecked():
            self.mw.toolbar.web.setFixedHeight(h) #menubar
        if self.bottombar.isChecked():
            b()


    def reset(self):
        self.mw.setStyleSheet(self.mwCSS)
        self.mw.toolbar.web.setFixedHeight(self.tb_height)
        self.mw.bottomWeb.show()

