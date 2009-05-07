# -*- coding: UTF-8 -*-

# Author:
#    Francesco Marella <francesco.marella@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from moio.plugins.Book import Book
from moio.plugins.Sender import Sender
from moio.plugins.uis.SenderChoicesDialog import SenderChoicesDialog

import exceptions
from moio.errors.PreferenceManagerError import PreferenceManagerError

class PreferenceDialog(QDialog):
    edited = False
    needRestart = False
    senderList = None

    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)

        self.bookComboBox = QComboBox()
        self.bookComboBox.addItems(Book.getPlugins().keys())
        self.bookComboBox.setCurrentIndex(self.bookComboBox.findText(mf.pm.getBook(), Qt.MatchExactly))
        self.proxyUrl = QLineEdit()
        self.proxyUrl.setMaxLength(255)
        if mf.pm.isProxyEnabled():
            self.proxyUrl.setText(mf.pm.getProxy())
        self.resetSenderListButton = QPushButton("Reimposta lista Sender")
        self.changePasswordButton = QPushButton("Cambia password")
        self.applyButton = QPushButton("Applica")
        self.closeButton = QPushButton("Chiudi")

        self.setMinimumWidth(400)             

        self.__set_properties()
        self.__do_layout()

        self.mf = mf
        self.connect(self.applyButton, SIGNAL('clicked(bool)'),
                 self.applyButtonEventHandler)
        self.connect(self.resetSenderListButton, SIGNAL('clicked(bool)'),
                 self.resetSenderListHandler)
        self.connect(self.closeButton, SIGNAL('clicked(bool)'),
                 self, SLOT('close()'))

        self.connect(self.proxyUrl, SIGNAL('textChanged(const QString&)'),
                 self.proxyUrlHandler)

        self.connect(self.changePasswordButton, SIGNAL('clicked(bool)'),
                 self.changePasswordEventHandler)

        self.connect(self.bookComboBox, SIGNAL('currentIndexChanged(int)'),
                 self.bookComboBoxHandler)
        
        posx = (QDesktopWidget().width()-self.width())/2
        posy = ((QDesktopWidget().height()/3*2)-self.height())/2
        self.move(posx,posy)           
        
    def __set_properties(self):
        self.setWindowTitle("Preferenze")
        self.applyButton.setDefault(True)

    def __do_layout(self):

        vbox = QVBoxLayout()
        
        hbox_1 = QHBoxLayout()
        label = QLabel("Seleziona la rubrica:")
        hbox_1.addWidget(label, 1)
        hbox_1.addWidget(self.bookComboBox, 1)
        vbox.addLayout(hbox_1, 0)

        hbox_2 = QHBoxLayout()
        label2 = QLabel("Proxy:")
        hbox_2.addWidget(label2, 1)
        hbox_2.addWidget(self.proxyUrl, 1)
        vbox.addLayout(hbox_2, 0)

        hbox_4 = QHBoxLayout()
        hbox_4.addStretch(1)
        hbox_4.addWidget(self.resetSenderListButton, 0)
        hbox_4.addStretch(1)
        hbox_4.addWidget(self.changePasswordButton, 0)
        hbox_4.addStretch(1)
        vbox.addLayout(hbox_4, 0)

        hbox_3 = QHBoxLayout()
        hbox_3.addWidget(self.applyButton, 0)
        hbox_3.addStretch(1)
        hbox_3.addWidget(self.closeButton, 0)
        vbox.addLayout(hbox_3, 0)

        self.setLayout(vbox)
        self.resize(self.sizeHint())

    def applyButtonEventHandler(self):
        if self.edited:
            self.mf.pm.setBook(unicode(self.bookComboBox.currentText()))
            if self.proxyUrl.text() == "":
                self.mf.pm.unsetProxy()
            else:
                self.mf.pm.setProxy(unicode(self.proxyUrl.text()))
            if self.senderList:
                self.mf.pm.setSenderList(self.senderList, 
                    Sender.getPlugins().keys())
            self.edited = False
        if self.needRestart:
            QMessageBox.information(self, u"Informazione", 
                u"Per applicare le modifiche è necessario\n riavviare MoioSMS.")
        self.close()

    def proxyUrlHandler(self, newProxyUrl):
        self.edited = True

    def bookComboBoxHandler(self, bookIndex):
        self.edited = True
        self.needRestart = True

    def resetSenderListHandler(self):
        self.edited = True
        self.needRestart = True
        scd=SenderChoicesDialog(self.mf)
        result = scd.exec_()
        if result == 0:
            self.senderList = Sender.getPlugins().keys()
        else:
            self.senderList = scd.getSenderList()

    def changePasswordEventHandler(self):
        if self.mf.pm.isEncryptionEnabled():
            keyValid = False
            while keyValid == False:
                pd, result = QInputDialog.getText(None, "Master Password",
                        u"Inserisci la vecchia Master Password",
                        QLineEdit.Password)
                if result == False:
                    return
                keyValid = self.mf.pm.checkEncryptionKey(self.mf.masterKey)
            self.mf.pm.disableEncryption()
            self.mf.masterKey = None
        else:
            result = QMessageBox.question(self,
                u"Vuoi crittare i tuoi dati sensibili?",
                u"Nessuna Master Password, utilizzarne una?\n", 'Si','No')
            if result==0:
                pd, result = QInputDialog.getText(self, "Master Password",
                        u"Inserisci la Master Password"+\
                        u" (ti verrà richiesta ad ogni uso di MoioSMS)",
                        QLineEdit.Password)
                pd = unicode(pd)
                self.mf.masterKey = pd
                self.mf.pm.enableEncryption(pd)
            else:
                self.mf.masterKey = None
                self.mf.pm.disableEncryption()
    
    def closeEvent(self, event):
        """Evento di chiusura della finestra"""
        if self.edited:
            result = QMessageBox.question(self,
            u"Vuoi chiudere?",
            u"Attenzione, le modifiche apportate non sono\n" +
            u"state salvate. Chiudere ugualmente?",
            'Si','No')
            if result == 1:
                event.ignore()
