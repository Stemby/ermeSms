#!/usr/bin/env python

# TODO -- integrate the importer in pyMoioSMS

from os import getenv
from ConfigParser import ConfigParser, NoSectionError
from moio.PreferenceManager import PreferenceManager

question = "Do you want to import MoioSMS 2 contacts? (Y/n) --> "
answer = raw_input(question)
if answer.lower() in ('', 'y'):

    pyMoioSMSfile = PreferenceManager.getConfigFileName(PreferenceManager.getInstance())
    MoioSMSfile = pyMoioSMSfile.replace("py", "")

    # Read MoioSMS contacts if MoioSMSfile exists
    try: file(MoioSMSfile)
    except IOError: quit("The '%s' file doesn't exist" % MoioSMSfile)
    MoioSMSconfig = ConfigParser()
    MoioSMSconfig.optionxform = str
    MoioSMSconfig.read(MoioSMSfile)
    try: contacts = MoioSMSconfig.items('contacts')
    except NoSectionError: quit("The is no such contact stored in your MoioSMS2 file!")

    # Write contacts into pyMoioSMS configuration file
    try: file(pyMoioSMSfile)
    except IOError: quit("The '%s' file doesn't exist" % pyMoioSMSfile)
    pyMoioSMSconfig = ConfigParser()
    pyMoioSMSconfig.optionxform = str
    pyMoioSMSconfig.read(pyMoioSMSfile)
    pyMoioSMSconfig.add_section('contacts') if not pyMoioSMSconfig.has_section('contacts') else None
    for key, value in contacts:
        if pyMoioSMSconfig.has_option('contacts', key):
            if value == pyMoioSMSconfig.get('contacts', key): print "[!] Skipping '%s' (it already exists here..)" % key
            else:
                print "[!] An option called '%s' already exists but having a different number." % key
                new_key = raw_input("Do you want to add it using a different name? Enter it here now or leave this field empty to skip this contact\n")
                if new_key: pyMoioSMSconfig.set('contacts', new_key, value)
                else: print "[!] Skipping '%s'" % key
        else: pyMoioSMSconfig.set('contacts', key, value)
    pyMoioSMSconfig.write(open(pyMoioSMSfile, "w"))
    print "OK! I've successfully parsed %s contacts :)" % len(contacts)

elif answer.lower() == 'n':
    pass
else:
    quit('Not valid command. Quit')
