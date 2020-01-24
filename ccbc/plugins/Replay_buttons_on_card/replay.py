# -*- mode: Python ; coding: utf-8 -*-
#
# Copyright © 2013–16 Roland Sieker <ospalh@gmail.com>
#
# License: GNU AGPL, version 3 or later;
# http://www.gnu.org/copyleft/agpl.html

"""Add-on for Anki 2 to add AnkiDroid-style replay buttons."""

# part of the code has been integrated into the reviewer/clayout/browser,
# other parts may have been modified as needed.

import re
from anki.hooks import addHook
from aqt import mw


RE=re.compile(r"\[sound:(.*?)\]")


def play_button_filter(qa_html, qa_type, *args, **kwargs):
    if not mw.pm.profile.get("ccbc.showAudPlayBtn", True):
        return qa_html

    def add_button(sound):
        if 'q' == qa_type:
            title = u"Replay"
        else:
            title = sound.group(1)
        return u"""%s\
<a href='javascript:py.link("ankiplay:%s");' \
title="%s" class="replaybutton browserhide"><span><svg viewBox="0 0 32 32">\
<polygon points="11,25 25,16 11,7"/>Replay</svg></span></a>\
<span style="display: none;">&#91;sound:%s&#93;</span>\
"""%(sound.group(0), sound.group(1), title, sound.group(1))
        # The &#91; &#93; are the square brackets that we want to
        # appear as brackets and not trigger the playing of the
        # sound. The span inside the a around the svg is there to
        # bring this closer in line with AnkiDroid.

    s,cnt=RE.subn(add_button, qa_html)
    if not cnt:
        return qa_html
    #prevent focus on btn clicks/touches
    return s + """<script>
$('.replaybutton').on('mousedown',function(e){e.preventDefault();});
$('.replaybutton').on('touchdown',function(e){e.preventDefault();});
</script>"""


addHook("mungeQA", play_button_filter)
