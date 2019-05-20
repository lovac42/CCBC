from PyQt4 import QtCore, QtGui
from anki.lang import _


def menu(self):
    self.verticalLayout_2.removeWidget(self.tableView)
    self.infogrid = QtGui.QGridLayout()
    self.infowidget = QtGui.QWidget()
    self.infowidget.setLayout(self.infogrid)
    self.verticalLayout_2.addWidget(self.infowidget)    
    self.verticalLayout_2.addWidget(self.tableView)
