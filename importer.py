#!/usr/bin/env python

# TODO -- capital letters become small letters: why???

import os
from ConfigParser import ConfigParser

question = "Do you want to import MoioSMS 2 contacts? (Y/n) --> "
answer = raw_input(question)
if answer == 'Y' or answer == 'y' or answer == '':
    home = os.getenv('HOME') # TODO: probably to generalize

    MoioSMSfile = home + '/.moiosms/config.ini' # TODO: probably to generalize
    pyMoioSMSfile = home + '/.pymoiosms/config.ini' # TODO: probably to generalize
    
    # Read MoioSMS contacts
    MoioSMSconfig = ConfigParser()
    MoioSMSconfig.read(MoioSMSfile)
    contacts = MoioSMSconfig.items('contacts')

    # Write contacts into pyMoioSMS configuration file
    pyMoioSMSconfig = ConfigParser()
    pyMoioSMSconfig.read(pyMoioSMSfile)
    for couple in contacts:
        print couple[0],
        print couple[1]
        pyMoioSMSconfig.set('contacts', couple[0], couple[1])
    pyMoioSMSconfig.write(open(pyMoioSMSfile, 'r+'))

elif answer == 'n':
    pass
else:
    print 'Not valid command. Quit'


