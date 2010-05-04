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

#TODO: personalizzare la rubrica da utilizzare
#TODO: mostrare tutti i numeri di cellulare di un contatto

import os
import sys
import traceback
import re
import platform
import subprocess

from cStringIO import StringIO

from moio.PreferenceManager import PreferenceManager
from moio.CodingManager import CodingManager

from moio.plugins.Book import Book

from moio.errors.NotFoundError import NotFoundError
from moio.errors.BookError import BookError

class EvolutionBook(Book):
    """Gestore della rubrica di Evolution."""

    idcontatti = {}
    """Dizionario che contiene nome => uid"""
    contatti = {}
    """Dizionario che contiene nome => numero"""

    cm = CodingManager.getInstance()
    """Gestore della codifica dei caratteri."""

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        if platform.system() in ("Windows", "Darwin", "Microsoft"):
            return False
        try:
            import evolution.ebook
            import gobject
        except ImportError:
            return False
        if evolution.ebook.__version__ < (2,2,2):
            return False
        return True

    def lookup(self, name):
        """Cerca un nome nella rubrica."""
        try:
            return self.contatti[name]
        except:
            raise NotFoundError(name)

    def lookupNumber(self, number):
        """Cerca un numero nella rubrica."""
        number = self.cm.quoteUnicode(number)
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
        try:
            import evolution.ebook as e
            import gobject
            for contatto in e.open_addressbook("default").get_all_contacts():
                gp = contatto.get_property
                name = self.cm.unQuoteUnicode(gp('full-name'))
                if not gp('mobile-phone') == None:
                    self.contatti[name] = gp('mobile-phone')
                    self.idcontatti[name] = contatto.get_uid()
        except:
            raise BookError(u"La rubrica di Evolution non è disponibile. Scegliere un altro plugin.")
        finally:
            return self.contatti

    def addContact(self, name, number):
        """Aggiunge un contatto alla rubrica."""
        try:
            import evolution.ebook as e
            import gobject
            contatto = e.EContact()
            #FIXME: problema con caratteri accentati nel nome
            name = self.cm.unQuoteUnicode(name)
            contatto.props.full_name = name
            contatto.props.mobile_phone = number
            id1 = e.open_addressbook("default").add_contact(contatto)
            self.idcontatti[name] = id1
            self.contatti[name] = number
        except:
            raise BookError(u"La rubrica di Evolution non è disponibile. Scegliere un altro plugin.")

    def deleteContact(self, name):
        """Rimuove un contatto dalla rubrica."""
        try:
            import evolution.ebook as e
            import gobject
            id1 = self.idcontatti[name]
            e.open_addressbook("default").remove_contact_by_id(id1)
            del self.contatti[name]
            del self.idcontatti[name]
        except:
            raise BookError(u"La rubrica di Evolution non è disponibile. Scegliere un altro plugin.")

    def saveBook(self):
        """Salva i contatti."""
        pass

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
