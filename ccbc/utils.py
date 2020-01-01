# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

import os, re
from anki.utils import isMac

from PyQt4 import QtCore, QtGui


def _getExportFolder():
    # running from source?
    srcFolder = os.path.join(os.path.dirname(__file__), "..")
    webInSrcFolder = os.path.abspath(os.path.join(srcFolder, "web"))
    if os.path.exists(webInSrcFolder):
        return webInSrcFolder
    elif isMac:
        dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(dir + "/../../Resources/web")
    else:
        raise Exception("couldn't find web folder")


def webBundlePath(fname):
    path = _getExportFolder()
    return os.path.abspath(os.path.join(path,fname))


def readFile(fname):
    path=webBundlePath(fname)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()


def readBinary(fname):
    path=webBundlePath(fname)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f.read()


def getIcon(fn):
    p = _getExportFolder()
    f = os.path.join(p,"images",fn)
    return QtGui.QIcon(os.path.abspath(f))


RE_URI = re.compile(r"^(https?|file|ftp)://", re.I)
def isURL(s):
    return not not RE_URI.search(s)


RE_DATA_URI = re.compile(r"^data:image/", re.I)
def isDataURL(s):
    return not not RE_DATA_URI.search(s)

