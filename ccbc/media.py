# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import os, re, anki
import base64, urllib
from anki.media import MediaManager
from anki.utils import checksum
from ccbc.utils import isURL


class ExtMediaManager(MediaManager):

    cssRegexps = [
        # href element quoted case
        "(?i)(<link[^>]* href=(?P<str>[\"'])(?P<fname>[^>]+?)(?P=str)[^>]*>)",
        # unquoted case
        "(?i)(<link[^>]* href=(?!['\"])(?P<fname>[^ >]+)[^>]*?>)",
    ]


    def __init__(self, col, server):
        MediaManager.__init__(self, col, server)
        self.regexps += self.cssRegexps


    def handle_resource(self, src):
        # src=urllib.parse.unquote(src)
        if src.lower().startswith("file://"):
            src = os.path.basename(src)
        if isURL(src):
            src = self.importImg(src)
        elif src.lower().startswith("data:image/"):
            src = re.sub(r'\r|\n|\t','',src)
            src = self.inlinedImageToFilename(src)
        else:
            return None #not valid uri
        return src

    def importImg(self, url):
        "Download file into media folder and return local filename or None."
        # urllib doesn't understand percent-escaped utf8, but requires things like
        # '#' to be escaped. we don't try to unquote the incoming URL, because
        # we should only be receiving file:// urls from url mime, which is unquoted
        if url.lower().startswith("file://"):
            url = url.replace("%", "%25")
            url = url.replace("#", "%23")
        # fetch it into a temporary folder
        try:
            req = urllib.request.Request(url, None, {
                'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
            filecontents = urllib.request.urlopen(req).read()
        except urllib.error.URLError as e:
            showWarning(_("An error occurred while opening %s") % e)
            return
        path = urllib.parse.unquote(url)
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



