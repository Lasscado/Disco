from json import load

from dotenv import load_dotenv

load_dotenv()

with open('./data/emojis.json', encoding='utf-8') as emojis:
    emojis = load(emojis)

with open('./data/avatars.json', encoding='utf-8') as avatars:
    avatars = load(avatars)
