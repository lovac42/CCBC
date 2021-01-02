# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import os, re, anki, sys
import base64, urllib
import unicodedata
import requests
import aqt

from anki.media import MediaManager
from anki.utils import checksum, isWin, isMac
from anki.db import DB, DBError
from anki.notes import Note
from anki.find import Finder
from ccbc.utils import isURL, isDataURL
from anki.sync import AnkiRequestsClient
from anki.lang import _
from anki.consts import *


RE_CR_LF_TAB = re.compile(r'\r|\n|\t')

RE_FILE_URI = re.compile(r'^file://', re.I)
RE_LOCALHOST_URI = re.compile(r'^file://([^/])', re.I)      #file://localhost/etc/usr
RE_LOCALPATH_URI = re.compile(r'^file:(/[^/]|///)', re.I)   #file:///etc/usr or file:/etc/usr


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
        src = urllib.parse.unquote(src)
        if src.startswith("//"):
            #PITA: protocol-relative URL, These must be removed as it causes
            #5-30 secs freezes due to network lag.
            protocal='https:'

        if protocal or isURL(src):
            src = self.importResource(src, protocal)
        elif isDataURL(src):
            src = RE_CR_LF_TAB.sub('', src)
            src = self.inlinedImageToFilename(src)
        return src


    def importResource(self, url, protocal=''):
        "Download file into media folder and return local filename or None."
        purl=protocal+url
        ct = None
        if RE_FILE_URI.search(purl):
            filecontents=self._importLocalResource(url)
            if not filecontents:
                return url
        else: # https://
            res=self._importNetResource(url,protocal)
            if not res:
                return url
            filecontents = res.content
            ct = res.headers.get("content-type")
        return self.writeData(purl, filecontents, typeHint=ct)


    def _importLocalResource(self, path):
        if isWin:
            if RE_LOCALHOST_URI.search(path):
                # try samba path, windows only
                src='\\\\'+RE_LOCALHOST_URI.sub(r'\1', path)
            else:
                src=RE_LOCALPATH_URI.sub('', path)
        else:
            src=RE_LOCALPATH_URI.sub('/', path)
        return open(src, "rb").read()


    def _importNetResource(self, url, protocal=''):
        try:
            reqs = AnkiRequestsClient()
            reqs.timeout = 30
            r = reqs.get(protocal+url)
            if r.status_code != 200:
                if protocal: #retry with http instead of https
                    return self._importNetResource('http:'+url)
                aqt.utils.showWarning(_("Unexpected response code: %s") % r.status_code)
                return
            return r
        except urllib.error.URLError as e:
            if protocal: #retry with http instead of https
                return self._importNetResource('http:'+url)
            aqt.utils.showWarning(_("An error occurred while opening %s") % e)
            return
        except requests.exceptions.RequestException as e:
            aqt.utils.showWarning(_("An error occurred while requesting %s") % e)
            return


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
                return _addPastedImage(self, data, "."+ext)
        return ""


    def escapeImages(self, string, unescape=False):
        if unescape:
            fn = urllib.parse.unquote
        else:
            fn = urllib.parse.quote
        def repl(match):
            tag = match.group(0)
            fname = match.group("fname")
            if re.match("(https?|file|ftp)://?", fname):
                return tag
            return tag.replace(fname, fn(fname))
        for reg in self.imgRegexps:
            string = re.sub(reg, repl, string)
        return string


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
        #_ files, so it's added it back in for now.
        nohave = [x for x in allRefs if not x.startswith("_") and not isURL(x)]

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

        return (nohave, unused, warnings)
