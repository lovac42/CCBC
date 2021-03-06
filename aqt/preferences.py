# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import datetime, time
import anki.lang
import aqt
from aqt.qt import *
from aqt.utils import openFolder, showInfo, askUser
from aqt.sound import getMics
from anki.lang import _
from anki.hooks import runHook
from anki.utils import isWin


class Preferences(QDialog):

    def __init__(self, mw):
        if not mw.col:
            showInfo(_("Please open a profile first."))
            return
        QDialog.__init__(self, mw, Qt.Window)
        mw.setupDialogGC(self)
        self.mw = mw
        self.prof = self.mw.pm.profile
        self.form = aqt.forms.preferences.Ui_Preferences()
        self.form.setupUi(self)
        self.form.buttonBox.button(QDialogButtonBox.Close).setAutoDefault(False)
        self.silentlyClose = True
        self.setupLang()
        self.setupCollection()
        self.setupNetwork()
        self.setupBackup()
        self.setupOptions()
        self.show()

    def accept(self):
        # avoid exception if main window is already closed
        if not self.mw.col:
            return
        self.updateCollection()
        self.updateNetwork()
        self.updateBackup()
        self.updateOptions()
        self.mw.pm.save()
        self.mw.reset()
        self.done(0)
        aqt.dialogs.markClosed("Preferences")
        runHook('profileChanged')

    def reject(self):
        self.accept()

    # Language
    ######################################################################

    def setupLang(self):
        f = self.form
        f.lang.addItems([x[0] for x in anki.lang.langs])
        f.lang.setCurrentIndex(self.langIdx())
        f.lang.currentIndexChanged.connect(self.onLangIdxChanged)

    def langIdx(self):
        codes = [x[1] for x in anki.lang.langs]
        try:
            return codes.index(anki.lang.getLang())
        except:
            return codes.index("en_US")

    def onLangIdxChanged(self, idx):
        code = anki.lang.langs[idx][1]
        self.mw.pm.setLang(code)
        showInfo(_("Please restart Anki to complete language change."), parent=self)

    # Collection options
    ######################################################################

    def setupCollection(self):
        import anki.consts as c
        f = self.form
        qc = self.mw.col.conf
        self._setupDayCutoff()
        # if isMac:
            # f.hwAccel.setVisible(False)
        # else:
            # f.hwAccel.setChecked(self.mw.pm.glMode() != "software")
        f.lrnCutoff.setValue(qc['collapseTime']/60.0)
        f.timeLimit.setValue(qc['timeLim']/60.0)
        f.showEstimates.setChecked(qc['estTimes'])
        f.showProgress.setChecked(qc['dueCounts'])
        # f.nightMode.setChecked(qc.get("nightMode", False))
        f.newSpread.addItems(list(c.newCardSchedulingLabels().values()))
        f.newSpread.setCurrentIndex(qc['newSpread'])
        f.useCurrent.setCurrentIndex(int(not qc.get("addToCur", True)))
        f.dayLearnFirst.setChecked(qc.get("dayLearnFirst", False))
        if self.mw.col.schedVer() != 2:
            f.dayLearnFirst.setVisible(False)
        else:
            f.newSched.setChecked(True)

    def updateCollection(self):
        f = self.form
        d = self.mw.col

        # if not isMac:
            # wasAccel = self.mw.pm.glMode() != "software"
            # wantAccel = f.hwAccel.isChecked()
            # if wasAccel != wantAccel:
                # if wantAccel:
                    # self.mw.pm.setGlMode("auto")
                # else:
                    # self.mw.pm.setGlMode("software")
                # showInfo(_("Changes will take effect when you restart Anki."))

        qc = d.conf
        qc['dueCounts'] = f.showProgress.isChecked()
        qc['estTimes'] = f.showEstimates.isChecked()
        qc['newSpread'] = f.newSpread.currentIndex()
        # qc['nightMode'] = f.nightMode.isChecked()
        qc['timeLim'] = f.timeLimit.value()*60
        qc['collapseTime'] = f.lrnCutoff.value()*60
        qc['addToCur'] = not f.useCurrent.currentIndex()
        qc['dayLearnFirst'] = f.dayLearnFirst.isChecked()
        self._updateDayCutoff()
        self._updateSchedVer(f.newSched.isChecked())
        d.setMod()

    # Scheduler version
    ######################################################################

    def _updateSchedVer(self, wantNew):
        haveNew = self.mw.col.schedVer() == 2

        # nothing to do?
        if haveNew == wantNew:
            return

        if not askUser(
            _(
                "This will reset any cards in learning, clear filtered decks, and change the scheduler version. Proceed?"
            )
        ):
            return

        if wantNew:
            self.mw.col.changeSchedulerVer(2)
        else:
            self.mw.col.changeSchedulerVer(1)

    # Day cutoff
    ######################################################################

    def _setupDayCutoff(self):
        if self.mw.col.schedVer() == 2:
            self._setupDayCutoffV2()
        else:
            self._setupDayCutoffV1()

    def _setupDayCutoffV1(self):
        self.startDate = datetime.datetime.fromtimestamp(self.mw.col.crt)
        self.form.dayOffset.setValue(self.startDate.hour)

    def _setupDayCutoffV2(self):
        self.form.dayOffset.setValue(self.mw.col.conf.get("rollover", 4))

    def _updateDayCutoff(self):
        if self.mw.col.schedVer() == 2:
            self._updateDayCutoffV2()
        else:
            self._updateDayCutoffV1()

    def _updateDayCutoffV1(self):
        hrs = self.form.dayOffset.value()
        old = self.startDate
        date = datetime.datetime(
            old.year, old.month, old.day, hrs)
        self.mw.col.crt = int(time.mktime(date.timetuple()))

    def _updateDayCutoffV2(self):
        self.mw.col.conf['rollover'] = self.form.dayOffset.value()

    # Network
    ######################################################################

    def setupNetwork(self):
        self.form.syncOnProgramOpen.setChecked(
            self.prof['autoSync'])
        self.form.syncMedia.setChecked(
            self.prof['syncMedia'])
        if not self.prof['syncKey']:
            self._hideAuth()
        else:
            self.form.syncUser.setText(self.prof.get('syncUser', ""))
            self.form.syncDeauth.clicked.connect(self.onSyncDeauth)

    def _hideAuth(self):
        self.form.syncDeauth.setVisible(False)
        self.form.syncUser.setText("")
        self.form.syncLabel.setText(_("""\
<b>Synchronization</b><br>
Not currently enabled; click the sync button in the main window to enable."""))

    def onSyncDeauth(self):
        self.prof['syncKey'] = None
        self.mw.col.media.forceResync()
        self._hideAuth()

    def updateNetwork(self):
        self.prof['autoSync'] = self.form.syncOnProgramOpen.isChecked()
        self.prof['syncMedia'] = self.form.syncMedia.isChecked()
        if self.form.fullSync.isChecked():
            self.mw.col.modSchema(check=False)
            self.mw.col.setMod()

    # Backup
    ######################################################################

    def setupBackup(self):
        self.form.numBackups.setValue(self.prof['numBackups'])
        self.form.openBackupFolder.linkActivated.connect(self.onOpenBackup)

    def onOpenBackup(self):
        openFolder(self.mw.pm.backupFolder())

    def updateBackup(self):
        self.prof['numBackups'] = self.form.numBackups.value()

    # Basic & Advanced Options
    ######################################################################

    def setupOptions(self):
        self.form.pastePNG.setChecked(self.prof.get("pastePNG", False))
        self.form.ansKeysLEdit.setText(self.prof.get("ccbc.extraAnsKeys", "1234"))
        # self.form.ansKeyActNothing.setChecked() #default, not used
        self.form.ansKeyActFlip.setChecked(self.prof.get("ccbc.flipGrade", False))
        self.form.ansKeyActGrade.setChecked(self.prof.get("ccbc.forceGrade", False))
        self.form.cascadeGradeBtns.setChecked(self.prof.get("ccbc.revCascadeBtn", False))
        self.form.colorGradeBtns.setChecked(self.prof.get("ccbc.revColorBtn", False))
        self.form.bigGradeBtns.setChecked(self.prof.get("ccbc.revBigBtn", False))
        self.form.showFormatBtns.setChecked(self.prof.get("ccbc.showFormatBtns", True))
        self.form.autoCompleter.setChecked(self.prof.get("ccbc.autoCompleter", False))
        self.form.powerUserMode.setChecked(self.prof.get("ccbc.powerUserMode", False))

        ed=("notepad.exe","mspaint.exe") if isWin else ("","")
        self.form.extTxtCmdLEdit.setText(self.prof.get("ccbc.extTxtCmd",ed[0]))
        self.form.extImgCmdLEdit.setText(self.prof.get("ccbc.extImgCmd",ed[1]))

        self.form.showAudPlayBtn.setChecked(self.prof.get("ccbc.showAudPlayBtn", True))
        self.form.stpAudOnShwAns.setChecked(self.prof.get("ccbc.stpAudOnShwAns", True))
        self.form.noAutoPlay.setChecked(self.prof.get("ccbc.noAutoPlay", False))
        self.form.mpvDA.setChecked(self.prof.get("mpv.directAccess", True))
        self.form.noScript.setChecked(self.prof.get("tidyTags.noScript", True))
        self.form.importMedia.setChecked(self.prof.get("tidyTags.importMedia", True))

        self.form.skipBackupQE.setChecked(self.prof.get("ccbc.skipBackupOnQuickExit", False))
        self.form.skipBackupSP.setChecked(self.prof.get("ccbc.skipBackupOnSwitchProfile", False))
        self.form.exitWarning.setChecked(self.prof.get("ccbc.warnOnQuickExit", True))

        self.form.micChannel.setCurrentIndex(self.prof.get("PYAU_CHANNELS", 1)-1)
        idx = getMics(self.prof.get("PYAU_INPUT_DEVICE", ""))
        try:
            self.form.micDevice.setCurrentIndex(idx)
        except TypeError: pass

        if not isWin:
            self.form.mpvDA.setVisible(False)
        if self.mw.col.sched.type == "anki":
            self.form.skipFinalDrill.setVisible(False)
        else: #custom experimental module
            qc = self.mw.col.conf
            self.form.skipFinalDrill.setCheckState(qc.get("skipFinalDrill", 0))
            self.form.skipFinalDrill.clicked.connect(self.toggleFinalDrill)
            self.toggleFinalDrill()


    def updateOptions(self):
        keys = self.form.ansKeysLEdit.text()[:4]
        if not keys or keys=="1234":
            self.prof.pop('ccbc.extraAnsKeys', None)
        else:
            self.prof['ccbc.extraAnsKeys'] = keys

        if self.form.ansKeyActNothing.isChecked():
            self.prof['ccbc.flipGrade'] = False
            self.prof['ccbc.forceGrade'] = False
        else:
            self.prof['ccbc.flipGrade'] = self.form.ansKeyActFlip.isChecked()
            self.prof['ccbc.forceGrade'] = self.form.ansKeyActGrade.isChecked()

        self.prof['pastePNG'] = self.form.pastePNG.isChecked()
        self.prof['ccbc.revCascadeBtn'] = self.form.cascadeGradeBtns.isChecked()
        self.prof['ccbc.revColorBtn'] = self.form.colorGradeBtns.isChecked()
        self.prof['ccbc.revBigBtn'] = self.form.bigGradeBtns.isChecked()
        self.prof['ccbc.showFormatBtns'] = self.form.showFormatBtns.isChecked()
        self.prof['ccbc.autoCompleter'] = self.form.autoCompleter.isChecked()
        self.prof['ccbc.powerUserMode'] = self.form.powerUserMode.isChecked()

        self.prof['ccbc.extImgCmd'] = self.form.extImgCmdLEdit.text()
        self.prof['ccbc.extTxtCmd'] = self.form.extTxtCmdLEdit.text()

        self.prof['ccbc.showAudPlayBtn'] = self.form.showAudPlayBtn.isChecked()
        self.prof['ccbc.stpAudOnShwAns'] = self.form.stpAudOnShwAns.isChecked()
        self.prof['ccbc.noAutoPlay'] = self.form.noAutoPlay.isChecked()
        self.prof['mpv.directAccess'] = self.form.mpvDA.isChecked()
        self.prof['tidyTags.noScript'] = self.form.noScript.isChecked()
        self.prof['tidyTags.importMedia'] = self.form.importMedia.isChecked()

        self.prof['ccbc.skipBackupOnQuickExit'] = self.form.skipBackupQE.isChecked()
        self.prof['ccbc.skipBackupOnSwitchProfile'] = self.form.skipBackupSP.isChecked()
        self.prof['ccbc.warnOnQuickExit'] = self.form.exitWarning.isChecked()

        self.prof['PYAU_CHANNELS'] = self.form.micChannel.currentIndex()+1

        if self.form.micDevice.currentIndex():
            t = self.form.micDevice.currentText()
            idx,name = t.split(":",1)
            self.prof['PYAU_INPUT_DEVICE'] = name
            self.prof['PYAU_INPUT_INDEX'] = int(idx)
            _,rate = name.rsplit(" ",1)
            self.prof['PYAU_INPUT_RATE'] = int(rate)
        else:
            self.prof['PYAU_INPUT_DEVICE'] = ""
            self.prof['PYAU_INPUT_INDEX'] = None
            self.prof['PYAU_INPUT_RATE'] = 44100

        qc = self.mw.col.conf
        qc['skipFinalDrill'] = self.form.skipFinalDrill.checkState()

    def toggleFinalDrill(self):
        checked=self.form.skipFinalDrill.checkState()
        if checked==1: #CB_NO_NEW
            txt="Skip Final Drill: (don't skip new)"
        elif checked==2: #CB_ALL
            txt="Skip Final Drill: (skip all)"
        else:
            txt='Skip Final Drill: (disabled)'
        self.form.skipFinalDrill.setText(_(txt))

