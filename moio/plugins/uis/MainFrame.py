# -*- coding: utf-8 -*-

import sys
import os
import exceptions
import Queue
import time

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from moio.plugins.Book import Book
from moio.plugins.uis.PreferenceDialog import PreferenceDialog
from moio.plugins.uis.Icons import getOkData, getErrorData, getIconData
from moio.plugins.uis.SenderChoicesDialog import SenderChoicesDialog
from moio.plugins.uis.OfflineSendDialog import OfflineSendDialog
from moio.plugins.uis.LogViewerDialog import LogViewerDialog
from moio.plugins.uis.PasswordErrorDialog import PasswordErrorDialog
from moio.plugins.uis.CaptchaDialog import CaptchaDialog

from moio.plugins.uis.GraphicalUI import GraphicalUI
from moio.PreferenceManager import PreferenceManager
from moio.plugins.uis.SendMessage import SendMessage
from moio.plugins.Sender import Sender

from moio.errors.PreferenceManagerError import PreferenceManagerError
from moio.errors.BookError import BookError

class MainFrame(QFrame):

    ui = GraphicalUI.getInstance()
    """Riferimento al plugin UI relativo a questo frame."""

    pm = PreferenceManager.getInstance()
    """Riferimento al gestore delle preferenze."""

    masterKey = None
    """La chiave di crittazione del PreferenceManager o None se non è
    settata."""

    offlineSend = None
    """Riferimento alla dialog per l'invio posticipato"""

    tray = None
    traymessage = None
    """Riferimento all'icona e ai messaggi nella sistem tray"""

    qReq = Queue.Queue(1)
    qRes = Queue.Queue(1)
    qCaptcha = Queue.Queue(1)
    """Oggetti per far dialogare i Thread"""

    book = None
    
    def __init_book(self):
        try:
            if not (self.pm.isBookSet() and 
               (self.pm.getBook() in Book.getPlugins().keys())):
                self.pm.setBook("BuiltInBook")
        except PreferenceManagerError:
             pass
        self.book = Book.getPlugins()[self.pm.getBook()]

    def __init__(self):
        self.flag = Qt.WindowFlags(Qt.Window)
        QFrame.__init__(self, None, self.flag)
        self.setWindowState(Qt.WindowActive)

        self.defaultFlag = Qt.WindowFlags(Qt.CustomizeWindowHint |
                                          Qt.WindowTitleHint |
                                          Qt.WindowSystemMenuHint )
		#inizializza il book
        self.__init_book()

        #Icona della titlebar
        pixmap = QPixmap()
        pixmap.loadFromData(getIconData())
        icon = QIcon()
        icon.addPixmap(pixmap)
        self.setWindowIcon(icon)

        self.label = QLabel("A:")
        self.destinationComboBox = QComboBox()
        self.destinationComboBox.setInsertPolicy(QComboBox.NoInsert)
        self.destinationComboBox.setEditable(True)
        self.destinationComboBox.completer().setCaseSensitivity(
            Qt.CaseSensitive)
        try:
            contatti = self.book.getContacts().keys()
            contatti.sort()
        except BookError, be:
            QMessageBox.critical(self, u"Errore", be.__str__())
        self.destinationComboBox.addItems(contatti)
        self.deleteButton = QPushButton("Cancella")
        self.addButton = QPushButton("Metti in rubrica")
        self.label.setMinimumHeight(self.addButton.minimumSizeHint().height())
        self.messageTextCtrl = QTextEdit("Inserisci il tuo messaggio qui.")
        self.messageTextCtrl.setMinimumHeight(70)
        self.messageTextCtrl.setTabChangesFocus(True)
        if self.pm.isSenderListAvailable(Sender.getPlugins().keys()) == False:
            scd=SenderChoicesDialog(self)
            result = scd.exec_()
            if result == 0:
                senderList = Sender.getPlugins().keys()
            else:
                senderList = scd.getSenderList()
                self.pm.setSenderList(senderList,Sender.getPlugins().keys())
        else: senderList = self.pm.getSenderList()
        self.senderBoxes = {}
        self.senderRadioBox = QGroupBox("Scegli il sito per l'invio")
        for i in senderList:
            self.senderBoxes[i] = QRadioButton(i)
        self.senderBoxes[senderList[0]].setChecked(True)
        self.logButton = QPushButton("Apri Registro")
        self.prefButton = QPushButton("Preferenze")
        self.check = QCheckBox("Posticipa invio")
        self.sendButton = QPushButton("Invia!")
        self.stopButton = QPushButton("Annulla invio...")
        self.messageLabel = QLabel("Non in rubrica")
        self.gauge = QProgressBar()
        self.gauge.setRange(0,1000)
        self.gauge.setMinimumHeight(32)
        self.normalcursor = self.cursor()
        self.waitcursor = QCursor(Qt.BusyCursor)

        self.bitmap = QLabel()
        self.iconsize = QSize(32,32)
        self.bitmap.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.bitmap.setMinimumSize(32,32)
        self.bitmap.resize(self.bitmap.sizeHint())

        self.__set_properties()
        self.__do_layout()

        self.sendButton.setToolTip("Invia l'SMS")
        self.stopButton.setToolTip("Interrompi l'invio")
        self.logButton.setToolTip("Esamina gli SMS inviati")
        self.check.setToolTip("Selezione per posticipare l'invio")
        self.addButton.setToolTip("Aggiungi il numero inserito in rubrica")
        self.deleteButton.setToolTip("Rimuovi l'elemento selezionato dalla" +\
                                     " rubrica")

        #imposto la system tray icon
        self.tray = QSystemTrayIcon(icon)
        if self.tray.supportsMessages():
            self.traymessage = self.tray.showMessage
        if self.tray.isSystemTrayAvailable():
            #imposto il menu contestuale
            self.menu = QMenu("MoioSMS", self)
            self.mostra = self.menu.addAction('Nascondi MoioSMS',
                                              self.systemTrayEventHandler)
            self.preferenze = self.menu.addAction('Preferenze',
                                                  self.prefButtonEventHandler)
            self.menu.addSeparator()
            log = self.menu.addAction('Mostra Log',
                                      self.logButtonEventHandler)
            self.menu.addSeparator()
            esci = self.menu.addAction('Esci', self.closeEvent)

            self.tray.setContextMenu(self.menu)
            self.tray.show()
            self.connect(self.tray,
                     SIGNAL('activated(QSystemTrayIcon::ActivationReason)'),
                     self.systemTrayEventHandler)
        else: 
            self.tray = None

        #Evento: il testo nella combobox cambia
        #PRIMA viene richiamato destinationComboBoxEventHandler
        #e POI updateLabel
        self.connect(self.destinationComboBox,
                     SIGNAL('editTextChanged(const QString&)'),
                     self.destinationComboBoxEventHandler)
        self.connect(self.destinationComboBox,
                     SIGNAL('editTextChanged(const QString&)'),
                     self.updateLabel)

        #Eventi: pressione di bottoni
        self.connect(self.addButton, SIGNAL('clicked(bool)'),
                     self.addButtonEventHandler)
        self.connect(self.addButton, SIGNAL('clicked(bool)'),
                     self.updateLabel)
        self.connect(self.deleteButton, SIGNAL('clicked(bool)'),
                     self.deleteButtonEventHandler)
        self.connect(self.deleteButton, SIGNAL('clicked(bool)'),
                     self.updateLabel)
        self.connect(self.logButton, SIGNAL('clicked(bool)'),
                     self.logButtonEventHandler)
        self.connect(self.stopButton, SIGNAL('clicked(bool)'),
                     self.stopButtonEventHandler)
        self.connect(self.sendButton, SIGNAL('clicked(bool)'),
                     self.sendButtonEventHandler)
        self.connect(self.prefButton, SIGNAL('clicked(bool)'),
                     self.prefButtonEventHandler)

        #Altri eventi che comportano aggiornamenti della barra di stato
        self.connect(self.messageTextCtrl, SIGNAL('textChanged()'),
                     self.updateLabel)

        for i in self.senderBoxes:
            self.connect(self.senderBoxes[i], SIGNAL('clicked(bool)'),
                     self.updateLabel)

        #Eventi personalizzati di comunicazione tra Thread e system tray
        self.connect(self, SIGNAL('passRequest'),
                     self.passRequestEventHandler)
        self.connect(self, SIGNAL('proxyRequest'),
                     self.proxyRequestEventHandler)
        self.connect(self, SIGNAL('gaugeUpdate'),
                     self.gaugeUpdateEventHandler)
        self.connect(self, SIGNAL('criticalError'),
                     self.criticalSenderErrorHandler)
        self.connect(self, SIGNAL('userDecodeCaptcha'),
                     self.userDecodeCaptchaHandler)
        self.connect(self, SIGNAL('sentMessageUpdate'),
                     self.sentUpdateEventHandler)
        self.connect(self, SIGNAL('logSave'),
                     self.logSaveEventHandler)
        self.connect(self, SIGNAL('minimizeToTray'),
                     self.systemTrayEventHandler, Qt.QueuedConnection)

        #Se specificato da linea di comando, inserisco i parametri
        if (len(sys.argv) in [3,4]) and sys.argv[1]=="-gui":
            self.destinationComboBox.setEditText(sys.argv[2])
            if (len(sys.argv) == 4):
                self.messageTextCtrl.setText(sys.argv[3])
        else:
            #altrimenti gli ultimi settaggi usati
            if self.pm.isLastUsedAvailable("destination"):
                self.destinationComboBox.setEditText(
                    self.pm.getLastUsed("destination"))

        #se il messaggio precedente non è stato inviato
        if self.pm.isLastUsedAvailable("message"):
            self.messageTextCtrl.setText(self.pm.getLastUsed("message"))
        #se trova i settaggi per il sender dell'ultimo destinatario
        if self.pm.isLastUsedAvailable("destination"):
            if self.pm.isContactSenderAvailable(
                self.pm.getLastUsed("destination")):
                if self.senderBoxes.has_key(self.pm.getContactSender(
                    self.pm.getLastUsed("destination"))):
                    self.senderBoxes[self.pm.getContactSender(
                        self.pm.getLastUsed("destination"))].setChecked(True)
            #altrimenti l'ultimo selezionato
            elif self.pm.isLastUsedAvailable("sender"):
                if self.senderBoxes.has_key(self.pm.getLastUsed("sender")):
                    self.senderBoxes[self.pm.getLastUsed(
                        "sender")].setChecked(True)

        #sposto al centro la Main
        posx = (QDesktopWidget().width()-self.width())/2
        posy = ((QDesktopWidget().height()/3*2)-self.height())
        self.move(posx,posy)

        #Per evitare di riscrivere codice di inizializzazione già presente
        #negli eventHandler, li avvio manualmente la prima volta
        self.destinationComboBoxEventHandler('init')
        self.updateLabel()
        self.updateSentMessages()

    def __set_properties(self):
        self.setWindowTitle("MoioSMS " + self.pm.getVersion())
        self.destinationComboBox.setFocus()
        self.deleteButton.hide()
        self.stopButton.hide()
        self.gauge.hide()
        self.sendButton.setDefault(True)

        if self.pm.isEncryptionEnabled():
            keyValid = False
            while keyValid == False:
                pd, result = QInputDialog.getText(None, "Master Password",
                        u"Inserisci la Master Password",
                        QLineEdit.Password)
                if result == False:
                    sys.exit(0)
                self.masterKey = unicode(pd)
                keyValid = self.pm.checkEncryptionKey(self.masterKey)

    def __do_layout(self):
        grid = QGridLayout()
        hbox_1 = QHBoxLayout()
        hbox_2 = QHBoxLayout()
        grid_2 = QGridLayout()
        hbox_5 = QHBoxLayout()
        grid.setSpacing(5)
        grid_2.setSpacing(0)

        hbox_1.addWidget(self.label, 0, Qt.AlignLeft)
        hbox_1.addWidget(self.destinationComboBox, 1)
        hbox_1.addWidget(self.deleteButton, 0)
        hbox_1.addWidget(self.addButton, 0)
        hbox_1.addWidget(self.prefButton, 0)
        grid.addLayout(hbox_1, 0, 0)

        hbox_2.addWidget(self.bitmap)
        hbox_2.addWidget(self.messageLabel, 1, Qt.AlignLeft)
        hbox_2.addWidget(self.gauge)
        grid.addLayout(hbox_2, 1, 0)

        vbox = QVBoxLayout()
        vbox.addWidget(self.messageTextCtrl, 1)
        grid.addLayout(vbox, 2, 0)

        x = 0
        y = 0
        for i in self.senderBoxes:
            grid_2.addWidget(self.senderBoxes[i], y, x)
            x += 1
            if x == 4:
                x=0
                y += 1
        self.senderRadioBox.setLayout(grid_2)
        grid.addWidget(self.senderRadioBox, 3, 0)

        hbox_5.addStretch(1)
        hbox_5.addWidget(self.sendButton, 1)
        hbox_5.addWidget(self.stopButton, 1)
        hbox_5.addStretch(1)
        hbox_5.addWidget(self.logButton,0)
        checkBox = QGroupBox()
        check = QHBoxLayout()
        check.addWidget(self.check)
        checkBox.setLayout(check)
        hbox_5.addWidget(checkBox, 0)
        grid.addLayout(hbox_5, 4, 0)

        self.setLayout(grid)
        self.resize(self.minimumSizeHint())
        self.move(600,400)

    def setIcon(self, icon):
        """Cambia l'immagine visualizzata.
        Passando None l'immagine viene rimossa."""
        if icon :
            pixmap = QPixmap(self.iconsize)
            pixmap.loadFromData(icon)
            self.bitmap.setPixmap(pixmap)
        else: self.bitmap.setText(' ')

    def insertDestinationComboBox(self, name):
        """Inserisci il nome indicato in ordine alfabetico"""
        i = 0
        k = self.destinationComboBox.count()
        while i < self.destinationComboBox.count():
            if (unicode(name).lower() <
                unicode(self.destinationComboBox.itemText(i)).lower()):
                k = i
                i = self.destinationComboBox.count()
            i += 1
        self.destinationComboBox.insertItem(k,name)

    def getSender(self):
        """Restituisce il sender selezionato in valore unicode"""
        value = None
        for i in self.senderBoxes:
            if self.senderBoxes[i].isChecked():
                value = i
        value = unicode(value)
        return value

    def destinationComboBoxEventHandler(self, event):
        """Mostra o nasconde i bottoni per la rubrica."""
        destString = unicode(self.destinationComboBox.currentText())

        showAddButton = False
        showDeleteButton = False

        #Se c'è un destinatario, 5 casi:
        if destString != "":
            if self.isValid(destString):
                if self.book.isNumberInContacts(destString):
                    #1-E' un numero in rubrica. Sostituisco col nome,
                    #propongo di cancellarlo
                    destString = self.book.lookupNumber(destString)
                    self.destinationComboBox.setEditText(destString)
                    showDeleteButton = True
                else:
                    #2-E' un numero valido non in rubrica.
                    #Propongo di aggiungerlo
                    showAddButton = True
            elif self.book.isInContacts(destString):
                #3- è un nome in rubrica, propongo di cancellarlo
                showDeleteButton = True
            elif self.isNumber(destString)==False:
                #4- è un nome non in rubrica, propongo di aggiungerlo
                showAddButton = True
            #5- E' un numero ma non è valido

        if self.pm.isContactSenderAvailable(destString):
            if self.senderBoxes.has_key(self.pm.getContactSender(destString)):
                self.senderBoxes[self.pm.getContactSender(
                    destString)].setChecked(True)

        #Aggiorno la grafica
        self.addButton.setVisible(showAddButton)
        self.deleteButton.setVisible(showDeleteButton)

        self.update()

    def updateLabel(self, event=None):
        """Aggiorna la barra dei messaggi segnalando all'utente eventuali
        problemi. Se vengono rilevati problemi, disabilita il bottone Invia"""
        canSend = True
        message = ""

        destString = unicode(self.destinationComboBox.currentText())

        #1- Segnalazioni di errore

        text = unicode(self.messageTextCtrl.toPlainText())

        if destString == "":
            message = "Inserisci un destinatario"
            canSend = False
        elif self.isNumber(destString) == False and \
             self.book.isInContacts(destString)==False:
            message = "Non in rubrica"
            canSend = False
        elif self.isNumber(destString) and self.isValid(destString) == False:
            message = "Inserisci un numero di cellulare"
            canSend = False
        elif text == "":
            message = "Inserisci del testo nel messaggio"
            canSend = False

        #2- Segnalazioni secondarie (da mostrare se non ci sono
        #errori
        if canSend:
            if not event or event==True:
                #2.1- L'utente ha appena scritto un carattere del mesaggio
                #     o ha selezionato un nuovo sender
                sender = Sender.getPlugins()[self.getSender()]
                texts = sender.splitText(sender.replaceNonAscii(text))
                textCount = len(texts)
                lastTextCharCount = len(texts[-1])
                remainingCharCount = sender.maxLength - lastTextCharCount
                newCharCount = sender.newCharCount(text)
                if textCount==1:
                    message = "Scritto un messaggio: "
                else:
                    message = "Scritti "+str(textCount)+" messaggi: "
                if remainingCharCount==0:
                    message += "messaggio riempito."
                else:
                    message += "mancano "+str(remainingCharCount)+\
                               " caratteri a riempire il messaggio"
                if textCount > 1 and not newCharCount == sender.maxLength:
                    message += "\ne togli "+str(newCharCount)+" caratteri pe"+\
                               "r scrivere un messaggio in meno."                    
            else:
                #2.2- L'utente ha appena scritto un carattere del destinatario
                if self.book.isInContacts(destString):
                    message = "In rubrica con il numero "+\
                              self.book.lookup(destString)
                elif self.isValid(destString):
                    message = "Puoi salvare questo numero in rubrica"

        #aggiorno il label sent sender
        self.updateSentMessages()

        #Aggiorno la grafica
        self.messageLabel.setText(message)
        self.gauge.hide()
        if canSend:
            self.setIcon(getOkData())
        else:
            self.setIcon(getErrorData())
        self.sendButton.setEnabled(canSend)
        self.update()

    def isValid(self, number):
        """Ritorna True se il numero è valido."""
        l = len(number)
        if self.isNumber(number):
            hasCountryCode = number[0]=="+"
            return ((hasCountryCode and (l==12 or l==13)) or
                    (hasCountryCode == False and (l==9 or l==10)))
        else:
            return False

    def isNumber(self, string):
        """Ritorna True se la stringa inserita è un numero oppure
         un numero preceduto da +."""
        if len(string)==0:
            return False
        elif len(string)==1:
            return string.isdigit() or string=="+"
        else:
            return string.isdigit() or \
                   (string[0]=="+" and string[1:].isdigit())

    def gaugeIncrement(self, value):
        """Aumenta il livello della gauge bar durante un invio"""
        self.emit(SIGNAL('gaugeUpdate'), value)

    def userDecodeCaptchaRequest(self, stream):
        """Evento per la decodifica del captcha"""
        self.emit(SIGNAL('userDecodeCaptcha'), stream)

    def updateSentMessages(self):
        """Controlla e aggiorna il numero di SMS inviati da un gestore"""
        self.pm.checkSentSender()
        for i in self.pm.getSenderList():
            if self.pm.isSentSenderAvailable(i):
                self.senderBoxes[i].setText(i + \
                    " ("+self.pm.getSentSender(i)+")")
                self.senderBoxes[i].setToolTip(i + \
                    " ("+self.pm.getSentSender(i)+")")
            else:
                self.senderBoxes[i].setText(i + " (0)")
                self.senderBoxes[i].setToolTip(i + " (0)")

    def deleteButtonEventHandler(self, event):
        """Cancella un contatto dalla rubrica e aggiorna la visualizzazione."""
        destString = unicode(self.destinationComboBox.currentText())
        destIndex = self.destinationComboBox.findText(
                                self.destinationComboBox.currentText())
        try:
            self.book.deleteContact(destString)
        except BookError, be:
            QMessageBox.critical(self, u"Errore", be.__str__())
        self.destinationComboBox.removeItem(destIndex)
        self.destinationComboBox.setEditText("")
        self.destinationComboBoxEventHandler(event)
        self.updateLabel(event)

    def addButtonEventHandler(self, event):
        """Aggiunge un contatto alla rubrica e aggiorna la visualizzazione."""
        text = unicode(self.destinationComboBox.currentText())
        #Due casi:
        if self.isValid(text):
            #L'utente ha immesso un numero, chiedo il nome
            name = u"Inserisci il nome qui"
            cancelled = False
            retried = False
            valid = False
            while (not valid) and (not cancelled):
                message = u"A che nome inserire "+text+" in rubrica?"
                if retried:
                    message += u"\nDevi inserire un nome in lettere."
                name, md = QInputDialog.getText(None, u"Aggiungi in rubrica",
                                                message, QLineEdit.Normal,
                                                name)
                if not md:
                    cancelled = True
                else:
                    name = unicode(name)
                    if self.isNumber(name):
                        retried = True
                    elif name == "":
                        retried = True
                    else:
                        valid = True
                        try:
                            self.book.addContact(name, text)
                        except BookError, be:
                            QMessageBox.critical(self, u"Errore", be.__str__())
                        self.insertDestinationComboBox(name)
                        self.messageTextCtrl.setFocus()
        else:
            #L'utente ha immesso un nome, chiedo il numero
            number = u"Inserisci il numero qui"
            cancelled = False
            retried = False
            valid = False
            while (not valid) and (not cancelled):
                message = u"Qual'è il numero di "+text+"?"
                if retried:
                    message+= u" Sono ammessi solo numeri di cellulare validi."
                number, md = QInputDialog.getText(None, u"Aggiungi in rubrica",
                                                message, QLineEdit.Normal,
                                                number)
                if not md:
                    cancelled = True
                else:
                    number = unicode(number)
                    if not self.isValid(number):
                        retried = True
                    else:
                        valid = True
                        try:
                            self.book.addContact(text, number)
                        except BookError, be:
                            QMessageBox.critical(self, u"Errore", be.__str__())
                        self.insertDestinationComboBox(text)
                        self.messageTextCtrl.setFocus()

        self.destinationComboBoxEventHandler(event)
        self.updateLabel(event)

    def sendButtonEventHandler(self, event):
        """Mostra la barra di avanzamento (gauge) e richiama il metodo
        sendMessage."""
        #evento se Offline è segnato
        if self.check.isChecked():
            if not self.offlineSend:
                y = self.y() + self.height() + 27
                x = self.x()
                self.offlineSend = OfflineSendDialog(self, x,y, self.width())
            self.offlineSend.show()
            data = {"text" : unicode(self.messageTextCtrl.toPlainText()),
                    "dest" : unicode(self.destinationComboBox.currentText()),
                    "sender": self.getSender()}
            self.offlineSend.addSMS("SMS incodato alle "+time.strftime('%X'),
                                    data)
        #altrimenti invio normale
        else:
            #controlla la lista sentsender
            self.pm.checkSentSender()

            #Aggiorna la grafica
            self.bitmap.hide()
            self.messageLabel.hide()
            self.gauge.show()
            self.destinationComboBox.setEnabled(False)
            self.addButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
            self.messageTextCtrl.setEnabled(False)
            self.check.setEnabled(False)
            self.setCursor(self.waitcursor)
            self.senderRadioBox.setEnabled(False)
            self.sendButton.hide()
            self.stopButton.show()
            self.stopButton.setDefault(True)

            self.update()

            info = {}
            info['offline'] = None
            info['sender'] = self.getSender()
            info['dest'] = unicode(self.destinationComboBox.currentText())
            info['text'] = unicode(self.messageTextCtrl.toPlainText())

            #salva il messaggio prima dell'invio
            self.pm.setLastUsed("sender", info['sender'])
            self.pm.setLastUsed("destination", info['dest'])
            self.pm.setLastUsed("message", info['text'])
            try:
                self.pm.writeConfigFile()
            except exceptions.IOError:
                QMessageBox.critical(self, "Errore di salvataggio",
                    u"MoioSMS non può salvare i tuoi dati su disco. \n" +\
                    u"Controlla di poter scrivere sul file:\n" + \
                    self.pm.getConfigFileName())
            #fine salvataggio

            #Manda effettivamente il messaggio.
            #Il messaggio viene inviato in un altro thread
            t = SendMessage(self, info)
            t.start()

    def sentUpdateEventHandler(self, hadError):
        """Gestisce l'aggiornameto della grafica a fine invio di un
        singolo SMS"""
        if hadError:
            self.setIcon(getErrorData())
            self.messageLabel.setText(hadError)
            try:
                import pynotify
                pynotify.init ("MoioSMS")
                n = pynotify.Notification ("MoioSMS",
                    u"Messaggio non inviato tramite " +\
                             self.getSender()+u" a "+\
                             unicode(self.destinationComboBox.currentText()), 
                                     "error")
                n.show()
            except ImportError:
                if self.traymessage: self.traymessage(u"Messaggio NON inviato",
                                 u"Messaggio NON inviato utilizzando " +\
                                 self.getSender()+u" a "+\
                                 unicode(self.destinationComboBox.currentText()),
                                 QSystemTrayIcon.Warning, 2000)
        else:
            self.messageLabel.setText("SMS INVIATO!")
            self.setIcon(getOkData())
            try:
                import pynotify
                pynotify.init ("MoioSMS")
                n = pynotify.Notification ("MoioSMS",
                    u"Messaggio inviato correttamente tramite " +\
                             self.getSender()+u" a "+\
                             unicode(self.destinationComboBox.currentText()), 
                                     "MoioSMS")
                n.show()
            except ImportError:
                if self.traymessage: self.traymessage(u"Messaggio inviato",
                                 u"Messaggio inviato correttamente tramite " +\
                                 self.getSender()+u" a "+\
                                 unicode(self.destinationComboBox.currentText()))
            #cancella il messaggio salvato
            if self.pm.isLastUsedAvailable("message"):
                self.pm.unsetField('lastused','message')

        self.gauge.hide()
        self.bitmap.show()
        self.messageLabel.show()
        self.stopButton.hide()
        self.sendButton.show()
        self.destinationComboBox.setEnabled(True)
        self.addButton.setEnabled(True)
        self.deleteButton.setEnabled(True)
        self.messageTextCtrl.setEnabled(True)
        self.senderRadioBox.setEnabled(True)
        self.check.setEnabled(True)
        self.sendButton.setDefault(True)
        self.updateSentMessages()
        self.setCursor(self.normalcursor)

        self.update()
        #Pronti per un altro messaggio

    def passRequestEventHandler(self, data):
        """Gestisce l'evento di richiesta password durante l'invio di un SMS"""
        md = PasswordErrorDialog(self)
        md.request = data['request']
        md.setMessage(data['message'])
        for i in data['request']:
            md.prepare(i)
            if data.has_key(i): md.setTextValue(i,data[i])
        md.do_layout()
        result = md.exec_()
        if result == 0:
            self.qReq.put(False)
        else:
            dataR = {}
            for i in data['request']:
                dataR[i] = md.getValue(i)
            self.qReq.put(dataR)
            
    def prefButtonEventHandler(self):
        pd = PreferenceDialog(self)
        pd.show()

    def proxyRequestEventHandler(self):
        """Gestisce l'evento di richiesta proxy durante l'invio di un SMS"""
        proxy = ""
        if self.pm.isProxyEnabled():
            proxy = self.pm.getProxy()
        proxy, md  = QInputDialog.getText(self, u"Errore di connessione",
                        "Internet funziona? Se usi un proxy immetti " +\
                        "l'indirizzo qui.\nFormato: http://nomeutente:" +\
                        "password@indirizzo:porta", QLineEdit.Normal, proxy)
        if not md:
            self.qReq.put(md)
        else:
            proxy = unicode(proxy)
            if proxy != "":
                self.pm.setProxy(proxy)
            else:
                self.pm.unsetProxy()
            self.qReq.put('prosegui')

    def logSaveEventHandler(self, senderName, dest, text):
        """Evento di scrittura del file di log"""
        try:
            self.pm.logSMS(senderName, dest, text)
        except exceptions.IOError:
            QMessageBox.critical(self, "Errore di salvataggio",
                u"MoioSMS non può salvare i messaggi inviati " +\
                u"sul disco.\nControlla di poter scrivere sul file:\n" + \
                self.pm.getlogFileName())

    def stopButtonEventHandler(self):
        """Gestisce l'evento di interruzione di invio"""
        Sender.getPlugins()[self.getSender()].stop = True

    def logButtonEventHandler(self, event=None):
        """Gestisce l'evento di visione del file di log"""
        ld = LogViewerDialog(self)
        ld.show()

    def gaugeUpdateEventHandler(self, value):
        """Aumenta il livello della gauge bar durante un invio"""
        if value:
            if value < 0: value = self.gauge.value() - int(1000/(-value))
            else: value = self.gauge.value() + int(1000/value)
        self.gauge.setValue(value)
        self.update()

    def criticalSenderErrorHandler(self, message):
        """Finestra di errore di invio messaggio"""
        QMessageBox.critical(self, u"Errore", message)

    def userDecodeCaptchaHandler(self, stream):
        """Gestore di richiesta di decodifica del captcha dell'utente"""
        cd = CaptchaDialog(self)
        try:
            cd.setImage(stream)
        except: decoded = None
        else:
            result = cd.exec_()
            if result == 1: decoded = cd.getUserInput()
            else: decoded = ''
        self.qCaptcha.put(decoded)

    def systemTrayEventHandler(self, event = QSystemTrayIcon.Trigger):
        """Gestore degli eventi sulla tray icon"""
        if event == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.setWindowState(self.windowState() & ~Qt.WindowActive |
                                    Qt.WindowMinimized)
                self.hide()
                self.mostra.setText("Mostra MoioSMS")
            else:
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized |
                                    Qt.WindowActive)
                self.show()
                self.mostra.setText("Nascondi MoioSMS")
                self.raise_()
                self.activateWindow()
        elif event == Qt.WindowActive:
            self.setWindowState(self.windowState() & ~Qt.WindowActive |
                                Qt.WindowMinimized)
            self.hide()

    def changeEvent(self, event):
        """Gestore dell'evento di abbassamento della finestra a Tray"""
        if self.tray and (event.type() == QEvent.WindowStateChange):
            if event.oldState() == Qt.WindowActive:
                self.emit(SIGNAL('minimizeToTray'), event.oldState())

    def contextMenuEvent(self, event):
        """Mostra in menu constestuale"""
        x = event.globalX()-self.menu.sizeHint().width()
        y = event.globalY()-self.menu.sizeHint().height()
        self.menu.popup(QPoint(x,y))

    def closeEvent(self, event = None):
        """Salva il file di configurazione e termina il programma."""
        if self.offlineSend:
            if not self.offlineSend.listBox.count() == 0:
                result = QMessageBox.question(self,
                u"Vuoi chiudere?",
                u"Attenzione, chiudendo la finestra, i messaggi\n" +
                u"non inviati andranno persi. Chiudere ugualmente?",
                'Si','No')
                if result == 1:
                    event.ignore()
                    return        
        self.tray.hide()
        senderName = self.getSender()
        self.pm.setLastUsed("sender", senderName)
        self.pm.setLastUsed("destination",
                            unicode(self.destinationComboBox.currentText()))

        if not self.pm.isEncryptionSpecified():
            result = QMessageBox.question(self,
                u"Vuoi crittare i tuoi dati sensibili?",
                u"MoioSMS sta per salvare i tuoi dati su disco.\n" +
                u"E' possibile salvare i tuoi dati di accesso ai siti in" +
                u"forma crittata (protetta),\nrendendo più difficile a terzi" +
                u" il loro utilizzo non autorizzato.\n" +
                u"Salvare i dati in forma crittata, però, rende necessario" +
                u"l'inserimento di una Master Password\n ad ogni uso di"+
                u"MoioSMS.\nVuoi salvare salvare in forma crittata" +
                u" tramite Master Password (non sarà possibile cambiare " +
                u"questa scelta)?\n", 'Si','No')
            if result==0:
                pd, result = QInputDialog.getText(self, "Master Password",
                        u"Inserisci la Master Password"+\
                        u" (ti verrà richiesta ad ogni uso di MoioSMS)",
                        QLineEdit.Password)
                pd = unicode(pd)
                self.pm.enableEncryption(pd)
            else:
                self.pm.disableEncryption()
        try:
            self.pm.writeConfigFile()
            self.book.saveBook()
        except exceptions.IOError:
            QMessageBox.critical(self, "Errore di salvataggio",
                u"MoioSMS non può salvare i tuoi dati su disco. \n" +\
                u"Controlla di poter scrivere sul file:\n" + \
                self.pm.getConfigFileName() + "\n" + \
                u"MoioSMS terminerà ora e nessun dato è stato salvato.")
        sys.exit(0)
