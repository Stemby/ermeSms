# -*- coding: utf-8 -*-

import re
import sys
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class TheCellFreak(Sender):
    """Permette di spedire SMS dal sito www.thecellfreak.com/"""
    
    maxLength = 90
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password','Mittente']
    """Cosa richiede questo plugin?"""

    incValue = 3
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
            
            if number[0] == "+":
                prefix = number[:3]
                number = number[3:]
            else:
                prefix = '+39'

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']
            mittente = dati['Mittente']            
            
            #Faccio il login
            saver = StringIO()
            c.setopt(pycurl.URL, "http://www.thecellfreak.com/user")
            postFields = {}
            postFields["name"] = username          
            postFields["gotohome"] = '1'
            postFields["pass"] = password
            postFields["form_id"] = 'user_login'
            postFields["op"] = 'Log in'         
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
            self.perform(self.stop, saver)

            if (re.search('Wrong login info', saver.getvalue()) is not None):
                raise SiteAuthError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #Visito la pagina intermedia
            saver = StringIO()
            c.setopt(pycurl.POST, False)
            c.setopt(pycurl.URL, "http://www.thecellfreak.com")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            if ui: ui.gaugeIncrement(self.incValue)
            
            #Spedisco l'SMS
            saver = StringIO()
            c.setopt(pycurl.URL, "http://www.thecellfreak.com/sendsms/send2")
            postFields = {}
            postFields["sms_sendtocountry"] = 'IT'
            postFields["sms_sendtonumber"] = number
            postFields["sms_sendfrom"] = mittente
            postFields["sms_message"] = text      
            postFields["cname"] = '1'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
            self.perform(self.stop, saver)
            
            if (re.search("SMS Sent sucessfully", saver.getvalue()) is None):
                self.checkForErrors(saver.getvalue())
                raise SenderError(self.__class__.__name__)
        
        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search('0 messages left', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"SMS terminati.")
        if(re.search('Please enter a destination number', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Destinatario errato")
        if(re.search('Please write your message', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Testo mancante")        
