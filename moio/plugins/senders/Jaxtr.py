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

class Jaxtr(Sender):
    """Permette di spedire SMS dal sito Jaxtr.com"""
   
    maxLength = 90
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""
   
    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 4
    """Incremento della gauge per pagina."""
   
    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return True
       
    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima
        maxLength con le credenziali specificate, supponendo Internet
        raggiungibile."""
        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()
            
            if number[0]!="+":
                number = "+39"+number

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            #Visito la pagina di login
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            c.setopt(pycurl.URL, "http://www.jaxtr.com/user/login.jsp")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)            

            #faccio il login, prima parte
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["tzOffset"] = "-1"
            postFields["navigateURL"] = ""
            postFields["refPage"] = ""
            postFields["jaxtrId"] = username
            postFields["password"] = password
            postFields["Login"] = "Login"
            postFields["_sourcePage"] = "%2Flogin.jsp"
            postFields["__fp"] = ""
            c.setopt(pycurl.POSTFIELDS,
            self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL, "http://www.jaxtr.com/user/Login.action")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)            

            #Visito la pagina home
            c.setopt(pycurl.POST, False)
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            c.setopt(pycurl.URL, "http://www.jaxtr.com/user/home.jsp")
            self.perform(self.stop)
           
            try:
                re.search('Log Out', saver.getvalue()).group(0)
            except:
                raise SiteAuthError(self.__class__.__name__)


           #tentativo di invio ad uno dei molti paesi supportati
            try:
                prefix = number[:3]
                code = re.search("'([a-z]+)': { 'name': '[A-Za-z]+', 'code': '"+"\\"+prefix+"'", saver.getvalue()).group(1)
            except:
                raise SiteCustomError(self.__class__.__name__,
                                      u"Paese di destinazione non supportato.")

            if ui: ui.gaugeIncrement(self.incValue)

            #Invio di un sms
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)

            c.setopt(pycurl.POST, True)

            postFields = {}
            postFields["CountryName"] = code.upper()
            postFields["phone"] = number[3:]
            postFields["message"] = str(text)
            postFields["bySMS"] = "true"

            c.setopt(pycurl.POSTFIELDS,
            self.codingManager.urlEncode(postFields))
           
            url = "http://www.jaxtr.com/user/sendsms";

            c.setopt(pycurl.REFERER, "http://www.jaxtr.com/user/home.jsp")
            c.setopt(pycurl.URL, url)
            self.perform(self.stop)

            if (re.search("to send more", saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__,
                    u"Hai finito gli sms disponibili per questo mese.")
            elif (re.search("sent", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)
           
        except pycurl.error as e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))
