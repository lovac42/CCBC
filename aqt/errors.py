# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

import sys, traceback
import html
import re

from anki.lang import _
from aqt.qt import *
from aqt.utils import showText, showWarning, supportText
from aqt import mw

if not os.environ.get("DEBUG"):
    def excepthook(etype,val,tb):
        sys.stderr.write("Caught exception:\n%s\n" % (
            ''.join(traceback.format_exception(etype, val, tb))))
    sys.excepthook = excepthook

class ErrorHandler(QObject):
    "Catch stderr and write into buffer."
    ivl = 100

    errorTimer = pyqtSignal()

    def __init__(self, mw):
        QObject.__init__(self, mw)
        self.mw = mw
        self.timer = None
        self.errorTimer.connect(self._setTimer)
        self.pool = ""
        self._oldstderr = sys.stderr
        sys.stderr = self

    def unload(self):
        sys.stderr = self._oldstderr
        sys.excepthook = None

    def write(self, data):
        # dump to stdout
        sys.stdout.write(data)
        # save in buffer
        self.pool += data
        # and update timer
        self.setTimer()

    def setTimer(self):
        # we can't create a timer from a different thread, so we post a
        # message to the object on the main thread
        self.errorTimer.emit()

    def _setTimer(self):
        if not self.timer:
            self.timer = QTimer(self.mw)
            self.timer.timeout.connect(self.onTimeout)
        self.timer.setInterval(self.ivl)
        self.timer.setSingleShot(True)
        self.timer.start()

    def tempFolderMsg(self):
        return _("""Unable to access Anki media folder. The permissions on \
your system's temporary folder may be incorrect.""")

    def onTimeout(self):
        error = html.escape(self.pool)
        self.pool = ""
        self.mw.progress.clear()
        if "abortSchemaMod" in error:
            return
        if "10013" in error:
            return showWarning(_("Your firewall or antivirus program is preventing Anki from creating a connection to itself. Please add an exception for Anki."))
        if "Pyaudio not" in error:
            return showWarning(_("Please install PyAudio"))
        if "install mplayer" in error:
            return showWarning(_("Sound and video on cards will not function until mpv or mplayer is installed."))
        if "no default input" in error.lower():
            return showWarning(_("Please connect a microphone, and ensure "
                                 "other programs are not using the audio device."))
        if "invalidTempFolder" in error:
            return showWarning(self.tempFolderMsg())
        if "Beautiful Soup is not an HTTP client" in error:
            return
        if "database or disk is full" in error:
            return showWarning(_("Your computer's storage may be full. Please delete some unneeded files, then try again."))
        if "disk I/O error" in error:
            return showWarning(_("""\
An error occurred while accessing the database.

Possible causes:

- Antivirus, firewall, backup, or synchronization software may be \
  interfering with Anki. Try disabling such software and see if the \
  problem goes away.
- Your disk may be full.
- The Documents/Anki folder may be on a network drive.
- Files in the Documents/Anki folder may not be writeable.
- Your hard disk may have errors.

It's a good idea to run Tools>Check Database to ensure your collection \
is not corrupt.
"""))

        stdText = _("""\
<h1>Error</h1>
<p>An error occurred. Please use <b>Tools &gt; Check Database</b> to see if \
that fixes the problem.</p>

<p>If problems persist, you are SOL.</p>""")


        pluginText = _("""\
<h1>Error</h1>

<p>An error occurred. Please start CCBC while holding down the shift \
key, which will temporarily disable the add-ons you have installed.</p>

<p>If the issue only occurs when add-ons are enabled, please use the \
Add-ons config manager to disable some add-ons and restart CCBC, \
repeat this step until you discover the add-on that is causing the problem.</p>

<p>Obviously, no support is given, so you're SOL.</p>

<p>Debug info:</p>
""")

        # if self.mw.addonManager.dirty:
        if "addon" in error:
            txt = pluginText
            error = supportText() + self._addonText(error) + "\n" + error
        else:
            txt = stdText
            error = supportText() + "\n" + error

        # show dialog
        txt = txt + "<div style='white-space: pre-wrap'>" + error + "</div>"
        showText(txt, type="html", copyBtn=True)

    def _addonText(self, error):
        matches = re.findall(r"addonz/(.*?)/", error)
        if not matches:
            return ""
        # reverse to list most likely suspect first, dict to deduplicate:
        addons = [mw.addonManager.addonName(i) for i in
                  dict.fromkeys(reversed(matches))]
        txt = _("""Add-ons possibly involved: {}\n""")
        # highlight importance of first add-on:
        addons[0] = "<b>{}</b>".format(addons[0])
        return txt.format(", ".join(addons))

    def flush(self):
        # no-op to avoid pyinstaller exit warning
        pass
