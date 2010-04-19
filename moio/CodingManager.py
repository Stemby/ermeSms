# -*- coding: utf-8 -*-

import locale
import sys
import urllib

from moio.lib.singletonmixin import Singleton

class CodingManager(Singleton):
    """Qualche metodo utile per la gestione delle stringhe Unicode."""

    stdinEncoding = "iso-8859-1"
    stdoutEncoding = "iso-8859-1"
    argvEncoding = "iso-8859-1"

    def __init__(self):
        """Costruttore di default."""
        testString = "ciao"
        try:
            if sys.stdout.encoding is not None:
                testString.encode(sys.stdout.encoding)
                self.stdoutEncoding = sys.stdout.encoding
        except (LookupError, AttributeError):
            pass
        try:
            if sys.stdin.encoding is not None:
                testString.decode(sys.stdin.encoding)
                self.stdinEncoding = sys.stdin.encoding
        except (LookupError, AttributeError):
            pass
        defaultLocale = locale.getdefaultlocale()[1]
        if defaultLocale is not None:
            try:
                testString.decode(defaultLocale)
                self.argvEncoding = defaultLocale
            except LookupError:
                pass

    def unicodeStdin(self, string):
        """Converte una stringa presa dallo standard input in Unicode."""
        return string.decode(self.stdinEncoding)

    def unicodeArgv(self, string):
        """Converte una stringa dagli argomenti in Unicode."""
        return string.decode(self.argvEncoding)

    def encodeStdout(self, unicodeString):
        """Converte una stringa Unicode in stringa stampabile su stdout"""
        return unicodeString.encode(self.stdoutEncoding, "replace")

    def quoteUnicode(self, unicodeString):
        """Converte una stringa Unicode in ASCII codificato."""
        return unicodeString.encode("unicode_escape", "replace")

    def unQuoteUnicode(self, string):
        """Converte una stringa da ASCII codificato a Unicode."""
        return string.decode("unicode_escape")

    def quoteBase64(self, bitString):
        """Converte una stringa di bit in ASCII codificato."""
        return bitString.encode("base64")

    def unQuoteBase64(self, string):
        """Converte una stringa da ASCII codificato a stringa di bit."""
        return string.decode("base64")

    def urlEncode(self, dictionary):
        """Converte il dizionario in una stringa in formato
        application/x-www-form-urlencoded"""
        #Per evitare errori di codifica, sostituisco con ? i
        #caratteri non-ascii
        safeDictionary = {}
        for k, v in dictionary.iteritems():
            safeDictionary[k.encode("ascii", "replace")] = v.encode("ascii", "replace")
        return urllib.urlencode(safeDictionary)

    def xmlEncode(self, unicodeString, encoding="ascii"):
        """
        Encode unicode_data for use as XML or HTML, with characters outside
        of the encoding converted to XML numeric character references.
        """
        result = unicodeString.replace("&", "&amp;")
        result = result.encode(encoding, 'xmlcharrefreplace')
        result = result.replace("<", "&lt;")
        result = result.replace(">", "&lt;")
        return result

    def iso88591ToUnicode(self, string):
        """Converte una stringa da iso-8859-1 a Unicode."""
        return string.decode("iso-8859-1")

    def unicodeToIso88591(self, string):
        """Converte una stringa da iso-8859-1 a Unicode."""
        return string.encode("iso-8859-1", "replace")
