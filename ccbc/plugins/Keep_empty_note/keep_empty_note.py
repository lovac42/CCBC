# FROM: https://github.com/Arthur-Milchior/anki-keep-empty-note/blob/master/init.py
# This file has been modified by lovac42 for CCBC, and is not the same as the original.
# Modificatios: Only onDelete is necessary here.


import os
from anki.lang import _, ngettext
from aqt import dialogs
from aqt.utils import saveGeom, showWarning, tooltip
from aqt.qt import *



#TODO: Remove fstrings, they don't work on Pi

def p(msg):
    if os.getenv("ANKIDEV",0):
        print(msg)


def onDelete(mw, diag, cids):
    p(f"Calling new onDelete with cids {cids}")

    cids = set(mw.col.emptyCids()) #change here to make a set
    saveGeom(diag, "emptyCards")
    QDialog.accept(diag)
    mw.checkpoint(_("Delete Empty"))

    # Beginning of changes
    nidToCidsToDelete = dict()
    for cid in cids:
        card = mw.col.getCard(cid)
        note = card.note()
        nid = note.id
        if nid not in nidToCidsToDelete:
            p(f"note {nid} not yet in nidToCidsToDelete. Thus adding it")
            nidToCidsToDelete[nid] = set()
        else:
            p(f"note {nid} already in nidToCidsToDelete.")
        nidToCidsToDelete[nid].add(cid)
        p(f"Adding card {cid} to note {nid}.")

    emptyNids = set()
    cardsOfEmptyNotes = set()
    for nid, cidsToDeleteOfNote in nidToCidsToDelete.items():
        note = mw.col.getNote(nid)
        cidsOfNids = set([card.id for card in note.cards()])
        p(f"In note {nid}, the cards are {cidsOfNids}, and the cards to delete are {cidsToDeleteOfNote}")
        if cidsOfNids == cidsToDeleteOfNote:
            p(f"Both sets are equal")
            emptyNids.add(note.id)
            cids -= cidsOfNids
        else:
            p(f"Both sets are different")

    mw.col.remCards(cids, notes = False)
    nidsWithTag = set(mw.col.findNotes("tag:NoteWithNoCard"))
    p (f"emptyNids is {emptyNids}, nidsWithTag is {nidsWithTag}")

    for nid in emptyNids - nidsWithTag:
        note = mw.col.getNote(nid)
        note.addTag("NoteWithNoCard")
        p(f"Adding tag to note {note.id}")
        note.flush()

    for nid in nidsWithTag - emptyNids:
        note = mw.col.getNote(nid)
        # TODO: If there's only 1 note, this method is never triggered.
        # So the tag stays.
        note.delTag("NoteWithNoCard")
        p(f"Removing tag from note {note.id}")
        note.flush()

    if emptyNids:
        showWarning(f"""{len(emptyNids)} note(s) should have been deleted because they had no more cards. They now have the tag "NoteWithNoCard". Please go check them. Then either edit them to save their content, or delete them from the browser.""")
        browser = dialogs.open("Browser", mw)
        browser.form.searchEdit.lineEdit().setText("tag:NoteWithNoCard")
        browser.onSearchActivated()

    # end of changes
    tooltip(ngettext("%d card deleted.", "%d cards deleted.", len(cids)) % len(cids))
    mw.reset()

