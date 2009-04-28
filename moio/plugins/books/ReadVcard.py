# -*- coding: utf-8 -*-

# simply vCard parser, 
# currently only handle, names, mails and phones

# license: GPL
# author: Pavel Nemec <pnemec@suse.cz>
# 2007-06-29 HACK WEEK

# Info:
#    This modified code only handle names and cell phones.
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


import codecs
import os
import platform

from moio.plugins.Book import Book
from moio.PreferenceManager import PreferenceManager
from moio.errors.PreferenceManagerError import PreferenceManagerError
from moio.CodingManager import CodingManager
from moio.errors.NotFoundError import NotFoundError
from moio.errors.BookError import BookError


class ReadVcard(Book):
    
    bookFilePath = ""
    
    contatti = {}
    
    cm = CodingManager.getInstance()
    """Gestore della codifica dei caratteri."""
    
    def __init__(self):
        self.newFiles=[self.bookFilePath]
    
    def clear(self):
        self.newFiles=[]

    def isAvailable(self):
        if platform.system() in ("Windows", "Darwin", "Microsoft"):
            return False
        else:
            self.bookFilePath = os.environ['HOME'] + "/.kde/share/apps/kabc/std.vcf"
            return False

    def lookup(self, name):
        """Cerca un nome nella rubrica."""
        try:
	        return self.contatti[name]
        except:
            raise NotFoundError(name)

    def lookupNumber(self, number):
        """Cerca un numero nella rubrica."""
        number = self.cm.quoteUnicode(number)
        #Decisamente non il modo migliore, ma funziona.
        #contacts = self.contatti #self.getContacts()
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
        for file in self.newFiles:
            try:
                fr = codecs.open(file,'r', encoding='utf-8')
            except IOError:
                print 'Error:  Couldn\'t parse file: .', file
                continue;
            #print "going parse: ", file
            line=fr.readline()
            while line!="":
                if line.startswith("BEGIN:VCARD"):
					#PARSING NEW VCARD
					#print "new vcard"
                    line = fr.readline()
                    while line!="":
                        #print "\t",line
                        if line.startswith("END:VCARD"): break
                        if line.startswith("FN:"): 
                            line = line.replace("FN:","")
                            line = line.replace("\n","")
                            name = line
                            #print "storing name: ",line
                        if line.startswith("N:"):  #another format for maili
                            line = line.replace("N:","")
                            #print "have an N name ", line
                            parts = line.split(";")
                            if (len(parts)>1): 
                                name = parts[1]+ " "+ parts[0]
                            else: 
                                name = parts[0]
                            #print "storing name: ",parts[1]+ " "+ parts[0]
                        if line.startswith("TEL"):
                            type="Home"
                            tel= line.rpartition(':')[2] #parts[2] is tel
							#we have somethink like
                            #TEL;type=blablab;type=pref:email@email
                            #or
                            #TEL;type=blablab:email@email
                            if line.find("type")!=-1:
                                parts = line.partition("type=")
                                if parts[2].find(";")!=-1:
                                    type = parts[2].split(';')[0]
                                else:
                                    type = parts[2].split(':')[0]
                            if line.find("TYPE")!=-1:
                                parts = line.split("TYPE=")
                                if parts[1].find(";")!=-1:
                                    type = parts[1].split(';')[0]
                                else:
                                    type = parts[1].split(':')[0]
                            type = type.replace('\n',"")
                            tel = tel.replace('\n',"")
                            if type == 'CELL':
                                self.contatti[name] = tel.replace('\r',"")
                        line=fr.readline()
                line=fr.readline()
            #print "parse finished, having ",len(self.list), " items"
        return self.contatti

    def addContact(self, name, number):
        pass

    def deleteContact(self, name):
        pass

    def saveBook(self):
        """Salva i contatti."""
        pass

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
