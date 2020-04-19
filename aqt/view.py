# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

#ctrl+mouse_wheel for fast zoom
#ctrl+shift+mouse_wheel for slow zoom


import json
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook
from anki.consts import MODEL_CLOZE


class ViewManager:
    def __init__(self, mw):
        self.mw = mw
        self.ir = IR_View_Manager(mw)

        self.zoom = ZoomManager(mw)
        self.getZoom = self.zoom.getZoom
        self.setZoom = self.zoom.setZoom

        self.scroll = ScrollManager(mw)
        self.getScroll = self.scroll.get
        self.setScroll = self.scroll.set

        self.fullScr = FullScreenManager(mw)
        self.setFullScreen = self.fullScr.set
        self.showCursor = self.fullScr.showCursor
        self.hideCursor = self.fullScr.hideCursor

        self.mw.web.setKeyHandler(self._keyHandler)
        self.mw.web.setMouseBtnHandler(self.ir.onEvent)
        self.mw.web.setWheelHandler(self._wheelHandler)

        # I choose to use hooks in case old addons 
        # override these methods, hooks are then much
        # safer and backwards compatible.
        addHook('profileLoaded', self.onProfileLoaded)
        addHook('unloadProfile', self.flush)
        addHook('beforeStateChange', self.onBeforeStateChange)
        addHook('afterStateChange', self.onAfterStateChange)
        addHook('checkpoint', self.flush) #suspend, bury, delete
        addHook('showQuestion', self.onShowQuestion)
        addHook('showAnswer', self.onShowAnswer)

    def onProfileLoaded(self):
        zi=self.mw.pm.profile.get("zoom.img",False)
        self.zoom.zoomImage.setChecked(zi)
        self.zoom.setZoomTextOnly() #init zoom settings

    def flush(self, *args):
        if self.mw.state == 'review':
            self.ir.flush(*args)

    def onBeforeStateChange(self, newS, oldS, *args):
        self.fullScr.showCursor()
        if oldS == 'review':
            self.ir.flush()

    def onAfterStateChange(self, newS, oldS, *args):
        self.fullScr.stateChanged(newS)
        if newS != 'review':
            self.fullScr.hideCursor()
            self.zoom.isIR = False
            self.zoom.adjust() #reload

    def onShowQuestion(self):
        c = self.mw.reviewer.card
        # self.ir.setCard(c) #moved to reviewer to prevent delay
        if self.ir.isIRCard():
            self.zoom.isIR = True
            z=self.ir.getZoom()
            self.setZoom(z or self.getZoom())
            self.setScroll(self.ir.getScroll())
        else:
            self.zoom.isIR = False
            if not self.zoom.zoomLock.isChecked():
                self.zoom.adjust() #reload

    def onShowAnswer(self):
        if self.ir.isIRCard():
            return
        if not self.zoom.zoomLock.isChecked():
            self.zoom.adjust()

    def isFullScreen(self):
        return self.mw.isFullScreen()

    def _wheelHandler(self, evt):
        if evt.modifiers() == Qt.ControlModifier:
            z=0.20 if self.zoom.isIR else 0.35 #TODO: add config for adjustments
            return self.zoom.mouseZoom(evt,z)
        elif evt.modifiers() == (Qt.ShiftModifier|Qt.ControlModifier):
            return self.zoom.mouseZoom(evt,0.08) #shift + zoom
        return self.ir.onEvent(evt)

    def _keyHandler(self, evt):
        if self.mw.reviewer._catchEsc(evt):
            return True
        return self.ir.onEvent(evt)

    def unhover(self):
        if self.mw.isFullScreen():
            self.fullScr.stateChanged("review")
            self.fullScr.hideCursor()

    def hoverBottom(self):
        if self.mw.isFullScreen():
            self.fullScr.hoverBottom()
            self.fullScr.showCursor()

    def hoverTop(self):
        if self.mw.isFullScreen():
            self.fullScr.hoverTop()
            self.fullScr.showCursor()





