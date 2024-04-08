﻿import aiohttp
import asyncio



class Errors:
    class InvalidAPIKey(Exception):
        def __init__(self, message="Invalid API key or URL."):
            self.message = message
            super().__init__(self.message)

    class BadRequest(Exception):
        def __init__(self, message="Bad Request: The request was invalid."):
            self.message = message
            super().__init__(self.message)

    class Forbidden(Exception):
        def __init__(self, message="Forbidden: The API key is invalid or the request is not authorized."):
            self.message = message
            super().__init__(self.message)

    class RateLimitExceeded(Exception):
        def __init__(self, message="Rate Limit Exceeded: The request was rate limited."):
            self.message = message
            super().__init__(self.message)

    class InternalServerError(Exception):
        def __init__(self, message="Internal Server Error: The server encountered an error."):
            self.message = message
            super().__init__(self.message)



class API:
    """
    Class for interacting with a translation API asynchronously using aiohttp.
    """

    def __init__(self, APIkey, url):
        """
        Initialize the API object.

        Args:
            APIkey (str): The API key for accessing the translation API.
            url (str): The base URL of the translation API.

        Raises:
            Errors.InvalidAPIKey: If the provided API key is invalid.
        """
        self.APIkey = APIkey
        try:
            self.url = url.rstrip('/')
        except AttributeError:
            raise ValueError("Invalid URL provided.")

        isValid = asyncio.run(self.validate_key())
        if not isValid:
            raise Errors.InvalidAPIKey()

    def _get_sample(self, text, isFile=False) -> str:
        """
        Extract a sample text from either a string or a file.

        Args:
            text (str): The input text or path to the file.
            isFile (bool): Indicates whether the input is a file path.

        Returns:
            str: The sample text.
        """
        if isFile:
            with open(text, 'r') as file:
                text = file.read()

        first_words = text.split(' ')
        if len(first_words) > 20:
            sample = ' '.join(first_words[:20])
        else:
            sample = ' '.join(first_words)

        return sample

    async def detect(self, text) -> dict:
        """
        Asynchronously detect the language of a given text.

        Args:
            text (str): The input text to detect language.

        Returns:
            dict: A dictionary containing the HTTP response status and detected language data.

        Raises:
            Errors.BadRequest: If the request is invalid.
            Errors.Forbidden: If the API key is invalid or the request is not authorized.
            Errors.RateLimitExceeded: If the request was rate limited.
            Errors.InternalServerError: If the server encountered an error.
        """
        url = f"{self.url}/detect"
        params = {
            "q": text,
            "api_key": self.APIkey
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                data = await response.json()
                response_data = {"status": response.status, "data": data}
                if response.status == 200:
                    return response_data
                elif response.status == 400:
                    raise Errors.BadRequest(response_data)
                elif response.status == 403:
                    raise Errors.Forbidden(response_data)
                elif response.status == 429:
                    raise Errors.RateLimitExceeded(response_data)
                elif response.status == 500:
                    raise Errors.InternalServerError(response_data)

    async def translate_text(self, text, dest_lang, source='') -> str:
        """
        Asynchronously translate a given text to the specified destination language.

        Args:
            text (str): The input text to translate.
            dest_lang (str): The destination language code.
            source (str, optional): The source language code. Defaults to ''.

        Returns:
            str: The translated text.

        Raises:
            Errors.BadRequest: If the request is invalid.
            Errors.Forbidden: If the API key is invalid or the request is not authorized.
            Errors.RateLimitExceeded: If the request was rate limited.
            Errors.InternalServerError: If the server encountered an error.
        """
        url = f'{self.url}/translate'
        if source == '':
            source = await self.detect(self._get_sample(text))
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
                if response.status == 200:
                    return data['translatedText']
                elif response.status == 400:
                    raise Errors.BadRequest(data)
                elif response.status == 403:
                    raise Errors.Forbidden(data)
                elif response.status == 429:
                    raise Errors.RateLimitExceeded(data)
                elif response.status == 500:
                    raise Errors.InternalServerError(data)

    async def get_settings(self) -> dict:
        """
        Asynchronously retrieve settings from the translation API.

        Returns:
            dict: A dictionary containing the settings data.
        """
        url = f'{self.url}/frontend/settings'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def validate_key(self) -> bool:
        """
        Asynchronously validate the API key.

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        data = await self.detect("Hello")
        if data["status"] == 200:
            return True
        else:
            return False

    async def get_languages(self) -> list:
        """
        Asynchronously retrieve a list of supported languages from the translation API.

        Returns:
            list: A list of supported languages.
        """
        url = f'{self.url}/languages'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        except:
            return None

    async def translate_file(self, file, dest_lang, source='') -> str:
        """
        Asynchronously translate the content of a file to the specified destination language.

        Args:
            file (str): The path to the file to translate.
            dest_lang (str): The destination language code.
            source (str, optional): The source language code. Defaults to ''.

        Returns:
            str: The URL of the translated file.

        Raises:
            Errors.BadRequest: If the request is invalid.
            Errors.Forbidden: If the API key is invalid or the request is not authorized.
            Errors.RateLimitExceeded: If the request was rate limited.
            Errors.InternalServerError: If the server encountered an error.
        """
        url = f'{self.url}/translate_file'
        if source == '':
            source = await self.detect(self._get_sample(file, True))
            source = source["data"][0]["language"]
        params = {
            "source": source,
            "target": dest_lang,
            "api_key": self.APIkey
        }
        files = {
            "file": open(file, 'rb')
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, data=files) as response:
                data = await response.json()
                if response.status == 200:
                    return data['translatedFileUrl']
                elif response.status == 400:
                    raise Errors.BadRequest(data)
                elif response.status == 403:
                    raise Errors.Forbidden(data)
                elif response.status == 429:
                    raise Errors.RateLimitExceeded(data)
                elif response.status == 500:
                    raise Errors.InternalServerError(data)




if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()

    translator = API(APIkey=os.getenv("libretransAPIkey"), url=os.getenv("libretransURL"))
    # print(asyncio.run(translator.detect("Hello, how are you?")))
    # print(asyncio.run(translator.translate("Hello, how are you?", 'de')))
    # print(asyncio.run(translator.get_languages()))
    # print(asyncio.run(translator.get_settings()))
    ttt = asyncio.run(translator.translate_file('translation_test.txt', 'de'))
    print(ttt)