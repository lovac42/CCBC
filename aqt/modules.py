# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC



import os
import aqt
from aqt.qt import *
from aqt.utils import showInfo, openFolder, isWin, \
    askUser, restoreGeom, saveGeom, showWarning, tooltip

from ccbc.plugins.Advanced_Copy_Fields import advanced_copy_fields
from ccbc.plugins.Card_Info_Bar_for_Browser import infobar
from ccbc.plugins.Replay_buttons_on_card import replay


class ModuleManager:
    def __init__(self, mw):
        self.mw = mw
        self.dirty = False
        sys.path.insert(0, self.modulesFolder())

    def modulesFolder(self, dir=None):
        root = self.mw.pm.moduleFolder()
        if not dir:
            return root
        return os.path.join(root, dir)

    def loadModules(self):
        for dir in self.allModules():
            self.dirty = True
            try:
                __import__(dir)
            except:
                showWarning(_("""\
A module you installed failed to load. If problems persist, delete the add-on.
\nTraceback:%s""" % traceback.format_exc()))

    def allModules(self):
        l = []
        for d in os.listdir(self.modulesFolder()):
            path = self.modulesFolder(d)
            if not os.path.exists(os.path.join(path, "__init__.py")):
                continue
            l.append(d)
        l.sort()
        return l