class ZoomManager():

    def __init__(self, mw):
        self.mw = mw
        self.isIR = False
        self.setupMenu()

        self.getZoom = self.mw.web.zoomFactor
        self.setZoom = self.mw.web.setZoomFactor

    def setupMenu(self):
        menu = self.mw.form.menuView
        subMenu = QMenu('&Zoom', menu)
        menu.addMenu(subMenu)

        a = QAction("Zoom In", subMenu)
        a.triggered.connect(self.zoomIn)
        a.setShortcut("Ctrl++")
        subMenu.addAction(a)

        a = QAction("Zoom In", self.mw)
        a.triggered.connect(self.zoomIn)
        a.setShortcut("Ctrl+=")
        self.mw.addAction(a)

        a = QAction("Zoom Out", subMenu)
        a.triggered.connect(self.zoomOut)
        a.setShortcut("Ctrl+-")
        subMenu.addAction(a)

        subMenu.addSeparator()

        a = QAction("Zoom Reset", subMenu)
        a.triggered.connect(lambda:self.reset(1)) #param=false w/o lambda
        a.setShortcut("Ctrl+\\")
        subMenu.addAction(a)
        subMenu.addSeparator()

        a = QAction("Zoom Lock", subMenu)
        a.setCheckable(True)
        a.setShortcut("Ctrl+|")
        self.zoomLock = a
        subMenu.addAction(a)

        a = QAction("Zoom on Images", subMenu)
        a.setCheckable(True)
        a.triggered.connect(self.setZoomTextOnly)
        self.zoomImage = a
        subMenu.addAction(a)
        subMenu.addSeparator()

        a = QAction("50%", subMenu)
        a.triggered.connect(lambda:self.reset(0.5))
        subMenu.addAction(a)
        a = QAction("75%", subMenu)
        a.triggered.connect(lambda:self.reset(0.75))
        subMenu.addAction(a)
        a = QAction("100%", subMenu)
        a.triggered.connect(lambda:self.reset(1))
        subMenu.addAction(a)
        subMenu.addSeparator()

        a = QAction("125%", subMenu)
        a.triggered.connect(lambda:self.reset(1.25))
        subMenu.addAction(a)
        a = QAction("150%", subMenu)
        a.triggered.connect(lambda:self.reset(1.5))
        subMenu.addAction(a)
        a = QAction("175%", subMenu)
        a.triggered.connect(lambda:self.reset(1.75))
        subMenu.addAction(a)
        a = QAction("200%", subMenu)
        a.triggered.connect(lambda:self.reset(2))
        subMenu.addAction(a)
        a = QAction("250%", subMenu)
        a.triggered.connect(lambda:self.reset(2.5))
        subMenu.addAction(a)
        a = QAction("300%", subMenu)
        a.triggered.connect(lambda:self.reset(3))
        subMenu.addAction(a)

    def adjust(self, zoomBy=0):
        if self.isIR or self.zoomLock.isChecked():
            key=None
            fct=self.getZoom()
        else:
            key = self._getKey()
            fct = self.mw.pm.profile.get(
                    key, self.getZoom())
        self.setFactor(fct+zoomBy,key)

    def setFactor(self, fct, key=None):
        factor = min(10, max(0.5, fct))
        self.setZoom(factor)
        if key:
            self.mw.pm.profile[key] = factor

    def _getKey(self):
        if self.mw.state != "review":
            return "zoom."+self.mw.state
        if self.isIR:
            return None

        m = self.mw.reviewer.card.model()
        ord = "" #target template card number
        if m['type'] != MODEL_CLOZE:
            card_num = self.mw.reviewer.card.ord
            if card_num: # discard 0, backwards compatible reasons
                ord = "_c%d"%card_num

        if self.mw.reviewer.state == "answer":
            return "zoom.a_m%s%s"%(str(m['id']),ord)
        return "zoom.q_m%s%s"%(str(m['id']),ord)

    def reset(self, z=1): #called by menuitems
        key = self._getKey()
        self.setFactor(z,key)

    def zoomIn(self, z):
        self.adjust(z or 0.25)

    def zoomOut(self, z):
        self.adjust(-z or -0.25)

    def mouseZoom(self, evt, zoom):
        step = evt.delta() / 12 #120/0.1
        if step < 0:
            self.zoomOut(zoom)
        else:
            self.zoomIn(zoom)
        return True

    def setZoomTextOnly(self):
        self.reset()
        zimg=self.zoomImage.isChecked()
        self.mw.pm.profile["zoom.img"] = zimg
        s=self.mw.web.settings()
        if zimg:
            s.setAttribute(QWebSettings.ZoomTextOnly,False)
        else:
            s.setAttribute(QWebSettings.ZoomTextOnly,True)






