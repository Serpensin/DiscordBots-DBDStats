from google.auth.exceptions import RefreshError
from google.cloud import translate_v2 as translate



class Translator:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.translate_client = translate.Client.from_service_account_json(self.credentials_path)

        try:
            self.check_credentials()
        except Exception as e:
            raise Exception(e)



    def translate_text(self, text, target_language, source_language = "en") -> str:
        try:
            result = self.translate_client.translate(text, target_language=target_language, source_language=source_language)
            return result["translatedText"]
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except RefreshError as e:
            raise RefreshError(e)

    def check_credentials(self) -> bool:
        try:
            result = self.translate_client.translate("Ping", target_language="en")
            if result["translatedText"] == "Ping":
                return True
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except RefreshError as e:
            raise RefreshError(e)

    def get_languages(self):
        try:
            languages = self.translate_client.get_languages()
            return languages
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except RefreshError as e:
            raise RefreshError(e)




if __name__ == '__main__':
    credentials_path = "googleauth.json"
    translator = Translator(credentials_path)

    text = "Hello"
    translated_text = translator.translate_text(text, target_language="de")
    print(translated_text)

    credentials_valid = translator.check_credentials()
    print(credentials_valid)