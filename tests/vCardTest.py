#!/usr/bin/python
# -*- coding: utf-8 -*-

class vCardTest():

    contatti = {}
    bookFileName = "/home/francesco/.moiosms/rubrica.vcf"

    def getContacts(self):
        import vobject
        f = open(self.bookFileName, 'r')
        stream = f.read()
        for vobj in vobject.readComponents(stream):
            if vobj.behavior == vobject.vcard.VCard3_0:
                if 'tel' in vobj.contents:
                    tels = vobj.contents['tel']
                    i = 0
                    name = vobj.fn.value
                    for tel in tels:
                        number = tel.value
                        if i == 0: 
                            self.contatti[name] = number
                        else:
                            self.contatti[name + ' ('+str(i)+')'] = number
                        i += 1
        return self.contatti

vcobj = vCardTest()
contatti = vcobj.getContacts()

print contatti
