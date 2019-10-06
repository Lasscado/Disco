import re
from os import listdir
from json import load

from dotenv import load_dotenv

LOCALE = re.compile('^[a-z]{2}(_[A-Z]{2})?$')

load_dotenv()

with open('./data/emojis.json', encoding='utf-8') as emojis:
    emojis = load(emojis)

with open('./data/avatars.json', encoding='utf-8') as avatars:
    avatars = load(avatars)

locales = {}
for locale in [l for l in listdir('./locales') if LOCALE.match(l)]:
    data = {}
    for archive in listdir(f'./locales/{locale}'):
        data[archive[:-5]] = load(open(f'./locales/{locale}/{archive}', encoding='utf-8'))

    locales[locale] = data
