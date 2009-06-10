# -*- coding: utf-8 -*-

import re
import sys
from cStringIO import StringIO

import pycurl

from moio.plugins.Sender import Sender
from moio.ConnectionManager import ConnectionManager
from moio.errors.SiteCustomError import SiteCustomError
from moio.errors.SiteConnectionError import SiteConnectionError
from moio.errors.SiteAuthError import SiteAuthError
from moio.errors.SenderError import SenderError

class CremonaWeb(Sender):
    """Permette di spedire SMS dal sito www.e-cremonaweb.it"""
    
    maxLength = 140
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password','Cellulare']
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
            
            if not number[0] == "+": number = '+39' + number

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']
            mittente = dati['Cellulare']
        
            #Visito la pagina iniziale
            saver = StringIO()
            c.setopt(pycurl.URL, "http://www.e-cremonaweb.it/")
            self.perform(self.stop, saver)             

            if ui: ui.gaugeIncrement(self.incValue)        	

            if (re.search("Ciao, ", saver.getvalue()) is None):
                #Faccio il login, se non sono già loggato
                
                try:          
                    login = re.search('(?<=(force_session" value="1" />\r\n        	<input type="hidden" name="))[^"]+', saver.getvalue()).group(0)
                except AttributeError:
                    raise SenderError(self.__class__.__name__)
                
                saver = StringIO()
                c.setopt(pycurl.URL, "http://www.e-cremonaweb.it/index.php")
                postFields = {}
                postFields["username"] = username
                postFields["passwd"] = password
                postFields["Submit"] = 'Entra'
                postFields["remember"] = 'yes'
                postFields["option"] = 'login'            
                postFields["op2"] = 'login'
                postFields["return"] = "http://www.e-cremonaweb.it/index.php"
                postFields["lang"] = 'italian'
                postFields["message"] = '0'
                postFields["force_session"] = '1'
                postFields[login] = '1'            
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
                self.perform(self.stop, saver)            

                if (re.search("Nome utente o password non validi", saver.getvalue()) is not None):
                    raise SiteAuthError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #Visito la pagina degli sms
            saver = StringIO()
            c.setopt(pycurl.POST, False)            
            c.setopt(pycurl.URL, "http://www.e-cremonaweb.it/index.php?option=com_content&task=view&id=528&Itemid=291")
            self.perform(self.stop, saver)            

            try:          
                session = re.search('(?<=(<form id="registrazione" method="get" name="q_form_))[^"]', saver.getvalue()).group(0)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)            
              
            #Spedisco l'SMS
            saver = StringIO()
            postFields = {}
            postFields["formID"] = session
            postFields["proprionum"] = mittente
            postFields["q8_Testodelmessaggio"] = text
            postFields["filtering_rubrica"] = '+39'
            postFields["q9_Numerodestinatario"] = number
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
            self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL,"http://www.e-cremonaweb.it/singlesms.php")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            if (re.search("1;\d;\d\d?", saver.getvalue()) is None):
                if (re.search("0;\d;0", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Sms del mese esauriti.")                
                elif (re.search("0;0;\d\d?", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Sms di oggi esauriti.")
                else: raise SenderError(self.__class__.__name__)
        
        except pycurl.error as e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("Attenzione: Sms non inviato", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Sms Esauriti")
