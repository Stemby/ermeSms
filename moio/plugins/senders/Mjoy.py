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

class Mjoy(Sender):
    """Permette di spedire SMS dal sito mjoy.com"""

    maxLength = 140
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""
   
    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 4
    """Incremento della gauge per pagina."""     
   
    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return True
       
    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()
            c.setopt(pycurl.USERAGENT,'Opera/9.50 (J2ME/MIDP; Opera Mini/4.1.10781/298; U; en)')
            
            if number[0] != "+": number = '+39' + number

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']                   
           
            #visito la pagina iniziale
            c.setopt(pycurl.URL, "http://www.mjoy.com/m/login.htm")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            #eseguo il login
            saver = StringIO()
            postFields = {}
            postFields["nickname"] = username
            postFields["password"] = password
            postFields["action"] = 'login'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.URL, "http://www.mjoy.com/m/login.htm")
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())
            
            try:
                code = re.search('(?<=(/m/messages/))[^/]+', saver.getvalue()).group(0)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)            
            
            #vado alla pagina degli SMS
            saver = StringIO()           
            c.setopt(pycurl.POST, False)
            url = 'http://www.mjoy.com/m/messages/' + code + '/new.htm'
            c.setopt(pycurl.URL, url)
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())

            if ui: ui.gaugeIncrement(self.incValue)            

            #Invio un sms           
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["recipient"] = number
            postFields["msgxmlm"] = text
            postFields["send"] = 'send'
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL, url)
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())
    
            if (re.search("Messaggio inviato", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)
           
        except pycurl.error as e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("Nickname o password errati", page) is not None):
            raise SiteAuthError(self.__class__.__name__)
