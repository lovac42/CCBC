#https://github.com/ijgnd/anki__reviewer_deck_and_card_info_sidebar/blob/master/src/deck_and_card_info_during_review/helper_functions.py

import time

from aqt import mw
from anki.utils import fmtTimeSpan


def due_day(card):
    if card.type in (0,1):
        return "(New)"
    mydue = card.odue if card.odid else card.due
    if card.type in (2,3) and mydue<100000: #lrn burried cards
        mydue = time.time()+((mydue-mw.col.sched.today)*86400)
    if mydue<0:
        return "Error"
    return time.strftime("%Y-%m-%d", time.localtime(mydue))


#function time from anki/stats.py
def stattime(tm):
    str = ""
    if tm >= 60:
        str = fmtTimeSpan((tm/60)*60, short=True, point=-1, unit=1)
    if tm%60 != 0 or not str:
        str += fmtTimeSpan(tm%60, point=2 if not str else -1, short=True)
    return str


def is_early_review_then_return_percentage_interval(card):
    due = card.odue if card.odid else card.due
    # print('///////////////')
    # print(due)
    if not due > mw.col.sched.today:
        # print('a1')
        return False
    else:
        if card.queue == 1:  #learn
            # print('a2')
            return False
        elif card.queue == 0 and card.type == 0:   #new
            # print('a3')
            return False
        else:
            try:
                lastRev = due - card.ivl
                elapsed = mw.col.sched.today - lastRev
                p = elapsed/float(card.ivl) * 100
                pf = "{0:.2f}".format(p) + " %"
                return pf
            except ZeroDivisionError:
                return False
