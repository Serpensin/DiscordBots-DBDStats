import aiohttp




class LibreTranslateAPI:
    def __init__(self, APIkey = ''):
        self.APIkey = APIkey
        self.url = "https://translate.bloodygang.com"


    async def _get_sample(self, text):
        sentences = text.split('. ')
        first_sentence_words = sentences[0].split(' ')

        if len(first_sentence_words) > 10:
            sample = ' '.join(first_sentence_words[:10])
        else:
            sample = ' '.join(first_sentence_words)

        return sample


    async def detect(self, text):
        url = f"{self.url}/detect"
        params = {
            "q": text,
            "api_key": self.APIkey
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                return {"status": response.status, "data": data}


    async def translate(self, text, dest_lang, source = ''):
        url = f'{self.url}/translate'
        if source == '':
            source = await self.detect(await self._get_sample(text))
            source = source["data"][0]["language"]
        params = {
            "q": text,
            "source": source,
            "target": dest_lang,
            "api_key": self.APIkey
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                return {"status": response.status, "data": data}







