#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Un programma per mandare SMS via Internet.

Con questo piccolo programma a base di pycurl ed espressioni regolari sarete
in grado di inviare dei Brevi Messaggi di Testo (SMS) in modo semplice e
veloce, attraverso uno dei siti che permettono di inviarli.
Login manager e rubrica telefonica sono inclusi.

Creato e mantenuto da Silvio Moioli (silvio@moioli.net), www.moioli.net
Distribuito in licenza GNU GPL.
"""
#controlla che il programma non sia gia'  avviato
try:
    import psutil
    from os import getpid
except: pass
else:
    this = psutil.Process(getpid())
    quit() if (this.cmdline in [i.cmdline if i.pid != getpid() else [] for i in psutil.get_process_list()]) else None

#carico i moduli e avvio il programma
from moio.plugins.UI import UI
from moio.FatalExceptionHandler import FatalExceptionHandler

#carico tutti i plugin dell'applicazione
from moio.plugins.senders import *
from moio.plugins.uis import *
from moio.plugins.captchadecoders import *
from moio.plugins.books import *

#Ricerca la migliore interfaccia utilizzabile (interfaccia disponibile
#a priorita' massima)
bestUI = UI.getBestPlugin()

#Inizializza il gestore delle eccezioni fatali
FatalExceptionHandler(bestUI)

#Manda in esecuzione l'interfaccia
bestUI.run()
