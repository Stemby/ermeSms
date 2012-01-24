# -*- coding: UTF-8 -*-

# TODO: translate to English

import threading
import os
import sys

from PyQt4.QtCore import SIGNAL

from ermesms.plugins.Sender import Sender
from ermesms.CodingManager import CodingManager
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SenderError import SenderError
from ermesms.errors.StopError import StopError
from ermesms.errors.ConnectionError import ConnectionError
from ermesms.errors.CaptchaError import CaptchaError
from ermesms.errors.PreferenceManagerError import PreferenceManagerError
from ermesms.errors.NotFoundError import NotFoundError

class SendMessage(threading.Thread):

    def __init__(self, mf, info):
        threading.Thread.__init__(self)
        self.offline = info['offline']
        self.dest = info['dest']
        self.senderName = info['sender']
        self.text = info['text']
        self.mf = mf
        self.pm = self.mf.pm
        self.masterKey = self.mf.masterKey


    def run(self):
        """Spedisce un messaggio e aggiorna la grafica."""
        #imposta senderName e identifica l'invio offline
        senderName = self.senderName
        sender = Sender.getPlugins()[senderName]

        done = False
        hadError = False
        while done == False:
            try:
                reg = {}
                dn = self.dest
                if sender.requiresRegistration:
                    for i in sender.requiresRegistration:
                        reg[i] = self.pm.getAccount(senderName,i,
                                                    self.masterKey)
                if self.mf.isValid(dn)==False:
                    dn = self.pm.lookup(dn)
                if self.pm.isProxyEnabled():
                    proxy = self.pm.getProxy()
                else:
                    proxy = ''

                #resetta la gauge
                self.mf.gaugeIncrement(0)

                sender.send(proxy, dn, self.text, reg, self.mf)

                #log
                self.mf.emit(SIGNAL('logSave'), senderName, self.dest,
                               sender.replaceSpecialChars(self.text))
                #salvo il gestore
                self.pm.setContactSender(self.dest,senderName)
                #aggiungo 1 ai mex inviati
                textCount=sender.countTexts(sender.replaceSpecialChars(
                    self.text))
                if self.pm.isSentSenderAvailable(senderName):
                    sentmessage = int(self.pm.getSentSender(senderName))+\
                                  textCount
                else: sentmessage = textCount
                self.pm.setSentSender(senderName,str(sentmessage))

                done = True

            except PreferenceManagerError:
                data = {'message' : "Immetti dei dati validi per accedere " + \
                    "al sito " + senderName }
                data['request'] = sender.requiresRegistration
                self.mf.emit(SIGNAL('passRequest'), data)
                data = self.mf.qReq.get(True)
                if not data:
                    done = True
                    hadError = u"L'ultimo SMS non è stato" +\
                               u" inviato a causa di un errore."

                else:
                    for i in sender.requiresRegistration:
                        self.pm.addAccount(i,data[i],senderName,self.masterKey)
            except SiteAuthError:
                data = {'message' : "Dati inseriti non validi, " + \
                          "reimmetterli (sito "+senderName+")"}
                data['request']= sender.requiresRegistration
                for i in data['request']:
                    data[i]= self.pm.getAccount(senderName,i,self.masterKey)
                self.mf.emit(SIGNAL('passRequest'), data)
                data = self.mf.qReq.get(True)
                if not data:
                    done = True
                    hadError = u"L'ultimo SMS non è stato" +\
                               u" inviato a causa di un errore."
                else:
                    self.pm.clearAccount(senderName)
                    for i in sender.requiresRegistration:
                        self.pm.addAccount(i,data[i],senderName,self.masterKey)
            except ConnectionError:
                self.mf.emit(SIGNAL('proxyRequest'))
                data = self.mf.qReq.get(True)
                if not data:
                    done = True
                    hadError = u"L'ultimo SMS non è stato" +\
                               u" inviato a causa di un errore."
            except StopError:
                done = True
                hadError = u"L'ultimo SMS non è stato inviato per" + \
                           u" interruzione dell'utente."
            except (SiteConnectionError, SiteCustomError, SenderError,
                    CaptchaError, NotFoundError), e:
                done = True

                hadError = u"L'ultimo SMS non è stato" +\
                           u" inviato a causa di un errore."
                self.mf.emit(SIGNAL('criticalError'), e.__str__())
            except:
                done = True
                hadError = u"L'ultimo SMS non è stato" +\
                            u" inviato a causa di un errore."
                message = u"Si è verificato un errore imprevisto.\n" + \
                          u"Il sender "+senderName+u" non puo' essere " + \
                          u"utilizzato.\nDettagli dell'errore:\n" + \
                          str(sys.exc_info())
                self.mf.emit(SIGNAL('criticalError'), unicode(message))

        #se invio offline, comunico l'esito
        if self.offline: self.mf.qRes.put(hadError)
        #se invio direttamente aggiorno tutto
        else: self.mf.emit(SIGNAL('sentMessageUpdate'), hadError)


class SendDelayed(threading.Thread):

    def __init__(self, mf, data):
        threading.Thread.__init__(self)
        self.mf = mf
        self.data = data

    def run(self):
        #invio gli sms in un altro thread
        result = []
        for i,data in self.data:
            data['offline'] = True
            t = SendMessage(self.mf, data)
            t.start()
            hadError = self.mf.qRes.get()
            self.mf.offlineSend.emit(SIGNAL('singleSent'), hadError, data)
            result.append((i,hadError,data))
        self.mf.offlineSend.emit(SIGNAL('sentOfflineUpdate'), result)

