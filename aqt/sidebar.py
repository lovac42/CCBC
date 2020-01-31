# -*- coding: utf-8 -*-
# Copyright 2019-2020 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import re
import anki.find
import aqt
from anki.lang import ngettext, _
from aqt.qt import *
from aqt.utils import getOnlyText, askUser, showWarning, showInfo
from anki.utils import intTime, ids2str
from anki.errors import DeckRenameError, AnkiError
from anki.hooks import runHook, addHook
from typing import Callable, List, Dict, Optional
from anki.lang import _


class SidebarItem:
    def __init__(self,
                 name: str,
                 icon: str,
                 onClick: Callable[[], None] = None,
                 onExpanded: Callable[[bool], None] = None,
                 expanded: bool = False) -> None:
        self.name = name
        self.icon = icon
        self.onClick = onClick
        self.onExpanded = onExpanded
        self.expanded = expanded
        self.children: List["SidebarItem"] = []
        self.parentItem: Optional[SidebarItem] = None

        self.tooltip = None
        self.foreground = None
        self.background = None

    def addChild(self, cb: "SidebarItem") -> None:
        self.children.append(cb)
        cb.parentItem = self

    def rowForChild(self, child: "SidebarItem") -> Optional[int]:
        try:
            return self.children.index(child)
        except ValueError:
            return None



