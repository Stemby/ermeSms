#!/usr/bin/python
# -*- coding: utf-8 -*-
import evolution
import gobject

props = gobject.list_properties( evolution.ebook.EContact)
pp = [ p.name for p in props if 'phone' in p.name ]

contacts = {}
res = {}

for contact in evolution.ebook.open_addressbook('default').get_all_contacts():
    gp = contact.get_property
    numbers = [ ( p, gp(p) ) for p in pp if gp(p) ]
    if len(numbers):
        contacts[gp('full-name')] = numbers

for person in sorted( contacts.keys()):
    for ( type, number ) in contacts[person]:
        if len(contacts[person]) > 1:
            caption = '%s (%s)' % ( person, type[0].upper() + type[1:].replace( '-', ' ') )
        else:
            caption = person
        res[caption] = number

print res
