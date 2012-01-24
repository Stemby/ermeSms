# -*- coding: utf-8 -*-

import re
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class Wadja(Sender):
    """Permette di spedire SMS dal sito Wadja"""
   
    maxLength = 92
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
            
            if number[0] != "+": number = '+39' + number

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']                        
        
            #visito la pagina del login
            saver = StringIO()            
            c.setopt(pycurl.URL, "http://m.wadja.com/login/default.aspx?url=%2fDefault.aspx")
            self.perform(self.stop, saver)

            try:
                view = re.search('(?<=(name="__VIEWSTATE" id="__VIEWSTATE" value="))[^"]+', saver.getvalue()).group(0)          
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)         

            #se non sono gia' loggato, eseguo il login
            if (re.search("Sign out", saver.getvalue()) is None) and \
               (re.search("Esci", saver.getvalue()) is None) : 
                saver = StringIO()                
                c.setopt(pycurl.URL, "http://m.wadja.com/login/default.aspx?url=%2fdefault.aspx")
                postFields = {}
                postFields["__VIEWSTATE"] = view
                postFields["ctl00$cntBody$txtUser"] = username
                postFields["ctl00$cntBody$txtPass"] = password
                postFields["ctl00$cntBody$btnLogin"] = 'Sign In'
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
                self.perform(self.stop, saver)

                self.checkForErrors(saver.getvalue())
                if (re.search("Sign out", saver.getvalue()) is None) and \
                   (re.search("Esci", saver.getvalue()) is None) :
                    raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #visito la pagina degli sms
            saver = StringIO()            
            c.setopt(pycurl.URL, "http://m.wadja.com/compose/sms.aspx")
            self.perform(self.stop, saver)

            try:
                view = re.search('(?<=(name="__VIEWSTATE" id="__VIEWSTATE" value="))[^"]+', saver.getvalue()).group(0)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if (re.search(' value="1">', saver.getvalue())) is not None:
                mitt = '1'
            else: mitt = '0'

            if ui: ui.gaugeIncrement(self.incValue)      

            #invio il messaggio
            saver = StringIO()            
            c.setopt(pycurl.URL, "http://m.wadja.com/compose/sms.aspx")
            postFields = {}
            postFields["__VIEWSTATE"] = view
            postFields["ctl00$cntBody$cmpsSMS$ddlFrom"] = mitt
            postFields["ctl00$cntBody$cmpsSMS$txtSMS"] = number
            postFields["ctl00$cntBody$cmpsSMS$txtMSG"] = text
            postFields["ctl00$cntBody$cmpsSMS$btnSend"] = 'Send'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())
            
            if (re.search("Your sms has been sent", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)
           
        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("Invalid Login", page) is not None):
            raise SiteAuthError(self.__class__.__name__)
        if(re.search("no recipient specified", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Numero di telefono non valido")
        if(re.search("no message written", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Non hai inserito il messaggio")
        if(re.search("Daily limit reached to the numbers outside wadja.", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Limite di messaggi inviati per oggi.")
        if(re.search("Daily limit reached to the same number outside wadja.", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Limite di messaggi inviati oggi allo stesso numero")        
