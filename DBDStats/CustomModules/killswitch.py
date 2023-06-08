import aiohttp
import html2text
from bs4 import BeautifulSoup



async def get_killswitch(return_type='html'):
    if return_type not in ['html', 'md']:
        raise ValueError("Invalid return type. Return type needs to be either 'html' or 'md'.")

    url = 'https://forums.bhvr.com/dead-by-daylight/kb/articles/299-kill-switch-master-list'
    converter = html2text.HTML2Text()
    converter.ignore_links = True

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Find the required sections
            kill_switch_section = soup.find('h2', {'data-id': 'kill-switch-(disabled)'})
            known_issues_section = soup.find('h2', {'data-id': 'known-issues-(not-disabled)'})

            # Extract the content between the two sections
            content = []
            current_section = kill_switch_section.find_next_sibling()
            while current_section and current_section != known_issues_section:
                # Remove any images
                for img in current_section.find_all('img'):
                    img.decompose()
                content.append(str(current_section))
                current_section = current_section.find_next_sibling()

            # Convert the content to the required format
            content = '\n'.join(content)
            if not content:
                return None
            elif return_type == 'html':
                return content
            elif return_type == 'md':
                return converter.handle(content)

    return None




if __name__ == '__main__':
    import asyncio
    md = asyncio.run(get_killswitch('md'))
    
    md = md.strip()
    md.replace("\n", "")
    

    print(type(md))
    print(md)
