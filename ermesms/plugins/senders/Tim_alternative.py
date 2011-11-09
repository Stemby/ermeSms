# -*- coding: utf-8 -*-

# Versione modificata da Paolo Viotti in data 8/12/2010
# Usa mechanize invece di pycurl

import re
import sys
#import traceback
from cStringIO import StringIO

#import pycurl
import urllib
import mechanize

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
#from ermesms.plugins.CaptchaDecoder import CaptchaDecoder
from ermesms.plugins.captchadecoders.AskUserCaptchaDecoder import AskUserCaptchaDecoder
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.CaptchaError import CaptchaError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class Tim(Sender):
    """Permette di spedire SMS dal sito di tim.it"""

    maxLength = 640
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
            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                u"Questo sito permette di inviare SMS solo verso cellulari italiani.")

            br = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))
            br.addheaders = [('User-agent', 'Opera/9.51 Beta (Microsoft Windows; PPC; Opera Mobi/1718; U; en)')]
              
            br.open("http://www.tim.it")
            br.select_form(nr=1)
            br.form["login"] = dati['Nome utente']
            br.form["password"] = dati['Password']
            res = br.submit()
            if ui: ui.gaugeIncrement(self.incValue)

            req = br.click_link(text='SMS da Web')
            res = br.open(req)
            br.select_form(nr=0)
            br.form["freeNumbers"] = number
            br.form["textAreaStandard"] = text
            res = br.submit()
            if ui: ui.gaugeIncrement(self.incValue)

            captchaBroken = False
            while captchaBroken == False:
                postFields = {}
                try:
                    saver = StringIO()
                    br.retrieve('https://smsweb.tim.it/sms-web/validatecaptcha:image/false?t:ac=Dispatch', "/tmp/captcha") # "/tmp/captcha": NON PORTABILE
                    saver.write(open("/tmp/captcha", "r").read())   # BRUTTO
                    postFields["verificationCode"] = AskUserCaptchaDecoder.getInstance().decodeCaptcha(saver, self.__class__.__name__)
                except CaptchaError:
                    raise SenderError(self.__class__.__name__)

                if not postFields["verificationCode"]:
                    raise SiteCustomError(self.__class__.__name__,
                                    u"Captcha non inserito. Invio interrotto.")
				
                br.select_form(nr=0)
                postFields["t:ac"] = "Dispatch"
                postFields["t:formdata"] = br.form.controls[1]._value
                params = urllib.urlencode(postFields)
                f = br.open("https://smsweb.tim.it/sms-web/validatecaptcha.validatecaptchaform", params)
                if not re.search(u"Le lettere che hai inserito non corrispondono a quelle presenti nell'immagine", br.response().get_data()):
                    captchaBroken = True

            self.checkForErrors(br.response().get_data())

            if (re.search("SMS inviato", br.response().get_data()) is None):
                raise SenderError(self.__class__.__name__)

        except Exception as e:
            #traceback.print_exc(file=sys.stdout)
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(e.message))

    def checkForErrors(self, page):
        if (re.search(u'"Messaggio Errore"', page) is not None) or \
           (re.search(u'Bad Gateway', page) is not None) or \
           (re.search(u'Il servizio &egrave; momentaneamente non disponibile', page) is not None) or \
           (re.search(u'Siamo spiacenti, la pagina che hai richiesto al momento non &egrave; disponibile.', page) is not None) or \
           (re.search(u'Internal Server Error', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il servizio non \W?\W? al momento disponibile.")
        if (re.search(u'SMS non inviato, il numero non \W?\W? TIM', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il destinatario non e' un numero Tim.")
        if (re.search(u'numero massimo di SMS', page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Hai raggiunto il limite di SMS per oggi.")
        if (re.search(u'essere autenticati', page) is not None) or \
           (re.search(u'loginerror.do', page) is not None):
            raise SiteAuthError(self.__class__.__name__)
