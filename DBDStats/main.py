#Import
import discord
import requests as r
import time
import logging
import logging.handlers
import os
from zipfile import ZIP_DEFLATED, ZipFile
import json
from random import randrange
from datetime import timedelta, datetime
from googletrans import Translator
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio
import platform
from prettytable import PrettyTable


#Set vars
api_base = 'https://dbd.tricky.lol/api/'                                
perks_base = 'https://dbd.tricky.lol/dbdassets/perks/'
bot_base = 'https://cdn.bloodygang.com/botfiles/DBDStats/'
map_portraits = bot_base+'mapportraits/'
#char_portraits = bot_base+'charportraits/'   
alt_playerstats = 'https://dbd.tricky.lol/playerstats/'
steamStore = 'https://store.steampowered.com/app/'
languages = ['Afrikaans', 'Albanian', 'Amharic', 'Arabic', 'Armenian', 'Azerbaijani', 'Basque', 'Belarusian', 'Bengali', 'Bosnian', 'Bulgarian', 'Catalan', 'Cebuano', 'Chichewa', 'Chinese (Simplified)', 'Chinese (Traditional)', 'Corsican', 'Croatian', 'Czech', 'Danish', 'Dutch', 'English', 'Esperanto', 'Estonian', 'Filipino', 'Finnish', 'French', 'Frisian', 'Galician', 'Georgian', 'German', 'Greek', 'Gujarati', 'Haitian Creole', 'Hausa', 'Hawaiian', 'Hebrew', 'Hebrew', 'Hindi', 'Hmong', 'Hungarian', 'Icelandic', 'Igbo', 'Indonesian', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kannada', 'Kazakh', 'Khmer', 'Korean', 'Kurdish (Kurmanji)', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Lithuanian', 'Luxembourgish', 'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori', 'Marathi', 'Mongolian', 'Myanmar (Burmese)', 'Nepali', 'Norwegian', 'Odia', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Romanian', 'Russian', 'Samoan', 'Scots Gaelic', 'Serbian', 'Sesotho', 'Shona', 'Sindhi', 'Sinhala', 'Slovak', 'Slovenian', 'Somali', 'Spanish', 'Sundanese', 'Swahili', 'Swedish', 'Tajik', 'Tamil', 'Telugu', 'Thai', 'Turkish', 'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Vietnamese', 'Welsh', 'Xhosa', 'Yiddish', 'Yoruba', 'Zulu']


#Init
if not os.path.exists('DBDStats'):
    os.mkdir('DBDStats')
if not os.path.exists('DBDStats//Logs'):
    os.mkdir('DBDStats//Logs')
if not os.path.exists('DBDStats//Buffer'):
    os.mkdir('DBDStats//Buffer')
if not os.path.exists('DBDStats//Buffer//Stats'):
    os.mkdir('DBDStats//Buffer//Stats')
log_folder = 'DBDStats//Logs//'
buffer_folder = 'DBDStats//Buffer//'
stats_folder = 'DBDStats//Buffer//Stats//'
logger = logging.getLogger('discord')
manlogger = logging.getLogger('Program')
logger.setLevel(logging.INFO)
manlogger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename = log_folder+'DBDStats.log',
    encoding = 'utf-8',
    maxBytes = 8 * 1024 * 1024, 
    backupCount = 5,            
    mode='w')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
manlogger.addHandler(handler)
manlogger.info('------')
manlogger.info('Engine powering up...')
load_dotenv()
TOKEN = os.getenv('TOKEN')
ownerID = os.getenv('OWNER_ID')
steamAPIkey = os.getenv('steamAPIkey')
support_id = os.getenv('support_server')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
translator = Translator()
tb = PrettyTable()
#Fix error on windows on shutdown.
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    
#Presence    
class Presence():    
    def get_activity():
        with open('activity.json') as f:
            data = json.load(f)
            activity_type = data['activity_type']
            activity_title = data['activity_title']
            activity_url = data['activity_url']
        if activity_type == 'Playing':
            return discord.Game(name=activity_title)
        elif activity_type == 'Streaming':
            return discord.Activity(type=discord.ActivityType.streaming, name=activity_title, url=activity_url)
        elif activity_type == 'Listening':
            return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
        elif activity_type == 'Watching':
            return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
        elif activity_type == 'Competing':
            return discord.Activity(type=discord.ActivityType.competing, name=activity_title)
        
    def get_status():
        with open('activity.json') as f:
            data = json.load(f)
            status = data['status']
        if status == 'online':
            return discord.Status.online
        elif status == 'idle':
            return discord.Status.idle
        elif status == 'dnd':
            return discord.Status.dnd
        elif status == 'invisible':
            return discord.Status.invisible
  
        
#Bot        
class aclient(discord.AutoShardedClient):
    def __init__(self):
        super().__init__(owner_id = ownerID,
                              intents = intents,
                              status = discord.Status.invisible
                        )
        self.synced = False
    async def on_ready(self):
        logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            manlogger.info('Syncing...')
            await tree.sync()
            manlogger.info('Synced.')
            self.synced = True
            await bot.change_presence(activity = Presence.get_activity(), status = Presence.get_status())
        global owner
        owner = await bot.fetch_user(ownerID)
        manlogger.info('Initialization completed...')
        manlogger.info('------')
        print('READY')
bot = aclient()
tree = discord.app_commands.CommandTree(bot)


#Events
class Events():
    @bot.event
    async def on_guild_remove(guild):
        manlogger.info(f'I got kicked from {guild}. (ID: {guild.id})')
    
    @bot.event
    async def on_guild_join(guild):
        manlogger.info(f'I joined {guild}. (ID: {guild.id})')
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                perms = []
                for roles in guild.roles:
                    if roles.permissions.manage_guild and roles.permissions.manage_roles or roles.permissions.administrator and not roles.is_bot_managed():
                        perms.append(roles.id)
                if perms == []:
                    break
                else:
                    for role in perms: 
                        await channel.send(f'<@&{role}>')
                    await channel.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the initial setup.')
                return
        await guild.owner.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the initial setup.')
    
    @tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(Functions.translate(interaction, 'This comand is on cooldown.\nTime left: `')+Functions.seconds_to_minutes(error.retry_after)+'`.', ephemeral = True)
            #manlogger.warning(str(error)+' '+interaction.user.name+' | '+str(interaction.user.id))
        else:
            await interaction.followup.send(error, ephemeral = True)
            manlogger.warning(str(error)+' '+interaction.user.name+' | '+str(interaction.user.id))


