import aiohttp
import html2text
import re
from bs4 import BeautifulSoup



async def get_update_content(version: str = None, return_type='html'):
    url = 'https://dbd.tricky.lol/patchnotes'
    converter = html2text.HTML2Text()
    converter.ignore_links = True

    if version is not None:
        version = __validate_and_format(version)
        
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
    
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')
            update_divs = soup.find_all('div', class_='update')
    
            for update_div in update_divs:
                h1_tags = update_div.find_all('h1')
                for h1 in h1_tags:
                    if version is None or (version and version in h1.text):
                        return __convert_content(update_div, return_type)
    return None


def __validate_and_format(version):
    if not re.fullmatch(r'([5-9]|[1-9]\d)\.\d\.\d', version) and not re.fullmatch(r'[5-9]\d{2}|[1-9]\d{3}', version):
        raise ValueError("Invalid version format. Version needs to be at least 5.0.0 or 500.")
    version = version.replace('.', '')
    version = list(version)
    version.insert(-1, '.')
    version.insert(-3, '.')
    return ''.join(version)


def __convert_content(update_div, return_type):
    converter = html2text.HTML2Text()
    converter.ignore_links = True

    content = update_div.prettify()
    if return_type == 'md':
        content = converter.handle(content)
    
    return content







if __name__ == '__main__':
    import asyncio
    version = '5.0.0'
    content = asyncio.run(get_update_content(return_type = 'md'))
    print(content)
    with open('Markdown.md', 'w', encoding='utf-8') as f:
        f.write(content)

    