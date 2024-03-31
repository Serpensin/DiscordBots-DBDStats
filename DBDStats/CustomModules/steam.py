import aiohttp
import asyncio
import http



class Errors:
    class Private(Exception):
        """Custom error indicating an attempt to access a private profile."""

        def __init__(self, message="This profile is private."):
            self.message = message
            super().__init__(self.message)

    class RateLimit(Exception):
        """Custom error indicating the exceeding of a rate limit."""

        def __init__(self, message="Rate limit exceeded."):
            self.message = message
            super().__init__(self.message)

    class InvalidKey(Exception):
        """Custom error indicating that the key is invalid."""

        def __init__(self, message="Invalid key."):
            self.message = message
            super().__init__(self.message)





class API():
    def __init__(self, key):
        self.KEY = key
        self.URL_GetOwnedGames = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={key}&steamid='
        self.URL_ResolveVanity = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={key}&vanityurl='
        self.URL_GetPlayerAchievements = f'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={key}&steamid='
        self.URL_GetPlayerSummeries = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={key}&steamids='

        isValid = asyncio.run(self.keyIsValid())
        if not isValid:
            raise Errors.InvalidKey()




    async def keyIsValid(self) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.URL_GetPlayerSummeries}76561198889439823') as response:
                if response.status != 200:
                    return False
                else:
                    data = await response.json()
        if 'response' in data and 'players' in data['response']:
            return True
        else:
            return False



    async def get_player_summeries(self, steamid) -> dict:
        steamids = steamid.split(',')
        cleaned_steamids = ''
        for entry in steamids:
            check = await self.link_to_id(str(entry).strip())
            if check is None:
                raise ValueError('Invalid steamid or link.')
            else:
                cleaned_steamids += f'{check},'
        cleaned_steamids = cleaned_steamids.removesuffix(',')
        url = f'{self.URL_GetPlayerSummeries}{cleaned_steamids}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                elif response.status != 200:
                    return{"error": {"code": response.status, "message": http.HTTPStatus(response.status).phrase}}
                data = await response.json()
        return data






    async def get_player_achievements(self, steamid, appid) -> dict:
        steamid = await self.link_to_id(steamid)
        if steamid is None:
            raise ValueError('Invalid steamid or link.')
        url = f'{self.URL_GetPlayerAchievements}{steamid}&appid={appid}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                elif response.status != 200:
                    return{"error": {"code": response.status, "message": http.HTTPStatus(response.status).phrase}}
                data = await response.json()
        return data



    async def link_to_id(self, link) -> str:
        link = link.replace('https://steamcommunity.com/profiles/', '').replace('https://steamcommunity.com/id/', '').replace('/', '')
        if len(link) == 17 and link.isdigit():
            return link
        url = f'{self.URL_ResolveVanity}{link}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                elif response.status != 200:
                    return{"error": {"code": response.status, "message": http.HTTPStatus(response.status).phrase}}
                data = await response.json()
        return data['response']['steamid'] if data['response']['success'] == 1 else None


    async def ownsGame(self, steamid, appid) -> bool:
        steamid = await self.link_to_id(steamid)
        if steamid is None:
            raise ValueError('Invalid steamid or link.')
        url = f'{self.URL_GetOwnedGames}{steamid}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                elif response.status != 200:
                    return{"error": {"code": response.status, "message": http.HTTPStatus(response.status).phrase}}
                data = await response.json()
        try:
            for game in data['response']['games']:
                if game['appid'] == appid:
                    return True
        except KeyError:
            if data == {'response': {}}:
                raise Errors.Private()
            else:
                return False
        return False




if __name__ == '__main__':
    try:
        api = API('')
    except Errors.InvalidKey as e:
        print(e)
    try:
        print(asyncio.run(api.get_player_summeries('Schlangensuende, 76561197969978546')))
    except Errors.Private as e:
        print(e)