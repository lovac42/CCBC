# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

from aqt.qt import *

import time, sys, pyaudio
from anki.sound import Recorder
from aqt.utils import saveGeom, restoreGeom, showWarning
from anki.lang import _

if not Recorder:
    print("pyaudio not installed")

def getAudio(parent, encode=True):
    "Record and return filename"
    # record first
    if not Recorder:
        showWarning("pyaudio not installed")
        return

    r = Recorder()
    mb = QMessageBox(parent)
    restoreGeom(mb, "audioRecorder")
    mb.setWindowTitle("Anki")
    mb.setIconPixmap(QPixmap(":/icons/media-record.png"))
    but = QPushButton(_("Save"))
    mb.addButton(but, QMessageBox.AcceptRole)
    but.setDefault(True)
    but = QPushButton(_("Cancel"))
    mb.addButton(but, QMessageBox.RejectRole)
    mb.setEscapeButton(but)
    t = time.time()
    r.start()
    time.sleep(r.startupDelay)
    QApplication.instance().processEvents()
    while not mb.clickedButton():
        txt =_("Recording...<br>Time: %0.1f")
        mb.setText(txt % (time.time() - t))
        mb.show()
        QApplication.instance().processEvents()
    if mb.clickedButton() == mb.escapeButton():
        r.stop()
        r.cleanup()
        return
    saveGeom(mb, "audioRecorder")
    # ensure at least a second captured
    while time.time() - t < 1:
        time.sleep(0.1)
    r.stop()
    # process
    r.postprocess(encode)
    return r.file()


def getMics(last=""):
    p = pyaudio.PyAudio()
    mics=['Auto']
    cnt=1
    for idx in range(p.get_device_count()):
        dev=p.get_device_info_by_index(idx)
        if dev['maxInputChannels']:
            nameAndSamp="%s, %d"%(dev['name'],dev['defaultSampleRate'])
            if nameAndSamp==last:
                return cnt
            mics.append("%d:%s, %d"%(idx,dev['name'],dev['defaultSampleRate']))
            cnt += 1
    return mics
