# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


from aqt.qt import *
from PyQt4 import QtCore, QtGui

from ccbc.utils import *


p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","unordered_list.png")))
ICO_UNORDERED_LIST=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","ordered_list.png")))
ICO_ORDERED_LIST=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","indent.png")))
ICO_INDENT=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","outdent.png")))
ICO_OUTDENT=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","text_align_flush_left.png")))
ICO_JUSTIFY_LEFT=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","text_align_centered.png")))
ICO_JUSTIFY_CENTER=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","text_align_flush_right.png")))
ICO_JUSTIFY_RIGHT=QIcon(p)

p=QPixmap()
p.loadFromData(readBinary(os.path.join("images","text_align_justified.png")))
ICO_JUSTIFY_FULL=QIcon(p)
