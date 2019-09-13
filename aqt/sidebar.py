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
        'model': {}, 'dyn': {}, 'deck': None, 'pinTag': {},
    }

    marked = {
        'group': {}, 'tag': {}, 'fav': {}, 'pinDeck': {}, 'pinDyn': {},
        'model': {}, 'dyn': {}, 'deck': {}, 'pinTag': {},
    }


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
        self.setupContextMenuItems()


    def setupContextMenuItems(self):
              # Type, Item Title, Action Name, Callback
              # type -1: separator
              # type 0: normal
              # type 1: non-folder path, actual item
        self.MENU_ITEMS = {
            "pinDyn":(
                (1,"Empty","Empty",self._onTreeDeckEmpty),
                (1,"Rebuild","Rebuild",self._onTreeDeckRebuild),
                (1,"Options","Options",self._onTreeDeckOptions),
                (1,"Export","Export",self._onTreeDeckExport),
                (-1,),
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Unpin","Unpin",self._onTreeFavDelete),
                (-1,),
                (0,"Mark item (tmp)",None,self._onTreeMarkPinned),
            ),
            "pinDeck":(
                (1,"Add Notes",None,self._onTreeDeckAddCard),
                (1,"Options","Options",self._onTreeDeckOptions),
                (1,"Export","Export",self._onTreeDeckExport),
                (-1,),
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Unpin","Unpin",self._onTreeFavDelete),
                (-1,),
                (0,"Mark item (tmp)",None,self._onTreeMarkPinned),
            ),
            "pinTag":(
                (1,"Select All",None,self._onTreeTagSelectAll),
                (1,"Add Notes",None,self._onTreeTagAddCard),
                (-1,),
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Unpin","Unpin",self._onTreeFavDelete),
                (-1,),
                (0,"Mark item (tmp)",None,self._onTreeMarkPinned),
            ),
            "tag":(
                (0,"Select All",None,self._onTreeTagSelectAll),
                (0,"Add Notes",None,self._onTreeTagAddCard),
                (0,"Rename Leaf","Rename",self._onTreeTagRenameLeaf),
                (0,"Rename Branch","Rename",self._onTreeTagRenameBranch),
                (0,"Delete","Delete",self._onTreeTagDelete),
                (-1,),
                (0,"Pin item",None,self._onTreePin),
                (0,"Mark item (tmp)",None,self._onTreeMark),
                (0,"Convert to decks","Convert",self._onTreeTag2Deck),
            ),
            "deck":(
                (0,"Rename","Rename",self._onTreeDeckRename),
                (0,"Add Notes",None,self._onTreeDeckAddCard),
                (0,"Add Subdeck","Add",self._onTreeDeckAdd),
                (0,"Options","Options",self._onTreeDeckOptions),
                (0,"Export","Export",self._onTreeDeckExport),
                (0,"Delete","Delete",self._onTreeDeckDelete),
                (-1,),
                (0,"Pin item",None,self._onTreePin),
                (0,"Mark item (tmp)",None,self._onTreeMark),
                (0,"Convert to tags","Convert",self._onTreeDeck2Tag),
            ),
            "dyn":(
                (0,"Rename","Rename",self._onTreeDeckRename),
                (0,"Empty","Empty",self._onTreeDeckEmpty),
                (0,"Rebuild","Rebuild",self._onTreeDeckRebuild),
                (0,"Options","Options",self._onTreeDeckOptions),
                (0,"Export","Export",self._onTreeDeckExport),
                (0,"Delete","Delete",self._onTreeDeckDelete),
                (-1,),
                (0,"Pin item",None,self._onTreePin),
                (0,"Mark item (tmp)",None,self._onTreeMark),
            ),
            "fav":(
                (1,"Rename","Rename",self._onTreeFavRename),
                (1,"Modify","Modify",self._onTreeFavModify),
                (1,"Delete","Delete",self._onTreeFavDelete),
                (-1,),
                (0,"Mark item (tmp)",None,self._onTreeMark),
            ),
            "model":(
                (0,"Rename Leaf","Rename",self._onTreeModelRenameLeaf),
                (0,"Rename Branch","Rename",self._onTreeModelRenameBranch),
                (0,"Add Model","Add",self._onTreeModelAdd),
                (1,"Edit Fields","Edit",self.onTreeModelFields),
                (1,"LaTeX Options","Edit",self.onTreeModelOptions),
                (1,"Delete","Delete",self._onTreeModelDelete),
                (-1,),
                (0,"Mark item (tmp)",None,self._onTreeMark),
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
        if getattr(item, 'onclick', None):
            item.onclick()

    def onTreeCollapse(self, item):
        """Decks do not call this method"""
        if getattr(item, 'oncollapse', None):
            item.oncollapse() #decks only
            return
        if not isinstance(item.type, str):
            return
        exp = item.isExpanded()
        self.node_state[item.type][item.fullname] = exp
        if item.type == 'tag' and '::' not in item.fullname:
            if exp:
                item.setBackground(0, QBrush(QColor(0,0,10,10)))
            else:
                item.setBackground(0, QBrush(Qt.transparent))


    def dropMimeData(self, parent, row, data, action):
        # Dealing with qt serialized data is a headache,
        # so I'm just going to save a reference to the dropped item.
        # data.data('application/x-qabstractitemmodeldatalist')
        self.dropItem = parent
        return True


    def dropEvent(self, event):
        dragItem = event.source().currentItem()
        if not isinstance(dragItem.type, str):
            return
        if dragItem.type not in self.node_state:
            event.setDropAction(Qt.IgnoreAction)
            event.accept()
            return
        QAbstractItemView.dropEvent(self, event)
        if not self.dropItem or self.dropItem.type == dragItem.type:
            dragName = dragItem.fullname
            try:
                dropName = self.dropItem.fullname
            except AttributeError:
                dropName = None #no parent
            self.mw.checkpoint("Dragged "+dragItem.type)
            parse=self.col.decks #used for parsing '::' separators
            if dragItem.type in ("deck", "dyn"):
                self._deckDropEvent(dragName,dropName)
            elif dragItem.type == "tag":
                self._strDropEvent(dragName,dropName,self.moveTag)
                self.node_state['tag'][dropName] = True
            elif dragItem.type == "model":
                self._strDropEvent(dragName,dropName,self.moveModel)
                self.node_state['model'][dropName] = True
            elif dragItem.type == "fav":
                self._strDropEvent(dragName,dropName,self.moveFav)
                self.node_state['fav'][dropName] = True
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
        dragDid = parse.byName(dragName)["id"]
        dropDid = parse.byName(dropName)["id"] if dropName else None
        try:
            parse=self.col.decks #used for parsing '::' separators
            parse.renameForDragAndDrop(dragDid,dropDid)
        except DeckRenameError as e:
            showWarning(e.description)
        self.col.decks.get(dropDid)['browserCollapsed'] = False

    def moveFav(self, dragName, newName=""):
        saved = self.col.conf['savedFilters']
        for fav in list(saved):
            act = self.col.conf['savedFilters'].get(fav)
            if fav.startswith(dragName + "::"):
                nn = fav.replace(dragName+"::", newName+"::", 1)
                self.col.conf['savedFilters'][nn] = act
                del(self.col.conf['savedFilters'][fav])
                self.node_state['fav'][nn] = True
            elif fav == dragName:
                self.col.conf['savedFilters'][newName] = act
                del(self.col.conf['savedFilters'][dragName])
                self.node_state['fav'][newName] = True

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
                ids = f.findNotes("tag:"+tag)
                if rename:
                    nn = tag.replace(dragName+"::", newName+"::", 1)
                    self.col.tags.bulkAdd(ids,nn)
                    self.node_state['tag'][nn] = True
                self.col.tags.bulkRem(ids,tag)
                self.mw.progress.update(label=tag)
        # rename parent
        ids = f.findNotes("tag:"+dragName)
        if rename:
            self.col.tags.bulkAdd(ids,newName)
            self.node_state['tag'][newName] = True
        self.col.tags.bulkRem(ids,dragName)
        self.col.tags.save()
        self.col.tags.flush()
        self.col.tags.registerNotes()
        self.browser.setupHooks()


    def onTreeMenu(self, pos):
        item=self.currentItem()
        if not item or not isinstance(item.type, str):
            return

        m = QMenu(self)
        if item.type == "sys":
            pass #skip

        elif item.type == "group":
            if item.fullname == "deck":
                act = m.addAction("Add Deck")
                act.triggered.connect(lambda:
                    self._onTreeItemAction(item,"Add",self._onTreeDeckAdd))
                act = m.addAction("Empty All Filters")
                act.triggered.connect(lambda:
                    self._onTreeItemAction(item,"Empty",self.onEmptyAll))
                act = m.addAction("Rebuild All Filters")
                act.triggered.connect(lambda:
                    self._onTreeItemAction(item,"Rebuild",self.onRebuildAll))

            elif item.fullname == "model":
                act = m.addAction("Manage Model")
                act.triggered.connect(self.onManageModel)

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
        self.mw.progress.start(label="Sidebar Action")
        try:
            callback(item)
        finally:
            self.mw.progress.finish()
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
        # self.mw.onDeckConf(sel)
        if deck['dyn']:
            import aqt.dyndeckconf
            aqt.dyndeckconf.DeckConf(self.mw, deck=deck, parent=self.browser)
        else:
            import aqt.deckconf
            aqt.deckconf.DeckConf(self.mw, deck, self.browser)
        self.mw.reset(True)

    def _onTreeDeckExport(self, item):
        sel = self.col.decks.byName(item.fullname)
        # self.mw.onExport(did=sel['id'])
        import aqt.exporting
        aqt.exporting.ExportDialog(self.mw, sel['id'], self.browser)
        self.mw.reset(True)

    def _onTreeDeckAdd(self, item):
        default=item.fullname+"::" if item.type=='deck' else ''
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

    def _onTreeDeckRename(self, item):
        did = self.col.decks.byName(item.fullname)["id"]
        self.mw.deckBrowser._rename(did)
        self.col.decks.save()
        self.col.decks.flush()
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

    def _onTreeTagRenameBranch(self, item):
        newName = getOnlyText(_("New tag name:"),default=item.fullname)
        newName = newName.replace('"', "")
        if not newName or newName == item.fullname:
            return
        self.moveTag(item.fullname,newName)

    def _onTreeTagDelete(self, item):
        self.moveTag(item.fullname,rename=False)

    def _onTreeDeck2Tag(self, item):
        msg = _("Convert all notes in deck/subdecks to tags?")
        if not askUser(msg, parent=self, defaultno=True):
            return

        f = anki.find.Finder(self.col)
        parentDid = self.col.decks.byName(item.fullname)["id"]
        actv = self.col.decks.children(parentDid)
        actv = sorted(actv, key=lambda t: t[0])
        actv.insert(0,(item.fullname,parentDid))

        self.mw.checkpoint("Convert %s to tag"%item.type)
        for name,did in actv:
            #add subdeck tree structure as tags
            nids = f.findNotes('''"deck:%s" -"deck:%s::*"'''%(name,name))
            tagName = re.sub(r"\s*(::)?\s*","\g<1>",name)
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
            self.mw.progress.update(label=name)

        self.col.decks.save()
        self.col.decks.flush()
        self.col.tags.save()
        self.col.tags.flush()
        self.col.tags.registerNotes()
        self.mw.requireReset()


    def _onTreeTag2Deck(self, item):
        def tag2Deck(tag):
            did = self.col.decks.id(tag)
            cids = f.findCards("tag:"+tag)
            self.col.sched.remFromDyn(cids)
            self.col.db.execute(
                "update cards set usn=?, mod=?, did=? where id in %s"%ids2str(cids),
                self.col.usn(), intTime(), did
            )
            nids = f.findNotes("tag:"+tag)
            self.col.tags.bulkRem(nids,tag)
            self.mw.progress.update(label=tag)

        msg = _("Convert all tags to deck structure?")
        if not askUser(msg, parent=self, defaultno=True):
            return

        f = anki.find.Finder(self.col)
        parent = item.fullname
        tag2Deck(parent)
        for tag in self.col.tags.all():
            if tag.startswith(parent + "::"):
                tag2Deck(tag)
        self.col.decks.save()
        self.col.decks.flush()
        self.col.tags.save()
        self.col.tags.flush()
        self.col.tags.registerNotes()
        self.mw.requireReset()


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
        if newName:
            if p: newName="Pinned::"+newName
            self.col.conf['savedFilters'][newName] = act
            del(self.col.conf['savedFilters'][item.favname])

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

    def _onTreeModelRenameBranch(self, item):
        self.browser.form.searchEdit.lineEdit().setText("")
        model = self.col.models.byName(item.fullname)
        newName = getOnlyText(_("New model name:"),default=item.fullname)
        newName = newName.replace('"', "")
        if not newName or newName == item.fullname:
            return
        self.moveModel(item.fullname,newName)

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

    def _onTreeMarkPinned(self, item):
        tf=not self.marked[item.type].get(item.favname, False)
        self.marked[item.type][item.favname]=tf

    def _onTreePin(self, item):
        name = "Pinned::%s"%(
            item.fullname.split("::")[-1])
        search = '"%s:%s"'%(item.type,item.fullname)
        self.col.conf['savedFilters'][name] = search

    def onEmptyAll(self, item):
        for d in self.col.decks.all():
            if d['dyn']:
                self.col.sched.emptyDyn(d['id'])

    def onRebuildAll(self, item):
        for d in self.col.decks.all():
            if d['dyn']:
                self.col.sched.rebuildDyn(d['id'])

    def hasValue(self, item):
        if item.type == "model":
            return self.col.models.byName(item.fullname)
        if item.type == "fav":
            return self.col.conf['savedFilters'].get(item.fullname)
        if item.type in ("pinTag","pinDeck","pinDyn"):
            return self.col.conf['savedFilters'].get(item.favname)
        return False