class FullScreenManager:

    def __init__(self, mw):
        self.mw = mw
        self.mu_height = self.mw.height()
        self.tb_height = self.mw.toolbar.web.height()
        self.cursor_timer = None

        addHook('profileLoaded', self.onProfileLoaded)
        addHook('unloadProfile', self.onUnloadProfile)

        self.setupMenu()


    def setupMenu(self):
        menu = self.mw.form.menuView
        subMenu = QMenu('&Screen', menu)
        menu.addMenu(subMenu)

        self.cbFullScreen = QAction("Full Screen", subMenu)
        self.cbFullScreen.setCheckable(True)
        self.cbFullScreen.triggered.connect(self.onFullScreen)
        self.cbFullScreen.setShortcut("F11")
        subMenu.addAction(self.cbFullScreen)
        subMenu.addSeparator()

        self.menubar = QAction("Hide Menubar", subMenu)
        self.menubar.setCheckable(True)
        self.menubar.triggered.connect(self.cb_toggle)
        subMenu.addAction(self.menubar)

        self.toolbar = QAction("Hide Toolbar", subMenu)
        self.toolbar.setCheckable(True)
        self.toolbar.triggered.connect(self.cb_toggle)
        subMenu.addAction(self.toolbar)

        self.bottombar = QAction("Hide Bottombar", subMenu)
        self.bottombar.setCheckable(True)
        self.bottombar.triggered.connect(self.cb_toggle)
        subMenu.addAction(self.bottombar)

        subMenu.addSeparator()
        self.cbHideCursor = QAction("Hide Idle Cursor", subMenu)
        self.cbHideCursor.setCheckable(True)
        self.cbHideCursor.triggered.connect(self.cb_toggle)
        # subMenu.addAction(self.cbHideCursor)
        #TODO: re-enable this once workflow issue has been sorted out.


    def cb_toggle(self):
        self.mw.pm.profile['fs_hide_menubar'] = self.menubar.isChecked()
        self.mw.pm.profile['fs_hide_toolbar'] = self.toolbar.isChecked()
        self.mw.pm.profile['fs_hide_bottombar'] = self.bottombar.isChecked()
        t = self.mw.pm.profile['fs_hide_cursor'] = self.cbHideCursor.isChecked()
        if t:
            self.hideCursor()
        else:
            self.showCursor()
        self.stateChanged(self.mw.state)

    def onUnloadProfile(self):
        if self.mw.isFullScreen():
            #must not save FS state to profile
            self.mw.showNormal()

    def onProfileLoaded(self):
        self.wasMaxState = self.mw.isMaximized()
        b = self.mw.pm.profile.get('fs_hide_menubar',True)
        self.menubar.setChecked(b)
        b = self.mw.pm.profile.get('fs_hide_toolbar',True)
        self.toolbar.setChecked(b)
        b = self.mw.pm.profile.get('fs_hide_bottombar',False)
        self.bottombar.setChecked(b)
        b = self.mw.pm.profile.get('fs_hide_cursor',False)
        self.cbHideCursor.setChecked(b)
        self.cbFullScreen.setChecked(self.mw.isFullScreen())

    def onFullScreen(self):
        toggle = not self.mw.isFullScreen()
        self.set(toggle)
        if toggle:
            self.hideCursor()
        else:
            self.showCursor()

    def stateChanged(self, state):
        if self.mw.isFullScreen() and state == 'review':
            bh,th,hide = (0,0,True)
        else:
            bh,th,hide = (9999,self.tb_height,False)

        self.reset()
        if self.menubar.isChecked():
            #using show/hide prevents hotkeys from working
            self.mw.menuBar().setMaximumHeight(bh)
        if self.toolbar.isChecked():
            self.mw.toolbar.web.setFixedHeight(th)
        if hide and self.bottombar.isChecked():
            self.mw.bottomWeb.hide()
            self.mw.web.setFocus()
        else:
            self.mw.bottomWeb.show()

    def reset(self):
        self.mw.menuBar().setMaximumHeight(9999)
        self.mw.toolbar.web.setFixedHeight(self.tb_height)
        self.mw.bottomWeb.show()

    def set(self, toFS):
        self.mw.hide()
        if toFS:
            self.wasMaxState = self.mw.isMaximized()
            self.mw.showNormal() #lock oldSize
            self.mw.showFullScreen()
        elif self.wasMaxState:
            self.mw.showNormal() #lock oldSize
            self.mw.showMaximized()
        else:
            self.mw.showNormal()
        self.mw.show()
        self.stateChanged(self.mw.state)
        self.cbFullScreen.setChecked(self.mw.isFullScreen())

    def hoverBottom(self):
        if self.bottombar.isChecked():
            self.mw.bottomWeb.show()

    def hoverTop(self):
        if self.menubar.isChecked():
            self.mw.toolbar.web.setFixedHeight(0)
            self.mw.menuBar().setMaximumHeight(9999)

    def showCursor(self):
        if self.cursor_timer:
            self.cursor_timer.stop()
        self.mw.reviewer.web.eval("mouse_shown=true;")
        QApplication.restoreOverrideCursor()

    def hideCursor(self):
        if self.mw.isFullScreen() and \
        self.mw.state == 'review' and \
        self.cbHideCursor.isChecked():
            self.cursor_timer = self.mw.progress.timer(
                5000, self._hideCursor, False #TODO: config for timer
            )

    def _hideCursor(self):
        self.mw.reviewer.web.eval("mouse_shown=false;")
        QApplication.setOverrideCursor(Qt.BlankCursor)




