# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC

import getpass
import os
import sys
import argparse
import tempfile
import builtins
import locale
import gettext

from aqt.qt import *
import anki.lang
from anki.lang import langDir
from anki.utils import isMac, isWin
from anki import version as _version
from anki.lang import _
from builtins import str
from aqt import pinnedmodules


appVersion=_version
# appWebsite="http://google.com/appWebsite"
# appChanges="http://google.com/appChanges"
# appDonate="http://google.com/appDonate"
appShared="https://ankiweb.net/shared/"
# appUpdate="http://google.com/appUpdate"
mw = None # set on init

moduleDir = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

try:
    import aqt.forms
except ImportError as e:
    if "forms" in str(e):
        print("If you're running from git, did you run build_ui.sh?")
        print()
    raise

from anki.utils import checksum

# Dialog manager - manages modeless windows
##########################################################################
from aqt import addcards, browser, editcurrent, preferences, stats


class DialogManager(object):

    _dialogs = {
        "Preferences": [preferences.Preferences, None],
        # "AddCards": [addcards.AddCards, None],
        "EditCurrent": [editcurrent.EditCurrent, None],
        "Browser": [browser.Browser, None],
        "DeckStats": [stats.DeckStats, None]
    }

    def open(self, name, *args):
        (creator, instance) = self._dialogs[name]
        if instance:
            if instance.windowState() & Qt.WindowMinimized:
                instance.setWindowState(instance.windowState() & ~Qt.WindowMinimized)
            instance.activateWindow()
            instance.raise_()
            if hasattr(instance,"reopen"):
                instance.reopen(*args)
        else:
            instance = creator(*args)
            self._dialogs[name][1] = instance
        return instance

    def markClosed(self, name): #2.1
        self._dialogs[name] = [self._dialogs[name][0], None]

    def close(self, name): #2.0
        self._dialogs[name] = [self._dialogs[name][0], None]

    def allClosed(self): #2.1
        return not any(x[1] for x in self._dialogs.values())

    def closeAll(self): #v2.1 uses callbacks
        "True if all closed successfully."
        for (name, (creator, instance)) in self._dialogs.items():
            if instance:
                if not instance.canClose():
                    return False
                instance.forceClose = True
                instance.close()
                self.close(name)
        return True

    def hideAll(self):
        for (name, (creator, instance)) in self._dialogs.items():
            if instance:
                instance.hide()

    def showAll(self):
        for (name, (creator, instance)) in self._dialogs.items():
            if instance:
                instance.show()

dialogs = DialogManager()

# Language handling
##########################################################################
# Qt requires its translator to be installed before any GUI widgets are
# loaded, and we need the Qt language to match the gettext language or
# translated shortcuts will not work.

_gtrans = None
_qtrans = None

def setupLang(pm, app, force=None):
    global _gtrans, _qtrans
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass
    lang = force or pm.meta["defaultLang"]
    dir = langDir()
    # gettext
    _gtrans = gettext.translation(
        'anki', dir, languages=[lang], fallback=True)
    def fn__(arg):
        print("accessing _ without importing from anki.lang will break in the future")
        print("".join(traceback.format_stack()[-2]))
        from anki.lang import _
        return _(arg)
    def fn_ngettext(a, b, c):
        print("accessing ngettext without importing from anki.lang will break in the future")
        print("".join(traceback.format_stack()[-2]))
        from anki.lang import ngettext
        return ngettext(a, b, c)

    builtins.__dict__['_'] = fn__
    builtins.__dict__['ngettext'] = fn_ngettext
    anki.lang.setLang(lang, local=False)
    if lang in ("he","ar","fa"):
        app.setLayoutDirection(Qt.RightToLeft)
    else:
        app.setLayoutDirection(Qt.LeftToRight)
    # qt
    _qtrans = QTranslator()
    if _qtrans.load("qt_" + lang, dir):
        app.installTranslator(_qtrans)

# App initialisation
##########################################################################

