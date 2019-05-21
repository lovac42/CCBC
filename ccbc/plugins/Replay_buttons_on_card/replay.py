# -*- mode: Python ; coding: utf-8 -*-
#
# Copyright © 2013–16 Roland Sieker <ospalh@gmail.com>
#
# License: GNU AGPL, version 3 or later;
# http://www.gnu.org/copyleft/agpl.html

"""Add-on for Anki 2 to add AnkiDroid-style replay buttons."""

# part of the code has been integrated into the reviewer/clayout/browser

import re
from anki.hooks import addHook
from anki.cards import Card

# this part wraps around aqt.util.mungeQA
def play_button_filter(
        qa_html, qa_type, dummy_fields, dummy_model, dummy_data, dummy_col):
    u"""
    Filter the questions and answers to add play buttons.
    """

    def add_button(sound):
        u"""
        Add a button after the match.

        Add a button after the match to replay the audio. The title is
        set to "Replay" on the question side to hide information or to
        the file name on the answer.
        """
        if 'q' == qa_type:
            title = u"Replay"
        else:
            title = sound.group(1)
        return u"""{orig}<a href='javascript:py.link("ankiplay{fn}");' \
title="{ttl}" class="replaybutton browserhide"><span><svg viewBox="0 0 32 32">\
<polygon points="11,25 25,16 11,7"/>Replay</svg></span></a>\
<span style="display: none;">&#91;sound:{fn}&#93;</span>""".format(
            orig=sound.group(0), fn=sound.group(1), ttl=title)
        # The &#91; &#93; are the square brackets that we want to
        # appear as brackets and not trigger the playing of the
        # sound. The span inside the a around the svg is there to
        # bring this closer in line with AnkiDroid.
    return re.sub(r"\[sound:(.*?)\]", add_button, qa_html)

addHook("mungeQA", play_button_filter)




# thsi part wraps around anki.card.css
def svg_css(Card):
    return """<style scoped>
.replaybutton span {
  display: inline-block;
  vertical-align: middle;
  padding: 5px;
}

.replaybutton span svg {
  stroke: none;
  fill: black;
  display: inline;
  height: 1em;
  width: 1em;
  min-width: 12px;
  min-height: 12px;
}
</style>""" + old_css(Card)

old_css = Card.css
Card.css = svg_css

