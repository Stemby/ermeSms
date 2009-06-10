# -*- coding: utf-8 -*-

import sys
import os
import re
import platform
import subprocess

from cStringIO import StringIO

from moio.plugins.CaptchaDecoder import CaptchaDecoder
from moio.plugins.captchadecoders.Data import charData, lengthData, methodsData, bayesData
from moio.errors.CaptchaError import CaptchaError

class OCRCaptchaDecoder(CaptchaDecoder):
    """Chiede decodifica il captcha tramite programmi OCR (ocrad e gocr).
    Tali programmi devono essere disponibili nel PATH o nella directory dello script."""

    commandsAvailable = False
    """I comandi ocrad, gocr e gm sono disponibili?"""

    ocradCommand = None
    """Path completo e nome del comando ocrad su questo sistema."""

    gocrCommand = None
    """Path completo e nome del comando gocr su questo sistema."""

    gmCommand = None
    """Path completo e nome del comando gm su questo sistema."""

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    """Stringa di tutti i caratteri possibili nel captcha."""

    length = 4
    """Lunghezza in caratteri del captcha."""

    usedDict = {}
    """Dizionario delle statistiche di utilizzo dei metodi."""

    def __init__(self):
        """Costruttore di default."""
        #Tenta di stabilire la posizione dei comandi gm, ocrad e gocr
        paths = ("" ,os.path.abspath(os.path.dirname(sys.argv[0])) , os.getcwd())

        for path in paths:
            ocradCommand = '"'+os.path.join(path, "ocrad")+'" -h'
            gocrCommand ='"'+os.path.join(path, "gocr")+'" -h'
            gmCommand = '"'+os.path.join(path, "gm")+'"'
            gmOutput = self.getOutput(gmCommand, StringIO())
            ocradOutput = self.getOutput(ocradCommand, StringIO())
            gocrOutput = self.getOutput(gocrCommand, StringIO())
            ocradPresent = re.search("GNU Ocrad", ocradOutput) is not None;
            gocrPresent = re.search("Optical Character Recognition", gocrOutput) is not None;
            gmPresent = re.search("Magick", gmOutput) is not None;
            if (gmPresent and ocradPresent and gocrPresent):
                self.commandsAvailable = True
                self.ocradCommand = '"'+os.path.join(path, "ocrad")+'"'
                self.gocrCommand = '"'+os.path.join(path, "gocr")+'"'
                self.gmCommand = '"'+os.path.join(path, "gm")+'"'
                break

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        #Sono riuscito a trovare i comandi necessari?
        return self.commandsAvailable

    def getPriority(self):
        """Ritorna un indice di priorità (intero)."""
        return 2

    def getOutput(self, command, stream):
        """Esegue il comando command collegando allo standard input lo
        stream specificato e ritornando l'output come stringa."""
        #http://mail.python.org/pipermail/python-dev/2006-September/068784.html
        if platform.system() == "Windows" or platform.system() == "Microsoft":
            command = '"'+command+'"'
        #stdin, stdout, stderr = os.popen3(command, "b")
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stream.seek(0)
        out, err = process.communicate(stream.read())
        #In generale ritorna quanto è scritto sullo standard output,
        #ma se è vuoto ristorna eventuali messaggi d'errore.
        if out != "":
            return out
        else:
            return err

    def normalize(self, s):
        """Data una stringa elaborata da un OCR, ritorna una stringa
        composta da esattamente length caratteri con soli caratteri
        consentiti."""
        result1=s.strip().upper()
        result2=""
        for i in result1:
            if i not in self.chars:
                result2+="_"
            else:
                result2+=i
        result3=result2[:self.length]+(self.length-len(result2[:self.length]))*"_"
        return result3

    def gocr(self, stream, gmParams="", gocrParams=""):
        """Decodifica l'immagine leggibile dallo stream specificato filtrandola attraverso
        gm ed utilizzando gocr, con i parametri specificati."""
        guess = self.getOutput(self.gmCommand + " convert " + gmParams + " jpg:- pbm:- |" +
            self.gocrCommand + " " + gocrParams, stream)
        if re.search("NOT NORMAL", guess) is not None:
            raise CaptchaError()
        #Correzione di alcuni "errori frequenti", grazie Fernando
        if len(guess)>self.length:
            guess = guess.replace("LI","U")
            guess = guess.replace("IJ","U")
        return self.normalize(guess)

    def ocrad(self, stream, gmParams="", ocradParams=""):
        """Decodifica l'immagine leggibile dallo stream specificato filtrandola attraverso
        gm ed utilizzando ocrad, con i parametri specificati."""
        guess = self.getOutput(self.gmCommand + " convert " + gmParams + " jpg:- pnm:- |" +
            self.ocradCommand + " " + ocradParams, stream)
        if re.search("convert:", guess) is not None:
            raise CaptchaError()
        #Correzione di alcuni "errori frequenti", grazie Fernando
        guess = guess.replace(" ","")
        guess = guess.replace(".","")
        guess = guess.replace("*","")
        guess = guess.replace("'","")
        guess = guess.replace(",","")
        guess = guess.replace("]","J")
        guess = guess.replace("[","I")
        guess = guess.replace("|","I")
        guess = guess.replace("<","C")
        guess = guess.replace("\\","M")
        guess = guess.replace("r","T")
        guess = guess.replace("?","F")
        guess = guess.replace("lt","H")
        if "l" not in self.chars:
            guess = guess.replace("l","1")
        if "1" not in self.chars:
            guess = guess.replace("1","I")
        if "2" not in self.chars:
            guess = guess.replace("2","Z")
        if "3" not in self.chars:
            guess = guess.replace("3","B")
        if "4" not in self.chars:
            guess = guess.replace("4","A")
        if "5" not in self.chars:
            guess = guess.replace("5","S")
        if "7" not in self.chars:
            guess = guess.replace("7","J")
        if "8" not in self.chars:
            guess = guess.replace("8","B")
        if "9" not in self.chars:
            guess = guess.replace("9","Q")
        if "0" not in self.chars:
            guess = guess.replace("0","O")
        return self.normalize(guess)

    def decodeCaptcha(self, stream, senderName):
        """Questo metodo ritorna la stringa corrispondente all'immagine
        leggibile dallo stream specificato."""

        pbayes = bayesData[senderName]
        methods = methodsData[senderName]
        self.chars = charData[senderName]
        self.length = lengthData[senderName]

        guesses = []
        for method in methods:
            guesses.append(getattr(self, method["command"])(stream, method["gmParams"], method["ocrParams"]))

        guess = ""
        used = ""
        for charIndex in range(self.length):
            maxP = 0
            bestMethodIndex = 0
            for methodIndex, method in enumerate(methods):
                currentP = pbayes[methodIndex][guesses[methodIndex][charIndex]]
                if currentP>maxP:
                    maxP=currentP
                    bestMethodIndex=methodIndex
            guess += guesses[bestMethodIndex][charIndex]
            #self.usedDict[bestMethodIndex]+=1
        return guess

    #Metodi ***esclusivamente*** per lo sviluppo e il testing

    def bayes(self, files, oracles, method):
        """Ritorna il dizionario di probabilità per il metodo specificato."""
        #Guessed char frequencies dictionary
        gkc = {}
        #Read char frequencies dictionary
        rkc = {}
        for i in self.chars:
            gkc[i]=0
            rkc[i]=0

        for i, f in enumerate(files):
            guess = getattr(self, method["command"])(open(f), method["gmParams"], method["ocrParams"])
            for j, c in enumerate(guess):
               rkc[c]+=1
               if c==oracles[i][j]:
                   gkc[c]+=1
        result={}
        for i in self.chars:
            if rkc[i]!=0:
               result[i]=float(gkc[i])/float(rkc[i])
            else:
               result[i]=0
        return result

    def learn(self, senderName):
        """Ritorna il dizionario delle probabilità per un certo sito date le immagini nella cartella
        corrente."""
        methods = methodsData[senderName]
        self.chars = charData[senderName]
        self.length = lengthData[senderName]

        currentDir=os.getcwd()
        files = []
        oracles = []
        for fil in os.listdir(currentDir):
            files.append(currentDir+'/'+fil)
            oracles.append(fil)

        pbayes=[]
        for i, method in enumerate(methods):
            pbayes.append(self.bayes(files, oracles, method))

        return pbayes

    def test(self, senderName):
        """Decodifica le immagini nella cartella corrente."""
        methods = methodsData[senderName]
        self.usedDict = {}
        for i in range(len(methods)):
            self.usedDict[i]=0

        currentDir=os.getcwd()
        files = []
        oracles = []
        for fil in os.listdir(currentDir):
            files.append(currentDir+'/'+fil)
            oracles.append(fil)

        guessed = 0
        total = 0
        for i, f in enumerate(files):
            guess = self.decodeCaptcha(open(f), senderName)
            if oracles[i][:5]==guess:
                guessed+=1
            total+=1
            print "original: "+oracles[i][:5]+" guess: "+guess
        print "G: "+str(guessed)+" T: "+str(total)+" P: "+str(float(guessed)/float(total)*100)
        for i in range(len(methods)):
            print str(methods[i])+" used "+str(self.usedDict[i])+" times"
