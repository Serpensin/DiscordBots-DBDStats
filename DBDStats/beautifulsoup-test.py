
import requests
from bs4 import BeautifulSoup

url = 'https://steamcharts.com/app/381210'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26'}
page = requests.get(url).text
soup = BeautifulSoup(page, 'html.parser')
i = {}
count = 0
for stats in soup.find_all('div', class_='app-stat'):
    soup2 = BeautifulSoup(str(stats), 'html.parser')
    for stat in soup2.find_all('span', class_='num'):
        stat = str(stat).replace('<span class="num">', '').replace('</span>', '')
        if count == 0:
            i['Current Players'] = stat
        elif count == 1:
            i['Peak Players 24h'] = stat
        elif count == 2:
            i['Peak Players All Time'] = stat
        count += 1  
return i
