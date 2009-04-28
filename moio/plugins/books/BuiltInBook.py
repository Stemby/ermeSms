# -*- coding: utf-8 -*-

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

import os
import os.path
import sys
import traceback

from moio.plugins.Book import Book
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from moio.CaseSensitiveConfigParser import CaseSensitiveConfigParser
from moio.PreferenceManager import PreferenceManager
from moio.errors.PreferenceManagerError import PreferenceManagerError
from moio.CodingManager import CodingManager
from moio.errors.NotFoundError import NotFoundError

class BuiltInBook(Book):
    """Gestore della rubrica di MoioSMS."""
    
    c = CaseSensitiveConfigParser()
    """Gestore del file di configurazione."""
    
    bookBaseFileName = "rubrica.ini"
    """Path completo e nome del file di rubrica."""
    bookDirBaseName = ".moiosms"
    """Nome della cartella contenente i file di rubrica."""
    bookFileName = ""
    """Path completo e nome del file di rubrica."""
    
    oldConfigBaseFileName = "config.ini"
    """Path completo e nome del file di configurazione, dalla versione 2.13."""
    oldConfigFileName = ""
    """Path completo e nome del file di configurazione, dalla versione 2.13."""
    
    cm = CodingManager.getInstance()
    """Gestore della codifica dei caratteri."""    
    
    pm = PreferenceManager.getInstance()
    """Riferimento al gestore delle preferenze."""
    
    def __init__(self):
        """Inizializza i campi di quest'oggetto."""
        # dalla versione 2.14 il file di rubrica è in ~/.moiosms
        # se trovo un file di configurazione vecchio in ~, leggo entrambi
        # (quello vecchio viene cancellato alla chiusura)
        self.oldConfigFileName = os.path.join(self.__getSaveDir(), self.oldConfigBaseFileName)
        #self.configDirName = os.path.join(self.getSaveDir(), self.configDirBaseName)
        self.bookFileName = os.path.join(self.__getSaveDir(), self.bookBaseFileName)
        self.c.read([self.oldConfigFileName, self.bookFileName])
        self.__purge()
       
    def __purge(self):
        for section in self.c.sections():
            if section != "contacts":
                self.c.remove_section(section)

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return True

    def lookup(self, name):
        """Cerca un nome nella rubrica."""
        try:
            return self.__getField("contacts", name)
        except (NoSectionError, NoOptionError, PreferenceManagerError):
            raise NotFoundError(name)
            
    def lookupNumber(self, number):
        """Cerca un numero nella rubrica."""
        number = self.cm.quoteUnicode(number)
        #Decisamente non il modo migliore, ma funziona.
        #contacts = self.getContacts()
        inverseContacts = dict([[v, k] for k, v in self.getContacts().items()])
        try:
            return inverseContacts[number]
        except KeyError:
            if number[:3]=="+39":
                number = number[3:]
            else:
                number = "+39"+number
            try:
                return inverseContacts[number]
            except KeyError:
                raise NotFoundError(number)
    
    def isInContacts(self, name):
        """Ritorna True se un contatto è presente in rubrica."""
        try:
            self.lookup(name)
            return True
        except NotFoundError:
            return False

    def isNumberInContacts(self, number):
        """Ritorna True se il numero di un contatto è presente in rubrica."""
        try:
            self.lookupNumber(number)
            return True
        except NotFoundError:
            #ricerca alternativa
            if number[:3]=="+39":
                number = number[3:]
            else:
                number = "+39"+number
            try:
                self.lookupNumber(number)
                return True
            except NotFoundError:
                return False

    def getContacts(self):
        """Ritorna un dizionario con tutti i contatti in rubrica."""
        result = {}
        if self.c.has_section("contacts") == True:
            items = self.c.items("contacts")
            for name, number in items:
                name = self.cm.unQuoteUnicode(name)
                number = self.cm.unQuoteUnicode(number)
                result[name] = number
        return result

    def addContact(self, name, number):
        """Aggiunge un contatto alla rubrica."""
        self.__setField("contacts", name, number)

    def deleteContact(self, name):
        """Rimuove un contatto dalla rubrica."""
        self.__unsetField("contacts", name)

    def saveBook(self):
        """Salva su file i contatti."""
        # elimino il vecchio file delle impostazioni, se esiste
        #if os.path.isfile(self.oldConfigFileName):
        #    os.remove(self.oldConfigFileName)
        # se occorre, crea la directory
        if os.path.isdir(self.__getSaveDir()) == False:
            os.makedirs(self.bookDirName)
        self.c.write(file(self.bookFileName,"w"))
        
    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
    
    #metodi privati
    def __getField(self, section, key):
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

    def __setField(self, section, key, value):
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
    
    def __unsetField(self, section, key):
        """Rimuove una coppia chiave-valore dalla sezione
        section."""
        section = self.cm.quoteUnicode(section)
        key = self.cm.quoteUnicode(key)
        if self.c.has_section(section):
            if self.c.has_option(section, key):
                self.c.remove_option(section, key)
            if len(self.c.items(section))==0:
                self.c.remove_section(section)
                
    def __getSaveDir(self):
        """Ritorna la directory in cui salvare il file di configurazione."""
        return os.path.abspath(os.path.dirname(self.pm.getConfigFileName()))
