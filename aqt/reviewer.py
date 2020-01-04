# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from __future__ import division
import difflib
import re
import cgi
import unicodedata as ucd
import html.parser

from anki.lang import _, ngettext
from aqt.qt import *
from anki.utils import  stripHTML, isMac, json
from anki.hooks import addHook, runHook, runFilter
from anki.sound import playFromText, clearAudioQueue, play
from aqt.utils import mungeQA, getBase, openLink, tooltip, askUserDialog, \
    downArrow
from aqt.sound import getAudio
import aqt
import ccbc
from anki.lang import _
from html.parser import HTMLParser


class Reviewer(object):
    "Manage reviews.  Maintains a separate state."

    def __init__(self, mw):
        self.mw = mw
        self.web = mw.web
        self.card = None
        self.cardQueue = []
        self.hadCardQueue = False
        self._answeredIds = []
        self._recordedAudio = None
        self.typeCorrect = None # web init happens before this is set
        self.state = None
        self.bottom = aqt.toolbar.BottomBar(mw, mw.bottomWeb)
        # qshortcut so we don't autorepeat
        self.delShortcut = QShortcut(QKeySequence("Delete"), self.mw)
        self.delShortcut.setAutoRepeat(False)
        self.mw.connect(self.delShortcut, SIGNAL("activated()"), self.onDelete)
        addHook("leech", self.onLeech)

    def show(self):
        self.mw.col.reset()
        self.mw.keyHandler = self._keyHandler
        self.web.setLinkHandler(self._linkHandler)
        # self.web.setKeyHandler(self._catchEsc)

        btn_height = 0
        css_btn_height = ""
        conf = self.mw.pm.profile.get
        if conf("ccbc.revBigBtn",False):
            btn_height = 40
            css_btn_height = "height: 64px;"
        if conf("ccbc.revColorBtn",False):
            css = ccbc.css.user_rev_bottombar_color%css_btn_height
        else:
            css = ccbc.css.user_rev_bottombar_plain%css_btn_height
        self._bottomCSS = ccbc.css.rev_bottombar + css

        if isMac:
            self.bottom.web.setFixedHeight(btn_height+46) #untested
        else:
            self.bottom.web.setFixedHeight(btn_height+50+self.mw.fontHeightDelta*4)

        self.bottom.web.setLinkHandler(self._linkHandler)
        self._reps = None
        self.card = None
        self.nextCard()

    def lastCard(self):
        if self._answeredIds:
            if not self.card or self._answeredIds[-1] != self.card.id:
                try:
                    return self.mw.col.getCard(self._answeredIds[-1])
                except TypeError:
                    # id was deleted
                    return

    def cleanup(self):
        runHook("reviewCleanup")

    # Fetching a card
    ##########################################################################

    def nextCard(self):
        elapsed = self.mw.col.timeboxReached()
        if elapsed:
            part1 = ngettext("%d card studied in", "%d cards studied in", elapsed[1]) % elapsed[1]
            mins = int(round(elapsed[0]/60))
            part2 = ngettext("%s minute.", "%s minutes.", mins) % mins
            fin = _("Finish")
            diag = askUserDialog("%s %s" % (part1, part2),
                             [_("Continue"), fin])
            diag.setIcon(QMessageBox.Information)
            if diag.run() == fin:
                return self.mw.moveToState("deckBrowser")
            self.mw.col.startTimebox()
        if self.cardQueue:
            # undone/edited cards to show
            c = self.cardQueue.pop()
            c.startTimer()
            self.hadCardQueue = True
        else:
            if self.hadCardQueue:
                # the undone/edited cards may be sitting in the regular queue;
                # need to reset
                self.mw.col.reset()
                self.hadCardQueue = False
            c = self.mw.col.sched.getCard()
            if c and self.card and self.card.id == c.id:
                # if previously dropped card
                self.card=None
                return self.nextCard()
        self.card = c
        clearAudioQueue()
        if not c:
            return self.mw.moveToState("overview")
        if self._reps is None or self._reps % 100 == 0:
            # we recycle the webview periodically so webkit can free memory
            self._initWeb()
        else:
            self._showQuestion()

    # Audio
    ##########################################################################

    def replayAudio(self, previewer=None):
        if previewer:
            state = previewer._previewState
            c = previewer.card
        else:
            state = self.state
            c = self.card
        clearAudioQueue()
        if state == "question":
            playFromText(c.q())
        elif state == "answer":
            txt = ""
            if self._replayq(c, previewer):
                txt = c.q()
            txt += c.a()
            playFromText(txt)

    # Initializing the webview
    ##########################################################################


    def revHtml(self):
        return self._revHtml

    _revHtml = """
<div id=_mark>&#x2605;</div>
<div id=_flag>
<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="1em" height="1em"
viewBox="0 0 827 827"
 xmlns:xlink="http://www.w3.org/1999/xlink">
 <defs>
  <style type="text/css">
   <![CDATA[.fil1 {fill:darkgray;}]]>
  </style>
 </defs>
   <g transform="matrix(0.983406 0 0 1 -50.6456 -2.00487)">
    <text x="413.5" y="413.5" id="_110500896" class="fil0 fnt0"> </text>
   </g>
   <g>
    <polygon id="_113080104" class="fil1" points="205.94,180.234 372.979,723.046 287.874,745.81 120.834,202.998 "/>
   </g>
   <g>
    <path class="fil1" d="M313.243 102.322l5.90478 82.9268 -0.17367 0 -2.1691 0.216201 -2.18564 0.276454 -2.20218 0.490293 -2.56488 0.53755 -2.75391 0.738393 -2.76809 0.771473 -2.95475 1.11999 -3.1426 1.30075 -3.32808 1.31139 -3.3399 1.63864 -3.5242 1.79813 -3.53365 1.7875 -3.71914 2.09349 -3.72741 2.23172 -3.91053 2.52589 -4.09129 2.48454 -3.92589 2.76572 -4.10665 2.7102 -4.11137 2.97602 -4.29213 3.07053 -4.122 3.15678 -4.3004 3.40133 -4.47761 3.31154 -4.30749 3.54192 -4.48234 3.59981 -4.31103 3.65298 -4.48588 3.69787 -4.66074 3.7345 -4.48588 3.76758 -4.48588 3.95306 -4.65719 3.9696 -4.65601 3.81601 -59.7472 -61.1389 4.65601 -4.14209 4.65719 -3.9696 4.83322 -3.95306 4.83322 -4.09129 4.66074 -4.06057 4.83322 -4.02395 5.00571 -3.97669 4.82968 -3.92589 5.00217 -3.86563 4.82495 -3.96369 4.99508 -3.72504 5.16402 -3.80893 4.98681 -3.72032 5.15339 -3.6258 5.14867 -3.68606 5.31525 -3.41551 5.13331 -3.4604 5.29989 -3.17568 5.46411 -3.20758 5.45584 -3.06935 5.62006 -3.08944 5.60824 -2.77399 5.77128 -2.6145 5.75946 -2.61096 5.92132 -2.27661 6.08081 -2.09585 6.24149 -2.07104 6.22731 -1.71425 6.38562 -1.51341 6.7176 -1.14244 6.70343 -0.92624 6.68452 -0.539913 -0.17367 0zm5.73111 82.9268l-5.55744 -82.9268 2.28252 -0.0803371 2.26007 0.0283543 2.23408 0.133501 2.20573 0.236286 2.17383 0.337889 2.13957 0.434766 2.10058 0.531643 2.06159 0.623794 2.01788 0.714764 1.97062 0.804553 1.92218 0.888434 1.86902 0.973497 1.81349 1.05383 1.7556 1.13299 1.69417 1.2086 1.63037 1.28303 1.56303 1.35392 1.49333 1.42244 1.42008 1.4886 1.34328 1.55358 1.26531 1.61501 1.18261 1.6729 1.09755 1.73079 1.01012 1.78514 0.919151 1.83594 0.825819 1.88556 0.72776 1.93282 0.629701 1.97653 0.525736 2.01906 0.420589 2.05805 0.311897 2.09585 0.200843 2.13012 0.0850629 2.1372 -0.0295357 2.11594 -0.142953 2.09113 -0.252826 2.06514 -0.360336 2.03442 -0.464301 2.00252 -0.567086 1.96708 -0.667507 1.93045 -0.763203 1.88792 -0.858899 1.84539 -0.949869 1.79932 -1.03966 1.7497 -1.1259 1.69889 -1.20978 1.64337 -1.2913 1.58548 -1.36928 1.52641 -1.44607 1.46379 -1.5205 1.39763 -1.5902 1.32911 -1.65873 1.25822 -1.72489 1.18379 -1.7875 1.107 -1.84894 1.02784 -1.90564 0.946324 -1.96117 0.86008 -2.01434 0.772654 -2.06396 0.682866 -2.11239 0.588351 -2.15611 0.492656 -2.19864 0.394597 -2.23881 0.291813 -2.27543 0.187847zm138.735 -13.0843l-7.64148 82.9268 0 0 -8.33025 -1.05502 -7.9262 -1.57366 -7.52806 -2.06396 -7.30477 -2.53062 -6.73769 -2.80944 -6.5203 -3.06344 -6.13516 -3.1296 -5.75001 -3.33281 -5.54326 -3.51239 -5.16402 -3.50412 -5.13685 -3.46986 -4.76588 -3.57382 -4.74344 -3.4923 -4.37837 -3.38243 -4.36302 -3.41197 -4.17753 -3.25365 -3.99323 -3.07053 -3.9885 -3.02564 -3.63762 -2.62868 -3.46513 -2.69484 -3.46749 -2.25062 -3.12606 -2.10531 -2.96184 -1.77214 -2.6275 -1.57603 -2.29315 -1.19324 -2.13957 -0.948687 -1.641 -0.67814 -1.31729 -0.382783 -0.824637 -0.225653 -0.506833 -0.0425314 -0.193754 -0.160674 -0.23156 0.0720671 -5.90478 -82.9268 8.56772 -0.0720671 8.52991 0.484386 8.15068 1.34447 7.77144 1.8513 7.22207 2.3345 6.8511 2.6275 6.30765 2.90041 6.11626 3.14496 5.75356 3.20167 5.39322 3.39779 5.2101 3.40724 4.85685 3.55019 4.85449 3.34699 4.67964 3.60454 4.33584 3.34935 4.34057 3.39661 4.17753 3.25365 4.01568 3.08589 4.03103 3.05872 3.70142 2.84015 3.72386 2.59796 3.40015 2.49636 3.42732 2.20218 3.11188 1.88674 2.97129 1.70716 2.6594 1.50396 2.35222 1.11172 2.22227 0.857717 1.74733 0.5789 1.62328 0.43831 1.32674 0.271729 1.03375 0.0815186 0 0zm-7.64148 82.9268l7.64148 -82.9268 2.27425 0.237467 2.23408 0.342614 2.19273 0.441854 2.14666 0.541094 2.10058 0.63679 2.04978 0.72776 1.9978 0.81873 1.94345 0.904974 1.88556 0.988856 1.82531 1.06919 1.76269 1.14835 1.69771 1.22396 1.62919 1.29603 1.55949 1.36573 1.48742 1.43307 1.41181 1.49805 1.33383 1.5583 1.2535 1.61738 1.16961 1.67172 1.08573 1.72607 0.997126 1.77451 0.906156 1.82294 0.812823 1.86666 0.718309 1.90801 0.619069 1.94699 0.518647 1.98362 0.415863 2.01552 0.309534 2.04623 0.202024 2.07341 0.0897886 2.09704 -0.0224471 2.11948 -0.139409 2.13839 -0.254007 2.12893 -0.365061 2.09231 -0.472571 2.05214 -0.577719 2.00961 -0.679321 1.9659 -0.778561 1.91982 -0.874257 1.8702 -0.966409 1.8194 -1.0562 1.76387 -1.14244 1.70953 -1.22632 1.65046 -1.30666 1.58902 -1.38463 1.52522 -1.46025 1.46025 -1.52995 1.3929 -1.59965 1.32084 -1.66463 1.24877 -1.72725 1.17316 -1.78632 1.09637 -1.84303 1.01603 -1.89619 0.933329 -1.94699 0.848266 -1.99425 0.762021 -2.03796 0.671051 -2.07931 0.580081 -2.1183 0.485567 -2.15256 0.389871 -2.18564 0.28945 -2.21518 0.189029 -2.23999 0.0838814 -2.2648 -0.0212657 -2.2837 -0.129957zm175.878 -126.04l-13.8936 81.9533 5.24082 0.362699 2.56134 0.00827 0.251644 -0.0437129 -0.822274 0.211476 -2.04623 0.44658 -2.72792 0.824637 -3.38597 1.01957 -4.02276 1.35628 -4.28977 1.51223 -4.70799 1.64809 -5.10495 1.92691 -5.30461 2.02261 -5.65668 1.93518 -5.98748 2.31796 -5.94613 2.19037 -6.23204 2.20691 -6.49549 2.3664 -6.56284 2.34395 -6.60773 2.13839 -6.80385 2.23763 -6.80503 2.31796 -6.95625 2.05214 -6.91372 1.93045 -7.19372 1.95054 -7.10629 1.62565 -7.17009 1.60674 -7.21026 1.24286 -7.40401 1.18261 -7.40047 0.779743 -7.54815 0.517466 -7.67456 0.07443 -7.95101 -0.226834 7.64148 -82.9268 1.69889 0.226834 2.46446 -0.07443 3.03273 -0.193754 3.57973 -0.453669 3.92825 -0.532824 4.43154 -0.916789 4.73871 -0.956957 5.02225 -1.29957 5.10968 -1.30075 5.52436 -1.60438 5.56689 -1.72843 5.76301 -1.66818 5.76183 -1.91155 5.91305 -2.13839 5.86816 -2.01788 5.80081 -2.04269 5.8847 -2.20691 5.94613 -2.19037 5.64014 -1.99189 5.65668 -2.26125 5.65195 -2.02261 5.45229 -1.92691 5.40267 -1.9718 5.33179 -1.8383 5.06478 -1.68235 5.12267 -1.66936 5.1593 -1.47442 5.17229 -1.42244 5.68503 -1.18734 6.00284 -0.932147 7.51152 -0.331981 9.34746 0.610799z"/>
   </g>
   <g>
    <path class="fil1" d="M389.275 332.735l5.90478 82.9268 0 0 -2.15611 0.229197 -2.17265 0.287087 -2.3664 0.337889 -2.55661 0.707676 -2.57197 0.745481 -2.93585 0.776199 -2.95003 1.12472 -3.13787 1.30312 -3.32454 1.31375 -3.33754 1.641 -3.52184 1.79813 -3.53365 1.78514 -3.71796 2.09349 -3.90108 2.39239 -3.73568 2.35931 -4.09247 2.48218 -3.92471 2.76218 -4.10665 2.70665 -4.11137 2.97129 -4.29095 3.06581 -4.122 3.15205 -4.29804 3.39779 -4.47643 3.30682 -4.30394 3.5372 -4.47998 3.59627 -4.30631 3.64943 -4.47998 3.69315 -4.47998 3.73213 -4.65247 3.76403 -4.47525 3.95188 -4.64774 3.8042 -4.64301 3.97905 -59.7472 -61.1389 4.64301 -3.97905 4.64774 -4.13027 4.82259 -3.95188 4.65247 -4.08774 4.82732 -4.05821 4.82732 -4.01922 5.00099 -3.97314 4.82732 -3.92234 4.99862 -3.86091 4.82377 -3.95897 4.99272 -3.7215 5.16402 -3.8042 4.98563 -3.71559 5.15339 -3.62108 5.14867 -3.68251 5.31407 -3.41197 5.13449 -3.45804 5.47238 -3.33517 5.29044 -3.04218 5.45466 -3.06935 5.62006 -3.08707 5.60588 -2.77399 5.76892 -2.61686 5.75592 -2.61332 5.91659 -2.27898 6.07609 -2.10058 6.06191 -2.07577 6.39271 -1.72134 6.37735 -1.35982 6.53448 -1.31375 6.69043 -0.936873 6.67153 -0.552909 0 0zm5.90478 82.9268l-5.90478 -82.9268 2.28252 -0.0886071 2.26125 0.0200843 2.23526 0.125231 2.20691 0.229197 2.17619 0.328437 2.14075 0.427677 2.10412 0.523373 2.06396 0.616706 2.02142 0.708857 1.97535 0.796283 1.92573 0.882527 1.87375 0.966409 1.81822 1.04793 1.76151 1.1259 1.69889 1.20269 1.63628 1.27712 1.56894 1.34919 1.49923 1.41771 1.42598 1.48387 1.35037 1.54885 1.2724 1.61029 1.1897 1.66936 1.10582 1.72725 1.01721 1.78041 0.927421 1.83358 0.834089 1.8832 0.73603 1.93045 0.637971 1.97535 0.535187 2.0167 0.428859 2.05805 0.321349 2.09467 0.209113 2.13012 0.0945143 2.1372 -0.0212657 2.11594 -0.133501 2.09349 -0.244556 2.06514 -0.352066 2.03678 -0.456031 2.00488 -0.559997 1.97062 -0.658056 1.93164 -0.756114 1.89265 -0.85181 1.84894 -0.94278 1.80286 -1.03139 1.75442 -1.11881 1.70244 -1.20388 1.64809 -1.28539 1.59138 -1.36337 1.53231 -1.44016 1.46852 -1.51459 1.40354 -1.58548 1.33501 -1.654 1.26531 -1.72016 1.19088 -1.78396 1.11409 -1.84421 1.03493 -1.9021 0.952231 -1.95881 0.86835 -2.01197 0.779743 -2.06159 0.689954 -2.11003 0.596621 -2.15493 0.500926 -2.19746 0.402867 -2.23763 0.300083 -2.27543 0.196117zm138.56 -12.9355l-7.64148 82.9268 0 0 -8.33025 -1.0562 -7.92502 -1.57484 -7.70055 -2.06632 -7.1311 -2.53298 -6.73651 -2.81298 -6.52149 -3.06699 -6.13398 -3.13433 -5.75001 -3.33754 -5.54208 -3.51829 -5.16402 -3.51002 -5.13685 -3.47576 -4.76588 -3.58091 -4.74344 -3.49821 -4.37837 -3.38834 -4.36302 -3.41905 -4.17635 -3.26074 -3.99441 -3.07644 -3.9885 -3.03155 -3.63762 -2.79762 -3.6388 -2.54007 -3.29382 -2.25653 -3.12606 -2.11121 -2.96184 -1.93991 -2.6275 -1.42008 -2.29433 -1.19797 -2.14075 -0.952231 -1.63982 -0.682866 -1.31847 -0.386327 -0.824637 -0.229197 -0.506833 -0.0437129 -0.368606 -0.163037 -0.05789 0.0708857 -5.90478 -82.9268 8.74139 -0.0708857 8.35743 0.486749 8.15068 1.34565 7.77144 1.85484 7.22325 2.33805 6.84992 2.63222 6.30883 2.90395 6.11744 3.14969 5.75356 3.3718 5.39322 3.23948 5.2101 3.41315 5.03052 3.5561 4.68082 3.51593 4.67964 3.44977 4.33584 3.35526 4.34175 3.40251 4.17635 3.26074 4.01568 3.09298 4.03103 3.06463 3.70142 2.84606 3.72386 2.60505 3.40015 2.50227 3.42732 2.20809 3.1107 1.89265 2.97129 1.71189 2.65821 1.50868 2.35341 1.11527 2.22109 0.861261 1.921 0.581263 1.44843 0.440673 1.32556 0.27291 1.03375 0.0827 0 0zm-7.64148 82.9268l7.64148 -82.9268 2.27425 0.237467 2.23408 0.342614 2.19273 0.441854 2.14666 0.541094 2.10058 0.63679 2.04978 0.72776 1.9978 0.81873 1.94345 0.904974 1.88556 0.988856 1.82531 1.06919 1.76269 1.14835 1.69771 1.22396 1.62919 1.29603 1.55949 1.36573 1.48742 1.43307 1.41181 1.49805 1.33383 1.5583 1.2535 1.61738 1.16961 1.67172 1.08573 1.72607 0.997126 1.77451 0.906156 1.82294 0.812823 1.86666 0.718309 1.90801 0.619069 1.94699 0.518647 1.98362 0.415863 2.01552 0.309534 2.04623 0.202024 2.07341 0.0897886 2.09704 -0.0224471 2.11948 -0.139409 2.13839 -0.254007 2.12893 -0.365061 2.09231 -0.472571 2.05214 -0.577719 2.00961 -0.679321 1.9659 -0.778561 1.91982 -0.874257 1.8702 -0.966409 1.8194 -1.0562 1.76387 -1.14244 1.70953 -1.22632 1.65046 -1.30666 1.58902 -1.38463 1.52522 -1.46025 1.46025 -1.52995 1.3929 -1.59965 1.32084 -1.66463 1.24877 -1.72725 1.17316 -1.78632 1.09637 -1.84303 1.01603 -1.89619 0.933329 -1.94699 0.848266 -1.99425 0.762021 -2.03796 0.671051 -2.07931 0.580081 -2.1183 0.485567 -2.15256 0.389871 -2.18564 0.28945 -2.21518 0.189029 -2.23999 0.0838814 -2.2648 -0.0212657 -2.2837 -0.129957zm175.878 -126.182l-13.8936 81.9533 5.242 0.362699 2.56134 0.00945143 0.426496 -0.04135 -0.995944 0.213839 -2.04623 0.450124 -2.72674 0.828181 -3.38597 1.02312 -4.02158 1.36101 -4.28977 1.51695 -4.70799 1.654 -5.10495 1.93282 -5.30461 1.86548 -5.65668 2.10412 -5.81263 2.32387 -6.12098 2.19746 -6.23204 2.214 -6.49549 2.37231 -6.38917 2.35104 -6.7814 2.14429 -6.80385 2.24471 -6.80503 2.16083 -6.95625 2.2199 -6.91372 1.93636 -7.1949 1.95645 -7.10629 1.63037 -7.17009 1.61147 -7.21144 1.24641 -7.40401 1.18734 -7.40047 0.782106 -7.54933 0.519829 -7.67456 0.0756114 -7.9522 -0.225653 7.64148 -82.9268 1.70008 0.225653 2.46446 -0.0756114 3.03391 -0.196117 3.57973 -0.456031 3.92825 -0.53755 4.43272 -0.920333 4.73871 -0.961683 5.02225 -1.3043 5.11086 -1.30666 5.52436 -1.61029 5.56689 -1.57012 5.76301 -1.83712 5.76183 -1.91864 5.73938 -2.14429 6.04183 -2.02497 5.80081 -2.0486 5.8847 -2.214 5.77364 -2.19746 5.81263 -1.9978 5.65668 -2.10412 5.65195 -2.19155 5.45229 -1.93282 5.40267 -1.97771 5.33179 -1.84303 5.0636 -1.68708 5.12267 -1.6729 5.15812 -1.47797 5.17229 -1.42598 5.51136 -1.1897 6.17533 -0.93451 7.51152 -0.333163 9.34628 0.610799z"/>
   </g>
   <g>
    <polygon class="fil1" points="627.909,134.594 724.688,435.566 639.583,459.305 542.804,158.334 "/>
   </g>
   <polygon class="fil2" points="174.354,223.65 245.495,452.228 390.746,378.861 482.641,424.008 592.321,429.655 666.425,395.793 595.283,178.497 503.389,198.25 461.894,206.719 334.428,155.918 254.388,170.029 "/>
</svg></div>
<div id=qa></div>
<script>
var ankiPlatform = "desktop";
var typeans;
function _updateQA (q, answerMode, klass) {
    $("#qa").html(q);
    typeans = document.getElementById("typeans");
    if (typeans) {
        typeans.focus();
    }
    if (answerMode) {
        var e = $("#answer");
        if (e[0]) { e[0].scrollIntoView(); }
        $(document.body).removeClass("frontSide").addClass("backSide");
    } else {
        window.scrollTo(0, 0);
    }
    if (klass) {
        document.body.className = klass;
    }
    // don't allow drags of images, which cause them to be deleted
    $("img").attr("draggable", false);
};


_flagColours = {
    1: "#ff6666",
    2: "#ff9900",
    3: "#77ff77",
    4: "#77aaff"
};

function _drawFlag(flag) {
    var elem = $("#_flag");
    if (flag === 0) {
        elem.hide();
        return;
    }
    elem.show();
    //elem.css("color", _flagColours[flag]);
    elem.css("fill", _flagColours[flag]);
}

function _toggleStar (mark) {
    var elem = $("#_mark");
    if (!mark) {
        elem.hide();
    } else {
        elem.show();
    }
}

function _getTypedText () {
    if (typeans) {
        py.link("typeans:"+typeans.value);
    }
};
function _typeAnsPress() {
    if (window.event.keyCode === 13) {
        py.link("ansHack");
    }
}
</script>
"""

    def _initWeb(self):
        self._reps = 0
        self._bottomReady = False
        base = getBase(self.mw.col)
        # main window
        self.web.stdHtml(self.revHtml(), self._styles(),
            loadCB=lambda x: self._showQuestion(),
            head=base)
        # show answer / ease buttons
        self.bottom.web.show()
        self.bottom.web.stdHtml(
            self._bottomHTML(),
            self.bottom._css + self._bottomCSS,
        loadCB=lambda x: self._showAnswerButton())

    # Showing the question
    ##########################################################################

    def _mungeQA(self, buf):
        return self.typeAnsFilter(mungeQA(self.mw.col, buf))

    def _showQuestion(self):
        self._reps += 1
        self.state = "question"
        self.typedAnswer = None
        c = self.card
        # grab the question and play audio
        if c.isEmpty():
            q = _("""\
The front of this card is empty. Please run Tools>Empty Cards.""")
        else:
            q = c.q()
        if self.autoplay(c):
            playFromText(q)
        # render & update bottom
        q = self._mungeQA(q)
        q = runFilter("prepareQA", q, c, "reviewQuestion")
        klass = "card card%d frontSide" % (c.ord+1)
        self.web.eval("_updateQA(%s, false, '%s');" % (json.dumps(q), klass))
        self._toggleFlag()
        self._toggleStar()
        if self._bottomReady:
            self._showAnswerButton()
        self.mw.web.setFocus()
        # user hook
        runHook('showQuestion')

    def autoplay(self, card):
        if self.mw.pm.profile.get("ccbc.noAutoPlay", False):
            return False
        return self.mw.col.decks.confForDid(
            card.odid or card.did)['autoplay']

    def ignoreInputCase(self, card):
        try:
            return self.mw.col.decks.confForDid(
                card.odid or card.did).get(
                    "ccbc.ignoreInputCase", False)
        except:
            #err from clayout preview before adding card.
            return False

    def _replayq(self, card, previewer=None):
        s = previewer if previewer else self
        return s.mw.col.decks.confForDid(
            s.card.odid or s.card.did).get('replayq', True)


    def _toggleFlag(self):
        self.web.eval("_drawFlag(%s);" % self.card.userFlag())

    #renamed to _drawMark in 2.1
    def _toggleStar(self):
        self.web.eval("_toggleStar(%s);" % json.dumps(
            self.card.note().hasTag("marked")))

    # Showing the answer
    ##########################################################################

    def _showAnswer(self):
        if self.mw.state != "review":
            # showing resetRequired screen; ignore space
            return
        #save ir view on Q side, requires state=Q
        self.mw.viewmanager.flush()

        self.state = "answer"
        c = self.card
        a = c.a()
        # stop audio? No for 2.0, Yes for 2.1
        if self.mw.pm.profile.get("ccbc.stpAudOnShwAns", True):
            clearAudioQueue()
        # play audio?
        if self.autoplay(c):
            playFromText(a)
        # render and update bottom
        a = self._mungeQA(a)
        a = runFilter("prepareQA", a, c, "reviewAnswer")

        self.web.eval("_updateQA(%s, true);" % json.dumps(a))
        self._showEaseButtons()
        self.mw.web.setFocus()
        # user hook
        runHook('showAnswer')

    # Answering a card
    ############################################################

    def _answerCard(self, ease):
        "Reschedule card and show next."
        if self.mw.state != "review":
            # showing resetRequired screen; ignore key
            return
        forceGrade = self.mw.pm.profile.get("ccbc.forceGrade",False)
        if self.state != "answer" and not forceGrade:
            return
        if self.mw.col.sched.answerButtons(self.card) < ease:
            return
        self.mw.col.sched.answerCard(self.card, ease)
        self._answeredIds.append(self.card.id)
        self.mw.autosave()
        self.nextCard()

    # Handlers
    ############################################################

    def _catchEsc(self, evt):
        if self.mw.state!="review":
            return False
        if evt.key() == Qt.Key_Escape:
            self.web.eval("$('#typeans').blur();")
            return True

    def _showAnswerHack(self):
        # on <qt4.8, calling _showAnswer() directly fails to show images on
        # the answer side. But if we trigger it via the bottom web's python
        # link, it inexplicably works.
        self.bottom.web.eval("py.link('ans');")

    def _keyHandler(self, evt):
        conf = self.mw.pm.profile.get
        ExAnsKeys = conf("ccbc.extraAnsKeys", None)
        key = evt.text()
        if key == "e":
            self.mw.onEditCurrent()
        elif (key == " " or evt.key() in (Qt.Key_Return, Qt.Key_Enter)):
            if self.state == "question":
                if evt.modifiers()==Qt.ControlModifier:
                    self.nextCard() #drop card
                else:
                    self._showAnswerHack()
            elif self.state == "answer":
                self._answerCard(self._defaultEase())
        elif key in ("1", "2", "3", "4"):
            if evt.modifiers()==Qt.ControlModifier:
                self.setFlag(int(key))
            elif self.state == "question" and \
            conf("ccbc.flipGrade", False):
                self._showAnswerHack()
            else:
                self._answerCard(int(key))
        elif ExAnsKeys and key in ExAnsKeys:
            if self.state == "question" and \
            conf("ccbc.flipGrade", False):
                self._showAnswerHack()
            else:
                k = ExAnsKeys.index(key,0,4)
                self._answerCard(k+1)
        elif key == "r" or evt.key() == Qt.Key_F5:
            self.replayAudio()
        elif key == "*":
            self.onMark()
        elif key == "=":
            self.onBuryNote()
        elif key == "-":
            self.onBuryCard()
        elif key == "!":
            self.onSuspend()
        elif key == "@":
            self.onSuspendCard()
        elif key == "V":
            self.onRecordVoice()
        elif key == "o":
            self.onOptions()
        elif key == "v":
            self.onReplayRecorded()

    def _linkHandler(self, url):
        if url == "ans":
            self._showAnswer()
        elif url == "nxt":
            self.nextCard()
        elif url == "ansHack":
            self.mw.progress.timer(100, self._showAnswerHack, False)
        elif url.startswith("ease"):
            self._answerCard(int(url[4:]))
        elif url == "edit":
            self.mw.onEditCurrent()
        elif url == "more":
            self.showContextMenu()
        elif url.startswith("typeans:"):
            (cmd, arg) = url.split(":", 1)
            self.typedAnswer = arg
        elif url.startswith("ankiplay:"):
            (cmd, arg) = url.split(":", 1)
            clearAudioQueue()
            play(arg)
        else:
            openLink(url)

    # CSS
    ##########################################################################

    _css = ccbc.css.reviewer

    def _styles(self):
        return self._css

    # Type in the answer
    ##########################################################################

    typeAnsPat = "\[\[type:(.+?)\]\]"

    def typeAnsFilter(self, buf):
        if self.state == "question":
            return self.typeAnsQuestionFilter(buf)
        else:
            return self.typeAnsAnswerFilter(buf)

    def typeAnsQuestionFilter(self, buf):
        self.typeCorrect = None
        clozeIdx = None
        m = re.search(self.typeAnsPat, buf)
        if not m:
            return buf
        fld = m.group(1)
        # if it's a cloze, extract data
        if fld.startswith("cloze:"):
            # get field and cloze position
            clozeIdx = self.card.ord + 1
            fld = fld.split(":")[1]
        # loop through fields for a match
        for f in self.card.model()['flds']:
            if f['name'] == fld:
                self.typeCorrect = self.card.note()[f['name']]
                if clozeIdx:
                    # narrow to cloze
                    self.typeCorrect = self._contentForCloze(
                        self.typeCorrect, clozeIdx)
                self.typeFont = f['font']
                self.typeSize = f['size']
                break
        if not self.typeCorrect:
            if self.typeCorrect is None:
                if clozeIdx:
                    warn = _("Please run Tools>Empty Cards")
                else:
                    warn = _("Type answer: unknown field %s") % fld
                return re.sub(self.typeAnsPat, warn, buf)
            else:
                # empty field, remove type answer pattern
                return re.sub(self.typeAnsPat, "", buf)
        return re.sub(self.typeAnsPat, """
<center>
<input type=text id=typeans onkeypress="_typeAnsPress();"
   style="font-family: '%s'; font-size: %spx;">
</center>
""" % (self.typeFont, self.typeSize), buf)

    def typeAnsAnswerFilter(self, buf):
        # tell webview to call us back with the input content
        self.web.eval("_getTypedText();")
        if not self.typeCorrect:
            return re.sub(self.typeAnsPat, "", buf)
        origSize = len(buf)
        buf = buf.replace("<hr id=answer>", "")
        hadHR = len(buf) != origSize
        # munge correct value
        parser = HTMLParser()
        cor = stripHTML(self.mw.col.media.strip(self.typeCorrect))
        # ensure we don't chomp multiple whitespace
        cor = cor.replace(" ", "&nbsp;")
        cor = parser.unescape(cor)
        cor = cor.replace(u"\xa0", " ")
        given = self.typedAnswer
        # compare with typed answer
        res = self.correct(given, cor, showBad=False)
        # and update the type answer area
        def repl(match):
            # can't pass a string in directly, and can't use re.escape as it
            # escapes too much
            s = """
<span style="font-family: '%s'; font-size: %spx">%s</span>""" % (
                self.typeFont, self.typeSize, res)
            if hadHR:
                # a hack to ensure the q/a separator falls before the answer
                # comparison when user is using {{FrontSide}}
                s = "<hr id=answer>" + s
            return s
        return re.sub(self.typeAnsPat, repl, buf)

    def _contentForCloze(self, txt, idx):
        matches = re.findall("\{\{c%s::(.+?)\}\}"%idx, txt)
        if not matches:
            return None
        def noHint(txt):
            if "::" in txt:
                return txt.split("::")[0]
            return txt
        matches = [noHint(txt) for txt in matches]
        uniqMatches = set(matches)
        if len(uniqMatches) == 1:
            txt = matches[0]
        else:
            txt = ", ".join(matches)
        return txt

    def tokenizeComparison(self, given, correct):
        # compare in NFC form so accents appear correct
        given = ucd.normalize("NFC", given)
        correct = ucd.normalize("NFC", correct)
        if self.ignoreInputCase(self.card):
            s = difflib.SequenceMatcher(
                    None,
                    given.lower(),
                    correct.lower(),
                    autojunk=False
                )
        else:
            s = difflib.SequenceMatcher(None, given, correct, autojunk=False)
        givenElems = []
        correctElems = []
        givenPoint = 0
        correctPoint = 0
        offby = 0
        def logBad(old, new, str, array):
            if old != new:
                array.append((False, str[old:new]))
        def logGood(start, cnt, str, array):
            if cnt:
                array.append((True, str[start:start+cnt]))
        for x, y, cnt in s.get_matching_blocks():
            # if anything was missed in correct, pad given
            if cnt and y-offby > x:
                givenElems.append((False, "-"*(y-x-offby)))
                offby = y-x
            # log any proceeding bad elems
            logBad(givenPoint, x, given, givenElems)
            logBad(correctPoint, y, correct, correctElems)
            givenPoint = x+cnt
            correctPoint = y+cnt
            # log the match
            logGood(x, cnt, given, givenElems)
            logGood(y, cnt, correct, correctElems)
        return givenElems, correctElems

    def correct(self, given, correct, showBad=True):
        "Diff-corrects the typed-in answer."
        def good(s):
            return "<span class=typeGood>"+cgi.escape(s)+"</span>"
        def bad(s):
            return "<span class=typeBad>"+cgi.escape(s)+"</span>"
        def missed(s):
            return "<span class=typeMissed>"+cgi.escape(s)+"</span>"

        if given == correct:
            res = good(given)
        elif self.ignoreInputCase(self.card) \
        and given.lower() == correct.lower():
            res = good(given)
        else:
            res = ""
            givenElems, correctElems = self.tokenizeComparison(given, correct)
            for ok, txt in givenElems:
                if ok:
                    res += good(txt)
                else:
                    res += bad(txt)
            res += "<br>&darr;<br>"
            for ok, txt in correctElems:
                if ok:
                    res += good(txt)
                else:
                    res += missed(txt)
        res = "<div><code id=typeans>" + res + "</code></div>"
        return res

    # Bottom bar
    ##########################################################################

    _bottomCSS = "" #init in show()

    def _bottomHTML(self):
        return ccbc.html.rev_bottombar % dict(
            rem=self._remaining(), edit=_("Edit"),
            editkey=_("Shortcut key: %s") % "E",
            more=_("More"),
            downArrow=downArrow(),
            time=self.card.timeTaken() // 1000
            )

    def _showAnswerButton(self):
        self._bottomReady = True
        if not self.typeCorrect:
            self.bottom.web.setFocus()
        middle = '''
<span class=stattxt>%s</span><br>
<button title="%s" id=ansbut onclick='py.link(\"ans\");'>%s</button>
<button title="%s" id=nxtbut onclick='py.link(\"nxt\");'>%s</button>
''' % (
            self._remaining(),
            _("Shortcut key: %s") % _("Space"), _("Show Answer"),
            _("Shuffle This Card, Shortcut key: %s") % _("Ctrl+Return"), _("»")
        )
        # wrap it in a table so it has the same top margin as the ease buttons
        middle = "<table cellpadding=0><tr><td class=stat2 align=center>%s</td></tr></table>" % middle
        if self.card.shouldShowTimer():
            maxTime = self.card.timeLimit() / 1000
        else:
            maxTime = 0
        self.bottom.web.eval("showQuestion(%s,%d);" % (
            json.dumps(middle), maxTime))

    def _showEaseButtons(self):
        self.bottom.web.setFocus()
        middle = self._answerButtons()
        self.bottom.web.eval("showAnswer(%s);" % json.dumps(middle))

    def _remaining(self):
        if not self.mw.col.conf['dueCounts']:
            return ""
        if self.hadCardQueue:
            # if it's come from the undo queue, don't count it separately
            counts = list(self.mw.col.sched.counts())
        else:
            counts = list(self.mw.col.sched.counts(self.card))
        idx = self.mw.col.sched.countIdx(self.card)
        counts[idx] = "<u>%s</u>" % (counts[idx])
        space = " + "
        ctxt = '<font color="#000099">%s</font>' % counts[0]
        ctxt += space + '<font color="#C35617">%s</font>' % counts[1]
        ctxt += space + '<font color="#007700">%s</font>' % counts[2]
        return ctxt

    def _defaultEase(self):
        # return 3
        if self.mw.col.sched.answerButtons(self.card) == 4:
            return 3
        else:
            return 2

    def _answerButtonList(self):
        # return ((1, _("Again")), (2, _("Hard")), (3, _("Good")), (4, _("Easy")))
        l = ((1, _("Again")),)
        cnt = self.mw.col.sched.answerButtons(self.card)
        if cnt == 2:
            return l + ((2, _("Good")),)
        elif cnt == 3:
            return l + ((2, _("Good")), (3, _("Easy")))
        else:
            return l + ((2, _("Hard")), (3, _("Good")), (4, _("Easy")))

    def _answerButtons(self):
        times = []
        default = self._defaultEase()
        def but(i, label):
            if i == default:
                extra = "id=defease"
            else:
                extra = ""
            due = self._buttonTime(i)
            return '''
<td align=center>%s<button %s title="%s" onclick='py.link("ease%d");'>\
%s</button></td>''' % (due, extra, _("Shortcut key: %s") % i, i, label)
        buf = "<center><table cellpading=0 cellspacing=0><tr>"
        for ease, label in self._answerButtonList():
            buf += but(ease, label)
        buf += "</tr></table>"
        script = """
<script>$(function () { $("#defease").focus(); });</script>"""
        return buf + script

    def _buttonTime(self, i):
        if not self.mw.col.conf['estTimes']:
            return "<div class=spacer></div>"
        txt = self.mw.col.sched.nextIvlStr(self.card, i, True) or "&nbsp;"
        return '<span class=nobold>%s</span><br>' % txt

    # Leeches
    ##########################################################################

    def onLeech(self, card):
        # for now
        s = _("Card was a leech.")
        if card.queue < 0:
            s += " " + _("It has been suspended.")
        tooltip(s)

    # Context menu
    ##########################################################################

    # note the shortcuts listed here also need to be defined above
    def _contextMenu(self):
        currentFlag = self.card and self.card.userFlag()
        opts = [
            [_("Flag Card"), [
                [_("Red Flag"), "Ctrl+1", lambda: self.setFlag(1),
                 dict(checked=currentFlag == 1)],
                [_("Orange Flag"), "Ctrl+2", lambda: self.setFlag(2),
                 dict(checked=currentFlag == 2)],
                [_("Green Flag"), "Ctrl+3", lambda: self.setFlag(3),
                 dict(checked=currentFlag == 3)],
                [_("Blue Flag"), "Ctrl+4", lambda: self.setFlag(4),
                 dict(checked=currentFlag == 4)],
            ]],
            [_("Mark Note"), "*", self.onMark],
            [_("Bury Card"), "-", self.onBuryCard],
            [_("Bury Note"), "=", self.onBuryNote],
            [_("Suspend Card"), "@", self.onSuspendCard],
            [_("Suspend Note"), "!", self.onSuspend],
            [_("Delete Note"), "Delete", self.onDelete],
            [_("Options"), "O", self.onOptions],
            None,
            [_("Replay Audio"), "R", self.replayAudio],
            [_("Record Own Voice"), "Shift+V", self.onRecordVoice],
            [_("Replay Own Voice"), "V", self.onReplayRecorded],
        ]
        return opts

    def showContextMenu(self):
        opts = self._contextMenu()
        m = QMenu(self.mw)
        self._addMenuItems(m, opts)

        runHook("Reviewer.contextMenuEvent", self, m)
        m.exec_(QCursor.pos())

    def _addMenuItems(self, m, rows):
        for row in rows:
            if not row:
                m.addSeparator()
                continue
            if len(row) == 2:
                subm = m.addMenu(row[0])
                self._addMenuItems(subm, row[1])
                continue
            if len(row) == 4:
                label, scut, func, opts = row
            else:
                label, scut, func = row
                opts = {}
            a = m.addAction(label)
            if scut:
                a.setShortcut(QKeySequence(scut))
            if opts.get("checked"):
                a.setCheckable(True)
                a.setChecked(True)
            a.triggered.connect(func)

    def onOptions(self):
        self.mw.onDeckConf(self.mw.col.decks.get(
            self.card.odid or self.card.did))

    def setFlag(self, flag):
        # need to toggle off?
        if self.card.userFlag() == flag:
            flag = 0
        self.card.setUserFlag(flag)
        self.card.flush()
        self._toggleFlag()

    def onMark(self):
        f = self.card.note()
        if f.hasTag("marked"):
            f.delTag("marked")
        else:
            f.addTag("marked")
        f.flush()
        self._toggleStar()

    def onSuspend(self):
        self.mw.checkpoint(_("Suspend"))
        self.mw.col.sched.suspendCards(
            [c.id for c in self.card.note().cards()])
        tooltip(_("Note suspended."))
        self.mw.reset(guiOnly=True)

    def onSuspendCard(self):
        self.mw.checkpoint(_("Suspend"))
        self.mw.col.sched.suspendCards([self.card.id])
        tooltip(_("Card suspended."))
        self.mw.reset(guiOnly=True)

    def onDelete(self):
        # need to check state because the shortcut is global to the main
        # window
        if self.mw.state != "review" or not self.card:
            return
        self.mw.checkpoint(_("Delete"))
        cnt = len(self.card.note().cards())
        self.mw.col.remNotes([self.card.note().id])
        self.mw.reset(guiOnly=True)
        tooltip(ngettext(
            "Note and its %d card deleted.",
            "Note and its %d cards deleted.",
            cnt) % cnt)

    def onBuryCard(self):
        self.mw.checkpoint(_("Bury"))
        self.mw.col.sched.buryCards([self.card.id])
        self.mw.reset(guiOnly=True)
        tooltip(_("Card buried."))

    def onBuryNote(self):
        self.mw.checkpoint(_("Bury"))
        self.mw.col.sched.buryNote(self.card.nid)
        self.mw.reset(guiOnly=True)
        tooltip(_("Note buried."))

    def onRecordVoice(self):
        self._recordedAudio = getAudio(self.mw, encode=False)
        self.onReplayRecorded()

    def onReplayRecorded(self):
        if not self._recordedAudio:
            return tooltip(_("You haven't recorded your voice yet."))
        clearAudioQueue()
        play(self._recordedAudio)
