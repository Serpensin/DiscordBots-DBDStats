#Import
print('Loading...')
import asyncio
import aiohttp
import discord
import json
import logging
import logging.handlers
import os
import pathlib
import platform
import pycountry
import random
import requests as r
import sys
import time
from bs4 import BeautifulSoup
from datetime import timedelta, datetime
from discord.ext import tasks, commands
from dotenv import load_dotenv
from googletrans import Translator
from prettytable import PrettyTable
from twitch import TwitchAPI
from zipfile import ZIP_DEFLATED, ZipFile

    
#.replace('<br><br>', ' ').replace('<i>', '**').replace('</i>', '**').replace('<li>', '*').replace('</li>', '*').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.','. ')


#Set vars
api_base = 'https://dbd.tricky.lol/api/'                                
perks_base = 'https://dbd.tricky.lol/dbdassets/perks/'
bot_base = 'https://cdn.bloodygang.com/botfiles/DBDStats/'
map_portraits = bot_base+'mapportraits/'  
alt_playerstats = 'https://dbd.tricky.lol/playerstats/'
steamStore = 'https://store.steampowered.com/app/'
languages = ['Afrikaans', 'Albanian', 'Amharic', 'Arabic', 'Armenian', 'Azerbaijani',
             'Basque', 'Belarusian', 'Bengali', 'Bosnian', 'Bulgarian',
             'Catalan', 'Cebuano', 'Chichewa', 'Chinese (Simplified)', 'Chinese (Traditional)', 'Corsican', 'Croatian', 'Czech',
             'Danish', 'Dutch', 'English', 'Esperanto', 'Estonian', 'Filipino', 'Finnish', 'French', 'Frisian',
             'Galician', 'Georgian', 'German', 'Greek', 'Gujarati',
             'Haitian Creole', 'Hausa', 'Hawaiian', 'Hebrew', 'Hebrew', 'Hindi', 'Hmong', 'Hungarian',
             'Icelandic', 'Igbo', 'Indonesian', 'Irish', 'Italian', 'Japanese', 'Javanese',
             'Kannada', 'Kazakh', 'Khmer', 'Korean', 'Kurdish (Kurmanji)', 'Kyrgyz',
             'Lao', 'Latin', 'Latvian', 'Lithuanian', 'Luxembourgish',
             'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori', 'Marathi', 'Mongolian', 'Myanmar (Burmese)',
             'Nepali', 'Norwegian', 'Odia', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi',
             'Romanian', 'Russian', 'Samoan', 'Scots Gaelic', 'Serbian', 'Sesotho', 'Shona', 'Sindhi',
             'Sinhala', 'Slovak', 'Slovenian', 'Somali', 'Spanish', 'Sundanese', 'Swahili', 'Swedish',
             'Tajik', 'Tamil', 'Telugu', 'Thai', 'Turkish', 'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek',
             'Vietnamese', 'Welsh', 'Xhosa', 'Yiddish', 'Yoruba', 'Zulu']


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
stats_folder = os.path.abspath('DBDStats//Buffer//Stats//')
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
twitch_client_id = os.getenv('twitch_client_id')
twitch_client_secret = os.getenv('twitch_client_secret')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
translator = Translator()
tb = PrettyTable()
twitch_api = TwitchAPI(twitch_client_id, twitch_client_secret)
cleanup_lock = asyncio.Lock()
#Fix error on windows on shutdown.
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')
# print() will only print if run in debugger. pt() will always print.
pt = print
def print(msg):
    if sys.gettrace() is not None:
        pt(msg)



# Check if all required variables are set
twitch_available = bool(twitch_client_secret and twitch_client_id)
support_available = bool(support_id)
owner_available = bool(ownerID)
if not TOKEN or not steamAPIkey:
    manlogger.critical('Missing token or steam API key. Please check your .env file.')
    pt('Missing token or steam API key. Please check your .env file.')
    exit()



@tasks.loop(hours=1)
async def cleanup():
    async with cleanup_lock:
        manlogger.info('Cleaning up buffer...')
        for filename in os.scandir(stats_folder):
            if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 4:
                try:
                    os.remove(filename)
                except Exception as e:
                    manlogger.info(f"Error while deleting {filename.path}: {e}")



