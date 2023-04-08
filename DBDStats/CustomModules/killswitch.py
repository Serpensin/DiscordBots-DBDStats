import aiohttp
from bs4 import BeautifulSoup
import re


async def get():
    url = "https://forums.bhvr.com/dead-by-daylight/kb/articles/299-kill-switch-master-list"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            def entry_to_dict(text, start_marker, end_marker):
                start_index = text.find(start_marker) + len(start_marker)
                end_index = text.find(end_marker, start_index)
                extracted_text = text[start_index:end_index].strip()
                print(extracted_text)
                result = {}
                split_index = extracted_text.index("has")
                parts = [extracted_text[:split_index].strip(), extracted_text[split_index:].strip()]
                sentences = re.split('([.!?] *)', parts[1])
                capitalized = [word.capitalize() for word in sentences if word.strip()]
                result[parts[0]] = ' '.join(capitalized).replace(" .", ".")
                return result
            
            if response.status == 200:
                try:
                    text = await response.text()
                    soup = BeautifulSoup(text, "html.parser")
                    p_tags = soup.find_all('div')[1].get_text()
                    retext = str(p_tags)
                    text = str(re.sub("<.*?>", "", retext))
                    start_marker = "Kill Switch (Disabled)"
                    end_marker = "Known Issues (Not Disabled)"
                    extracted_text = entry_to_dict(text, start_marker, end_marker)
                    print(extracted_text)
                    print(type(extracted_text))
                except:
                    return None
            else:
                return 1
