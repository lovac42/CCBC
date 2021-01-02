# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import re
from html.parser import HTMLParser
from collections import deque


EMPTY_ELEMENTS = (
    "br","img","hr","link","meta","base",
    "embed","area","input","keygen","col",
    "param","source","track","wbr"
)



# Non-aggresive class for matching <div></div>
# Also filters out // urls which causes webkit to freeze
# due to network lags.

#TODO: write unit test for checking various html tags, white spaces, escape chars

class TidyTags(HTMLParser):
    tag_src_map = {"img":"src", "link":"href"}

    def __init__(self, mw, localize=False):
        HTMLParser.__init__(self)
        self.data = deque()
        self.stack = deque()

        self.noScript = -1 # 0=disable; 1=on; -1=off;

        self.rm_elements = ["iframe","object"]

        prof = mw.pm.profile
        if prof.get("tidyTags.noScript",True):
            self.rm_elements.append("script")
            self.rm_elements.append("noscript")
        # TODO: separate configs for html tags: style, form, etc...

        self.importer = None
        if localize and prof.get("tidyTags.importMedia",True):
            self.importer=mw.col.media


    # Empty elements tag endings "/>" will be automatically fixed

    def handle_starttag(self, tag, attributes):
        if self.noScript and tag in self.rm_elements:
            self.noScript=1
            return

        key=self.tag_src_map.get(tag)
        if key:
            s=self.importMedia(key,attributes)
            s='<%s %s/>'%(tag,s)
        else:
            s=self.get_starttag_text()
            # prevent protocol-relative URLs from freezing webkit
            s=re.sub(r'''(\s+(?:src|href)=['"])//''','\\1/_/',s,re.I)
        self.data.append(s)
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.noScript and tag in self.rm_elements:
            self.noScript=-1
            return
        if tag in EMPTY_ELEMENTS:
            return

        try:
            if self.stack[-1] == tag:
                self.stack.pop()
                self.data.append('</%s>'%tag)
        except IndexError: pass

    def handle_data(self, data):
        if self.noScript>0: #script block
            return
        self.data.append(data)

    def handle_comment(self, data):
        self.data.append('<!-- %s -->'%data)

    def handle_decl(self, data):
        self.data.append(data)


    # UTILS:

    def toString(self):
        return ''.join(self.data)

    def importMedia(self, key, attributes):
        src=self.get_attr(key,attributes)
        if self.importer:
            s=self.importer.handle_resource(src)
        else:
            s=re.sub(r'^//','https://',src)
        s=self.sub_attr(attributes,{key:s})
        return s

    def get_attr(self, seekTag, attributes):
        for a in attributes:
            if a[0]==seekTag:
                return a[1]
        return "" #for missing attrs e.g. <img/> (mnemosyne imports)

    def sub_attr(self, attributes, swap):
        arr=[]
        for a,v in attributes:
            r=swap.get(a, v)
            arr.append('%s="%s" '%(a,r))
        return ''.join(arr)