#Functions
class Functions():
    def steam_link_to_id(vanity):
        vanity = vanity.replace('https://steamcommunity.com/profiles/', '')
        vanity = vanity.replace('https://steamcommunity.com/id/', '')
        vanity = vanity.replace('/', '')
        resp = r.get(f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={steamAPIkey}&vanityurl={vanity}')
        if resp.json()['response']['success'] == 1:
            return resp.json()['response']['steamid']
        else:
            return vanity
    
    def CheckForDBD(id, steamAPIkey):
        id = Functions.steam_link_to_id(id)
        if len(id) != 17:
            return(1, 1)
        try:
            int(id)
        except:
            return(1, 1)
        try:
            resp = r.get(f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steamAPIkey}&steamid={id}&format=json')
            data = resp.json()
            if resp.status_code == 400:
                return(2, 2)
            if data['response'] == {}:
                return(3, 3)
            for event in data['response']['games']:
                if event['appid'] == 381210:
                    return(0, id)
                else:
                    continue
            return(4, 4)
        except:
            return(5, 5)
    
    def convert_time(timestamp):
        return(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp)))
    
    def convert_time_dateonly(timestamp):
        return(time.strftime('%Y-%m-%d', time.gmtime(timestamp)))
    
    def convert_number(number):
        return(f'{number:,}')
    
    async def check_429(path):
        resp = r.get(path)
        if resp.status_code == 429:               
            manlogger.error(str(resp.status_code)+' while accessing '+path)
            return(1)
        print(f'429 {resp}')
        return(resp.json())
    
    def check_if_removed(id):
        resp = r.get(f'{api_base}playerstats?steamid={id}')
        if resp.status_code == 404:
            print('404')
            url = f'{alt_playerstats}{id}'
            print(url)
            #url = 'https://develop.bloodygang.com/test.html'
            page = r.get(url).text
            soup = BeautifulSoup(page, 'html.parser')
            print(soup)
            for i in soup.find_all('div', id='error'):
                print(i)
                return i.text
            manlogger.warning(f'SteamID {id} got removed from the leaderboard.')
            return(1)
        return(0)
    
    async def create_support_invite(interaction):
        guild = bot.get_guild(int(support_id))
        channel = guild.channels[0]
        link = await channel.create_invite(reason='Created invite for '+interaction.user.name+' from server '+interaction.guild.name, max_age=60, max_uses=1, unique=True)
        return link
    
    def seconds_to_minutes(input_int):
        return(str(timedelta(seconds=input_int)))
    
    def translate(interaction, text):
        translator = Translator()
        for i in interaction.user.roles:
            if i.name in languages:
                try:
                    return(translator.translate(text, dest=i.name).text)
                except:
                    return(text)
        return(text)
    
    async def perk_load():
        char = await Functions.character_load()
        tb.clear()
        tb.field_names = ['Name', 'Category', 'Origin']
        if os.path.exists(buffer_folder+'perk_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'perk_info.json')) /3600 < 4):
            with open(buffer_folder+'perk_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)  
            if not os.path.exists(buffer_folder+'perks.txt') or ((time.time() - os.path.getmtime(buffer_folder+'perks.txt')) /3600 > 4):
                with open(buffer_folder+'perks.txt', 'w', encoding='utf8') as f:
                    for key in data.keys():
                        for i in char.keys():
                            print(i)
                            print(data[key]['character'])
                            if str(data[key]['character']) == str(i):
                                print(data[key]['name'])
                                print(str(data[key]['categories']))
                                print(char[i]['name'])
                                tb.add_row([data[key]['name'], str(data[key]['categories']).replace('[', '').replace('\'', '').replace(']', '').replace('None', ''), char[i]['name']])
                                break
                            elif data[key]['character'] is None:
                                tb.add_row([data[key]['name'], str(data[key]['categories']).replace('[', '').replace('\'', '').replace(']', '').replace('None', ''), ''])
                                break
                    tb.sortby = 'Name'
                    f.write(str(tb))
                    print(tb)
            print(type(data))
            return data
        else:
            data = await Functions.check_429(api_base+'perks')
            if data == 1:
                return(1)
            with open(buffer_folder+'perk_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'perk_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)
            with open(buffer_folder+'perks.txt', 'w', encoding='utf8') as f:
                for key in data.keys():
                    for i in char.keys():
                        if str(data[key]['character']) == str(i):
                            tb.add_row([data[key]['name'], str(data[key]['categories']).replace('[', '').replace('\'', '').replace(']', '').replace('None', ''), char[i]['name']])
                            break
                        elif data[key]['character'] is None:
                            tb.add_row([data[key]['name'], str(data[key]['categories']).replace('[', '').replace('\'', '').replace(']', '').replace('None', ''), ''])
                            break
                tb.sortby = 'Name'
                f.write(str(tb))
                print(tb)
            print(type(data))
            return data
    
    async def send_perk_info(data, perk, interaction, shrine: bool = ''):
        def length1(data):
            length = len(data[key]['tunables'][0])
            if length == 1:
                embed.add_field(name='0', value=data[key]['tunables'][0][0])
            elif length == 2:
                embed.add_field(name='0', value=data[key]['tunables'][0][0])
                embed.add_field(name='\u200b', value=data[key]['tunables'][0][1])
            elif length == 3:
                embed.add_field(name='0', value=data[key]['tunables'][0][0])
                embed.add_field(name='\u200b', value=data[key]['tunables'][0][1])
                embed.add_field(name='\u200b', value=data[key]['tunables'][0][2])
        def length2(data):
            length = len(data[key]['tunables'][1])
            if length == 1:
                embed.add_field(name='1', value=data[key]['tunables'][1][0])
            elif length == 2:
                embed.add_field(name='1', value=data[key]['tunables'][1][0])
                embed.add_field(name='\u200b', value=data[key]['tunables'][1][1])
            elif length == 3:
                embed.add_field(name='1', value=data[key]['tunables'][1][0])
                embed.add_field(name='\u200b', value=data[key]['tunables'][1][1])
                embed.add_field(name='\u200b', value=data[key]['tunables'][1][2])
        def length3(data):
            length = len(data[key]['tunables'][2])
            if length == 1:
                embed.add_field(name='2', value=data[key]['tunables'][2][0])
            elif length == 2:
                embed.add_field(name='2', value=data[key]['tunables'][2][0])
                embed.add_field(name='\u200b', value=data[key]['tunables'][2][1])
            elif length == 3:
                embed.add_field(name='2', value=data[key]['tunables'][2][0])
                embed.add_field(name='\u200b', value=data[key]['tunables'][2][1])
                embed.add_field(name='\u200b', value=data[key]['tunables'][2][2])
        def check():
            embed.set_thumbnail(url=bot_base+data[key]['image'])
            length_total = len(data[key]['tunables'])
            embed.add_field(name='\u200b', value='\u200b', inline = False)
            print(f'--------------{key}------------------------------{length_total}')
            print(data[key])
            if length_total == 1:
                length1(data)
            elif length_total == 2:
                length1(data)
                embed.add_field(name='\u200b', value='\u200b', inline = False)
                length2(data)
            elif length_total == 3:
                length1(data)
                embed.add_field(name='\u200b', value='\u200b', inline = False)
                length2(data)
                embed.add_field(name='\u200b', value='\u200b', inline = False)
                length3(data) 
        if shrine:
            embed = discord.Embed(title="Perk description for '"+data[perk]['name']+"'", description=Functions.translate(interaction, str(data[perk]['description']).replace('<br><br>', ' ').replace('<i>', '**').replace('</i>', '**').replace('<li>', '*').replace('</li>', '*').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ')).replace('.','. '), color=0xb19325)
            key = perk
            check()
            return embed
        else:        
            for key in data.keys():
                print(data)
                print(perk)
                embed = discord.Embed(title="Perk description for '"+data[key]['name']+"'", description=Functions.translate(interaction, str(data[key]['description']).replace('<br><br>', ' ').replace('<i>', '**').replace('</i>', '**').replace('<li>', '*').replace('</li>', '*').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ')).replace('.','. '), color=0xb19325)
                if data[key]['name'].lower() == perk.lower():
                    check()
                    await interaction.followup.send(embed=embed)
                    return
        return 1
    
    async def shrine_load():
        if os.path.exists(buffer_folder+'shrine_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'shrine_info.json')) /3600 < 4):
            with open(buffer_folder+'shrine_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)
                return data
        else:
            data = await Functions.check_429(bot_base+'shrine_info.json')
            if data == 1:
                return(1)
            with open(buffer_folder+'shrine_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'shrine_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)
                return data
            
#    async def archive_load():
#        if os.path.exists(buffer_folder+'archive_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'archive_info.json')) /3600 < 4):
#            with open(buffer_folder+'archive_info.json', 'r', encoding='utf8') as f:
#                data = json.load(f)  
#                print(type(data))
#                return data
#        else:
#            data = await Functions.check_429(api_base+'archives')
#            if data == 1:
#                return(1)
#            with open(buffer_folder+'archive_info.json', 'w', encoding='utf8') as f:
#                json.dump(data, f, indent=2)
#            with open(buffer_folder+'archive_info.json', 'r', encoding='utf8') as f:
#                data = json.load(f)
#                print(type(data))
#                return data    

    async def offerings_load():
        tb.field_names = ['ID', 'Name']
        if os.path.exists(buffer_folder+'offering_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'offering_info.json')) /3600 < 4):
            with open(buffer_folder+'offering_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)  
            if not os.path.exists(buffer_folder+'offerings.txt') or ((time.time() - os.path.getmtime(buffer_folder+'offerings.txt')) /3600 > 4):
                with open(buffer_folder+'offerings.txt', 'w', encoding='utf8') as f2:
                    for key in data.keys():
                        print(data[key])
                        print(data[key]['name'])
                        if data[key]['name'] == '' or data[key]['name'] is None:
                            tb.add_row([key, ''])
                        else:
                            tb.add_row([key, data[key]['name']])
                    tb.sortby = 'ID'
                    print(tb)
                    f2.write(str(tb))
                    print(type(data))
            tb.clear()
            return data
        else:
            data = await Functions.check_429(api_base+'offerings')
            if data == 1:
                return(1)
            print(data)
            print('-----------------------------')
            with open(buffer_folder+'offering_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'offering_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)
            with open(buffer_folder+'offerings.txt', 'w', encoding='utf8') as f2:
                for key in data.keys():
                    print(data[key])
                    print(data[key]['name'])
                    if data[key]['name'] == '' or data[key]['name'] is None:
                        tb.add_row([key, ''])
                    else:
                        tb.add_row([key, data[key]['name']])
                tb.sortby = 'ID'
                print(tb)
                f2.write(str(tb))
                print(type(data))
                tb.clear()
                return data
            
    async def character_load():
        tb.field_names = ['ID', 'Name', 'Role']
        if os.path.exists(buffer_folder+'character_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'character_info.json')) / 3600) <= 4:
            with open(buffer_folder+'character_info.json', 'r', encoding='utf8') as f:
                f = json.loads(f.read())
            with open(buffer_folder+'characters.txt', 'w', encoding='utf8') as f2:
                for key in f.keys():
                    tb.add_row([str(f[key]['id']), str(f[key]['name']).replace('The ', ''), f[key]['role']])
                tb.sortby = 'Name'
                f2.write(str(tb))
                tb.clear()
                return f
        else:
            data = await Functions.check_429(api_base+'characters')
            if data == 1:
                return 1
            with open(buffer_folder+'character_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'character_info.json', 'r', encoding='utf8') as f:
                f = json.loads(f.read())
            with open(buffer_folder+'characters.txt', 'w', encoding='utf8') as f2:
                for key in f.keys():
                    tb.add_row([str(f[key]['id']), str(f[key]['name']).replace('The ', ''), f[key]['role']])
                tb.sortby = 'Name'
                f2.write(str(tb))
                tb.clear()
                return f
            
    async def dlc_load():
        if os.path.exists(buffer_folder+'dlc.json') and ((time.time() - os.path.getmtime(buffer_folder+'dlc.json')) / 3600) <= 4:
            with open(buffer_folder+'dlc.json', 'r', encoding='utf8') as f:
                return json.loads(f.read())
        else:
            data = await Functions.check_429(api_base+'dlc')
            if data == 1:
                return 1
            with open(buffer_folder+'dlc.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'dlc.json', 'r', encoding='utf8') as f:
                return json.loads(f.read())

    async def items_load():
        tb.field_names = ['ID', 'Name', 'Type', 'Rarity']
        if os.path.exists(buffer_folder+'items.json') and ((time.time() - os.path.getmtime(buffer_folder+'items.json')) / 3600) <= 4:
            with open(buffer_folder+'items.json', 'r', encoding='utf8') as f:
                f = json.loads(f.read())
            with open(buffer_folder+'items.txt', 'w', encoding='utf8') as f2:
                for key in f.keys():
                    if f[key]['item_type'] is None:
                        f[key]['item_type'] = ''
                    tb.add_row([key, str(f[key]['name']), str(f[key]['item_type']), str(f[key]['rarity'])])
                tb.sortby = 'Type'
                f2.write(str(tb))
                tb.clear()
                return f
        else:
            data = await Functions.check_429(api_base+'items?role=survivor')
            if data == 1:
                return 1
            with open(buffer_folder+'items.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'items.json', 'r', encoding='utf8') as f:
                f = json.loads(f.read())
            with open(buffer_folder+'items.txt', 'w', encoding='utf8') as f2:
                for key in f.keys():
                    tb.add_row([key, str(f[key]['name']), str(f[key]['item_type']), str(f[key]['rarity'])])
                tb.sortby = 'Type'
                f2.write(str(tb))
                tb.clear()
                return f

            
#Info
class Info():
    async def rankreset(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(Functions.translate(interaction, "This command can only be used in a server."))
        else:
            resp = r.get(api_base+'rankreset')
            data = resp.json()
            embed = discord.Embed(description=Functions.translate(interaction, 'The next rank reset will take place on the following date: ')+' <t:'+str(data['rankreset'])+'>.', color=0x0400ff)
            await interaction.response.send_message(embed=embed)    

    async def event(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.")
        else:
            resp = r.get(api_base+'events')
            data = resp.json()
            for event in data:
                if not int(event['start']) <= int(time.time()) <= int(event['end']):
                    continue
                elif int(event['start']) <= int(time.time()) <= int(event['end']):
                    embed = discord.Embed(title="Event", description=Functions.translate(interaction, "Currently there is a event in DeadByDaylight.")+" <a:hyperWOW:1032389458319913023>", color=0x922f2f)
                    embed.add_field(name=Functions.translate(interaction, "Name"), value=event['name'], inline=True)
                    embed.add_field(name=Functions.translate(interaction, "Bloodpoint Multiplier"), value=event['multiplier'], inline=False)
                    embed.add_field(name=Functions.translate(interaction, "Beginning"), value=str(Functions.convert_time(event['start'])+' UTC'), inline=True)
                    embed.add_field(name=Functions.translate(interaction, "Ending"), value=str(Functions.convert_time(event['end'])+' UTC'), inline=True)
                    await interaction.followup.send(embed=embed)
                    return
                elif int(event['start']) >= int(time.time()) <= int(event['end']):
                    embed = discord.Embed(title="Event", description=Functions.translate(interaction, "There is a upcomming event in DeadByDaylight.")+" <a:SmugDance:1032349729167790090>", color=0x922f2f)
                    embed.add_field(name="Name", value=event['name'], inline=True)
                    embed.add_field(name="Bloodpoint Multiplier", value=event['multiplier'], inline=False)
                    embed.add_field(name="Beginning", value=str(Functions.convert_time(event['start'])+' UTC'), inline=True)
                    embed.add_field(name="Ending", value=str(Functions.convert_time(event['end'])+' UTC'), inline=True)
                    await interaction.followup.send(embed=embed)
                    return
            embed = discord.Embed(title="Event", description=Functions.translate(interaction, "Currently there is no event in DeadByDaylight.")+" <:pepe_sad:1032389746284056646>", color=0x922f2f)
            await interaction.followup.send(embed=embed)           

    async def playerstats(interaction: discord.Interaction, steamid):
        if interaction.guild is None:
            await interaction.response.send_message('This command can only be used inside a server.')
            return
        check = Functions.CheckForDBD(steamid, steamAPIkey)
        print(check)
        try:
            int(check[0])
        except:
            embed = discord.Embed(title=Functions.translate(interaction, 'Try again'), description=Functions.translate(interaction, check[1]), color=0x004cff)
            await interaction.response.send_message(embed=embed)
            return
        if check[0] == 1:
            await interaction.response.send_message(Functions.translate(interaction, 'The SteamID64 has to be 17 chars long and only containing numbers.'), ephemeral=True)   
        elif check[0] == 2:
            await interaction.response.send_message(Functions.translate(interaction, 'This SteamID64 is NOT in use.'), ephemeral=True)
        elif check[0] == 3:
            await interaction.response.send_message(Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking").replace('.','. ')+"\n[here](https://steamcommunity.com/profiles/"+id+"/edit/settings).", ephemeral=True)
        elif check[0] == 4:
            await interaction.response.send_message(Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look").replace('.','. ')+" [here](https://www.g2a.com/n/dbdstats).")
        elif check[0] == 5:
            embed1=discord.Embed(title="Fatal Error", description=Functions.translate(interaction, "It looks like there was an error querying the SteamAPI (probably a rate limit).\nPlease join our").replace('.','. ')+" [Support-Server]("+str(await Functions.create_support_invite(interaction))+Functions.translate(interaction, ") and create a ticket to tell us about this."), color=0xff0000)
            embed1.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.response.send_message(embed=embed1, ephemeral=True)
        elif check[0] == 0:
            await interaction.response.defer(thinking=True)
            for filename in os.scandir(stats_folder):
                if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 24:
                    os.remove(filename)
            #Get Stats
            removed = Functions.check_if_removed(check[1])
            if removed == 1:
                embed1 = discord.Embed(title="Statistics", url=alt_playerstats+check[1], description=Functions.translate(interaction, "It looks like this profile has been banned from displaying on our leaderboard.\nThis probably happened because achievements or statistics were manipulated.\nI can therefore not display any information in an embed.\nIf you still want to see the full statistics, please click on the link.").replace('.','. '), color=0xb19325)
                await interaction.followup.send(embed=embed1)
                return
            elif removed != 0:
                print(removed)
                await interaction.followup.send(content = removed)
                return
            if os.path.exists(f'{stats_folder}player_stats_{check[1]}.json') and ((time.time() - os.path.getmtime(f'{stats_folder}player_stats_{check[1]}.json')) / 3600) <= 4:
                with open(f'{stats_folder}player_stats_{check[1]}.json', 'r', encoding='utf8') as f:
                    player_stats = json.load(f)
            else:
                data = await Functions.check_429(f'{api_base}playerstats?steamid={check[1]}')
                print(f'WICHTIG {data}')
                if data != 1:
                    print('DUMP STATS')
                    with open(f'{stats_folder}player_stats_{check[1]}.json', 'w', encoding='utf8') as f:
                        json.dump(r.get(f'{api_base}playerstats?steamid={check[1]}').json(), f, indent=2)
                else:
                    await interaction.followup.send(Functions.translate(interaction, "The stats got loaded in the last 4h but I don't have a local copy. Try again in ~3-4h.").replace('.','. '), ephemeral=True)
                    return
                with open(f'{stats_folder}player_stats_{check[1]}.json', 'r', encoding='utf8') as f:
                    player_stats = json.load(f)
            steam_data = await Functions.check_429(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steamAPIkey}&steamids={check[1]}')
            if steam_data == 1 or player_stats == 1:
                await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later. (This error can also appear if the same profile got querried multiple times in a 3h window.)").replace('.','. '), ephemeral=True)
                return
            for event in steam_data['response']['players']:
                personaname = event['personaname']
                profileurl = event['profileurl']
                avatar = event['avatarfull']
            #Set embed headers
            embed1 = discord.Embed(title=Functions.translate(interaction, "Statistics (1/10) - Survivor Stats"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed2 = discord.Embed(title=Functions.translate(interaction, "Statistics (2/10) - Killer Interactions"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed3 = discord.Embed(title=Functions.translate(interaction, "Statistics (3/10) - Healing/Saved"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed4 = discord.Embed(title=Functions.translate(interaction, "Statistics (4/10) - Escaped"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed5 = discord.Embed(title=Functions.translate(interaction, "Statistics (5/10) - Repaired second floor generator and escaped"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed6 = discord.Embed(title=Functions.translate(interaction, "Statistics (6/10) - Killer Stats"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed7 = discord.Embed(title=Functions.translate(interaction, "Statistics (7/10) - Hooked"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed8 = discord.Embed(title=Functions.translate(interaction, "Statistics (8/10) - Powers"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed9 = discord.Embed(title=Functions.translate(interaction, "Statistics (9/10) - Survivors downed"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed10 = discord.Embed(title=Functions.translate(interaction, "Statistics (10/10) - Survivors downed with power"), description=personaname+'\n'+profileurl, color=0xb19325)
            #Set embed pictures
            embed1.set_thumbnail(url=avatar)
            embed2.set_thumbnail(url=avatar)
            embed3.set_thumbnail(url=avatar)
            embed4.set_thumbnail(url=avatar)
            embed5.set_thumbnail(url=avatar)
            embed6.set_thumbnail(url=avatar)
            embed7.set_thumbnail(url=avatar)
            embed8.set_thumbnail(url=avatar)
            embed9.set_thumbnail(url=avatar)
            embed10.set_thumbnail(url=avatar)
            #Set Embed Footers
            footer = Functions.translate(interaction, "Stats are updated every ~4h. | Last update: ").replace('.|','. | ')+str(Functions.convert_time(int(player_stats['updated_at'])))+" UTC"
            embed1.set_footer(text=footer)
            embed2.set_footer(text=footer)
            embed3.set_footer(text=footer)
            embed4.set_footer(text=footer)
            embed5.set_footer(text=footer)
            embed6.set_footer(text=footer)
            embed7.set_footer(text=footer)
            embed8.set_footer(text=footer)
            embed9.set_footer(text=footer)
            embed10.set_footer(text=footer)
            #Embed1 - Survivor
            embed1.add_field(name=Functions.translate(interaction, "Bloodpoints Earned"), value=Functions.convert_number(player_stats['bloodpoints']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Rank"), value=player_stats['survivor_rank'], inline=True)
            embed1.add_field(name="\u200b", value="\u200b", inline=False)
            embed1.add_field(name=Functions.translate(interaction, "Full loadout Games"), value=Functions.convert_number(player_stats['survivor_fullloadout']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Perfect Games"), value=Functions.convert_number(player_stats['survivor_perfectgames']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Generators repaired"), value=Functions.convert_number(player_stats['gensrepaired']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Gens without Perks"), value=Functions.convert_number(player_stats['gensrepaired_noperks']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Damaged gens repaired"), value=Functions.convert_number(player_stats['damagedgensrepaired']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Successful skill checks"), value=Functions.convert_number(player_stats['skillchecks']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Items Depleted"), value=Functions.convert_number(player_stats['itemsdepleted']), inline=False)
            embed1.add_field(name=Functions.translate(interaction, "Hex Totems Cleansed"), value=Functions.convert_number(player_stats['hextotemscleansed']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Hex Totems Blessed"), value=Functions.convert_number(player_stats['hextotemsblessed']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Exit Gates Opened"), value=Functions.convert_number(player_stats['blessedtotemboosts']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Hooks Sabotaged"), value=Functions.convert_number(player_stats['hookssabotaged']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Chests Searched"), value=Functions.convert_number(player_stats['chestssearched']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Chests Searched in the Basement"), value=Functions.convert_number(player_stats['chestssearched_basement']), inline=True)
            embed1.add_field(name=Functions.translate(interaction, "Mystery boxes opened"), value=Functions.convert_number(player_stats['mysteryboxesopened']), inline=True)
            #Embed2 - Killer Interactions
            embed2.add_field(name="\u200b", value="\u200b", inline=False)
            embed2.add_field(name=Functions.translate(interaction, "Dodged basic attack or projectiles"), value=Functions.convert_number(player_stats['dodgedattack']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Escaped chase after pallet stun"), value=Functions.convert_number(player_stats['escapedchase_palletstun']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Escaped chase injured after hit"), value=Functions.convert_number(player_stats['escapedchase_healthyinjured']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Escape chase by hiding in locker"), value=Functions.convert_number(player_stats['escapedchase_hidinginlocker']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Protection hits for unhooked survivor"), value=Functions.convert_number(player_stats['protectionhits_unhooked']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Protectionhits while a survivor is carried"), value=Functions.convert_number(player_stats['protectionhits_whilecarried']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Vaults while in chase"), value=Functions.convert_number(player_stats['vaultsinchase']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Dodge attack before vaulting"), value=Functions.convert_number(player_stats['vaultsinchase_missed']), inline=True)
            embed2.add_field(name=Functions.translate(interaction, "Wiggled from killers grasp"), value=Functions.convert_number(player_stats['wiggledfromkillersgrasp']), inline=True)
            #Embed3 - Healing/Saves
            embed3.add_field(name="\u200b", value="\u200b", inline=False)
            embed3.add_field(name=Functions.translate(interaction, "Survivors healed"), value=Functions.convert_number(player_stats['survivorshealed']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Survivors healed while injured"), value=Functions.convert_number(player_stats['survivorshealed_whileinjured']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Survivors healed while 3 others not healthy"), value=Functions.convert_number(player_stats['survivorshealed_threenothealthy']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Survivors healed who found you while injured"), value=Functions.convert_number(player_stats['survivorshealed_foundyou']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Survivors healed from dying state to injured"), value=Functions.convert_number(player_stats['healeddyingtoinjured']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Obsessions healed"), value=Functions.convert_number(player_stats['obsessionshealed']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Survivors saved (from death)"), value=Functions.convert_number(player_stats['saved']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Survivors saved during endgame"), value=Functions.convert_number(player_stats['saved_endgame']), inline=True)
            embed3.add_field(name=Functions.translate(interaction, "Killers pallet stunned while carrying a survivor"), value=Functions.convert_number(player_stats['killerstunnedpalletcarrying']), inline=True)
            embed3.add_field(name="Kobed", value=Functions.convert_number(player_stats['unhookedself']), inline=True)
            #Embed5 - Escaped
            embed4.add_field(name="\u200b", value="\u200b", inline=False)
            embed4.add_field(name=Functions.translate(interaction, "While healthy/injured"), value=Functions.convert_number(player_stats['escaped']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "While crawling"), value=Functions.convert_number(player_stats['escaped_ko']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "After kobed"), value=Functions.convert_number(player_stats['hooked_escape']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "Through the hatch"), value=Functions.convert_number(player_stats['escaped_hatch']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "Through the hatch while crawling"), value=Functions.convert_number(player_stats['escaped_hatchcrawling']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "Through the hatch with everyone"), value=Functions.convert_number(player_stats['escaped_allhatch']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "After been downed once"), value=Functions.convert_number(player_stats['escaped_downedonce']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "After been injured for half of the trial"), value=Functions.convert_number(player_stats['escaped_injuredhalfoftrail']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "With no bloodloss as obsession"), value=Functions.convert_number(player_stats['escaped_nobloodlossobsession']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "Last gen last survivor"), value=Functions.convert_number(player_stats['escaped_lastgenlastsurvivor']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "With new item"), value=Functions.convert_number(player_stats['escaped_newitem']), inline=True)
            embed4.add_field(name=Functions.translate(interaction, "With item from someone else"), value=Functions.convert_number(player_stats['escaped_withitemfrom']), inline=True)
            #Embed6 - Repaired second floor generator and escaped
            embed5.add_field(name="\u200b", value="\u200b", inline=False)
            embed5.add_field(name="Disturbed Ward", value=Functions.convert_number(player_stats['secondfloorgen_disturbedward']), inline=True)
            embed5.add_field(name="Father Campbells Chapel", value=Functions.convert_number(player_stats['secondfloorgen_fathercampbellschapel']), inline=True)
            embed5.add_field(name="Mothers Dwelling", value=Functions.convert_number(player_stats['secondfloorgen_mothersdwelling']), inline=True)
            embed5.add_field(name="Temple of Purgation", value=Functions.convert_number(player_stats['secondfloorgen_templeofpurgation']), inline=True)
            embed5.add_field(name="The Game", value=Functions.convert_number(player_stats['secondfloorgen_game']), inline=True)
            embed5.add_field(name="Family Residence", value=Functions.convert_number(player_stats['secondfloorgen_familyresidence']), inline=True)
            embed5.add_field(name="Sanctum of Wrath", value=Functions.convert_number(player_stats['secondfloorgen_sanctumofwrath']), inline=True)
            embed5.add_field(name="Mount Ormond", value=Functions.convert_number(player_stats['secondfloorgen_mountormondresort']), inline=True)
            embed5.add_field(name="Lampkin Lane", value=Functions.convert_number(player_stats['secondfloorgen_lampkinlane']), inline=True)
            embed5.add_field(name="Pale Rose", value=Functions.convert_number(player_stats['secondfloorgen_palerose']), inline=True)
            embed5.add_field(name="Hawkins", value=Functions.convert_number(player_stats['secondfloorgen_undergroundcomplex']), inline=True)
            embed5.add_field(name="Treatment Theatre", value=Functions.convert_number(player_stats['secondfloorgen_treatmenttheatre']), inline=True)
            embed5.add_field(name="Dead Dawg Saloon", value=Functions.convert_number(player_stats['secondfloorgen_deaddawgsaloon']), inline=True)
            embed5.add_field(name="Midwich", value=Functions.convert_number(player_stats['secondfloorgen_midwichelementaryschool']), inline=True)
            embed5.add_field(name="Raccoon City", value=Functions.convert_number(player_stats['secondfloorgen_racconcitypolicestation']), inline=True)
            embed5.add_field(name="Eyrie of Crows", value=Functions.convert_number(player_stats['secondfloorgen_eyrieofcrows']), inline=True)
            embed5.add_field(name="Garden of Joy", value=Functions.convert_number(player_stats['secondfloorgen_gardenofjoy']), inline=True)
            embed5.add_field(name="\u200b", value="\u200b", inline=True)
            #Embed7 - Killer Stats
            embed6.add_field(name=Functions.translate(interaction, "Rank"), value=player_stats['killer_rank'], inline=True)
            embed6.add_field(name="\u200b", value="\u200b", inline=False)
            embed6.add_field(name=Functions.translate(interaction, "Played with full loadout"), value=Functions.convert_number(player_stats['killer_fullloadout']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Perfect Games"), value=Functions.convert_number(player_stats['killer_perfectgames']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Survivors Killed"), value=Functions.convert_number(player_stats['killed']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Survivors Sacrificed"), value=Functions.convert_number(player_stats['sacrificed']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Sacrificed all before last gen"), value=Functions.convert_number(player_stats['sacrificed_allbeforelastgen']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Killed/Sacrificed after last gen"), value=Functions.convert_number(player_stats['killed_sacrificed_afterlastgen']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Killed all 4 with tier 3 Myers"), value=Functions.convert_number(player_stats['killed_allevilwithin']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Obsessions Sacrificed"), value=Functions.convert_number(player_stats['sacrificed_obsessions']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Hatches Closed"), value=Functions.convert_number(player_stats['hatchesclosed']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Gens damaged while 1-4 survivors are hooked"), value=Functions.convert_number(player_stats['gensdamagedwhileonehooked']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Gens damaged while undetectable"), value=Functions.convert_number(player_stats['gensdamagedwhileundetectable']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Grabbed while repairing a gen"), value=Functions.convert_number(player_stats['survivorsgrabbedrepairinggen']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Grabbed while you are hiding in locker"), value=Functions.convert_number(player_stats['survivorsgrabbedfrominsidealocker']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Hit one who dropped a pallet in chase"), value=Functions.convert_number(player_stats['survivorshitdroppingpalletinchase']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Hit while carrying"), value=Functions.convert_number(player_stats['survivorshitwhilecarrying']), inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Interrupted cleansing"), value=Functions.convert_number(player_stats['survivorsinterruptedcleansingtotem']), inline=True)
            embed6.add_field(name="\u200b", value="\u200b", inline=True)
            embed6.add_field(name=Functions.translate(interaction, "Vaults while in chase"), value=Functions.convert_number(player_stats['vaultsinchase_askiller']), inline=True)
            #Embed8 - Hooked
            embed7.add_field(name="\u200b", value="\u200b", inline=False)
            embed7.add_field(name=Functions.translate(interaction, "Suvivors hooked before a generator is repaired"), value=Functions.convert_number(player_stats['survivorshookedbeforegenrepaired']), inline=True)
            embed7.add_field(name=Functions.translate(interaction, "Survivors hooked during end game collapse"), value=Functions.convert_number(player_stats['survivorshookedendgamecollapse']), inline=True)
            embed7.add_field(name=Functions.translate(interaction, "Hooked a survivor while 3 other survivors were injured"), value=Functions.convert_number(player_stats['hookedwhilethreeinjured']), inline=True)
            embed7.add_field(name=Functions.translate(interaction, "3 Survivors hooked in basement"), value=Functions.convert_number(player_stats['survivorsthreehookedbasementsametime']), inline=True)
            embed7.add_field(name="\u200b", value="\u200b", inline=True)
            embed7.add_field(name=Functions.translate(interaction, "Survivors hooked in basement"), value=Functions.convert_number(player_stats['survivorshookedinbasement']), inline=True)
            #Embed9 - Powers
            embed8.add_field(name="\u200b", value="\u200b", inline=False)
            embed8.add_field(name=Functions.translate(interaction, "Beartrap Catches"), value=Functions.convert_number(player_stats['beartrapcatches']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Uncloak Attacks"), value=Functions.convert_number(player_stats['uncloakattacks']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Chainsaw Hits  (Billy)"), value=Functions.convert_number(player_stats['chainsawhits']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Blink Attacks"), value=Functions.convert_number(player_stats['blinkattacks']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Phantasms Triggered"), value=Functions.convert_number(player_stats['phantasmstriggered']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Hit each survivor after teleporting to phantasm trap"), value=Functions.convert_number(player_stats['survivorshiteachafterteleporting']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Evil Within Tier Ups"), value=Functions.convert_number(player_stats['evilwithintierup']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Shock Therapy Hits"), value=Functions.convert_number(player_stats['shocked']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Trials with all survivors in madness tier 3"), value=Functions.convert_number(player_stats['survivorsallmaxmadness']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Hatchets Thrown"), value=Functions.convert_number(player_stats['hatchetsthrown']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Pulled into Dream State"), value=Functions.convert_number(player_stats['dreamstate']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Reverse Bear Traps Placed"), value=Functions.convert_number(player_stats['rbtsplaced']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Cages of Atonement"), value=Functions.convert_number(player_stats['cagesofatonement']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Lethal Rush Hits"), value=Functions.convert_number(player_stats['lethalrushhits']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Lacerations"), value=Functions.convert_number(player_stats['lacerations']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Possessed Chains"), value=Functions.convert_number(player_stats['possessedchains']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Condemned"), value=Functions.convert_number(player_stats['condemned']), inline=True)
            embed8.add_field(name=Functions.translate(interaction, "Slammed"), value=Functions.convert_number(player_stats['slammedsurvivors']), inline=True)
            #Embed10 - Survivors downed
            embed9.add_field(name="\u200b", value="\u200b", inline=False)
            embed9.add_field(name=Functions.translate(interaction, "Downed while suffering from oblivious"), value=Functions.convert_number(player_stats['survivorsdowned_oblivious']), inline=True)
            embed9.add_field(name=Functions.translate(interaction, "Downed while Exposed"), value=Functions.convert_number(player_stats['survivorsdowned_exposed']), inline=True)
            embed9.add_field(name=Functions.translate(interaction, "Downed while carrying a survivor"), value=Functions.convert_number(player_stats['survivorsdownedwhilecarrying']), inline=True)
            embed9.add_field(name=Functions.translate(interaction, "Downed near a raised pallet"), value=Functions.convert_number(player_stats['survivorsdownednearraisedpallet']), inline=True)
            #Embed11 - Survivors downed with power
            embed10.add_field(name="\u200b", value="\u200b", inline=False)
            embed10.add_field(name=Functions.translate(interaction, "Downed with a Hatchet (24+ meters)"), value=Functions.convert_number(player_stats['survivorsdowned_hatchets']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed with a Chainsaw (Bubba)"), value=Functions.convert_number(player_stats['survivorsdowned_chainsaw']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while Intoxicated"), value=Functions.convert_number(player_stats['survivorsdowned_intoxicated']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed after Haunting"), value=Functions.convert_number(player_stats['survivorsdowned_haunting']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while in Deep Wound"), value=Functions.convert_number(player_stats['survivorsdowned_deepwound']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while having max sickness"), value=Functions.convert_number(player_stats['survivorsdowned_maxsickness']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while marked (Ghostface)"), value=Functions.convert_number(player_stats['survivorsdowned_marked']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while using Shred"), value=Functions.convert_number(player_stats['survivorsdowned_shred']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while using Blood Fury"), value=Functions.convert_number(player_stats['survivorsdowned_bloodfury']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while Speared"), value=Functions.convert_number(player_stats['survivorsdowned_speared']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while Victor is clinging to them"), value=Functions.convert_number(player_stats['survivorsdowned_victor']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while contaminated"), value=Functions.convert_number(player_stats['survivorsdowned_contaminated']), inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed while using Dire Crows"), value=Functions.convert_number(player_stats['survivorsdowned_direcrows']), inline=True)
            embed10.add_field(name="\u200b", value="\u200b", inline=True)
            embed10.add_field(name=Functions.translate(interaction, "Downed during nightfall"), value=Functions.convert_number(player_stats['survivorsdowned_nightfall']), inline=True)
            #Send Statistics
            await interaction.edit_original_response(embeds=[embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed8, embed9, embed10])    

    async def character(interaction: discord.Interaction, char: str):
        await interaction.response.defer(thinking = True)
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.")
            return
        data = await Functions.character_load()
        if data == 1:
            await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
            return
        dlc_data = await Functions.dlc_load()
        if dlc_data == 1:
            await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
            return
        if char == '':
            await interaction.followup.send(content=Functions.translate(interaction, "Here are the characters:"), file = discord.File(buffer_folder+'characters.txt'))
            return
        else:
            for key in data.keys():
                if str(data[key]['id']).lower() == char.lower().replace('the ', '') or str(data[key]['name']).lower().replace('the ', '') == char.lower():
                    embed = discord.Embed(title=Functions.translate(interaction, "Character Info"), description=str(data[key]['name']), color=0xb19325)
                    embed.set_thumbnail(url=bot_base+str(data[key]['image']))
                    print(bot_base+str(data[key]['image']))
                    embed.add_field(name=Functions.translate(interaction, "Role"), value=str(data[key]['role']).capitalize(), inline=True)
                    embed.add_field(name=Functions.translate(interaction, "Gender"), value=str(data[key]['gender']).capitalize(), inline=True)
                    for dlc_key in dlc_data.keys():
                        if dlc_key == data[key]['dlc']:
                            embed.add_field(name="DLC", value='['+str(dlc_data[dlc_key]['name']).capitalize().replace(' chapter', '')+']('+steamStore+str(dlc_data[dlc_key]['steamid'])+')', inline=True)
                    if data[key]['difficulty'] != 'none':
                        embed.add_field(name=Functions.translate(interaction, "Difficulty"), value=str(data[key]['difficulty']).capitalize(), inline=True)
                    if str(data[key]['role']) == 'killer':
                        embed.add_field(name=Functions.translate(interaction, "Walkspeed"), value=str(int(data[key]['tunables']['maxwalkspeed']) / 100)+'m/s', inline=True)
                        embed.add_field(name=Functions.translate(interaction, "Terror Radius"), value=str(int(data[key]['tunables']['terrorradius']) / 100)+'m', inline=True)
                    embed.add_field(name='\u200b', value='\u200b', inline=False)
                    embed.add_field(name="Bio", value=Functions.translate(interaction, str(data[key]['bio']).replace('<br><br>', '').replace('<br>', '').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.', '. ')), inline=False)
                    if len(data[key]['story']) > 4096:
                        story = buffer_folder+'character_story.txt'
                        if os.path.exists(story):
                            story = buffer_folder+'character_story'+str(randrange(1, 999))+'.txt'
                        with open(story, 'w', encoding='utf8') as f:
                            f.write(Functions.translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.')).replace('.', '. '))
                        await interaction.followup.send('Story', file=discord.File(r''+story))
                        os.remove(story)
                    elif 1024 < len(data[key]['story']) < 4096:
                        embed2 = discord.Embed(title='Story', description=Functions.translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('&nbsp;', ' ')).replace('.', '. '), color=0xb19325)
                        await interaction.followup.send(embeds=[embed, embed2])
                        return
                    else:
                        embed.add_field(name="Story", value=Functions.translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('<br>', '').replace('&nbsp;', ' ')).replace('.', '. '), inline=False)
                    await interaction.followup.send(embed=embed)
                    return
            embed = discord.Embed(title=Functions.translate(interaction, "Character Info"), description=Functions.translate(interaction, f"I couldn't find a character named {char}."), color=0xb19325)
            await interaction.followup.send(embed=embed)
            
    async def dlc(interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        data = await Functions.dlc_load()
        if name == '':
            embed = discord.Embed(title="DLC Info (1/2)",  description=Functions.translate(interaction, "Here is a list of all DLCs. Click the link to go to the steam storepage.").replace('.','. '), color=0xb19325)
            embed2 = discord.Embed(title="DLC Info (2/2)", description=Functions.translate(interaction, "Here is a list of all DLCs. Click the link to go to the steam storepage.").replace('.','. '), color=0xb19325)
            embed.add_field(name='\u200b', value='\u200b', inline=False)
            embed2.add_field(name='\u200b', value='\u200b', inline=False)
            i = 0
            for key in data.keys():
                if data[key]['steamid'] == 0:
                    continue
                if i <= 25:
                    embed.add_field(name=str(data[key]['name']), value='['+Functions.convert_time_dateonly(data[key]['time'])+']('+steamStore+str(data[key]['steamid'])+')')
                    i += 1
                if i > 25:
                    embed2.add_field(name=str(data[key]['name']), value='['+Functions.convert_time_dateonly(data[key]['time'])+']('+steamStore+str(data[key]['steamid'])+')')
            await interaction.followup.send(embeds=[embed, embed2])
        else:
            for key in data.keys():
                if data[key]['name'].lower() == name.lower():
                    embed = discord.Embed(title="DLC description for '"+data[key]['name']+"'", description=Functions.translate(interaction, str(data[key]['description']).replace('<br><br>', ' ')), color=0xb19325)
                    embed.set_thumbnail(url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{data[key]['steamid']}/header.jpg")
                    await interaction.followup.send(embed=embed)

    async def item(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        data = await Functions.items_load()
        if data == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the item data."))
            return
        print(f'NAME: {name}')
        if name == '':
            await interaction.followup.send(content = 'Here is a list of all items. You can use the command again with one of the items to get more info about it.', file = discord.File(buffer_folder+'items.txt'))
            return
        else:
            for i in data.keys():
                if str(data[i]['name']).lower() == name.lower() or str(i).lower() == name.lower():
                    if data[i]['name'] is None:
                        title = i
                        print(f'item1: {title}')
                    else:
                        title = data[i]['name']
                        print(f'item2: {title}')
                    embed = discord.Embed(title = title,
                                          description = Functions.translate(interaction, str(data[i]['description']).replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '').replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.')).replace('.', '. '),
                                          color = 0x00ff00)
                    embed.set_thumbnail(url = bot_base+data[i]['image'])
                    embed.add_field(name = '\u200b', value = '\u200b', inline = False)
                    embed.add_field(name = 'Rarity', value = str(data[i]['rarity']))
                    embed.add_field(name = 'Is in Bloodweb', value = str(data[i]['bloodweb']))
                    embed.add_field(name = 'Role', value = str(data[i]['role']))
                    if data[i]['event'] is not None:
                        embed.add_field(name = 'Event', value = str(data[i]['event']))
                    await interaction.followup.send(embed = embed)
                    
    async def map(interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        if os.path.exists(buffer_folder+'maps_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'maps_info.json')) / 3600) >= 4 or not os.path.exists(buffer_folder+'maps_info.json'):
            data = await Functions.check_429(api_base+'maps')
            if data == 1:
                await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
            with open(buffer_folder+'maps_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
        if name == '' and os.path.exists(buffer_folder+'maps.txt') and ((time.time() - os.path.getmtime(buffer_folder+'maps.txt')) / 3600) <= 4:
                await interaction.followup.send(file=discord.File(r''+buffer_folder+'maps.txt'))
                return
        elif name == '':
            map_info = open(buffer_folder+'maps_info.json', 'r', encoding='utf8')
            map_data = json.loads(map_info.read())
            with open(buffer_folder+'maps.txt', 'w', encoding='utf8') as f:
                for key in map_data.keys():
                    if key == 'Swp_Mound':
                        continue
                    f.write('Name: '+map_data[key]['name']+'\n')
                    map_info.close()
            await interaction.followup.send(file=discord.File(r''+buffer_folder+'maps.txt'))
        else:
            map_info = open(buffer_folder+'maps_info.json', 'r', encoding='utf8')
            map_data = json.loads(map_info.read())
            for key in map_data.keys():
                if map_data[key]['name'] == 'Swp_Mound':
                    continue
                if map_data[key]['name'].lower() == name.lower():
                    embed = discord.Embed(title="Map description for '"+map_data[key]['name']+"'", description=Functions.translate(interaction, str(map_data[key]['description']).replace('<br><br>', ' ')).replace('.','. '), color=0xb19325)
                    embed.set_thumbnail(url=map_portraits+key+'.png')
                    await interaction.followup.send(embed=embed)
                    map_info.close()
                    return
            map_info.close()
            await interaction.followup.send(f"No map with name **{name}** found.")                    

    async def offering(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        data = await Functions.offerings_load()
        if data == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the perk data."))
            return
        if name == '':
            await interaction.followup.send(content = 'Here is a list of all offerings. You can use the command again with one of the offerings to get more info about it.', file = discord.File(buffer_folder+'offerings.txt'))
            return
        else:
            for item in data.keys():
                if str(data[item]['name']).lower() == name.lower() or str(item).lower() == name.lower():
                    embed = discord.Embed(title = data[item]['name'],
                                          description = Functions.translate(interaction, str(data[item]['description']).replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '').replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.')).replace('.', '. '),
                                          color = 0x00ff00)
                    embed.set_thumbnail(url = bot_base+data[item]['image'])
                    embed.add_field(name = '\u200b', value = '\u200b', inline = False)
                    embed.add_field(name = 'Rarity', value = data[item]['rarity'])
                    embed.add_field(name = 'Type', value = data[item]['type'])
                    embed.add_field(name = 'Tags', value = str(data[item]['tags']).replace('[', '').replace(']', '').replace('\'', ''))
                    embed.add_field(name = 'Role', value = data[item]['role'])
                    embed.add_field(name = '\u200b', value = '\u200b')
                    embed.add_field(name = 'Retired', value = data[item]['retired'])
                    await interaction.followup.send(embed = embed)
                    return
            await interaction.followup.send(Functions.translate(interaction, "This offering doesn't exist."))

    async def perk(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
        data = await Functions.perk_load()
        if data == 1:
            await interaction.followup.send("Error while loading the perk data.")
            return
        else:
            if name == '':
                await interaction.followup.send(content = 'Here are the perks:' , file=discord.File(r''+buffer_folder+'perks.txt'))
            else:
                test = await Functions.send_perk_info(data, name, interaction)
                if test == 1:
                    await interaction.followup.send(f"There is no perk named {name}.")
                return

    async def killswitch(interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        resp = r.get(f'{bot_base}killswitch.json')
        data = resp.json()
        count = len(data.keys())
        for i in data.keys():
            if data[i]['Text'] == '':
                count -= 1  
            else:
                embed = discord.Embed(title="Killswitch", description=Functions.translate(interaction, data[i]['Text']).replace('.','. '), type='rich' , color=0xb19325)
                embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
                embed.add_field(name="\u200b", value=f"[Forum]({data[i]['Forum']})", inline=True)
                embed.add_field(name="\u200b", value=f"[Twitter]({data[i]['Twitter']})", inline=True)
                embed.set_footer(text=Functions.translate(interaction, "The data from this Kill Switch is updated manually.\nThis means it can take some time to update after BHVR changed it.").replace('.','. '))
                await interaction.followup.send(embed=embed)
        if count == 0:
            embed = discord.Embed(title="Killswitch", description=Functions.translate(interaction, 'Currently there is no Kill Switch active.').replace('.','. '), color=0xb19325)
            embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
            await interaction.followup.send(embed=embed)

    async def shrine(interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        data = await Functions.shrine_load()
        if data == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the perk data."))
        perks = await Functions.perk_load()
        if perks == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the perk data."))
            return
        embeds = []
        for shrine in data['perks']:
            print(shrine)
            for perk in perks.keys():
                if perk == shrine['id']:
                    shrine_embed = await Functions.send_perk_info(perks, perk, interaction, True)
                    shrine_embed.set_footer(text=f"Bloodpoints: {Functions.convert_number(shrine['bloodpoints'])} | Shards: {Functions.convert_number(shrine['shards'])}")
                    embeds.append(shrine_embed)               
        await interaction.followup.send(content = 'This is the current shrine.\nIt started at <t:'+str(data['start'])+'> and will last until <t:'+str(data['end'])+'>.\nUpdates every 4h.', embeds=embeds)

    async def version(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.")
        else:
            data = await Functions.check_429(api_base+'versions')
            if data == 1:
                await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '), ephemeral=True)
                return
            embed = discord.Embed(title='DB Version (1/2)', color=0x42a32e)
            embed.add_field(name=Functions.translate(interaction, 'Name'), value='\u200b', inline=True)
            embed.add_field(name=Functions.translate(interaction, 'Version'), value='\u200b', inline=True)
            embed.add_field(name=Functions.translate(interaction, 'Last Update'), value='\u200b', inline=True)
            embed2 = discord.Embed(title='DB Version (2/2)', color=0x42a32e)
            embed2.add_field(name=Functions.translate(interaction, 'Name'), value='\u200b', inline=True)
            embed2.add_field(name=Functions.translate(interaction, 'Version'), value='\u200b', inline=True)
            embed2.add_field(name=Functions.translate(interaction, 'Last Update'), value='\u200b', inline=True)
            resp = r.get(api_base+'versions')
            data = resp.json()
            i = 0
            for key in data.keys():
                i += 1
                if i <= 5:
                    embed.add_field(name='\u200b', value=key.capitalize(), inline=True)
                    embed.add_field(name='\u200b', value=data[key]['version'], inline=True)
                    embed.add_field(name='\u200b', value=str(Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
                if i >= 6:
                    embed2.add_field(name='\u200b', value=key.capitalize(), inline=True)
                    embed2.add_field(name='\u200b', value=data[key]['version'], inline=True)
                    embed2.add_field(name='\u200b', value=str(Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
            await interaction.followup.send(embeds=[embed, embed2])
        
    async def playercount(interaction: discord.Interaction):
        async def selfembed(data):
            embed = discord.Embed(title=Functions.translate(interaction, "Playercount"), color=0xb19325)
            embed.set_thumbnail(url="https://cdn.bloodygang.com/botfiles/dbd.png")
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=Functions.translate(interaction, "Current"), value=Functions.convert_number(int(data['Current Players'])), inline=True)
            embed.add_field(name=Functions.translate(interaction, "24h Peak"), value=Functions.convert_number(int(data['Peak Players 24h'])), inline=True)
            embed.add_field(name=Functions.translate(interaction, "All-time Peak"), value=Functions.convert_number(int(data['Peak Players All Time'])), inline=True)
            embed.set_footer(text=Functions.translate(interaction, "This will be updated every full hour."))
            await interaction.followup.send(embed = embed)
        async def selfget():
            url = 'https://steamcharts.com/app/381210'
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26'}
            page = r.get(url, headers = header)
            if page.status_code != 200:
                await interaction.followup.send(Functions.translate(interaction, "Error while fetching the playercount.").replace('.','. '))
                manlogger.warning(str(page.status_code)+' while accessing '+url)
            soup = BeautifulSoup(page.text, 'html.parser')
            data = {}
            count = 0
            for stats in soup.find_all('div', class_='app-stat'):
                soup2 = BeautifulSoup(str(stats), 'html.parser')
                for stat in soup2.find_all('span', class_='num'):
                    stat = str(stat).replace('<span class="num">', '').replace('</span>', '')
                    if count == 0:
                        data['Current Players'] = stat
                    elif count == 1:
                        data['Peak Players 24h'] = stat
                    elif count == 2:
                        data['Peak Players All Time'] = stat
                    count += 1
                data['update_hour'] = datetime.now().hour
            with open(buffer_folder+'playercount.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            return data
        await interaction.response.defer(thinking = True)
        if os.path.exists(buffer_folder+'playercount.json'):
            with open(buffer_folder+'playercount.json', 'r', encoding='utf8') as f:
                data = json.load(f)
            if data['update_hour'] == datetime.now().hour and ((time.time() - os.path.getmtime(buffer_folder+'playercount.json')) / 3600) <= 23:
                await selfembed(data)
                return
        await selfembed(await selfget())
        
    async def legacycheck(interaction: discord.Interaction, steamid):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        check = Functions.CheckForDBD(steamid, steamAPIkey)
        if check[0] == 1:
            await interaction.followup.send(Functions.translate(interaction, 'The SteamID64 has to be 17 chars long and only containing numbers.'))   
        elif check[0] == 2:
            await interaction.followup.send(Functions.translate(interaction, 'This SteamID64 is NOT in use.'))
        elif check[0] == 3:
            await interaction.followup.send(Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking").replace('.','. ')+"\n[here](https://steamcommunity.com/profiles/"+id+"/edit/settings).")
        elif check[0] == 4:
            await interaction.followup.send(Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look").replace('.','. ')+" [here](https://www.g2a.com/n/dbdstats).")
        elif check[0] == 5:
            embed1=discord.Embed(title="Fatal Error", description=Functions.translate(interaction, "It looks like there was an error querying the SteamAPI (probably a rate limit).\nPlease join our").replace('.','. ')+" [Support-Server]("+str(await Functions.create_support_invite(interaction))+Functions.translate(interaction, ") and create a ticket to tell us about this."), color=0xff0000)
            embed1.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.response.send_message(embed=embed1)
        elif check[0] == 0:
            resp = r.get(f'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={steamAPIkey}&steamid={check[1]}&appid=381210')
            data = resp.json()
            if data['playerstats']['success'] == False:
                await interaction.followup.send(Functions.translate(interaction, 'This profile is private.'))
                return
            for entry in data['playerstats']['achievements']:
                if entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 1 and int(entry['unlocktime']) < 1480017600:
                    await interaction.followup.send(Functions.translate(interaction, 'This player has probably legit legacy.').replace('.','. '))
                    return
                elif entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 1 and int(entry['unlocktime']) > 1480017600:
                    await interaction.followup.send(Functions.translate(interaction, 'If this player has legacy, they are pobably hacked.').replace('.','. '))
                    return
                elif entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 0:
                    await interaction.followup.send(Functions.translate(interaction, "This player doesn't even have one character prestiged.").replace('.','. '))
                    return
    
                
                
            
                    



##Owner Commands (Can only be used by the BotOwner.)
#Shutdown
@tree.command(name = 'shutdown', description = 'Savely shut down the bot.')
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        manlogger.info('Engine powering down...')
        await interaction.response.send_message(Functions.translate(interaction, 'Engine powering down...'), ephemeral = True)
        await bot.change_presence(status = discord.Status.offline)
        await bot.close()
    else:
        await interaction.response.send_message(Functions.translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
#Get Logs
@tree.command(name = 'get_logs', description = 'Get the current, or all logfiles.')
async def self(interaction: discord.Interaction):
    class LastXLines(discord.ui.Modal, title = 'Line Input'):
        self.timeout = 15
        answer = discord.ui.TextInput(label = Functions.translate(interaction, 'How many lines?'), style = discord.TextStyle.short, required = True, min_length = 1, max_length = 4)
        async def on_submit(self, interaction: discord.Interaction):
            try:
                int(self.answer.value)
            except:
                await interaction.response.send_message(content = Functions.translate(interaction, 'You can only use numbers!'), ephemeral = True)
                return
            if int(self.answer.value) == 0:
                await interaction.response.send_message(content = Functions.translate(interaction, 'You can not use 0 as a number!'), ephemeral = True)
                return
            with open(log_folder+'DBDStats.log', 'r', encoding='utf8') as f:
                with open(buffer_folder+'log-lines.txt', 'w', encoding='utf8') as f2:
                    count = 0
                    for line in (f.readlines()[-int(self.answer.value):]):
                        f2.write(line)
                        count += 1
            await interaction.response.send_message(content = Functions.translate(interaction, 'Here are the last '+str(count)+' lines of the current logfile:'), file = discord.File(r''+buffer_folder+'log-lines.txt') , ephemeral = True)
            if os.path.exists(buffer_folder+'log-lines.txt'):
                os.remove(buffer_folder+'log-lines.txt')
             
    class LogButton(discord.ui.View):
        def __init__(self):
            super().__init__()
            
        @discord.ui.button(label = Functions.translate(interaction, 'Last X lines'), style = discord.ButtonStyle.blurple)
        async def xlines(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            #await interaction.response.defer()
            await interaction.response.send_modal(LastXLines())
     
        @discord.ui.button(label = Functions.translate(interaction, 'Current Log'), style = discord.ButtonStyle.grey)
        async def current(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            await interaction.response.defer()
            try:
                await interaction.followup.send(file=discord.File(r''+log_folder+'DBDStats.log'), ephemeral=True)
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                        f.write(log_folder+'DBDStats.log')
                    try:
                        await interaction.response.send_message(file=discord.File(r''+buffer_folder+'Logs.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await interaction.followup.send(Functions.translate(interaction, "The log is too big to be send directly.\nYou have to look at the log in your server(VPS)."))
                os.remove(buffer_folder+'Logs.zip')
                            
        @discord.ui.button(label = Functions.translate(interaction, 'Whole Folder'), style = discord.ButtonStyle.grey)
        async def whole(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            await interaction.response.defer()
            if os.path.exists(buffer_folder+'Logs.zip'):
                os.remove(buffer_folder+'Logs.zip')
            with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                for file in os.listdir(log_folder):
                    if file.endswith(".zip"):
                        continue
                    f.write(log_folder+file)
            try:
                await interaction.followup.send(file=discord.File(r''+buffer_folder+'Logs.zip'), ephemeral=True)
            except discord.HTTPException as err:
                if err.status == 413:
                    await interaction.followup.send(Functions.translate(interaction, "The folder is too big to be send directly.\nPlease get the current file, or the last X lines."))          
            os.remove(buffer_folder+'Logs.zip')
    if interaction.user.id != int(ownerID):
        await interaction.response.send_message(Functions.translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
        return
    else:
        await interaction.response.send_message(Functions.translate(interaction, 'Send only the current Log, or the whole folder?'), view = LogButton(), ephemeral = True)
#Clear Buffer        
@tree.command(name = 'clear_buffer', description = 'Delete all files in buffer that are older than 4h.')
async def self(interaction: discord.Interaction):
    i = 0
    for filename in os.scandir(buffer_folder):
        if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 4:
            os.remove(filename)
            i += 1
    for filename in os.scandir(stats_folder):
        if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 4:
            os.remove(filename)
            i += 1
    await interaction.response.send_message(content=Functions.translate(interaction, f'I deleted {i} files.'), ephemeral=True)
#Change Activity
@tree.command(name = 'activity', description = 'Change my activity.')
@discord.app_commands.describe(type='The type of Activity you want to set.', title='What you want the bot to play, stream, etc...', url='Url of the stream. Only used if activity set to \'streaming\'.')
@discord.app_commands.choices(type=[
    discord.app_commands.Choice(name='Playing', value='Playing'),
    discord.app_commands.Choice(name='Streaming', value='Streaming'),
    discord.app_commands.Choice(name='Listening', value='Listening'),
    discord.app_commands.Choice(name='Watching', value='Watching'),
    discord.app_commands.Choice(name='Competing', value='Competing')
    ])
async def self(interaction: discord.Interaction, type: str, title: str, url: str = ''):
    if interaction.user.id == int(ownerID):
        await interaction.response.defer(ephemeral = True)
        with open('activity.json') as f:
            data = json.load(f)
        if type == 'Playing':
            data['activity_type'] = 'Playing'
            data['activity_title'] = title
        elif type == 'Streaming':
            data['activity_type'] = 'Streaming'
            data['activity_title'] = title
            data['activity_url'] = url
        elif type == 'Listening':
            data['activity_type'] = 'Listening'
            data['activity_title'] = title
        elif type == 'Watching':
            data['activity_type'] = 'Watching'
            data['activity_title'] = title
        elif type == 'Competing':
            data['activity_type'] = 'Competing'
            data['activity_title'] = title
        with open('activity.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = Presence.get_activity(), status = Presence.get_status())
        await interaction.followup.send(Functions.translate(interaction, 'Activity changed!'), ephemeral = True)
    else:
        await interaction.followup.send(Functions.translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
#Change Status
@tree.command(name = 'status', description = 'Change my status.')
@discord.app_commands.describe(status='The status you want to set.')
@discord.app_commands.choices(status=[
    discord.app_commands.Choice(name='Online', value='online'),
    discord.app_commands.Choice(name='Idle', value='idle'),
    discord.app_commands.Choice(name='Do not disturb', value='dnd'),
    discord.app_commands.Choice(name='Invisible', value='invisible')
    ])
async def self(interaction: discord.Interaction, status: str):
    if interaction.user.id == int(ownerID):
        await interaction.response.defer(ephemeral = True)
        with open('activity.json') as f:
            data = json.load(f)
        data['status'] = status
        with open('activity.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = Presence.get_activity(), status = Presence.get_status())
        await interaction.followup.send(Functions.translate(interaction, 'Status changed!'), ephemeral = True)
    else:
        await interaction.followup.send(Functions.translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
#Sync Commands
@tree.command(name = 'sync', description = 'Sync commands to guild.')
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        await interaction.response.defer(ephemeral = True)
        await interaction.followup.send('Syncing...')
        await tree.sync()
        await interaction.edit_original_response(content='Synced.')
    else:
        await interaction.response.send_message('You are not allowed to use this command.', ephemeral = True)        
      
        
##Bot Commands (These commands are for the bot itself.)
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! `{int(ping)}ms`')
#Change Nickname
@tree.command(name = 'change_nickname', description = 'Change the nickname of the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_nicknames = True)
@discord.app_commands.describe(nick='New nickname for me.')
async def self(interaction: discord.Interaction, nick: str):
    await interaction.guild.me.edit(nick=nick)
    await interaction.response.send_message(Functions.translate(interaction, f'My new nickname is now **{nick}**.'), ephemeral=True)
#Support Invite
@tree.command(name = 'support', description = 'Get invite to our support server.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
async def self(interaction: discord.Interaction):
    if interaction.guild.id != support_id:
        await interaction.response.send_message(await Functions.create_support_invite(interaction))
    else:
        await interaction.response.send_message(Functions.translate(interaction, 'You are already in our support server!'))
#Setup
@tree.command(name = 'setup_help', description = 'Get help with translation setup.')
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id))
async def self(interaction: discord.Interaction):
    language = discord.Embed(title="Setup - Language", description=Functions.translate(interaction, "Most outputs will be translated using Google Translator. However the default will be English. Every user can have there own language the bot will use on reply. To use this feature, you must have roles that are named **exactly** like following. Because there are 107 Languages/Roles, you have to setup the roles you need on your own.")+"\n\nAfrikaans, Albanian, Amharic, Arabic, Armenian, Azerbaijani, Basque, Belarusian, Bengali, Bosnian, Bulgarian, Catalan, Cebuano, Chichewa, Chinese (Simplified), Chinese (Traditional), Corsican, Croatian, Czech, Danish, Dutch, Esperanto, Estonian, Filipino, Finnish, French, Frisian, Galician, Georgian, German, Greek, Gujarati, Haitian Creole, Hausa, Hawaiian, Hebrew, Hebrew, Hindi, Hmong, Hungarian, Icelandic, Igbo, Indonesian, Irish, Italian, Japanese, Javanese, Kannada, Kazakh, Khmer, Korean, Kurdish (Kurmanji), Kyrgyz, Lao, Latin, Latvian, Lithuanian, Luxembourgish, Macedonian, Malagasy, Malay, Malayalam, Maltese, Maori, Marathi, Mongolian, Myanmar (Burmese), Nepali, Norwegian, Odia, Pashto, Persian, Polish, Portuguese, Punjabi, Romanian, Russian, Samoan, Scots Gaelic, Serbian, Sesotho, Shona, Sindhi, Sinhala, Slovak, Slovenian, Somali, Spanish, Sundanese, Swahili, Swedish, Tajik, Tamil, Telugu, Thai, Turkish, Ukrainian, Urdu, Uyghur, Uzbek, Vietnamese, Welsh, Xhosa, Yiddish, Yoruba, Zulu", color=0x004cff)
    await interaction.response.send_message(embeds=[language])
       


    
##DBD Commands (these commands are for DeadByDaylight.)


#Buy
@tree.command(name = "buy", description = 'This will post a link to a site where you can buy DeadByDaylight for a few bucks.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))        
async def self(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(Functions.translate(interaction, "This command can only be used in a server."))
    else:
        embed = discord.Embed(title="Buy Dead By Daylight", description=Functions.translate(interaction, "Click the title, to buy the game for a few bucks."), url="https://www.g2a.com/n/dbdstats", color=0x00ff00)
        await interaction.response.send_message(embed=embed)


 
                

#Info about Stuff
@tree.command(name = 'info', description = 'Get info about DBD related stuff.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
@discord.app_commands.describe(category = 'The category you want to get informations about.')
@discord.app_commands.choices(category = [
    discord.app_commands.Choice(name = 'Characters', value = 'char'),
    discord.app_commands.Choice(name = 'Playerstats', value = 'stats'),
    discord.app_commands.Choice(name = 'DLCs', value = 'dlc'),
    discord.app_commands.Choice(name = 'Events', value = 'event'),
    discord.app_commands.Choice(name = 'Items', value = 'item'),
    discord.app_commands.Choice(name = 'Maps', value = 'map'),
    discord.app_commands.Choice(name = 'Offerings', value = 'offering'),
    #discord.app_commands.Choice(name = 'Perks', value = 'perk'),
    discord.app_commands.Choice(name = 'Killswitch', value = 'killswitch'),
    discord.app_commands.Choice(name = 'Shrine', value = 'shrine'),
    discord.app_commands.Choice(name = 'Versions', value = 'version'),
    discord.app_commands.Choice(name = 'Rankreset', value = 'reset'),
    discord.app_commands.Choice(name = 'Playercount', value = 'player'),
    discord.app_commands.Choice(name = 'Legacy check', value = 'legacy'),
    ])
async def self(interaction: discord.Interaction, category: str):
    if interaction.guild is None:
        interaction.followup.send("This command can only be used in a server.")
        return
    if category == 'char':
        class Input(discord.ui.Modal, title = 'Get info about a char. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Enter ID or Name. Leave emnpty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.character(interaction, char = self.answer.value.strip())
        await interaction.response.send_modal(Input())
    elif category == 'stats':
        class Input(discord.ui.Modal, title = 'Enter SteamID64. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'ID64 or vanity(url) you want stats for.', style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.playerstats(interaction, steamid = self.answer.value.strip())
        await interaction.response.send_modal(Input())  
    elif category == 'dlc':
        class Input(discord.ui.Modal, title = 'Enter DLC. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'DLC you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.dlc(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())
    elif category == 'event':
        await Info.event(interaction)
    elif category == 'item':
        class Input(discord.ui.Modal, title = 'Enter Item. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Item you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.item(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())
    elif category == 'map':
        class Input(discord.ui.Modal, title = 'Enter Map. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Map you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.map(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())
    elif category == 'offering':
        class Input(discord.ui.Modal, title = 'Enter Offering. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Offering you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.offering(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())
    elif category == 'perk':
        class Input(discord.ui.Modal, title = 'Enter Perk. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Perk you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.perk(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())
    elif category == 'killswitch':
        await Info.killswitch(interaction)
    elif category == 'shrine':
        await Info.shrine(interaction)
    elif category == 'version':
        await Info.version(interaction)
    elif category == 'reset':
        await Info.rankreset(interaction)
    elif category == 'player':
        await Info.playercount(interaction)
    elif category == 'legacy':
        class Input(discord.ui.Modal, title = 'Enter SteamID64. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'ID64 or vanity(url) you want to check.', style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                print(self.answer.value)
                await Info.legacycheck(interaction, steamid = self.answer.value.strip())
        await interaction.response.send_modal(Input())         
    
   
            
    
            
    

    
    









bot.run(TOKEN, log_handler=None)
