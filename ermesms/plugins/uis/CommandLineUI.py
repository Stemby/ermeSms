# -*- coding: utf-8 -*-

import os
import sys
import traceback

from ermesms.plugins.UI import UI
from ermesms.plugins.Sender import Sender
from ermesms.plugins.uis.HelpUI import HelpUI
from ermesms.PreferenceManager import PreferenceManager
from ermesms.CodingManager import CodingManager
from ermesms.errors.NotFoundError import NotFoundError
from ermesms.errors.PreferenceManagerError import PreferenceManagerError
from ermesms.errors.SenderError import SenderError
from ermesms.errors.ConnectionError import ConnectionError
from ermesms.errors.SiteConnectionError import SiteConnectionError


class CommandLineUI(UI):
    """Gestore dell'interfaccia utente, versione a linea di comando."""

    def isAvailable(self):
        """Ritorna true se quest'interfaccia è utilizzabile."""
        return len(sys.argv) > 1 and (("-u" in sys.argv) == False)
        # FIXME: what is "-u" ???

    def getPriority(self):
        """Ritorna un codice di priorità. In caso più interfacce siano
           utilizzabili, viene scelta quella a maggiore priorità."""
        return 2

    def run(self):
        """Avvia questa interfaccia."""
        na = len(sys.argv) - 1
        exitCode = 0
        p = PreferenceManager.getInstance()
        cm = CodingManager.getInstance()
        try:
            if (na == 1):
                # Only 1 argument: 3 cases
                # 1) '-s' or '--show'
                # 2) '-h' or '--help'
                # 3) '-v' or '--version'
                arg1 = cm.unicodeArgv(sys.argv[1])
                if arg1 in ('-s', '--show'):
                    for name, number in p.getContacts().iteritems():
                        print '%s: %s' % (cm.encodeStdout(name),
                                cm.encodeStdout(number))
                elif arg1 in ('-h', '--help'):
                    HelpUI.getInstance().run() # TODO: to update
                elif arg1 in ('-v', '--version'):
                    print 'ermeSms %s' % p.getVersion()
                else:
                    if len(arg1) == 2 and arg1[0] == '-' and arg1[1] != '-':
                        print "ermesms: invalid option -- '%s'" % arg1[1]
                    else:
                        print "ermesms:  unrecognized option '%s'" % arg1
                    print "Try `ermesms --help' for more information."
            elif (na == 2):
                # 2 arguments: phone_number -- text
                arg1 = cm.unicodeArgv(sys.argv[1])
                arg2 = cm.unicodeArgv(sys.argv[2])
                self.sendSMS(arg1, arg2, Sender.getPlugins().keys()[0])
            elif (na == 3):
                # 3 arguments: 2 cases
                # 1) '-a' -- name -- phone_number
                # 2) phone_number -- text -- sender
                arg1 = cm.unicodeArgv(sys.argv[1])
                arg2 = cm.unicodeArgv(sys.argv[2])
                arg3 = cm.unicodeArgv(sys.argv[3])
                if arg1 in ('-a', '--add'):
                    p.addContact(arg2, arg3)
                    print "Added %s's phone number: %s." % (arg2, arg3)
                else:
                    if p.isProxyEnabled() == True:
                        os.environ["http_proxy"] = p.getProxy()
                    self.sendSMS(arg1, arg2, arg3)
            elif (na == 4):
                # 4 arguments: phone_number -- text -- '-p' -- proxy
                arg1 = cm.unicodeArgv(sys.argv[1])
                arg2 = cm.unicodeArgv(sys.argv[2])
                arg3 = cm.unicodeArgv(sys.argv[3])
                arg4 = cm.unicodeArgv(sys.argv[4])
                if arg3 in ('-p', '--proxy'):
                    if arg4 != "no":
                        p.setProxy(arg4)
                    else:
                        p.unsetProxy()
                    if p.isProxyEnabled() == True:
                        os.environ["http_proxy"] = p.getProxy()
                    self.sendSMS(arg1, arg2, Sender.getPlugins().keys()[0])
                else:
                    HelpUI.getInstance().run()
            elif (na == 5):
                # 5 arguments: phone_number -- text -- sender -- '-p' -- proxy
                arg1 = cm.unicodeArgv(sys.argv[1])
                arg2 = cm.unicodeArgv(sys.argv[2])
                arg3 = cm.unicodeArgv(sys.argv[3])
                arg4 = cm.unicodeArgv(sys.argv[4])
                arg5 = cm.unicodeArgv(sys.argv[5])
                if arg4 in ('-p', '--proxy'):
                    if arg5 != "no":
                        p.setProxy(arg5)
                    else:
                        p.unsetProxy()
                    if p.isProxyEnabled() == True:
                        os.environ["http_proxy"] = p.getProxy()
                    self.sendSMS(arg1, arg2, arg3)
                else:
                    HelpUI.getInstance().run()
            else:
                HelpUI.getInstance().run()
        except NotFoundError, e:
            print cm.encodeStdout(e.__str__())
            exitCode = 1
        except SenderError, e:
            print cm.encodeStdout(e.__str__())
            exitCode = 2
        except KeyboardInterrupt:
            print "Interrotto!"
            exitCode = 3
        except ConnectionError, e:
            print cm.encodeStdout(e.__str__())
            exitCode = 5
        except SiteConnectionError, e:
            print cm.encodeStdout(e.__str__())
            exitCode = 6
        except PreferenceManagerError, e:
            print cm.encodeStdout(e.__str__())
            exitCode = 7
        p.writeConfigFile()
        sys.exit(exitCode)


    def sendSMS(self, number, text, senderName):
        #Spedisco il messaggio: inizializzo il PreferenceManager
        #ed il CodingManager
        p = PreferenceManager.getInstance()
        cm = CodingManager.getInstance()

        masterKey = None
        if p.isEncryptionEnabled():
            keyValid = False
            while keyValid == False:
                masterKey = raw_input("Inserisci la Master Password:")
                keyValid = p.checkEncryptionKey(masterKey)
        #Se necessario, cerco il nome in rubrica
        #Inizializzo il sender e mando il messaggio
        if number.isdigit() == False:
            number = p.lookup(number)
        if Sender.getPlugins().has_key(senderName) == False:
            print "Sito "+senderName+" non riconosciuto."
        else:
            reg = {}
            s = Sender.getPlugins()[senderName]
            if s.requiresRegistration:
                try:
                    for i in s.requiresRegistration:
                        reg[i] = p.getAccount(senderName, i, masterKey)
                except PreferenceManagerError:
                    for i in s.requiresRegistration:
                        p.addAccount(i, cm.unicodeStdin(
                            raw_input("Immetti il dato "+i+": ")),
                                     senderName, masterKey)
                    for i in s.requiresRegistration:
                        reg[i] = p.getAccount(senderName, i, masterKey)
            s.sendOne(number, text, reg)
            print "Spedito!"

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
