from qgis import gui, core
from qgis.utils import iface
from PyQt5 import QtCore, uic, QtWidgets, QtGui

class DeleteSelected:

    def __init__(self):
        self.names = [ 'mActionDeleteSelected' ]

    def execute(self):
        for a in gui.QgsGui.shortcutsManager().listActions():
            if not( a.objectName() in self.names ):
                continue
            iface.activeLayer().startEditing()
            a.trigger()
            break