class ScrollManager():
    def __init__(self, mw):
        self.mw = mw

    def get(self):
        return self.mw.web.page().mainFrame().scrollPosition().y()

    def set(self, pos=0):
        self.mw.web.page().mainFrame().setScrollPosition(QPoint(0,pos))

    def reset(self):
        self.mw.web.page().mainFrame().setScrollPosition(QPoint(0,0))





class IR_View_Manager:
    def __init__(self, mw):
        self.mw = mw
        self.count = 0
        self.ir_data = None
        self.last_id = -1

        self._zoom = self.mw.web.zoomFactor
        self._scroll = self.mw.web.page().mainFrame().scrollPosition

    def setCard(self, card):
        if card.id != self.last_id:
            self.last_id=card.id
            self.ir_data=self._extractData(card)

    def _extractData(self, card):
        n=card.model()['name'][:6]
        if n == 'IRead2' or n == 'IR3':
            if card.data:
                d=json.loads(card.data)
                if d:
                    return d.get('viewm',[0,0])
            return [0,0]

    def onEvent(self, evt):
        if not self.ir_data:
            return False
        if self.mw.state!="review":
            return False
        if self.mw.reviewer.state=="answer":
            return False

        if isinstance(evt,QKeyEvent):
            if evt.key() == Qt.Key_Space or \
            (evt.key() >= Qt.Key_Left and \
             evt.key() <= Qt.Key_PageDown):
                self.cache()
                return True
        else:
            if self.count%5 == 0:
                self.cache()
            self.count+=1

    def isIRCard(self):
        return not self.ir_data == None

    def getZoom(self):
        return self.ir_data[1]

    def getScroll(self):
        return self.ir_data[0]

    def flush(self, chkpts=""):
        self.cache(flush=True)
        if chkpts in ("Bury","Suspend","Delete"):
            self.ir_data = None

    def cache(self, flush=False):
        if self.ir_data and self.mw.reviewer.state=='question':
            self.count = 0
            s = self._scroll().y() #TODO: restore exact scroll pos & window geo
            z = self._zoom()
            self.ir_data = [s,z]
            if not flush:
                return
            c = self.mw.reviewer.card
            if c:
                self.last_id = c.id
                d = {} if not c.data else json.loads(c.data)
                d['viewm'] = self.ir_data
                c.data = json.dumps(d)
                c.flush()
