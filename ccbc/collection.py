# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import anki
import time
import datetime
from anki.collection import *
from anki.utils import ids2str
from anki.consts import *
from anki.lang import _
from anki.models import ModelManager
from anki.decks import DeckManager

from ccbc.find import ExtFinder
from ccbc.media import ExtMediaManager
from ccbc.plugins.fix_redue import redue as fix_redue


class _ExtCollection(anki.collection._Collection):

    def __init__(self, db, server=False, log=False):
        self._debugLog = log
        self.db = db
        self.path = db._path
        self._openLog()
        self.log(self.path, anki.version)
        self.server = server
        self._lastSave = time.time()
        self.clearUndo()
        self.media = ExtMediaManager(self, server)
        self.models = ModelManager(self)
        self.decks = DeckManager(self)
        self.tags = TagManager(self)
        self.load()
        if not self.crt:
            d = datetime.datetime.today()
            d -= datetime.timedelta(hours=4)
            d = datetime.datetime(d.year, d.month, d.day)
            d += datetime.timedelta(hours=4)
            self.crt = int(time.mktime(d.timetuple()))
        self._loadScheduler()
        try: #check if scheduler is from modulez
            self.sched.type
        except:
            self.sched.type="anki"
        if not self.conf.get("newBury", False):
            self.conf['newBury'] = True
            self.setMod()

    def findCards(self, query, order=False):
        return ExtFinder(self).findCards(query, order)

    def findNotes(self, query):
        return ExtFinder(self).findNotes(query)

    def changeSchedulerVer(self, ver):
        anki.collection._Collection.changeSchedulerVer(self, ver)
        try: #check if scheduler is from modulez
            self.sched.type
        except:
            self.sched.type="anki"


    #Addon: clearer empty card info
    #https://github.com/Arthur-Milchior/anki-clearer-empty-card
    def emptyCardReport(self, cids):
        models = self.models
        rep = ""
        for ords, mid, flds in self.db.all("""
        select group_concat(ord), mid, flds from cards c, notes n
        where c.nid = n.id and c.id in %s group by nid order by mid""" % ids2str(cids)):
            model = models.get(mid)
            modelName  = model["name"]
            templates = model["tmpls"]
            isCloze = model["type"] == MODEL_CLOZE
            rep += _("Empty cards")+" ("+modelName+"): "
            if isCloze:
                 rep+=ords
            else:
                for ord in ords.split(","):
                    ord  = int(ord)
                    templateName = templates[ord]["name"]
                    rep += templateName+", "
            rep +="\nFields: %(f)s\n\n" % dict(f=flds.replace("\x1f", " / "))
        return rep



    def fixIntegrity(self):
        "Fix possible problems and rebuild caches."

        fix_redue(self)

        problems = []
        curs = self.db.cursor()
        self.save()
        oldSize = os.stat(self.path)[stat.ST_SIZE]
        if self.db.scalar("pragma integrity_check") != "ok":
            return (_("Collection is corrupt. Please see the manual."), False)
        # note types with a missing model
        ids = self.db.list("""
select id from notes where mid not in """ + ids2str(self.models.ids()))
        if ids:
            problems.append(
                ngettext("Deleted %d note with missing note type.",
                         "Deleted %d notes with missing note type.", len(ids))
                         % len(ids))
            self.remNotes(ids)
        # for each model
        for m in self.models.all():
            for t in m['tmpls']:
                if t['did'] == "None":
                    t['did'] = None
                    problems.append(_("Fixed AnkiDroid deck override bug."))
                    self.models.save(m)
            if m['type'] == MODEL_STD:
                # model with missing req specification
                if 'req' not in m:
                    self.models._updateRequired(m)
                    problems.append(_("Fixed note type: %s") % m['name'])
                # cards with invalid ordinal
                ids = self.db.list("""
select id from cards where ord not in %s and nid in (
select id from notes where mid = ?)""" %
                                   ids2str([t['ord'] for t in m['tmpls']]),
                                   m['id'])
                if ids:
                    problems.append(
                        ngettext("Deleted %d card with missing template.",
                                 "Deleted %d cards with missing template.",
                                 len(ids)) % len(ids))
                    self.remCards(ids)
            # notes with invalid field count
            ids = []
            for id, flds in self.db.execute(
                    "select id, flds from notes where mid = ?", m['id']):
                if (flds.count("\x1f") + 1) != len(m['flds']):
                    ids.append(id)
            if ids:
                problems.append(
                    ngettext("Deleted %d note with wrong field count.",
                             "Deleted %d notes with wrong field count.",
                             len(ids)) % len(ids))
                self.remNotes(ids)
        # delete any notes with missing cards
        ids = self.db.list("""
select id from notes where id not in (select distinct nid from cards)""")
        if ids:
            cnt = len(ids)
            problems.append(
                ngettext("Deleted %d note with no cards.",
                         "Deleted %d notes with no cards.", cnt) % cnt)
            self._remNotes(ids)
        # cards with missing notes
        ids = self.db.list("""
select id from cards where nid not in (select id from notes)""")
        if ids:
            cnt = len(ids)
            problems.append(
                ngettext("Deleted %d card with missing note.",
                         "Deleted %d cards with missing note.", cnt) % cnt)
            self.remCards(ids)
        # cards with odue set when it shouldn't be
        ids = self.db.list("""
select id from cards where odue > 0 and (type=1 or queue=2) and not odid""")
        if ids:
            cnt = len(ids)
            problems.append(
                ngettext("Fixed %d card with invalid properties.",
                         "Fixed %d cards with invalid properties.", cnt) % cnt)
            self.db.execute("update cards set odue=0 where id in "+
                ids2str(ids))
        # cards with odid set when not in a dyn deck
        dids = [id for id in self.decks.allIds() if not self.decks.isDyn(id)]
        ids = self.db.list("""
select id from cards where odid > 0 and did in %s""" % ids2str(dids))
        if ids:
            cnt = len(ids)
            problems.append(
                ngettext("Fixed %d card with invalid properties.",
                         "Fixed %d cards with invalid properties.", cnt) % cnt)
            self.db.execute("update cards set odid=0, odue=0 where id in "+
                ids2str(ids))
        # tags
        self.tags.registerNotes()
        # field cache
        for m in self.models.all():
            self.updateFieldCache(self.models.nids(m))
        # new cards can't have a due position > 32 bits, so wrap items over

        # 2 million back to 1 million
        # curs.execute("""
