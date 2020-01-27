# -*- coding: utf-8 -*-
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""\
Hooks - hook management and tools for extending Anki
==============================================================================

To find available hooks, grep for runHook and runFilter in the source code.

Instrumenting allows you to modify functions that don't have hooks available.
If you call wrap() with pos='around', the original function will not be called
automatically but can be called with _old().
"""

import decorator

# Hooks
##############################################################################

_hooks = {}

# Note:
#   This class prevents resize only, it does not prevent the list
#   from being mutilated by calls to remHook in the loop.
class Hooker:
    def __init__(self):
        self.level=0
        self.nulCnt=0
        self.tasks=[]

    def length(self):
        return len(self.tasks)

    def append(self, func):
        self.tasks.append(func)

    def remove(self, func):
        if not func:
            return
        try:
            i = self.tasks.index(func)
            self.tasks[i] = None
            self.nulCnt += 1
        except ValueError:
            pass

    def purge(self):
        if self.level<=0 and self.nulCnt>2:
            self.tasks=list(filter(None,self.tasks))
            self.level = self.nulCnt = 0

def runHook(hook, *args):
    "Run all functions on hook."
    hookers = _hooks.get(hook, None)
    if hookers:
        hookers.level += 1
        tsk=hookers.tasks
        for i in range(hookers.length()):
            func=tsk[i]
            try:
                if func:
                    func(*args)
            except:
                hookers.remove(func)
                hookers.level -= 1
                raise
        hookers.level -= 1
        hookers.purge()

def runFilter(hook, arg, *args):
    hookers = _hooks.get(hook, None)
    if hookers:
        hookers.level += 1
        tsk=hookers.tasks
        for i in range(hookers.length()):
            func=tsk[i]
            try:
                if func:
                    arg = func(arg, *args)
            except:
                hookers.remove(func)
                hookers.level -= 1
                raise
        hookers.level -= 1
        hookers.purge()
    return arg

def addHook(hook, func):
    "Add a function to hook. Ignore if already on hook."
    if not _hooks.get(hook, None):
        _hooks[hook] = Hooker()
    if func not in _hooks[hook].tasks:
        _hooks[hook].append(func)

def remHook(hook, func):
    "Remove a function if is on hook."
    hookers = _hooks.get(hook, None)
    if hookers:
        hookers.remove(func)

# Instrumenting
##############################################################################

def wrap(old, new, pos="after"):
    "Override an existing function."
    def repl(*args, **kwargs):
        if pos == "after":
            old(*args, **kwargs)
            return new(*args, **kwargs)
        elif pos == "before":
            new(*args, **kwargs)
            return old(*args, **kwargs)
        else:
            return new(_old=old, *args, **kwargs)

    def decorator_wrapper(f, *args, **kwargs):
        return repl(*args, **kwargs)

    return decorator.decorator(decorator_wrapper)(old)