class SidebarModel(QAbstractItemModel):
    nightmode = False #TODO: RM later, for 2.1.15

    def __init__(self, root: SidebarItem) -> None:
        super().__init__()
        self.root = root
        self.iconCache: Dict[str, QIcon] = {}

    # Qt API
    ######################################################################

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return len(self.root.children)
        else:
            item: SidebarItem = parent.internalPointer()
            return len(item.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem: SidebarItem
        if not parent.isValid():
            parentItem = self.root
        else:
            parentItem = parent.internalPointer()

        item = parentItem.children[row]
        return self.createIndex(row, column, item)

    def parent(self, child: QModelIndex) -> QModelIndex: # type: ignore
        if not child.isValid():
            return QModelIndex()

        childItem: SidebarItem = child.internalPointer()
        parentItem = childItem.parentItem

        if parentItem is None or parentItem == self.root:
            return QModelIndex()

        row = parentItem.rowForChild(childItem)
        if row is None:
            return QModelIndex()

        return self.createIndex(row, 0, parentItem)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        item: SidebarItem = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.DecorationRole:
            return self.iconFromRef(item.icon)
        elif role == Qt.BackgroundRole:
            return item.background
        elif role == Qt.ForegroundRole:
            return item.foreground
        elif role == Qt.ToolTipRole:
            return item.tooltip
        else:
            return None

    # Helpers
    ######################################################################

    def iconFromRef(self, iconRef: str) -> QIcon:
        icon = self.iconCache.get(iconRef)
        if icon is None:
            icon = QIcon(iconRef)
            self.iconCache[iconRef] = icon
        return icon

    def expandWhereNeccessary(self, tree: QTreeView) -> None:
        for row, child in enumerate(self.root.children):
            if child.expanded:
                idx = self.index(row, 0, QModelIndex())
                self._expandWhereNeccessary(idx, tree)

    def _expandWhereNeccessary(self, parent: QModelIndex, tree: QTreeView) -> None:
        parentItem: SidebarItem
        if not parent.isValid():
            parentItem = self.root
        else:
            parentItem = parent.internalPointer()

        # nothing to do?
        if not parentItem.expanded:
            return

        # expand children
        for row, child in enumerate(parentItem.children):
            if not child.expanded:
                continue
            childIdx = self.index(row, 0, parent)
            self._expandWhereNeccessary(childIdx, tree)

        # then ourselves
        tree.setExpanded(parent, True)


    # Drag and drop support
    ######################################################################

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.MoveAction | Qt.CopyAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.isValid():
            f |= Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return f






class SidebarTreeView(QTreeView):
    node_state = { # True for open, False for closed
        #Decks are handled per deck settings
        'group': {}, 'tag': {}, 'fav': {}, 'pinDeck': {}, 'pinDyn': {},
        'model': {}, 'dyn': {}, 'pinTag': {}, 'pin': {},
        'deck': None, 'Deck': None,
    }

    finder = {} # saved gui options

    marked = {
        'group': {}, 'tag': {}, 'fav': {}, 'pinDeck': {}, 'pinDyn': {},
        'model': {}, 'dyn': {}, 'deck': {}, 'pinTag': {}, 'pin': {},
    }

    def __init__(self, mw, browser):
        super().__init__()
        self.expanded.connect(self.onExpansion)
        self.collapsed.connect(self.onCollapse)

        self.found = {}
        self.mw = mw
        self.col = mw.col
        self.browser = browser
        self.timer = None

        addHook('profileLoaded', self.clear)

        self.mw.col.tags.registerNotes() # clearn unused tags to prevent lockup

    def clear(self):
        self.finder.clear()
        for k in self.node_state:
            try:
                self.node_state[k].clear()
            except AttributeError:
                pass
        for k in self.marked:
            try:
                self.marked[k].clear()
            except AttributeError:
                pass

    def onClickCurrent(self) -> None:
        idx = self.currentIndex()
        if idx.isValid():
            item: SidebarItem = idx.internalPointer()
            if item.onClick:
                item.onClick()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.onClickCurrent()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.onClickCurrent()
        else:
            super().keyPressEvent(event)

    def onExpansion(self, idx):
        self._onExpansionChange(idx, True)

    def onCollapse(self, idx):
        self._onExpansionChange(idx, False)

    def _onExpansionChange(self, idx, expanded):
        item = idx.internalPointer()
        try:
            self.node_state[item.type][item.fullname] = expanded
        except TypeError:
            pass
        except (AttributeError,KeyError):
            return # addon: Customize Sidebar, favTree errors

    def refresh(self):
        self.found = {}
        mw.col.tags.registerNotes() #calls "newTag" hook which invokes maybeRefreshSidebar
        #Clear to create a smooth UX
        self.marked['group'] = {}
        self.marked['pinDeck'] = {}
        self.marked['pinDyn'] = {}
        self.marked['pinTag'] = {}








class TagTreeWidget(QTreeWidget):
    def __init__(self, browser, parent):
        QTreeWidget.__init__(self, parent)
        self.setHeaderHidden(True)
        self.browser = browser
        self.col = browser.col
        self.node = {}
        self.addMode = False
        self.color = Qt.red

        self.itemClicked.connect(self.onClick)
        self.itemExpanded.connect(self.onCollapse)
        self.itemCollapsed.connect(self.onCollapse)

    def onClick(self, item, col):
        item.setSelected(False)
        if self.addMode or item.type=="tag":
            s = not self.node.get(item.fullname,False)
            self.node[item.fullname] = s
            color = self.color if s else Qt.transparent
            item.setBackground(0, QBrush(color))

    def onCollapse(self, item):
        try:
            s = self.node.get(item.fullname,False)
            color = self.color if s else Qt.transparent
            item.setBackground(0, QBrush(color))
        except AttributeError: pass

    def removeTags(self, nids):
        self.addMode = False
        self.color = Qt.red
        SORT = self.col.conf.get('Blitzkrieg.sort_tag',False)
        tags = self.col.db.list("""
select tags from notes where id in %s""" % ids2str(nids))
        tags = sorted(" ".join(tags).split(),
            key=lambda t: t.lower() if SORT else t)
        self._setTags(set(tags))

    def addTags(self, nids):
        self.addMode = True
        self.color = Qt.green
        SORT = self.col.conf.get('Blitzkrieg.sort_tag',False)
        allTags = sorted(self.col.tags.all(),
                key=lambda t: t.lower() if SORT else t)
        tags = self.col.db.list("""
select tags from notes where id in %s""" % ids2str(nids))
        tags = set(" ".join(tags).split())
        self._setTags(allTags,tags)

    def _setTags(self, allTags, curTags=""):
        tags_tree = {}
        for t in allTags:
            if self.addMode and t.lower() in ("marked","leech"):
                continue
            item = None
            node = t.split('::')
            for idx, name in enumerate(node):
                leaf_tag = '::'.join(node[0:idx + 1])
                if not tags_tree.get(leaf_tag):
                    parent = tags_tree['::'.join(node[0:idx])] if idx else self
                    item = QTreeWidgetItem(parent,[name])
                    item.fullname = leaf_tag
                    item.setExpanded(True)
                    tags_tree[leaf_tag] = item
                    if leaf_tag in curTags:
                        item.setBackground(0, QBrush(Qt.yellow))
            try:
                item.type = "tag"
                item.setIcon(0, QIcon(":/icons/anki-tag.png"))
            except AttributeError: pass
