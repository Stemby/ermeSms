# -*- coding: utf-8 -*-

import sys
import traceback

from moio.plugins.Sender import Sender
from moio.PreferenceManager import PreferenceManager
from moio.plugins.UI import UI

class GraphicalUI(UI):
    """Interfaccia grafica in PyQt."""

    MainFrame = None

    def isAvailable(self):
        """Ritorna true se quest'interfaccia è utilizzabile."""
        #non ci devono essere parametri se -gui non è specificato
        result = (len(sys.argv) == 1) or ("-gui" in sys.argv)
        try:
            #deve essere installata correttamente wxpython
            from PyQt4 import QtGui, QtCore
            from moio.plugins.uis.MainFrame import MainFrame
        except ImportError, e:
            result = False
            print e
        return result

    def getPriority(self):
        """Ritorna un codice di priorità. In caso più interfacce siano
        utilizzabili, viene scelta quella a maggiore priorità."""
        return 3

    def run(self):
        """Avvia questa interfaccia."""
        from PyQt4 import QtGui, QtCore
        from moio.plugins.uis.MainFrame import MainFrame
        import os
        self.QtUIApp = QtGui.QApplication(sys.argv)
        pluginWin=os.path.join(os.getcwd(),'qt4_plugins',
                                       'imageformats','qjpeg.dll')
        pluginMac=os.path.join(os.getcwd(),'qt4_plugins',
                                       'imageformats','libqjpeg.dylib')
        pluginUnix=os.path.join(os.getcwd(),'qt4_plugins',
                                       'imageformats','libqjpeg.so')
        if os.path.isfile(pluginWin) or os.path.isfile(pluginMac) or \
           os.path.isfile(pluginUnix):
            self.QtUIApp.setLibraryPaths(
                QtCore.QStringList(os.path.join(os.getcwd(),'qt4_plugins')))
        self.QtUIApp.setQuitOnLastWindowClosed(False)
        self.MainFrame = MainFrame()
        self.MainFrame.show()
        sys.exit(self.QtUIApp.exec_())


    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        from PyQt4 import QtGui
        QtGui.QMessageBox.critical(self.MainFrame, "Errore", message)

