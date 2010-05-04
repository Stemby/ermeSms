# -*- coding: UTF-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class PasswordErrorDialog(QDialog):

    request = None
    label = {}
    textCtrl = {}
    #indici per le singole richieste

    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)
        self.messageLabel = QLabel("Dati inseriti non validi, reimmetterli" +\
                                   "(sito XXXXXXXXXXXXXXXX)")
        self.okButton = QPushButton("OK")
        self.closeButton = QPushButton("Chiudi")

        self.__set_properties()

        self.connect(self.okButton, SIGNAL('clicked(bool)'),
                     self.okButtonEventHandler)
        self.connect(self.closeButton, SIGNAL('clicked(bool)'),
                     self, SLOT('close()'))

    def __set_properties(self):
        self.setWindowTitle("Inserisci i dati richiesti")
        self.okButton.setDefault(True)

    def do_layout(self):
        vbox = QVBoxLayout()
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.messageLabel, 0)
        hbox_1.addStretch(1)
        vbox.addLayout(hbox_1)
        vbox.addStretch(1)
        form = QFormLayout()
        for i in self.request:
            form.addRow(self.label[i],self.textCtrl[i])
        vbox.addLayout(form)
        vbox.addStretch(1)
        hbox_2 = QHBoxLayout()
        hbox_2.addStretch(1)
        hbox_2.addWidget(self.okButton, 0)
        hbox_2.addWidget(self.closeButton, 0)
        hbox_2.addStretch(1)
        vbox.addLayout(hbox_2)

        self.setLayout(vbox)
        self.resize(self.minimumSizeHint())

    def okButtonEventHandler(self, event):
        self.done(1)

    def prepare(self, i):
        self.label[i] = QLabel(i+":")
        if i == 'Nome utente':
            self.textCtrl[i] = QLineEdit("Immetti il nome utente qui.")
        elif i == 'Password':
            self.textCtrl[i] = QLineEdit("123456")
            self.textCtrl[i].setEchoMode(QLineEdit.Password)
        else: self.textCtrl[i] = QLineEdit("")
        if i == self.request[0]: self.textCtrl[i].setFocus()

    def setTextValue(self, i, value):
        self.textCtrl[i].setText(value)

    def setMessage(self, message):
        self.messageLabel.setText(message)

    def getValue(self,i):
        return unicode(self.textCtrl[i].text())
