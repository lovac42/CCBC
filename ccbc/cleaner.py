# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import re
from html.parser import HTMLParser


EMPTY_ELEMENTS = (
    "br","img","hr","link","meta","base",
    "embed","area","input","keygen","col",
    "param","source","track","wbr"
)

class Cleaner(HTMLParser):
    noScript = -1 # 0=disable

    def __init__(self, mw):
        HTMLParser.__init__(self)
        self.mw = mw
        self.data = []
        self.stack = []

    def handle_startendtag(self, tag, attributes):
        if tag=='img':
            src=self.get_attr('src',attributes)
            s=self.mw.col.media.handle_resource(src)
            if not s: return
            s='<img src="%s"/>'%s
        elif self.noScript:
            return
        else:
            s=self.get_starttag_text()
        self.data.append(s)

    def handle_starttag(self, tag, attributes):
        if tag in EMPTY_ELEMENTS:
            self.handle_startendtag(tag,attributes)
            return
        if tag=='script' and self.noScript:
            self.noScript=1
            return
        s=self.get_starttag_text()
        self.data.append(s)
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag=='script' and self.noScript:
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


    # UTILS:

    def toString(self):
        return ''.join(self.data)

    def get_attr(self, seekTag, attributes):
        for a in attributes:
            if a[0]==seekTag:
                return a[1]

    def sub_attr(self, attributes, swap):
        arr=[]
        for a,v in attributes:
            r=swap.get(a, v)
            arr.append('%s="%s" '%(a,r))
        return ''.join(arr)








# Base class for ebook and web imports

class HTMLCleaner(Cleaner):

    status={
        "head":False,
        "body":False,
        "base":"",
    }


    def __init__(self, mw):
        Cleaner.__init__(self, mw)
        self.noScript = 0 #disabled


    def handle_startendtag(self, tag, attributes):
        if self.status['head'] and tag=='base':
            self.status['base']=self.get_attr('href',attributes)

        elif tag=='link':
            rel=self.get_attr('rel',attributes)
            if rel and rel=='stylesheet':
                # TODO: add base url
                href=self.get_attr('href',attributes)
                href=self.mw.col.media.handle_resource(href)
                if not href: return
                s='<link href="%s" rel="stylesheet" />'%href
                self.data.append(s)

        if tag=='img':
            src=self.get_attr('src',attributes)
            s=self.mw.col.media.handle_resource(src)
            if not s: return
            #keeps all attributes for alignment
            s=self.sub_attr(attributes,{'src':s})
            s='<img %s />'%s
            self.data.append(s)

        elif self.status['body']:
            Cleaner.handle_startendtag(self, tag, attributes)


    def handle_starttag(self, tag, attributes):
        if tag in EMPTY_ELEMENTS:
            self.handle_startendtag(tag,attributes)
        elif tag in ('head','body'):
            self.status[tag]=True
        if self.status['body']:
            Cleaner.handle_starttag(self, tag, attributes)


    def handle_endtag(self, tag):
        if tag in ('head','body'):
            self.status[tag]=False
        if self.status['body']:
            Cleaner.handle_endtag(self, tag)


    def handle_data(self, data):
        if self.status['body']:
            Cleaner.handle_data(self, data)


    def handle_comment(self, data):
        self.data.append('<!-- %s -->'%data)

    # def handle_decl(self, data):
        # self.data.append(data)