#Presence    
class Presence():
    @staticmethod
    def get_activity() -> discord.Activity:
        with open('activity.json') as f:
            data = json.load(f)
            activity_type = data['activity_type']
            activity_title = data['activity_title']
            activity_url = data['activity_url']
        if activity_type == 'Playing':
            return discord.Game(name=activity_title)
        elif activity_type == 'Streaming':
            return discord.Streaming(name=activity_title, url=activity_url)
        elif activity_type == 'Listening':
            return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
        elif activity_type == 'Watching':
            return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
        elif activity_type == 'Competing':
            return discord.Activity(type=discord.ActivityType.competing, name=activity_title)
    
    @staticmethod
    def get_status() -> discord.Status:
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
            manlogger.info('------')
            manlogger.info('Syncing...')
            await tree.sync()
            manlogger.info('Synced.')
            self.synced = True
            await bot.change_presence(activity = Presence.get_activity(), status = Presence.get_status())
        global owner
        owner = await bot.fetch_user(ownerID)
        cleanup.start()
        manlogger.info('Initialization completed...')
        clear()
        pt('READY')
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
                    await channel.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the translation setup.')
                return
        await guild.owner.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the translation setup.')
    
    @tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(Functions.translate(interaction, 'This comand is on cooldown.\nTime left: `')+Functions.seconds_to_minutes(error.retry_after)+'`.', ephemeral = True)
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
    

    def check_for_dbd(id, steamAPIkey):
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

    
    def unicode_unescape(s):
        return bytes(s, 'utf-8').decode('unicode_escape')


    def get_language_name(lang_code):
        try:
            return pycountry.languages.get(alpha_2=lang_code).name
        except:
            return lang_code


    def convert_time(timestamp):
        return(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp)))
    

    def convert_time_dateonly(timestamp):
        return(time.strftime('%Y-%m-%d', time.gmtime(timestamp)))
    

    def convert_number(number):
        return f"{int(number):,}"
    

    async def check_api_rate_limit(url):
        # Check the 429 status code and return 1 when this appearance
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    return 1
                else:
                    return await response.json()
    

    def check_if_removed(id):
        try:
            resp = r.get(f'{api_base}playerstats?steamid={id}')
            resp.raise_for_status()  # Throws an exception if the status code is not 200
            return 0
        except r.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                url = f'{alt_playerstats}{id}'
                try:
                    page = r.get(url).text
                    soup = BeautifulSoup(page, 'html.parser')
                    for i in soup.find_all('div', id='error'):
                        return i.text
                except Exception as e:
                    manlogger.warning(f'Error while parsing {url}: {e}')
                    return 1
                else:
                    manlogger.warning(f'SteamID {id} got removed from the leaderboard.')
                    return 1
            else:
                manlogger.warning(f'Unexpected response from API: {e}')
                return 1
        except Exception as e:
            manlogger.warning(f'Error while querying API: {e}')
            return 1


    async def create_support_invite(interaction: discord.Interaction):
        try:
            guild = bot.get_guild(int(support_id))
        except ValueError:
            return "Could not find support guild."
        channel: discord.TextChannel = guild.text_channels[0]
        try:
            invite: discord.Invite = await channel.create_invite(
                reason=f"Created invite for {interaction.user.name} from server {interaction.guild.name}",
                max_age=60,
                max_uses=1,
                unique=True
            )
            return invite.url
        except discord.Forbidden:
            return "I do not have permission to create an invite in that channel."
        except discord.HTTPException:
            return "There was an error creating the invite."
    

    def seconds_to_minutes(input_int):
        return(str(timedelta(seconds=input_int)))
    

    def translate(interaction, text):
        translator = Translator()
        role_names = [role.name for role in interaction.user.roles]
        for lang in languages:
            if lang in role_names:
                try:
                    return translator.translate(text, dest=lang).text
                except:
                    pass
        return text
    

    async def perk_load():
        char = await Functions.char_load()
        tb.clear()
        tb.field_names = ['Name', 'Category', 'Origin']
        if os.path.exists(buffer_folder + 'perk_info.json') and (time.time() - os.path.getmtime(buffer_folder + 'perk_info.json')) / 3600 < 4:
            with open(buffer_folder + 'perk_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)
        else:
            data = await Functions.check_api_rate_limit(api_base + 'perks')
            if data == 1:
                return 1
            with open(buffer_folder + 'perk_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)

        with open(buffer_folder + 'perks.txt', 'w', encoding='utf8') as f:
            for key in data.keys():
                origin = ''
                for i in char.keys():
                    if str(data[key]['character']) == str(i):
                        origin = char[i]['name']
                        break
                if data[key]['character'] is None:
                    origin = ''
                tb.add_row([data[key]['name'], str(data[key]['categories']).replace('[', '').replace('\'', '').replace(']', '').replace('None', ''), origin])
            tb.sortby = 'Name'
            f.write(str(tb))
        return data
    

    async def perk_send(data, perk, interaction, shrine=False, random=False):
        def length(data, index):
            try:
                length = len(data[key]['tunables'][index])
                if length == 1:
                    embed.add_field(name=str(index), value=data[key]['tunables'][index][0])
                elif length == 2:
                    embed.add_field(name=str(index), value=data[key]['tunables'][index][0])
                    embed.add_field(name='\u200b', value=data[key]['tunables'][index][1])
                elif length == 3:
                    embed.add_field(name=str(index), value=data[key]['tunables'][index][0])
                    embed.add_field(name='\u200b', value=data[key]['tunables'][index][1])
                    embed.add_field(name='\u200b', value=data[key]['tunables'][index][2])
            except:
                pass
            
        async def check():
            embed.set_thumbnail(url=bot_base + data[key]['image'])
            length_total = len(data[key]['tunables'])
            embed.add_field(name='\u200b', value='\u200b', inline=False)
            character = await Functions.char_load()
            for i in character.keys():
                if str(i) == str(data[key]['character']):
                    embed.set_author(name=character[i]['name'], icon_url=bot_base + character[i]['image'])
                    break
            if length_total == 1:
                length(data, 0)
            elif length_total == 2:
                length(data, 0)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                length(data, 1)
            elif length_total == 3:
                length(data, 0)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                length(data, 1)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                length(data, 2)
    
        if shrine:
            embed = discord.Embed(title="Perk-Description for '" + data[perk]['name'] + "'", description=Functions.translate(interaction, str(data[perk]['description']).replace('<br><br>', ' ').replace('<i>', '**').replace('</i>', '**').replace('<li>', '*').replace('</li>', '*').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ')).replace('.','. '), color=0xb19325)
            key = perk
            await check()
            return embed
        else:
            for key in data.keys():
                embed = discord.Embed(title="Perk-Description for '" + data[key]['name'] + "'", description=Functions.translate(interaction, str(data[key]['description']).replace('<br><br>', ' ').replace('<i>', '**').replace('</i>', '**').replace('<li>', '*').replace('</li>', '*').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ')).replace('.','. '), color=0xb19325)
                if data[key]['name'].lower() == perk.lower():
                    await check()
                    if random:
                        return embed
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
        return 1


    async def shrine_load():
        shrine_path = pathlib.Path(buffer_folder) / 'shrine_info.json'
        if shrine_path.is_file() and ((time.time() - shrine_path.stat().st_mtime) / 3600 < 4):
            # File already available and changed within the last 4 hours
            try:
                data = json.loads(shrine_path.read_text())
                return data
            except Exception as e:
                manlogger.warning(f"Error loading the JSON file: {e}")
                return 1
        else:
            # File must be updated
            data = await Functions.check_api_rate_limit(api_base+'shrine')
            if data == 1:
                return 1
            try:
                shrine_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                return data
            except Exception as e:
                manlogger.warning(f"Error when writing the JSON file: {e}")
                return None
            

    async def offerings_load() -> dict:
        tb.field_names = ['ID', 'Name', 'Role']
        if os.path.exists(buffer_folder+'offering_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'offering_info.json')) /3600 < 4):
            with open(buffer_folder+'offering_info.json', 'r', encoding='utf8') as f:
                data = json.load(f)  
            if not os.path.exists(buffer_folder+'offerings.txt') or ((time.time() - os.path.getmtime(buffer_folder+'offerings.txt')) /3600 > 4):
                with open(buffer_folder+'offerings.txt', 'w', encoding='utf8') as f2:
                    for key in data.keys():
                        role = data[key]['role']
                        if not role:
                            role = 'killer, survivor'
                        if data[key]['name'] == '' or data[key]['name'] is None:
                            tb.add_row([key, '', role])
                        else:
                            tb.add_row([key, data[key]['name'], role])
                    tb.sortby = 'ID'
                    f2.write(str(tb))
        else:
            data = await Functions.check_api_rate_limit(api_base+'offerings')
            if data == 1:
                return {}
            with open(buffer_folder+'offering_info.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'offerings.txt', 'w', encoding='utf8') as f2:
                for key in data.keys():
                    role = data[key]['role']
                    if not role:
                        role = 'killer, survivor'
                    if data[key]['name'] == '' or data[key]['name'] is None:
                        tb.add_row([key, '', role])
                    else:
                        tb.add_row([key, data[key]['name'], role])
                tb.sortby = 'ID'
                f2.write(str(tb))
        return data
            

    async def char_load():
        tb.field_names = ['ID', 'Name', 'Role']
        file_path = buffer_folder + 'character_info.json'
        table_file_path = buffer_folder + 'characters.txt'
        if os.path.exists(file_path) and ((time.time() - os.path.getmtime(file_path)) / 3600) <= 4:
            with open(file_path, 'r', encoding='utf8') as f:
                data = json.load(f)
        else:
            data = await Functions.check_api_rate_limit(api_base+'characters')
            if data == 1:
                return 1
            with open(file_path, 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
        with open(table_file_path, 'w', encoding='utf8') as f:
            for key in data:
                tb.add_row([data[key]['id'], data[key]['name'].replace('The ', ''), data[key]['role']])
            tb.sortby = 'Name'
            f.write(str(tb))
            tb.clear()
        return data
    

    async def dlc_load():
        if os.path.exists(buffer_folder+'dlc.json') and ((time.time() - os.path.getmtime(buffer_folder+'dlc.json')) / 3600) <= 4:
            with open(buffer_folder+'dlc.json', 'r', encoding='utf8') as f:
                return json.loads(f.read())
        else:
            data = await Functions.check_api_rate_limit(api_base+'dlc')
            if data == 1:
                return 1
            with open(buffer_folder+'dlc.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(buffer_folder+'dlc.json', 'r', encoding='utf8') as f:
                return json.loads(f.read())


    async def item_load():
        tb.clear()
        tb.field_names = ['ID', 'Name', 'Type', 'Rarity']
    
        items_file_path = buffer_folder+'items.json'
        items_text_path = buffer_folder+'items.txt'
    
        if os.path.exists(items_file_path) and ((time.time() - os.path.getmtime(items_file_path)) / 3600) <= 4:
            with open(items_file_path, 'r', encoding='utf8') as f:
                f = json.load(f)
            with open(items_text_path, 'w', encoding='utf8') as f2:
                for key, item in f.items():
                    item_type = item.get('item_type', '')
                    tb.add_row([key, str(item['name']), str(item_type), str(item['rarity'])])
                tb.sortby = 'Type'
                f2.write(str(tb))
                tb.clear()
            return f
        else:
            data = await Functions.check_api_rate_limit(api_base+'items?role=survivor')
            if data == 1:
                return 1
            with open(items_file_path, 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            with open(items_file_path, 'r', encoding='utf8') as f:
                f = json.load(f)
            with open(items_text_path, 'w', encoding='utf8') as f2:
                for key, item in f.items():
                    item_type = item.get('item_type', '')
                    tb.add_row([key, str(item['name']), str(item_type), str(item['rarity'])])
                tb.sortby = 'Type'
                f2.write(str(tb))
                tb.clear()
            return f


    async def addon_load():
        char = await Functions.char_load()
        if char == 1:
            return 1
        
        tb.clear()
        tb.field_names = ['Name', 'Role', 'Origin']
        
        buffer_info_path = buffer_folder + 'addon_info.json'
        buffer_addons_path = buffer_folder + 'addons.txt'
        
        update_buffer_info = not os.path.exists(buffer_info_path) or ((time.time() - os.path.getmtime(buffer_info_path)) / 3600 > 4)
        update_buffer_addons = not os.path.exists(buffer_addons_path) or ((time.time() - os.path.getmtime(buffer_addons_path)) / 3600 > 4)
    
        if not update_buffer_info:
            with open(buffer_info_path, 'r', encoding='utf8') as f:
                data = json.load(f)
        else:
            data = await Functions.check_api_rate_limit(api_base + 'addons')
            if data == 1:
                return 1
            with open(buffer_info_path, 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
                
        for key in data.keys():
            addon = data[key]
            parent_items = addon.get('parents', [])
            parent_item_names = [str(parent).replace('[', '').replace('\'', '').replace(']', '') for parent in parent_items]
    
            for i in char.keys():
                item = char[i]['item']
                item_name = str(item).replace('[', '').replace('\'', '').replace(']', '')
    
                if item_name in parent_item_names:
                    tb.add_row([addon['name'], addon['role'], str(char[i]['name']).replace('The', '')])
                    break
                elif not parent_items:
                    tb.add_row([addon['name'], addon['role'], str(addon['item_type']).replace('None', '')])
                    break
        
        tb.sortby = 'Origin'
        if update_buffer_addons:
            with open(buffer_addons_path, 'w', encoding='utf8') as f:
                f.write(str(tb))
                
        return data


    async def addon_send(data, addon, interaction: discord.Interaction, random: bool = False):
        for i in data.keys():
            if data[i]['name'] == addon:
                embed = discord.Embed(title=data[i]['name'], description=str(data[i]['description']).replace('<br>', '').replace('<b>', '').replace('</b>', '').replace('.', '. '), color=0x0400ff)
                embed.set_thumbnail(url=bot_base+data[i]['image'])
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                embed.add_field(name='Rarity', value=data[i]['rarity'], inline=True)
                embed.add_field(name='Role', value=data[i]['role'], inline=True)
                if data[i]['item_type'] is None:
                    char = await Functions.char_load()
                    for key in char.keys():
                        if str(data[i]['parents']).replace('[', '').replace('\'', '').replace(']', '') == str(char[key]['item']).replace('[', '').replace('\'', '').replace(']', ''):
                            embed.add_field(name='Origin', value=char[key]['name'], inline=True)
                            break
                else:
                    embed.add_field(name='Origin', value=data[i]['item_type'], inline=True)
                if random:
                    return embed
                else:
                    await interaction.followup.send(embed=embed, ephemeral = True)
                

    async def offering_send(interaction, data, name, loadout: bool = False):
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
                if loadout:
                    return embed
                await interaction.followup.send(embed = embed, ephemeral = True)
                return
        await interaction.followup.send(Functions.translate(interaction, "This offering doesn't exist."), ephemeral = True)
        

    async def item_send(interaction, data, name, loadout: bool = False):
        for i in data.keys():
            if str(data[i]['name']).lower() == name.lower() or str(i).lower() == name.lower():
                if data[i]['name'] is None:
                    title = i
                else:
                    title = data[i]['name']
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
                if loadout == True:
                    return embed, data[i]['item_type']
                await interaction.followup.send(embed = embed, ephemeral = True)
                

    async def char_send(interaction, data, char, dlc_data, loadout: bool = False):
        for key in data.keys():
            if str(data[key]['id']).lower().replace('the ', '') == char.lower().replace('the ', '') or str(data[key]['name']).lower().replace('the ', '') == char.lower().replace('the ', ''):
                embed = discord.Embed(title=Functions.translate(interaction, "Character Info"), description=str(data[key]['name']), color=0xb19325)
                embed.set_thumbnail(url=bot_base+str(data[key]['image']))
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
                if loadout:
                    return embed
                if len(data[key]['story']) > 4096:
                    story = buffer_folder+'character_story.txt'
                    if os.path.exists(story):
                        story = buffer_folder+'character_story'+str(random.randrange(1, 999))+'.txt'
                    with open(story, 'w', encoding='utf8') as f:
                        f.write(Functions.translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.')).replace('.', '. '))
                    await interaction.followup.send(embed=embed, ephemeral = True)
                    await interaction.followup.send(f"Story of {data[key]['name']}", file=discord.File(r''+story), ephemeral = True)
                    os.remove(story)
                    return
                elif 1024 < len(data[key]['story']) < 4096:
                    embed2 = discord.Embed(title='Story', description=Functions.translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('&nbsp;', ' ')).replace('.', '. '), color=0xb19325)
                    await interaction.followup.send(embeds=[embed, embed2], ephemeral = True)
                    return
                else:
                    embed.add_field(name="Story", value=Functions.translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('<br>', '').replace('&nbsp;', ' ')).replace('.', '. '), inline=False)
                await interaction.followup.send(embed=embed, ephemeral = True)
                return
        embed = discord.Embed(title=Functions.translate(interaction, "Character Info"), description=Functions.translate(interaction, f"I couldn't find a character named {char}."), color=0xb19325)
        await interaction.followup.send(embed=embed, ephemeral = True)


    async def get_item_type(item, data):
        for key, value in data.items():
            if item.lower() == key.lower() or item.lower() == value["name"].lower():
                return value["item_type"]
        return 1


    async def find_killer_item(killer, chars):
        killer_data = None
        for char_data in chars.values():
            if str(char_data['id']).lower().replace('the', '').strip() == str(killer).lower().replace('the', '').strip() or str(char_data['name']).lower().replace('the', '').strip() == str(killer).lower().replace('the', '').strip():
                killer_data = char_data
                break
        if killer_data is None or 'item' not in killer_data:
            return 1
        return killer_data['item']


    async def find_killer_by_item(item_name: str, killers_data) -> str:
        for killer in killers_data.values():
            if killer.get('item') == item_name:
                return killer['id']
        return 1

                
        
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
        if not interaction.guild:
            await interaction.followup.send("This command can only be used in a server.")
            return
    
        resp = r.get(api_base + 'events')
        data = resp.json()
        current_event = None
        upcoming_event = None
    
        for event in data:
            start_time = int(event['start'])
            end_time = int(event['end'])
            now = int(time.time())
            if start_time <= now <= end_time:
                current_event = event
                break
            elif now < start_time and (upcoming_event is None or upcoming_event['start'] > start_time):
                upcoming_event = event
    
        if current_event is not None:
            embed = discord.Embed(title="Event", description=Functions.translate(interaction, "Currently there is a event in DeadByDaylight.")+" <a:hyperWOW:1032389458319913023>", color=0x922f2f)
            embed.add_field(name=Functions.translate(interaction, "Name"), value=current_event['name'], inline=True)
            embed.add_field(name=Functions.translate(interaction, "Bloodpoint Multiplier"), value=current_event['multiplier'], inline=False)
            embed.add_field(name=Functions.translate(interaction, "Beginning"), value=str(Functions.convert_time(current_event['start'])+' UTC'), inline=True)
            embed.add_field(name=Functions.translate(interaction, "Ending"), value=str(Functions.convert_time(current_event['end'])+' UTC'), inline=True)
            await interaction.followup.send(embed=embed)
        elif upcoming_event is not None:
            embed = discord.Embed(title="Event", description=Functions.translate(interaction, "There is a upcoming event in DeadByDaylight.")+" <a:SmugDance:1032349729167790090>", color=0x922f2f)
            embed.add_field(name="Name", value=upcoming_event['name'], inline=True)
            embed.add_field(name="Bloodpoint Multiplier", value=upcoming_event['multiplier'], inline=False)
            embed.add_field(name="Beginning", value=str(Functions.convert_time(upcoming_event['start'])+' UTC'), inline=True)
            embed.add_field(name="Ending", value=str(Functions.convert_time(upcoming_event['end'])+' UTC'), inline=True)
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(title="Event", description=Functions.translate(interaction, "Currently there is no event in DeadByDaylight.")+" <:pepe_sad:1032389746284056646>", color=0x922f2f)
            await interaction.followup.send(embed=embed)
           

    async def playerstats(interaction: discord.Interaction, steamid):
        if interaction.guild is None:
            await interaction.response.send_message('This command can only be used inside a server.')
            return
        check = Functions.check_for_dbd(steamid, steamAPIkey)
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
            clean_filename = os.path.basename(f'player_stats_{check[1]}.json')
            file_path = os.path.join(stats_folder, clean_filename)
            if removed == 1:
                embed1 = discord.Embed(title="Statistics", url=alt_playerstats+check[1], description=Functions.translate(interaction, "It looks like this profile has been banned from displaying on our leaderboard.\nThis probably happened because achievements or statistics were manipulated.\nI can therefore not display any information in an embed.\nIf you still want to see the full statistics, please click on the link.").replace('.','. '), color=0xb19325)
                await interaction.followup.send(embed=embed1)
                return
            elif removed != 0:
                await interaction.followup.send(content = removed)
                return
            if os.path.exists(f'{stats_folder}player_stats_{check[1]}.json') and ((time.time() - os.path.getmtime(f'{stats_folder}player_stats_{check[1]}.json')) / 3600) <= 4:
                with open(file_path, 'r', encoding='utf8') as f:
                    player_stats = json.load(f)
            else:
                data = await Functions.check_api_rate_limit(f'{api_base}playerstats?steamid={check[1]}')
                if data != 1:
                    with open(file_path, 'w', encoding='utf8') as f:
                        json.dump(r.get(f'{api_base}playerstats?steamid={check[1]}').json(), f, indent=2)
                else:
                    await interaction.followup.send(Functions.translate(interaction, "The stats got loaded in the last 4h but I don't have a local copy. Try again in ~3-4h.").replace('.','. '), ephemeral=True)
                    return
                with open(file_path, 'r', encoding='utf8') as f:
                    player_stats = json.load(f)
            steam_data = await Functions.check_api_rate_limit(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steamAPIkey}&steamids={check[1]}')
            if steam_data == 1 or player_stats == 1:
                await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later. (This error can also appear if the same profile got querried multiple times in a 4h window.)").replace('.','. '), ephemeral=True)
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
            #Set Static Infos
            embeds = [embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed8, embed9, embed10]
            footer = Functions.translate(interaction, "Stats are updated every ~4h. | Last update: ").replace('.|','. | ')+str(Functions.convert_time(int(player_stats['updated_at'])))+" UTC"

            for embed in embeds:
                embed.set_thumbnail(url=avatar)
                embed.set_footer(text=footer)

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
        data = await Functions.char_load()
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
            await Functions.char_send(interaction, data, char, dlc_data)
            return
             
        
    async def dlc(interaction: discord.Interaction, name: str = ''):
        await interaction.response.defer(thinking=True)
        data = await Functions.dlc_load()
        if not name:
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
    
        # Check if the command is being used in a server
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.")
            return
    
        # Load item data
        data = await Functions.item_load()
        if data == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the item data."))
            return
    
        # Send list of all items if no name is specified
        if name == '':
            await interaction.followup.send(content='Here is a list of all items. You can use the command again with one of the items to get more info about it.', file=discord.File(f'{buffer_folder}items.txt'))
            return
    
        # Send info about the specified item
        await Functions.item_send(interaction, data, name)
        return
            

    async def map(interaction: discord.Interaction, name: str = ''):
        await interaction.response.defer(thinking=True)
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        maps_info_file = os.path.join(buffer_folder, 'maps_info.json')
        maps_file = os.path.join(buffer_folder, 'maps.txt')
        if os.path.isfile(maps_info_file) and ((time.time() - os.path.getmtime(maps_info_file)) / 3600) >= 4 or not os.path.isfile(maps_info_file):
            data = await Functions.check_api_rate_limit(api_base+'maps')
            if data == 1:
                await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
            with open(maps_info_file, 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
        if not name and os.path.isfile(maps_file) and ((time.time() - os.path.getmtime(maps_file)) / 3600) <= 4:
            await interaction.followup.send(file=discord.File(maps_file))
            return
        elif not name:
            with open(maps_info_file, 'r', encoding='utf8') as f:
                map_data = json.load(f)
            with open(maps_file, 'w', encoding='utf8') as f:
                for key, value in map_data.items():
                    if key == 'Swp_Mound':
                        continue
                    f.write(f"Name: {value['name']}\n")
            await interaction.followup.send(file=discord.File(maps_file))
        else:
            with open(maps_info_file, 'r', encoding='utf8') as f:
                map_data = json.load(f)
            for key, value in map_data.items():
                if value['name'] == 'Swp_Mound':
                    continue
                if value['name'].lower() == name.lower():
                    embed = discord.Embed(title=f"Map description for '{value['name']}'", description=Functions.translate(interaction, str(value['description']).replace('<br><br>', ' ')).replace('.','. '), color=0xb19325)
                    embed.set_thumbnail(url=f"{map_portraits}{key}.png")
                    await interaction.followup.send(embed=embed)
                    return
            await interaction.followup.send(f"No map with name **{name}** found.")


    async def offering(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.")
            return
        data = await Functions.offerings_load()
        if data == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the perk data."), ephemeral=True)
            return
        if not name:
            with open(buffer_folder+'offerings.txt', 'rb') as f:
                await interaction.followup.send(content='Here is a list of all offerings. You can use the command again with one of the offerings to get more info about it.', file=discord.File(f))
            return
        await Functions.offering_send(interaction, data, name)

            
    async def perk(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        data = await Functions.perk_load()
        if data == 1:
            await interaction.followup.send("Error while loading the perk data.")
            return
        if not name:
            await interaction.followup.send(content='Here are the perks:', file=discord.File(r''+buffer_folder+'perks.txt'))
            return
        else:
            test = await Functions.perk_send(data, name, interaction)
            if test == 1:
                await interaction.followup.send(f"There is no perk named {name}.", ephemeral=True)
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
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the shrine data."))
        perks = await Functions.perk_load()
        if perks == 1:
            await interaction.followup.send(Functions.translate(interaction, "Error while loading the perk data."))
            return
        embeds = []
        for shrine in data['perks']:
            for perk in perks.keys():
                if perk == shrine['id']:
                    shrine_embed = await Functions.perk_send(perks, perk, interaction, True)
                    shrine_embed.set_footer(text=f"Bloodpoints: {Functions.convert_number(shrine['bloodpoints'])} | Shards: {Functions.convert_number(shrine['shards'])}")
                    embeds.append(shrine_embed)               
        await interaction.followup.send(content = 'This is the current shrine.\nIt started at <t:'+str(data['start'])+'> and will last until <t:'+str(data['end'])+'>.\nUpdates every 4h.', embeds=embeds)


    async def version(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.")
        else:
            data = await Functions.check_api_rate_limit(api_base+'versions')
            if data == 1:
                await interaction.followup.send(Functions.translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '), ephemeral=True)
                return
            embed1 = discord.Embed(title='DB Version (1/2)', color=0x42a32e)
            embed1.add_field(name=Functions.translate(interaction, 'Name'), value='\u200b', inline=True)
            embed1.add_field(name=Functions.translate(interaction, 'Version'), value='\u200b', inline=True)
            embed1.add_field(name=Functions.translate(interaction, 'Last Update'), value='\u200b', inline=True)
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
                    embed1.add_field(name='\u200b', value=key.capitalize(), inline=True)
                    embed1.add_field(name='\u200b', value=data[key]['version'], inline=True)
                    embed1.add_field(name='\u200b', value=str(Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
                if i >= 6:
                    embed2.add_field(name='\u200b', value=key.capitalize(), inline=True)
                    embed2.add_field(name='\u200b', value=data[key]['version'], inline=True)
                    embed2.add_field(name='\u200b', value=str(Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
            await interaction.followup.send(embeds=[embed1, embed2])

        
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
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50'}
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
            await interaction.followup.send("This command can only be used in a server.")
            return
        dbd_check = Functions.check_for_dbd(steamid, steamAPIkey)
        if dbd_check[0] == 1:
            await interaction.followup.send(Functions.translate(interaction, 'The SteamID64 has to be 17 chars long and only containing numbers.'))   
        elif dbd_check[0] == 2:
            await interaction.followup.send(Functions.translate(interaction, 'This SteamID64 is NOT in use.'))
        elif dbd_check[0] == 3:
            await interaction.followup.send(Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking").replace('.','. ')+"\n[here](https://steamcommunity.com/profiles/"+id+"/edit/settings).")
        elif dbd_check[0] == 4:
            await interaction.followup.send(Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look").replace('.','. ')+" [here](https://www.g2a.com/n/dbdstats).")
        elif dbd_check[0] == 5:
            embed1=discord.Embed(title="Fatal Error", description=Functions.translate(interaction, "It looks like there was an error querying the SteamAPI (probably a rate limit).\nPlease join our").replace('.','. ')+" [Support-Server]("+str(await Functions.create_support_invite(interaction))+Functions.translate(interaction, ") and create a ticket to tell us about this."), color=0xff0000)
            embed1.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.response.send_message(embed=embed1)
        elif dbd_check[0] == 0:
            resp = r.get(f'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={steamAPIkey}&steamid={dbd_check[1]}&appid=381210')
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
    

    async def addon(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        data = await Functions.addon_load()
        if data == 1:
            await interaction.followup.send("Error while loading the addon data.")
            return
        else:
            if name == '':
                await interaction.followup.send(content = 'Here are the addons:' , file=discord.File(r''+buffer_folder+'addons.txt'))
            else:
                test = await Functions.addon_send(data, name, interaction)
                if test == 1:
                    await interaction.followup.send(f"There is no addon named {name}.")
                return


    async def twitch_info(interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild is None:
            interaction.followup.send("This command can only be used in a server.")
            return
        embeds = []
        game_id = twitch_api.get_game_id("Dead by Daylight")
        stats = twitch_api.get_category_stats(game_id)
        top = twitch_api.get_top_streamers(game_id)
        image = twitch_api.get_category_image(game_id)
        embed = discord.Embed(title="Twitch Info", url="https://www.twitch.tv/directory/game/Dead%20by%20Daylight", description="Statistics", color=0xffb8ff)
        embed.set_thumbnail(url=image)
        embed.add_field(name="Total Viewers", value=Functions.convert_number(stats['viewer_count']), inline=True)
        embed.add_field(name="Total Streams", value=Functions.convert_number(stats['stream_count']), inline=True)
        embed.add_field(name="\u00D8 Viewer/Stream", value=Functions.convert_number(stats['average_viewer_count']), inline=True)
        embed.add_field(name="Current Rank", value=Functions.convert_number(stats['category_rank']), inline=False)
        embeds.append(embed)
        for streamer in top.values():
            embed = discord.Embed(title=streamer['streamer'], description=Functions.unicode_unescape(streamer['title']), color=0xffb8ff)
            embed.set_thumbnail(url=streamer['thumbnail'])
            embed.add_field(name="Viewer", value=Functions.convert_number(streamer['viewer_count']), inline=True)
            embed.add_field(name="Follower", value=Functions.convert_number(streamer['follower_count']), inline=True)
            embed.add_field(name="\u200b", value=f"[Stream]({streamer['link']})", inline=True)
            embed.add_field(name="Language", value=Functions.get_language_name(streamer['language']), inline=True)
            embed.set_footer(text=f"Started at: {streamer['started_at']}")
            embeds.append(embed)
        await interaction.followup.send(embeds=embeds)


 
#Random
class Random():
    async def perk(interaction: discord.Interaction, amount, role, loadout: bool = False):
        if not loadout:
            await interaction.response.send_message(f'Selecting {amount} perks for {role}...\nThis will take a while. Especially when the translation is activated.', ephemeral=True)
        perks = await Functions.perk_load()
        if perks == 1:
            await interaction.followup.send("Error while loading the perk data.")
            return
        keys = set(perks.keys())
        selected_keys = set()
        embeds = []
        while len(embeds) < amount and keys - selected_keys:
            key = random.choice(list(keys - selected_keys))
            entry = perks[key]
            if entry['role'] == role:
                embed = await Functions.perk_send(perks, entry['name'], interaction, False, True)
                embeds.append(embed)
            selected_keys.add(key)
        if not embeds:
            await interaction.followup.send(f"No perks found for {role}.", ephemeral=True)
            return
        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral=True)

         
    async def offering(interaction: discord.Interaction, role, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking = True)
        offerings = await Functions.offerings_load()
        if offerings == 1:
            await interaction.followup.send("Error while loading the offering data.", ephemeral = True)
            return
        else:
            keys = list(offerings.keys())
            while True:
                key = random.choice(keys)
                entry = offerings[key]
                if entry['retired'] == 1:
                    continue
                if entry['role'] == role or entry['role'] is None:
                    if loadout:
                        return await Functions.offering_send(interaction, offerings, entry['name'], True)
                    await Functions.offering_send(interaction, offerings, entry['name'])
                    return
                else:
                    continue
            
    
    async def item(interaction: discord.Interaction, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking = True)
        items = await Functions.item_load()
        if items == 1:
            await interaction.followup.send("Error while loading the item data.")
            return
        keys = list(items.keys())
        while True:
            key = random.choice(keys)
            entry = items[key]
            if entry['bloodweb'] == 0:
                continue
            if loadout:
                temp = await Functions.item_send(interaction, items, entry['name'], True)
                return temp[0], temp[1]
            await Functions.item_send(interaction, items, entry['name'])
            return

                
    async def char(interaction: discord.Interaction, role, loadout: bool = False):
        dlc_data = await Functions.dlc_load()
        if dlc_data == 1:
            await interaction.followup.send("Error while loading the dlc data.", ephemeral = True)
            return
        chars = await Functions.char_load()
        if chars == 1:
            await interaction.followup.send("Error while loading the char data.", ephemeral = True)
            return
        else:
            keys = list(chars.keys())
            while True:
                key = random.choice(keys)
                entry = chars[key]
                if entry['role'] == role:
                    if loadout == True:
                        return await Functions.char_send(interaction, chars, entry['name'], dlc_data, True), entry['id'], entry['role']
                    await Functions.char_send(interaction, chars, entry['name'], dlc_data)
                    return
                else:
                    continue
            
                
    async def addon(interaction: discord.Interaction, parent, loadout: bool = False):
        if not loadout:
            await interaction.response.defer()
        item = await Functions.item_load()
        if item == 1:
            await interaction.followup.send("Error while loading the item data.", ephemeral = True)
            return
        addons = await Functions.addon_load()
        if addons == 1:
            await interaction.followup.send("Error while loading the addon data.", ephemeral = True)
            return
        else:
            parent_type = await Functions.get_item_type(parent, item)
            keys = list(addons.keys())
            selected_keys = set()
            embeds = []
            i = 0
            while i < 2:
                key = random.choice(keys)
                entry = addons[key]
                if entry['item_type'] is None:
                    continue
                if entry['item_type'] == parent_type and key not in selected_keys:
                    embed = await Functions.addon_send(addons, entry['name'], interaction, True)
                    embeds.append(embed)
                    i += 1
                    selected_keys.add(key)
                else:
                    continue
            if loadout:
                return embeds
            await interaction.followup.send(embeds=embeds, ephemeral = True)
            return
        
        
    async def adfk(interaction: discord.Interaction, killer, loadout: bool = False):
        if not loadout:
            await interaction.response.defer()
        addons = await Functions.addon_load()
        if addons == 1:
            await interaction.followup.send("Error while loading the addon data.", ephemeral = True)
            return
        chars = await Functions.char_load()
        if chars == 1:
            await interaction.followup.send("Error while loading the char data.", ephemeral = True)
            return
        killer_item = await Functions.find_killer_item(killer, chars)
        if killer_item == 1:
            await interaction.followup.send(f"There is no killer named '{killer}'.", ephemeral = True)
            return
        keys = list(addons.keys())
        selected_keys = set()
        embeds = []
        i = 0
        while i < 2:
            key = random.choice(keys)
            entry = addons[key]
            if killer_item in entry['parents'] and key not in selected_keys:
                embed = await Functions.addon_send(addons, entry['name'], interaction, True)
                embeds.append(embed)
                i += 1
                selected_keys.add(key)
            else:
                continue
        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral = True)
        return


    async def loadout(interaction: discord.Interaction, role):
        await interaction.response.defer(thinking = True, ephemeral = True)
        chars = await Functions.char_load()
        if chars == 1:
            await interaction.followup.send("Error while loading the char data.")
            return
        embeds = []
        char = await Random.char(interaction, role, True)
        embeds.append(char[0])
        
        if char[2] == 'survivor':
            item = await Random.item(interaction, True)
            embeds.append(item[0])
            addon = await Random.addon(interaction, item[1], True)
            embeds.extend(addon)
        elif char[2] == 'killer':
            killer_item = await Functions.find_killer_item(char[1], chars)
            killer = await Functions.find_killer_by_item(killer_item, chars)
            addon = await Random.adfk(interaction, killer, True)
            embeds.extend(addon)
        
        perks = await Random.perk(interaction, 4, char[2], True)
        embeds.extend(perks)
        offering = await Random.offering(interaction, char[2],True)
        embeds.append(offering)

        await interaction.followup.send(embeds=embeds)
             
        
            
##Owner Commands (Can only be used by the BotOwner.)
#Shutdown
if owner_available:
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
if owner_available:
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
if owner_available:        
    @tree.command(name = 'clear_buffer', description = 'Delete all files in buffer and stats.')
    async def self(interaction: discord.Interaction):
        files_removed = 0
        for filename in os.listdir(buffer_folder):
            if os.path.isfile(os.path.join(buffer_folder, filename)):
                os.remove(os.path.join(buffer_folder, filename))
                files_removed += 1
        for filename in os.listdir(stats_folder):
            if os.path.isfile(os.path.join(stats_folder, filename)):
                os.remove(os.path.join(stats_folder, filename))
                files_removed += 1
        await interaction.response.send_message(content=Functions.translate(interaction, f'{files_removed} files were removed.'), ephemeral=True)


#Change Activity
if owner_available:
    @tree.command(name = 'activity', description = 'Change my activity.')
    @discord.app_commands.describe(type='The type of Activity you want to set.', title='What you want the bot to play, stream, etc...', url='Url of the stream. Only used if activity set to \'streaming\'.')
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name='Competing', value='Competing'),
        discord.app_commands.Choice(name='Listening', value='Listening'),
        discord.app_commands.Choice(name='Playing', value='Playing'),
        discord.app_commands.Choice(name='Streaming', value='Streaming'),
        discord.app_commands.Choice(name='Watching', value='Watching')
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
if owner_available:
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
if owner_available:
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
if support_available:
    @tree.command(name = 'support', description = 'Get invite to our support server.')
    @discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
    async def self(interaction: discord.Interaction):
        if str(interaction.guild.id) != support_id:
            await interaction.response.send_message(await Functions.create_support_invite(interaction), ephemeral = True)
        else:
            await interaction.response.send_message(Functions.translate(interaction, 'You are already in our support server!'), ephemeral = True)


#Setup
@tree.command(name = 'setup_help', description = 'Get help with translation setup.')
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_guild = True)
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
    discord.app_commands.Choice(name = 'Addons', value = 'addon'),
    discord.app_commands.Choice(name = 'Characters', value = 'char'),
    discord.app_commands.Choice(name = 'DLCs', value = 'dlc'),
    discord.app_commands.Choice(name = 'Events', value = 'event'),
    discord.app_commands.Choice(name = 'Items', value = 'item'),
    discord.app_commands.Choice(name = 'Killswitch', value = 'killswitch'),
    discord.app_commands.Choice(name = 'Legacy check', value = 'legacy'),
    discord.app_commands.Choice(name = 'Maps', value = 'map'),
    discord.app_commands.Choice(name = 'Offerings', value = 'offering'),
    discord.app_commands.Choice(name = 'Perks', value = 'perk'),
    discord.app_commands.Choice(name = 'Playercount', value = 'player'),
    discord.app_commands.Choice(name = 'Playerstats', value = 'stats'),
    discord.app_commands.Choice(name = 'Rankreset', value = 'reset'),
    discord.app_commands.Choice(name = 'Shrine', value = 'shrine'),
    discord.app_commands.Choice(name = 'Twitch', value = 'twitch'),
    discord.app_commands.Choice(name = 'Versions', value = 'version')
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
                await Info.character(interaction, char = self.answer.value.lower().replace('the', '').strip())
        await interaction.response.send_modal(Input())
    
    elif category == 'stats':
        class Input(discord.ui.Modal, title = 'Enter SteamID64. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'ID64 or vanity(url) you want stats for.', style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.playerstats(interaction, steamid = self.answer.value.strip())
        await interaction.response.send_modal(Input())  
    
    elif category == 'dlc':
        class Input(discord.ui.Modal, title = 'Enter DLC. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'DLC you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.dlc(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'event':
        await Info.event(interaction)

    elif category == 'item':
        class Input(discord.ui.Modal, title = 'Enter Item. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Item you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.item(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'map':
        class Input(discord.ui.Modal, title = 'Enter Map. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Map you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.map(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'offering':
        class Input(discord.ui.Modal, title = 'Enter Offering. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Offering you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.offering(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'perk':
        class Input(discord.ui.Modal, title = 'Enter Perk. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Perk you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
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
                await Info.legacycheck(interaction, steamid = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'addon':
        class Input(discord.ui.Modal, title = 'Enter Addon. Timeout in 15 seconds.'):
            self.timeout = 15
            answer = discord.ui.TextInput(label = 'Addon you want infos. Empty for list.', style = discord.TextStyle.short, required = False)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.addon(interaction, name = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'twitch':
        await Info.twitch_info(interaction)


#Randomize           
@tree.command(name = 'random', description = 'Get a random perk, offering, map, item, char or full loadout.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
@discord.app_commands.describe(category = 'What do you want to randomize?')
@discord.app_commands.choices(category = [
    discord.app_commands.Choice(name = 'Addon', value = 'addon'),
    discord.app_commands.Choice(name = 'Addon for Killer', value = 'adfk'),
    discord.app_commands.Choice(name = 'Char', value = 'char'),
    discord.app_commands.Choice(name = 'Item', value = 'item'),
    discord.app_commands.Choice(name = 'Loadout', value = 'loadout'),
    discord.app_commands.Choice(name = 'Offering', value = 'offering'),
    discord.app_commands.Choice(name = 'Perk', value = 'perk')
    ])
async def randomize(interaction: discord.Interaction, category: str):
    if interaction.guild is None:
        await interaction.response.send_message(content = 'You must use this command in a server.', ephemeral = True)
        return

    if category == 'perk':
        class Input(discord.ui.Modal, title='How many perks? Timeout in 30 seconds.'):
            timeout = 30
            answer = discord.ui.TextInput(label='Amount of perks.', style=discord.TextStyle.short, placeholder='1 - 4', min_length=1, max_length=1, required=True)
            role = discord.ui.TextInput(label='Role', style=discord.TextStyle.short, placeholder='Survivor or Killer', min_length=6, max_length=8, required=True)
    
            async def on_submit(self, interaction: discord.Interaction):
                x = self.answer.value
                y = self.role.value.lower()
    
                if not x.isdigit():
                    await interaction.response.send_message(content='Invalid input: the amount of perks must be a number.', ephemeral=True)
                    return
                
                x = int(x)
                if x < 1 or x > 4:
                    await interaction.response.send_message(content='Invalid input: the amount of perks must be between 1 and 4.', ephemeral=True)
                    return
    
                if y != 'survivor' and y != 'killer':
                    await interaction.response.send_message(content='Invalid input: the role must be either Survivor or Killer.', ephemeral=True)
                    return
                
                await Random.perk(interaction, x, y)
                
        await interaction.response.send_modal(Input())
         
    elif category == 'offering':
        class Input(discord.ui.Modal, title='Offering for whom? Timeout in 30 seconds.'):
            timeout = 30
            role = discord.ui.TextInput(label='Role', style=discord.TextStyle.short, placeholder='Survivor or Killer', min_length=6, max_length=8, required=True)

            async def on_submit(self, interaction: discord.Interaction):
                y = self.role.value.lower()
    
                if y != 'survivor' and y != 'killer':
                    await interaction.response.send_message(content='Invalid input: the role must be either Survivor or Killer.', ephemeral=True)
                    return
                
                await Random.offering(interaction, y)

        await interaction.response.send_modal(Input())        
        
    elif category == 'item':
        await Random.item(interaction)
        
    elif category == 'char':
        class Input(discord.ui.Modal, title='Char for whom? Timeout in 30 seconds.'):
            timeout = 30
            role = discord.ui.TextInput(label='Role', style=discord.TextStyle.short, placeholder='Survivor or Killer', min_length=6, max_length=8, required=True)

            async def on_submit(self, interaction: discord.Interaction):
                role = self.role.value.lower().strip()
    
                if role != 'survivor' and role != 'killer':
                    await interaction.response.send_message(content='Invalid input: the role must be either Survivor or Killer.', ephemeral=True)
                    return
                
                await Random.char(interaction, role)
                
        await interaction.response.send_modal(Input())
        
    elif category == 'addon':
        class Input(discord.ui.Modal, title = 'Enter Addon. Timeout in 30 seconds.'):
            self.timeout = 30
            answer = discord.ui.TextInput(label = 'Item you want Addons for.', style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                await Random.addon(interaction, self.answer.value.strip())
        await interaction.response.send_modal(Input())        

    elif category == 'adfk':
        class Input(discord.ui.Modal, title = 'Enter Killer. Timeout in 30 seconds.'):
            self.timeout = 30
            answer = discord.ui.TextInput(label = 'Killer you want Addons for.', max_length = 20, style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                await Random.adfk(interaction, self.answer.value.lower().replace('the', '').strip())
        await interaction.response.send_modal(Input())
      
    elif category == 'loadout':
        class Input(discord.ui.Modal, title='Loadout for whom? Timeout in 30 seconds.'):
            timeout = 30
            role = discord.ui.TextInput(label='Role', style=discord.TextStyle.short, placeholder='Survivor or Killer', min_length=6, max_length=8, required=True)

            async def on_submit(self, interaction: discord.Interaction):
                role = self.role.value.lower().strip()
    
                if role != 'survivor' and role != 'killer':
                    await interaction.response.send_message(content='Invalid input: the role must be either Survivor or Killer.', ephemeral=True)
                    return
                
                await Random.loadout(interaction, role)
                
        await interaction.response.send_modal(Input())

    else:
        await interaction.response.send_message('Invalid category.', ephemeral = True)
            
    
        
    



                  


bot.run(TOKEN, log_handler=None)
