# -*- coding: UTF-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class AddressBookDialog(QDialog):
   
    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)
                
        self.addressBox = QTableWidget()
        self.addressBox.setMinimumHeight(300)
        self.addressBox.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.addressBox.setSelectionMode(QAbstractItemView.SingleSelection)
        self.addressBox.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.addressBox.horizontalHeader().setResizeMode(QHeaderView.Stretch)        
        self.addressBox.setAlternatingRowColors(True)
        
        self.removeButton = QPushButton("Cancella")
        self.addButton = QPushButton("Aggiungi")
        self.editButton = QPushButton("Modifica")
        self.saveButton = QPushButton("Salva")        
        self.closeButton = QPushButton("Chiudi")       

        self.mf = mf
        self.edited = False

        self.__set_properties()
        self.__do_layout()

        self.removeButton.setToolTip("Cancella il nome selezionato")
        self.addButton.setToolTip("Aggiungi un nome alla rubrica")
        self.editButton.setToolTip("Modifica il nome selezionato")
        self.saveButton.setToolTip("Salva le modifiche")
        self.closeButton.setToolTip("Chiudi e senza salvare le modifiche")      

        self.connect(self.removeButton, SIGNAL('clicked(bool)'),
                     self.removeButtonEventHandler)
        self.connect(self.addButton, SIGNAL('clicked(bool)'),
                     self.addButtonEventHandler)
        self.connect(self.editButton, SIGNAL('clicked(bool)'),
                     self.editButtonEventHandler)
        self.connect(self.closeButton, SIGNAL('clicked(bool)'),
                     self.close)
        self.connect(self.saveButton, SIGNAL('clicked(bool)'),
                     self.saveButtonEventHandler)        
        self.connect(self.addressBox, SIGNAL('clicked(const QModelIndex&)'),
                     self.activateButtonEventHandler)
        self.connect(self.addressBox, SIGNAL('itemDoubleClicked(QTableWidgetItem *)'),
                     self.editButtonEventHandler)

        self.popolaAddress()
        
        posx = (QDesktopWidget().width()-self.width())/2
        posy = ((QDesktopWidget().height()/3*2)-self.height())/2
        self.move(posx,posy)

    def __set_properties(self):
        self.setWindowTitle("Rubrica")
        self.editButton.setDefault(True)
        self.removeButton.setEnabled(False)
        self.addButton.setEnabled(True)
        self.editButton.setEnabled(False)
        self.saveButton.setEnabled(self.edited)        
        self.closeButton.setEnabled(True)     

    def __do_layout(self):
        vbox = QVBoxLayout()
        
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.addressBox, 1)
        vbox.addLayout(hbox_1)        
        
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(self.removeButton, 0)
        hbox_2.addWidget(self.addButton, 0)
        hbox_2.addWidget(self.editButton, 0)
        hbox_2.addWidget(self.saveButton, 0)        
        hbox_2.addWidget(self.closeButton, 0)
        vbox.addLayout(hbox_2)

        self.setLayout(vbox)
        self.resize(self.minimumSizeHint())        

    def popolaAddress(self):
        self.addressBox.clear()
        self.addressBox.setColumnCount(2)
        rubrica = self.mf.book.getContacts()
        for i,name in enumerate(rubrica.keys()):
            self.addressBox.insertRow(i)
            self.addressBox.setRowHeight(i,20)            
            self.addressBox.setItem(i,0,QTableWidgetItem(name))
            self.addressBox.setItem(i,1,QTableWidgetItem(rubrica[name]))
        self.setAddressLayout()

    def setAddressLayout(self):
        labels = ['']*self.addressBox.rowCount()
        self.addressBox.setVerticalHeaderLabels(labels)        
        self.addressBox.sortItems(0)
        self.addressBox.setHorizontalHeaderLabels(['Nome','Numero'])
        self.addressBox.setColumnWidth(1,100)
        self.addressBox.setColumnWidth(0,199)

    def activateButtonEventHandler(self, index):
        self.removeButton.setEnabled(True)
        self.editButton.setEnabled(True)

    def removeButtonEventHandler(self, event):
        self.addressBox.removeRow(self.addressBox.currentRow())
        self.edited = True
        self.saveButton.setEnabled(self.edited)
        self.removeButton.setEnabled(False)
        self.editButton.setEnabled(False)
        
    def addButtonEventHandler(self, event):
        ade = AddressBookEditDialog(self, self.mf, True)
        ade.exec_()
        
    def editButtonEventHandler(self, event):
        ade = AddressBookEditDialog(self, self.mf, False)
        ade.setName(self.addressBox.item(self.addressBox.currentRow(),0).text())
        ade.setNumber(self.addressBox.item(self.addressBox.currentRow(),1).text())        
        ade.exec_()
            
    def saveButtonEventHandler(self, event):
        if self.edited:
            self.mf.book.clearContacts()
            i = 0
            while i < self.addressBox.rowCount():
                name = unicode(self.addressBox.item(i,0).text())
                number = unicode(self.addressBox.item(i,1).text())
                self.mf.book.addContact(name,number)
                i +=1
        self.edited = False
        self.saveButton.setEnabled(self.edited)        
       
    def closeEvent(self, event):
        """Evento di chiusura della finestra"""
        self.mf.fillContacts()        
        if self.edited:
            result = QMessageBox.question(self,
            u"Vuoi chiudere?",
            u"Attenzione, le modifiche apportate non sono\n" +
            u"state salvate. Chiudere ugualmente?",
            'Si','No')
            if result == 1:
                event.ignore()        

