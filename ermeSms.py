#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Un programma per mandare SMS via Internet.

Con questo piccolo programma a base di pycurl ed espressioni regolari sarete
in grado di inviare dei Brevi Messaggi di Testo (SMS) in modo semplice e
veloce, attraverso uno dei siti che permettono di inviarli.
Login manager e rubrica telefonica sono inclusi.
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
from ermesms.plugins.UI import UI
from ermesms.FatalExceptionHandler import FatalExceptionHandler

#carico tutti i plugin dell'applicazione
from ermesms.plugins.senders import *
from ermesms.plugins.uis import *
from ermesms.plugins.captchadecoders import *

#Ricerca la migliore interfaccia utilizzabile (interfaccia disponibile
#a priorita' massima)
bestUI = UI.getBestPlugin()

#Inizializza il gestore delle eccezioni fatali
FatalExceptionHandler(bestUI)

#Manda in esecuzione l'interfaccia
bestUI.run()