# update cards set due=1000000+due%1000000,mod=?,usn=? where due>=1000000
# and type=0""", [intTime(), self.usn()])
        # if curs.rowcount:
            # problems.append("Found %d new cards with a due number >= 1,000,000 - consider repositioning them in the Browse screen." % curs.rowcount)

        # new card position
        self.conf['nextPos'] = self.db.scalar(
            "select max(due)+1 from cards where type = 0") or 0
        # reviews should have a reasonable due #
        ids = self.db.list(
            "select id from cards where queue = 2 and due > 100000")
        if ids:
            problems.append("Reviews had incorrect due date.")
            self.db.execute(
                "update cards set due = ?, ivl = 1, mod = ?, usn = ? where id in %s"
                % ids2str(ids), self.sched.today, intTime(), self.usn())
        # v2 sched had a bug that could create decimal intervals
        curs.execute("update cards set ivl=round(ivl),due=round(due) where ivl!=round(ivl) or due!=round(due)")
        if curs.rowcount:
            problems.append("Fixed %d cards using float point for intervals." % curs.rowcount)

        curs.execute("update revlog set ivl=round(ivl),lastIvl=round(lastIvl) where ivl!=round(ivl) or lastIvl!=round(lastIvl)")
        if curs.rowcount:
            problems.append("Fixed %d review history entries using float point for intervals." % curs.rowcount)
        # models
        if self.models.ensureNotEmpty():
            problems.append("Added missing note type.")
        # and finally, optimize
        self.optimize()
        newSize = os.stat(self.path)[stat.ST_SIZE]
        txt = _("Database rebuilt and optimized.")
        ok = not problems
        problems.append(txt)
        # if any problems were found, force a full sync
        if not ok:
            self.modSchema(check=False)
        self.save()
        return ("\n".join(problems), ok)

