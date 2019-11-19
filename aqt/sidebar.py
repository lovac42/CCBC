# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
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
from anki.hooks import runHook


class SidebarTreeWidget(QTreeWidget):
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


    def __init__(self, parent):
        QTreeWidget.__init__(self, parent)
        self.found = {}
        self.browser = None
        self.timer = None
        self.dropItem = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        self.itemClicked.connect(self.onTreeClick)
        self.itemExpanded.connect(self.onTreeCollapse)
        self.itemCollapsed.connect(self.onTreeCollapse)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onTreeMenu)
        self.setupContextMenuItems()


    def setupContextMenuItems(self):
              # Type, Item Title, Action Name, Callback
              # type -1: separator
              # type 0: normal
              # type 1: non-folder path, actual item
        self.MENU_ITEMS = {
            "pin":((-1,),),
            "pinDyn":(
                (1,"Empty","Empty",self._onTreeDeckEmpty),
                (1,"Rebuild","Rebuild",self._onTreeDeckRebuild),
                (1,"Options","Options",self._onTreeDeckOptions),
                (1,"Export","Export",self._onTreeDeckExport),
                (-1,),
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Unpin",None,self._onTreePinDelete),
            ),
            "pinDeck":(
                (1,"Add Notes",None,self._onTreeDeckAddCard),
                (1,"Options","Options",self._onTreeDeckOptions),
                (1,"Export","Export",self._onTreeDeckExport),
                (-1,),
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Unpin",None,self._onTreePinDelete),
            ),
            "pinTag":(
                (1,"Show All",None,self._onTreeTagSelectAll),
                (1,"Add Notes",None,self._onTreeTagAddCard),
                # (0,"Tag Selected","Tag",self._onTreeTag),
                # (1,"Untag Selected","Untag",self._onTreeUnTag),
                (-1,),
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Unpin",None,self._onTreePinDelete),
            ),
            "tag":(
                (0,"Show All",None,self._onTreeTagSelectAll),
                (0,"Add Notes",None,self._onTreeTagAddCard),
                (0,"Rename Leaf","Rename",self._onTreeTagRenameLeaf),
                (0,"Rename Branch","Rename",self._onTreeTagRenameBranch),
                # (0,"Tag Selected","Tag",self._onTreeTag),
                # (0,"Untag Selected","Untag",self._onTreeUnTag),
                (0,"Delete","Delete",self._onTreeTagDelete),
                (-1,),
                (0,"Convert to decks","Convert",self._onTreeTag2Deck),
            ),
            "deck":(
                (0,"Rename Leaf","Rename",self._onTreeDeckRenameLeaf),
                (0,"Rename Branch","Rename",self._onTreeDeckRename),
                (0,"Add Notes",None,self._onTreeDeckAddCard),
                (0,"Add Subdeck","Add",self._onTreeDeckAdd),
                (0,"Options","Options",self._onTreeDeckOptions),
                (0,"Export","Export",self._onTreeDeckExport),
                (0,"Delete","Delete",self._onTreeDeckDelete),
                (-1,),
                (0,"Convert to tags","Convert",self._onTreeDeck2Tag),
            ),
            "dyn":(
                (0,"Rename Leaf","Rename",self._onTreeDeckRenameLeaf),
                (0,"Rename Branch","Rename",self._onTreeDeckRename),
                (0,"Empty","Empty",self._onTreeDeckEmpty),
                (0,"Rebuild","Rebuild",self._onTreeDeckRebuild),
                (0,"Options","Options",self._onTreeDeckOptions),
                (0,"Export","Export",self._onTreeDeckExport),
                (0,"Delete","Delete",self._onTreeDeckDelete),
            ),
            "fav":(
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Modify","Modify",self._onTreeFavModify),
                (1,"Delete","Delete",self._onTreeFavDelete),
            ),
            "model":(
                (0,"Rename Leaf","Rename",self._onTreeModelRenameLeaf),
                (0,"Rename Branch","Rename",self._onTreeModelRenameBranch),
                (0,"Add Model","Add",self._onTreeModelAdd),
                (1,"Edit Fields","Edit",self.onTreeModelFields),
                (1,"LaTeX Options","Edit",self.onTreeModelOptions),
                (1,"Delete","Delete",self._onTreeModelDelete),
            ),
        }


    def keyPressEvent(self, evt):
        if evt.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.currentItem()
            self.onTreeClick(item, 0)
        elif evt.key() in (Qt.Key_Down, Qt.Key_Up):
            super().keyPressEvent(evt)
            item = self.currentItem()
            self.onTreeClick(item, 0)
        else:
            super().keyPressEvent(evt)

    def onTreeClick(self, item, col):
        #In Qt5, right click does not trigger this method.
        if getattr(item, 'onclick', None):
            item.onclick()
            if item.type=='tag' and \
            self.col.conf.get('Blitzkrieg.showAllTags', False):
                self._onTreeTagSelectAll(item)
            else:
                item.onclick()
            self.timer=self.mw.progress.timer(
                20, lambda:self._changeDecks(item), False)

    def onTreeCollapse(self, item):
        """Decks do not call this method"""
        if getattr(item, 'oncollapse', None):
            item.oncollapse() #decks only
            return
        if not isinstance(item.type, str):
            return
        exp = item.isExpanded()
        self.node_state[item.type][item.fullname] = exp
        #highlight parent decks
        if item.type == 'tag' and item.childCount() \
        and not self.marked['tag'].get(item.fullname) \
        and '::' not in item.fullname:
            color = QColor(0,0,10,10) if exp else Qt.transparent
            item.setBackground(0, QBrush(color))

    def dropMimeData(self, parent, row, data, action):
        # Dealing with qt serialized data is a headache,
        # so I'm just going to save a reference to the dropped item.
        # data.data('application/x-qabstractitemmodeldatalist')
        if parent and isinstance(parent.type, str):
            #clear item to allow dropping to groups
            self.dropItem = parent if parent.type!='group' else None
        return True


    def dropEvent(self, event):
        dragItem = event.source().currentItem()
        if not isinstance(dragItem.type, str):
            return
        dgType = dragItem.type
        if dgType not in self.node_state:
            event.setDropAction(Qt.IgnoreAction)
            event.accept()
            return
        QAbstractItemView.dropEvent(self, event)
        if not self.dropItem or \
        self.dropItem.type == dgType or \
        self.dropItem.type == dgType[:3]: #pin
            self.mw.checkpoint("Dragged "+dgType)
            dragName,dropName = self._getItemNames(dragItem)
            parse = self.col.decks #used for parsing '::' separators
            cb = None
            if dgType in ("deck", "dyn"):
                self._deckDropEvent(dragName,dropName)
            elif dgType == "tag":
                cb = self.moveTag
            elif dgType == "model":
                cb = self.moveModel
            elif dgType[:3] in ("fav","pin"):
                cb = self.moveFav
            if cb:
                self._strDropEvent(dragName,dropName,cb)
                self.node_state[dgType][dropName] = True
        self.col.setMod()
        self.browser.buildTree()

    def _strDropEvent(self, dragName, dropName, callback):
        parse=self.col.decks #used for parsing '::' separators
        if dragName and not dropName:
            if len(parse._path(dragName)) > 1:
                callback(dragName, parse._basename(dragName))
        elif parse._canDragAndDrop(dragName, dropName):
            assert dropName.strip()
            callback(dragName, dropName + "::" + parse._basename(dragName))

    def _deckDropEvent(self, dragName, dropName):
        parse=self.col.decks #used for parsing '::' separators
        dragDeck = parse.byName(dragName)
        dragDid = dragDeck["id"]
        dropDid = parse.byName(dropName)["id"] if dropName else None
        try:
            parse.renameForDragAndDrop(dragDid,dropDid)
        except DeckRenameError as e:
            showWarning(e.description)
        self.col.decks.get(dropDid)['browserCollapsed'] = False
        # Adding HL here gets really annoying
        # self.highlight('deck',dragDeck['name'])

    def moveFav(self, dragName, newName=""):
        try:
            type = self.dropItem.type
        except AttributeError:
            type = "fav"
        saved = self.col.conf['savedFilters']
        for fav in list(saved):
            act = self.col.conf['savedFilters'].get(fav)
            if fav.startswith(dragName + "::"):
                nn = fav.replace(dragName+"::", newName+"::", 1)
                self.col.conf['savedFilters'][nn] = act
                del(self.col.conf['savedFilters'][fav])
                self.node_state[type][nn] = True
            elif fav == dragName:
                self.col.conf['savedFilters'][newName] = act
                del(self.col.conf['savedFilters'][dragName])
                self.node_state[type][newName] = True

    def moveModel(self, dragName, newName=""):
        "Rename or Delete models"
        self.browser.editor.saveNow()
        self.browser.editor.setNote(None)
        self.browser.singleCard=False
        self.browser.teardownHooks() #RuntimeError: CallbackItem has been deleted
        for m in self.col.models.all():
            modelName=m['name']
            if modelName.startswith(dragName + "::"):
                m['name'] = modelName.replace(dragName+"::", newName+"::", 1)
                self.col.models.save(m)
            elif modelName == dragName:
                m['name'] = newName
                self.col.models.save(m)
            self.node_state['model'][newName] = True
        self.col.models.flush()
        self.browser.model.reset()
        self.browser.setupHooks()


    def moveTag(self, dragName, newName="", rename=True):
        "Rename or Delete tag"
        self.browser.editor.saveNow()
        self.browser.editor.setNote(None)
        self.browser.singleCard=False
        self.browser.teardownHooks() #RuntimeError: CallbackItem has been deleted
        f = anki.find.Finder(self.col)
        # rename children
        for tag in self.col.tags.all():
            if tag.startswith(dragName + "::"):
                ids = f.findNotes('"tag:%s"'%tag)
                if rename:
                    nn = tag.replace(dragName+"::", newName+"::", 1)
                    self.col.tags.bulkAdd(ids,nn)
                    self.node_state['tag'][nn] = True
                self.col.tags.bulkRem(ids,tag)
        # rename parent
        ids = f.findNotes('"tag:%s"'%dragName)
        if rename:
            self.col.tags.bulkAdd(ids,newName)
            self.node_state['tag'][newName] = True
        self.col.tags.bulkRem(ids,dragName)
        self.col.tags.save()
        self.col.tags.flush()
        self.col.tags.registerNotes()
        self.browser.setupHooks()


    def onTreeMenu(self, pos):
        try: #isRightClick, stop timer
            self.timer.stop()
        except: pass

        item=self.currentItem()
        if not item or not isinstance(item.type, str):
            return

        m = QMenu(self)
        if item.type == "sys":
            pass #skip

        elif self.mw.app.keyboardModifiers()==Qt.ShiftModifier:
            if item.type != "group":
                act = m.addAction("Mark/Unmark item (tmp)")
                act.triggered.connect(lambda:self._onTreeMark(item))
                if item.type in ("deck","tag"):
                    act = m.addAction("Pin Item")
                    act.triggered.connect(lambda:self._onTreePin(item))
                if item.type in ("pin","fav"):
                    ico = self.col.conf.get('Blitzkrieg.icon_fav', True)
                    act = m.addAction("Show icon for paths")
                    act.setCheckable(True)
                    act.setChecked(ico)
                    act.triggered.connect(lambda:self._toggleIconOption(item))

            act = m.addAction("Refresh")
            act.triggered.connect(self.refresh)
            if item.type == "group":
                if item.fullname in ("tag","deck","model"):
                    sort = self.col.conf.get('Blitzkrieg.sort_'+item.fullname, False)
                    act = m.addAction("Sort by A-a-B-b")
                    act.setCheckable(True)
                    act.setChecked(sort)
                    act.triggered.connect(lambda:self._toggleSortOption(item))
                if item.fullname in ("tag","model"):
                    ico = self.col.conf.get('Blitzkrieg.icon_'+item.fullname, True)
                    act = m.addAction("Show icon for paths")
                    act.setCheckable(True)
                    act.setChecked(ico)
                    act.triggered.connect(lambda:self._toggleIconOption(item))
                if item.fullname == "deck":
                    up = self.col.conf.get('Blitzkrieg.updateOV', False)
                    act = m.addAction("Auto Update Overview")
                    act.setCheckable(True)
                    act.setChecked(up)
                    act.triggered.connect(self._toggleMWUpdate)
                elif item.fullname == "tag":
                    sa = self.col.conf.get('Blitzkrieg.showAllTags', False)
                    act = m.addAction("Auto Show Subtags")
                    act.setCheckable(True)
                    act.setChecked(sa)
                    act.triggered.connect(self._toggleShowSubtags)

            if item.childCount():
                m.addSeparator()
                act = m.addAction("Collapse All")
                act.triggered.connect(lambda:self._expandAllChildren(item))
                act = m.addAction("Expand All")
                act.triggered.connect(lambda:self._expandAllChildren(item,True))

        elif item.type == "group":
            if item.fullname == "tag":
                act = m.addAction("Refresh")
                act.triggered.connect(self.refresh)
            elif item.fullname == "deck":
                act = m.addAction("Add Deck")
                act.triggered.connect(lambda:
                    self._onTreeItemAction(item,"Add",self._onTreeDeckAdd))
                act = m.addAction("Empty All Filters")
                act.triggered.connect(self.onEmptyAll)
                act = m.addAction("Rebuild All Filters")
                act.triggered.connect(self.onRebuildAll)
            elif item.fullname == "model":
                act = m.addAction("Manage Model")
                act.triggered.connect(self.onManageModel)

            m.addSeparator()
            act = m.addAction("Find...")
            act.triggered.connect(lambda:self.findRecursive(item))
            act = m.addAction("Collapse All")
            act.triggered.connect(lambda:self._expandAllChildren(item))
            act = m.addAction("Expand All")
            act.triggered.connect(lambda:self._expandAllChildren(item,True))

        else:
            for itm in self.MENU_ITEMS[item.type]:
                if itm[0] < 0:
                    m.addSeparator()
                elif not itm[0] or self.hasValue(item):
                    act = m.addAction(itm[1])
                    act.triggered.connect(
                        lambda b, item=item, itm=itm:
                            self._onTreeItemAction(item,itm[2],itm[3])
                    )

        runHook("Blitzkrieg.treeMenu", self, item, m)
        m.popup(QCursor.pos())


    def _onTreeItemAction(self, item, action, callback):
        self.browser.editor.saveNow()
        self.browser.editor.setNote(None)
        self.browser.singleCard=False
        if action:
            self.mw.checkpoint(action+" "+item.type)
        self.browser.teardownHooks() #RuntimeError: CallbackItem has been deleted
        try:
            callback(item)
        finally:
            self.col.setMod()
            self.browser.setupHooks()
            self.browser.onReset()
            self.browser.buildTree()


    def _onTreeDeckEmpty(self, item):
        sel = self.col.decks.byName(item.fullname)
        self.col.sched.emptyDyn(sel['id'])
        self.mw.reset()

    def _onTreeDeckRebuild(self, item):
        sel = self.col.decks.byName(item.fullname)
        self.col.sched.rebuildDyn(sel['id'])
        self.mw.reset()

    def _onTreeDeckOptions(self, item):
        deck = self.col.decks.byName(item.fullname)
        try: #new versions
            if deck['dyn']:
                import aqt.dyndeckconf
                aqt.dyndeckconf.DeckConf(self.mw, deck=deck, parent=self.browser)
            else:
                import aqt.deckconf
                aqt.deckconf.DeckConf(self.mw, deck, self.browser)
        except TypeError: #old versions
            self.mw.onDeckConf(deck)
        self.mw.reset(True)

    def _onTreeDeckExport(self, item):
        deck = self.col.decks.byName(item.fullname)
        try: #new versions
            import aqt.exporting
            aqt.exporting.ExportDialog(self.mw, deck['id'], self.browser)
        except TypeError: #old versions
            self.mw.onExport(did=deck['id'])
        self.mw.reset(True)

    def _onTreeDeckAdd(self, item=None):
        default=item.fullname+"::" if item and item.type=='deck' else ''
        deck = getOnlyText(_("Name for deck:"),default=default)
        if deck:
            self.col.decks.id(deck)
            self.col.decks.save()
            self.col.decks.flush()
            self.mw.reset(True)

    def _onTreeDeckDelete(self, item):
        did = self.col.decks.byName(item.fullname)["id"]
        self.mw.deckBrowser._delete(did)
        self.col.decks.save()
        self.col.decks.flush()
        self.mw.reset(True)

    def _onTreeDeckRenameLeaf(self, item):
        self.mw.checkpoint(_("Rename Deck"))
        from aqt.utils import showWarning
        from anki.errors import DeckRenameError

        sel = self.col.decks.byName(item.fullname)
        try:
            path,leaf = item.fullname.rsplit('::',1)
            newName = path+'::'+ getOnlyText(_("New deck name:"), default=leaf)
        except ValueError:
            newName = getOnlyText(_("New deck name:"), default=item.fullname)
        newName = newName.replace('"', "")
        if not newName or newName == item.fullname:
            return

        deck = self.col.decks.get(sel["id"])
        try:
            self.col.decks.rename(deck, newName)
        except DeckRenameError as e:
            return showWarning(e.description)
        self.mw.show()
        self.mw.reset(True)

    def _onTreeDeckRename(self, item):
        sel = self.col.decks.byName(item.fullname)
        self.mw.deckBrowser._rename(sel["id"])
        if item.fullname != sel['name']:
            self.col.decks.save()
            self.col.decks.flush()
            self.highlight('deck',sel['name'])
            self.mw.reset(True)

    def _onTreeDeckAddCard(self, item):
        from aqt import addcards
        d = self.col.decks.byName(item.fullname)
        self.col.decks.select(d["id"])
        diag = aqt.dialogs.open("AddCards", self.mw)

    def _onTreeTagAddCard(self, item):
        from aqt import addcards
        diag = aqt.dialogs.open("AddCards", self.mw)
        diag.editor.tags.setText(item.fullname)

    def _onTreeTagSelectAll(self, item):
        item.onclick()
        el = self.browser.form.searchEdit.lineEdit()
        el.setText(el.text()+"*")
        self.browser.onSearch()

    def _onTreeTagRenameLeaf(self, item):
        oldNameArr = item.fullname.split("::")
        newName = getOnlyText(_("New tag name:"),default=oldNameArr[-1])
        newName = newName.replace('"', "")
        if not newName or newName == oldNameArr[-1]:
            return
        oldNameArr[-1] = newName
        newName = "::".join(oldNameArr)
        self.moveTag(item.fullname,newName)
        self.highlight('tag',newName)

    def _onTreeTagRenameBranch(self, item):
        newName = getOnlyText(_("New tag name:"),default=item.fullname)
        newName = newName.replace('"', "")
        if not newName or newName == item.fullname:
            return
        self.moveTag(item.fullname,newName)
        self.highlight('tag',newName)

    def _onTreeTagDelete(self, item):
        self.moveTag(item.fullname,rename=False)

    def _onTreeTag(self, item, add=True):
        sel = self.browser.selectedNotes()
        tag = item.fullname
        self.browser.model.beginReset()
        if add:
            mw.col.tags.bulkAdd(sel,tag)
        else:
            mw.col.tags.bulkRem(sel,tag)
        self.browser.model.endReset()
        mw.requireReset()

    def _onTreeUnTag(self, item):
        self._onTreeTag(item,False)

    def _onTreeDeck2Tag(self, item):
        msg = _("Convert all notes in deck/subdecks to tags?")
        if not askUser(msg, parent=self, defaultno=True):
            return

        self.mw.progress.start(
            label=_("Converting decks to tags"))
        try:
            f = anki.find.Finder(self.col)
            self.browser.form.searchEdit.lineEdit().setText("")
            parentDid = self.col.decks.byName(item.fullname)["id"]
            actv = self.col.decks.children(parentDid)
            actv = sorted(actv, key=lambda t: t[0])
            actv.insert(0,(item.fullname,parentDid))

            found = False
            for name,did in actv:
                self.mw.progress.update(label=name)
                #add subdeck tree structure as tags
                nids = f.findNotes('''"deck:%s" -"deck:%s::*"'''%(name,name))
                if nids:
                    found = True
                    tagName = re.sub(r"\s*(::)\s*","\g<1>",name)
                    tagName = re.sub(r"\s+","_",tagName)
                    self.col.tags.bulkAdd(nids, tagName)
                #skip parent or dyn decks
                if did == parentDid or self.col.decks.get(did)['dyn']:
                    continue
                #collapse subdecks into one
                self.col.sched.emptyDyn(None, "odid=%d"%did)
                self.col.db.execute(
                    "update cards set usn=?, mod=?, did=? where did=?",
                    self.col.usn(), intTime(), parentDid, did
                )
                self.col.decks.rem(did,childrenToo=False)
        finally:
            self.mw.progress.finish()
            if not found:
                showInfo("No Cards in deck")
                return
            self.col.decks.save()
            self.col.decks.flush()
            self.col.tags.save()
            self.col.tags.flush()
            self.highlight('tag',item.fullname)
            self.col.tags.registerNotes()
            self.mw.requireReset()

    def _onTreeTag2Deck(self, item):
        def tag2Deck(tag):
            did = self.col.decks.id(tag)
            cids = f.findCards('"tag:%s"'%tag)
            if not cids:
                return
            self.col.sched.remFromDyn(cids)
            self.col.db.execute(
                "update cards set usn=?, mod=?, did=? where id in %s"%ids2str(cids),
                self.col.usn(), intTime(), did
            )
            nids = f.findNotes('"tag:%s"'%tag)
            self.col.tags.bulkRem(nids,tag)

        msg = _("Convert all tags to deck structure?")
        if not askUser(msg, parent=self, defaultno=True):
            return

        self.mw.progress.start(
            label=_("Converting tags to decks"))
        try:
            f = anki.find.Finder(self.col)
            self.browser.form.searchEdit.lineEdit().setText("")
            parent = item.fullname
            tag2Deck(parent)
            for tag in self.col.tags.all():
                self.mw.progress.update(label=tag)
                if tag.startswith(parent + "::"):
                    tag2Deck(tag)
        finally:
            self.mw.progress.finish()
            self.col.decks.save()
            self.col.decks.flush()
            self.col.tags.save()
            self.col.tags.flush()
            self.highlight('deck',item.fullname)
            self.col.tags.registerNotes()
            self.mw.requireReset()

    def _onTreePinDelete(self, item):
        act=self.col.conf['savedFilters'].get(item.favname)
        if not act: return
        del self.col.conf['savedFilters'][item.favname]

    def _onTreeFavDelete(self, item):
        act=self.col.conf['savedFilters'].get(item.favname)
        if not act: return
        if askUser(_("Remove %s from your saved searches?") % item.favname):
            del self.col.conf['savedFilters'][item.favname]

    def _onTreeFavRename(self, item):
        act = self.col.conf['savedFilters'].get(item.favname)
        if not act: return
        s=item.favname
        p=False
        if item.type.startswith("pin"):
            s=re.sub(r"^Pinned::","",s)
            p=True
        newName = getOnlyText(_("New search name:"),default=s)
        newName = re.sub(r"^Pinned::","",newName)
        if newName:
            if p: newName="Pinned::"+newName
            del(self.col.conf['savedFilters'][item.favname])
            self.col.conf['savedFilters'][newName] = act

    def _onTreeFavModify(self, item):
        act = self.col.conf['savedFilters'].get(item.fullname)
        if not act: return
        act = getOnlyText(_("New Search:"), default=act)
        if act:
            self.col.conf['savedFilters'][item.fullname] = act

    def _onTreeModelRenameLeaf(self, item):
        self.browser.form.searchEdit.lineEdit().setText("")
        oldNameArr = item.fullname.split("::")
        newName = getOnlyText(_("New model name:"),default=oldNameArr[-1])
        newName = newName.replace('"', "")
        if not newName or newName == oldNameArr[-1]:
            return
        oldNameArr[-1] = newName
        newName = "::".join(oldNameArr)
        self.moveModel(item.fullname,newName)
        self.highlight('model',newName)

    def _onTreeModelRenameBranch(self, item):
        self.browser.form.searchEdit.lineEdit().setText("")
        model = self.col.models.byName(item.fullname)
        newName = getOnlyText(_("New model name:"),default=item.fullname)
        newName = newName.replace('"', "")
        if not newName or newName == item.fullname:
            return
        self.moveModel(item.fullname,newName)
        self.highlight('model',newName)

    def _onTreeModelDelete(self, item):
        self.browser.form.searchEdit.lineEdit().setText("")
        model = self.col.models.byName(item.fullname)
        if not model:
            return
        if self.col.models.useCount(model):
            msg = _("Delete this note type and all its cards?")
        else:
            msg = _("Delete this unused note type?")
        if askUser(msg, parent=self, defaultno=True):
            try:
                self.col.models.rem(model)
            except AnkiError:
                #user says no to full sync requirement
                return

        self.col.models.save()
        self.col.models.flush()
        self.browser.setupTable()
        self.browser.model.reset()

    def _onTreeModelAdd(self, item):
        from aqt.models import AddModel
        self.browser.form.searchEdit.lineEdit().setText("")
        m = AddModel(self.mw, self.browser).get()
        if m:
            #model is already created
            txt = getOnlyText(_("Name:"), default=item.fullname+'::')
            if txt:
                m['name'] = txt
            self.col.models.ensureNameUnique(m)
            self.col.models.save(m)

    def onTreeModelFields(self, item):
        from aqt.fields import FieldDialog
        model = self.col.models.byName(item.fullname)
        self.col.models.setCurrent(model)
        n = self.col.newNote(forDeck=False)
        for name in list(n.keys()):
            n[name] = "("+name+")"
        try:
            if "{{cloze:Text}}" in model['tmpls'][0]['qfmt']:
                n['Text'] = _("This is a {{c1::sample}} cloze deletion.")
        except:
            # invalid cloze
            pass
        FieldDialog(self.mw, n, parent=self.browser)

    def onTreeModelOptions(self, item):
        from aqt.forms import modelopts
        model = self.col.models.byName(item.fullname)
        d = QDialog(self)
        frm = modelopts.Ui_Dialog()
        frm.setupUi(d)
        frm.latexHeader.setText(model['latexPre'])
        frm.latexFooter.setText(model['latexPost'])
        d.setWindowTitle(_("Options for %s") % model['name'])
        d.exec_()
        model['latexPre'] = str(frm.latexHeader.toPlainText())
        model['latexPost'] = str(frm.latexFooter.toPlainText())
        self.col.models.save()
        self.col.models.flush()

    def onManageModel(self):
        self.browser.editor.saveNow()
        self.browser.editor.setNote(None)
        self.browser.singleCard=False
        self.mw.checkpoint("Manage model")
        import aqt.models
        aqt.models.Models(self.mw, self.browser)
        self.col.setMod()
        self.browser.onReset()
        self.browser.buildTree()

    def _onTreeMark(self, item):
        tf=not self.marked[item.type].get(item.fullname, False)
        self.marked[item.type][item.fullname]=tf
        color=Qt.yellow if tf else Qt.transparent
        item.setBackground(0, QBrush(color))
        item.setSelected(False)

    def _onTreePin(self, item):
        name = "Pinned::%s"%(
            item.fullname.split("::")[-1])
        search = '"%s:%s"'%(item.type,item.fullname)
        self.col.conf['savedFilters'][name] = search
        self.browser.buildTree()

    def onEmptyAll(self):
        for d in self.col.decks.all():
            if d['dyn']:
                self.col.sched.emptyDyn(d['id'])
        self.browser.onReset()

    def onRebuildAll(self):
        for d in self.col.decks.all():
            if d['dyn']:
                self.col.sched.rebuildDyn(d['id'])
        self.browser.onReset()

    def hasValue(self, item):
        if item.type == "model":
            return self.col.models.byName(item.fullname)
        if item.type == "fav":
            return self.col.conf['savedFilters'].get(item.fullname)
        if item.type in ("pinTag","pinDeck","pinDyn"):
            return self.col.conf['savedFilters'].get(item.favname)
        return False

    def _getItemNames(self, dragItem):
        try: #type fav or pin
            dragName = dragItem.favname
            try:
                dropName = self.dropItem.favname
            except AttributeError:
                dropName = None #no parent
        except AttributeError:
            dragName = dragItem.fullname
            try:
                dropName = self.dropItem.fullname
            except AttributeError:
                dropName = None #no parent
        if not dropName and dragItem.type[:3] == "pin":
            dropName="Pinned"
        return dragName,dropName

    def _toggleMWUpdate(self):
        up = self.col.conf.get('Blitzkrieg.updateOV', False)
        self.col.conf['Blitzkrieg.updateOV'] = not up

    def _toggleShowSubtags(self):
        sa = self.col.conf.get('Blitzkrieg.showAllTags', False)
        self.col.conf['Blitzkrieg.showAllTags'] = not sa

    def _toggleSortOption(self, item):
        sort = not self.col.conf.get('Blitzkrieg.sort_'+item.fullname,False)
        self.col.conf['Blitzkrieg.sort_'+item.fullname] = sort
        self.browser.buildTree()

    def _toggleIconOption(self, item):
        TYPE='fav' if item.type in ("pin","fav") else item.fullname
        ico = not self.col.conf.get('Blitzkrieg.icon_'+TYPE,True)
        self.col.conf['Blitzkrieg.icon_'+TYPE] = ico
        self.browser.buildTree()

    def _changeDecks(self, item):
        up = self.col.conf.get('Blitzkrieg.updateOV', False)
        if up and item.type in ('deck','dyn','pinDeck','pinDyn') \
        and self.mw.state == 'overview':
            d = self.col.decks.byName(item.fullname)
            self.col.decks.select(d["id"])
            self.mw.moveToState("overview")

    def _expandAllChildren(self, item, expanded=False):
        for i in range(item.childCount()):
            itm = item.child(i)
            if itm.childCount():
                self._expandAllChildren(itm, expanded)
        item.setExpanded(expanded)

    def findRecursive(self, item):
        TAG_TYPE = item.fullname
        self.found = {}
        self.found[TAG_TYPE] = {}
        d = QDialog(self.browser)
        frm = aqt.forms.findtreeitems.Ui_Dialog()
        frm.setupUi(d)

        # Restore btn states
        frm.input.setText(self.finder.get('txt',''))
        frm.input.setFocus()
        frm.cb_case.setChecked(self.finder.get('case',0))
        for idx,func in enumerate((
            frm.btn_contains, frm.btn_exactly,
            frm.btn_startswith, frm.btn_endswith,
            frm.btn_regexp
        )):
            func.setChecked(0)
            if self.finder.get('radio',0)==idx:
                func.setChecked(2)

        if not d.exec_():
            return

        txt = frm.input.text()
        if not txt:
            return
        options = Qt.MatchRecursive
        self.finder['txt'] = txt
        self.finder['case'] = frm.cb_case.isChecked()
        if self.finder['case']:
            options |= Qt.MatchCaseSensitive

        if frm.btn_exactly.isChecked():
            options |= Qt.MatchExactly
            self.finder['radio'] = 1
        elif frm.btn_startswith.isChecked():
            options |= Qt.MatchStartsWith
            self.finder['radio'] = 2
        elif frm.btn_endswith.isChecked():
            options |= Qt.MatchEndsWith
            self.finder['radio'] = 3
        elif frm.btn_regexp.isChecked():
            options |= Qt.MatchRegExp
            self.finder['radio'] = 4
        else:
            options |= Qt.MatchContains
            self.finder['radio'] = 0

        self._expandAllChildren(item,True)
        self.browser.buildTree()
        for itm in self.findItems(txt,options):
            if itm.type == TAG_TYPE:
                itm.setBackground(0, QBrush(Qt.cyan))
                self.found[TAG_TYPE][itm.fullname] = True

        if not self.found[TAG_TYPE]:
            showInfo("Found nothing, nada, zilch!")


    def refresh(self):
        self.found = {}
        self.col.tags.registerNotes()
        #Clear to create a smooth UX
        self.marked['group'] = {}
        self.marked['pinDeck'] = {}
        self.marked['pinDyn'] = {}
        self.marked['pinTag'] = {}

    def highlight(self, type, name):
        def unhighlight():
            del(self.marked[type][name])
        self.marked[type][name] = True
        self.mw.progress.timer(100,unhighlight,False)
        if type == 'deck':
            return
        #set parent expanded
        nodes=name.split('::')
        while len(nodes)>1:
            nodes.pop()
            n='::'.join(nodes)
            self.node_state[type][n] = True


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
