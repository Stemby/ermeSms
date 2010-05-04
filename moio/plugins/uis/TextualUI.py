# -*- coding: utf-8 -*-

import os
import sys
import traceback

from moio.plugins.Sender import Sender
from moio.plugins.UI import UI
from moio.PreferenceManager import PreferenceManager
from moio.CodingManager import CodingManager
from moio.errors.NotFoundError import NotFoundError
from moio.errors.PreferenceManagerError import PreferenceManagerError
from moio.errors.SenderError import SenderError
from moio.errors.ConnectionError import ConnectionError
from moio.errors.SiteConnectionError import SiteConnectionError

#TODO: add bits of code to use books plugins

class TextualUI(UI):
    """Gestore dell'interfaccia utente, versione testuale."""

    def isAvailable(self):
        """Ritorna true se quest'interfaccia è utilizzabile."""
        UISpecified = "-u" in sys.argv
        textualUISpecified = False
        if UISpecified:
            index = sys.argv.index("-u")
            if len(sys.argv) > (index+1):
                textualUISpecified = sys.argv[index+1] == "textual"
        return len(sys.argv)==1 or textualUISpecified

    def getPriority(self):
        """Ritorna un codice di priorità. In caso più interfacce siano
           utilizzabili, viene scelta quella a maggiore priorità."""
        return 1

    def run(self):
        """Avvia questa interfaccia."""
        exitCode = 0
        try:
            p = PreferenceManager.getInstance()
            cm = CodingManager.getInstance()
            masterKey = None
            print "(Questo programma funziona anche dalla linea di comando, \
vedi LEGGIMI)"
            masterKey = None
            if p.isEncryptionEnabled():
                keyValid = False
                while keyValid == False:
                    masterKey = raw_input("Inserisci la Master Password:")
                    keyValid = p.checkEncryptionKey(masterKey)
            number = raw_input("Immetti il numero del destinatario e \
premi INVIO: ")
            number = cm.unicodeStdin(number)
            text = cm.unicodeStdin(
                raw_input("Immetti il testo e premi INVIO: "))
            print "Siti disponibili per l'invio:"
            plugins = Sender.getPlugins().keys()
            for i in plugins:
                print i
            print "Immetti il nome del sito. Le maiuscole non fanno differenza."
            sender = raw_input("Premi solo INVIO per "+plugins[0]+":")
            sender = cm.unicodeStdin(sender)
            if (sender == ""):
                sender = plugins[0]
            proxy = ""
            if p.isProxyEnabled():
                print "Proxy attualmente configurato: " + p.getProxy()
                proxy = raw_input("(INVIO per confermare, \"no\" per " +
                    "disabilitare o nuovo indirizzo:)")
                if proxy == "no":
                    p.unsetProxy()
                elif proxy != "":
                    p.setProxy(proxy)
            else:
                print "Immetti l'indirizzo e la porta del proxy:"
                proxy = raw_input("(se non sai cosa sono o non li usi premi INVIO)")
                if proxy != "":
                    p.setProxy(proxy)
            if p.isProxyEnabled() == True:
                os.environ["http_proxy"] = p.getProxy()
            self.sendSMS(number, text, masterKey, sender)
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
        p.writeConfigFile()
        sys.exit(exitCode)

    def sendSMS(self, number, text, masterKey, senderName):
        #Spedisco il messaggio: inizializzo il PreferenceManager
        #ed il CodingManager
        p = PreferenceManager.getInstance()
        cm = CodingManager.getInstance()

        #Se necessario, cerco il nome in rubrica
        #Inizializzo il sender e mando il messaggio
        senderName = senderName.title()
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
            s.send(number, text, reg)
            print "Spedito!"

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
