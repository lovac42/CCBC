# -*- coding: utf-8 -*-
# Copyright 2019-2021 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from anki.find import Finder


class ExtFinder(Finder):

    #Addon: rated0Search
    def _findRated(self, args):
        # days(:optional_ease)
        (val, args) = args
        r = val.split(":")
        try:
            days = int(r[0])
        except ValueError:
            return
        days = min(days, 365)
        # ease
        ease = ""
        if len(r) > 1:
            if r[1] not in ("0", "1", "2", "3", "4"):
                return
            ease = "and ease=%s" % r[1]
        cutoff = (self.col.sched.dayCutoff - 86400*days)*1000
        return ("c.id in (select cid from revlog where id>%d %s)" %
                (cutoff, ease))

