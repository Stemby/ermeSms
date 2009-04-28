#!/usr/bin/python
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
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from moio.Plugin import Plugin

class Book(Plugin):
    """Classe base dei plugin per le rubriche."""
    
    def lookup(self, name):
        """Cerca un nome nella rubrica."""
        raise NotImplementedError()

    def lookupNumber(self, number):
        """Cerca un numero nella rubrica."""
        raise NotImplementedError()
        
    def isInContacts(self, name):
        """Ritorna True se un contatto è presente in rubrica."""
        raise NotImplementedError()

    def isNumberInContacts(self, number):
        """Ritorna True se il numero di un contatto è presente in rubrica."""
        raise NotImplementedError()

    def getContacts(self):
        """Ritorna un dizionario con tutti i contatti in rubrica."""
        raise NotImplementedError()

    def addContact(self, name, number):
        """Aggiunge un contatto alla rubrica."""
        raise NotImplementedError()

    def deleteContact(self, name):
        """Rimuove un contatto dalla rubrica."""
        raise NotImplementedError()
        
    def saveBook(self):
        """Salva le impostazioni."""
        raise NotImplementedError()
    
    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        raise NotImplementedError()
