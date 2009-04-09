# -*- coding: utf-8 -*-

import re
from cStringIO import StringIO

import pycurl

from moio.plugins.Sender import Sender
from moio.ConnectionManager import ConnectionManager
from moio.errors.SiteCustomError import SiteCustomError
from moio.errors.SiteConnectionError import SiteConnectionError
from moio.errors.SiteAuthError import SiteAuthError
from moio.errors.SenderError import SenderError

class Tin(Sender):
    """Permette di spedire SMS dal sito di tin.it"""
    
    maxLength = 130
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""
    
    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 6
    """Incremento della gauge per pagina."""
    
    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return True
    
    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        try:
            c = self.connectionManager.getCurl()

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']            
            
            #Ammazzo i vecchi cookie
            self.connectionManager.forgetCookiesFromDomain("alice.it")
            
            #Inizia la raccolta dei cookie...
            c.setopt(pycurl.URL, "http://tin.alice.it")
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)            
            self.perform(self.stop)
            
            if ui: ui.gaugeIncrement(self.incValue)               
            
            #Faccio il login
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["USER"] = username[:username.find("@")]
            postFields["DOMAIN"] = username[username.find("@")+1:]
            postFields["PASS"] = password
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL, "http://communicator.virgilio.it/asp/a3login.asp")
            self.perform(self.stop)
            
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            c.setopt(pycurl.URL, "http://communicator.alice.it/asp/a3login.asp")
            self.perform(self.stop)
            
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            postFields = {}
            postFields["a3l"]=username
            postFields["a3p"]=password
            postFields["a3si"]="-1"
            postFields["percmig"]="100"
            postFields["a3st"]="VCOMM"
            postFields["a3aid"]="comhpvi"
            postFields["a3flag"]="0"
            postFields["a3ep"]="http://communicator.alice.it/asp/login.asp"
            postFields["a3afep"]="http://communicator.alice.it/asp/login.asp"
            postFields["a3se"]="http://communicator.alice.it/asp/login.asp"
            postFields["a3dcep"]="http://communicator.alice.it/asp/homepage.asp?s=005"
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL, "http://aaacsc.alice.it/piattaformaAAA/controller/AuthenticationServlet")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)            
            
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode({}))
            c.setopt(pycurl.URL, "http://communicator.alice.it/asp/menu.asp?dest=WP")
            self.perform(self.stop)
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            c.setopt(pycurl.URL, "http://communicator.alice.it/asp/loadWP.asp")
            self.perform(self.stop)
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            c.setopt(pycurl.URL, "http://communicator.alice.it/asp/preview_WEBMAIL.asp")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)            
            
            if (re.search(u"Ciao", saver.getvalue()) is None):
                raise SiteAuthError(self.__class__.__name__)
            
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            c.setopt(pycurl.URL,
                "http://communicator.alice.it/asp/dframeset.asp?dxserv=SMS")
            self.perform(self.stop)

            #Serve per settare un oscuro cookie...
            c.setopt(pycurl.URL,
                "http://casa.virgilio.it/common/includes/header/css/header_4.css")
            self.perform(self.stop)
            
            #Altro cookie...
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            getFields = {}
            getFields["username"]=username
            c.setopt(pycurl.URL,
                "http://gsmailmdumail.alice.it:8080/supermail/controller?" +
                self.codingManager.urlEncode(getFields))
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)            

            if number[0] != "+":
                number = "+39" + number
            
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            postFields = {}
            postFields["lista_operatori"] = "x"
            postFields["numero"] = ""
            postFields["select"] = "x"
            postFields["testo"] = text
            postFields["recipient"] = number
            c.setopt(pycurl.POSTFIELDS,
            self.codingManager.urlEncode(postFields))
            getFields = {}
            getFields["username"]=username
            getFields["action"]="sendsmspreview"
            c.setopt(pycurl.URL,
                "http://gsmailmdumail.alice.it:8080/supermail/controller?" +
                self.codingManager.urlEncode(getFields))
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)
            
            # conferma
            #Altro cookie...
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            getFields = {}
            getFields["username"]=username
            getFields["action"]="sendsms"
            c.setopt(pycurl.URL,
                "http://gsmailmdumail.alice.it:8080/supermail/controller?" +
                self.codingManager.urlEncode(getFields))
            self.perform(self.stop)

            if (re.search("Messaggio inviato correttamente al server", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))
