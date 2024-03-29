# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import re
import gc
import faulthandler
import signal
import zipfile
import time

from send2trash import send2trash
from aqt.qt import *
from anki import Collection
from anki.utils import  isWin, isMac, intTime, splitFields, ids2str, versionWithBuild, noOpTxtSearch
from anki.hooks import runHook, addHook, runFilter

import aqt
import aqt.progress
import aqt.webview
import aqt.toolbar
from aqt.utils import saveGeom, restoreGeom, showInfo, showWarning, \
    restoreState, getOnlyText, askUser, showText, tooltip, \
    openLink, checkInvalidFilename, openFolder
import anki.db
from anki.lang import ngettext, _


class AnkiQt(QMainWindow):
    def __init__(self, app, profileManager, args):
        QMainWindow.__init__(self)
        self.state = "startup"
        self.setAcceptDrops(True)
        aqt.mw = self
        self.app = app
        if isWin:
            self._xpstyle = QStyleFactory.create("WindowsXP")
            self.app.setStyle(self._xpstyle)

        self.pm = profileManager
        # running 2.0 for the first time?
        self.pm.meta['firstRun'] = False
        self.pm.save()

        self.night_mode = None

        # init rest of app
        if qtmajor == 4 and qtminor < 8:
            # can't get modifiers immediately on qt4.7, so no safe mode there
            self.safeMode = False
        else:
            self.safeMode = self.app.queryKeyboardModifiers() & Qt.ShiftModifier

        self.setupModules()
        self.setupUI()
        self.setupAddons()

        # must call this after ui set up
        if self.safeMode:
            tooltip(_("Shift key was held down. Skipping automatic "
                    "syncing and add-on loading."))
        # were we given a file to import?
        if args and args[0]:
            self.onAppMsg(args[0])
        # Load profile in a timer so we can let the window finish init and not
        # close on profile load error.
        if isMac and qtmajor >= 5:
            self.show()
        self.progress.timer(10, self.setupProfile, False)

    def setupUI(self):
        try:
            self.col = None
            self.setupAppMsg()
            self.setupKeys()
            self.setupThreads()
            self.setupFonts()
            self.setupMainWindow()
            self.setupSystemSpecific()
            self.setupStyle()
            self.setupMenus()
            self.setupProgress()
            self.setupErrorHandler()
            self.setupSignals()
            # self.setupAutoUpdate()
            self.setupHooks()
            self.setupRefreshTimer()
            self.updateTitleBar()
            # managers
            self.setupManagers()
            # screens
            self.setupDeckBrowser()
            self.setupOverview()
            self.setupReviewer()
        except:
            showInfo(_("Error loading UI:\n%s") % traceback.format_exc())
            sys.exit(1)

    # Profiles
    ##########################################################################

    def setupProfile(self):
        self.pendingImport = None
        self.restoringBackup = False
        # profile not provided on command line?
        if not self.pm.name:
            # if there's a single profile, load it automatically
            profs = self.pm.profiles()
            if len(profs) == 1:
                try:
                    self.pm.load(profs[0])
                except:
                    # password protected
                    pass
        if not self.pm.name:
            self.showProfileManager()
        else:
            self.loadProfile()


    def showProfileManager(self):
        self.state = "profileManager"
        d = self.profileDiag = QDialog()
        f = self.profileForm = aqt.forms.profiles.Ui_Dialog()
        f.setupUi(d)
        d.connect(f.login, SIGNAL("clicked()"), self.onOpenProfile)
        d.connect(f.profiles, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),
                  self.onOpenProfile)
        d.connect(f.quit, SIGNAL("clicked()"), lambda: sys.exit(0))
        d.connect(f.add, SIGNAL("clicked()"), self.onAddProfile)
        d.connect(f.rename, SIGNAL("clicked()"), self.onRenameProfile)
        d.connect(f.delete_2, SIGNAL("clicked()"), self.onRemProfile)
        d.connect(d, SIGNAL("rejected()"), lambda: d.close())
        self.refreshProfilesList()
        # raise first, for osx testing
        d.show()
        d.activateWindow()
        d.raise_()
        d.exec_()


    def refreshProfilesList(self):
        f = self.profileForm
        f.profiles.clear()
        profs = self.pm.profiles()
        f.profiles.addItems(profs)
        try:
            idx = profs.index(self.pm.name)
        except:
            idx = 0
        f.profiles.setCurrentRow(idx)

    def onProfileRowChange(self, n):
        if n < 0:
            # called on .clear()
            return
        name = self.pm.profiles()[n]
        f = self.profileForm
        self.pm.load(name)

    def openProfile(self):
        name = self.pm.profiles()[self.profileForm.profiles.currentRow()]
        return self.pm.load(name)

    def onOpenProfile(self):
        if not self.openProfile():
            # showWarning(_("Invalid password."))
            return
        self.profileDiag.close()
        self.loadProfile()
        return True

    def profileNameOk(self, str):
        return not checkInvalidFilename(str)

    def onAddProfile(self):
        name = getOnlyText(_("Name:"))
        if name:
            name = name.strip()
            if name in self.pm.profiles():
                return showWarning(_("Name exists."))
            if not self.profileNameOk(name):
                return
            self.pm.create(name)
            self.pm.name = name
            self.refreshProfilesList()


    def onRenameProfile(self):
        name = getOnlyText(_("New name:"), default=self.pm.name)
        if not self.openProfile():
            return showWarning(_("Invalid password."))
        if not name:
            return
        if name == self.pm.name:
            return
        if name in self.pm.profiles():
            return showWarning(_("Name exists."))
        if not self.profileNameOk(name):
            return
        self.pm.rename(name)
        self.refreshProfilesList()

    def onRemProfile(self):
        profs = self.pm.profiles()
        if len(profs) < 2:
            return showWarning(_("There must be at least one profile."))
        # password correct?
        if not self.openProfile():
            return
        # sure?
        if not askUser(_("""\
All cards, notes, and media for this profile will be deleted. \
Are you sure?""")):
            return
        self.pm.remove(self.pm.name)
        self.refreshProfilesList()

    def loadProfile(self):
        # show main window
        if self.pm.profile['mainWindowState']:
            restoreGeom(self, "mainWindow")
            restoreState(self, "mainWindow")
        else:
            self.resize(500, 400)
        # toolbar needs to be retranslated
        self.toolbar.draw()
        # titlebar
        self.setWindowTitle("Anki - " + self.pm.name)
        # show and raise window for osx
        self.show()
        self.activateWindow()
        self.raise_()
        # maybe sync (will load DB)
        if self.pendingImport and os.path.basename(
                self.pendingImport).startswith("backup-"):
            # skip sync when importing a backup
            self.loadCollection()
        else:
            self.onSync(auto=True)
        # import pending?
        if self.pendingImport:
            if self.pm.profile['key']:
                showInfo(_("""\
To import into a password protected profile, please open the profile before attempting to import."""))
            else:
                self.handleImport(self.pendingImport)

            self.pendingImport = None
        runHook("profileLoaded")

    def unloadProfile(self, browser=True):
        if not self.pm.profile:
            # already unloaded
            return
        runHook("unloadProfile")
        if not self.unloadCollection():
            return
        self.state = "profileManager"
        self.onSync(auto=True, reload=False)
        self.pm.profile['mainWindowGeom'] = self.saveGeometry()
        self.pm.profile['mainWindowState'] = self.saveState()
        self.pm.save()
        self.pm.profile = None
        self.hide()
        self.restoringBackup = False
        if browser:
            self.showProfileManager()

    def onSwitchProfile(self):
        self.form.actionSwitchProfile.setDisabled(True)
        self.unloadProfile()
        self.form.actionSwitchProfile.setDisabled(False)


    # Collection load/unload
    ##########################################################################

    def loadCollection(self):
        cpath = self.pm.collectionPath()
        try:
            self.col = Collection(cpath, log=True)
        except anki.db.DBError:
            # warn user
            showWarning(_("""\
Your collection is corrupt. Please create a new profile, then \
see the manual for how to restore from an automatic backup.

Debug info:
""")+traceback.format_exc())
            self.unloadProfile()
        except Exception as e:
            # the custom exception handler won't catch these if we immediately
            # unload, so we have to manually handle it
            if "invalidColVersion" == str(e):
                showWarning("""\
This profile requires a newer version of Anki to open. Did you forget to use the Downgrade button prior to switching Anki versions?""")
                sys.exit(1)
            if "invalidTempFolder" in repr(str(e)):
                showWarning(self.errorHandler.tempFolderMsg())
                self.unloadProfile()
                return
            self.unloadProfile()
            raise
        self.progress.setupDB(self.col.db)
        self.col.db._db.create_function(
            "filterTxtSearch", 1, noOpTxtSearch
        )
        self.maybeEnableUndo()
        self.moveToState("deckBrowser")

    def unloadCollection(self):
        """
        Unload the collection.

        This unloads a collection if there is one and returns True if
        there is no collection after the call. (Because the unload
        worked or because there was no collection to start with.)
        """
        if self.col:
            if not self.closeAllCollectionWindows():
                return
            self.progress.start(immediate=True)
            corrupt = False
            try:
                self.maybeOptimize()
            except:
                corrupt = True
            if not corrupt:
                if os.getenv("ANKIDEV", 0):
                    corrupt = False
                else:
                    corrupt = self.col.db.scalar("pragma integrity_check") != "ok"
            if corrupt:
                showWarning(_("Your collection file appears to be corrupt. \
This can happen when the file is copied or moved while Anki is open, or \
when the collection is stored on a network or cloud drive. Please see \
the manual for information on how to restore from an automatic backup."))
            self.col.close()
            self.col = None
            if not corrupt:
                self.backup()
            self.progress.finish()
        return True


    # Backup and auto-optimize
    ##########################################################################

    def backup(self):
        if os.getenv("ANKIDEV", 0):
            print("dev mode, no backups")
            return

        nbacks = self.pm.profile['numBackups']
        if not nbacks:
            print("Backup disabled")
            return

        if not self.form.actionSwitchProfile.isEnabled():
            if self.pm.profile.get(
                'ccbc.skipBackupOnSwitchProfile', False
            ):
                print("Backup skipped on switch profile")
                return
        elif self.form.actionExit.isEnabled():
            if self.pm.profile.get(
                'ccbc.skipBackupOnQuickExit', False
            ):
                print("Backup skipped on quick exit")
                return

        if self.pm.profile.get('compressBackups', True):
            zipStorage = zipfile.ZIP_DEFLATED
        else:
            zipStorage = zipfile.ZIP_STORED

        # print("Backup collection started...")
        dir = self.pm.backupFolder()
        path = self.pm.collectionPath()
        # find existing backups
        backups = []
        for file in os.listdir(dir):
            m = re.search("backup-(\d+).apkg", file)
            if not m:
                # unknown file
                continue
            backups.append((int(m.group(1)), file))
        backups.sort()

        # get next num
        n = backups[-1][0] + 1 if backups else 1
        # do backup
        newpath = os.path.join(dir, "backup-%d.apkg" % n)
        z = zipfile.ZipFile(newpath, "w", zipStorage)
        z.write(path, "collection.anki2")
        z.writestr("media", "{}")
        z.close()
        # remove if over
        if len(backups) + 1 > nbacks:
            delete = len(backups) + 1 - nbacks
            delete = backups[:delete]
            for file in delete:
                os.unlink(os.path.join(dir, file[1]))
        print("Backup completed (total:%d)" % n)

    def maybeOptimize(self):
        # have two weeks passed?
        if (intTime() - self.pm.profile['lastOptimize']) < 86400*14:
            return
        self.progress.start(label=_("Optimizing..."), immediate=True)
        try:
            self.col.optimize()
            self.pm.profile['lastOptimize'] = intTime()
            self.pm.save()
        finally:
            self.progress.finish()

    # State machine
    ##########################################################################

    def moveToState(self, state, *args):
        #print "-> move from", self.state, "to", state
        oldState = self.state or "dummy"
        cleanup = getattr(self, "_"+oldState+"Cleanup", None)
        if cleanup:
            cleanup(state)
        self.state = state
        runHook('beforeStateChange', state, oldState, *args)
        getattr(self, "_"+state+"State")(oldState, *args)
        runHook('afterStateChange', state, oldState, *args)

    def _deckBrowserState(self, oldState):
        self.deckBrowser.show()

    def _colLoadingState(self, oldState):
        "Run once, when col is loaded."
        self.enableColMenuItems()
        # ensure cwd is set if media dir exists
        self.col.media.dir()
        runHook("colLoading", self.col)
        self.moveToState("overview")

    def _selectedDeck(self):
        did = self.col.decks.selected()
        if not self.col.decks.nameOrNone(did):
            showInfo(_("Please select a deck."))
            return
        return self.col.decks.get(did)

    def _overviewState(self, oldState):
        if not self._selectedDeck():
            return self.moveToState("deckBrowser")
        self.col.reset()
        self.overview.show()

    def _reviewState(self, oldState):
        self.reviewer.show()

    def _reviewCleanup(self, newState):
        if newState != "resetRequired" and newState != "review":
            self.reviewer.cleanup()

    def noteChanged(self, nid):
        "Called when a card or note is edited (but not deleted)."
        runHook("noteChanged", nid)

    # Resetting state
    ##########################################################################

    def reset(self, guiOnly=False):
        "Called for non-trivial edits. Rebuilds queue and updates UI."
        if self.col:
            if not guiOnly:
                self.col.reset()
            runHook("reset")
            self.maybeEnableUndo()
            self.moveToState(self.state)

    def requireReset(self, modal=False):
        "Signal queue needs to be rebuilt when edits are finished or by user."
        self.autosave()
        self.resetModal = modal
        if self.interactiveState():
            self.moveToState("resetRequired")

    def interactiveState(self):
        "True if not in profile manager, syncing, etc."
        return self.state in ("overview", "review", "deckBrowser")

    def maybeReset(self):
        self.autosave()
        if self.state == "resetRequired":
            self.state = self.returnState
            self.reset()

    def delayedMaybeReset(self):
        # if we redraw the page in a button click event it will often crash on
        # windows
        self.progress.timer(100, self.maybeReset, False)

    def _resetRequiredState(self, oldState):
        if oldState != "resetRequired":
            self.returnState = oldState
        if self.resetModal:
            # we don't have to change the webview, as we have a covering window
            return
        self.web.setLinkHandler(lambda url: self.delayedMaybeReset())
        i = _("Waiting for editing to finish.")
        b = self.button("refresh", _("Resume Now"), id="resume")
        css = self.web.bundledCSS("resetRequired.css") #trigger 2.1 addons
        self.web.stdHtml("""
<center><div style="height: 100%%">
<div style="position:relative; vertical-align: middle;">
%s<br>
%s</div></div></center>
""" % (i, b), css=self.sharedCSS + css)
        self.bottomWeb.hide()
        self.web.setFocus()
        self.web.eval("$('#resume').focus()")

    # HTML helpers
    ##########################################################################

    sharedCSS = """
body {
background: #f3f3f3;
margin: 2em;
}
h1 { margin-bottom: 0.2em; }
"""

    def button(self, link, name, key=None, class_="", id=""):
        class_ = "but "+ class_
        if key:
            key = _("Shortcut key: %s") % key
        else:
            key = ""
        return '''
<button id="%s" class="%s" onclick="py.link('%s');return false;"
title="%s">%s</button>''' % (
            id, class_, link, key, name)

    # Main window setup
    ##########################################################################

    def setupMainWindow(self):
        # main window
        self.form = aqt.forms.main.Ui_MainWindow()
        self.form.setupUi(self)
        # toolbar
        tweb = aqt.webview.AnkiWebView()
        tweb.setObjectName("toolbarWeb")
        tweb.setFocusPolicy(Qt.WheelFocus)
        tweb.setFixedHeight(20+self.fontHeightDelta)
        self.toolbar = aqt.toolbar.Toolbar(self, tweb)
        self.toolbar.draw()
        # main area
        self.web = aqt.webview.AnkiWebView()
        self.web.setObjectName("mainText")
        self.web.setFocusPolicy(Qt.WheelFocus)
        self.web.setMinimumWidth(400)
        # bottom area
        sweb = self.bottomWeb = aqt.webview.AnkiWebView()
        #sweb.hide()
        sweb.setFixedHeight(100)
        sweb.setObjectName("bottomWeb")
        sweb.setFocusPolicy(Qt.WheelFocus)
        # add in a layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(tweb)
        self.mainLayout.addWidget(self.web)
        self.mainLayout.addWidget(sweb)
        self.form.centralwidget.setLayout(self.mainLayout)

    def closeAllCollectionWindows(self):
        return aqt.dialogs.closeAll()

    def hideAllCollectionWindows(self):
        aqt.dialogs.hideAll()

    def showAllCollectionWindows(self):
        aqt.dialogs.showAll()

    # Managers setup
    ##########################################################################

    def setupManagers(self):
        from aqt.view import ViewManager
        self.viewmanager = ViewManager(self)

    # Components
    ##########################################################################

    def setupSignals(self):
        signal.signal(signal.SIGINT, self.onSigInt)

    def onSigInt(self, signum, frame):
        # interrupt any current transaction and schedule a rollback & quit
        self.col.db.interrupt()
        def quit():
            self.col.db.rollback()
            self.close()
        self.progress.timer(100, quit, False)

    def setupProgress(self):
        self.progress = aqt.progress.ProgressManager(self)

    def setupErrorHandler(self):
        import aqt.errors
        self.errorHandler = aqt.errors.ErrorHandler(self)

    def setupAddons(self):
        if self.safeMode:
            return
        try:
            import aqt.addons
            self.addonManager = aqt.addons.AddonManager(self)
            self.addonManager.loadAddons()
        except:
            showInfo(_("Error loading addons:\n%s") % traceback.format_exc())
            sys.exit(1)

    def setupModules(self):
        if self.safeMode:
            return
        try:
            import aqt.modules
            self.moduleManager = aqt.modules.ModuleManager(self)
            self.moduleManager.loadModules()
        except:
            showInfo(_("Error loading modules:\n%s") % traceback.format_exc())
            sys.exit(1)

    def setupThreads(self):
        self._mainThread = QThread.currentThread()

    def inMainThread(self):
        return self._mainThread == QThread.currentThread()

    def setupDeckBrowser(self):
        from aqt.deckbrowser import DeckBrowser
        self.deckBrowser = DeckBrowser(self)

    def setupOverview(self):
        from aqt.overview import Overview
        self.overview = Overview(self)

    def setupReviewer(self):
        from aqt.reviewer import Reviewer
        self.reviewer = Reviewer(self)

    # Syncing
    ##########################################################################

    def onSync(self, auto=False, reload=True):
        if not auto or (self.pm.profile['syncKey'] and
                        self.pm.profile['autoSync'] and
                        not self.safeMode):

            try:
                from aqt.sync import SyncManager
            except:
                if not auto:
                    showInfo(_("Please install a sync module."))
                return

            if not self.unloadCollection():
                return
            # set a sync state so the refresh timer doesn't fire while deck
            # unloaded
            self.state = "sync"
            self.syncer = SyncManager(self, self.pm)
            self.syncer.sync()
        if reload:
            if not self.col:
                self.loadCollection()

    # Tools
    ##########################################################################

    def raiseMain(self):
        if not self.app.activeWindow():
            # make sure window is shown
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        return True

    def setStatus(self, text, timeout=3000):
        self.form.statusbar.showMessage(text, timeout)

    def setupStyle(self):
        buf = ""
        # allow addons to modify the styling
        buf = runFilter("setupStyle", buf)
        # allow users to extend styling
        p = os.path.join(aqt.mw.pm.base, "style.css")
        if os.path.exists(p):
            buf += open(p).read()
        self.setStyleSheet(buf)

    # Key handling
    ##########################################################################

    def setupKeys(self):
        self.keyHandler = None
        # debug shortcut
        self.debugShortcut = QShortcut(QKeySequence("Ctrl+:"), self)
        self.connect(
            self.debugShortcut, SIGNAL("activated()"), self.onDebug)

    def keyPressEvent(self, evt):
        # do we have a delegate?
        if self.keyHandler:
            # did it eat the key?
            if self.keyHandler(evt):
                return
        # run standard handler
        QMainWindow.keyPressEvent(self, evt)
        # check global keys
        key = evt.text()
        if key == "d":
            self.moveToState("deckBrowser")
        elif key == "s":
            if self.state == "overview":
                self.col.startTimebox()
                self.moveToState("review")
                if self.state == "overview":
                    tooltip(_("No cards are due yet."))
            else:
                self.moveToState("overview")
        elif key == "a":
            self.onAddCard()
        elif key == "b":
            self.onBrowse()
        elif key == "S":
            self.onStats()
        elif key == "y":
            self.onSync()

    # App exit
    ##########################################################################

    def closeWarning(self):
        if not self.pm.profile.get(
            'ccbc.warnOnQuickExit', True
        ):
            return True
        return askUser(_("Are you sure you want to exit?"))

    def onMenuExit(self):
        self.form.actionExit.setDisabled(True)
        self.close()
        self.form.actionExit.setDisabled(False)

    def closeEvent(self, event):
        "User hit the X button, etc."
        if self.state == "profileManager":
            # if profile manager active, this event may fire via OS X menu bar's
            # quit option
            self.profileDiag.close()
            event.accept()
        elif self.onClose(force=True):
            event.accept()
        else:
            event.ignore()

    def onClose(self, force=False):
        "Called from a shortcut key. Close current active window."
        aw = self.app.activeWindow()
        all_gui_closed = False

        if not aw or aw == self or force:
            if not self.closeAllCollectionWindows():
                return False
            all_gui_closed = True

        if self.form.actionExit.isEnabled():
            if not self.closeWarning():
                return False

        if all_gui_closed:
            self.unloadProfile(browser=False)
            self.app.closeAllWindows()
            return True
        aw.close()

    # Undo & autosave
    ##########################################################################

    def onUndo(self):
        n = self.col.undoName()
        if not n:
            return
        cid = self.col.undo()
        if cid and self.state == "review":
            card = self.col.getCard(cid)
            self.col.sched.reset()
            self.reviewer.cardQueue.append(card)
            self.reviewer.nextCard()
            runHook("revertedCard", cid)
        else:
            self.reset()
            tooltip(_("Reverted to state prior to '%s'.") % n.lower())
            runHook("revertedState", n)
        self.maybeEnableUndo()

    def maybeEnableUndo(self):
        if self.col and self.col.undoName():
            self.form.actionUndo.setText(_("Undo %s") %
                                            self.col.undoName())
            self.form.actionUndo.setEnabled(True)
            runHook("undoState", True)
        else:
            self.form.actionUndo.setText(_("Undo"))
            self.form.actionUndo.setEnabled(False)
            runHook("undoState", False)

    def checkpoint(self, name):
        runHook("checkpoint", name) #allows data tobe flushed
        self.col.save(name)
        self.maybeEnableUndo()

    def autosave(self):
        self.col.autosave()
        self.maybeEnableUndo()

    # Other menu operations
    ##########################################################################

    def onAddCard(self):
        from aqt import addcards
        name = "AddCards_%d"%addcards.AddCards.unique_id
        aqt.dialogs._dialogs[name] = [addcards.AddCards, None]
        instance = aqt.dialogs.open(name, self)
        addcards.AddCards.unique_id += 1

    def onBrowse(self):
        from aqt import browser
        rev = self.state=='review'
        b=aqt.dialogs.open("Browser", self, not rev)
        if rev:
            b.form.searchEdit.lineEdit().setText("is:current")
        b.onSearch()

    def onStats(self):
        deck = self._selectedDeck()
        if not deck:
            return
        from aqt import stats
        aqt.dialogs.open("DeckStats", self)

    def onEditCurrent(self):
        from aqt import editcurrent
        aqt.dialogs.open("EditCurrent", self)

    def onDeckConf(self, deck=None):
        if not deck:
            deck = self.col.decks.current()
        if deck['dyn']:
            import aqt.dyndeckconf
            aqt.dyndeckconf.DeckConf(self, deck=deck)
        else:
            import aqt.deckconf
            aqt.deckconf.DeckConf(self, deck)

    def onOverview(self):
        self.col.reset()
        self.moveToState("overview")

    def onPrefs(self):
        import aqt.preferences
        aqt.preferences.Preferences(self)

    def onNoteTypes(self):
        import aqt.models
        aqt.models.Models(self, self, fromMain=True)

    # Importing & exporting
    ##########################################################################

    def handleImport(self, path):
        import aqt.importing
        if not os.path.exists(path):
            return showInfo(_("Please use File>Import to import this file."))
        aqt.importing.importFile(self, path)

    def onImport(self):
        import aqt.importing
        aqt.importing.onImport(self)

    def onExport(self, did=None):
        import aqt.exporting
        aqt.exporting.ExportDialog(self, did=did)

    # Cramming
    ##########################################################################

    def onCram(self, search=""):
        import aqt.dyndeckconf
        n = 1
        deck = self.col.decks.current()
        if not search:
            if not deck['dyn']:
                search = 'deck:"%s" ' % deck['name']
        decks = self.col.decks.allNames()
        while _("Filtered Deck %d") % n in decks:
            n += 1
        name = _("Filtered Deck %d") % n
        did = self.col.decks.newDyn(name)
        diag = aqt.dyndeckconf.DeckConf(self, first=True, search=search)
        if not diag.ok:
            # user cancelled first config
            self.col.decks.rem(did)
            self.col.decks.select(deck['id'])

    # Menu, title bar & status
    ##########################################################################

    def setupMenus(self):
        f = self.form
        f.actionExit.triggered.connect(self.onMenuExit)
        f.actionBossKey.triggered.connect(self.boss_key)
        f.actionSwitchProfile.triggered.connect(self.onSwitchProfile)
        f.actionImport.triggered.connect(self.onImport)
        f.actionExport.triggered.connect(self.onExport)
        f.actionPreferences.triggered.connect(self.onPrefs)
        f.actionUndo.triggered.connect(self.onUndo)
        f.actionFullDatabaseCheck.triggered.connect(self.onCheckDB)
        f.actionCheckMediaDatabase.triggered.connect(self.onCheckMediaDB)
        f.actionStudyDeck.triggered.connect(self.onStudyDeck)
        f.actionCreateFiltered.triggered.connect(self.onCram)
        f.actionEmptyCards.triggered.connect(self.onEmptyCards)
        f.actionNoteTypes.triggered.connect(self.onNoteTypes)

    def updateTitleBar(self):
        self.setWindowTitle("CCBC")

    # Auto update
    ##########################################################################

    def setupAutoUpdate(self):
        pass

    def newVerAvail(self, ver):
        pass

    def newMsg(self, data):
        aqt.update.showMessages(self, data)

    def clockIsOff(self, diff):
        diffText = ngettext("%s second", "%s seconds", diff) % diff
        warn = _("""\
In order to ensure your collection works correctly when moved between \
devices, Anki requires your computer's internal clock to be set correctly. \
The internal clock can be wrong even if your system is showing the correct \
local time.

Please go to the time settings on your computer and check the following:

- AM/PM
- Clock drift
- Day, month and year
- Timezone
- Daylight savings

Difference to correct time: %s.""") % diffText
        showWarning(warn)
        self.app.closeAllWindows()

    # Count refreshing
    ##########################################################################

    def setupRefreshTimer(self):
        # every 10 minutes
        self.progress.timer(10*60*1000, self.onRefreshTimer, True)

    def onRefreshTimer(self):
        if not self.col:
            return #exiting anki
        if self.state == "deckBrowser":
            self.deckBrowser.refresh()
        elif self.state == "overview":
            self.overview.refresh()

    # Permanent libanki hooks
    ##########################################################################

    def setupHooks(self):
        addHook("modSchema", self.onSchemaMod)
        addHook("remNotes", self.onRemNotes)
        addHook("odueInvalid", self.onOdueInvalid)

    def onOdueInvalid(self):
        showWarning(_("""\
Invalid property found on card. Please use Tools>Check Database, \
and if the problem comes up again, please ask on the support site."""))

    # Log note deletion
    ##########################################################################

    def onRemNotes(self, col, nids):
        path = os.path.join(self.pm.profileFolder(), "deleted.txt")
        existed = os.path.exists(path)
        with open(path, 'a', encoding='utf-8') as f:
            if not existed:
                f.write("nid\tmid\tfields\n")
            for id, mid, flds in col.db.execute(
                    "select id, mid, flds from notes where id in %s" %
                ids2str(nids)):
                fields = splitFields(flds)
                f.write(("\t".join([str(id), str(mid)] + fields)))
                f.write("\n")

    # Schema modifications
    ##########################################################################

    def onSchemaMod(self, arg):
        return askUser(_("""\
The requested change will require a full upload of the database when \
you next synchronize your collection. If you have reviews or other changes \
waiting on another device that haven't been synchronized here yet, they \
will be lost. Continue?"""))

    # Advanced features
    ##########################################################################

    def onCheckDB(self):
        "True if no problems"
        self.progress.start(immediate=True)
        try:
            ret, ok = self.col.fixIntegrity()
        finally:
            self.progress.finish()
        if not ok:
            showText(ret)
        else:
            tooltip(ret)
        self.reset()
        return ret

    def onCheckMediaDB(self):
        self.progress.start(immediate=True)
        try:
            (nohave, unused, invalid) = self.col.media.check()
        finally:
            self.progress.finish()
        # generate report
        report = ""
        if invalid:
            report += _("Invalid encoding; please rename:")
            report += "\n" + "\n".join(invalid)
        if unused:
            numberOfUnusedFilesLabel = len(unused)
            if report:
                report += "\n\n\n"
            report += ngettext("%d file found in media folder not used by any cards:",
                "%d files found in media folder not used by any cards:",
                numberOfUnusedFilesLabel) % numberOfUnusedFilesLabel
            report += "\n" + "\n".join(unused)
        if nohave:
            if report:
                report += "\n\n\n"
            report += _(
                "Used on cards but missing from media folder:")
            report += "\n" + "\n".join(nohave)
        if not report:
            tooltip(_("No unused or missing files found."))
            return
        # show report and offer to delete
        diag = QDialog(self)
        diag.setWindowTitle("Anki")
        layout = QVBoxLayout(diag)
        diag.setLayout(layout)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(report)
        layout.addWidget(text)
        box = QDialogButtonBox(QDialogButtonBox.Close)
        layout.addWidget(box)
        if unused:
            b = QPushButton(_("Delete Unused"))
            b.setAutoDefault(False)
            b.clicked.connect(lambda:self.deleteUnused(unused,diag))
            box.addButton(b, QDialogButtonBox.ActionRole)
            b = QPushButton(_("Explore Unused"))
            b.setAutoDefault(False)
            b.clicked.connect(lambda:openFolder(self.pm.mediaFolder()))
            box.addButton(b, QDialogButtonBox.ActionRole)
        if nohave:
            b = QPushButton(_("Browse Missing"))
            b.setAutoDefault(False)
            b.clicked.connect(lambda:self.browseMissingMedia(nohave,diag))
            box.addButton(b, QDialogButtonBox.ActionRole)
        diag.connect(box, SIGNAL("rejected()"), diag, SLOT("reject()"))
        diag.setMinimumHeight(400)
        diag.setMinimumWidth(500)
        restoreGeom(diag, "checkmediadb")
        diag.exec_()
        saveGeom(diag, "checkmediadb")

    def browseMissingMedia(self, nohave, diag):
        #dialog blocks browser from being usable
        diag.close()
        from aqt import mw, dialogs
        browser = dialogs.open("Browser", mw, False)
        browser.form.searchEdit.lineEdit().setText("tag:MissingMedia")
        browser.onSearchActivated()

    def deleteUnused(self, unused, diag):
        if not askUser(
            _("Delete unused media?")):
            return
        mdir = self.col.media.dir()
        self.progress.start(immediate=True)
        try:
            numberOfFilesDeleted = 0
            lastProgress = 0
            for c, f in enumerate(unused):
                path = os.path.join(mdir, f)
                if os.path.exists(path):
                    send2trash(path)
                    numberOfFilesDeleted += 1
                now = time.time()
                if now - lastProgress >= 0.3:
                    numberOfRemainingFilesToBeDeleted = len(unused) - c
                    lastProgress = now
                    label = ngettext(
                        "%d file remaining...",
                        "%d files remaining...",
                        numberOfRemainingFilesToBeDeleted
                    ) % numberOfRemainingFilesToBeDeleted
                    self.progress.update(label)
        finally:
            self.progress.finish()
        tooltip(ngettext(
            "Deleted %d file.",
            "Deleted %d files.",
            numberOfFilesDeleted
        ) % numberOfFilesDeleted )
        diag.close()

    def onStudyDeck(self):
        from aqt.studydeck import StudyDeck
        ret = StudyDeck(
            self, dyn=True, current=self.col.decks.current()['name'])
        if ret.name:
            self.col.decks.select(self.col.decks.id(ret.name))
            self.moveToState("overview")

    def onEmptyCards(self):
        def browseCards(cids):
            from aqt import dialogs
            browser = dialogs.open("Browser", self, False)
            browser.form.searchEdit.lineEdit().setText("cid:%s"%ids2str(cids))
            browser.onSearchActivated()

        self.progress.start(immediate=True)
        try:
            cids = self.col.emptyCids()
            if not cids:
                self.progress.finish()
                tooltip(_("No empty cards."))
                return
            report = self.col.emptyCardReport(cids)
        finally:
            self.progress.finish()
        part1 = ngettext("%d card", "%d cards", len(cids)) % len(cids)
        part1 = _("%s to delete:") % part1
        diag, box = showText(part1 + "\n\n" + report, run=False,
                geomKey="emptyCards")
        b = QPushButton(_("Browse Cards"))
        b.setAutoDefault(False)
        b.clicked.connect(lambda:browseCards(cids))
        box.addButton(b, QDialogButtonBox.ActionRole)
        box.addButton(_("Delete Cards"), QDialogButtonBox.AcceptRole)
        box.button(QDialogButtonBox.Close).setDefault(True)
        from ccbc.plugins.Keep_empty_note.keep_empty_note import onDelete
        box.accepted.connect(lambda:onDelete(self,diag,cids))
        diag.show()

    # Debugging
    ######################################################################

    def onDebug(self):
        d = self.debugDiag = QDialog()
        frm = aqt.forms.debug.Ui_Dialog()
        frm.setupUi(d)
        s = self.debugDiagShort = QShortcut(QKeySequence("ctrl+return"), d)
        self.connect(s, SIGNAL("activated()"),
                     lambda: self.onDebugRet(frm))
        s = self.debugDiagShort = QShortcut(
            QKeySequence("ctrl+shift+return"), d)
        self.connect(s, SIGNAL("activated()"),
                     lambda: self.onDebugprint(frm))
        d.show()

    def _captureOutput(self, on):
        mw = self
        class Stream(object):
            def write(self, data):
                mw._output += data
        if on:
            self._output = ""
            self._oldStderr = sys.stderr
            self._oldStdout = sys.stdout
            s = Stream()
            sys.stderr = s
            sys.stdout = s
        else:
            sys.stderr = self._oldStderr
            sys.stdout = self._oldStdout

    def _debugCard(self):
        return self.reviewer.card.__dict__

    def _debugBrowserCard(self):
        return aqt.dialogs._dialogs['Browser'][1].card.__dict__

    def onDebugprint(self, frm):
        frm.text.setPlainText("pp(%s)" % frm.text.toPlainText())
        self.onDebugRet(frm)

    def onDebugRet(self, frm):
        import pprint, traceback
        text = frm.text.toPlainText()
        card = self._debugCard
        bcard = self._debugBrowserCard
        mw = self
        pp = pprint.pprint
        self._captureOutput(True)
        try:
            exec(text)
        except:
            self._output += traceback.format_exc()
        self._captureOutput(False)
        buf = ""
        for c, line in enumerate(text.strip().split("\n")):
            if c == 0:
                buf += ">>> %s\n" % line
            else:
                buf += "... %s\n" % line
        try:
            frm.log.appendPlainText(buf + (self._output or "<no output>"))
        except UnicodeDecodeError:
            frm.log.appendPlainText(_("<non-unicode text>"))
        frm.log.ensureCursorVisible()

    # System specific code
    ##########################################################################

    def setupFonts(self):
        f = QFontInfo(self.font())
        ws = QWebSettings.globalSettings()
        self.fontHeight = f.pixelSize()
        self.fontFamily = f.family()
        self.fontHeightDelta = max(0, self.fontHeight - 13)
        ws.setFontFamily(QWebSettings.StandardFont, self.fontFamily)
        ws.setFontSize(QWebSettings.DefaultFontSize, self.fontHeight)

    def setupSystemSpecific(self):
        self.hideMenuAccels = False
        if isMac:
            # mac users expect a minimize option
            self.minimizeShortcut = QShortcut("Ctrl+M", self)
            self.connect(self.minimizeShortcut, SIGNAL("activated()"),
                         self.onMacMinimize)
            self.hideMenuAccels = True
            self.maybeHideAccelerators()
            self.hideStatusTips()
        elif isWin:
            # make sure ctypes is bundled
            from ctypes import windll, wintypes
            _dummy = windll
            _dummy = wintypes

    def maybeHideAccelerators(self, tgt=None):
        if not self.hideMenuAccels:
            return
        tgt = tgt or self
        for action in tgt.findChildren(QAction):
            txt = action.text()
            m = re.match("^(.+)\(&.+\)(.+)?", txt)
            if m:
                action.setText(m.group(1) + (m.group(2) or ""))

    def hideStatusTips(self):
        for action in self.findChildren(QAction):
            action.setStatusTip("")

    def onMacMinimize(self):
        self.setWindowState(self.windowState() | Qt.WindowMinimized)

    # Single instance support
    ##########################################################################

    def setupAppMsg(self):
        self.connect(self.app, SIGNAL("appMsg"), self.onAppMsg)

    def onAppMsg(self, buf):
        if self.state == "startup":
            # try again in a second
            return self.progress.timer(1000, lambda: self.onAppMsg(buf), False)
        elif self.state == "profileManager":
            # can't raise window while in profile manager
            if buf == "raise":
                return
            self.pendingImport = buf
            return tooltip(_("Deck will be imported when a profile is opened."))
        if not self.interactiveState() or self.progress.busy():
            # we can't raise the main window while in profile dialog, syncing, etc
            if buf != "raise":
                showInfo(_("""\
Please ensure a profile is open and Anki is not busy, then try again."""),
                     parent=None)
            return
        # raise window
        if isWin:
            # on windows we can raise the window by minimizing and restoring
            self.showMinimized()
            self.setWindowState(Qt.WindowActive)
            self.showNormal()
        else:
            # on osx we can raise the window. on unity the icon in the tray will just flash.
            self.activateWindow()
            self.raise_()
        if buf == "raise":
            return
        # import
        # if not isinstance(buf, unicode):
            # buf = unicode(buf, "utf8", "ignore")

        self.handleImport(buf)




    # GC
    ##########################################################################
    # ensure gc runs in main thread

    def setupDialogGC(self, obj):
        obj.finished.connect(lambda: self.gcWindow(obj))

    def gcWindow(self, obj):
        obj.deleteLater()
        self.progress.timer(1000, self.doGC, False)

    def disableGC(self):
        gc.collect()
        gc.disable()

    def doGC(self):
        assert not self.progress.inDB
        gc.collect()



    # Crash log
    ##########################################################################

    def setupCrashLog(self):
        p = os.path.join(self.pm.base, "crash.log")
        self._crashLog = open(p, "ab", 0)
        faulthandler.enable(self._crashLog)

    def onAbout(self):
        from aqt.utils import supportText, showText
        addmgr = self.addonManager
        addons = "\n".join(addmgr.annotatedName(d) for d in addmgr.allAddons())
        info = "\n".join((supportText(), "Add-ons:\n\n{}".format(addons)))
        showText(info)


    # Handle Drag n Drop
    ##########################################################################

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if not mime.hasUrls():
            return None
        for url in mime.urls():
            f = url.toLocalFile()
            _,ext = os.path.splitext(f)
            ext = ext.lower()
            if ext == self.addonManager.ext:
                self.addonManager.onAddonsDialog()
                #passes the ball to addonManager's dragEnterEvent
                break

    # def dropEvent(self, evt):
        # Nothing drops here, no focus
        # see aqt.webview
        # pass

    # Media server
    ##########################################################################

    # def setupMediaServer(self):
        # self.mediaServer = aqt.mediasrv.MediaServer(self)
        # self.mediaServer.start()

    # def baseHTML(self):
        # return '<base href="%s">' % self.serverURL()

    # def serverURL(self):
        # return "http://127.0.0.1:%d/" % self.mediaServer.getPort()


    # Boss key (privacy mode)
    ##########################################################################

    def boss_key(self):
        cmd = self.pm.profile.get("ccbc.bossCmd","notepad.exe")
        if not cmd:
            # TODO: Write gui for this option
            #   Use debugger to set command for ccbc.bossCmd
            showInfo("No external text editor was set.")
            return
        if isWin:
            cmd = cmd.replace('/','\\')

        anki.sound.clearAudioQueue()

        import subprocess, time
        from anki.utils import tmpdir
        fname = os.path.join(tmpdir(), "note%d.txt"%time.time())

        f = open(fname, "w")
        f.write(self.pm.profile.get("ccbc.bossText","To Whom It May Concern:"))
        f.close()

        runHook("BOSS_KEY", True)
        self.hideAllCollectionWindows()
        self.hide()
        try:
            self.debugDiag.close()
        except AttributeError: pass

        self.pm.save()
        self.col.autosave()

        subprocess.call('''%s "%s"'''%(cmd,fname), shell=True)
        self.show()
        self.showAllCollectionWindows()
        runHook("BOSS_KEY", False)
