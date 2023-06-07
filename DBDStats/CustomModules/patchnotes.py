import aiohttp
from bs4 import BeautifulSoup
import asyncio
import html2text



async def get_update_content(version, return_type='html'):
    url = 'https://dbd.tricky.lol/patchnotes'
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')
            update_divs = soup.find_all('div', class_='update')

            for update_div in update_divs:
                h1_tags = update_div.find_all('h1')
                for h1 in h1_tags:
                    if version in h1.text:
                        if return_type == 'html':
                            return update_div.prettify()
                        elif return_type == 'md':
                            return converter.handle(update_div.prettify())

    return None



if __name__ == '__main__':
    version = '6.2.1'
    content = asyncio.run(get_update_content(version, 'md'))
    print(content)

    