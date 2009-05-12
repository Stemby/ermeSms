# -*- coding: utf-8 -*-

import re
import sys
from cStringIO import StringIO

import pycurl
import urllib

from moio.plugins.Sender import Sender
from moio.ConnectionManager import ConnectionManager
#from moio.plugins.CaptchaDecoder import CaptchaDecoder
from moio.plugins.captchadecoders.AskUserCaptchaDecoder import AskUserCaptchaDecoder
from moio.errors.SiteCustomError import SiteCustomError
from moio.errors.SiteConnectionError import SiteConnectionError
from moio.errors.CaptchaError import CaptchaError
from moio.errors.SiteAuthError import SiteAuthError
from moio.errors.SenderError import SenderError

class TimNEW(Sender):
    """Permette di spedire SMS dal sito di tim.it"""

    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 4
    """Incremento della gauge per pagina."""

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        #Deve essere disponibile un qualunque CaptchaDecoder
        return AskUserCaptchaDecoder.getInstance().isAvailable()

    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima
        maxLength con le credenziali specificate, supponendo Internet
        raggiungibile."""

        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()

            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                u"Questo sito permette di inviare SMS solo verso cellulari italiani.")

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            c.setopt(pycurl.URL, "http://www.tim.it")            
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            #Faccio il login
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["urlOk"] = "https://www.tim.it/119/consumerdispatcher"
            postFields["portale"] = "timPortale"
            postFields["login"] = username
            postFields["password"] = password
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL,
                "https://www.tim.it/authfe/login.do")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())            

            if ui: ui.gaugeIncrement(self.incValue)

            c.setopt(pycurl.URL,
                "https://smsweb.tim.it/sms-web/adddispatch?start=new")
            saver = StringIO()            
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            try:
                formdata1 = re.search('(?<=(name="addDispatchForm"><div class="t-invisible"><input name="t:formdata" type="hidden" value="))[^"]+', saver.getvalue()).group(0)
                formdata2 = re.search('(?<=(seperateFreeNumbers:hidden" name="t:formdata" type="hidden" value="))[^"]+', saver.getvalue()).group(0)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            try:
                jsession = re.search('(?<=(adddispatch.adddispatchform;jsessionid=))[^"]+', saver.getvalue()).group(0)
            except: jsession = None

            if ui: ui.gaugeIncrement(self.incValue)

            postFields = {}
            postFields["t:formdata"] = formdata2
            postFields["recipientType"] = 'FREE_NUMBERS'
            postFields["freeNumbers"] = number
            postFields["textAreaStandard"] = text
            postFields["deliverySmsClass"] = 'STANDARD'
            postdata = self.codingManager.urlEncode(postFields)+"&"+\
                       urllib.urlencode({"t:formdata":formdata1})
            c.setopt(pycurl.POSTFIELDS, postdata )
            c.setopt(pycurl.POST, True)
            url = "https://smsweb.tim.it/sms-web/adddispatch.adddispatchform"                      
            if jsession: url += ";jsessionid="+jsession
            c.setopt(pycurl.URL, url )
            saver = StringIO()
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            try:
                formdata = re.search('(?<=(value="Dispatch"></input><input name="t:formdata" type="hidden" value="))[^"]+', saver.getvalue()).group(0)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            captchaBroken = False
            while captchaBroken == False:
                postFields = {}                
                try:
                    saver = StringIO()
                    c.setopt(pycurl.POST, False)
                    c.setopt(pycurl.URL, "https://smsweb.tim.it/sms-web/validatecaptcha:image/false?t:ac=Dispatch" )
                    self.perform(self.stop, saver)
                    #postFields["verificationCode"] = CaptchaDecoder.getBestPlugin().decodeCaptcha(saver, self.__class__.__name__)
                    postFields["verificationCode"] = AskUserCaptchaDecoder.getInstance().decodeCaptcha(saver, self.__class__.__name__)
                except CaptchaError:
                    raise SenderError(self.__class__.__name__)
                
                if not postFields["verificationCode"]:
                    raise SiteCustomError(self.__class__.__name__,
                                    u"Captcha non inserito. Invio interrotto.")                
                
                postFields["t:formdata"] = formdata
                postFields["t:ac"] = "Dispatch"
                c.setopt(pycurl.POSTFIELDS,
                    self.codingManager.urlEncode(postFields))                
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.URL, "https://smsweb.tim.it/sms-web/validatecaptcha.validatecaptchaform" )
                saver = StringIO()
                self.perform(self.stop, saver)

                if not re.search(u"Le lettere che hai inserito non corrispondono a quelle presenti nell'immagine", saver.getvalue()):
                    captchaBroken = True

            self.checkForErrors(saver.getvalue())

            if (re.search("SMS inviato", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error as e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        if (re.search(u'"Messaggio Errore"', page) is not None) or \
           (re.search(u'Bad Gateway', page) is not None) or \
           (re.search(u'Il servizio &egrave; momentaneamente non disponibile', page) is not None) or \
           (re.search(u'Siamo spiacenti, la pagina che hai richiesto al momento non &egrave; disponibile.', page) is not None) or \
           (re.search(u'Internal Server Error', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il servizio non è al momento disponibile.")
        if (re.search(u'SMS non inviato, il numero non &egrave; TIM', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il destinatario non e' un numero Tim.")
        if (re.search(u'numero massimo di SMS', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Hai raggiunto il limite di SMS per oggi.")
        if (re.search(u'essere autenticati', page) is not None) or \
           (re.search(u'loginerror.do', page) is not None):
            raise SiteAuthError(self.__class__.__name__)
