from .data import locales
from functools import reduce
from os import environ

fallback = environ['FALLBACK_LOCALE']

def l(locale, path, values = {}):
    if hasattr(locale, 'locale'):
        locale = locale.locale

    keys = path.split('.')
    try:
        string = locales[locale]
        for k in keys:
            string = string[k]
    except KeyError:
        try:
            string = locales[fallback]
            for k in keys:
                string = string[k]
        except KeyError:
            return path

    return string.format(**values)