# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import os, re, anki, sys
import base64, urllib
import unicodedata
from anki.media import MediaManager
from anki.utils import checksum, isWin, isMac
from anki.db import DB, DBError
from anki.notes import Note
from anki.find import Finder
from ccbc.utils import isURL
from anki.lang import _
from anki.consts import *



class ExtMediaManager(MediaManager):

    processSubdir = False

    cssRegexps = [
        # href element quoted case
        "(?i)(<link[^>]* href=(?P<str>[\"'])(?P<fname>[^>]+?)(?P=str)[^>]*>)",
        # unquoted case
        "(?i)(<link[^>]* href=(?!['\"])(?P<fname>[^ >]+)[^>]*?>)",
    ]


    def __init__(self, col, server):
        MediaManager.__init__(self, col, server)
        self.regexps += self.cssRegexps

        if self.processSubdir:
            self._illegalCharReg = re.compile(r'[][><:"?*^\\|\0\r\n]')


    def handle_resource(self, src):
        protocal=''
        # src=urllib.parse.unquote(src)
        if src.startswith("//"): #PITA: protocol-relative URL
            protocal='https:'    #These must be removed as it causes 5sec freezes due to network lag.
        elif src.lower().startswith("file://"):
            src = os.path.basename(src)

        if protocal or isURL(src):
            src = self.importImg(src, protocal)
        elif src.lower().startswith("data:image/"):
            src = re.sub(r'\r|\n|\t','',src)
            src = self.inlinedImageToFilename(src)
        return src

    def importImg(self, url, protocal=''):
        "Download file into media folder and return local filename or None."
        # urllib doesn't understand percent-escaped utf8, but requires things like
        # '#' to be escaped. we don't try to unquote the incoming URL, because
        # we should only be receiving file:// urls from url mime, which is unquoted
        if not protocal and \
        url.lower().startswith("file://"):
            url = url.replace("%", "%25")
            url = url.replace("#", "%23")

        # fetch it into a temporary folder
        purl=protocal+url
        try:
            req = urllib.request.Request(purl, None, {
                'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
            filecontents = urllib.request.urlopen(req).read()
        except urllib.error.URLError as e:
            if protocal: #retry with http instead of https
                return self.importImg('http:'+url)
            print("Can't get url: %s" % e)
            return url

        path = urllib.parse.unquote(purl)
        return self.writeData(path, filecontents)

    def inlinedImageToFilename(self, txt):
        def _addPastedImage(media, data, ext):
            # ext should include dot
            # hash and write
            csum = checksum(data)
            fname = "{}-{}{}".format("paste", csum, ext)
            return media.writeData(fname, data)

        prefix = "data:image/"
        suffix = ";base64,"
        for ext in ("jpg", "jpeg", "png", "gif"):
            fullPrefix = prefix + ext + suffix
            if txt.startswith(fullPrefix):
                b64data = txt[len(fullPrefix):].strip()
                data = base64.b64decode(b64data, validate=True)
                if ext == "jpeg":
                    ext = "jpg"
                return addPastedImage(self, data, "."+ext)
        return ""



    def writeData(self, opath, data, typeHint=None):
        # if fname is a full path, use only the basename
        fname = os.path.basename(opath)

        # if it's missing an extension and a type hint was provided, use that
        if not os.path.splitext(fname)[1] and typeHint:
            # mimetypes is returning '.jpe' even after calling .init(), so we'll do
            # it manually instead
            typeMap = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "text/css": ".css",
            }
            if typeHint in typeMap:
                fname += typeMap[typeHint]

        # make sure we write it in NFC form (pre-APFS Macs will autoconvert to NFD),
        # and return an NFC-encoded reference
        fname = unicodedata.normalize("NFC", fname)
        # ensure it's a valid filename
        base = self.cleanFilename(fname)
        (root, ext) = os.path.splitext(base)
        def repl(match):
            n = int(match.group(1))
            return " (%d)" % (n+1)
        # find the first available name
        csum = checksum(data)
        while True:
            mfolder=self.col.conf.get("customMediaFolder", "")
            fname = root + ext
            path = os.path.join(self.dir(), fname)
            # if it doesn't exist, copy it directly
            if not os.path.exists(path):
                with open(path, "wb") as f:
                    f.write(data)
                if mfolder:
                    return mfolder+'/'+fname
                return fname
            # if it's identical, reuse
            with open(path, "rb") as f:
                if checksum(f.read()) == csum:
                    if mfolder:
                        return mfolder+'/'+fname
                    return fname
            # otherwise, increment the index in the filename
            reg = r" \((\d+)\)$"
            if not re.search(reg, root):
                root = root + " (1)"
            else:
                root = re.sub(reg, repl, root)






    #TODO: Create media manager to find, rename, relocate medias instead.

    #Addon: Tag missing media - https://ankiweb.net/shared/info/2027876532
    def check(self, local=None):
        "Return (missingFiles, unusedFiles)."

        mdir = self.dir()
        # gather all media references in NFC form
        allRefs = set()
        refsToNid = dict() # this dic is new
        for nid, mid, flds in self.col.db.execute("select id, mid, flds from notes"):
            noteRefs = self.filesInStr(mid, flds)
            # check the refs are in NFC
            for f in noteRefs:
                # if they're not, we'll need to fix them first
                if f != unicodedata.normalize("NFC", f):
                    self._normalizeNoteRefs(nid)
                    noteRefs = self.filesInStr(mid, flds)
                    break
            # new. update refsToNid
            for f in noteRefs:
                if f not in refsToNid:
                    refsToNid[f] = set()
                refsToNid[f].add(nid)
            # end new
            allRefs.update(noteRefs)

        # loop through media folder
        unused = []
        if local is None:
            files = os.listdir(mdir)
        else:
            files = local
        renamedFiles = False
        dirFound = False
        warnings = []
        for file in files:
            if not local:
                if not os.path.isfile(file):
                    if self.processSubdir:
                        dir=file
                        path=[dir+'/'+f for f in os.listdir(dir)]
                        files.extend(path)
                    else:
                        # ignore directories
                        dirFound = True
                    continue

            if file.startswith("_"):
                # leading _ says to ignore file
                continue

            if self.hasIllegal(file):
                name = file.encode(sys.getfilesystemencoding(), errors="replace")
                name = str(name, sys.getfilesystemencoding())
                warnings.append(
                    _("Invalid file name, please rename: %s") % name)
                continue

            nfcFile = unicodedata.normalize("NFC", file)

            # we enforce NFC fs encoding on non-macs
            if not isMac and not local:
                if file != nfcFile:
                    # delete if we already have the NFC form, otherwise rename
                    if os.path.exists(nfcFile):
                        os.unlink(file)
                        renamedFiles = True
                    else:
                        os.rename(file, nfcFile)
                        renamedFiles = True
                    file = nfcFile

            # compare
            if nfcFile not in allRefs:
                unused.append(file)
            else:
                allRefs.discard(nfcFile)

        # if we renamed any files to nfc format, we must rerun the check
        # to make sure the renamed files are not marked as unused
        if renamedFiles:
            return self.check(local=local)

        #This line was removed in the addon, but was causing problems for
        #_files, so it's added it back in for now.
        nohave = [x for x in allRefs if not x.startswith("_")]

        # NEW: A line here removed because it was a bug
        # New
        finder = Finder(self.col)
        alreadyMissingNids = finder.findNotes("tag:MissingMedia")
        nidsOfMissingRefs = set()
        for ref in nohave:
            nidsOfMissingRefs.update(refsToNid[ref])
            #print(f"nidsOfMissingRefs is now {nidsOfMissingRefs}")

        for nid in nidsOfMissingRefs:
            if nid not in alreadyMissingNids:
                # print(f"missing nid {nid}")
                note = Note(self.col, id = nid)
                note.addTag("MissingMedia")
                note.flush()

        for nid in alreadyMissingNids:
            if nid not in nidsOfMissingRefs:
                # print(f"not missing anymore nid {nid}")
                note = Note(self.col, id = nid)
                note.delTag("MissingMedia")
                note.flush()
        # end new

        # make sure the media DB is valid
        try:
            self.findChanges()
        except DBError:
            self._deleteDB()
        if not self.processSubdir and dirFound:
            warnings.append(
                _("Anki does not support files in subfolders of the collection.media folder."))

        if nohave:
            from aqt import mw, dialogs
            browser = dialogs.open("Browser", mw)
            browser.form.searchEdit.lineEdit().setText("tag:MissingMedia")
            browser.onSearchActivated()
        return (nohave, unused, warnings)
