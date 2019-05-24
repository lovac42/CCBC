# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import re, base64, urllib
from html.parser import HTMLParser
from aqt.qt import *
from anki.utils import checksum

class Cleaner(HTMLParser):
    def __init__(self, mw):
        HTMLParser.__init__(self)
        self.mw = mw
        self.data = []
        self.stack = []

    def handle_startendtag(self, tag, attributes):
        if tag=='img':
            s=self.handle_src(attributes)
        else:
            s=self.get_starttag_text()
        self.data.append(s)

    def handle_starttag(self, tag, attributes):
        if tag=='img':
            s=self.handle_src(attributes)
        else:
            s=self.get_starttag_text()
        self.data.append(s)
        self.stack.append(tag)

    def handle_endtag(self, tag):
        try:
            if self.stack[-1] == tag:
                self.stack.pop()
                self.data.append('</%s>'%tag)
        except IndexError: pass

    def handle_data(self, data):
        self.data.append(data)

    def handle_comment(self, data):
        self.data.append('<!-- %s -->'%data)

    # def handle_decl(self, data):
        # self.data.append(data)

    def toString(self):
        return ''.join(self.data)


    def handle_src(self, attributes):
        arr=[]
        for a in attributes:
            src=None
            if a[0]=='src':
                src=urllib.parse.unquote(a[1])
                if src.lower().startswith("file://"):
                    src = os.path.basename(src)
                if self.isURL(src):
                    src = self.importImg(src)
                elif src.lower().startswith("data:image/"):
                    src = re.sub(r'\r|\n|\t','',src)
                    src = self.inlinedImageToFilename(src)
            arr.append('%s="%s" '%(a[0],src or a[1]))
        return "<img %s/>"%''.join(arr)

    def isURL(self, s):
        s = s.lower()
        return (s.startswith("http://")
            or s.startswith("https://")
            or s.startswith("ftp://")
            or s.startswith("file://"))

    def importImg(self, url):
        "Download file into media folder and return local filename or None."
        # urllib doesn't understand percent-escaped utf8, but requires things like
        # '#' to be escaped. we don't try to unquote the incoming URL, because
        # we should only be receiving file:// urls from url mime, which is unquoted
        if url.lower().startswith("file://"):
            url = url.replace("%", "%25")
            url = url.replace("#", "%23")
        # fetch it into a temporary folder
        self.mw.progress.start(immediate=True)
        try:
            req = urllib.request.Request(url, None, {
                'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
            filecontents = urllib.request.urlopen(req).read()
        except urllib.error.URLError as e:
            showWarning(_("An error occurred while opening %s") % e)
            return
        finally:
            self.mw.progress.finish()
        path = urllib.parse.unquote(url)
        return self._addMediaFromData(path, filecontents)

    def inlinedImageToFilename(self, txt):
        prefix = "data:image/"
        suffix = ";base64,"
        for ext in ("jpg", "jpeg", "png", "gif"):
            fullPrefix = prefix + ext + suffix
            if txt.startswith(fullPrefix):
                b64data = txt[len(fullPrefix):].strip()
                data = base64.b64decode(b64data, validate=True)
                if ext == "jpeg":
                    ext = "jpg"
                return self._addPastedImage(data, "."+ext)
        return ""

    # ext should include dot
    def _addPastedImage(self, data, ext):
        # hash and write
        csum = checksum(data)
        fname = "{}-{}{}".format("paste", csum, ext)
        return self._addMediaFromData(fname, data)

    def _addMediaFromData(self, fname, data):
        return self.mw.col.media.writeData(fname, data)











class HTMLCleaner(Cleaner):
    def __init__(self, mw):
        Cleaner.__init__(self, mw)
        self.record=False

    def handle_startendtag(self, tag, attributes):
        if self.record:
            Cleaner.handle_startendtag(self, tag, attributes)

    def handle_starttag(self, tag, attributes):
        if tag.lower()=='body':
            self.record=True
            return
        if self.record:
            Cleaner.handle_starttag(self, tag, attributes)

    def handle_endtag(self, tag):
        if tag.lower()=='body':
            self.record=False
        if self.record:
            Cleaner.handle_endtag(self, tag)

    def handle_data(self, data):
        if self.record:
            Cleaner.handle_data(self, data)

    def handle_comment(self, data):
        if self.record:
            Cleaner.handle_comment(self, data)

    # def handle_decl(self, data):
        # self.data.append(data)



# Tests
if __name__ == "__main__":
    import urllib.request as urllib2
    html_page = html_page = urllib2.urlopen("https://developer.chrome.com")
    parser = HTMLCleaner()
    parser.feed(str(html_page.read()))
    print ( str(parser.toString().replace('\\n','\n')) )