class AnkiApp(QApplication):

    # Single instance support on Win32/Linux
    ##################################################

    appMsg = pyqtSignal(str)

    KEY = None #set later
    TMOUT = 30000

    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self._argv = argv

    def secondInstance(self):
        # we accept only one command line argument. if it's missing, send
        # a blank screen to just raise the existing window
        opts, args = parseArgs(self._argv)
        self.KEY = "anki"+checksum(opts.base+opts.profile+getpass.getuser())

        buf = "raise"
        if args and args[0]:
            buf = os.path.abspath(args[0])
        if self.sendMsg(buf):
            print("Already running; reusing existing instance.")
            return True
        else:
            # send failed, so we're the first instance or the
            # previous instance died
            QLocalServer.removeServer(self.KEY)
            self._srv = QLocalServer(self)
            self._srv.newConnection.connect(self.onRecv)
            self._srv.listen(self.KEY)
            return False

    def sendMsg(self, txt):
        sock = QLocalSocket(self)
        sock.connectToServer(self.KEY, QIODevice.WriteOnly)
        if not sock.waitForConnected(self.TMOUT):
            # first instance or previous instance dead
            return False
        sock.write(txt.encode("utf8"))
        if not sock.waitForBytesWritten(self.TMOUT):
            # existing instance running but hung
            QMessageBox.warning(
                None, "Anki Already Running",
                "If the existing instance of Anki is not responding, please close it using your task manager, or restart your computer.")
            sys.exit(1)
        sock.disconnectFromServer()
        return True

    def onRecv(self):
        sock = self._srv.nextPendingConnection()
        if not sock.waitForReadyRead(self.TMOUT):
            sys.stderr.write(sock.errorString())
            return
        path = bytes(sock.readAll()).decode("utf8")
        self.appMsg.emit(path)
        sock.disconnectFromServer()

    # OS X file/url handler
    ##################################################

    def event(self, evt):
        if evt.type() == QEvent.FileOpen:
            self.appMsg.emit(evt.file() or "raise")
            return True
        return QApplication.event(self, evt)



def parseArgs(argv):
    "Returns (opts, args)."
    # py2app fails to strip this in some instances, then anki dies
    # as there's no such profile
    if isMac and len(argv) > 1 and argv[1].startswith("-psn"):
        argv = [argv[0]]
    parser = argparse.ArgumentParser(description="CCBC " + appVersion)
    parser.usage = "%(prog)s [OPTIONS] [file to import]"
    parser.add_argument("-b", "--base", help="path to base folder", default="")
    parser.add_argument("-p", "--profile", help="profile name to load", default="")
    parser.add_argument("-l", "--lang", help="interface language (en, de, etc)")
    parser.add_argument("-d", "--dev", help="run in dev mode", action='store_true')
    opts,args = parser.parse_known_args(argv[1:])
    if isWin and not opts.base:
        portable = os.path.dirname(os.path.dirname(__file__))
        portFile = os.path.join(portable, "portable.dat")
        if os.path.exists(os.path.join(portable, "portable.dat")):
            opts.base = os.path.join(portable,"Data")
    return opts,args


def run():
    try:
        _run()
    except Exception as e:
        # traceback.print_exc()
        QMessageBox.critical(None, "Startup Error",
                             "Please notify support of this error:\n\n"+
                             traceback.format_exc())

def _run(argv=None, exec=True):
    """Start AnkiQt application or reuse an existing instance if one exists.

    If the function is invoked with exec=False, the AnkiQt will not enter
    the main event loop - instead the application object will be returned.

    The 'exec' and 'argv' arguments will be useful for testing purposes.

    If no 'argv' is supplied then 'sys.argv' will be used.
    """
    global mw

    if argv is None:
        argv = sys.argv

    # parse args
    opts, args = parseArgs(argv)
    opts.base = opts.base or ""
    opts.profile = opts.profile or ""
    if opts.dev:
        os.environ["ANKIDEV"] = "1"
        print("running in dev mode")

    if isMac:
        if getattr(sys, 'frozen', None):
            # on osx we'll need to add the qt plugins to the search path
            rd = os.path.abspath(moduleDir + "/../../..")
            QCoreApplication.setLibraryPaths([rd])
        QFont.insertSubstitution(".Lucida Grande UI", "Lucida Grande")

    # create the app
    QCoreApplication.setApplicationName("Anki")
    app = AnkiApp(argv)
    if app.secondInstance():
        # we've signaled the primary instance, so we should close
        return

    # disable icons on mac; this must be done before window created
    if isMac:
        app.setAttribute(Qt.AA_DontShowIconsInMenus)

    # disable help button in title bar on qt versions that support it
    if isWin and qtminor >= 10:
        QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton)


    # we must have a usable temp dir
    try:
        tempfile.gettempdir()
    except:
        QMessageBox.critical(
            None, "Error", """\
No usable temporary folder found. Make sure C:\\temp exists or TEMP in your \
environment points to a valid, writable folder.""")
        return

    # qt version must be up to date
    if qtmajor <= 4 and qtminor <= 6:
        QMessageBox.warning(
            None, "Error", "Your Qt version is known to be buggy. Until you "
          "upgrade to a newer Qt, you may experience issues such as images "
          "failing to show up during review.")

    # profile manager
    from aqt.profiles import ProfileManager
    pm = ProfileManager(opts.base, opts.profile)

    # i18n
    setupLang(pm, app, opts.lang)

    # remaining pm init
    pm.ensureProfile()

    # load the main window
    import aqt.main
    mw = aqt.main.AnkiQt(app, pm, args)
    if exec:
        app.exec_()
    else:
        return app