class AddressBookEditDialog(QDialog):
    def __init__(self, ab, mf, new):
        QDialog.__init__(self, mf, mf.defaultFlag)
        self.messageLabel = QLabel("Inserisci il nome da visualizzare e il"+\
                                   " numero")
        self.nameText = QLineEdit("Nome")
        self.numberText = QLineEdit("Numero")        
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Chiudi")

        self.__set_properties()
        self.__do_layout()

        self.mf = mf
        self.ab = ab
        self.new = new

        self.connect(self.okButton, SIGNAL('clicked(bool)'),
                     self.okButtonEventHandler)
        self.connect(self.cancelButton, SIGNAL('clicked(bool)'),
                     self.cancelButtonEventHandler)        

    def __set_properties(self):
        self.setWindowTitle("Inserisci i dati richiesti")
        self.okButton.setDefault(True)

    def __do_layout(self):
        vbox = QVBoxLayout()
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.messageLabel, 0)
        hbox_1.addStretch(1)
        vbox.addLayout(hbox_1)
        vbox.addStretch(1)
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(self.nameText, 0)
        hbox_2.addStretch(1)
        hbox_2.addWidget(self.numberText, 0)        
        vbox.addLayout(hbox_2)
        vbox.addStretch(1)
        hbox_3 = QHBoxLayout()
        hbox_3.addStretch(1)
        hbox_3.addWidget(self.okButton, 0)
        hbox_3.addStretch(1)        
        hbox_3.addWidget(self.cancelButton, 0)        
        hbox_3.addStretch(1)
        vbox.addLayout(hbox_3)

        self.setLayout(vbox)
        self.resize(self.minimumSizeHint())

    def okButtonEventHandler(self, event):
        if self.nameText.text() and \
           not self.mf.isNumber(unicode(self.nameText.text())) and \
           self.mf.isValid(unicode(self.numberText.text())):
            i = 0
            exists = False
            while i < self.ab.addressBox.rowCount():
                name = unicode(self.ab.addressBox.item(i,0).text())
                if name == self.nameText.text():
                    exists = True
                    row = i
                i +=1
            if not exists:
                if self.new:
                    row = self.ab.addressBox.rowCount()
                    self.ab.addressBox.insertRow(row)
                    self.ab.addressBox.setRowHeight(row,20)
                    self.ab.addressBox.setItem(row, 0, QTableWidgetItem())
                    self.ab.addressBox.setItem(row, 1, QTableWidgetItem())
                else:
                    row = self.ab.addressBox.currentRow()                    
            item = self.ab.addressBox.item(row, 0)
            self.ab.addressBox.item(row, 0).setText(self.nameText.text())
            self.ab.addressBox.item(row, 1).setText(self.numberText.text())
            self.ab.setAddressLayout()
            row = self.ab.addressBox.row(item)
            self.ab.addressBox.selectionModel().clearSelection()
            self.ab.addressBox.selectRow(row)
            self.ab.addressBox.scrollToItem(item)
            self.ab.edited = True
            self.ab.saveButton.setEnabled(self.ab.edited)            
            self.done(1)
        else: self.messageLabel.setText("Inserisci il nome da visualizzare "+\
                                        "e il numero\n\n" +\
                                        "Dati inseriti non validi!\n")

    def cancelButtonEventHandler(self):
        self.done(1)

    def setName(self, name):
        self.nameText.setText(name)

    def setNumber(self, number):
        self.numberText.setText(number)
