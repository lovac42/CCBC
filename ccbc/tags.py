# -*- coding: utf-8 -*-
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


import re
from anki.tags import TagManager


class ExtTagManager(TagManager):


    # String-based utilities
    ##########################################################################

    # TODO: Redo with dialog and preview for affected tags.

    def remFromStr(self, deltags, tags):
        "Delete tags if they exist."
        def wildcard(pat, str):
            pat = re.escape(pat).replace('\\*', '.*')
            # return re.match("^"+pat+"$", str, re.IGNORECASE)

            #FROM: Using regexps to remove tags
            #https://ankiweb.net/shared/info/1502698883
            return re.search(pat, str, re.IGNORECASE)

        currentTags = self.split(tags)
        for tag in self.split(deltags):
            # find tags, ignoring case
            remove = []
            for tx in currentTags:
                if (tag.lower() == tx.lower()) or wildcard(tag, tx):
                    remove.append(tx)
            # remove them
            for r in remove:
                currentTags.remove(r)
        return self.join(currentTags)

