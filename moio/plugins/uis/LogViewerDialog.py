# -*- coding: UTF-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import re
import exceptions
import os

REGEX = ['\*', '\.', '\$', '\^', '\+', '\{', '\}',
         '\|', '\]', '\[', '\(', '\)', '\^', '\?']

class LogViewerDialog(QDialog):

    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)

        self.sortBox = QGroupBox("Ordina per:")
        self.sortDate = QRadioButton("Data")
        self.sortDate.setChecked(True)
        self.sortDest = QRadioButton("Destinatario")
        self.sortSender = QRadioButton("Gestore")
        self.countText = QLabel('0 messaggi')
        self.selectedCountText = QLabel('0 messaggi selezionati')        
        self.findString = QLineEdit("Inserisci il testo da ricercare")
        self.saveButton = QPushButton("Salva")
        self.reloadButton = QPushButton("Ricarica")        
        self.closeButton = QPushButton("Chiudi")
        self.clearButton = QPushButton("Svuota")

        self.mouseColumn = None
        self.mouseItem = None
        self.color = QColor(Qt.transparent)        

        self.logTree = QTreeWidget()
        self.logTree.setHeaderHidden(True)      
        self.logTree.setAlternatingRowColors(True)
        self.logTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.logTree.setExpandsOnDoubleClick(False)
        self.logTree.header().setResizeMode(QHeaderView.ResizeToContents)
        self.logTree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.logTree.setSelectionMode(QAbstractItemView.ExtendedSelection)        
        self.connect(self.logTree,
                     SIGNAL('customContextMenuRequested(const QPoint&)'),
                     self.customContextMenu)
        self.logTree.setMinimumHeight(300)
        self.setMinimumWidth(600)             

        self.__set_properties()
        self.__do_layout()

        self.mf = mf

        self.menu = QMenu("MoioSMS", self)
        self.delLine = self.menu.addAction('Elimina riga', self.deleteItem)
        self.menu.addSeparator()
        self.menu.addAction('Espandi selezione', self.expandToText)
        self.menu.addAction('Espandi tutti', self.expandAll)
        self.menu.addAction('Collassa tutti', self.collapseAll)
        self.menu.addSeparator()
        self.copyCell = self.menu.addAction('Copia cella', self.copiaCella)
        self.connect(self.menu, SIGNAL('aboutToHide()'), self.restoreColor)        
        
        self.closeButton.setToolTip("Chiude il registro (senza salvare)")
        self.saveButton.setToolTip("Salva le modifiche apportate al "+\
                                   "registro")
        self.reloadButton.setToolTip("Ricarica i messaggi salvati nel file "+\
                                     "del registro")
        self.clearButton.setToolTip("Svuota il registro")
        self.findString.setToolTip("Inserisci la/le parola/e che vuoi "+\
                                   "ricercare")

        self.primary = 'data'
        self.subprimary = 'dest'
        self.secondary = 'sender'
        self.subsubprimary = 'ora'
        self.reloadButtonHandler()

        self.connect(self.findString, SIGNAL('textChanged(const QString&)'),
                 self.findTextHandler)
        self.connect(self.saveButton, SIGNAL('clicked(bool)'),
                 self.saveButtonHandler)
        self.connect(self.clearButton, SIGNAL('clicked(bool)'),
                 self.clearButtonHandler)
        self.connect(self.reloadButton, SIGNAL('clicked(bool)'),
                 self.reloadButtonHandler)        
        self.connect(self.closeButton, SIGNAL('clicked(bool)'),
                 self, SLOT('close()'))
        self.connect(self.sortDate, SIGNAL('clicked(bool)'),
                 self.sortDateHandler)
        self.connect(self.sortDest, SIGNAL('clicked(bool)'),
                 self.sortDestHandler)
        self.connect(self.sortSender, SIGNAL('clicked(bool)'),
                 self.sortSenderHandler)
        self.connect(self.logTree, SIGNAL('itemExpanded(QTreeWidgetItem *)'),
                     self.fitColumnSize)
        self.connect(self.logTree, SIGNAL('itemCollapsed(QTreeWidgetItem *)'),
                     self.fitColumnSize)
        self.connect(self.logTree,
                     SIGNAL('itemClicked(QTreeWidgetItem *,int)'),
                     self.treeClickHandler)
        self.connect(self.logTree,
                     SIGNAL('itemSelectionChanged()'),self.treeSelectionUpdate)
        
        posx = (QDesktopWidget().width()-self.width())/2
        posy = ((QDesktopWidget().height()/3*2)-self.height())/2
        self.move(posx,posy)           
        
    def __set_properties(self):
        self.setWindowTitle("Lista degli SMS inviati")
        self.findString.setFocus()
        self.closeButton.setDefault(True)

    def __do_layout(self):

        vbox = QVBoxLayout()
        
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.sortDate, 0)
        hbox_1.addStretch(1)        
        hbox_1.addWidget(self.sortDest, 0)
        hbox_1.addStretch(1)        
        hbox_1.addWidget(self.sortSender, 0)        
        self.sortBox.setLayout(hbox_1)
        vbox.addWidget(self.sortBox, 0)

        hbox_3 = QHBoxLayout()
        hbox_3.addWidget(self.countText, 0)
        hbox_3.addSpacing(10)
        hbox_3.addWidget(self.selectedCountText, 0)
        hbox_3.addSpacing(10)        
        searchBox = QGroupBox("Ricerca")
        search = QHBoxLayout()
        search.addWidget(self.findString, 1)
        searchBox.setLayout(search)
        hbox_3.addWidget(searchBox, 1)        
        vbox.addLayout(hbox_3, 0)
        
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(self.logTree, 1)
        vbox.addLayout(hbox_2, 1)

        hbox_4 = QHBoxLayout()
        hbox_4.addWidget(self.clearButton, 0)        
        hbox_4.addStretch(1)
        hbox_4.addWidget(self.reloadButton, 0)        
        hbox_4.addStretch(1)        
        hbox_4.addWidget(self.saveButton, 0)
        hbox_4.addStretch(1)
        hbox_4.addWidget(self.closeButton, 0)
        vbox.addLayout(hbox_4, 0)        

        self.setLayout(vbox)
        self.resize(self.sizeHint())       

    def customContextMenu(self, pos):
        """Evento di gestione per il menu contestuale del logTree"""
        if pos.x() < self.logTree.columnWidth(0): self.mouseColumn = 0
        elif pos.x() < (self.logTree.columnWidth(1)+\
                        self.logTree.columnWidth(0)): self.mouseColumn = 1
        else: self.mouseColumn = 2
        self.mouseItem = self.logTree.itemAt(pos)
        if self.mouseItem:
            self.logTree.setCurrentItem(self.mouseItem)
            self.mouseItem.setBackgroundColor(self.mouseColumn,QColor(
                                                                Qt.darkGray))
        self.delLine.setVisible(self.mouseItem != None)
        self.copyCell.setVisible(self.mouseItem != None)
        x = self.logTree.mapToGlobal(pos).x()-self.menu.sizeHint().width()
        y = self.logTree.mapToGlobal(pos).y()-self.menu.sizeHint().height()
        self.menu.popup(QPoint(x,y))

    def restoreColor(self):
        """Evento per ripristinare il colore modificato dal click"""
        if self.mouseItem:
            self.mouseItem.setBackgroundColor(self.mouseColumn,QColor(
                                                            Qt.transparent))        

    def encodeData(self, data):
        """Restituisce la data in formato yymmdd da dd/mm/yy"""
        data = unicode(data)
        if re.match('\d\d/\d\d/\d\d',data):
            data = (data[6:8]+data[3:5]+data[0:2])
        return data

    def keyPressEvent(self, event):
        """Gestore evento di pressione Canc o Del con il logTree"""
        if (event.key()==Qt.Key_Delete or event.key()==Qt.Key_Backspace) and\
            self.logTree.currentItem():
            self.mouseItem = self.logTree.currentItem()
            self.deleteItem()            

    def deleteItem(self):
        """Cancella gli oggetti selezionati nel logTree"""
        self.edited = True        
        for item in self.logTree.selectedItems():
            if item.parent():
                #se è subsubprimary
                if item.parent().parent():
                    top = self.encodeData(item.parent().parent().text(0))
                    sub = self.encodeData(item.parent().text(0))
                    text = self.encodeData(item.text(2))
                    for i in self.messages.keys():
                        if self.messages[i][self.primary] == unicode(top) and \
                           self.messages[i][self.subprimary] == unicode(sub) and \
                           self.messages[i]['text'] == unicode(text):
                            del self.messages[i]
                #se è subprimary
                else:
                    top = self.encodeData(item.parent().text(0))
                    sub = self.encodeData(item.text(0))               
                    for i in self.messages.keys():
                        if self.messages[i][self.primary] == unicode(top) and \
                           self.messages[i][self.subprimary] == unicode(sub):
                            del self.messages[i]
                item.parent().removeChild(item)
            #se è primary
            else:
                top = self.encodeData(item.text(0))
                self.logTree.takeTopLevelItem(
                                self.logTree.indexOfTopLevelItem(item))            
                for i in self.messages.keys():
                    if self.messages[i][self.primary] == unicode(top):
                        del self.messages[i]            
        self.deleteNoChildren()
        if self.findString.text()==QString("") or \
           self.findString.text()==QString("Inserisci il testo da ricercare"):
            self.countVisible()
        else: self.findTextHandler(self.findString.text())

    def copiaCella(self):
        """Copia nella clipboard la cella selezionata"""
        QApplication.clipboard().setText(
                        self.mouseItem.data(self.mouseColumn,0).toString())

    def expandAll(self):
        """Espande e adatta le colonne alla grandezza adatta"""
        self.logTree.expandAll()
        self.fitColumnSize()

    def expandToText(self):
        """Espande e adatta le colonne alla grandezza adatta"""
        item = self.mouseItem
        if item:
            if item.text(2): return
            i = 0
            if not item.isExpanded(): self.logTree.expandItem(item)
            while item.child(i):
                self.logTree.expandItem(item.child(i))
                i += 1
            self.fitColumnSize()

    def collapseAll(self):
        """Collassa e adatta le colonne alla grandezza adatta"""        
        self.logTree.collapseAll()
        self.fitColumnSize()        

    def fitColumnSize(self, item = None):
        """Adatta le colonne alla grandezza adatta"""
        self.logTree.resizeColumnToContents(0)
        self.logTree.resizeColumnToContents(1)
        x = (self.width()-100-self.logTree.columnWidth(0)-\
             self.logTree.columnWidth(1))
        self.logTree.setColumnWidth(2, x)
        if item: self.logTree.scrollToItem(self.logTree.itemBelow(item))    
            
    def sortDateHandler(self, event):
        """Imposta le variabili per ordinare per data e riordina"""
        self.findString.setText("Inserisci il testo da ricercare")
        self.primary = 'data'
        self.subprimary = 'dest'
        self.subsubprimary = 'ora'          
        self.secondary = 'sender'      
        self.popolaTree()
        
    def sortDestHandler(self, event):
        """Imposta le variabili per ordinare per destinatario e riordina"""        
        self.findString.setText("Inserisci il testo da ricercare")        
        self.primary = 'dest'
        self.subprimary = 'data'
        self.subsubprimary = 'ora'          
        self.secondary = 'sender'      
        self.popolaTree()
        
    def sortSenderHandler(self, event):
        """Imposta le variabili per ordinare per sender e riordina"""      
        self.findString.setText("Inserisci il testo da ricercare")        
        self.primary = 'sender'
        self.subprimary = 'dest'
        self.subsubprimary = 'data'         
        self.secondary = 'ora'       
        self.popolaTree()

    def findTextHandler(self, text):
        """Cerca unao + stringhe nei messaggi"""
        value = unicode(text).lower()
        if value == "inserisci il testo da ricercare": value = ""
        value = re.sub('\\\\','\\\\\\\\',value)        
        for i in REGEX:
            value = re.sub(i,i,value)
        i = 0
        values = value.split(' ')
        iterator = QTreeWidgetItemIterator(self.logTree,
                                           QTreeWidgetItemIterator.All)
        while iterator.value():
            item = iterator.value()
            if item.text(2):
                text = unicode(item.text(2))
                hide = False
                for word in values:
                    if not re.search(word,text): hide = True
                if not hide:
                    item.parent().parent().setHidden(False)
                    item.parent().setHidden(False)
                item.setHidden(hide)
            else: item.setHidden(True)
            iterator.__iadd__(1)              
        if not value: self.logTree.collapseAll()
        else: self.logTree.expandAll()
        self.fitColumnSize()
        self.countVisible()

    def sortTree(self, lista):
        """Ordina gli elementi nella lista in ingresso"""
        finallist = None
        if not lista: return []
        if type(lista[0]) == str or type(lista[0]) == unicode:
            if 'item' in lista: lista.remove('item')
            if len(lista)==0: return []
            if (re.match('\d\d:\d\d:\d\d',lista[0]) and (len(lista[0]) == 8)) or \
               (re.match('\d\d\d\d\d\d',lista[0]) and (len(lista[0]) == 6)):
                finallist = sorted(lista, reverse=True)      
            elif re.search('#\d+',str(lista)):
                finallist = sorted(lista,
                    cmp=lambda x,y: +2*(x[0]=='#')-2*(y[0]=='#')+cmp(x,y))
            else:
                finallist = sorted(lista)
        else:
            link = {}            
            for i in lista:
                link[(i.text(0),i.text(1))] = i
            if self.subsubprimary == 'data' and self.secondary == 'ora':
                sortcmp = lambda x,y: (-2*cmp(x[0],y[0]))-cmp(x[1],y[1])
            elif self.subsubprimary == 'ora':
                sortcmp = lambda x,y: (-2*cmp(x[0],y[0]))+cmp(x[1],y[1])
            else: sortcmp=None
            elenco = sorted(link.keys(), cmp=sortcmp)
            finallist = []
            for i in elenco:
                finallist.append(link[(i)])
        return finallist

    def treeClickHandler(self, item, column):
        """Gestisce l'espansione e collasso degli elementi nel logTree"""
        if not item.isExpanded(): self.logTree.expandItem(item)
        else: self.logTree.collapseItem(item)

    def treeSelectionUpdate(self):
        """Aggiorna la label per il conto dei messaggi selezionati"""
        count = 0
        for item in self.logTree.selectedItems():
            if item.parent():
                if item.parent().parent():
                    if not item.parent().parent().isSelected() and \
                       not item.parent().isSelected():
                        count += 1
                else:
                    if not item.parent().isSelected():
                        count += item.childCount()
            else:
                i = 0
                while item.child(i):
                    count += item.child(i).childCount()
                    i+=1
        self.selectedCountText.setText(str(count)+' messaggi selezionati')

    def saveButtonHandler(self):
        """Evento di gestione del salvataggio del registro"""
        self.edited = False
        rubrica = self.mf.book.getContacts()        
        try:        
            f = open(self.mf.pm.getlogFileName(),'w')
            n=0
            messaggio = {}
            for i in self.messages.keys():
                data = self.messages[i]['data']
                if self.messages[i]['dest'][0] == '#':
                    dest = self.messages[i]['dest'][1:]
                elif rubrica.has_key(self.messages[i]['dest']):
                    dest = rubrica[self.messages[i]['dest']]
                else: dest = self.messages[i]['dest']
                sender = self.messages[i]['sender']
                ora = self.messages[i]['ora']
                text = self.messages[i]['text']
                logdata = 'data='+data+'\nora='+ora+'\nsender='+sender+\
                          '\ndest='+dest+'\ntext='+text+'\n---\n'      
                f.write(logdata)
            f.close()
        except exceptions.IOError:
            QMessageBox.critical(self, "Errore di salvataggio",
                u"MoioSMS non può salvare i messaggi inviati " +\
                u"sul disco.\nControlla di poter scrivere sul file:\n" + \
                self.mf.pm.getlogFileName())            

    def clearButtonHandler(self):
        """Evento di gestione della cancellazione del registro"""
        self.edited = True
        self.logTree.clear()
        self.messages = {}
        self.countText.setText('0 Messaggi')

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

    def decodeData(self):
        """Rinomina le date nell'albero per renderle comprensibili"""
        if 'data' == self.subsubprimary: datacolumn = 0
        elif 'data' == self.secondary: datacolumn = 1
        elif 'data' == self.subprimary: datacolumn = 2
        else: datacolumn = 3
        iterator = QTreeWidgetItemIterator(self.logTree,
                                           QTreeWidgetItemIterator.All)
        while iterator.value():
            item = iterator.value()
            modifica = False
            if item.text(2) and (datacolumn == 0 or datacolumn == 1):
                column = datacolumn
                modifica = True
            elif item.parent() and not item.text(2) and datacolumn == 2:
                column = 0
                modifica = True
            elif not item.parent() and datacolumn == 3:
                column = 0
                modifica = True
            if modifica:
                olddata = unicode(item.text(column))
                newdata = (olddata[4:6]+'/'+olddata[2:4]+'/'+olddata[0:2])                
                item.setText(column,newdata)
            iterator.__iadd__(1)

    def deleteNoChildren(self):
        """Cancella i padri senza figli"""
        iterator = QTreeWidgetItemIterator(self.logTree,
                                           QTreeWidgetItemIterator.NoChildren)
        while iterator.value():
            item = iterator.value()
            if not item.text(2):
                if item.parent().childCount() == 1:
                    self.logTree.takeTopLevelItem(
                        self.logTree.indexOfTopLevelItem(item.parent()))
                else: item.parent().removeChild(item)
            iterator.__iadd__(1)   

    def countVisible(self):
        """Conta gli elementi visibili e aggiorna la label"""
        count = 0
        iterator = QTreeWidgetItemIterator(self.logTree,
                                           QTreeWidgetItemIterator.NotHidden)
        while iterator.value():
            if iterator.value().text(2): count += 1
            iterator.__iadd__(1)
        self.countText.setText(str(count)+" messaggi")

    def reloadButtonHandler(self):
        """Evento di gestione del ricaricamento dal file di log"""
        self.edited = False        
        self.findString.setText("Inserisci il testo da ricercare")
        if not os.path.isfile(self.mf.pm.getlogFileName()):
            try:
                if not os.path.isdir(self.mf.pm.configDirName):
                    os.makedirs(self.mf.pm.configDirName)                
                f = open(self.mf.pm.getlogFileName(),'w')
                f.close()
            except exceptions.IOError:
                QMessageBox.critical(self, "Errore di salvataggio",
                    u"MoioSMS non può salvare i messaggi inviati " +\
                    u"sul disco.\nControlla di poter scrivere sul file:\n" + \
                    self.mf.pm.getlogFileName())
                self.done(1)
            else: self.loadMessages()
        else:
            self.loadMessages()

    def loadMessages(self):
        """Carica i dati dal file di log al programma"""
        oldrubrica = self.mf.book.getContacts()
        rubrica = {}
        for i in oldrubrica.items():
            rubrica[i[1]] = i[0]            
        f = open(self.mf.pm.getlogFileName(),'r')
        n=0
        messaggio = {}
        self.messages = {}
        for i in f.readlines():
            if i[-1:] == '\n':
                i = i[:-1]
            if i[:5] == 'data=':
                messaggio['data']=i[5:]
            elif i[:4] == 'ora=':
                messaggio['ora']=i[4:]           
            elif i[:7] == 'sender=':
                messaggio['sender']=i[7:]
            elif i[:5] == 'dest=':
                if i[5:].isdigit():
                    if rubrica.has_key(i[5:]):
                        messaggio['dest'] = rubrica[i[5:]]
                    else: messaggio['dest'] = '#'+ i[5:]
                else: messaggio['dest'] = i[5:]
            elif i[:5] == 'text=':
                messaggio['text']=i[5:]
            elif i == '---':
                if messaggio.has_key('data') and \
                   messaggio.has_key('dest') and \
                   messaggio.has_key('sender') and \
                   messaggio.has_key('text') and \
                   messaggio.has_key('ora'):
                    self.messages[n] = messaggio
                    n += 1
                messaggio = {}
        f.close()
        self.popolaTree()
        
    def popolaTree(self):
        """Crea gli elementi del logTree e lo disegna"""
        self.logTree.clear()
        self.logTree.setColumnCount(3)
        tree = {}
        for i in self.messages.keys():
            thistop = self.messages[i][self.primary]
            thissub = self.messages[i][self.subprimary]
            if not tree.has_key(thistop):
                tree[thistop] = {}
                tree[thistop]['item'] = QTreeWidgetItem()
                tree[thistop]['item'].setText(0, thistop)
                tree[thistop]['item'].setBackgroundColor(0, self.color)
            if not tree[thistop].has_key(thissub):
                tree[thistop][thissub] = {}
                tree[thistop][thissub]['item'] = QTreeWidgetItem()
                tree[thistop][thissub]['item'].setText(0, thissub)
                tree[thistop][thissub]['item'].setBackgroundColor(0,self.color)
            if not tree[thistop][thissub].has_key('texts'):
                tree[thistop][thissub]['texts'] = []
            text = QTreeWidgetItem()
            text.setText(0, self.messages[i][self.subsubprimary])
            text.setBackgroundColor(0,self.color)
            text.setText(1, self.messages[i][self.secondary])
            text.setBackgroundColor(1,self.color)            
            text.setText(2, self.messages[i]['text'])
            text.setBackgroundColor(2,self.color)            
            text.setToolTip(2, self.messages[i]['text'])
            tree[thistop][thissub]['texts'].append(text)
        iter1 = tree.keys()
        iter1 = self.sortTree(iter1)
        for primar in iter1:
            self.logTree.addTopLevelItem(tree[primar]['item'])            
            iter2 = tree[primar].keys()
            iter2 = self.sortTree(iter2)
            for subprimar in iter2:
                texts = self.sortTree(tree[primar][subprimar]['texts'])
                for text in texts:
                    tree[primar][subprimar]['item'].addChild(text)
                tree[primar]['item'].addChild(
                                            tree[primar][subprimar]['item'])                
        self.decodeData()
        self.fitColumnSize()
        self.countVisible()
