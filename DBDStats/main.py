#Import
print('Loading...')
import aiohttp
import asyncio
import discord
import json
import jsonschema
import logging
import logging.handlers
import math
import os
import platform
import psutil
import pycountry
import pymongo
import pymongo.errors as mongoerr
import pytz
import random
import re
import sentry_sdk
import socket
import sqlite3
import sys
import time
import traceback
import zlib
from aiohttp import web
from bs4 import BeautifulSoup
from CustomModules.app_translation import Translator as CustomTranslator
from CustomModules.libretrans import LibreTranslateAPI
from CustomModules.twitch import TwitchAPI
from CustomModules import killswitch
from CustomModules import patchnotes
from CustomModules import steamcharts
from datetime import timedelta, datetime
from dotenv import load_dotenv
from prettytable import PrettyTable
from typing import Any, List, Literal, Optional
from urllib.parse import urlparse
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile



#Set vars
app_folder_name = 'DBDStats'
api_base = 'https://dbd.tricky.lol/api/' # For production
#api_base = 'http://localhost:5000/' # For testing
perks_base = 'https://dbd.tricky.lol/dbdassets/perks/'
bot_base = 'https://cdn.bloodygang.com/botfiles/DBDStats/'
map_portraits = f'{bot_base}mapportraits/'
alt_playerstats = 'https://dbd.tricky.lol/playerstats/'
steamStore = 'https://store.steampowered.com/app/'
bot_version = "1.8.0"
languages = ['Arabic', 'Azerbaijani', 'Catalan', 'Chinese', 'Czech', 'Danish', 'Dutch', 'Esperanto', 'Finnish', 'French',
             'German', 'Greek', 'Hebrew', 'Hindi', 'Hungarian', 'Indonesian', 'Irish', 'Italian', 'Japanese',
             'Korean', 'Persian', 'Polish', 'Portuguese', 'Russian', 'Slovak', 'Spanish', 'Swedish', 'Turkish', 'Ukrainian']
api_langs = ['de', 'en', 'fr', 'es', 'ru', 'ja', 'ko', 'pl', 'pt-BR', 'zh-TW']


##Init
discord.VoiceClient.warn_nacl = False
load_dotenv()
#Init sentry
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production'
)
# print() will only print if run in debugger. pt() will always print.
pt = print
def print(msg):
    if sys.gettrace() is not None:
        pt(msg)
#Set-up folders
paths = [
    f'{app_folder_name}//Logs',
    f'{app_folder_name}//Buffer//Stats',
    f'{app_folder_name}//Buffer//addon',
    f'{app_folder_name}//Buffer//char',
    f'{app_folder_name}//Buffer//dlc',
    f'{app_folder_name}//Buffer//event',
    f'{app_folder_name}//Buffer//item',
    f'{app_folder_name}//Buffer//killer',
    f'{app_folder_name}//Buffer//map',
    f'{app_folder_name}//Buffer//offering',
    f'{app_folder_name}//Buffer//perk',
]
for path in paths:
    os.makedirs(path, exist_ok=True)
log_folder = f'{app_folder_name}//Logs//'
buffer_folder = f'{app_folder_name}//Buffer//'
stats_folder = os.path.abspath(f'{app_folder_name}//Buffer//Stats//')
activity_file = os.path.join(app_folder_name, 'activity.json')
sql_file = os.path.join(app_folder_name, f'{app_folder_name}.db')

#Set-up logging
logger = logging.getLogger('discord')
manlogger = logging.getLogger('Program')
logger.setLevel(logging.INFO)
manlogger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(
    filename = f'{log_folder}DBDStats.log',
    encoding = 'utf-8',
    when = 'midnight',
    backupCount = 27
    )
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
manlogger.addHandler(handler)
manlogger.info('Engine powering up...')

#Load env
TOKEN = os.getenv('TOKEN')
OWNERID = os.getenv('OWNER_ID')
STEAMAPIKEY = os.getenv('steamAPIkey')
SUPPORTID = os.getenv('support_server')
TWITCH_CLIENT_ID = os.getenv('twitch_client_id')
TWITCH_CLIENT_SECRET = os.getenv('twitch_client_secret')
LIBRETRANS_APIKEY = os.getenv('libretransAPIkey')
LIBRETRANS_URL = os.getenv('libretransURL')
DB_HOST = os.getenv('MongoDB_host')
DB_PORT = os.getenv('MongoDB_port')
DB_USER = os.getenv('MongoDB_user')
DB_PASS = os.getenv('MongoDB_password')
DB_NAME = os.getenv('MongoDB_database')
DB_COLLECTION = os.getenv('MongoDB_collection')
TOPGG_TOKEN = os.getenv('TOPGG_TOKEN')
DISCORDBOTS_TOKEN = os.getenv('DISCORDBOTS_TOKEN')
DISCORDBOTLISTCOM_TOKEN = os.getenv('DISCORDBOTLIST_TOKEN')
DISCORDLIST_TOKEN = os.getenv('DISCORDLIST_TOKEN')
DISCORDS_TOKEN = os.getenv('DISCORDS_TOKEN')

#Create activity.json if not exists
class JSONValidator:
    schema = {
        "type" : "object",
        "properties" : {
            "activity_type" : {
                "type" : "string",
                "enum" : ["Playing", "Streaming", "Listening", "Watching", "Competing"]
            },
            "activity_title" : {"type" : "string"},
            "activity_url" : {"type" : "string"},
            "status" : {
                "type" : "string",
                "enum" : ["online", "idle", "dnd", "invisible"]
            },
        },
    }

    default_content = {
        "activity_type": "Playing",
        "activity_title": "Made by Serpensin: https://gitlab.bloodygang.com/Serpensin",
        "activity_url": "",
        "status": "online"
    }

    def __init__(self, file_path):
        self.file_path = file_path

    def validate_and_fix_json(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                try:
                    data = json.load(file)
                    jsonschema.validate(instance=data, schema=self.schema)  # validate the data
                except jsonschema.exceptions.ValidationError as ve:
                    print(f'ValidationError: {ve}')
                    self.write_default_content()
                except json.decoder.JSONDecodeError as jde:
                    print(f'JSONDecodeError: {jde}')
                    self.write_default_content()
        else:
            self.write_default_content()

    def write_default_content(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.default_content, file, indent=4)
validator = JSONValidator(activity_file)
validator.validate_and_fix_json()

#Check if running in docker
try:
    running_in_docker = os.getenv('RUNNING_IN_DOCKER', 'false').lower() == 'true'

    if running_in_docker:
        manlogger.info('Running in docker container.')
        pt('Running in docker container.')
        docker = True
    else:
        manlogger.info('Not running in docker container.')
        pt('Not running in docker container.')
        docker = False
except:
    manlogger.info('Not running in docker container.')
    print('Not running in docker container.')
    docker = False

#Set-up DB
def is_mongo_reachable(host, port, timeout=60):
    try:
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        manlogger.info('Running with MongoDB container.')
        pt('Running with MongoDB container.')
        return True
    except socket.error:
        manlogger.info('Running without MongoDB container.')
        pt('Running without MongoDB container.')
        return False

mongo_host = 'mongo'
mongo_port = 27017

if docker and is_mongo_reachable(mongo_host, mongo_port):
    connection_string = f'mongodb://{mongo_host}:{mongo_port}/DBDStats'
else:
    connection_string = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

db = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=10000)

tb = PrettyTable()
twitch_api = TwitchAPI(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)

#Fix error on windows on shutdown.
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

# Check if all required variables are set
try:
	db.server_info()
	db_available = True
	manlogger.info('Connected to MongoDB.')
	pt('Connected to MongoDB.')
except mongoerr.OperationFailure as e:
	manlogger.warning(f"Error connecting to MongoDB Platform. | Fallback to json-storage. -> {e.details.get('errmsg')}")
	pt(f"Error connecting to MongoDB Platform. | Fallback to json-storage. -> {e.details.get('errmsg')}")
	db_available = False
except mongoerr.ServerSelectionTimeoutError as e:
	error_message = e.args[0]
	error_content = error_message.replace(">]>","")
	manlogger.warning(f"Error connecting to MongoDB Platform. | Fallback to json-storage. -> {error_content}")
	pt(f"Error connecting to MongoDB Platform. | Fallback to json-storage. -> {error_content}")
	db_available = False
#db_available = False
libretrans_url = LIBRETRANS_URL
translator = LibreTranslateAPI(LIBRETRANS_APIKEY, libretrans_url)
translate_available = False
retry_count = 10
while not translate_available and retry_count > 0:
    if asyncio.run(translator.check_status()):
        manlogger.info('Connected to LibreTranslate.')
        pt('Connected to LibreTranslate.')
        translate_available = True
    else:
        retry_count -= 1
        if retry_count > 0:
            manlogger.warning(f'Error connecting to LibreTranslate. | Retrying in 5 seconds. | Retries left: {retry_count}')
            pt(f'Error connecting to LibreTranslate. | Retrying in 5 seconds. | Retries left: {retry_count}')
            asyncio.run(asyncio.sleep(5))
        else:
            manlogger.warning('Could not connect to LibreTranslate. | Disabling translation.')
            pt('Could not connect to LibreTranslate. | Disabling translation.')
            translate_available = False

twitch_available = bool(TWITCH_CLIENT_SECRET and TWITCH_CLIENT_ID)
support_available = bool(SUPPORTID)



