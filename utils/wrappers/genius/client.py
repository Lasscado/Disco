import re
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from .errors import *
from .song import Song


class Client:
    def __init__(self, client_access_token: str):
        self._base_url = 'https://api.genius.com'
        self.__headers = {"Authorization": 'Bearer ' + client_access_token}

    async def search(self, query: str, limit: int = 10) -> List[Song]:
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.get(self._base_url + f'/search?q={query}') as resp:
                json = await resp.json()

                if json['meta']['status'] != 200:
                    raise ResponseError(json['meta']['message'])

                return [Song(data['result']) for data in json['response']['hits'] if \
                        data['result']['url'].endswith('-lyrics')][:limit]

    async def get_lyrics(self, song: Song) -> str:
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.get(song.url) as resp:
                if resp.status != 200:
                    raise ResponseError('Response returned with code ' + resp.status)

                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')

                div = soup.find('div', class_='lyrics')
                if not div:
                    return

                lyrics = re.sub('\n{2}\[.+\]', '\n', div.get_text())

                return lyrics
