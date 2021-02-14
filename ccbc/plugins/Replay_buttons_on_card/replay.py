# -*- mode: Python ; coding: utf-8 -*-
#
# Copyright © 2013–16 Roland Sieker <ospalh@gmail.com>
#
# License: GNU AGPL, version 3 or later;
# http://www.gnu.org/copyleft/agpl.html

# *Modified* with bug fixes.
# This file has been modified for bug fixes, and not related to the original.

"""Add-on for Anki 2 to add AnkiDroid-style replay buttons."""

# part of the code has been integrated into the reviewer/clayout/browser,
# other parts may have been modified as needed.

import re
from anki.hooks import addHook
from aqt import mw


RE_PLAYBTN = re.compile(r"\[sound:(.*?)\]")


def play_button_filter(qa_html, qa_type, *args, **kwargs):
    if not mw.pm.profile.get("ccbc.showAudPlayBtn", True):
        return qa_html
    if mw.state ==  "review" and mw.viewmanager.ir.isIRCard():
        return qa_html

    def add_button(sound):
        if 'q' == qa_type:
            title = u"Replay"
        else:
            title = sound.group(1)
        return u"""%s\
<a href='javascript:py.link("ankiplay:%s");' \
title="%s" class="replaybutton browserhide ir-filter"><span><svg viewBox="0 0 32 32">\
<polygon points="11,25 25,16 11,7"/>Replay</svg></span></a>\
"""%(sound.group(0), sound.group(1).replace("'","&#39;"), title)

    s,cnt=RE_PLAYBTN.subn(add_button, qa_html)
    if not cnt:
        return qa_html
    #prevent focus on btn clicks/touches
    return s + """<script>
$('.replaybutton').on('mousedown',function(e){e.preventDefault();});
$('.replaybutton').on('touchdown',function(e){e.preventDefault();});
</script>"""


addHook("mungeQA", play_button_filter)
