# -*- coding: utf-8 -*-

# TODO: finish to translate in English
# TODO: better aspect

import sys

from ermesms.CodingManager import CodingManager
from ermesms.plugins.Sender import Sender
from ermesms.plugins.UI import UI

class HelpUI(UI):
    """Interfaccia utente quando-tutto-il-resto-fallisce: una spiegazione
    dell'uso del programma."""

    def isAvailable(self):
        """Questa interfaccia è sempre utilizzabile."""
        return True

    def getPriority(self):
        """Priorità minima."""
        return 0

    def run(self):
        """Avvia questa interfaccia."""
        print "ermeSms by Thomas Bertani\n"
        print "Website: https://github.com/sylarpowa/ermeSms\n"
        print "USO:"
        print "MODALITA' INTERATTIVA: ermesms\n"
        print "MODALITA' A LINEA DI COMANDO: "
        print 'ermesms number "text" (send a message to a phone number)'
        print 'ermesms name "text" (send a message to a phone number present into the phone book)'
        print "ermesms -a name number (add a phone number into the phone book)"
        print "ermesms -s (display the phone book)\n"
        # TODO: ermesms -v
        print "Per usare un sito in particolare, aggiungere uno dei parametri seguenti:"
        for i in Sender.getPlugins():
            print i
        print
        print "Per usare un proxy, aggiungere -p indirizzo:porta in coda"
        print "(usare -p no per disabilitare)"
        print
        print("Address book, password and settings "
                "are into the file .ermesms/config.ini.")
        print "Comments/Suggests/Bugs: sylar@anche.no"

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)

