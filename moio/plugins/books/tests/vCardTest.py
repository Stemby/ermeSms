#!/usr/bin/python
# -*- coding: utf-8 -*-

class vCardTest():

    contatti = {}
    bookFileName = "/home/francesco/.moiosms/rubrica.vcf"

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

    def addContact(self, name, number):
        """Aggiunge un contatto alla rubrica."""
        try:
            nome, cognome = name.split(" ", 2)
        except ValueError:
            nome = name
        import vobject
        j = vobject.vCard()
        j.add('n')
        j.n.value = vobject.vcard.Name( family=cognome, given=nome )
        j.add('fn')
        j.fn.value = nome + ' ' + cognome
        j.add('tel')
        j.tel.value = number
        j.tel.type_param = 'CELL'
        f = open(self.bookFileName, 'a')
        f.write(j.serialize())
        f.close()

    def deleteContact(self, name):
        """Rimuove un contatto dalla rubrica."""
        import vobject
        f = open(self.bookFileName, 'r')
        stream = f.read()
        f.close()
        f = open(self.bookFileName, 'w')
        for vobj in vobject.readComponents(stream):
            if vobj.behavior == vobject.vcard.VCard3_0:
                if not self.__revertNonAscii(name) == vobj.fn.value:
                    f.write(vobj.serialize())
        f.close()

    def updateContact(self, name, number):
        import vobject
        f = open(self.bookFileName, 'r')
        stream = f.read()
        f.close()
        f = open(self.bookFileName, 'w')
        for vobj in vobject.readComponents(stream):
            if vobj.behavior == vobject.vcard.VCard3_0:
                if not self.__revertNonAscii(name) == vobj.fn.value:
                    f.write(vobj.serialize())
                else:
                    vobj.add('tel')
                    vobj.tel.value = number
                    vobj.tel.type_param = 'CELL'
                    f.write(vobj.serialize())
        f.close()

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

    def __revertNonAscii(self, text):
        """Modifica alcuni caratteri non-ASCII dalla stringa."""
        #Brutto, ma funziona.
        text = text.replace("a_", u"à")
        text = text.replace("e_", u"è")
        text = text.replace("e_", u"é")
        text = text.replace("i_", u"ì")
        text = text.replace("o_", u"ò")
        text = text.replace("u_", u"ù")
        return text


vcobj = vCardTest()
vcobj.addContact("Valentinò Rossi", "3471223345")
vcobj.deleteContact("Valentino_ Rossi")
contatti = vcobj.getContacts()
print contatti
