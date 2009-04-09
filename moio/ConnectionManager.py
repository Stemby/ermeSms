# -*- coding: utf-8 -*-

import re

import pycurl

from moio.lib.singletonmixin import Singleton
from moio.errors.StopError import StopError

class ConnectionManager(Singleton):
    """Ritorna e configura gli oggetti Curl.
    Questa classe vorrebbe essere un Facade su pycurl, anche se al momento
    non lo è completamente."""

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
        #self.curl.setopt(pycurl.VERBOSE, 1)
        self.__setcurl__()

    def __setcurl__(self):
        """Imposta alcuni valori che possono essere stati modificati"""
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.USERAGENT, 'Mozilla/5.0 (Windows; U; Windows NT 6.0; it; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6')
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
        self.curl.setopt(pycurl.PROXY, proxy)

    def doNothing(self, args):
        """Funzione-parametro per pycurl, scarta la pagina richiesta."""
        pass

    def ePerform(self, stop = None):
        if stop: raise StopError()
        else: self.curl.perform()
