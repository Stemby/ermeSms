# -*- coding: UTF-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from moio.plugins.uis.SendMessage import SendMessage, SendDelayed
from moio.plugins.uis.Icons import getOkData, getErrorData

DESTROLE = 32
SENDERROLE = 33
TEXTROLE = 34

class OfflineSendDialog(QDialog):

    updateTimer = QTimer()
    sendTimer = QTimer()
    remainTime = 0
    """Dati per i timer"""
    
    def __init__(self, mf, posx, posy, sizex):
        QDialog.__init__(self, mf, mf.defaultFlag)
                
        self.listBox = QListWidget()
        self.listBox.setMinimumHeight(70)
        self.listBox.setSelectionMode(QAbstractItemView.SingleSelection)  
        
        self.removeButton = QPushButton("Rimuovi SMS")
        self.destLabel = QLabel("Destinatario: ")
        self.destText = QLineEdit("")
        self.destText.setReadOnly(True)
        self.senderLabel = QLabel("Sender: ")
        self.senderText = QLineEdit("")
        self.senderText.setReadOnly(True)        
        self.messageLabel = QLabel("Messaggio: ")
        self.messageText = QTextEdit("")
        self.messageText.setReadOnly(True)        
        self.messageText.setMinimumHeight(70)
        self.sendButton = QPushButton("Invia gli SMS in coda")
        self.delayedSend = QGroupBox("Invio a orario definito:")
        self.delayedSend.setCheckable(True)
        self.delayedSend.setChecked(False)
        self.delayedButton = QPushButton("Start Timer")
        self.closeButton = QPushButton("Chiudi")
        self.sendTime = QDateTimeEdit(QTime.currentTime())
        self.setMinimumWidth(sizex)
        self.__set_properties()
        self.__do_layout()

        self.mf = mf

        self.sendButton.setToolTip("Invia gli SMS nella lista")
        self.removeButton.setToolTip("Rimuove l'SMS selezionato")
        self.destText.setToolTip("Destinatario (non modificabile)")
        self.senderText.setToolTip("Gestore (non modificabile)")
        self.messageText.setToolTip("Messaggio (non modificabile)")
        self.delayedButton.setToolTip("Premi per far partire il timer " +\
                                      "dell'invio")        

        self.connect(self.sendButton, SIGNAL('clicked(bool)'),
                     self.sendButtonEventHandler)
        self.connect(self.removeButton, SIGNAL('clicked(bool)'),
                     self.removeButtonEventHandler)
        self.connect(self.delayedButton, SIGNAL('clicked(bool)'),
                     self.delayedButtonEventHandler)        
        self.connect(self.listBox,
             SIGNAL('currentItemChanged(QListWidgetItem *,QListWidgetItem *)'),
                     self.updateEventHandler)
        self.connect(self.listBox,
                     SIGNAL('itemClicked (QListWidgetItem *)'),
                     self.updateEventHandler)        
        self.connect(self.delayedSend, SIGNAL('toggled(bool)'),
                     self.activateDelayed)        
        self.connect(self, SIGNAL('sentOfflineUpdate'),
                     self.sentOfflineUpdateEventHandler)
        self.connect(self, SIGNAL('singleSent'),
                     self.trayBarMessageUpdate)
        
        self.connect(self.updateTimer, SIGNAL('timeout()'),
                     self.updateDelayedButtonText)
        self.connect(self.sendTimer, SIGNAL('timeout()'),
                     self.sendTimerTimeout)          
        self.connect(self.closeButton, SIGNAL('clicked(bool)'),
                     self.closeEvent)

        self.move(posx,posy)

    def __set_properties(self):
        self.setWindowTitle("Lista degli SMS in Coda")
        self.removeButton.setEnabled(False)
        self.sendButton.setEnabled(False)
        self.delayedSend.setEnabled(False)
        self.sendButton.setDefault(True)

    def __do_layout(self):

        vbox = QVBoxLayout()
        
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.listBox, 1)
        hbox_1.addWidget(self.removeButton, 0)
        vbox.addLayout(hbox_1)        
        
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(self.destLabel, 0)
        hbox_2.addWidget(self.destText, 1)
        hbox_2.addWidget(self.senderLabel, 0)
        hbox_2.addWidget(self.senderText, 1)        
        vbox.addLayout(hbox_2)

        hbox_3 = QHBoxLayout()
        hbox_3.addWidget(self.messageLabel, 0)
        hbox_3.addWidget(self.messageText, 1)        
        vbox.addLayout(hbox_3)
        
        hbox_4 = QHBoxLayout()
        hbox_4.addStretch(1)
        hbox_4.addWidget(self.sendButton, 0)
        hbox_4.addStretch(1)
        hbox_4.addWidget(self.closeButton, 0)
        hbox_4.addStretch(1)
        delayedBox = QHBoxLayout()
        delayedBox.addWidget(self.sendTime, 1)
        delayedBox.addWidget(self.delayedButton, 0)        
        self.delayedSend.setLayout(delayedBox)
        hbox_4.addWidget(self.delayedSend, 3)
        vbox.addLayout(hbox_4)

        self.setLayout(vbox)
        self.resize(self.minimumSizeHint())

    def sendButtonEventHandler(self, event = None):
        """Gestisce il preinvio dei messaggi in coda"""
        self.mf.pm.checkSentSender()

        self.mf.bitmap.hide()
        self.mf.messageLabel.hide()
        self.mf.gauge.show()
        self.mf.destinationComboBox.setEnabled(False)
        self.mf.addButton.setEnabled(False)
        self.mf.deleteButton.setEnabled(False)
        self.mf.messageTextCtrl.setEnabled(False)
        self.mf.check.setEnabled(False)
        self.mf.setCursor(self.mf.waitcursor)
        self.mf.senderRadioBox.setEnabled(False)           
        self.mf.sendButton.setEnabled(False)
        
        self.delayedSend.setEnabled(False)
        self.sendButton.setEnabled(False)
        self.removeButton.setEnabled(False)
        self.listBox.setEnabled(False)
        
        i = 0
        data = []
        while i < self.listBox.count():
            item = self.listBox.item(i)
            itemdata = {
                'dest': unicode(item.data(DESTROLE).toString()),
                'text': unicode(item.data(TEXTROLE).toString()),
                'sender': unicode(item.data(SENDERROLE).toString())
                }                        
            data.append((i,itemdata))
            i += 1
        t = SendDelayed(self.mf, data)
        t.start()

    def activateDelayed(self, state):
        """Attiva e disattiva il bottone di invio"""
        self.sendButton.setEnabled(not state)
        self.stopTimer()

    def startTimer(self):
        """Avvia i Timer"""        
        self.remainTime = QTime.currentTime().msecsTo(self.sendTime.time())
        if self.remainTime < 0: self.remainTime += 86400000
        self.delayedButton.setText("Stop Timer")
        self.sendTime.setEnabled(False)        
        self.sendTimer.start(self.remainTime)
        self.updateTimer.start(1000)
            
    def stopTimer(self):
        """Blocca i Timer"""
        self.sendTimer.stop()
        self.updateTimer.stop()
        self.sendTime.setEnabled(True)
        self.delayedButton.setToolTip("Premi per far partire il timer " +\
                                      "dell'invio")
        self.delayedButton.setText("Start Timer")

    def delayedButtonEventHandler(self, event):
        """Evento di gestione del pulsate del timer"""
        if not self.sendTimer.isActive():
            self.startTimer()
        else:
            self.stopTimer()

    def sendTimerTimeout(self):
        """Avvia l'invio dei messaggi in coda"""
        self.stopTimer()
        self.sendButtonEventHandler()

    def updateDelayedButtonText(self):
        """Aggiorna il valore nel ToolTip"""
        self.remainTime -= 1000
        if self.remainTime > 1000:
            ore = self.remainTime // 3600000
            minuti = (self.remainTime-ore*3600000) // 60000
            secondi = (self.remainTime-ore*3600000-minuti*60000) // 1000
            self.delayedButton.setToolTip("Mancano "+str(ore)+"h, "+\
                                str(minuti)+"m, "+str(secondi)+"s")

    def sentOfflineUpdateEventHandler(self, result):
        """Gestisce il risultato dell'invio dei messaggi in coda"""
        close = None
        errors = []
        remove = []
        for i,hadError,data in result:
            if hadError:
                errors.append(u"Messaggio diretto a " + data["dest"] + \
                              u" utilizzando "+data["sender"])
            else: remove.append(i)
        remove.sort(reverse=True)
        for i in remove:
            self.listBox.takeItem(i)
        if len(errors) == 0:
            self.mf.messageLabel.setText("SMS INVIATI!")            
            self.mf.setIcon(getOkData())
            QMessageBox.information(self, "Messaggi Inviati",
                                    u"Tutti i messaggi in coda sono stati\n"+\
                                    u"inviati correttamente")
            close = True
        else:
            message = u"Si è verificato un errore nell'invio di alcuni " +\
                      u"messaggi:\n"
            for error in errors:
                message += error+u"\n"
            self.mf.messageLabel.setText("Alcuni SMS non sono stati inviati.")                
            self.mf.setIcon(getErrorData())
            QMessageBox.warning(self, "Errore", message)

        self.mf.gauge.hide()
        self.mf.bitmap.show()
        self.mf.messageLabel.show()        
        self.mf.sendButton.setEnabled(True)
        self.mf.destinationComboBox.setEnabled(True)
        self.mf.addButton.setEnabled(True)
        self.mf.deleteButton.setEnabled(True)
        self.mf.messageTextCtrl.setEnabled(True)
        self.mf.senderRadioBox.setEnabled(True)
        self.mf.check.setEnabled(True)
        self.mf.sendButton.setDefault(True)
        self.mf.updateSentMessages()
        self.mf.setCursor(self.mf.normalcursor)

        self.delayedSend.setEnabled(True)
        self.sendButton.setEnabled(not self.delayedSend.isChecked())
        self.removeButton.setEnabled(True)
        self.listBox.setEnabled(True)        
        if close: self.done(1)

    def closeEvent(self, event):
        """Resetta il riferimento e nasconde la dialog"""
        if not self.listBox.count() == 0:
            result = QMessageBox.question(self,
            u"Vuoi chiudere?",
            u"Attenzione, chiudendo la finestra, i messaggi\n" +
            u"non inviati andranno persi. Chiudere ugualmente?",
            'Si','No')
            if result == 1:
                event.ignore()
                return
        self.stopTimer()
        self.listBox.clear()
        self.destText.setText('')
        self.senderText.setText('')
        self.messageText.setText('')

    def removeButtonEventHandler(self, event):
        """Toglie dalla lista dei messaggi quello selezionato"""
        self.listBox.takeItem(self.listBox.currentRow())
        if self.listBox.currentItem():
            self.listBox.setItemSelected(self.listBox.currentItem(),False)  
        self.destText.setText("")
        self.senderText.setText("")
        self.messageText.setText("")        
        self.removeButton.setEnabled(False)
        if self.listBox.count() == 0:
            self.sendButton.setEnabled(False)
            self.delayedSend.setEnabled(False)            

    def updateEventHandler(self, item, previous=None):
        """Aggiorna con il messaggio selezionato"""
        if item:
            self.destText.setText(item.data(DESTROLE).toString())
            self.messageText.setText(item.data(TEXTROLE).toString())
            self.senderText.setText(item.data(SENDERROLE).toString())            
            self.removeButton.setEnabled(True)
        else: self.removeButton.setEnabled(False)
        
    def addSMS(self,title,data):
        """Aggiunge l'SMS compilato nel MainFrame alla lista da inviare"""
        item = QListWidgetItem(title)
        self.listBox.addItem(item)
        item.setData(DESTROLE, QVariant(data['dest']))
        item.setData(SENDERROLE, QVariant(data['sender']))
        item.setData(TEXTROLE, QVariant(data['text']))         
        self.delayedSend.setEnabled(True)
        self.sendButton.setEnabled(not self.delayedSend.isChecked())

    def trayBarMessageUpdate(self, hadError, data):
        """Mostra un messaggio in prossimità dell'icona nella traybar"""
        if self.mf.traymessage:
            if hadError:
                self.mf.traymessage(u"Messaggio NON inviato",
                    u"Messaggio NON inviato utilizzando " +\
                    data['sender']+u"\ndiretto a "+data['dest'],
                    QSystemTrayIcon.Warning, 2000)            
            else:  
                self.mf.traymessage(u"Messaggio inviato",
                    u"Messaggio inviato correttamente tramite " +\
                    data['sender']+u"\ndiretto a "+data['dest'])
