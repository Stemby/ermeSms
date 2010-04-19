# -*- coding: utf-8 -*-
"""Un programma per mandare SMS via Internet.

Con questo piccolo programma a base di pycurl ed espressioni regolari sarete
in grado di inviare dei Brevi Messaggi di Testo (SMS) in modo semplice e
veloce, attraverso uno dei siti che permettono di inviarli.
Login manager e rubrica telefonica sono inclusi.

Creato e mantenuto da Silvio Moioli (silvio@moioli.net), www.moioli.net
Distribuito in licenza GNU GPL.
"""
#controlla che il programma non sia già avviato
try:
    import psutil, os
except: pass
else:
    this = psutil.Process(os.getpid())
    count = 0
    for i in psutil.get_process_list():
        try:
            if i.cmdline == this.cmdline: count +=1
        except: pass
    if count > 1:
        import sys
        sys.exit(0)

#carico i moduli e avvio il programma
from moio.plugins.UI import UI
from moio.FatalExceptionHandler import FatalExceptionHandler

#carico tutti i plugin dell'applicazione
from moio.plugins.senders import *
from moio.plugins.uis import *
from moio.plugins.captchadecoders import *

#Ricerca la migliore interfaccia utilizzabile (interfaccia disponibile
#a priorità massima)
bestUI = UI.getBestPlugin()

#Inizializza il gestore delle eccezioni fatali
FatalExceptionHandler(bestUI)

#Manda in esecuzione l'interfaccia
bestUI.run()
