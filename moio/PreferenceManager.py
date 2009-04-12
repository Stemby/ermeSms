# -*- coding: utf-8 -*-

import os
import os.path
import hashlib
import sys
import time

from moio.lib.rijndael import rijndael
from moio.lib.singletonmixin import Singleton

from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from moio.CaseSensitiveConfigParser import CaseSensitiveConfigParser
from moio.CodingManager import CodingManager
from moio.errors.NotFoundError import NotFoundError
from moio.errors.PreferenceManagerError import PreferenceManagerError

class PreferenceManager(Singleton):
    """Gestisce username, password e rubrica dell'utente."""

    c = CaseSensitiveConfigParser()
    """Gestore del file di configurazione."""

    logFileName = 'logsms.txt'
    """ Info x logger """
    configBaseFileName = "config.ini"
    """Path completo e nome del file di configurazione."""
    configDirBaseName = ".moiosms"
    """Nome della cartella contenente i file di configurazione."""
    configDirName = ""
    """Path completo della cartella con i file di configurazione."""
    configFileName = ""
    """Path completo e nome del file di configurazione."""

    cm = CodingManager.getInstance()
    """Gestore della codifica dei caratteri."""
    paddingChar = "\n"
    """Carattere utilizzato per rendere la lunghezza dei valori crittati
    multipla di 8."""
    version = "2.19 Qt"
    """Versione del programma"""

    def __init__(self):
        """Inizializza i campi di quest'oggetto."""
        self.configDirName = os.path.join(self.getSaveDir(), self.configDirBaseName)
        self.configFileName = os.path.join(self.configDirName, self.configBaseFileName)
        self.c.read([self.configFileName])

    def getVersion(self):
        """Ritorna la versione del programma."""
        return self.version

    def getAccount(self, sender, chiave, key=None):
        """Legge la chiave dal file di configurazione e lo ritorna."""
        if self.isEncryptionEnabled():
            return self.getEncryptedField("login"+sender, "e"+chiave, key)
        else:
            return self.getField("login"+sender,chiave)

    def getLastUsed(self, key):
        """Ritorna un valore LRU."""
        return self.getField("lastused", key)

    def getlogFileName(self):
        """Ritorna il percorso completo del file di log"""
        return os.path.join(self.getSaveDir(), self.configDirBaseName, self.logFileName)

    def getContactSender(self, key):
        """Ritorna il valore del sender associato al nome in rubrica"""
        return self.getField("ContactSender", key)

    def getSentSender(self, key):
        """Ritorna il numero di messaggi inviati oggi"""
        return self.getField("SentSender", key)

    def getSenderList(self):
        """Ritorna la lista dei sender utilizzati"""
        items = self.c.items("SenderList")
        senderList = []
        for sender, state in items:
            if state == 'True': senderList.append(sender)
        return senderList

    def isLastUsedAvailable(self, key):
        """Ritorna True se esiste una chiave LRU."""
        return self.hasField("lastused", key)

    def isEncryptionEnabled(self):
        """Ritorna true se le password sono crittate"""
        if self.hasField("encryption", "enabled"):
            return self.getField("encryption", "enabled") == "true"
        else:
            return False

    def isEncryptionSpecified(self):
        """Ritorna True se è specificato un qualche valore per la crittografia
        (abilitata o disabilitata)."""
        return self.hasField("encryption", "enabled")

    def isSentSenderAvailable(self, key):
        """Ritorna True se esiste il numero di messaggi inviati oggi."""
        return self.hasField("SentSender", key)

    def isSenderListAvailable(self, senderList):
        """Ritorna la lista dei sender utilizzati"""
        esito = True
        for sender in senderList:
            if self.hasField('SenderList',sender) == False: esito = False
        if self.c.has_section('SenderList'):
            items = self.c.items("SenderList")
            for sender, i in items:
                if senderList.count(sender) != 1:
                    esito = False
        if esito == False: self.c.remove_section('SenderList')
        return esito

    def isContactSenderAvailable(self, key):
        """Ritorna True se esiste una chiave LRU."""
        return self.hasField("ContactSender", key)

    def checkSentSender(self):
        """Controlla che i dati siano aggiornati a oggi"""
        if self.isSentSenderAvailable('Reset'):
            lastreset = self.getSentSender('Reset')
            if time.strftime('%d/%m/%y') != lastreset:
                self.c.remove_section('SentSender')
                self.setSentSender('Reset',time.strftime('%d/%m/%y'))
        else: self.setSentSender('Reset',time.strftime('%d/%m/%y'))

    def logSMS(self, sender, dest, text):
        """Salvataggio dei dati da loggare"""
        if os.path.isfile(self.getlogFileName()) == False :
            logfile = open(self.getlogFileName(), 'w+')
        else: logfile = open(self.getlogFileName(), 'a+')
        logdata = 'data='+time.strftime('%y%m%d')+'\nora='+\
                  time.strftime('%X')+'\nsender='+sender+'\ndest='+dest+\
                  '\ntext='+text+'\n---\n'
        logfile.write(logdata)
        logfile.close()


    def isProxyEnabled(self):
        """Ritorna True se un proxy è configurato."""
        return self.hasField("proxy", "url")

    def getProxy(self):
        """Ritorna l'url del proxy server per questo computer."""
        return self.getField("proxy", "url")

    def addAccount(self, chiave, valore, sender, key=None):
        """Salva una chiave nel file di configurazione, opzionalmente
        crittato (se key è specificato e non è None)."""
        if self.isEncryptionEnabled():
            self.setEncryptedField("login"+sender, "e"+chiave, valore, key)
        else:
            self.setField("login"+sender, chiave, valore)

    def clearAccount(self,sender):
        if self.c.has_section("login"+sender):
            self.c.remove_section("login"+sender)

    def enableEncryption(self, key):
        """Abilita la cifratura di nomi utenti e password e cifra quelli esistenti."""
        for section in self.c.sections():
            if section[:5]=="login":
                for option in self.c.options(section):
                    value = self.getField(section,option)
                    self.setEncryptedField(section, "e"+option, value, key)
                    self.unsetField(section, option)
        self.setField("encryption", "enabled", "true")
        self.setField("encryption", "keyhash", self.cm.quoteBase64(hashlib.sha1.new(key).digest()))

    def checkEncryptionKey(self, key):
        """Ritorna True se la chiave passata corrisponde con la chiave utilizzata per la cifratura."""
        keyHash1 = hashlib.sha1.new(key).digest()
        keyHash2 = self.cm.unQuoteBase64(self.getField("encryption", "keyhash"))
        return keyHash1 == keyHash2

    def disableEncryption(self):
        """Disabilita la crittografia, eliminando ogni eventuale voce crittata."""
        self.setField("encryption", "enabled", "false")
        for i in self.c.sections():
            if i[:5]=="login":
                self.c.remove_section(i)

    def addContact(self, name, number):
        """Aggiunge un contatto alla rubrica."""
        self.setField("contacts", name, number)

    def setLastUsed(self, key, value):
        """Setta una coppia chiave-valore LRU."""
        self.setField("lastused", key, value)

    def setProxy(self, url):
        """Setta il proxy server per questo computer."""
        self.setField("proxy", "url", url)

    def setSenderList(self, senderList, totalSender):
        """Ritorna la lista dei sender utilizzati"""
        for sender in totalSender:
            if senderList.count(sender) == 1: self.setField("SenderList", sender, 'True')
            else: self.setField("SenderList", sender, 'False')

    def setContactSender(self, key, value):
        """Associa a un utente in rubrica in sender."""
        self.setField("ContactSender", key, value)

    def setSentSender(self, key, value):
        """Associa a un utente in rubrica in sender."""
        self.setField("SentSender", key, value)

    def unsetProxy(self):
        """Rimuovi il proxy server per questo computer."""
        self.unsetField("proxy", "url")

    def deleteContact(self, name):
        """Toglie un contatto dalla rubrica."""
        self.unsetField("contacts", name)
        if self.isContactSenderAvailable(name) : self.unsetField("ContactSender",name)

    def clear(self):
        """Azzera la configurazione."""
        self.c = ConfigParser()

    def getConfigFileName(self):
        """Ritorna il path completo del file di configurazione."""
        return self.configFileName

    #metodi privati
    def getField(self, section, key):
        """Ritorna il valore corrispondente a key nella sezione
        section."""
        try:
            section = self.cm.quoteUnicode(section)
            key = self.cm.quoteUnicode(key)
            result = self.c.get(section, key)
            result = self.cm.unQuoteUnicode(result)
        except (NoSectionError, NoOptionError):
            raise PreferenceManagerError(u"Non trovo la chiave: " + key +
                u" nella sezione: "+ section)
        return result

    def setField(self, section, key, value):
        """Setta una coppia chiave-valore corrispondente nella sezione
        section."""
        if key == "":
            raise PreferenceManagerError(u"Specificare un valore.")
        section = self.cm.quoteUnicode(section)
        key = self.cm.quoteUnicode(key)
        value = self.cm.quoteUnicode(value)
        if not self.c.has_section(section):
            self.c.add_section(section)
        self.c.set(section, key, value)

    def unsetField(self, section, key):
        """Rimuove una coppia chiave-valore dalla sezione
        section."""
        section = self.cm.quoteUnicode(section)
        key = self.cm.quoteUnicode(key)
        if self.c.has_section(section):
            if self.c.has_option(section, key):
                self.c.remove_option(section, key)
            if len(self.c.items(section))==0:
                self.c.remove_section(section)

    def hasField(self, section, key):
        """Ritorna True se la sezione ha la chiave specificata."""
        section = self.cm.quoteUnicode(section)
        key = self.cm.quoteUnicode(key)
        return self.c.has_section(section) and \
            self.c.has_option(section, key)

    def getEncryptedField(self, section, key, encryptionKey):
        """Ritorna il valore corrispondente a key nella sezione
        section, decrittandolo con la chiave encryptionKey."""
        r = rijndael(hashlib.sha1(encryptionKey).digest())
        encryptedValue = self.cm.unQuoteBase64(self.getField(section, key))
        cleartextValue = ""
        for i in range(len(encryptedValue)/16):
            cleartextValue += r.decrypt(encryptedValue[i*16:(i+1)*16])
        #Rimuovo il padding
        while cleartextValue[-1] == self.paddingChar:
            cleartextValue = cleartextValue[:-1]
        return cleartextValue

    def setEncryptedField(self, section, key, value, encryptionKey):
        """Setta una coppia chiave-valore corrispondente nella sezione
        section crittando key con la chiave encryptionKey."""
        r = rijndael(hashlib.sha1(encryptionKey).digest())
        paddedValue = value  + (16 - (len(value) % 16)) * self.paddingChar
        encryptedValue = ""
        for i in range(len(paddedValue)/16):
            encryptedValue += r.encrypt(paddedValue[i*16:(i+1)*16])
        encryptedValue = self.cm.quoteBase64(encryptedValue)
        self.setField(section, key, encryptedValue)

    def getSaveDir(self):
        """Ritorna la directory in cui salvare il file di configurazione."""
        if "portable" not in self.version:
            #Caso normale: cerco la home dell'utente
            try:
                if os.path.exists(os.environ["USERPROFILE"]):
                    return os.environ["USERPROFILE"]
            except Exception:
                pass
            try:
                if os.path.exists(os.path.expanduser("~")):
                    return os.path.expanduser("~")
            except Exception:
                pass
            try:
                if os.path.exists(os.environ["HOME"]):
                    return os.environ["HOME"]
            except Exception:
                pass
            return os.getcwd()
        else:
            #Versione "portable": salvo nella directory del programma
            return os.getcwd()

    def writeConfigFile(self):
        """Salva su file le impostazioni."""
        # se occorre, crea la directory
        if os.path.isdir(self.configDirName) == False:
            os.makedirs(self.configDirName)
        self.c.write(file(self.configFileName,"w"))

    def getBook(self):
        """Ritorna il book preferito."""
        return self.getField("books", "preferito")
    
    def setBook(self, book):
        """Setta il book preferito."""
        self.setField("books", "preferito", book) 

    def isBookSet(self):
        """Ritorna True se un book è configurato."""
        return self.hasField("books", "preferito")
