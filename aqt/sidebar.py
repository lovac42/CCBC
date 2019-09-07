# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# Copyright 2006-2019 Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/CCBC


import anki.find
from anki.lang import ngettext, _
from aqt.qt import *
from aqt.utils import getOnlyText, askUser, showWarning
from anki.errors import DeckRenameError


class SidebarTreeWidget(QTreeWidget):
    def __init__(self, parent):
        QTreeWidget.__init__(self, parent)
        self.dropItem = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        self.itemClicked.connect(self.onTreeClick)
        self.itemExpanded.connect(self.onTreeCollapse)
        self.itemCollapsed.connect(self.onTreeCollapse)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onTreeMenu)

    def keyPressEvent(self, evt):
        if evt.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.currentItem()
            self.onTreeClick(item, 0)
        else:
            super().keyPressEvent(evt)

    def onTreeClick(self, item, col):
        if getattr(item, 'onclick', None):
            item.onclick()

    def onTreeCollapse(self, item):
        if getattr(item, 'oncollapse', None):
            item.oncollapse()

    def dropMimeData(self, parent, row, data, action):
        # Dealing with qt serialized data is a headache,
        # so I'm just going to save a reference to the dropped item.
        # data.data('application/x-qabstractitemmodeldatalist')
        self.dropItem = parent
        return True


    def dropEvent(self, event):
        dragItem = event.source().currentItem()
        if dragItem.type not in ("tag","deck"):
            event.setDropAction(Qt.IgnoreAction)
            event.accept()
            return

        QAbstractItemView.dropEvent(self, event)
        if not self.dropItem or self.dropItem.type == dragItem.type:
            dragName = dragItem.fullname
            try:
                dropName = self.dropItem.fullname
            except AttributeError:
                dropName = None

            self.mw.checkpoint("Dragged "+dragItem.type)
            parse=self.col.decks #used for parsing '::' separators

            if dragItem.type == "deck":
                dragDid = parse.byName(dragName)["id"]
                dropDid = parse.byName(dropName)["id"] if dropName else None
                try:
                    parse.renameForDragAndDrop(dragDid,dropDid)
                except DeckRenameError as e:
                    showWarning(e.description)

            elif dragItem.type == "tag":
                if dragName and not dropName:
                    if len(parse._path(dragName)) > 1:
                        self.moveTag(dragName, parse._basename(dragName))
                elif parse._canDragAndDrop(dragName, dropName):
                    assert dropName.strip()
                    self.moveTag(dragName, dropName + "::" + parse._basename(dragName))
                self.col.tags.registerNotes()
        self.browser.buildTree()


    def moveTag(self, dragName, newName="", rename=True):
        "Rename or Delete tag"
        self.browser.editor.saveNow()
        self.browser.editor.setNote(None)
        self.browser.singleCard=False
        f = anki.find.Finder(self.col)
        # rename children
        for tag in self.col.tags.all():
            if tag.startswith(dragName + "::"):
                ids = f.findNotes("tag:"+tag)
                if rename:
                    nn = tag.replace(dragName+"::", newName+"::", 1)
                    self.col.tags.bulkAdd(ids,nn)
                self.col.tags.bulkRem(ids,tag)
        # rename parent
        ids = f.findNotes("tag:"+dragName)
        if rename:
            self.col.tags.bulkAdd(ids,newName)
        self.col.tags.bulkRem(ids,dragName)
        self.col.tags.flush()


    def _onTreeItemAction(self, item, action):
        self.browser.editor.saveNow()
        self.browser.editor.setNote(None)
        self.browser.singleCard=False
        self.mw.checkpoint(action+" "+item.type)

        if item.type == "deck":
            did=self.col.decks.byName(item.fullname)["id"]
            if action=="Add":
                deck = getOnlyText(_("Name for deck:"),default=item.fullname+"::")
                if deck:
                    self.col.decks.id(deck)
            elif action=="Delete":
                self.mw.deckBrowser._delete(did)
            else:
                self.mw.deckBrowser._rename(did)
            self.mw.reset(True)


        elif item.type == "tag":
            if action=="RenameL":
                oldNameArr = item.fullname.split("::")
                newName = getOnlyText(_("New tag name:"),default=oldNameArr[-1])
                newName = newName.replace('"', "")
                if not newName or newName == oldNameArr[-1]:
                    return
                oldNameArr[-1] = newName
                newName = "::".join(oldNameArr)
            elif action=="RenameB":
                newName = getOnlyText(_("New tag name:"),default=item.fullname)
                newName = newName.replace('"', "")
                if not newName or newName == item.fullname:
                    return

            if action.startswith("Rename"):
                self.moveTag(item.fullname,newName)
            else:
                self.moveTag(item.fullname,rename=False)
            self.col.tags.registerNotes()


        elif item.type == "fav":
            if action=="Delete":
                el=self.browser.form.searchEdit.lineEdit()
                el.deleteClicked()
            else: #rename
                newName = getOnlyText(_("New search name:"),default=item.fullname)
                act=self.col.conf['savedFilters'][item.fullname]
                self.col.conf['savedFilters'][newName]=act
                del(self.col.conf['savedFilters'][item.fullname])
                self.col.setMod()


        elif item.type == "model":
            self.browser.form.searchEdit.lineEdit().setText("")
            model = self.col.models.byName(item.fullname)
            if action=="Delete":
                if self.col.models.useCount(model):
                    msg = _("Delete this note type and all its cards?")
                else:
                    msg = _("Delete this unused note type?")
                if not askUser(msg, parent=self):
                    return
                self.col.models.rem(model)
                model = None
                self.col.models.flush()
                self.browser.setupTable()
            else: #rename
                newName = getOnlyText(_("New model name:"),default=item.fullname)
                model['name'] = newName
                self.col.models.save(model)
                self.col.models.flush()
            self.browser.model.reset()

        self.col.setMod()
        self.browser.buildTree()


    def onTreeMenu(self, pos):
        item=self.currentItem()
        if not item:
            return
        if item.type in ("tag","deck","fav","model"):
            m = QMenu(self)
            if item.type == "deck":            
                act = m.addAction("Add")
                act.triggered.connect(lambda:self._onTreeItemAction(item,"Add"))
            if item.type == "tag":
                act = m.addAction("Rename Leaf")
                act.triggered.connect(lambda:self._onTreeItemAction(item,"RenameL"))
                act = m.addAction("Rename Branch")
                act.triggered.connect(lambda:self._onTreeItemAction(item,"RenameB"))
            else:
                act = m.addAction("Rename")
                act.triggered.connect(lambda:self._onTreeItemAction(item,"Rename"))
            act = m.addAction("Delete")
            act.triggered.connect(lambda:self._onTreeItemAction(item,"Delete"))
            m.popup(QCursor.pos())
