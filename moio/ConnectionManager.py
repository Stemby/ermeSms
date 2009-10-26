# -*- coding: utf-8 -*-

import re
import time
import pycurl
from cStringIO import StringIO

from moio.lib.singletonmixin import Singleton
from moio.errors.StopError import StopError

class ConnectionManager(Singleton):
    """Ritorna e configura gli oggetti Curl.
    Questa classe vorrebbe essere un Facade su pycurl, anche se al momento
    non lo è completamente."""

    debug = None
    debugDataOld = None
    """Valori utilizzati dalla debug mode"""    

    curl = None
    """Istanza dell'oggetto Curl per la comunicazione con le librerie
    libcurl."""

    def __init__(self):
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.COOKIEFILE, "")
        self.curl.setopt(pycurl.ENCODING, "") #abilita gzip
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)# non verifica il certificato SSL
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 0)
        self.curl.setopt(pycurl.TIMEOUT, 30)
        self.__setcurl__()

    def __setcurl__(self):
        """Imposta alcuni valori che possono essere stati modificati"""
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.USERAGENT, 'Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)')
        self.curl.setopt(pycurl.POST, False)

    def getCurl(self):
        """Ritorna un oggetto Curl (unica istanza nell'applicazione)"""
        self.__setcurl__()
        return self.curl

    def forgetCookiesFromDomain(self, domain):
        """Rimuove i cookie di un certo dominio."""
        cookieList= self.curl.getinfo(pycurl.INFO_COOKIELIST)
        #Toglie tutto
        self.curl.setopt(pycurl.COOKIELIST, "ALL")
        #Rimette il resto
        for i in cookieList:
            if (re.search(domain,i) is None):
                self.curl.setopt(pycurl.COOKIELIST, i)

    def isInternetReachable(self):
        """Ritorna True se Internet è raggiungibile."""
        #Pare che al momento non esistano modi migliori...
        return self.ping("http://www.google.it")

    def ping(self, url):
        """Ritorna True se il sito all'url specificato è raggiungibile."""
        try:
            c = self.getCurl()
            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
            c.setopt(pycurl.URL, url)
            c.perform()
        except pycurl.error:
            return False
        return True

    def setCurlProxy(self, proxy):
        """Imposta il proxy del curl"""
        self.curl.setopt(pycurl.PROXY, str(proxy))

    def doNothing(self, args):
        """Funzione-parametro per pycurl, scarta la pagina richiesta."""
        pass

    def debugFunction(self, arg1, arg2):
        """Funzione per il salvataggio dei dati di debug"""
        fdebug = open('debug.xml', 'ab')
        if arg1 == pycurl.INFOTYPE_DATA_IN: debugData = 'DataIn'
        if arg1 == pycurl.INFOTYPE_DATA_OUT: debugData = 'DataOut'
        if arg1 == pycurl.INFOTYPE_TEXT: debugData = 'Text'
        if arg1 == pycurl.INFOTYPE_HEADER_IN: debugData = 'HeaderIn'
        if arg1 == pycurl.INFOTYPE_HEADER_OUT: debugData = 'HeaderOut'
        if arg1 == pycurl.INFOTYPE_SSL_DATA_IN: debugData = 'SSLIn'
        if arg1 == pycurl.INFOTYPE_SSL_DATA_OUT: debugData = 'SSLOut'
        if not self.debugDataOld == debugData:
            if self.debugDataOld: fdebug.write('\n</'+self.debugDataOld+'>\n')
            fdebug.write('<'+debugData+'>\n')
            self.debugDataOld = debugData
        fdebug.write(arg2)
        fdebug.close()

    def ePerform(self, stop = None, saver = None):
        """Funzione che sostituisce il normale perform per permettere lo
        stop dell'invio e salvare i dati in debug mode"""
        if stop: raise StopError()
        if self.debug == 'On':
            self.curl.setopt(pycurl.VERBOSE, 1)
            self.curl.setopt(pycurl.DEBUGFUNCTION, self.debugFunction)
        else:
            self.curl.setopt(pycurl.VERBOSE, 0)            
        if not saver and self.debug == 'On':
                saver = StringIO()
                saverwrite = saver.write
        elif not saver and not self.debug: saverwrite = self.doNothing
        else: saverwrite = saver.write
        self.curl.setopt(pycurl.WRITEFUNCTION, saverwrite)
        self.curl.perform()
        if self.debug == 'On':
            f = open(str(int(time.time()))+'.txt', 'wb')
            f.write(saver.getvalue())
            f.close