#Bot
class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()
        intents.dm_messages = True

        super().__init__(owner_id = OWNERID,
                              intents = intents,
                              status = discord.Status.invisible,
                              auto_reconnect = True
                        )
        self.synced = False
        self.cache_updated = False
        self.initialized = False


    class Presence():
        @staticmethod
        def get_activity() -> discord.Activity:
            with open(activity_file) as f:
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
            with open(activity_file) as f:
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


    async def setup_database(self):
        c.executescript('''
        CREATE TABLE IF NOT EXISTS "changelogs" (
	        "id"	        INTEGER,
            "guild_id"      INTEGER,
	        "channel_id"	INTEGER,
	        PRIMARY KEY("id" AUTOINCREMENT)
        );
        CREATE TABLE IF NOT EXISTS "shrine" (
	        "id"	        INTEGER,
            "guild_id"      INTEGER,
	        "channel_id"	INTEGER,
	        PRIMARY KEY("id" AUTOINCREMENT)
        )
        ''')


    async def on_guild_remove(self, guild):
        manlogger.info(f'I got kicked from {guild}. (ID: {guild.id})')


    async def on_guild_join(self, guild):
        manlogger.info(f'I joined {guild}. (ID: {guild.id})')


    async def on_message(self, message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'activity - Set the activity of the bot\n'
                                       'changelog - Upload a txt, or md, that is send to the changelog channels\n'
                                       'help - Shows this message\n'
                                       'log - Get the log\n'
                                       'shutdown - Shutdown the bot\n'
                                       'status - Set the status of the bot\n'
                                       '```')

        if message.guild is None and message.author.id == int(OWNERID):
            args = message.content.split(' ')
            command, *args = args
            file = message.attachments
            print(command)

            if command == 'help':
                await __wrong_selection()
                return

            elif command == 'log':
                await Owner.log(message, args)
                return

            elif command == 'activity':
                await Owner.activity(message, args)
                return

            elif command == 'status':
                await Owner.status(message, args)
                return

            elif command == 'shutdown':
                await Owner.shutdown(message)
                return

            elif command == 'changelog':
                await Owner.changelog(message, file)
                return

            else:
                await __wrong_selection()


    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        options = interaction.data.get("options")
        option_values = ""
        if options:
            for option in options:
                option_values += f"{option['name']}: {option['value']}"
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{str(timedelta(seconds=int(error.retry_after)))}`', ephemeral=True)
            return
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(f'You are missing the following permissions: `{", ".join(error.missing_permissions)}`', ephemeral=True)
            return
        else:
            try:
                try:
                    await interaction.response.send_message(f"Error! Try again.", ephemeral=True)
                except:
                    try:
                        await interaction.followup.send(f"Error! Try again.", ephemeral=True)
                    except:
                        pass
            except discord.Forbidden:
                try:
                    await interaction.followup.send(f"{error}\n\n{option_values}", ephemeral=True)
                except discord.NotFound:
                    try:
                        await interaction.response.send_message(f"{error}\n\n{option_values}", ephemeral=True)
                    except discord.NotFound:
                        pass
                except Exception as e:
                    manlogger.warning(f"Unexpected error while sending message: {e}")
            finally:
                traceback.print_exception(type(error), error, error.__traceback__)
                try:
                    manlogger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}")
                    print(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}")
                except AttributeError:
                    manlogger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}")
                    print(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}")
                sentry_sdk.capture_exception(error)


    async def on_ready(self):
        if self.initialized:
            await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
            return
        global owner, start_time, shutdown, conn, c
        logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            manlogger.info('Syncing...')
            pt('Syncing commands...')
            await tree.set_translator(CustomTranslator())
            await tree.sync()
            manlogger.info('Synced.')
            print('Commands synced.')
            self.synced = True
        conn = sqlite3.connect(sql_file)
        c = conn.cursor()
        await self.setup_database()
        shutdown = False
        try:
            owner = await bot.fetch_user(OWNERID)
            print('Owner found.')
        except:
            print('Owner not found.')

        #Start background tasks
        bot.loop.create_task(update_cache.task())
        if TOPGG_TOKEN:
            bot.loop.create_task(update_stats.topgg())
        if DISCORDBOTS_TOKEN:
            bot.loop.create_task(update_stats.discordbots())
        if DISCORDBOTLISTCOM_TOKEN:
            bot.loop.create_task(update_stats.discordbotlist_com())
        if DISCORDLIST_TOKEN:
            bot.loop.create_task(update_stats.discordlist())
        if DISCORDS_TOKEN:
            bot.loop.create_task(update_stats.discords())
        if twitch_available:
            bot.loop.create_task(Functions.update_twitchinfo_task())
        bot.loop.create_task(Functions.health_server())
        bot.loop.create_task(Functions.check_db_connection_task())

        while not self.cache_updated:
            await asyncio.sleep(1)
        bot.loop.create_task(Functions.subscribe_shrine_task())
        if not docker:
            clear()
        await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
        pt(r'''
 ____     ____     ____     ____     __              __
/\  _`\  /\  _`\  /\  _`\  /\  _`\  /\ \__          /\ \__
\ \ \/\ \\ \ \L\ \\ \ \/\ \\ \,\L\_\\ \ ,_\     __  \ \ ,_\    ____
 \ \ \ \ \\ \  _ <'\ \ \ \ \\/_\__ \ \ \ \/   /'__`\ \ \ \/   /',__\
  \ \ \_\ \\ \ \L\ \\ \ \_\ \ /\ \L\ \\ \ \_ /\ \L\.\_\ \ \_ /\__, `\
   \ \____/ \ \____/ \ \____/ \ `\____\\ \__\\ \__/.\_\\ \__\\/\____/
    \/___/   \/___/   \/___/   \/_____/ \/__/ \/__/\/_/ \/__/ \/___/

        ''')
        start_time = datetime.now()
        manlogger.info('Initialization completed.')
        pt('READY')
        self.initialized = True
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error



#Update cache/db (Every ~4h)
class update_cache():
    async def __update_perks():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f"{api_base}perks?locale={lang}")
            if data == 1:
                manlogger.warning("Perks couldn't be updated.")
                print("Perks couldn't be updated.")
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['perk'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}perk//{lang}.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=2)


    async def __update_offerings():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f'{api_base}offerings?locale={lang}')
            if data == 1:
                manlogger.warning("Offerings couldn't be updated.")
                print("Offerings couldn't be updated.")
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['offering'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}offering//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)


    async def __update_chars():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f'{api_base}characters?locale={lang}')
            if data == 1:
                manlogger.warning("Characters couldn't be updated.")
                print("Characters couldn't be updated.")
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['char'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}char//{lang}.json", 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)


    async def __update_dlc():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f'{api_base}dlc?locale={lang}')
            if data == 1:
                manlogger.warning("DLC couldn't be updated.")
                print("DLC couldn't be updated.")
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['dlc'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}dlc//{lang}.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=2)


    async def __update_item():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f'{api_base}items?role=survivor&locale={lang}')
            if data == 1:
                manlogger.warning("Items couldn't be updated.")
                print("Items couldn't be updated.")
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['item'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}item//{lang}.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=2)


    async def __update_addon():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f'{api_base}addons?locale={lang}')
            if data == 1:
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['addon'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}addon//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)


    async def __update_map():
        for lang in api_langs:
            data = await Functions.check_api_rate_limit(f'{api_base}maps?locale={lang}')
            if data == 1:
                manlogger.warning("Maps couldn't be updated.")
                print("Maps couldn't be updated.")
                return 1
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['map'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}map//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)


    async def __update_event():
        for lang in api_langs:
            data_list = await Functions.check_api_rate_limit(f'{api_base}events?locale={lang}')
            if data_list == 1:
                manlogger.warning("Events couldn't be updated.")
                print("Events couldn't be updated.")
                return 1
            data = {}
            for i in range(len(data_list)):
                data[str(i)] = data_list[i]
            if db_available:
                data['_id'] = lang
                db[DB_NAME]['event'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}event//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)


    async def __update_version():
        data = await Functions.check_api_rate_limit(f'{api_base}versions')
        if data == 1:
            manlogger.warning("Version couldn't be updated.")
            print("Version couldn't be updated.")
            return 1
        if db_available:
            data['_id'] = 'version_info'
            db[DB_NAME]['version'].update_one({'_id': 'version_info'}, {'$set': data}, upsert=True)
        with open(f'{buffer_folder}version_info.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)


    async def __clear_playerstats():
        for filename in os.scandir(stats_folder):
            if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 24:
                os.remove(filename)


    async def __name_lists():
        async def load_and_set_names(request_data, target_var_name):
            for lang in api_langs:
                killer = False
                if request_data == 'killers':
                    request_data = 'chars'
                    killer = True
                data = await Functions.data_load(request_data, lang)
                if data is None:
                    print(f'{request_data} couldn\'t be updated for namelist {lang}.')
                    manlogger.fatal(f'{request_data} couldn\'t be updated for namelist {lang}.')
                    sentry_sdk.capture_message(f'{request_data} couldn\'t be updated for namelist {lang}.')
                    return
                new_names = []
                for key in data.keys():
                    if str(key) != '_id':
                        if killer:
                            if data[key]['role'] == 'killer':
                                name = str(data[key]['name']).replace('&nbsp;', ' ')
                                new_names.append(name)
                        else:
                            name = str(data[key]['name']).replace('&nbsp;', ' ')
                            new_names.append(name)
                new_names = [name for name in new_names if name is not None]
                globals()[f'{target_var_name}_{lang}'] = new_names

        updates = [load_and_set_names('addons', 'addon_names'),
                   load_and_set_names('addons', 'addon_names'),
                   load_and_set_names('chars', 'char_names'),
                   load_and_set_names('killers', 'killer_names'),
                   load_and_set_names('dlcs', 'dlc_names'),
                   load_and_set_names('items', 'item_names'),
                   load_and_set_names('maps', 'map_names'),
                   load_and_set_names('offerings', 'offering_names'),
                   load_and_set_names('perks', 'perk_names')
                   ]

        tasks = [asyncio.create_task(update) for update in updates]

        for task in tasks:
            await task



    async def start_cache_update():
        print('Updating cache...')
        manlogger.info('Updating cache...')

        updates = [update_cache.__update_chars(),
                   update_cache.__update_perks(),
                   update_cache.__update_offerings(),
                   update_cache.__update_dlc(),
                   update_cache.__update_item(),
                   update_cache.__update_map(),
                   update_cache.__update_addon(),
                   update_cache.__update_event(),
                   update_cache.__update_version(),
                   update_cache.__clear_playerstats()
                   ]

        tasks = [asyncio.create_task(update) for update in updates]

        for task in tasks:
           await task
        await update_cache.__name_lists()

        bot.cache_updated = True

        print('Cache updated.')
        manlogger.info('Cache updated.')


    async def task():
        while not shutdown:
            await update_cache.start_cache_update()
            try:
                await asyncio.sleep(60*60*4)
            except asyncio.CancelledError:
                pass


#Update botstats on websites
class update_stats():
    async def topgg():
        headers = {
            'Authorization': TOPGG_TOKEN,
            'Content-Type': 'application/json'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://top.gg/api/bots/{bot.user.id}/stats', headers=headers, json={'server_count': len(bot.guilds), 'shard_count': len(bot.shards)}) as resp:
                    if resp.status != 200:
                        manlogger.error(f'Failed to update top.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                pass


    async def discordbots():
        headers = {
            'Authorization': DISCORDBOTS_TOKEN,
            'Content-Type': 'application/json'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://discord.bots.gg/api/v1/bots/{bot.user.id}/stats', headers=headers, json={'guildCount': len(bot.guilds), 'shardCount': len(bot.shards)}) as resp:
                    if resp.status != 200:
                        manlogger.error(f'Failed to update discord.bots.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                pass


    async def discordbotlist_com():
        headers = {
            'Authorization': DISCORDBOTLISTCOM_TOKEN,
            'Content-Type': 'application/json'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://discordbotlist.com/api/v1/bots/{bot.user.id}/stats', headers=headers, json={'guilds': len(bot.guilds), 'users': sum(guild.member_count for guild in bot.guilds)}) as resp:
                    if resp.status != 200:
                        manlogger.error(f'Failed to update discordbotlist.com: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                pass


    async def discordlist():
        headers = {
            'Authorization': f'Bearer {DISCORDLIST_TOKEN}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://api.discordlist.gg/v0/bots/{bot.user.id}/guilds', headers=headers, json={"count": len(bot.guilds)}) as resp:
                    if resp.status != 200:
                        manlogger.error(f'Failed to update discordlist.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                pass


    async def discords():
        headers = {
            'Authorization': DISCORDS_TOKEN,
            'Content-Type': 'application/json'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://discords.com/bots/api/bot/{bot.user.id}', headers=headers, json={"server_count": len(bot.guilds)}) as resp:
                    if resp.status != 200:
                        manlogger.error(f'Failed to update discords.com: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                pass



#Functions
class Functions():
    async def health_server():
        async def __health_check(request):
            return web.Response(text="Healthy")

        app = web.Application()
        app.router.add_get('/health', __health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        try:
            await site.start()
        except OSError as e:
            manlogger.warning(f'Error while starting health server: {e}')
            print(f'Error while starting health server: {e}')


    async def steam_link_to_id(vanity):
        vanity = vanity.replace('https://steamcommunity.com/profiles/', '')
        vanity = vanity.replace('https://steamcommunity.com/id/', '')
        vanity = vanity.replace('/', '')
        api_url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAMAPIKEY}&vanityurl={vanity}'
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                try:
                    if data['response']['success'] == 1:
                        return data['response']['steamid']
                    else:
                        return vanity
                except:
                    return None


    async def check_for_dbd(id, steamAPIkey):
        id = await Functions.steam_link_to_id(id)
        if id is None:
            return (1, 1)
        if len(id) != 17:
            return (1, 1)
        try:
            int(id)
        except:
            return (1, 1)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steamAPIkey}&steamid={id}&format=json') as resp:
                    data = await resp.json()
                    if resp.status == 400:
                        return (2, 2)
                    if data['response'] == {}:
                        return (3, 3)
                    for event in data['response']['games']:
                        if event['appid'] == 381210:
                            return (0, id)
                        else:
                            continue
                    return (4, 4)
        except:
            return(5, 5)


    async def get_language_name(lang_code):
        if lang_code == 'pt-BR':
            return 'Portuguese'
        elif lang_code == 'zh-TW':
            return 'Chinese'
        try:
            lang = pycountry.languages.get(alpha_2=lang_code).name
            return lang
        except Exception as e:
            print(e)
            return None


    async def convert_time(timestamp, request='full'):
        if request == 'full':
            return(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp)))
        elif request == 'date':
            return(time.strftime('%Y-%m-%d', time.gmtime(timestamp)))
        elif request == 'time':
            return(time.strftime('%H:%M:%S', time.gmtime(timestamp)))


    def convert_to_unix_timestamp(iso_time: str, local_tz: str = 'Europe/Berlin') -> int:
        """
        Convert an ISO 8601 formatted string to a UNIX timestamp.
        Parameters:
        - iso_time (str): The ISO 8601 formatted time string (e.g., "2023-11-07T14:59:59").
        - local_tz (str): The local timezone as a string (default is 'Europe/Berlin').
        Returns:
        - int: The corresponding UNIX timestamp.
        """
        # Create a datetime object in UTC timezone
        dt_object = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC)

        # Convert to local timezone
        local_timezone = pytz.timezone(local_tz)
        dt_object = dt_object.astimezone(local_timezone)

        # Get the UNIX timestamp
        unix_timestamp = int(dt_object.timestamp())

        return unix_timestamp


    async def convert_number(number, pureInt: bool = False):
        if pureInt:
            return int(number)
        else:
            return f"{int(number):,}"


    async def check_api_rate_limit(url):
        # Check the 429 status code and return 1 when this appearance
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(response)
                if response.status == 429:
                    return 1
                else:
                    return await response.json()


    async def check_if_removed(id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{api_base}playerstats?steamid={id}') as resp:
                    print(resp.status)
                    resp.raise_for_status()  # Throws an exception if the status code is not 200
                    return 0
        except aiohttp.ClientResponseError as e:
            print(e.request_info.url)
            if e.status == 404:
                url = f'{alt_playerstats}{id}'
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            page = await resp.text()
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


    async def create_support_invite(interaction):
        try:
            guild = bot.get_guild(int(SUPPORTID))
        except ValueError:
            return "Could not find support guild."
        if guild is None:
            return "Could not find support guild."
        if not guild.text_channels:
            return "Support guild has no text channels."
        try:
            member = await guild.fetch_member(interaction.user.id)
        except discord.NotFound:
            member = None
        if member is not None:
            return "You are already in the support guild."
        channels: discord.TextChannel = guild.text_channels
        for channel in channels:
            try:
                invite: discord.Invite = await channel.create_invite(
                    reason=f"Created invite for {interaction.user.name} from server {interaction.guild.name} ({interaction.guild_id})",
                    max_age=60,
                    max_uses=1,
                    unique=True
                )
                return invite.url
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue
        return "Could not create invite. There is either no text-channel, or I don't have the rights to create an invite."


    async def get_language_code(interaction: discord.Interaction, lang_type: Literal['server', 'client'] = 'client'):
        if type(interaction) == discord.Guild:
            lang_code = interaction.preferred_locale[1][:2]
        elif lang_type == 'server':
            lang_code = interaction.guild_locale[1]
        else:
            lang_code = interaction.locale[1]
        lang_name = await Functions.get_language_name(lang_code)
        if lang_name in languages:
            return lang_code
        else:
            return 'en'


    async def translate(interaction: discord.Interaction, text):
        if type(interaction) == discord.app_commands.transformers.NoneType:
            lang = 'en'
        elif type(interaction) != str:
            lang = await Functions.get_language_code(interaction)
            if lang in api_langs:
                if type(interaction) != discord.Guild:
                    return text
        else:
            lang = interaction

        hashed = format(zlib.crc32(text.encode('utf-8')), '08x')
        print(f'Translation Hash: {hashed}')

        if not db_available:
            try:
                with open(f'{buffer_folder}translations.json', 'r', encoding='utf8') as f:
                    data = json.load(f)
            except:
                data = {}
        else:
            data = json.loads(json.dumps(db[DB_NAME]['translations'].find_one({'_id': 'translations'})))
            if data is None:
                data = {}

        if hashed in data.keys():
            print(f'Hash {hashed} found in cache.')
            if lang in data[hashed].keys():
                print(f'Language {lang} found in cache.')
                return data[hashed][lang]
            else:
                print(f'Language {lang} not found in cache.')
                translation = await translator.translate(text, lang)
                data[hashed] = {lang: translation['data']['translatedText']}
                if db_available:
                    db[DB_NAME]['translations'].update_one(
                        {'_id': 'translations'},
                        {
                            '$set': {
                                f'{hashed}.{lang}': translation['data']['translatedText']
                            }
                        }
                    )
                else:
                    with open(f'{buffer_folder}translations.json', 'r', encoding='utf8') as f:
                        old_data = json.load(f)
                    data = Functions.merge_dictionaries(old_data, data)
                    with open(f'{buffer_folder}translations.json', 'w', encoding='utf8') as f:
                        json.dump(data, f, indent=4)
                return translation['data']['translatedText']
        else:
            print(f'Hash {hashed} not found in cache.')
            translation = await translator.translate(text, lang)
            data[hashed] = {lang: translation['data']['translatedText']}
            if db_available:
                db[DB_NAME]['translations'].update_one({'_id': 'translations'}, {'$set': data}, upsert=True)
            else:
                with open(f'{buffer_folder}translations.json', 'w', encoding='utf8') as f:
                    json.dump(data, f, indent=4)
            return translation['data']['translatedText']


    async def data_load(requested: Literal['addons', 'chars', 'dlcs', 'events', 'items', 'maps', 'offerings', 'perks', 'shrine', 'twitch', 'versions'], lang: Literal['de', 'en', 'fr', 'es', 'ru', 'ja', 'ko', 'pl', 'pt-BR', 'zh-TW'] = ''):
        requested = (lambda s: s[:-1] if s.endswith('s') else s)(requested)
        if lang not in api_langs:
            lang = 'en'

        file_name = f"{buffer_folder}{requested}//"
        db_id = f"{requested}_info"

        if requested == 'shrine':
            file_name = f"{buffer_folder}shrine_info"
        elif requested == 'version':
            file_name = f"{buffer_folder}version_info"
        elif requested == 'twitch':
            file_name = f"{buffer_folder}twitch_info"
        elif requested != 'shrine':
            file_name += f"{lang}"
            db_id = lang
        else:
            raise Exception('Invalid request.')

        if not db_available:
            with open(f"{file_name}.json", "r", encoding="utf8") as f:
                data = json.load(f)
        else:
            data = json.loads(json.dumps(db[DB_NAME][requested].find_one({'_id': db_id})))

        return data


    async def perk_send(perk, lang, interaction, shrine=False, random=False):
        async def check():
            embed.set_thumbnail(url=f"{bot_base}{data[key]['image']}")
            character = await Functions.data_load('chars', lang)
            if character is None:
                return
            for i in character.keys():
                if str(i) == str(data[key]['character']):
                    embed.set_author(name=f"{character[i]['name']}", icon_url=f"{bot_base}{character[i]['image']}")
                    break

        def get_tunables_value(position: int) -> str:
            try:
                length = len(data[perk]['tunables'][position])
            except:
                return ''
            if length == 1:
                return data[perk]['tunables'][position][0]
            elif length == 2:
                return f"{data[perk]['tunables'][position][0]}/{data[perk]['tunables'][position][1]}"
            elif length == 3:
                return f"{data[perk]['tunables'][position][0]}/{data[perk]['tunables'][position][1]}/{data[perk]['tunables'][position][2]}"

        if shrine:
            data = await Functions.data_load('perks')
        else:
            data = await Functions.data_load('perks', lang)
        if data is None:
            if type(interaction) == discord.Interaction:
                await interaction.followup.send('Perks couldn\'t be loaded.', ephemeral=True)
                return
            else:
                return {}

        perk = str(Functions.find_key_by_name(perk, data)).replace(' ', '')

        if shrine:
            data = await Functions.data_load('perks', lang)
            if data is None:
                return {}

        description = str(Functions.format_complete_text_with_list(str(data[perk]['description']) \
        .replace('<br><br>', ' ') \
        .replace('<br>', '') \
        .replace('<i>', '**') \
        .replace('</i>', '**') \
        .replace('<b>', '**') \
        .replace('</b>', '**') \
        .replace('&nbsp;', ' ') \
        .replace('{0}', get_tunables_value(0)) \
        .replace('{1}', get_tunables_value(1)) \
        .replace('{2}', get_tunables_value(2)) \
        .replace('{3}', get_tunables_value(3)) \
        .replace('{4}', get_tunables_value(4)) \
        .replace('{5}', get_tunables_value(5)) \
        .replace('{6}', get_tunables_value(6))))
        description = description \
        .replace('<li>', '') \
        .replace('</li>', '')
        print(perk)

        if shrine and type(interaction) == discord.Interaction:
            if lang in api_langs:
                embed = discord.Embed(title=f"{data[perk]['name']}", description=description, color=0xb19325)
            else:
                embed = discord.Embed(title=f"{await Functions.translate(interaction, 'Perk-Description for')} '{data[perk]['name']}'", description=await Functions.translate(interaction, description), color=0xb19325)
            key = perk
            await check()
            return embed
        elif shrine and type(interaction) != discord.Interaction:
            if lang in api_langs:
                embed = discord.Embed(title=f"{data[perk]['name']}", description=description, color=0xb19325)
            else:
                embed = discord.Embed(title=f"{await Functions.translate(lang, 'Perk-Description for')} '{data[perk]['name']}'", description=await Functions.translate(lang, description), color=0xb19325)
            key = perk
            await check()
            return embed
        else:
            for key in data.keys():
                if str(key) == '_id':
                    continue
                if key == perk:
                    if lang in api_langs:
                        embed = discord.Embed(title=f"{data[key]['name']}", description=description, color=0xb19325)
                    else:
                        embed = discord.Embed(title=f"{await Functions.translate(interaction, 'Perk-Description for')} '{data[key]['name']}'", description=await Functions.translate(interaction, description), color=0xb19325)
                    await check()
                    if random:
                        return embed
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
        await interaction.followup.send(await Functions.translate(interaction, f"The perk {perk} doesn't exist."), ephemeral=True)


    async def addon_send(addon, lang, interaction: discord.Interaction, random: bool = False):
        data = await Functions.data_load('addons', lang)
        if data is None:
            await interaction.followup.send('Addons couldn\'t be loaded.', ephemeral=True)
            return

        addon = Functions.find_key_by_name(addon, data)
        for key in data.keys():
            if str(key) == '_id':
                continue
            if key == addon:
                description = str(data[key]['description']) \
                .replace('<br>', '') \
                .replace('<b>', '') \
                .replace('</b>', '') \
                .replace('<i>','') \
                .replace('</i>','') \
                .replace('.', '. ') \
                .replace('&nbsp;', ' ') \
                .replace('&nbsp;', ' ')

                if lang in api_langs:
                    embed = discord.Embed(title=data[key]['name'],
                                      description=description,
                                      color=0x0400ff)
                else:
                    embed = discord.Embed(title=str(data[key]['name']).replace('&nbsp;', ' '),
                                      description = await Functions.translate(interaction, description), color=0x0400ff)
                embed.set_thumbnail(url=f"{bot_base}{data[key]['image']}")
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                embed.add_field(name='Rarity', value=data[key]['rarity'], inline=True)
                embed.add_field(name='Role', value=data[key]['role'], inline=True)
                if data[key]['item_type'] is None:
                    char = await Functions.data_load('chars', lang)
                    if char is None:
                        return
                    for key in char.keys():
                        if str(key) == '_id':
                            continue
                        if str(data[addon]['parents']).replace('[', '').replace('\'', '').replace(']', '') == str(char[key]['item']).replace('[', '').replace('\'', '').replace(']', ''):
                            embed.add_field(name='Origin', value=char[key]['name'], inline=True)
                            break
                else:
                    embed.add_field(name='Origin', value=data[key]['item_type'], inline=True)
                if random:
                    return embed
                else:
                    await interaction.followup.send(embed=embed, ephemeral = True)
                    return not None
        return None


    async def offering_send(interaction, offering, lang, loadout: bool = False):
        data = await Functions.data_load('offerings', lang)
        if data is None:
            await interaction.followup.send('Offerings couldn\'t be loaded.', ephemeral=True)
            return

        offering = Functions.find_key_by_name(offering, data)
        for item in data.keys():
            if item == '_id':
                continue
            if str(data[item]['name']).lower() == offering.lower() or str(item).lower() == offering.lower():
                if lang in api_langs:
                    embed = discord.Embed(title = data[item]['name'],
                                      description = str(data[item]['description']).replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '').replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.').replace('.', '. '),
                                      color = 0x00ff00)
                else:
                    embed = discord.Embed(title = data[item]['name'],
                                      description = await Functions.translate(interaction, str(data[item]['description']).replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '').replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.').replace('.', '. ')),
                                      color = 0x00ff00)
                embed.set_thumbnail(url=f"{bot_base}{data[item]['image']}")
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
        await interaction.followup.send(await Functions.translate(interaction, f"The offering {offering} doesn't exist."), ephemeral = True)


    async def item_send(interaction, item, lang, loadout: bool = False):
        data_en = await Functions.data_load('items', lang)
        if data_en is None:
            await interaction.followup.send('Items couldn\'t be loaded.', ephemeral=True)
            return
        data_loc = await Functions.data_load('items', lang)
        if data_loc is None:
            await interaction.followup.send('Items couldn\'t be loaded.', ephemeral=True)
            return

        item = Functions.find_key_by_name(item, data_en)
        for i in data_loc.keys():
            if i == '_id':
                continue
            if str(data_loc[i]['name']).lower() == item.lower() or str(i).lower() == item.lower():
                if data_loc[i]['name'] is None:
                    title = i
                else:
                    title = data_loc[i]['name']
                if lang in api_langs:
                    embed = discord.Embed(title = title,
                                      description = str(data_loc[i]['description']).replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '').replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.').replace('.', '. '),
                                      color = 0x00ff00)
                else:
                    embed = discord.Embed(title = title,
                                      description = await Functions.translate(interaction, str(data_loc[i]['description']).replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '').replace('<br><br>', '').replace('<br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.').replace('.', '. ')),
                                      color = 0x00ff00)
                embed.set_thumbnail(url=f"{bot_base}{data_loc[i]['image']}".replace('UI/Icons/items', 'UI/Icons/Items'))
                embed.add_field(name = '\u200b', value = '\u200b', inline = False)
                embed.add_field(name = 'Rarity', value = str(data_loc[i]['rarity']))
                embed.add_field(name = 'Is in Bloodweb', value = str(data_loc[i]['bloodweb']))
                embed.add_field(name = 'Role', value = str(data_loc[i]['role']))
                if data_loc[i]['event'] is not None:
                    embed.add_field(name = 'Event', value = str(data_loc[i]['event']))
                if loadout == True:
                    return embed, data_loc[i]['item_type']
                await interaction.followup.send(embed = embed, ephemeral = True)
                return
        else:
            await interaction.followup.send(await Functions.translate(interaction, f"The item {item} doesn't exist."), ephemeral = True)


    async def char_send(interaction, data, char, dlc_data, lang, loadout: bool = False):
        for key in data.keys():
            if str(key) == '_id':
                continue
            if str(data[key]['name']) == char:
                embed = discord.Embed(title=await Functions.translate(interaction, "Character Info"), description=str(data[key]['name']), color=0xb19325)
                embed.set_thumbnail(url=f"{bot_base}{data[key]['image']}")
                embed.add_field(name=await Functions.translate(interaction, "Role"), value=str(data[key]['role']).capitalize(), inline=True)
                embed.add_field(name=await Functions.translate(interaction, "Gender"), value=str(data[key]['gender']).capitalize(), inline=True)
                for dlc_key in dlc_data.keys():
                    if dlc_key == data[key]['dlc']:
                        embed.add_field(name="DLC", value=f"[{dlc_data[dlc_key]['name'].capitalize().replace(' chapter', '')}]({steamStore}{dlc_data[dlc_key]['steamid']})", inline=True)
                if data[key]['difficulty'] != 'none':
                    embed.add_field(name=await Functions.translate(interaction, "Difficulty"), value=str(data[key]['difficulty']).capitalize(), inline=True)
                if str(data[key]['role']) == 'killer':
                    embed.add_field(name=await Functions.translate(interaction, "Walkspeed"), value=f"{int(data[key]['tunables']['MaxWalkSpeed']) / 100}m/s", inline=True)
                    embed.add_field(name=await Functions.translate(interaction, "Terror Radius"), value=f"{int(data[key]['tunables']['TerrorRadius']) / 100}m", inline=True)
                    embed.add_field(name='\u200b', value='\u200b', inline=True)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                if lang in api_langs and lang != 'en':
                    embed.add_field(name="Bio", value=str(data[key]['bio']).replace('<ul>', '').replace('</ul>', '').replace('<br><br>', '').replace('<br>', '').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.', '. '), inline=False)
                else:
                    embed.add_field(name="Bio", value=await Functions.translate(interaction, str(data[key]['bio']).replace('<ul>', '').replace('</ul>', '').replace('<br><br>', '').replace('<br>', '').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.', '. ')), inline=False)
                if loadout:
                    return embed

                story_text = str(data[key]['story']).replace('<i>', '*').replace('</i>', '*').replace('<ul>', '').replace('</ul>', '').replace('<br><br>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.').replace('.', '. ')
                print(f"Story length: {len(story_text)}")
                if len(story_text) > 4096:
                    story_text = Functions.insert_newlines(story_text)
                    story_file = f'{buffer_folder}character_story{uuid4()}.txt'
                    with open(story_file, 'w', encoding='utf8') as f:
                        if lang in api_langs and lang != 'en':
                            f.write(story_text)
                        else:
                            f.write(await Functions.translate(interaction, story_text))
                    await interaction.followup.send(embed=embed, ephemeral = True)
                    await interaction.followup.send(f"Story of {data[key]['name']}", file=discord.File(f"{story_file}"), ephemeral=True)
                    os.remove(story_file)
                    return
                elif 1024 < len(story_text) <= 4096:
                    if lang in api_langs and lang != 'en':
                        embed2 = discord.Embed(title="Story", description=story_text, color=0xb19325)
                    else:
                        embed2 = discord.Embed(title='Story', description=await Functions.translate(interaction, story_text), color=0xb19325)
                    await interaction.followup.send(embeds=[embed, embed2], ephemeral = True)
                    return
                else:
                    if lang in api_langs and lang != 'en':
                        embed.add_field(name="Story", value=story_text, inline=False)
                    else:
                        embed.add_field(name="Story", value=await Functions.translate(interaction, story_text), inline=False)
                await interaction.followup.send(embed=embed, ephemeral = True)
                return
        embed = discord.Embed(title=await Functions.translate(interaction, "Character Info"), description=await Functions.translate(interaction, f"I couldn't find a character named {char}."), color=0xb19325)
        await interaction.followup.send(embed=embed, ephemeral = True)


    async def get_item_type(item, data):
        types = ['map', 'key', 'toolbox', 'medkit', 'flashlight', 'firecracker', 'rainbow_map']
        if item in types:
            return item
        for key, value in data.items():
            if value == 'item_info':
                continue
            if item.lower() == key.lower() or item.lower() == value["name"].lower():
                return value["item_type"]
        return 1


    async def find_killer_item(killer, chars):
        killer_data = None
        for char_data in chars.values():
            if char_data in api_langs:
                continue
            if str(char_data['id']).lower().replace('the', '').strip() == str(killer).lower().replace('the', '').strip() or str(char_data['name']).lower().replace('the', '').strip() == str(killer).lower().replace('the', '').strip():
                killer_data = char_data
                break
        if killer_data is None or 'item' not in killer_data:
            return 1
        return killer_data['item']


    async def find_killer_by_item(item_name: str, killers_data) -> str:
        for killer in killers_data.values():
            if killer in api_langs:
                continue
            if killer.get('item') == item_name:
                return killer['id']
        return 1


    def find_key_by_name(input_name, data):
        for key, value in data.items():
            if key == '_id':
                continue
            key_name = str(value.get('name')).replace('&nbsp;', ' ')
            if key_name == input_name:
                return key
        return input_name


    def merge_dictionaries(json1, json2):
        for key, value in json2.items():
            if key in json1:
                json1[key].update(value)
            else:
                json1[key] = value
        return json1


    def format_complete_text_with_list(text):
        """
        Formats the provided text to create a markdown list using regex.
        The function identifies the list within the text, formats it, and returns the complete text with the formatted list.

        :param text: String containing the list items within the complete text.
        :return: Complete text with the formatted markdown list.
        """
        # Define a regex pattern to match the list section
        list_pattern = r'<ul><li>(.*?)</li></ul>'

        # Search for the list in the text
        list_match = re.search(list_pattern, text, re.DOTALL)

        if list_match:
            # Extract the list part
            list_text = list_match.group(1)

            # Split the list into items and format each item as a markdown list item
            list_items = list_text.split('</li><li>')
            markdown_list = ['\n'] + [f"- {item.strip()}" for item in list_items if item.strip()] + ['\n']

            # Replace the original list in the text with the formatted markdown list
            formatted_list = '\n'.join(markdown_list)
            formatted_text = re.sub(list_pattern, formatted_list, text, flags=re.DOTALL)
            return formatted_text
        else:
            # If no list is found, return the original text
            return text


    def insert_newlines(text, words_per_line=30):
        """
        Inserts a newline character into a string of text approximately every 'words_per_line' words,
        avoiding splits near punctuation or too close to the end of a sentence.
        Now also considers commas as punctuation and avoids breaking if the last period was within the last 4 words.

        :param text: The text to be processed.
        :param words_per_line: The approximate number of words per line.
        :return: The processed text with newlines inserted.
        """
        words = text.split()
        processed_text = ""
        word_count = 0
        last_period_index = -5  # Initialize to a value outside the checking range

        for i, word in enumerate(words):
            processed_text += word + " "
            word_count += 1

            # Update the index of the last period
            if "." in word:
                last_period_index = i

            # Check if it's time for a new line
            if word_count >= words_per_line:
                next_words = words[i+1:i+5]
                next_words_str = " ".join(next_words)

                # Conditions to avoid breaking: near punctuation, too close to the end of a sentence,
                # or if the last period was within the last 4 words
                if (word[-1] not in ".!?,"
                    and not any(punc in next_words_str for punc in ".!?,")
                    and i - last_period_index >= 4):
                    processed_text = processed_text.rstrip() + "\n"
                    word_count = 0

        return processed_text.strip()


    async def get_or_fetch(item: str, item_id: int) -> Optional[Any]:
        """
        Attempts to retrieve an object using the 'get_<item>' method of the bot class, and
        if not found, attempts to retrieve it using the 'fetch_<item>' method.

        :param item: Name of the object to retrieve
        :param item_id: ID of the object to retrieve
        :return: Object if found, else None
        :raises AttributeError: If the required methods are not found in the bot class
        """
        get_method_name = f'get_{item}'
        fetch_method_name = f'fetch_{item}'

        get_method = getattr(bot, get_method_name, None)
        fetch_method = getattr(bot, fetch_method_name, None)

        if get_method is None or fetch_method is None:
            raise AttributeError(f"Methods {get_method_name} or {fetch_method_name} not found on bot object.")

        item_object = get_method(item_id)
        if item_object is None:
            try:
                item_object = await fetch_method(item_id)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass
        return item_object


    async def subscribe_shrine_task():
        async def function():
            shrine_new = await Functions.check_api_rate_limit('https://api.nightlight.gg/v1/shrine')
            if shrine_new == 1:
                manlogger.warning("Shrine couldn't be updated.")
                print("Shrine couldn't be updated.")
                return 1
            shrine_old = await Functions.data_load('shrine')
            if shrine_old is None or shrine_new['data']['week'] != shrine_old['data']['week']:
                if db_available:
                    shrine_new['_id'] = 'shrine_info'
                    db[DB_NAME]['shrine'].update_one({'_id': 'shrine_info'}, {'$set': shrine_new}, upsert=True)
                with open(f"{buffer_folder}shrine_info.json", "w", encoding="utf8") as f:
                    json.dump(shrine_new, f, indent=4)
            if shrine_old is None or shrine_new['data']['week'] > shrine_old['data']['week']:
                c.execute('SELECT * FROM shrine')
                for row in c.fetchall():
                    await Info.shrine(channel_id=(row[1], row[2]))

        while not shutdown:
            await function()
            try:
                await asyncio.sleep(60*15)
            except asyncio.CancelledError:
                pass


    async def check_db_connection_task():
        async def __upload_json_to_db():
            for entry in os.scandir(buffer_folder):
                if entry.is_dir():
                    if entry.name in ['Stats']:
                        continue
                    for filename in os.scandir(entry):
                        if filename.is_file() and filename.path.endswith('.json'):
                            with open(filename.path, 'r', encoding='utf8') as file:
                                data = json.load(file)
                                db[DB_NAME][str(entry.name)].update_one({'_id': data['_id']}, {'$set': data}, upsert=True)
                if entry.is_file() and entry.name in ['shrine_info.json', 'version_info.json']:
                    with open(entry.path, 'r', encoding='utf8') as file:
                        data = json.load(file)
                        db[DB_NAME][str(entry.name).replace('shrine_info.json', 'shrine').replace('version_info.json', 'version')].update_one({'_id': str(entry.name).replace('shrine_info.json', 'shrine_info').replace('version_info.json', 'version_info')}, {'$set': data}, upsert=True)

        async def function():
            global db_available
            try:
                db.server_info()
                if not db_available:
                    db_available = True
                    await __upload_json_to_db()
                    manlogger.info("Database connection established.")
                    try:
                        await owner.send("Database connection established.")
                    except:
                        pass
            except Exception as e:
                if not db_available:
                    return
                else:
                    db_available = False
                    manlogger.warning(f"Database connection lost. {e} -> Fallback to json.")
                    try:
                        await owner.send(f"Database connection lost.\n{e}\n-> Fallback to json.")
                    except:
                        pass

        if db_available:
            while not shutdown:
                try:
                    await function()
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    pass


    async def update_twitchinfo_task():
        async def function():
            if not twitch_available:
                return
            game_id = await twitch_api.get_game_id("Dead by Daylight")
            if game_id is None:
                return
            stats = await twitch_api.get_category_stats(game_id)
            if not isinstance(stats, dict):
                return
            top = await twitch_api.get_top_streamers(game_id)
            image = await twitch_api.get_category_image(game_id)
            if image is None:
                image = ''
            # Create json from data - Stats
            data = {
                '_id': 'twitch_info',
                'viewer_count': await Functions.convert_number(stats['viewer_count'], True),
                'stream_count': await Functions.convert_number(stats['stream_count'], True),
                'average_viewer_count': await Functions.convert_number(stats['average_viewer_count'], True),
                'category_rank': await Functions.convert_number(stats['category_rank'], True),
                'image': image,
                'updated_at': await Functions.convert_number(time.time(), True)
            }
            # Create json from data - Top Streamers
            data['top_streamers'] = {}
            for entry in top:
                data['top_streamers'][str(entry)] = {
                    'streamer': top[entry]['streamer'],
                    'viewer_count': await Functions.convert_number(top[entry]['viewer_count'], True),
                    'follower_count': await Functions.convert_number(top[entry]['follower_count'], True),
                    'link': top[entry]['link'],
                    'title': top[entry]['title'],
                    'language': top[entry]['language'],
                    'thumbnail': top[entry]['thumbnail'],
                    'started_at': top[entry]['started_at']
                }
            # Update database
            if db_available:
                db[DB_NAME]['twitch'].update_one({'_id': 'twitch_info'}, {'$set': data}, upsert=True)
            # Update json
            with open(f"{buffer_folder}twitch_info.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=4)

        while not shutdown:
            await function()
            try:
                await asyncio.sleep(60*5)
            except asyncio.CancelledError:
                pass


#Info
class Info():
    async def rankreset(interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{api_base}rankreset') as resp:
                data = await resp.json()
        embed = discord.Embed(description=f"{await Functions.translate(interaction, 'The next rank reset will take place on the following date: ')}\n<t:{data['rankreset']}>.", color=0x0400ff)
        await interaction.response.send_message(embed=embed)


    async def event(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        lang = await Functions.get_language_code(interaction)

        data = await Functions.data_load('events', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, 'The event data could not be loaded.'), ephemeral=True)
            return
        current_event = None
        upcoming_event = None

        for event in data:
            if event == '_id':
                continue
            start_time = data[event]['start']
            end_time = data[event]['end']
            now = time.time()
            if start_time <= now <= end_time:
                current_event = event
                break
            elif now < start_time and (upcoming_event is None or data[event]['start'] > start_time):
                upcoming_event = event

        if current_event is not None:
            embed = discord.Embed(title="Event", description=await Functions.translate(interaction, "Currently there is a event in DeadByDaylight.")+" <a:hyperWOW:1032389458319913023>", color=0x922f2f)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Name"), value=data[current_event]['name'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Type"), value=data[current_event]['type'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Bloodpoint Multiplier"), value=data[current_event]['multiplier'], inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Beginning"), value=str(await Functions.convert_time(data[current_event]['start'])+' UTC'), inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Ending"), value=str(await Functions.convert_time(data[current_event]['end'])+' UTC'), inline=True)
            await interaction.followup.send(embed=embed)
        elif upcoming_event is not None:
            embed = discord.Embed(title="Event", description=await Functions.translate(interaction, "There is a upcoming event in DeadByDaylight.")+" <a:SmugDance:1032349729167790090>", color=0x922f2f)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Name"), value=data[upcoming_event]['name'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Type"), value=data[upcoming_event]['type'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Bloodpoint Multiplier"), value=data[upcoming_event]['multiplier'], inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Beginning"), value=str(await Functions.convert_time(data[upcoming_event]['start'])+' UTC'), inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Ending"), value=str(await Functions.convert_time(data[upcoming_event]['end'])+' UTC'), inline=True)
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(title="Event", description=await Functions.translate(interaction, "Currently there is no event in DeadByDaylight.\nAnd none are planned.")+" <:pepe_sad:1032389746284056646>", color=0x922f2f)
            await interaction.followup.send(embed=embed)


    async def playerstats(interaction: discord.Interaction, steamid):
        await interaction.response.defer(thinking=True)
        check = await Functions.check_for_dbd(steamid, STEAMAPIKEY)
        try:
            int(check[0])
        except:
            embed = discord.Embed(title=await Functions.translate(interaction, 'Try again'), description=await Functions.translate(interaction, check[1]), color=0x004cff)
            await interaction.followup.send(embed=embed)
            return
        if check[0] == 1:
            await interaction.followup.send(await Functions.translate(interaction, 'The SteamID64 has to be 17 chars long and only containing numbers.'), ephemeral=True)
        elif check[0] == 2:
            await interaction.followup.send(await Functions.translate(interaction, 'This SteamID64 is NOT in use.'), ephemeral=True)
        elif check[0] == 3:
            await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f"\n[here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
        elif check[0] == 4:
            await interaction.followup.send(await Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look")+" [here](https://www.g2a.com/n/dbdstats).")
        elif check[0] == 5:
            embed1=discord.Embed(title="Fatal Error", description=await Functions.translate(interaction, "It looks like there was an error querying the SteamAPI (probably a rate limit).\nPlease join our")+" [Support-Server]("+str(await Functions.create_support_invite(interaction))+await Functions.translate(interaction, ") and create a ticket to tell us about this."), color=0xff0000)
            embed1.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.followup.send(embed=embed1, ephemeral=True)
        elif check[0] == 0:
            #Get Stats
            removed = await Functions.check_if_removed(check[1])
            clean_filename = os.path.basename(f'player_stats_{check[1]}.json')
            file_path = os.path.join(stats_folder, clean_filename)
            if removed == 1:
                embed1 = discord.Embed(title="Statistics", url=alt_playerstats+check[1], description=(await Functions.translate(interaction, "It looks like this profile has been banned from displaying on our leaderboard.\nThis probably happened because achievements or statistics were manipulated.\nI can therefore not display any information in an embed.\nIf you still want to see the full statistics, please click on the link.")), color=0xb19325)
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
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f'{api_base}playerstats?steamid={check[1]}') as resp:
                            player_stats = await resp.json()
                            with open(file_path, 'w', encoding='utf8') as f:
                                json.dump(player_stats, f, indent=2)
                else:
                    await interaction.followup.send(await Functions.translate(interaction, "The stats got loaded in the last 4h but I don't have a local copy. Try again in ~3-4h."), ephemeral=True)
                    return
                with open(file_path, 'r', encoding='utf8') as f:
                    player_stats = json.load(f)
            steam_data = await Functions.check_api_rate_limit(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAMAPIKEY}&steamids={check[1]}')
            if steam_data == 1 or player_stats == 1:
                await interaction.followup.send(await Functions.translate(interaction, "The bot got ratelimited. Please try again later. (This error can also appear if the same profile got querried multiple times in a 4h window.)"), ephemeral=True)
                return
            for event in steam_data['response']['players']:
                personaname = event['personaname']
                profileurl = event['profileurl']
                avatar = event['avatarfull']
            #Set embed headers
            embed1 = discord.Embed(title=await Functions.translate(interaction, "Statistics (1/10) - Survivor Stats"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed2 = discord.Embed(title=await Functions.translate(interaction, "Statistics (2/10) - Killer Interactions"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed3 = discord.Embed(title=await Functions.translate(interaction, "Statistics (3/10) - Healing/Saved"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed4 = discord.Embed(title=await Functions.translate(interaction, "Statistics (4/10) - Escaped"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed5 = discord.Embed(title=await Functions.translate(interaction, "Statistics (5/10) - Repaired second floor generator and escaped"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed6 = discord.Embed(title=await Functions.translate(interaction, "Statistics (6/10) - Killer Stats"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed7 = discord.Embed(title=await Functions.translate(interaction, "Statistics (7/10) - Hooked"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed8 = discord.Embed(title=await Functions.translate(interaction, "Statistics (8/10) - Powers"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed9 = discord.Embed(title=await Functions.translate(interaction, "Statistics (9/10) - Survivors downed"), description=personaname+'\n'+profileurl, color=0xb19325)
            embed10 = discord.Embed(title=await Functions.translate(interaction, "Statistics (10/10) - Survivors downed with power"), description=personaname+'\n'+profileurl, color=0xb19325)
            #Set Static Infos
            embeds = [embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed8, embed9, embed10]
            footer = (await Functions.translate(interaction, "Stats are updated every ~4h. | Last update: ")).replace('.|','. | ')+str(await Functions.convert_time(int(player_stats['updated_at'])))+" UTC"

            for embed in embeds:
                embed.set_thumbnail(url=avatar)
                embed.set_footer(text=footer)

            #Embed1 - Survivor
            embed1.add_field(name=await Functions.translate(interaction, "Bloodpoints Earned"), value=await Functions.convert_number(player_stats['bloodpoints']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Rank"), value=player_stats['survivor_rank'], inline=True)
            embed1.add_field(name="\u200b", value="\u200b", inline=False)
            embed1.add_field(name=await Functions.translate(interaction, "Full loadout Games"), value=await Functions.convert_number(player_stats['survivor_fullloadout']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Perfect Games"), value=await Functions.convert_number(player_stats['survivor_perfectgames']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Generators repaired"), value=await Functions.convert_number(player_stats['gensrepaired']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Gens without Perks"), value=await Functions.convert_number(player_stats['gensrepaired_noperks']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Damaged gens repaired"), value=await Functions.convert_number(player_stats['damagedgensrepaired']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Successful skill checks"), value=await Functions.convert_number(player_stats['skillchecks']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Items Depleted"), value=await Functions.convert_number(player_stats['itemsdepleted']), inline=False)
            embed1.add_field(name=await Functions.translate(interaction, "Hex Totems Cleansed"), value=await Functions.convert_number(player_stats['hextotemscleansed']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Hex Totems Blessed"), value=await Functions.convert_number(player_stats['hextotemsblessed']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Blessed Boosts"), value=await Functions.convert_number(player_stats['blessedtotemboosts']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Exit Gates Opened"), value=await Functions.convert_number(player_stats['exitgatesopened']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Hooks Sabotaged"), value=await Functions.convert_number(player_stats['hookssabotaged']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Chests Searched"), value=await Functions.convert_number(player_stats['chestssearched']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Chests Searched in the Basement"), value=await Functions.convert_number(player_stats['chestssearched_basement']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Mystery boxes opened"), value=await Functions.convert_number(player_stats['mysteryboxesopened']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Killers aura revealed"), value=await Functions.convert_number(player_stats['killersaurarevealed']), inline=True)
            embed1.add_field(name=await Functions.translate(interaction, "Screams"), value=await Functions.convert_number(player_stats['screams']), inline=True)
            #Embed2 - Killer Interactions
            embed2.add_field(name="\u200b", value="\u200b", inline=False)
            embed2.add_field(name=await Functions.translate(interaction, "Dodged basic attack or projectiles"), value=await Functions.convert_number(player_stats['dodgedattack']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Escaped chase after pallet stun"), value=await Functions.convert_number(player_stats['escapedchase_palletstun']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Escaped chase injured after hit"), value=await Functions.convert_number(player_stats['escapedchase_healthyinjured']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Escape chase by hiding in locker"), value=await Functions.convert_number(player_stats['escapedchase_hidinginlocker']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Protection hits for unhooked survivor"), value=await Functions.convert_number(player_stats['protectionhits_unhooked']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Protectionhits while a survivor is carried"), value=await Functions.convert_number(player_stats['protectionhits_whilecarried']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Vaults while in chase"), value=await Functions.convert_number(player_stats['vaultsinchase']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Dodge attack before vaulting"), value=await Functions.convert_number(player_stats['vaultsinchase_missed']), inline=True)
            embed2.add_field(name=await Functions.translate(interaction, "Wiggled from killers grasp"), value=await Functions.convert_number(player_stats['wiggledfromkillersgrasp']), inline=True)
            #Embed3 - Healing/Saves
            embed3.add_field(name="\u200b", value="\u200b", inline=False)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors healed"), value=await Functions.convert_number(player_stats['survivorshealed']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors healed while injured"), value=await Functions.convert_number(player_stats['survivorshealed_whileinjured']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors healed while 3 others not healthy"), value=await Functions.convert_number(player_stats['survivorshealed_threenothealthy']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors healed who found you while injured"), value=await Functions.convert_number(player_stats['survivorshealed_foundyou']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors healed from dying state to injured"), value=await Functions.convert_number(player_stats['healeddyingtoinjured']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Obsessions healed"), value=await Functions.convert_number(player_stats['obsessionshealed']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors saved (from death)"), value=await Functions.convert_number(player_stats['saved']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Survivors saved during endgame"), value=await Functions.convert_number(player_stats['saved_endgame']), inline=True)
            embed3.add_field(name=await Functions.translate(interaction, "Killers pallet stunned while carrying a survivor"), value=await Functions.convert_number(player_stats['killerstunnedpalletcarrying']), inline=True)
            embed3.add_field(name="Kobed", value=await Functions.convert_number(player_stats['unhookedself']), inline=True)
            #Embed4 - Escaped
            embed4.add_field(name="\u200b", value="\u200b", inline=False)
            embed4.add_field(name=await Functions.translate(interaction, "While healthy/injured"), value=await Functions.convert_number(player_stats['escaped']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "While crawling"), value=await Functions.convert_number(player_stats['escaped_ko']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "After kobed"), value=await Functions.convert_number(player_stats['hooked_escape']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "Through the hatch"), value=await Functions.convert_number(player_stats['escaped_hatch']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "Through the hatch while crawling"), value=await Functions.convert_number(player_stats['escaped_hatchcrawling']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "Through the hatch with everyone"), value=await Functions.convert_number(player_stats['escaped_allhatch']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "After been downed once"), value=await Functions.convert_number(player_stats['escaped_downedonce']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "After been injured for half of the trial"), value=await Functions.convert_number(player_stats['escaped_injuredhalfoftrail']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "With no bloodloss as obsession"), value=await Functions.convert_number(player_stats['escaped_nobloodlossobsession']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "Last gen last survivor"), value=await Functions.convert_number(player_stats['escaped_lastgenlastsurvivor']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "With new item"), value=await Functions.convert_number(player_stats['escaped_newitem']), inline=True)
            embed4.add_field(name=await Functions.translate(interaction, "With item from someone else"), value=await Functions.convert_number(player_stats['escaped_withitemfrom']), inline=True)
            #Embed5 - Repaired second floor generator and escaped
            embed5.add_field(name="\u200b", value="\u200b", inline=False)
            embed5.add_field(name="Disturbed Ward", value=await Functions.convert_number(player_stats['secondfloorgen_disturbedward']), inline=True)
            embed5.add_field(name="Father Campbells Chapel", value=await Functions.convert_number(player_stats['secondfloorgen_fathercampbellschapel']), inline=True)
            embed5.add_field(name="Mothers Dwelling", value=await Functions.convert_number(player_stats['secondfloorgen_mothersdwelling']), inline=True)
            embed5.add_field(name="Temple of Purgation", value=await Functions.convert_number(player_stats['secondfloorgen_templeofpurgation']), inline=True)
            embed5.add_field(name="The Game", value=await Functions.convert_number(player_stats['secondfloorgen_game']), inline=True)
            embed5.add_field(name="Family Residence", value=await Functions.convert_number(player_stats['secondfloorgen_familyresidence']), inline=True)
            embed5.add_field(name="Sanctum of Wrath", value=await Functions.convert_number(player_stats['secondfloorgen_sanctumofwrath']), inline=True)
            embed5.add_field(name="Mount Ormond", value=await Functions.convert_number(player_stats['secondfloorgen_mountormondresort']), inline=True)
            embed5.add_field(name="Lampkin Lane", value=await Functions.convert_number(player_stats['secondfloorgen_lampkinlane']), inline=True)
            embed5.add_field(name="Pale Rose", value=await Functions.convert_number(player_stats['secondfloorgen_palerose']), inline=True)
            embed5.add_field(name="Hawkins", value=await Functions.convert_number(player_stats['secondfloorgen_undergroundcomplex']), inline=True)
            embed5.add_field(name="Treatment Theatre", value=await Functions.convert_number(player_stats['secondfloorgen_treatmenttheatre']), inline=True)
            embed5.add_field(name="Dead Dawg Saloon", value=await Functions.convert_number(player_stats['secondfloorgen_deaddawgsaloon']), inline=True)
            embed5.add_field(name="Midwich", value=await Functions.convert_number(player_stats['secondfloorgen_midwichelementaryschool']), inline=True)
            embed5.add_field(name="Raccoon City", value=await Functions.convert_number(player_stats['secondfloorgen_racconcitypolicestation']), inline=True)
            embed5.add_field(name="Eyrie of Crows", value=await Functions.convert_number(player_stats['secondfloorgen_eyrieofcrows']), inline=True)
            embed5.add_field(name="Garden of Joy", value=await Functions.convert_number(player_stats['secondfloorgen_gardenofjoy']), inline=True)
            embed5.add_field(name="Shattered Square", value=await Functions.convert_number(player_stats['secondfloorgen_shatteredsquare']), inline=True)
            embed5.add_field(name="Shelter Woods", value=await Functions.convert_number(player_stats['secondfloorgen_shelterwoods']), inline=True)
            embed5.add_field(name="Toba Landing", value=await Functions.convert_number(player_stats['secondfloorgen_tobalanding']), inline=True)
            embed5.add_field(name="Nostromo Wreckage", value=await Functions.convert_number(player_stats['secondfloorgen_messhall']), inline=True)
            #Embed6 - Killer Stats
            embed6.add_field(name=await Functions.translate(interaction, "Rank"), value=player_stats['killer_rank'], inline=True)
            embed6.add_field(name="\u200b", value="\u200b", inline=False)
            embed6.add_field(name=await Functions.translate(interaction, "Played with full loadout"), value=await Functions.convert_number(player_stats['killer_fullloadout']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Perfect Games"), value=await Functions.convert_number(player_stats['killer_perfectgames']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Survivors Killed"), value=await Functions.convert_number(player_stats['killed']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Survivors Sacrificed"), value=await Functions.convert_number(player_stats['sacrificed']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Sacrificed all before last gen"), value=await Functions.convert_number(player_stats['sacrificed_allbeforelastgen']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Killed/Sacrificed after last gen"), value=await Functions.convert_number(player_stats['killed_sacrificed_afterlastgen']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Killed all 4 with tier 3 Myers"), value=await Functions.convert_number(player_stats['killed_allevilwithin']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Obsessions Sacrificed"), value=await Functions.convert_number(player_stats['sacrificed_obsessions']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Hatches Closed"), value=await Functions.convert_number(player_stats['hatchesclosed']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Gens damaged while 1-4 survivors are hooked"), value=await Functions.convert_number(player_stats['gensdamagedwhileonehooked']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Gens damaged while undetectable"), value=await Functions.convert_number(player_stats['gensdamagedwhileundetectable']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Grabbed while repairing a gen"), value=await Functions.convert_number(player_stats['survivorsgrabbedrepairinggen']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Grabbed while you are hiding in locker"), value=await Functions.convert_number(player_stats['survivorsgrabbedfrominsidealocker']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Hit one who dropped a pallet in chase"), value=await Functions.convert_number(player_stats['survivorshit_droppingpalletinchase']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Hit while carrying"), value=await Functions.convert_number(player_stats['survivorshit_whilecarrying']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Interrupted cleansing"), value=await Functions.convert_number(player_stats['survivorsinterruptedcleansingtotem']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Vaults while in chase"), value=await Functions.convert_number(player_stats['vaultsinchase_askiller']), inline=True)
            embed6.add_field(name=await Functions.translate(interaction, "Survivors made scream"), value=await Functions.convert_number(player_stats['survivorscreams']), inline=True)
            #Embed7 - Hooked
            embed7.add_field(name="\u200b", value="\u200b", inline=False)
            embed7.add_field(name=await Functions.translate(interaction, "Suvivors hooked before a generator is repaired"), value=await Functions.convert_number(player_stats['survivorshookedbeforegenrepaired']), inline=True)
            embed7.add_field(name=await Functions.translate(interaction, "Survivors hooked during end game collapse"), value=await Functions.convert_number(player_stats['survivorshookedendgamecollapse']), inline=True)
            embed7.add_field(name=await Functions.translate(interaction, "Hooked a survivor while 3 other survivors were injured"), value=await Functions.convert_number(player_stats['hookedwhilethreeinjured']), inline=True)
            embed7.add_field(name=await Functions.translate(interaction, "3 Survivors hooked in basement"), value=await Functions.convert_number(player_stats['survivorsthreehookedbasementsametime']), inline=True)
            embed7.add_field(name="\u200b", value="\u200b", inline=True)
            embed7.add_field(name=await Functions.translate(interaction, "Survivors hooked in basement"), value=await Functions.convert_number(player_stats['survivorshookedinbasement']), inline=True)
            #Embed8 - Powers
            embed8.add_field(name="\u200b", value="\u200b", inline=False)
            embed8.add_field(name=await Functions.translate(interaction, "Beartrap Catches"), value=await Functions.convert_number(player_stats['beartrapcatches']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Uncloak Attacks"), value=await Functions.convert_number(player_stats['uncloakattacks']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Chainsaw Hits  (Billy)"), value=await Functions.convert_number(player_stats['chainsawhits']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Blink Attacks"), value=await Functions.convert_number(player_stats['blinkattacks']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Phantasms Triggered"), value=await Functions.convert_number(player_stats['phantasmstriggered']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Hit each survivor after teleporting to phantasm trap"), value=await Functions.convert_number(player_stats['survivorshit_afterteleporting']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Evil Within Tier Ups"), value=await Functions.convert_number(player_stats['evilwithintierup']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Shock Therapy Hits"), value=await Functions.convert_number(player_stats['shocked']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Trials with all survivors in madness tier 3"), value=await Functions.convert_number(player_stats['survivorsallmaxmadness']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Hatchets Thrown"), value=await Functions.convert_number(player_stats['hatchetsthrown']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Pulled into Dream State"), value=await Functions.convert_number(player_stats['dreamstate']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Reverse Bear Traps Placed"), value=await Functions.convert_number(player_stats['rbtsplaced']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Cages of Atonement"), value=await Functions.convert_number(player_stats['cagesofatonement']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Lethal Rush Hits"), value=await Functions.convert_number(player_stats['lethalrushhits']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Lacerations"), value=await Functions.convert_number(player_stats['lacerations']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Possessed Chains"), value=await Functions.convert_number(player_stats['possessedchains']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Condemned"), value=await Functions.convert_number(player_stats['condemned']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Slammed"), value=await Functions.convert_number(player_stats['slammedsurvivors']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Damaged while pursued by Guard"), value=await Functions.convert_number(player_stats['survivorsdamagedpursuedbyguard']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Tailattacks"), value=await Functions.convert_number(player_stats['tailattacks']), inline=True)
            embed8.add_field(name=await Functions.translate(interaction, "Survivor hit 3 sec after scamper"), value=await Functions.convert_number(player_stats['survivorshit_scamper']), inline=True)
            #Embed9 - Survivors downed
            embed9.add_field(name="\u200b", value="\u200b", inline=False)
            embed9.add_field(name=await Functions.translate(interaction, "Downed while hindered"), value=await Functions.convert_number(player_stats['survivorsdowned_hindered']), inline=True)
            embed9.add_field(name=await Functions.translate(interaction, "Downed while suffering from oblivious"), value=await Functions.convert_number(player_stats['survivorsdowned_oblivious']), inline=True)
            embed9.add_field(name=await Functions.translate(interaction, "Downed while Exposed"), value=await Functions.convert_number(player_stats['survivorsdowned_exposed']), inline=True)
            embed9.add_field(name=await Functions.translate(interaction, "Downed while carrying a survivor"), value=await Functions.convert_number(player_stats['survivorsdowned_whilecarrying']), inline=True)
            embed9.add_field(name="\u200b", value="\u200b", inline=True)
            embed9.add_field(name=await Functions.translate(interaction, "Downed near a raised pallet"), value=await Functions.convert_number(player_stats['survivorsdowned_nearraisedpallet']), inline=True)
            #Embed10 - Survivors downed with power
            embed10.add_field(name="\u200b", value="\u200b", inline=False)
            embed10.add_field(name=await Functions.translate(interaction, "Downed with a Hatchet (24+ meters)"), value=await Functions.convert_number(player_stats['survivorsdowned_hatchets']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed with a Chainsaw (Bubba)"), value=await Functions.convert_number(player_stats['survivorsdowned_chainsaw']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while Intoxicated"), value=await Functions.convert_number(player_stats['survivorsdowned_intoxicated']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed after Haunting"), value=await Functions.convert_number(player_stats['survivorsdowned_haunting']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while in Deep Wound"), value=await Functions.convert_number(player_stats['survivorsdowned_deepwound']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while having max sickness"), value=await Functions.convert_number(player_stats['survivorsdowned_maxsickness']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while marked (Ghostface)"), value=await Functions.convert_number(player_stats['survivorsdowned_marked']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while using Shred"), value=await Functions.convert_number(player_stats['survivorsdowned_shred']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while using Blood Fury"), value=await Functions.convert_number(player_stats['survivorsdowned_bloodfury']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while Speared"), value=await Functions.convert_number(player_stats['survivorsdowned_speared']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while Victor is clinging to them"), value=await Functions.convert_number(player_stats['survivorsdowned_victor']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while contaminated"), value=await Functions.convert_number(player_stats['survivorsdowned_contaminated']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while using Dire Crows"), value=await Functions.convert_number(player_stats['survivorsdowned_direcrows']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed while exposed by Lock On"), value=await Functions.convert_number(player_stats['survivorsdowned_lockon']), inline=True)
            embed10.add_field(name=await Functions.translate(interaction, "Downed during nightfall"), value=await Functions.convert_number(player_stats['survivorsdowned_nightfall']), inline=True)
            #Send Statistics
            await interaction.edit_original_response(embeds=[embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed8, embed9, embed10])


    async def character(interaction: discord.Interaction, char: str):
        await interaction.response.defer(thinking = True)
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('chars', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error. Try again later."))
            return
        dlc_data = await Functions.data_load('dlcs', lang)
        if dlc_data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error. Try again later."))
            return
        else:
            await Functions.char_send(interaction, data, char, dlc_data, lang)
            return


    async def dlc(interaction: discord.Interaction, name: str = ''):
        await interaction.response.defer(thinking=True)
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('dlcs', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error. Try again later."))
            return
        if not name:
            data.pop('_id', None)
            data = dict(sorted(data.items(), key=lambda x: x[1]['time']))

            num_entries = sum(1 for key in data.keys() if key != '_id')

            max_fields_per_embed = 24

            num_embeds = math.ceil(num_entries / max_fields_per_embed)

            embed_description = (await Functions.translate(interaction, "Here is a list of all DLCs. Click the link to go to the steam storepage."))

            embeds = []
            for i in range(num_embeds):
                start_index = i * max_fields_per_embed
                end_index = min(start_index + max_fields_per_embed, num_entries)
                embed_title = f"DLC Info ({i+1}/{num_embeds})" if num_embeds > 1 else "DLC Info"
                embed = discord.Embed(title=embed_title, description=embed_description, color=0xb19325)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                j = 0
                for key in data.keys():
                    if key == '_id':
                        continue
                    if data[key]['steamid'] == 0:
                        continue
                    if j < start_index:
                        j += 1
                        continue
                    if j >= end_index:
                        break
                    embed.add_field(name=str(data[key]['name']), value=f"[{await Functions.convert_time(data[key]['time'], 'date')}]({steamStore}{str(data[key]['steamid'])})", inline=True)
                    j += 1
                embeds.append(embed)
            await interaction.followup.send(embeds=embeds)
        else:
            for key in data.keys():
                if str(key) == '_id':
                    continue
                if data[key]['name'].lower().replace('chapter', '').replace('®', '').replace('™', '').strip() == name.lower().replace('chapter', '').replace('®', '').replace('™', '').strip():
                    embed = discord.Embed(title="DLC description for '"+data[key]['name']+"'", description=await Functions.translate(interaction, str(data[key]['description']).replace('<br><br>', ' ').replace('&nbsp;', '')), color=0xb19325)
                    embed.set_thumbnail(url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{data[key]['steamid']}/header.jpg")
                    embed.set_footer(text = f"{await Functions.translate(interaction, 'Released at')}: {await Functions.convert_time(data[key]['time'], 'date')}")
                    await interaction.followup.send(embed=embed)
                    return
            await interaction.followup.send(await Functions.translate(interaction, "No DLC found with this name."))


    async def item(interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('items', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading the item data."))
            return

        await Functions.item_send(interaction, name, lang)
        return


    async def maps(interaction: discord.Interaction, name):
        await interaction.response.defer(thinking=True)
        lang = await Functions.get_language_code(interaction)

        data = await Functions.data_load('maps', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading map-data. Please try again later."))
            return
        for key, value in data.items():
            if key == 'Swp_Mound' or key == '_id':
                continue
            if value['name'].lower() == name.lower():
                embed = discord.Embed(title=f"Map description for '{value['name']}'", description=await Functions.translate(interaction, str(value['description']).replace('<br><br>', ' ')), color=0xb19325)
                embed.set_thumbnail(url=f"{map_portraits}{key}.png")
                await interaction.followup.send(embed=embed)


    async def offering(interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('offerings', 'en')
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading the perk data."), ephemeral=True)
            return
        await Functions.offering_send(interaction, name, lang)


    async def perk(interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        lang = await Functions.get_language_code(interaction)
        await Functions.perk_send(name, lang, interaction)


    async def killswitch(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        if os.path.exists(f'{buffer_folder}killswitch.json'):
            if os.path.getmtime(f'{buffer_folder}killswitch.json') > time.time() - 900:
                with open(f'{buffer_folder}killswitch.json', 'r') as f:
                    data = json.load(f)
                    if data['killswitch_on'] == 0:
                        embed = discord.Embed(title="Killswitch", description=(await Functions.translate(interaction, 'Currently there is no Kill Switch active.')), color=0xb19325)
                        embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
                        embed.set_footer(text = f'Update every 15 minutes.')
                        await interaction.followup.send(embed=embed)
                        return
                    else:
                        embed = discord.Embed(title="Killswitch", description=data['md'], color=0xb19325)
                        embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
                        embed.set_footer(text = f'Update every 15 minutes.')
                        await interaction.followup.send(embed=embed)
                        return
        try:
            data = await killswitch.get_killswitch('md')
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral = True)
            return

        if data.replace('\n', '').strip() == '':
            embed = discord.Embed(title="Killswitch", description=(await Functions.translate(interaction, 'Currently there is no Kill Switch active.')), color=0xb19325)
            embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
            embed.set_footer(text = f'Update every 15 minutes.')
            await interaction.followup.send(embed=embed)
            killswitch_on = 0
        elif data is not None:
            embed = discord.Embed(title="Killswitch", description=data, color=0xb19325)
            embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
            embed.set_footer(text = f'Update every 15 minutes.')
            await interaction.followup.send(embed=embed)
            killswitch_on = 1

        data_to_save = {
            'md': data,
            'killswitch_on': killswitch_on
            }

        with open(f'{buffer_folder}killswitch.json', 'w') as f:
            json.dump(data_to_save, f, indent=4)


    async def shrine(interaction: discord.Interaction = None, channel_id: tuple = ''):
        if channel_id != '':
            channel = await Functions.get_or_fetch('channel', channel_id[1])
            if channel is None:
                manlogger.info(f"Channel <#{channel_id[1]}> not found. Removing from db.")
                c.execute(f"DELETE FROM shrine WHERE channel_id = {channel_id[1]}")
                conn.commit()
                return
            guild: discord.Guild = await Functions.get_or_fetch('guild', channel_id[0])
            if guild is None:
                manlogger.info(f"Guild {channel_id[0]} not found. Removing from db.")
                c.execute(f"DELETE FROM shrine WHERE guild_id = {channel_id[0]}")
                conn.commit()
                return
            data = await Functions.data_load('shrine')
            if data is None:
                return
            embeds = []
            for shrine in data['data']['perks']:
                print(shrine)
                shrine_embed = await Functions.perk_send(shrine['name'], guild.preferred_locale[1][:2], None, shrine=True)
                shrine_embed.set_footer(text=f"Bloodpoints: {await Functions.convert_number(shrine['bloodpoints'])} | Shards: {await Functions.convert_number(shrine['shards'])}\n{await Functions.translate(guild, 'Usage by players')}: {await Functions.translate(guild, shrine['usage_tier'])}")
                embeds.append(shrine_embed)
            await channel.send(content = f"This is the current shrine.\nIt started at <t:{Functions.convert_to_unix_timestamp(data['data']['start'])}> and will last until <t:{Functions.convert_to_unix_timestamp(data['data']['end'])}>.\nUpdates every 15 minutes.", embeds=embeds)
            return
        else:
            await interaction.response.defer(thinking=True)
            lang = await Functions.get_language_code(interaction)
            data = await Functions.data_load('shrine')
            if data is None:
                await interaction.followup.send(await Functions.translate(interaction, "Error while loading the shrine data."))
                return
            perk_data = await Functions.data_load('perks', lang)
            perk_data_en = await Functions.data_load('perks')
            if perk_data is None:
                await interaction.followup.send(await Functions.translate(interaction, "Error while loading the perk data."))
                return
            embeds = []
            for shrine in data['data']['perks']:
                print(shrine)
                shrine_perk_name = Functions.find_key_by_name(shrine['name'], perk_data_en)
                shrine_embed = await Functions.perk_send(shrine_perk_name, lang, interaction, True)
                shrine_embed.set_footer(text=f"Bloodpoints: {await Functions.convert_number(shrine['bloodpoints'])} | Shards: {await Functions.convert_number(shrine['shards'])}\n{await Functions.translate(interaction, 'Usage by players')}: {await Functions.translate(interaction, shrine['usage_tier'])}")
                embeds.append(shrine_embed)
            await interaction.followup.send(content = f"This is the current shrine.\nIt started at <t:{Functions.convert_to_unix_timestamp(data['data']['start'])}> and will last until <t:{Functions.convert_to_unix_timestamp(data['data']['end'])}>.\nUpdates every 15 minutes.", embeds=embeds)


    async def version(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        data = await Functions.data_load('versions')

        embed1 = discord.Embed(title='DB Version (1/2)', color=0x42a32e)
        embed1.add_field(name=await Functions.translate(interaction, 'Name'), value='\u200b', inline=True)
        embed1.add_field(name=await Functions.translate(interaction, 'Version'), value='\u200b', inline=True)
        embed1.add_field(name=await Functions.translate(interaction, 'Last Update'), value='\u200b', inline=True)
        embed2 = discord.Embed(title='DB Version (2/2)', color=0x42a32e)
        embed2.add_field(name=await Functions.translate(interaction, 'Name'), value='\u200b', inline=True)
        embed2.add_field(name=await Functions.translate(interaction, 'Version'), value='\u200b', inline=True)
        embed2.add_field(name=await Functions.translate(interaction, 'Last Update'), value='\u200b', inline=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(api_base+'versions') as resp:
                data = await resp.json()
        i = 0
        for key in data.keys():
            i += 1
            if i <= 5:
                embed1.add_field(name='\u200b', value=key.capitalize(), inline=True)
                embed1.add_field(name='\u200b', value=data[key]['version'], inline=True)
                embed1.add_field(name='\u200b', value=str(await Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
            if i >= 6:
                embed2.add_field(name='\u200b', value=key.capitalize(), inline=True)
                embed2.add_field(name='\u200b', value=data[key]['version'], inline=True)
                embed2.add_field(name='\u200b', value=str(await Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
        await interaction.followup.send(embeds=[embed1, embed2])


    async def playercount(interaction: discord.Interaction):
        async def selfembed(data):
            embed = discord.Embed(title=await Functions.translate(interaction, "Playercount"), color=0xb19325)
            embed.set_thumbnail(url=f"{bot_base}dbd.png")
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Current"), value=await Functions.convert_number(int(data['Current Players'])), inline=True)
            embed.add_field(name=await Functions.translate(interaction, "24h Peak"), value=await Functions.convert_number(int(data['Peak Players 24h'])), inline=True)
            embed.add_field(name=await Functions.translate(interaction, "All-time Peak"), value=await Functions.convert_number(int(data['Peak Players All Time'])), inline=True)
            embed.set_footer(text=await Functions.translate(interaction, "This will be updated every full hour."))
            await interaction.followup.send(embed = embed)
        async def selfget():
            data = await steamcharts.playercount('381210')
            try:
                current_players = data['Current Players']
                day_peak = data['Peak Players 24h']
                alltime_peak = data['Peak Players All Time']
            except:
                error_code = data['error']['code']
                error_message = data['error']['message']
                pt(f"Error while getting the playercount. Error Code: {error_code} | Error Message: {error_message}")
                manlogger.warning(f"Error while getting the playercount. Error Code: {error_code} | Error Message: {error_message}")
                await interaction.followup.send(f"Error while getting the playercount. Error Code: {error_code} | Error Message: {error_message}")
                return
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
        await interaction.response.defer(thinking=True)
        dbd_check = await Functions.check_for_dbd(steamid, STEAMAPIKEY)
        if dbd_check[0] == 1:
            await interaction.followup.send(await Functions.translate(interaction, 'The SteamID64 has to be 17 chars long and only containing numbers.'))
        elif dbd_check[0] == 2:
            await interaction.followup.send(await Functions.translate(interaction, 'This SteamID64 is NOT in use.'))
        elif dbd_check[0] == 3:
            await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f"\n[here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
        elif dbd_check[0] == 4:
            await interaction.followup.send(await Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look") + " [here](https://www.g2a.com/n/dbdstats).")
        elif dbd_check[0] == 5:
            embed1 = discord.Embed(title="Fatal Error", description=await Functions.translate(interaction, "It looks like there was an error querying the SteamAPI (probably a rate limit).\nPlease join our") + f" [Support-Server]({str(await Functions.create_support_invite(interaction))})" + await Functions.translate(interaction, ") and create a ticket to tell us about this."), color=0xff0000)
            embed1.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.followup.send(embed=embed1)
        elif dbd_check[0] == 0:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={STEAMAPIKEY}&steamid={dbd_check[1]}&appid=381210') as resp:
                    data = await resp.json()
            if data['playerstats']['success'] == False:
                await interaction.followup.send(await Functions.translate(interaction, 'This profile is private.'))
                return
            for entry in data['playerstats']['achievements']:
                if entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 1 and int(entry['unlocktime']) < 1480017600:
                    await interaction.followup.send(await Functions.translate(interaction, 'This player has probably legit legacy.'))
                    return
                elif entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 1 and int(entry['unlocktime']) > 1480017600:
                    await interaction.followup.send(await Functions.translate(interaction, 'If this player has legacy, they are probably hacked.'))
                    return
                elif entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 0:
                    await interaction.followup.send(await Functions.translate(interaction, "This player doesn't even have one character prestiged."))
                    return


    async def addon(interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('addons', lang)
        if data is None:
            await interaction.followup.send("Error while loading the addon data.")
            return
        embed = await Functions.addon_send(name, lang, interaction)
        if embed is None:
            await interaction.followup.send(f"There is no addon named {name}.")
        return


    async def twitch_info(interaction: discord.Interaction):
        if not twitch_available:
            await interaction.response.send_message("Twitch API is currently not available.\nAsk the owner of this instance to enable it.", ephemeral=True)
            return

        data = await Functions.data_load('twitch')

        embeds = []

        embed = discord.Embed(title=f"Twitch Info - <t:{data['updated_at']}>", url="https://www.twitch.tv/directory/game/Dead%20by%20Daylight", description="Statistics", color=0xff00ff)
        embed.set_thumbnail(url=data['image'])
        embed.set_footer(text=f"Update every 5 minutes.")
        embed.add_field(name="Total Viewers", value=await Functions.convert_number(data['viewer_count']), inline=True)
        embed.add_field(name="Total Streams", value=await Functions.convert_number(data['stream_count']), inline=True)
        embed.add_field(name="\u00D8 Viewer/Stream", value=await Functions.convert_number(data['average_viewer_count']), inline=True)
        embed.add_field(name="Current Rank", value=await Functions.convert_number(data['category_rank']), inline=False)
        embeds.append(embed)
        for streamer in data['top_streamers'].values():
            embed = discord.Embed(title=streamer['streamer'], description=streamer['title'], color=0xffb8ff)
            embed.set_thumbnail(url=streamer['thumbnail'])
            embed.add_field(name="Viewer", value=await Functions.convert_number(streamer['viewer_count']), inline=True)
            embed.add_field(name="Follower", value=await Functions.convert_number(streamer['follower_count']), inline=True)
            embed.add_field(name="\u200b", value=f"[Stream]({streamer['link']})", inline=True)
            embed.add_field(name="Language", value=await Functions.get_language_name(streamer['language']), inline=True)
            embed.set_footer(text=f"Started at: {streamer['started_at']}")
            embeds.append(embed)

        await interaction.response.send_message(embeds=embeds)


    async def patch(interaction: discord.Interaction):
        # If the patchnotes are older than 2 hours, update them
        if os.path.isfile(f'{buffer_folder}patchnotes.md') and time.time() - os.path.getmtime(f'{buffer_folder}patchnotes.md') < 7200:
            await interaction.response.send_message(content = 'Here are the current patchnotes.\nThey get updated at least every 2 hours.', file = discord.File(f'{buffer_folder}patchnotes.md'))
        else:
            await interaction.response.defer(thinking=True)

            data = await patchnotes.get_update_content(return_type = 'md')

            with open(f'{buffer_folder}patchnotes.md', 'w', encoding='utf-8') as f:
                f.write(data)
            await interaction.followup.send(content = 'Here are the current patchnotes.\nThey get updated at least every 2 hours.', file = discord.File(f'{buffer_folder}patchnotes.md'))


#Random
class Random():
    async def perk(interaction: discord.Interaction, amount, role, lang, loadout: bool = False):
        if not loadout:
            await interaction.response.send_message(f'Selecting {amount} perks for {role}...\nThis will take a while. Especially when the translation is activated.', ephemeral=True)
        perks = await Functions.data_load('perks', lang)
        if perks is None:
            await interaction.followup.send("Error while loading the perk data.")
            return
        keys = list(perks.keys())
        if '_id' in keys:
            keys.remove('_id')
        role_keys = [key for key in keys if perks[key]['role'] == role]
        random.shuffle(role_keys)
        embeds = []
        for key in role_keys:
            if len(embeds) >= amount:
                break
            entry = perks[key]
            print(entry['name'])
            embed = await Functions.perk_send(entry['name'], lang, interaction, False, True)
            embeds.append(embed)
        if not embeds:
            await interaction.followup.send(f"No perks found for {role}.", ephemeral=True)
            return
        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral=True)


    async def offering(interaction: discord.Interaction, role, lang, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking=True, ephemeral=True)
        offerings = await Functions.data_load('offerings', lang)
        if offerings is None:
            await interaction.followup.send("Error while loading the offering data.", ephemeral = True)
            return
        else:
            keys = list(offerings.keys())
            if '_id' in keys:
                keys.remove('_id')
            valid_keys = [key for key in keys if offerings[key]['retired'] != 1 and (offerings[key]['role'] == role or offerings[key]['role'] is None)]
            random.shuffle(valid_keys)
            if not valid_keys:
                await interaction.followup.send(f"No offerings found for {role}.", ephemeral=True)
                return
            key = valid_keys[0]
            entry = offerings[key]
            if loadout:
                return await Functions.offering_send(interaction, entry['name'], lang, True)
            await Functions.offering_send(interaction, entry['name'], lang)
            return


    async def item(interaction: discord.Interaction, lang, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking=True, ephemeral=True)
        items = await Functions.data_load('items', lang)
        if items is None:
            await interaction.followup.send("Error while loading the item data.")
            return

        keys = list(items.keys())
        if '_id' in keys:
            keys.remove('_id')
        valid_keys = [key for key in keys if items[key]['bloodweb'] != 0]
        random.shuffle(valid_keys)
        if not valid_keys:
            await interaction.followup.send("No items found.", ephemeral=True)
            return

        key = valid_keys[0]
        entry = items[key]
        if loadout:
            temp = await Functions.item_send(interaction, entry['name'], lang, True)
            return temp[0], temp[1]
        await Functions.item_send(interaction, entry['name'], lang)
        return


    async def char(interaction: discord.Interaction, role, lang, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking=True, ephemeral=True)
        dlc_data = await Functions.data_load('dlcs', lang)
        if dlc_data is None:
            await interaction.followup.send("Error while loading the dlc data.", ephemeral = True)
            return
        chars = await Functions.data_load('chars', lang)
        if chars is None:
            await interaction.followup.send("Error while loading the char data.", ephemeral = True)
            return
        else:
            keys = list(chars.keys())
            if '_id' in keys:
                keys.remove('_id')
            valid_keys = [key for key in keys if chars[key]['role'] == role]
            random.shuffle(valid_keys)
            if not valid_keys:
                await interaction.followup.send(f"No characters found for {role}.", ephemeral=True)
                return
            key = valid_keys[0]
            entry = chars[key]
            if loadout:
                return await Functions.char_send(interaction, chars, entry['name'], dlc_data, lang, True), entry['id'], entry['role']
            await Functions.char_send(interaction, chars, entry['name'], dlc_data, lang)
            return


    async def addon(interaction: discord.Interaction, parent, lang, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            item = await Functions.data_load('items', lang)
            addons = await Functions.data_load('addons', lang)
            if item is None or addons is None:
                await interaction.followup.send("Error while loading the addon/item data.", ephemeral = True)
                return
        except Exception as e:
            await interaction.followup.send(f"Error while loading the data: {str(e)}", ephemeral = True)
            return

        parent_type = await Functions.get_item_type(parent, item)
        if parent_type is None and not loadout:
            await interaction.followup.send(f"There is no addon for an item named **{parent}**.", ephemeral = True)
            return

        keys = list(addons.keys())
        random.shuffle(keys)
        selected_keys = []
        embeds = []

        for key in keys:
            if len(selected_keys) >= 2:
                break
            if key == '_id':
                continue
            entry = addons[key]
            if entry == 'addon_info':
                continue
            if entry['item_type'] is None or entry['item_type'] != parent_type:
                continue

            embed = await Functions.addon_send(entry['name'], lang, interaction, True)
            embeds.append(embed)
            selected_keys.append(key)

        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral = True)
        return


    async def adfk(interaction: discord.Interaction, killer, lang, loadout: bool = False):
        if not loadout:
            await interaction.response.defer(thinking=True, ephemeral=True)
        addons = await Functions.data_load('addons', lang)
        if addons is None:
            await interaction.followup.send("Error while loading the addon data.", ephemeral = True)
            return
        chars = await Functions.data_load('chars', lang)
        if chars is None:
            await interaction.followup.send("Error while loading the char data.", ephemeral = True)
            return
        killer_item = await Functions.find_killer_item(killer, chars)
        if killer_item == 1:
            await interaction.followup.send(f"There is no killer named **{killer}**.", ephemeral = True)
            return
        keys = list(addons.keys())
        if '_id' in keys:
            keys.remove('_id')
        valid_keys = [key for key in keys if killer_item in addons[key]['parents']]
        random.shuffle(valid_keys)
        if len(valid_keys) < 2:
            await interaction.followup.send(f"Not enough addons found for {killer_item}.", ephemeral=True)
            return
        embeds = []
        for i in range(2):
            key = valid_keys[i]
            entry = addons[key]
            embed = await Functions.addon_send(entry['name'], lang, interaction, True)
            embeds.append(embed)
        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral = True)
        return


    async def loadout(interaction: discord.Interaction, role):
        lang = await Functions.get_language_code(interaction)
        await interaction.response.send_message(f'Generating loadout for {role}...', ephemeral=True)
        chars = await Functions.data_load('chars', lang)
        if chars is None:
            await interaction.followup.send("Error while loading the char data.")
            return
        embeds = []
        char = await Random.char(interaction, role, lang, True)
        embeds.append(char[0])

        if char[2] == 'survivor':
            item = await Random.item(interaction, lang, True)
            embeds.append(item[0])
            addon = await Random.addon(interaction, item[1], lang, True)
            if addon is not None:
                embeds.extend(addon)
        elif char[2] == 'killer':
            killer_item = await Functions.find_killer_item(char[1], chars)
            killer = await Functions.find_killer_by_item(killer_item, chars)
            addon = await Random.adfk(interaction, killer, lang, True)
            if addon is not None:
                embeds.extend(addon)

        perks = await Random.perk(interaction, 4, char[2], lang, True)
        embeds.extend(perks)
        offering = await Random.offering(interaction, char[2], lang, True)
        embeds.append(offering)

        await interaction.followup.send(embeds=embeds)


##Owner Commands
class Owner():
    async def log(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'log [current/folder/lines] (Replace lines with a positive number, if you only want lines.) - Get the log\n'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        if args[0] == 'current':
            try:
                await message.channel.send(file=discord.File(r''+log_folder+'DBDStats.log'))
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                        f.write(log_folder+'DBDStats.log')
                    try:
                        await message.channel.send(file=discord.File(r''+buffer_folder+'Logs.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await message.channel.send("The log is too big to be send directly.\nYou have to look at the log in your server (VPS).")
                    os.remove(buffer_folder+'Logs.zip')
                    return
        elif args[0] == 'folder':
            if os.path.exists(buffer_folder+'Logs.zip'):
                os.remove(buffer_folder+'Logs.zip')
            with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                for file in os.listdir(log_folder):
                    if file.endswith(".zip"):
                        continue
                    f.write(log_folder+file)
            try:
                await message.channel.send(file=discord.File(r''+buffer_folder+'Logs.zip'))
            except discord.HTTPException as err:
                if err.status == 413:
                    await message.channel.send("The folder is too big to be send directly.\nPlease get the current file, or the last X lines.")
            os.remove(buffer_folder+'Logs.zip')
            return
        else:
            try:
                if int(args[0]) < 1:
                    await __wrong_selection()
                    return
                else:
                    lines = int(args[0])
            except ValueError:
                await __wrong_selection()
                return
            with open(log_folder+'DBDStats.log', 'r', encoding='utf8') as f:
                with open(buffer_folder+'log-lines.txt', 'w', encoding='utf8') as f2:
                    count = 0
                    for line in (f.readlines()[-lines:]):
                        f2.write(line)
                        count += 1
            await message.channel.send(content = f'Here are the last {count} lines of the current logfile:', file = discord.File(r''+buffer_folder+'log-lines.txt'))
            if os.path.exists(buffer_folder+'log-lines.txt'):
                os.remove(buffer_folder+'log-lines.txt')
            return


    async def activity(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'activity [playing/streaming/listening/watching/competing] [title] (url) - Set the activity of the bot\n'
                                       '```')
        def isURL(zeichenkette):
            try:
                ergebnis = urlparse(zeichenkette)
                return all([ergebnis.scheme, ergebnis.netloc])
            except:
                return False

        def remove_and_save(liste):
            if liste and isURL(liste[-1]):
                return liste.pop()
            else:
                return None

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        url = remove_and_save(args[1:])
        title = ' '.join(args[1:])
        print(title)
        print(url)
        with open(activity_file, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'playing':
            data['activity_type'] = 'Playing'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'streaming':
            data['activity_type'] = 'Streaming'
            data['activity_title'] = title
            data['activity_url'] = url
        elif action == 'listening':
            data['activity_type'] = 'Listening'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'watching':
            data['activity_type'] = 'Watching'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'competing':
            data['activity_type'] = 'Competing'
            data['activity_title'] = title
            data['activity_url'] = ''
        else:
            await __wrong_selection()
            return
        with open(activity_file, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Activity set to {action} {title}{" " + url if url else ""}.')


    async def status(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'status [online/idle/dnd/invisible] - Set the status of the bot'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        with open(activity_file, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'online':
            data['status'] = 'online'
        elif action == 'idle':
            data['status'] = 'idle'
        elif action == 'dnd':
            data['status'] = 'dnd'
        elif action == 'invisible':
            data['status'] = 'invisible'
        else:
            await __wrong_selection()
            return
        with open(activity_file, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Status set to {action}.')


    async def changelog(message, file):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'changelog [file] - Upload a txt, or md, that is send to the changelog channels.'
                                       '```')
        send_as_file = False
        if file == []:
            await __wrong_selection()
            return
        try:
            if file[0].size > 8388608:
                await message.channel.send('The file is too big. Max. 8MB.')
                return
            filetype = str({file[0].filename.split('.')[-1]}).replace("{'", '').replace("'}", '')
            changelog = f'{buffer_folder}changelog.{filetype}'
            await file[0].save(changelog)
            with open(changelog, 'rb') as f:
                text = f.read().decode('utf-8')
                if len(text) > 2000:
                    send_as_file = True
        except:
            traceback.print_exc()
            manlogger.warning(f'Error while reading the changelog file.')
            await message.channel.send('Error while reading the changelog file.')
            os.remove(changelog)
            return

        reply = await message.reply('Publishing...')

        c.execute("SELECT * FROM changelogs")
        data = c.fetchall()
        if data == []:
            await reply.edit(content = 'There are no changelog channels set.')
            return
        published_success = 0
        published_total = 0
        for entry in data:
            channel = await Functions.get_or_fetch('channel', entry[2])
            if channel is None:
                manlogger.info(f"Channel {entry[2]} not found. Removing from db.")
                c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                published_total += 1
                continue
            if not send_as_file:
                try:
                    await channel.send(text)
                    published_success += 1
                    published_total += 1
                except discord.errors.NotFound:
                    manlogger.info(f"Channel {entry[2]} not found. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except discord.errors.Forbidden:
                    manlogger.info(f"Missing permissions in channel {entry[2]}. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except:
                    traceback.print_exc()
                    manlogger.warning(f'Error while publishing the changelog to {entry[2]}.')
                    published_total += 1
            else:
                try:
                    await channel.send(file=discord.File(changelog))
                    published_success += 1
                    published_total += 1
                except discord.errors.NotFound:
                    manlogger.info(f"Channel {entry[2]} not found. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except discord.errors.Forbidden:
                    manlogger.info(f"Missing permissions in channel {entry[2]}. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except:
                    traceback.print_exc()
                    manlogger.warning(f'Error while publishing the changelog to {entry[2]}.')
                    published_total += 1
        os.remove(changelog)
        conn.commit()
        await reply.edit(content = f'Published to `{published_success}/{published_total}` channels.')


    async def shutdown(message):
        global shutdown
        manlogger.info('Engine powering down...')
        await message.channel.send('Engine powering down...')
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        conn.close()
        db.close()

        await bot.close()



##Bot Commands (These commands are for the bot itself.)
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! \nCommand execution time: `{int(ping)}ms`\nPing to gateway: `{int(bot.latency * 1000 if interaction.guild is None else bot.shards.get(interaction.guild.shard_id).latency * 1000)}ms`')


#Bot Info
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    member_count = sum(guild.member_count for guild in bot.guilds)

    embed = discord.Embed(
        title=f"Informationen about {bot.user.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

    embed.add_field(name="Created at", value=bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), inline=True)
    embed.add_field(name="Version", value=bot_version, inline=True)
    embed.add_field(name="Uptime", value=str(timedelta(seconds=int((datetime.now() - start_time).total_seconds()))), inline=True)

    embed.add_field(name="Owner", value=f"<@!{OWNERID}>", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="Server", value=f"{len(bot.guilds)}", inline=True)
    embed.add_field(name="Member count", value=str(member_count), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="Shards", value=f"{bot.shard_count}", inline=True)
    embed.add_field(name="Shard ID", value=f"{interaction.guild.shard_id if interaction.guild else 'N/A'}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="Python", value=f"{platform.python_version()}", inline=True)
    embed.add_field(name="discord.py", value=f"{discord.__version__}", inline=True)
    embed.add_field(name="Sentry", value=f"{sentry_sdk.consts.VERSION}", inline=True)

    embed.add_field(name="Repo", value=f"[GitLab](https://gitlab.bloodygang.com/Serpensin/DBDStats)", inline=True)
    embed.add_field(name="Invite", value=f"[Invite me](https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=67423232&scope=bot)", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    if interaction.user.id == int(OWNERID):
        # Add CPU and RAM usage
        process = psutil.Process(os.getpid())
        cpu_usage = process.cpu_percent()
        ram_usage = round(process.memory_percent(), 2)
        ram_real = round(process.memory_info().rss / (1024 ** 2), 2)

        embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_real} MB", inline=True)

    await interaction.response.send_message(embed=embed)


#Subscribe
@tree.command(name = 'subscribe', description = 'Subscribe to a specific category for automatic posts.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild.id))
@discord.app_commands.checks.has_permissions(manage_guild = True)
@discord.app_commands.describe(channel = 'The channel you want to post messages to.',
                               shrine = 'Subscribe to the shrine.',
                               changelogs = 'Subscribe to the changelogs of this bot.'
                               )
async def self(interaction: discord.Interaction,
               channel: discord.TextChannel,
               shrine: bool,
               changelogs: bool
               ):
    if interaction.guild is None:
        await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
        return

    permissions = channel.permissions_for(interaction.guild.me)
    if not (permissions.send_messages and permissions.attach_files and permissions.embed_links):
        await interaction.response.send_message('I\'m missing one of the following persmissions in the specified channel:\n• `SEND_MESSAGES`\n• `ATTACH_FILES`\n• `EMBED_LINKS`', ephemeral=True)
        return

    message = ''
    if shrine:
        c.execute('SELECT * FROM shrine WHERE channel_id = ?', (channel.id,))
        if c.fetchone() is None:
            c.execute('INSERT INTO shrine (guild_id, channel_id) VALUES (?, ?)', (interaction.guild_id, channel.id,))
            message += f'Successfully subscribed to the shrine on channel <#{channel.id}>.\n'
        else:
            message += f'You are already subscribed to the shrine on channel <#{channel.id}>.\n'
    else:
        c.execute('SELECT * FROM shrine WHERE channel_id = ?', (channel.id,))
        if c.fetchone() is None:
            message += f'You are not subscribed to the shrine on channel <#{channel.id}>.\n'
        else:
            c.execute('DELETE FROM shrine WHERE channel_id = ?', (channel.id,))
            message += f'Successfully unsubscribed from the shrine on channel <#{channel.id}>.\n'

    if changelogs:
        c.execute('SELECT * FROM changelogs WHERE channel_id = ?', (channel.id,))
        if c.fetchone() is None:
            c.execute('INSERT INTO changelogs (guild_id, channel_id) VALUES (?, ?)', (interaction.guild_id, channel.id,))
            message += f'Successfully subscribed to the changelogs on channel <#{channel.id}>.\n'
        else:
            message += f'You are already subscribed to the changelogs on channel <#{channel.id}>.\n'
    else:
        c.execute('SELECT * FROM changelogs WHERE channel_id = ?', (channel.id,))
        if c.fetchone() is None:
            message += f'You are not subscribed to the changelogs on channel <#{channel.id}>.\n'
        else:
            c.execute('DELETE FROM changelogs WHERE channel_id = ?', (channel.id,))
            message += f'Successfully unsubscribed from the changelogs on channel <#{channel.id}>.\n'

    conn.commit()
    message += '\nYou can subscribe to the shrine and changelogs on multiple channels.\nIf sending a message failed because of missing permissions, this specific sub will be canceled without notice.'
    await interaction.response.send_message(message, ephemeral=True)


#Translation info
@tree.command(name = 'translation_info', description = 'Get info about the translation.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild.id))
@discord.app_commands.checks.has_permissions(manage_guild = True)
async def self(interaction: discord.Interaction):
    await interaction.response.defer(thinking = True, ephemeral = True)

    if interaction.guild is None:
        await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
        return
    embed = discord.Embed(title = 'Translation', color = 0x00ff00)
    embed.description = 'This bot is translated into the following languages:'
    temp = []
    for lang in api_langs:
        lang = await Functions.get_language_name(lang)
        temp.append(lang)
        embed.description += f'\n• {lang}'
    embed.description += '\n\nFor this languages, the bot uses ML (maschine learning) to translate the text, which can be a bit whacky. That\'s the reason, we only output these languages. For the input, you still have to use english.'
    for lang in languages:
        if lang not in temp:
            embed.description += f'\n• {lang}'
    embed.description += '\n\nThe bot will automatically select the language based on the client who invokes a comand.\nIf you sub to the shrine, he will post it in the language of the server (community).\nIf he can\'t translate to that languag, he\'ll default to english.'
    await interaction.followup.send(embed = embed, ephemeral = True)


#Support Invite
if support_available:
    @tree.command(name = 'support', description = 'Get invite to our support server.')
    @discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
    async def self(interaction: discord.Interaction):
        if str(interaction.guild.id) != SUPPORTID:
            await interaction.response.defer(ephemeral = True)
            await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral = True)
        else:
            await interaction.response.send_message('You are already in our support server!', ephemeral = True)


##DBD Commands (these commands are for DeadByDaylight.)
#Buy
@tree.command(name = "buy", description = 'This will post a link to a site where you can buy DeadByDaylight for a few bucks.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
async def self(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(await Functions.translate(interaction, "This command can only be used in a server."))
    else:
        embed = discord.Embed(title="Buy Dead By Daylight", description=await Functions.translate(interaction, "Click the title, to buy the game for a few bucks."), url="https://www.g2a.com/n/dbdstats", color=0x00ff00)
        await interaction.response.send_message(embed=embed)


#Info about Stuff
messages = {
    'en': 'Bot is starting...',
    'de': 'Bot startet...',
    'fr': 'Bot commence...',
    'es': 'El bot está empezando...',
    'ru': 'Бот запускается...',
    'ja': 'ボットが起動しています...',
    'ko': '봇이 시작됩니다...',
    'pl': 'Bot się uruchamia...',
    'pt-BR': 'O bot está iniciando...',
    'zh-TW': '机器人正在启动...',
}

def create_global_lists():
    categories = ["addon", "char", "killer", "dlc", "item", "map", "offering", "perk"]
    for category in categories:
        for lang in api_langs:
            global_var_name = f"{category}_names_{lang}"
            globals()[global_var_name] = [messages[lang]]
create_global_lists()

async def get_localized_list(interaction: discord.Interaction, list_type: Literal['addon', 'char', 'killer', 'dlc', 'item', 'map', 'offering', 'perk']) -> List[str]:
    lang = await Functions.get_language_code(interaction)
    if lang not in api_langs:
        lang = 'en'
    list_name = f'{list_type}_names_{lang}'
    return globals()[list_name]


async def autocomplete_addons(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    addon_list = await get_localized_list(interaction, 'addon')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in addon_list[:25]]
    matching_names = [name for name in addon_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_character(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    char_list = await get_localized_list(interaction, 'char')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in char_list[:25]]
    matching_names = [name for name in char_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_killer(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    killer_list = await get_localized_list(interaction, 'killer')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in killer_list[:25]]
    matching_names = [name for name in killer_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_dlcs(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    dlc_list = await get_localized_list(interaction, 'dlc')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in dlc_list[:25]]
    matching_names = [name for name in dlc_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_items(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    item_list = await get_localized_list(interaction, 'item')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in item_list[:25]]
    matching_names = [name for name in item_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_maps(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    map_list = await get_localized_list(interaction, 'map')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in map_list[:25]]
    matching_names = [name for name in map_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_offerings(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    offering_list = await get_localized_list(interaction, 'offering')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in offering_list[:25]]
    matching_names = [name for name in offering_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]

async def autocomplete_perks(interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
    perk_list = await get_localized_list(interaction, 'perk')
    if current == '':
        return [discord.app_commands.Choice(name=name, value=name) for name in perk_list[:25]]
    matching_names = [name for name in perk_list if current.lower() in name.lower()]
    return [discord.app_commands.Choice(name=name, value=name) for name in matching_names]


#Info
@tree.command(name = 'info', description = 'Get info about DBD related stuff.')
@discord.app_commands.checks.cooldown(2, 30, key=lambda i: (i.user.id))
@discord.app_commands.describe(category = 'The category you want to get informations about.',
                               addon = 'Only used if "Addons" is selected. Start writing to search...',
                               character = 'Only used if "Characters" is selected. Start writing to search...',
                               dlc = 'Only used if "DLCs" is selected. Leave empty to get an overview. Start writing to search...',
                               item = 'Only used if "Items" is selected. Start writing to search...',
                               map = 'Only used if "Maps" is selected. Start writing to search...',
                               offering = 'Only used if "Offerings" is selected. Start writing to search...',
                               perk = 'Only used if "Perks" is selected. Start writing to search...'
                               )
@discord.app_commands.autocomplete(addon=autocomplete_addons,
                                   character=autocomplete_character,
                                   dlc=autocomplete_dlcs,
                                   item=autocomplete_items,
                                   map=autocomplete_maps,
                                   offering=autocomplete_offerings,
                                   perk=autocomplete_perks
                                   )
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
    discord.app_commands.Choice(name = 'Patchnotes', value = 'patch'),
    discord.app_commands.Choice(name = 'Perks', value = 'perk'),
    discord.app_commands.Choice(name = 'Playercount', value = 'player'),
    discord.app_commands.Choice(name = 'Playerstats', value = 'stats'),
    discord.app_commands.Choice(name = 'Rankreset', value = 'reset'),
    discord.app_commands.Choice(name = 'Shrine', value = 'shrine'),
    discord.app_commands.Choice(name = 'Twitch', value = 'twitch'),
    discord.app_commands.Choice(name = 'Versions', value = 'version')
    ])
async def self(interaction: discord.Interaction,
               category: str,
               addon: str = None,
               character: str = None,
               dlc: str = None,
               item: str = None,
               map: str = None,
               offering: str = None,
               perk: str = None
               ):
    if interaction.guild is None:
        await interaction.response.send_message("This command can only be used in a server.")
        return

    if category == 'char':
        if character is None:
            await interaction.response.send_message(await Functions.translate(interaction, "You need to specify a character."))
        else:
            await Info.character(interaction, char = character)

    elif category == 'stats':
        class Input(discord.ui.Modal, title = 'Enter SteamID64. Timeout in 30 seconds.'):
            self.timeout = 30
            answer = discord.ui.TextInput(label = 'ID64 or vanity(url) you want stats for.', style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.playerstats(interaction, steamid = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'dlc':
        await Info.dlc(interaction, name = dlc)

    elif category == 'event':
        await Info.event(interaction)

    elif category == 'item':
        if item is None:
            await interaction.response.send_message(await Functions.translate(interaction, "You need to specify an item."))
        else:
            await Info.item(interaction, name = item)

    elif category == 'map':
        if map is None:
            await interaction.response.send_message(await Functions.translate(interaction, "You need to specify a map."))
        else:
            await Info.maps(interaction, name = map)

    elif category == 'offering':
        if offering is None:
            await interaction.response.send_message(await Functions.translate(interaction, "You need to specify an offering."))
        else:
            await Info.offering(interaction, name = offering)

    elif category == 'perk':
        if perk is None:
            await interaction.response.send_message(await Functions.translate(interaction, "You need to specify a perk."))
        else:
            await Info.perk(interaction, name = perk)

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
        class Input(discord.ui.Modal, title = 'Enter SteamID64. Timeout in 30 seconds.'):
            self.timeout = 30
            answer = discord.ui.TextInput(label = 'ID64 or vanity(url) you want to check.', style = discord.TextStyle.short, required = True)
            async def on_submit(self, interaction: discord.Interaction):
                await Info.legacycheck(interaction, steamid = self.answer.value.strip())
        await interaction.response.send_modal(Input())

    elif category == 'addon':
        if addon is None:
            await interaction.response.send_message(await Functions.translate(interaction, "You need to specify an addon."))
        else:
            await Info.addon(interaction, name = addon)

    elif category == 'twitch':
        await Info.twitch_info(interaction)

    elif category == 'patch':
        await Info.patch(interaction)

    else:
        await interaction.response.send_message('Invalid category.', ephemeral=True)


#Randomize
@tree.command(name = 'random', description = 'Get a random perk, offering, map, item, char or full loadout.')
@discord.app_commands.checks.cooldown(2, 30, key=lambda i: (i.user.id))
@discord.app_commands.describe(category = 'What do you want to randomize?',
                               item = 'Only used if "Addon" is selected.',
                               killer = 'Only used if "Addon for Killer" is selected. Start writing to search...'
                               )
@discord.app_commands.autocomplete(killer=autocomplete_killer)
@discord.app_commands.choices(category = [
    discord.app_commands.Choice(name = 'Addon', value = 'addon'),
    discord.app_commands.Choice(name = 'Addon for Killer', value = 'adfk'),
    discord.app_commands.Choice(name = 'Char', value = 'char'),
    discord.app_commands.Choice(name = 'Item', value = 'item'),
    discord.app_commands.Choice(name = 'Loadout', value = 'loadout'),
    discord.app_commands.Choice(name = 'Offering', value = 'offering'),
    discord.app_commands.Choice(name = 'Perk', value = 'perk')
    ],
    item = [
    discord.app_commands.Choice(name = 'Medikit', value = 'medkit'),
    discord.app_commands.Choice(name = 'Flashlight', value = 'flashlight'),
    discord.app_commands.Choice(name = 'Toolbox', value = 'toolbox'),
    discord.app_commands.Choice(name = 'Map', value = 'map'),
    discord.app_commands.Choice(name = 'Key', value = 'key')
    ])
async def self(interaction: discord.Interaction,
                    category: str,
                    item: str = None,
                    killer: str = None):
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
                lang = await Functions.get_language_code(interaction)

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

                await Random.perk(interaction, x, y, lang)

        await interaction.response.send_modal(Input())

    elif category == 'offering':
        class Input(discord.ui.Modal, title='Offering for whom? Timeout in 30 seconds.'):
            timeout = 30
            role = discord.ui.TextInput(label='Role', style=discord.TextStyle.short, placeholder='Survivor or Killer', min_length=6, max_length=8, required=True)

            async def on_submit(self, interaction: discord.Interaction):
                role = self.role.value.lower()

                if role != 'survivor' and role != 'killer':
                    await interaction.response.send_message(content='Invalid input: the role must be either Survivor or Killer.', ephemeral=True)
                    return
                lang = await Functions.get_language_code(interaction)

                await Random.offering(interaction, role, lang)

        await interaction.response.send_modal(Input())

    elif category == 'item':
        lang = await Functions.get_language_code(interaction)
        await Random.item(interaction, lang)

    elif category == 'char':
        class Input(discord.ui.Modal, title='Char for whom? Timeout in 30 seconds.'):
            timeout = 30
            role = discord.ui.TextInput(label='Role', style=discord.TextStyle.short, placeholder='Survivor or Killer', min_length=6, max_length=8, required=True)

            async def on_submit(self, interaction: discord.Interaction):
                role = self.role.value.lower().strip()

                if role != 'survivor' and role != 'killer':
                    await interaction.response.send_message(content='Invalid input: the role must be either Survivor or Killer.', ephemeral=True)
                    return

                lang = await Functions.get_language_code(interaction)

                await Random.char(interaction, role, lang)

        await interaction.response.send_modal(Input())

    elif category == 'addon':
        if item is None:
            await interaction.response.send_message(content='You need to specify an item.', ephemeral=True)
            return
        lang = await Functions.get_language_code(interaction)
        await Random.addon(interaction, item, lang)

    elif category == 'adfk':
        if killer is None:
            await interaction.response.send_message(content='You need to specify a killer.', ephemeral=True)
            return
        lang = await Functions.get_language_code(interaction)
        await Random.adfk(interaction, killer, lang)

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
        await interaction.response.send_message('Invalid category.', ephemeral=True)



















if __name__ == '__main__':
    if not TOKEN or not STEAMAPIKEY:
        error_message = 'Missing token or steam API key. Please check your .env file.'
        manlogger.critical(error_message)
        sys.exit(error_message)
    else:
        try:
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            error_message = 'Invalid token. Please check your .env file.'
            manlogger.critical(error_message)
            sys.exit(error_message)
        except asyncio.CancelledError:
            if shutdown:
                pass
