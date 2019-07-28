from .data import locales
from functools import reduce
from os import environ

fallback = environ['FALLBACK_LOCALE']

def l(locale, value):
    if hasattr(locale, 'locale'):
        locale = locale.locale

    navigate = value.split('.')
    return reduce(dict.get, navigate, locales[locale]) \
        or reduce(dict.get, navigate, locales[fallback])