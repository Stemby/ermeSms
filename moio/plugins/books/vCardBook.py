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

from moio.plugins.Book import Book
from moio.PreferenceManager import PreferenceManager
from moio.errors.PreferenceManagerError import PreferenceManagerError
from moio.CodingManager import CodingManager
from moio.errors.NotFoundError import NotFoundError
from moio.errors.BookError import BookError


class vCardBook(Book):
    
    bookBaseFileName = "rubrica.vcf"
    """Path completo e nome del file di rubrica."""
    bookDirBaseName = ".moiosms"
    """Nome della cartella contenente i file di rubrica."""
    bookFileName = ""
    """Path completo e nome del file di rubrica."""
    
    #cm = CodingManager.getInstance()
    #"""Gestore della codifica dei caratteri."""    
    
    pm = PreferenceManager.getInstance()
    """Riferimento al gestore delle preferenze."""
    
    contatti = {}

    def __init__(self):
        self.bookFileName = os.path.join(self.__getSaveDir(), self.bookBaseFileName)
    
    def isAvailable(self):
        try:
            import vobject
            return True
        except ImportError:
            return False

    def lookup(self, name):
        #name = name)
        """Cerca un nome nella rubrica."""
        try:
	        return self.contatti[name]
        except:
            raise NotFoundError(name)

    def lookupNumber(self, number):
        """Cerca un numero nella rubrica."""
        inverseContacts = dict([[v, k] for k, v in self.contatti.items()])
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
        #name = unicode(name)
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
        import vobject
        #TODO: try: except: I/O operation        
        f = open(self.bookFileName, 'r')
        stream = f.read()
        for vobj in vobject.readComponents(stream):
            if vobj.behavior == vobject.vcard.VCard3_0:
                if 'tel' in vobj.contents:
                    tels = vobj.contents['tel']
                    i = 0
                    name = self.__replaceNonAscii(vobj.fn.value)
                    for tel in tels:
                        number = tel.value
                        if i == 0: 
                            self.contatti[name] = number
                        else:
                            self.contatti[name + ' ('+str(i)+')'] = number
                        i += 1
        f.close()
        return self.contatti

    def __replaceNonAscii(self, text):
        """Modifica alcuni caratteri non-ASCII dalla stringa."""
        #Brutto, ma funziona.
        text = text.replace(u"à", "a_")
        text = text.replace(u"è", "e_")
        text = text.replace(u"é", "e_")
        text = text.replace(u"ì", "i_")
        text = text.replace(u"ò", "o_")
        text = text.replace(u"ù", "u_")
        return text

    def addContact(self, name, number):
        """Aggiunge un contatto alla rubrica."""
        pass

    def deleteContact(self, name):
        """Rimuove un contatto dalla rubrica."""
        pass

    def clearContacts(self):
        """Rimuove tutti contatti dalla rubrica."""
        pass

    def saveBook(self):
        """Salva i contatti."""
        if os.path.isdir(self.__getSaveDir()) == False:
            os.makedirs(self.bookDirName)
        pass
        #self.c.write(file(self.bookFileName,"w"))

    def __getSaveDir(self):
        """Ritorna la directory in cui salvare il file di configurazione."""
        return os.path.abspath(os.path.dirname(self.pm.getConfigFileName()))

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
