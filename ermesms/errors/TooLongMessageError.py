# -*- coding: utf-8 -*-

class TooLongMessageError(Exception):
    """Indica che il messaggio specificato eccede le dimensioni gestibili da MoioSMS."""

    def __init__(self):
        Exception.__init__(self)

    def __str__(self):
        return u"Il messaggio è troppo lungo."
