# -*- coding: utf-8 -*-

# TODO: translate to English

import re
import sys
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.plugins.CaptchaDecoder import CaptchaDecoder
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.CaptchaError import CaptchaError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class VodafoneWidget(Sender):
    """Permette di spedire SMS dal widget vodafone.it (tnx to jamiro and bunbury)"""

    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password', 'SIM']
    """Cosa richiede questo plugin?"""

    incValue = 7
    """Incremento della gauge per pagina."""

    def __init__(self):
        self.encoding = 'FIXME'

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        #Deve essere disponibile un qualunque CaptchaDecoder
        return CaptchaDecoder.getBestPlugin() is not None

    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']
            sim = str(dati['SIM'])

            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                u"Questo sito permette di inviare SMS solo verso cellulari italiani.")
            
            c.setopt(pycurl.HTTPHEADER, [
                                         'X-Flash-Version: 10,0,45,2;',
                                         'Accept: */*;',
                                         'Accept-Encoding: gzip,deflate;',
                                         'Accept-Language: it-it;'
                                         'Connection: keep-alive;'])
            c.setopt(pycurl.USERAGENT, 'Vodafone_DW')
            c.setopt(pycurl.REFERER, 'http://www.vodafone.it/')            
            
            #faccio il login
            saver = StringIO()
            c.setopt(pycurl.URL, "https://widget.vodafone.it/190/trilogy/jsp/login.do")
            postFields = {}
            postFields["username"] = username
            postFields["password"] = password            
            postFields["cu_channel"] = 'MM'
            postFields["cu_notrace"] = 'true'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(
                postFields, self.encoding))
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())

            if (re.search("Ciao ", saver.getvalue()) is None):
                raise SiteAuthError(self.__class__.__name__)                
               
            if ui: ui.gaugeIncrement(self.incValue)

            #eventuale cambio sim
            if sim and (re.search('value="'+sim+'" selected >',
                                  saver.getvalue()) is None):
                saver = StringIO()
                c.setopt(pycurl.URL, "http://www.areaprivati.vodafone.it/190/trilogy/jsp/swapSim.do?channel=VODAFONE_DW&tk=9604,l&ty_sim="+sim)
                self.perform(self.stop, saver)
                self.checkForErrors(saver.getvalue())

            if ui: ui.gaugeIncrement(self.incValue)                         

            #Visito pagina intermedia
            c.setopt(pycurl.POST, False)
            c.setopt(pycurl.URL,
                "https://widget.vodafone.it/190/fsms/precheck.do?channel=VODAFONE_DW")
            self.perform(self.stop)

            self.checkForErrors(saver.getvalue())
            if ui: ui.gaugeIncrement(self.incValue)

            #Spedisco l'SMS
            saver = StringIO()
            postFields = {}
            postFields["receiverNumber"] = number
            postFields["message"] = text
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            c.setopt(pycurl.URL,
                "https://widget.vodafone.it/190/fsms/prepare.do?channel=VODAFONE_DW")
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())

            captchaBroken = False
            while captchaBroken == False:
                postFields = {}
                if re.search('CODEIMG',saver.getvalue()) is not None:
                    try:
                        captchaimage = re.search('(?<=(<e n="CODEIMG" ><!\[CDATA\[))[^\]]+', saver.getvalue()).group(0)
                        captchaimage = captchaimage.decode("base64")
                        saver = StringIO(captchaimage)
                        postFields["verifyCode"] = CaptchaDecoder.getBestPlugin().decodeCaptcha(saver, 'Vodafone')
                    except CaptchaError:
                        raise SenderError(self.__class__.__name__)
                
                    if not postFields["verifyCode"]:
                        raise SiteCustomError(self.__class__.__name__,
                                    u"Captcha non inserito. Invio interrotto.")

                #Confermo l'invio
                if ui: ui.gaugeIncrement(self.incValue)
                postFields["receiverNumber"] = number
                postFields["message"] = text
                
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS,
                    self.codingManager.urlEncode(postFields, self.encoding))
                saver = StringIO()
                c.setopt(pycurl.URL,
                    "https://widget.vodafone.it/190/fsms/send.do?channel=VODAFONE_DW")
                self.perform(self.stop, saver)

                if re.search('CODEIMG',saver.getvalue()) is None:
                    captchaBroken = True                    
                elif ui: ui.gaugeIncrement(-self.incValue)

            self.checkForErrors(saver.getvalue())

            if (re.search("inviati correttamente", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search('n="ERRORCODE" v="100"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il servizio non e' al momento disponibile.")
        if(re.search('n="ERRORCODE" v="101"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il servizio non e' al momento disponibile.")
        if(re.search('n="ERRORCODE" v="102"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Sessione scaduta.")
        if(re.search('n="ERRORCODE" v="103"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Siamo spiacenti. Il tuo profilo di registrazione non e' abilitato a questo servizio.")
        if(re.search('n="ERRORCODE" v="104"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il servizio non e' al momento disponibile.")        
        if(re.search('n="ERRORCODE" v="105"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il servizio non e' al momento disponibile.")        
        if(re.search('n="ERRORCODE" v="106"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Contenuto non disponibile.")        
        if(re.search('n="ERRORCODE" v="107"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Hai raggiunto il numero massimo di SMS a tua disposizione oggi.")        
        if(re.search('n="ERRORCODE" v="108"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"E' stato raggiunto il numero massimo di SMS verso il numero destinatario.")        
        if(re.search('n="ERRORCODE" v="109"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Attenzione! Messaggio vuoto.")        
        if(re.search('n="ERRORCODE" v="110"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Hai superato il numero di caratteri disponibili.")        
        if(re.search('n="ERRORCODE" v="111"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Inserisci il numero di cellulare del destinatario.")        
        if(re.search('n="ERRORCODE" v="112"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il numero di cellulare deve essere di nove o dieci cifre e contenere solo caratteri numerici.")        
        if(re.search('n="ERRORCODE" v="113"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il destinatario non e' un utente Vodafone.")        
        if(re.search('n="ERRORCODE" v="114"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Verifica il numero mittente")        
        if(re.search('n="ERRORCODE" v="115"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Attenzione! Errore SIM.")        
        if(re.search('n="ERRORCODE" v="116"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Verifica il codice inserito e invia il tuo SMS.")        
        if(re.search('n="ERRORCODE" v="117"', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Contenuto non disponibile.")

