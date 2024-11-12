#Import
import time
startupTime_start = time.time()
import aiohttp
import asyncio
import datetime
import discord
import html2text
import json
import jsonschema
import os
import platform
import psutil
import pycountry
import pytz
import random
import re
import sentry_sdk
import signal
import sqlite3
import sys
import tempfile
import zlib
from aiohttp import web
from bs4 import BeautifulSoup
from CustomModules import bot_directory
from CustomModules import googletrans
from CustomModules import log_handler
from CustomModules import killswitch
from CustomModules import libretrans
from CustomModules import steam
from CustomModules import steamcharts
from CustomModules.app_translation import Translator as CommandTranslator
from CustomModules.twitch import TwitchAPI
from discord.utils import is_docker
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from typing import Any, List, Literal, Optional
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile



#Set vars
load_dotenv()
app_folder_name = 'DBDStats'
api_base = 'https://dbd.tricky.lol/api/' # For production
#api_base = 'http://localhost:5000/' # For testing
NO_CACHE = False # Disables cache for faster start (!!!DOESN'T WORK IN PRODUCTION!!!)
bot_base = 'https://cdn.serpensin.com/botfiles/DBDStats/'
map_portraits = f'{bot_base}mapportraits/'
alt_playerstats = 'https://dbd.tricky.lol/playerstats/'
steamStore = 'https://store.steampowered.com/app/'
bot_version = "1.16.3"
api_langs = ['de', 'en', 'fr', 'es', 'ru', 'ja', 'ko', 'pl', 'pt-BR', 'zh-TW']
DBD_ID = 381210
isRunnigInDocker = is_docker()

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
TOPGG_TOKEN = os.getenv('TOPGG_TOKEN')
DISCORDBOTS_TOKEN = os.getenv('DISCORDBOTS_TOKEN')
DISCORDBOTLISTCOM_TOKEN = os.getenv('DISCORDBOTLIST_TOKEN')
DISCORDLIST_TOKEN = os.getenv('DISCORDLIST_TOKEN')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './googleauth.json')
LOG_LEVEL = os.getenv('LOG_LEVEL')

discord.VoiceClient.warn_nacl = False

#Init sentry
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
    release=f'DBDStats@{bot_version}'
)

#Fix error on windows on shutdown.
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#Set-up folders
def folder_setup():
    paths = [
            f'{app_folder_name}//Logs',
            f'{app_folder_name}//Buffer//Stats',
            f'{app_folder_name}//Buffer//addon',
            f'{app_folder_name}//Buffer//char',
            f'{app_folder_name}//Buffer//dlc',
            f'{app_folder_name}//Buffer//event',
            f'{app_folder_name}//Buffer//item',
            f'{app_folder_name}//Buffer//map',
            f'{app_folder_name}//Buffer//offering',
            f'{app_folder_name}//Buffer//patchnotes',
            f'{app_folder_name}//Buffer//perk',
        ]
    for path in paths:
        os.makedirs(path, exist_ok=True)
folder_setup()
log_folder = f'{app_folder_name}//Logs//'
buffer_folder = f'{app_folder_name}//Buffer//'
stats_folder = f'{app_folder_name}//Buffer//Stats//'
activity_file = os.path.join(app_folder_name, 'activity.json')
sql_file = os.path.join(app_folder_name, f'{app_folder_name}.db')


# #Set-up logging
log_manager = log_handler.LogManager(log_folder, app_folder_name, LOG_LEVEL)
discord_logger = log_manager.get_logger('discord')
program_logger = log_manager.get_logger('Program')
program_logger.info('Engine powering up...')


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
                            program_logger.debug(f'ValidationError: {ve}')
                            self.write_default_content()
                        except json.decoder.JSONDecodeError as jde:
                            program_logger.debug(f'JSONDecodeError: {jde}')
                            self.write_default_content()
                else:
                    self.write_default_content()

            def write_default_content(self):
                with open(self.file_path, 'w') as file:
                    json.dump(self.default_content, file, indent=4)
validator = JSONValidator(activity_file)
validator.validate_and_fix_json()


if isRunnigInDocker:
    if DB_PASS != '' and DB_NAME != '':
        connection_string = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    else:
        connection_string = f'mongodb://mongo:27017/DBDStats'
else:
    connection_string = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    # connection_string = f'mongodb://{DB_HOST}:{DB_PORT}/{DB_NAME}'
db = AsyncIOMotorClient(connection_string, server_api=ServerApi('1'), serverSelectionTimeoutMS=10000)
isDbAvailable = False

async def isMongoReachable(task: bool = False):
    global isDbAvailable
    try:
        result = await db.admin.command('ping')
        if result.get('ok') == 1:
            message = 'Connected to MongoDB.'
            if not task:
                program_logger.info(message)
                isDbAvailable = True
            return True
        else:
            message = f"Error connecting to MongoDB Platform. {result.get('errmsg')} -> Fallback to json-storage."
            if not task:
                program_logger.warning(message)
                isDbAvailable = False
            return message
    except Exception as e:
        message = f"Error connecting to MongoDB Platform. {e} -> Fallback to json-storage."
        if not task:
            program_logger.warning(message)
            isDbAvailable = False
        return message

# Google Translate API
try:
    TranslatorGoogle = googletrans.API(GOOGLE_APPLICATION_CREDENTIALS)
    program_logger.info('Connected to GoogleTranslate.')
    isGoogleAvailable = True
except Exception as e:
    program_logger.warning(f'Error connecting to GoogleTranslate. | Disabling translation. -> {e}')
    isGoogleAvailable = False

# LibreTranslate API
try:
    TranslatorLibre = libretrans.API(LIBRETRANS_APIKEY, LIBRETRANS_URL)
    program_logger.info('Connected to LibreTranslate.')
    isLibreAvailable = True
except ValueError as e:
    program_logger.warning(f'Error connecting to LibreTranslate. | Disabling translation. -> {e}')
    isLibreAvailable = False

# Twitch API
try:
    TwitchApi = TwitchAPI(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    program_logger.info('Connected to Twitch API.')
    isTwitchAvailable = True
except ValueError as e:
    program_logger.warning(f'Error connecting to Twitch API. | Disabling Twitch features. -> {e}')
    isTwitchAvailable = False

# Steam API
try:
    SteamApi = steam.API(STEAMAPIKEY)
except steam.Errors.InvalidKey:
    error_message = 'Invalid Steam API key.'
    program_logger.critical(error_message)
    sys.exit(error_message)



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
        self.firstDBchecked = False


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
        program_logger.info(f'I got kicked from {guild}. (ID: {guild.id})')

    async def on_guild_join(self, guild):
        program_logger.info(f'I joined {guild}. (ID: {guild.id})')

    async def on_message(self, message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'activity - Set the activity of the bot\n'
                                       'broadcast - Broadcast a message to all server owners\n'
                                       'changelog - Upload a txt, or md, that is send to the changelog channels\n'
                                       'clean - Clean specific parts\n'
                                       'help - Shows this message\n'
                                       'log - Get the log\n'
                                       'shutdown - Shutdown the bot\n'
                                       'status - Set the status of the bot\n'
                                       '```')

        if message.guild is None and message.author.id == int(OWNERID):
            args = message.content.split(' ')
            command, *args = args
            file = message.attachments
            program_logger.debug(command)

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
            elif command == 'clean':
                await Owner.clean(message, args)
                return
            elif command == 'broadcast':
                await Owner.broadcast(' '.join(args))
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
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{str(datetime.timedelta(seconds=Functions.safe_int(error.retry_after)))}`', ephemeral=True)
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
                    program_logger.warning(f"Unexpected error while sending message: {e}")
            finally:
                try:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}")
                except AttributeError:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}")
                sentry_sdk.capture_exception(error)

    async def setup_hook(self):
        global owner, conn, c, shutdown
        shutdown = False
        program_logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            program_logger.info('Syncing...')
            await tree.set_translator(CommandTranslator())
            await tree.sync()
            program_logger.info('Synced.')
            program_logger.debug('Commands synced.')
            self.synced = True
        conn = sqlite3.connect(sql_file)
        c = conn.cursor()
        await self.setup_database()
        try:
            owner = await bot.fetch_user(OWNERID)
            program_logger.debug('Owner found.')
        except:
            program_logger.debug('Owner not found.')     
            
        #Start background tasks
        stats = bot_directory.Stats(bot=bot,
                                    logger=program_logger,
                                    TOPGG_TOKEN=TOPGG_TOKEN,
                                    DISCORDBOTS_TOKEN=DISCORDBOTS_TOKEN,
                                    DISCORDBOTLISTCOM_TOKEN=DISCORDBOTLISTCOM_TOKEN,
                                    DISCORDLIST_TOKEN=DISCORDLIST_TOKEN,
                                    )
        bot.loop.create_task(Background.check_db_connection_task())
        while not self.firstDBchecked:
            await asyncio.sleep(0)
        bot.loop.create_task(Background.health_server())
        bot.loop.create_task(Background.update_twitchinfo_task())
        bot.loop.create_task(stats.task())
        bot.loop.create_task(Cache.task())

    async def on_ready(self):
        if self.initialized:
            await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
            return
        global start_time
        
        bot.loop.create_task(Background.subscribe_shrine_task())
        await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
        program_logger.info(r'''
 ____     ____     ____     ____     __              __
/\  _`\  /\  _`\  /\  _`\  /\  _`\  /\ \__          /\ \__
\ \ \/\ \\ \ \L\ \\ \ \/\ \\ \,\L\_\\ \ ,_\     __  \ \ ,_\    ____
 \ \ \ \ \\ \  _ <'\ \ \ \ \\/_\__ \ \ \ \/   /'__`\ \ \ \/   /',__\
  \ \ \_\ \\ \ \L\ \\ \ \_\ \ /\ \L\ \\ \ \_ /\ \L\.\_\ \ \_ /\__, `\
   \ \____/ \ \____/ \ \____/ \ `\____\\ \__\\ \__/.\_\\ \__\\/\____/
    \/___/   \/___/   \/___/   \/_____/ \/__/ \/__/\/_/ \/__/ \/___/

        ''')
        start_time = datetime.datetime.now()
        program_logger.info(f"Initialization completed in {time.time() - startupTime_start} seconds.")
        self.initialized = True
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error


class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        program_logger.info('Received signal to shutdown...')
        bot.loop.create_task(Owner.shutdown(owner))


#Update cache/db (Every ~4h)
class Cache():
    async def _update_perks():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f"{api_base}perks?locale={lang}")
            except Exception:
                program_logger.warning("Perks couldn't be updated.")
                program_logger.debug("Perks couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['perk'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}perk//{lang}.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=2)

    async def _update_offerings():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f'{api_base}offerings?locale={lang}')
            except Exception:
                program_logger.warning("Offerings couldn't be updated.")
                program_logger.debug("Offerings couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['offering'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}offering//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)

    async def _update_chars():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f'{api_base}characters?locale={lang}')
            except Exception:
                program_logger.warning("Characters couldn't be updated.")
                program_logger.debug("Characters couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['char'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}char//{lang}.json", 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)

    async def _update_dlc():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f'{api_base}dlc?locale={lang}')
            except Exception:
                program_logger.warning("DLC couldn't be updated.")
                program_logger.debug("DLC couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['dlc'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}dlc//{lang}.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=2)

    async def _update_item():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f'{api_base}items?role=survivor&locale={lang}')
            except Exception:
                program_logger.warning("Items couldn't be updated.")
                program_logger.debug("Items couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['item'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f"{buffer_folder}item//{lang}.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=2)

    async def _update_addon():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f'{api_base}addons?locale={lang}')
            except Exception:
                program_logger.warning("Addons couldn't be updated.")
                program_logger.debug("Addons couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['addon'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}addon//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)

    async def _update_map():
        for lang in api_langs:
            try:
                data = await Functions.check_rate_limit(f'{api_base}maps?locale={lang}')
            except Exception:
                program_logger.warning("Maps couldn't be updated.")
                program_logger.debug("Maps couldn't be updated.")
                return 1
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['map'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}map//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)

    async def _update_event():
        for lang in api_langs:
            try:
                data_list = await Functions.check_rate_limit(f'{api_base}events?locale={lang}')
            except Exception:
                program_logger.warning("Events couldn't be updated.")
                program_logger.debug("Events couldn't be updated.")
                return 1
            data = {}
            for i in range(len(data_list)):
                data[str(i)] = data_list[i]
            data['_id'] = lang
            if isDbAvailable:
                await db[DB_NAME]['event'].update_one({'_id': lang}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}event//{lang}.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)

    async def _update_version():
        try:
            data = await Functions.check_rate_limit(f'{api_base}versions')
        except Exception:
            program_logger.warning("Version couldn't be updated.")
            program_logger.debug("Version couldn't be updated.")
            return 1
        data['_id'] = 'version_info'
        if isDbAvailable:
            await db[DB_NAME]['version'].update_one({'_id': 'version_info'}, {'$set': data}, upsert=True)
        with open(f'{buffer_folder}version_info.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)

    async def _update_patchnotes():
        try:
            data = await Functions.check_rate_limit(f'{api_base}patchnotes')
        except Exception:
            program_logger.warning("Patchnotes couldn't be updated.")
            program_logger.debug("Patchnotes couldn't be updated.")
            return 1
        if os.path.exists(f'{buffer_folder}patchnotes'):
            for filename in os.scandir(f'{buffer_folder}patchnotes'):
                os.remove(filename)
        else:
            os.makedirs(f'{buffer_folder}patchnotes', exist_ok=True)
        data.sort(key=lambda x: x["id"], reverse=True)
        if isDbAvailable:
            await db[DB_NAME]['patchnotes'].drop()
        for entry in data:
            notes = {key: value for key, value in entry.items() if key == "notes"}
            notes['_id'] = entry["id"]
            with open(f'{buffer_folder}patchnotes//{str(entry["id"]).replace(".", "")}.json', 'w', encoding='utf8') as f:
                json.dump(notes, f, indent=2)
            if isDbAvailable:
                await db[DB_NAME]['patchnotes'].update_one({'_id': entry['id']}, {'$set': notes}, upsert=True)

    async def _clear_playerstats():
        for filename in os.scandir(stats_folder):
            if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 24:
                os.remove(filename)

    async def _name_lists():
        async def load_and_set_names(request_data, target_var_name):
            for lang in api_langs:
                killer = False
                if request_data == 'killers':
                    request_data = 'chars'
                    killer = True
                data = await Functions.data_load(request_data, lang)
                if data is None:
                    program_logger.fatal(f'{request_data} couldn\'t be updated for namelist {lang}.')
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

        global patch_versions
        patch_versions = []

        while(patch_versions == []):
            for filename in os.listdir(f'{buffer_folder}patchnotes'):
                base_name, extension = os.path.splitext(filename)
                patched_version = ''
                for i, char in enumerate(base_name):
                    patched_version += char
                    if i < len(base_name) -1 and char.isdigit() and base_name[i +1 ].isdigit():
                        patched_version += '.'
                patch_versions.append(patched_version)
            patch_versions.sort(reverse=True)

    async def start_cache_update():
        program_logger.info('Updating cache...')

        updates = [Cache._update_chars(),
                   Cache._update_perks(),
                   Cache._update_offerings(),
                   Cache._update_dlc(),
                   Cache._update_item(),
                   Cache._update_map(),
                   Cache._update_addon(),
                   Cache._update_event(),
                   Cache._update_version(),
                   Cache._update_patchnotes(),
                   Cache._clear_playerstats()
                   ]

        tasks = [asyncio.create_task(update) for update in updates]

        cache429 = False
        for task in tasks:
           task = await task
           if task == 1 and not bot.cache_updated:
               cache429 = True
        if cache429:
            message = 'Cache couldn\'t be populated, because of a 429. Exiting...'
            paths = [
                f'{buffer_folder}addon',
                f'{buffer_folder}char',
                f'{buffer_folder}dlc',
                f'{buffer_folder}event',
                f'{buffer_folder}item',
                f'{buffer_folder}map',
                f'{buffer_folder}offering',
                f'{buffer_folder}perk',
            ]
            for path in paths:
                for lang in api_langs:
                    filename = f"{path}//{lang}.json"
                    if not os.path.exists(filename):
                        program_logger.critical(message)
                        sys.exit(message)
            if not os.path.exists(f"{buffer_folder}//version_info.json"):
                program_logger.critical(message)
                sys.exit(message)
        await Cache._name_lists()

        bot.cache_updated = True
        program_logger.info('Cache updated.')

    async def task():
        if NO_CACHE:
            await Cache._name_lists()
            bot.cache_updated = True
            return
        while True:
            await Cache.start_cache_update()
            try:
                await asyncio.sleep(60*60*4)
            except asyncio.CancelledError:
                break


#Background tasks
class Background():
    async def check_db_connection_task():
        async def _upload_json_to_db():
            for entry in os.scandir(buffer_folder):
                if entry.is_dir():
                    if entry.name in ['Stats']:
                        continue
                    for filename in os.scandir(entry):
                        if filename.is_file() and filename.path.endswith('.json'):
                            with open(filename.path, 'r', encoding='utf8') as file:
                                data = json.load(file)
                                await db[DB_NAME][str(entry.name)].update_one({'_id': data['_id']}, {'$set': data}, upsert=True)
                if entry.is_file() and entry.name in ['shrine_info.json', 'version_info.json', 'translations.json', 'twitch_info']:
                    with open(entry.path, 'r', encoding='utf8') as file:
                        data = json.load(file)
                        await db[DB_NAME][str(entry.name)
                                    .replace('shrine_info.json', 'shrine')
                                    .replace('translations.json', 'translations')
                                    .replace('version_info.json', 'version')].update_one({'_id': str(entry.name)
                                                                                          .replace('shrine_info.json', 'shrine_info')
                                                                                          .replace('translations.json', 'translations')
                                                                                          .replace('version_info.json', 'version_info')}, {'$set': data}, upsert=True)

        async def _function():
            if not bot.initialized:
                if not bot.firstDBchecked:
                    await isMongoReachable()
                    bot.firstDBchecked = True
            global isDbAvailable
            old = isDbAvailable
            new = await isMongoReachable(True)
            if type(new) == bool:
                if old != new:
                    await _upload_json_to_db()
                    isDbAvailable = True
                    program_logger.info("Database connection established.")
                    try:
                        await owner.send("Database connection established.")
                    except:
                        pass
            else:
                if type(new) == str and not old:
                    return
                else:
                    isDbAvailable = False
                    program_logger.warning(f"Database connection lost. {new} -> Fallback to json.")
                    try:
                        await owner.send(f"Database connection lost.\n{new}\n-> Fallback to json.")
                    except:
                        pass

        while True:
            try:
                await _function()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break

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
            program_logger.warning(f'Error while starting health server: {e}')
            program_logger.debug(f'Error while starting health server: {e}')

    async def subscribe_shrine_task():
        async def function():
            try:
                shrine_new = await Functions.check_rate_limit('https://api.nightlight.gg/v1/shrine')
            except Exception:
                program_logger.warning("Shrine couldn't be updated.")
                program_logger.debug("Shrine couldn't be updated.")
                return 1
            else:
                shrine_old = await Functions.data_load('shrine')
                if shrine_old is None or shrine_new['data']['week'] != shrine_old['data']['week']:
                    if isDbAvailable:
                        shrine_new['_id'] = 'shrine_info'
                        await db[DB_NAME]['shrine'].update_one({'_id': 'shrine_info'}, {'$set': shrine_new}, upsert=True)
                    with open(f"{buffer_folder}shrine_info.json", "w", encoding="utf8") as f:
                        json.dump(shrine_new, f, indent=4)
                if shrine_old is None or shrine_new['data']['week'] > shrine_old['data']['week']:
                    c.execute('SELECT * FROM shrine')
                    for row in c.fetchall():
                        try:
                            await Info.shrine(channel_id=(row[1], row[2]))
                        except Exception as e:
                            program_logger.warning(f'Error while sending subscribed shrine to {row[1]}: {e}')

        while True:
            await function()
            try:
                await asyncio.sleep(60*15)
            except asyncio.CancelledError:
                break

    async def update_twitchinfo_task():
        async def function():
            game_id = await TwitchApi.get_game_id("Dead by Daylight")
            if game_id is None:
                return
            stats = await TwitchApi.get_category_stats(game_id)
            if not isinstance(stats, dict):
                return
            top = await TwitchApi.get_top_streamers(game_id)
            image = await TwitchApi.get_category_image(game_id)
            if image is None:
                image = ''
            # Create json from data - Stats
            data = {
                '_id': 'twitch_info',
                'viewer_count': Functions.safe_int(stats['viewer_count']),
                'stream_count': Functions.safe_int(stats['stream_count']),
                'average_viewer_count': Functions.safe_int(stats['average_viewer_count']),
                'category_rank': Functions.safe_int(stats['category_rank']),
                'image': image,
                'updated_at': Functions.safe_int(time.time())
            }
            # Create json from data - Top Streamers
            data['top_streamers'] = {}
            for entry in top:
                data['top_streamers'][str(entry)] = {
                    'streamer': top[entry]['streamer'],
                    'viewer_count': Functions.safe_int(top[entry]['viewer_count']),
                    'follower_count': Functions.safe_int(top[entry]['follower_count']),
                    'link': top[entry]['link'],
                    'title': top[entry]['title'],
                    'language': top[entry]['language'],
                    'thumbnail': top[entry]['thumbnail'],
                    'started_at': top[entry]['started_at']
                }
            # Update database
            if isDbAvailable:
                await db[DB_NAME]['twitch'].update_one({'_id': 'twitch_info'}, {'$set': data}, upsert=True)
            # Update json
            with open(f"{buffer_folder}twitch_info.json", "w", encoding="utf8") as f:
                json.dump(data, f, indent=4)

        while True:
            if not isTwitchAvailable:
                break
            await function()
            try:
                await asyncio.sleep(60*5)
            except asyncio.CancelledError:
                break


#Functions
class Functions():
    async def build_lang_lists():
        global libre_languages, google_languages
        google_languages = []
        libre_languages = []
        if isGoogleAvailable:
            lang_codes = TranslatorGoogle.get_languages()
            for lang in lang_codes:
                lang_name = await Functions.get_language_name(lang['language'])
                if lang_name is not None:
                    google_languages.append(lang_name)
                else:
                    program_logger.debug(f'Error while loading Google languages: {lang}')
            google_languages = sorted(google_languages)
            program_logger.info('Google languages loaded.')
            program_logger.debug(google_languages)
        if isLibreAvailable:
            lang_codes = await TranslatorLibre.get_languages()
            for entry in lang_codes:
                if entry['code'] == 'en':
                    for lang in entry['targets']:
                        lang_name = await Functions.get_language_name(lang)
                        if lang_name is not None:
                            libre_languages.append(lang_name)
                        else:
                            program_logger.debug(f'Error while loading LibreTranslate languages: {lang}')
            libre_languages = sorted(libre_languages)
            program_logger.info('LibreTranslate languages loaded.')
            program_logger.debug(libre_languages)

    async def check_rate_limit(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                program_logger.debug(response)
                if response.status != 200:
                    response.raise_for_status()
                else:
                    return await response.json()

    async def check_if_removed(id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{api_base}playerstats?steamid={id}') as resp:
                    program_logger.debug(resp.status)
                    resp.raise_for_status()  # Throws an exception if the status code is not 200
                    return 0
        except aiohttp.ClientResponseError as e:
            program_logger.debug(e.request_info.url)
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
                    program_logger.warning(f'Error while parsing {url}: {e}')
                    return 1
                else:
                    program_logger.warning(f'SteamID {id} got removed from the leaderboard.')
                    return 3
            elif e.status == 429:
                program_logger.warning(f'Rate limit exceeded while checking SteamID {id}.')
                return 2
            else:
                program_logger.warning(f'Unexpected response from API: {e}')
                return 1
        except Exception as e:
            program_logger.warning(f'Error while querying API: {e}')
            return 1

    async def convert_time(timestamp, request='full'):
        if request == 'full':
            return(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp)))
        elif request == 'date':
            return(time.strftime('%Y-%m-%d', time.gmtime(timestamp)))
        elif request == 'time':
            return(time.strftime('%H:%M:%S', time.gmtime(timestamp)))

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

    async def data_load(requested: Literal['addons', 'chars', 'dlcs', 'events', 'items', 'maps', 'offerings', 'perks', 'shrine', 'twitch', 'versions', 'patchnotes'], lang: Literal['de', 'en', 'fr', 'es', 'ru', 'ja', 'ko', 'pl', 'pt-BR', 'zh-TW'] = '', version: str = ''):
        requested = (lambda s: s[:-1] if s.endswith('s') and s != "patchnotes" else s)(requested)
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
        elif requested == 'patchnotes':
            db_id = version
            file_name += f"{version.replace('.', '')}"
        elif requested != 'shrine':
            file_name += f"{lang}"
            db_id = lang
        else:
            raise TypeError('Invalid request.')

        if not isDbAvailable:
            try:
                with open(f"{file_name}.json", "r", encoding="utf8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                return None
        else:
            data = json.loads(json.dumps(await db[DB_NAME][requested].find_one({'_id': db_id})))

        return data

    async def find_killer_by_item(item_name: str, killers_data) -> str:
        for killer in killers_data.values():
            if killer in api_langs:
                continue
            if killer.get('item') == item_name:
                return killer['id']
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

    async def get_language_code(interaction: discord.Interaction, lang_type: Literal['server', 'client'] = 'client'):
        if type(interaction) == discord.Guild:
            lang_code = interaction.preferred_locale[1][:2]
        elif lang_type == 'server':
            lang_code = interaction.guild_locale[1]
        else:
            lang_code = interaction.locale[1]
        lang_name = await Functions.get_language_name(lang_code)
        if lang_name in google_languages and isGoogleAvailable:
            return lang_code
        elif lang_name in libre_languages and isLibreAvailable:
            return lang_code
        else:
            return 'en'

    async def get_language_name(lang_code):
        if lang_code in ['zh-TW', 'zt', 'zh-CN']:
            return 'Chinese'
        elif lang_code == 'doi':
            return 'Dogri'
        elif lang_code == 'el':
            return 'Greek'
        elif lang_code == 'iw':
            return 'Hebrew'
        elif lang_code == 'jw':
            return 'Javanese'
        elif lang_code == 'ms':
            return 'Malay'
        elif lang_code == 'mni-Mtei':
            return 'Meiteilon'
        elif lang_code in ['nep', 'ne']:
            return 'Nepali'
        elif lang_code == 'nb':
            return 'Norwegian'
        elif lang_code in ['or', 'ori']:
            return 'Oriya'
        elif lang_code == 'pt-BR':
            return 'Portuguese'
        elif lang_code in ['es-ES', 'es']:
            return 'Spanish'
        elif lang_code == 'sw':
            return 'Swahili'
        try:
            lang = pycountry.languages.get(alpha_2=lang_code).name
            return lang
        except AttributeError:
            try:
                lang = pycountry.languages.get(alpha_3=lang_code).name
                return lang
            except AttributeError:
                return None

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

    async def translate(interaction: discord.Interaction, text):
        async def _translate(text, target_lang, source_lang='en'):
            async def _libre():
                try:
                    translated_text = await TranslatorLibre.translate_text(text, target_lang, source_lang)
                    program_logger.debug(f"Translated with LibreTranslate.: {translated_text}")
                    return translated_text
                except Exception as e:
                    program_logger.warning(f"Error while translating: {e}")
                    program_logger.debug(f"Error while translating: {e}")
                    return text

            if isGoogleAvailable:
                try:
                    translated_text = TranslatorGoogle.translate_text(text, target_lang, source_lang)
                    program_logger.debug(f"Translated with Google Translator.: {translated_text}")
                    return translated_text
                except Exception as e:
                    if isLibreAvailable:
                        t = await _libre()
                        return t
            elif isLibreAvailable:
                return await _libre()
            else:
                return text

        if type(interaction) == discord.app_commands.transformers.NoneType:
            lang = 'en'
        elif type(interaction) != str:
            lang = await Functions.get_language_code(interaction)
        else:
            lang = interaction
        if type(interaction) != discord.Guild and type(interaction) != str:
            if interaction.guild is None or lang == 'en':
                return text

        hashed = format(zlib.crc32(text.encode('utf-8')), '08x')
        program_logger.debug(f'Translation Hash: {hashed}')

        if isDbAvailable:
            data = json.loads(json.dumps(await db[DB_NAME]['translations'].find_one({'_id': 'translations'})))
        else:
            try:
                with open(f'{buffer_folder}translations.json', 'r', encoding='utf8') as f:
                    try:
                        data = json.loads(json.dumps(json.load(f)))
                    except ValueError:
                        data = {}
            except FileNotFoundError:
                data = {}

        if data is None and isDbAvailable:
            data = {}
        if hashed in data.keys():
            program_logger.debug(f'Hash {hashed} found in cache.')
            if lang in data[hashed].keys():
                program_logger.debug(f'Language {lang} found in cache.')
                return data[hashed][lang]
            else:
                program_logger.debug(f'Language {lang} not found in cache.')
                translation = await _translate(text, lang)
                if translation == text:
                    return text
                data[hashed] = {lang: translation}
                if isDbAvailable:
                    await db[DB_NAME]['translations'].update_one(
                        {'_id': 'translations'},
                        {
                            '$set': {
                                f'{hashed}.{lang}': translation
                            }
                        }
                    )
                try:
                    with open(f'{buffer_folder}translations.json', 'r', encoding='utf8') as f:
                        old_data = json.load(f)
                except FileNotFoundError:
                    old_data = {}
                data = Functions.merge_dictionaries(old_data, data)
                with open(f'{buffer_folder}translations.json', 'w', encoding='utf8') as f:
                    json.dump(data, f, indent=4)
                return translation
        else:
            program_logger.debug(f'Hash {hashed} not found in cache.')
            translation = await _translate(text, lang)
            if translation == text:
                return text
            data[hashed] = {lang: translation}
            if isDbAvailable:
                await db[DB_NAME]['translations'].update_one({'_id': 'translations'}, {'$set': data}, upsert=True)
            with open(f'{buffer_folder}translations.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=4)
            return translation

    async def safe_add_field(embed, name_key, value_key, player_stats, interaction, inline=True):
        try:
            value = Functions.safe_int(player_stats[value_key])
        except KeyError as e:
            value = None
            program_logger.warning(f"KeyError while adding field: {e}")
            sentry_sdk.capture_exception(e)
        
        translated_name = await Functions.translate(interaction, name_key)
        embed.add_field(name=translated_name, value=f"{value:,}" if value is not None else "NOT FOUND", inline=inline)

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
        dt_object = datetime.datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC)

        # Convert to local timezone
        local_timezone = pytz.timezone(local_tz)
        dt_object = dt_object.astimezone(local_timezone)

        # Get the UNIX timestamp
        unix_timestamp = Functions.safe_int(dt_object.timestamp())

        return unix_timestamp

    def find_key_by_name(input_name, data):
        for key, value in data.items():
            if key == '_id':
                continue
            key_name = str(value.get('name')).lower().replace('&nbsp;', ' ').replace('\'', '').replace('\u2019', '').replace(':', '').replace(' ', '')
            if key_name == input_name.lower().replace('&nbsp;', ' ').replace('\'', '').replace('\u2019', '').replace(':', '').replace(' ', ''):
                return key
        return input_name

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

    def merge_dictionaries(json1, json2):
        for key, value in json2.items():
            if key in json1:
                if key == '_id':
                    continue
                json1[key].update(value)
            else:
                json1[key] = value
        return json1
    
    def safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0


#Send informations
class SendInfo():
    async def addon(addon, lang, interaction: discord.Interaction, random: bool = False):
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
                embed.add_field(name=await Functions.translate(interaction, 'Rarity'), value=str(await Functions.translate(interaction, data[key]['rarity'])).capitalize(), inline=True)
                embed.add_field(name=await Functions.translate(interaction, 'Role'), value=str(await Functions.translate(interaction, data[key]['role'])).capitalize(), inline=True)
                if data[key]['item_type'] is None:
                    char = await Functions.data_load('chars', lang)
                    if char is None:
                        return
                    for key in char.keys():
                        if str(key) == '_id':
                            continue
                        if str(data[addon]['parents']).replace('[', '').replace('\'', '').replace(']', '') == str(char[key]['item']).replace('[', '').replace('\'', '').replace(']', ''):
                            embed.add_field(name=await Functions.translate(interaction, 'Origin'), value=str(await Functions.translate(interaction, char[key]['name'])).capitalize(), inline=True)
                            break
                else:
                    embed.add_field(name=await Functions.translate(interaction, 'Origin'), value=str(await Functions.translate(interaction, data[key]['item_type'])).capitalize(), inline=True)
                if random:
                    return embed
                else:
                    await interaction.followup.send(embed=embed, ephemeral = True)
                    return not None
        return None

    async def char(interaction, data, char, dlc_data, lang, loadout: bool = False):
        for key in data.keys():
            if str(key) == '_id':
                continue
            if str(data[key]['name']) == char:
                embed = discord.Embed(title=await Functions.translate(interaction, "Character Info"), description=str(data[key]['name']), color=0xb19325)
                embed.set_thumbnail(url=f"{bot_base}{data[key]['image']}")
                embed.add_field(name=await Functions.translate(interaction, "Role"), value=str(await Functions.translate(interaction, data[key]['role'])).capitalize(), inline=True)
                embed.add_field(name=await Functions.translate(interaction, "Gender"), value=str(await Functions.translate(interaction, data[key]['gender'])).capitalize(), inline=True)
                for dlc_key in dlc_data.keys():
                    if dlc_key == data[key]['dlc']:
                        embed.add_field(name="DLC", value=f"[{dlc_data[dlc_key]['name'].capitalize().replace(' chapter', '')}]({steamStore}{dlc_data[dlc_key]['steamid']})", inline=True)
                if data[key]['difficulty'] != 'none':
                    embed.add_field(name=await Functions.translate(interaction, "Difficulty"), value=str(await Functions.translate(interaction, data[key]['difficulty'])).capitalize(), inline=True)
                if str(data[key]['role']) == 'killer':
                    embed.add_field(name=await Functions.translate(interaction, "Walkspeed"), value=f"{Functions.safe_int(data[key]['tunables']['MaxWalkSpeed']) / 100}m/s", inline=True)
                    embed.add_field(name=await Functions.translate(interaction, "Terror Radius"), value=f"{Functions.safe_int(data[key]['tunables']['TerrorRadius']) / 100}m", inline=True)
                    embed.add_field(name='\u200b', value='\u200b', inline=True)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                if lang in api_langs and lang != 'en':
                    embed.add_field(name="Bio", value=str(data[key]['bio']).replace('<ul>', '').replace('</ul>', '').replace('<br><br>', '').replace('<br>', '').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.', '. '), inline=False)
                else:
                    embed.add_field(name="Bio", value=await Functions.translate(interaction, str(data[key]['bio']).replace('<ul>', '').replace('</ul>', '').replace('<br><br>', '').replace('<br>', '').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.', '. ')), inline=False)
                if loadout:
                    return embed

                story_text = str(data[key]['story']).replace('<i>', '*').replace('</i>', '*').replace('<ul>', '').replace('</ul>', '').replace('<br><br>', '').replace('<br>', '').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.').replace('.', '. ')
                program_logger.debug(f"Story length: {len(story_text)}")
                if len(story_text) > 4096:
                    story_text = Functions.insert_newlines(story_text)
                    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False, encoding='utf8') as story_file:
                        if lang in api_langs and lang != 'en':
                            story_file.write(story_text)
                        else:
                            story_file.write(await Functions.translate(interaction, story_text))
                    await interaction.followup.send(embed=embed, ephemeral = True)
                    await interaction.followup.send(f"Story of {data[key]['name']}", file=discord.File(f"{story_file.name}"), ephemeral=True)
                    os.remove(story_file.name)
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

    async def item(interaction, item, lang, loadout: bool = False):
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
                embed.add_field(name = await Functions.translate(interaction, 'Rarity'), value = await Functions.translate(interaction, str(data_loc[i]['rarity']).capitalize()))
                bloodweb = "Yes" if data_loc[i]['bloodweb'] == 1 else "No"
                embed.add_field(name = await Functions.translate(interaction, 'Is in Bloodweb'), value = await Functions.translate(interaction, bloodweb))
                embed.add_field(name = await Functions.translate(interaction, 'Role'), value = await Functions.translate(interaction, str(data_loc[i]['role'])))
                if data_loc[i]['event'] is not None:
                    embed.add_field(name = await Functions.translate(interaction, 'Event'), value = str(data_loc[i]['event']))
                if loadout == True:
                    return embed, data_loc[i]['item_type']
                await interaction.followup.send(embed = embed, ephemeral = True)
                return
        else:
            await interaction.followup.send(await Functions.translate(interaction, f"The item {item} doesn't exist."), ephemeral = True)

    async def offering(interaction, offering, lang, loadout: bool = False):
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
                embed.add_field(name = await Functions.translate(interaction, 'Rarity'), value = str(await Functions.translate(interaction, data[item]['rarity'])).capitalize())
                embed.add_field(name = await Functions.translate(interaction, 'Type'), value = await Functions.translate(interaction, data[item]['type']))
                embed.add_field(name = await Functions.translate(interaction, 'Tags'), value = await Functions.translate(interaction, str(data[item]['tags']).replace('[', '').replace(']', '').replace('\'', '')))
                role = data[item]['role'] if data[item]['role'] is not None else "Both"
                embed.add_field(name = await Functions.translate(interaction, 'Role'), value = await Functions.translate(interaction, role))
                embed.add_field(name = '\u200b', value = '\u200b')
                retired = "Yes" if data[item]['retired'] == 1 else "No"
                embed.add_field(name = await Functions.translate(interaction, 'Retired'), value = await Functions.translate(interaction, retired))
                if loadout:
                    return embed
                await interaction.followup.send(embed = embed, ephemeral = True)
                return
        await interaction.followup.send(await Functions.translate(interaction, f"The offering {offering} doesn't exist."), ephemeral = True)

    async def perk(perk, lang, interaction, shrine=False, random=False):
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

        perk = str(Functions.find_key_by_name(perk, data))#.replace(' ', '')

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
        program_logger.debug(perk)

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


#Info
class Info():
    async def addon(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('addons', lang)
        if data is None:
            await interaction.followup.send("Error while loading the addon data.")
            return
        embed = await SendInfo.addon(name, lang, interaction)
        if embed is None:
            await interaction.followup.send(f"There is no addon named {name}.")
        return

    async def adepts(interaction: discord.Integration, steamid):
        await interaction.response.defer()
        try:
            ownesDBD = await SteamApi.ownsGame(steamid, DBD_ID)
        except ValueError:
            await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
            return
        except steam.Errors.Private:
            await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f" [here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
            return
        except steam.Errors.RateLimit:
            embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
            embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.followup.send(embed=embed)
            return
        if not ownesDBD:
            await interaction.followup.send(await Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look") + " [here](https://www.g2a.com/n/dbdstats).")
        else:
            try:
                steamid = await SteamApi.link_to_id(steamid)
            except steam.Errors.RateLimit:
                embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
                embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
                await interaction.followup.send(embed=embed)
                return
            except ValueError:
                await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
                return
            if steamid is None:
                await interaction.followup.send(await Functions.translate(interaction, "The SteamID is not valid."))
                return
            try:
                data = await Functions.check_rate_limit(f'{api_base}playeradepts?steamid={steamid}')
            except Exception as e:
                if e.code == 429:
                    await interaction.followup.send(await Functions.translate(interaction, "The bot got ratelimited. Please try again later. (This error can also appear if the same profile got querried multiple times in a 4h window.)"), ephemeral=True)
                    return
                elif e.code == 404:
                    await interaction.followup.send(await Functions.translate(interaction, "I couldn't find any data for this profile."), ephemeral=True)
                    return
            try:
                steam_data = await SteamApi.get_player_summeries(steamid)
            except ValueError:
                await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
                return
            except steam.Errors.RateLimit:
                embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
                embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
                await interaction.followup.send(embed=embed)
                return
            if steam_data == {}:
                await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f" [here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
                return

            event = steam_data['response']['players'][0]
            personaname = event['personaname']
            profileurl = event['profileurl']
            avatar = event['avatarfull']

            updated_at = data['updated_at']
            entrys_to_remove = ['created_at', 'updated_at', 'steamid']
            for entry in entrys_to_remove:
                data.pop(entry, None)

            data_items = list(data.items())
            data_items.sort()
            data.clear()
            for key, value in data_items:
                data[key] = value

            count = 0
            embeds = []

            async def create_embed():
                embed = discord.Embed(title=await Functions.translate(interaction, "Adept"), description=personaname+'\n'+profileurl, color=0xb19325)
                footer = (await Functions.translate(interaction, "Last update")).replace('.|','. | ')+': '+str(await Functions.convert_time(Functions.safe_int(updated_at)))+" UTC"
                embed.set_thumbnail(url=avatar)
                embed.set_footer(text=footer)
                embed.add_field(name="\u200b", value="\u200b", inline=False)
                return embed
            embed = await create_embed()

            for i in range(0, len(data), 2):
                key1, value1 = list(data.items())[i]
                key2, value2 = list(data.items())[i + 1]
                program_logger.debug(f"{key1}: {value1}")
                program_logger.debug(f"{key2}: {value2}")
                embed.add_field(name=str(key1).replace('_count', '').capitalize(), value=value1, inline=True)
                embed.add_field(name=await Functions.translate(interaction, "Unlocked at"), value=f'<t:{value2}>', inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                count += 1

                if count == 8:
                    embeds.append(embed)
                    count = 0
                    embed = await create_embed()

            if count > 0:
                embeds.append(embed)
                count = 0

            try:
                await interaction.edit_original_response(embeds=embeds)
            except Exception as e:
                program_logger.debug(e)
                for i in range(0, len(embeds), 10):
                    await interaction.followup.send(embeds=embeds[i:i+10])

    async def character(interaction: discord.Interaction, char: str):
        await interaction.response.defer()
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
            await SendInfo.char(interaction, data, char, dlc_data, lang)
            return

    async def dlc(interaction: discord.Interaction, name: str = ''):
        await interaction.response.defer()
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
            num_embeds = -(-num_entries // max_fields_per_embed)

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

    async def event(interaction: discord.Interaction):
        await interaction.response.defer()

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
            embed = discord.Embed(title="Event", description=await Functions.translate(interaction, "Currently there is a event in DeadByDaylight.")+" <a:hyperWOW:1245674053272997998>", color=0x922f2f)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Name"), value=data[current_event]['name'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Type"), value=data[current_event]['type'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Bloodpoint Multiplier"), value=data[current_event]['multiplier'], inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Beginning"), value=str(await Functions.convert_time(data[current_event]['start'])+' UTC'), inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Ending"), value=str(await Functions.convert_time(data[current_event]['end'])+' UTC'), inline=True)
            await interaction.followup.send(embed=embed)
        elif upcoming_event is not None:
            embed = discord.Embed(title="Event", description=await Functions.translate(interaction, "There is a upcoming event in DeadByDaylight.")+" <a:SmugDance:1245674032465051678>", color=0x922f2f)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Name"), value=data[upcoming_event]['name'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Type"), value=data[upcoming_event]['type'], inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Bloodpoint Multiplier"), value=data[upcoming_event]['multiplier'], inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Beginning"), value=str(await Functions.convert_time(data[upcoming_event]['start'])+' UTC'), inline=True)
            embed.add_field(name=await Functions.translate(interaction, "Ending"), value=str(await Functions.convert_time(data[upcoming_event]['end'])+' UTC'), inline=True)
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(title="Event", description=await Functions.translate(interaction, "Currently there is no event in DeadByDaylight.\nAnd none are planned.")+" <:pepe_sad:1245674076736065576>", color=0x922f2f)
            await interaction.followup.send(embed=embed)

    async def item(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('items', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading the item data."))
            return

        await SendInfo.item(interaction, name, lang)
        return

    async def killswitch(interaction: discord.Interaction):
        await interaction.response.defer()

        if os.path.exists(f'{buffer_folder}killswitch.json') and os.path.getmtime(f'{buffer_folder}killswitch.json') > time.time() - 900:
            with open(f'{buffer_folder}killswitch.json', 'r') as f:
                data = json.load(f)
                if data['killswitch_on'] == 0:
                    embed = discord.Embed(title="Killswitch", description=(await Functions.translate(interaction, 'Currently there is no Kill Switch active.')), color=0xb19325)
                    embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
                    embed.set_footer(text = f'Update every 15 minutes.')
                    await interaction.followup.send(embed=embed)
                    return
                else:
                    embed = discord.Embed(title="Killswitch", description=await Functions.translate(interaction, data['md']), color=0xb19325)
                    embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
                    embed.set_footer(text = await Functions.translate(interaction, 'Update every 15 minutes.'))
                    await interaction.followup.send(embed=embed)
                    return
        try:
            data = await killswitch.get_killswitch('md')
        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral = True)
            return

        data = await Functions.translate(interaction, data.replace('\n\n', '[TEMP_NL]').replace('\n', ' ').replace('[TEMP_NL]', '\n\n').strip())

        if data.replace('\n', '').strip() == '':
            embed = discord.Embed(title="Killswitch", description=(await Functions.translate(interaction, 'Currently there is no Kill Switch active.')), color=0xb19325)
            embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
            embed.set_footer(text = await Functions.translate(interaction, 'Update every 15 minutes.'))
            await interaction.followup.send(embed=embed)
            killswitch_on = 0
        elif data is not None:
            embed = discord.Embed(title="Killswitch", description=data, color=0xb19325)
            embed.set_thumbnail(url=f'{bot_base}killswitch.jpg')
            embed.set_footer(text = await Functions.translate(interaction, 'Update every 15 minutes.'))
            await interaction.followup.send(embed=embed)
            killswitch_on = 1

        data_to_save = {
            'md': data,
            'killswitch_on': killswitch_on
            }

        with open(f'{buffer_folder}killswitch.json', 'w') as f:
            json.dump(data_to_save, f, indent=4)

    async def legacycheck(interaction: discord.Interaction, steamid):
        await interaction.response.defer()
        try:
            ownsDBD = await SteamApi.ownsGame(steamid, DBD_ID)
        except ValueError:
            await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
            return
        except steam.Errors.Private:
            await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f" [here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
            return
        except steam.Errors.RateLimit:
            embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
            embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.followup.send(embed=embed)
            return
        if not ownsDBD:
            await interaction.followup.send(await Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look") + " [here](https://www.g2a.com/n/dbdstats).")
        else:

            try:
                data = await SteamApi.get_player_achievements(steamid, DBD_ID)
            except ValueError:
                await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
            except steam.Errors.RateLimit:
                embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
                embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
                await interaction.followup.send(embed=embed)
                return
            if Functions.safe_int(data['playerstats']['steamID']) > 76561198347189883:
                await interaction.followup.send(await Functions.translate(interaction, 'If this player has legacy, they are fraudulent.'))
                return
            if data['playerstats']['success'] == False:
                await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f" [here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
                return
            for entry in data['playerstats']['achievements']:
                if entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 1 and Functions.safe_int(entry['unlocktime']) < 1480017600:
                    await interaction.followup.send(await Functions.translate(interaction, 'This player has probably legit legacy.'))
                    return
                elif entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 1 and Functions.safe_int(entry['unlocktime']) > 1480017600:
                    await interaction.followup.send(await Functions.translate(interaction, 'If this player has legacy, they are probably fraudulent.'))
                    return
                elif entry['apiname'] == 'ACH_PRESTIGE_LVL1' and entry['achieved'] == 0:
                    await interaction.followup.send(await Functions.translate(interaction, "This player doesn't even have one character prestiged."))
                    return

    async def maps(interaction: discord.Interaction, name):
        await interaction.response.defer()
        lang = await Functions.get_language_code(interaction)

        data = await Functions.data_load('maps', lang)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading map-data. Please try again later."))
            return
        for key, value in data.items():
            if key == 'Swp_Mound' or key == '_id':
                continue
            try:
                if value['name'].lower() == name.lower():
                    embed = discord.Embed(title=f"Map description for '{value['name']}'", description=await Functions.translate(interaction, str(value['description']).replace('<br><br>', ' ')), color=0xb19325)
                    embed.set_thumbnail(url=f"{map_portraits}{key}.png")
                    await interaction.followup.send(embed=embed)
                    return
            except AttributeError:
                continue
        await interaction.followup.send(await Functions.translate(interaction, "No map found with this name."))

    async def offering(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        lang = await Functions.get_language_code(interaction)
        data = await Functions.data_load('offerings', 'en')
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading the perk data."), ephemeral=True)
            return
        await SendInfo.offering(interaction, name, lang)

    async def patch(interaction: discord.Interaction, version: str):
        await interaction.response.defer()
        data = await Functions.data_load('patchnotes', version=version)
        if data is None:
            await interaction.followup.send(await Functions.translate(interaction, "Error while loading the patchnotes."))
        else:
            data = data['notes']
            converter = html2text.HTML2Text()
            converter.ignore_links = True
            content = converter.handle(data)
            try:
                await interaction.followup.send(content)
            except discord.errors.HTTPException:
                with open(f'{buffer_folder}patchnotes.md', 'w', encoding='utf8') as f:
                    f.write(content)
                await interaction.followup.send(file=discord.File(f'{buffer_folder}patchnotes.md'))
                os.remove(f'{buffer_folder}patchnotes.md')

    async def perk(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        lang = await Functions.get_language_code(interaction)
        await SendInfo.perk(name, lang, interaction)

    async def playercount(interaction: discord.Interaction):
        async def selfembed(data):
            embed = discord.Embed(title=await Functions.translate(interaction, "Player count"), color=0xb19325)
            embed.set_thumbnail(url=f"{bot_base}dbd.png")
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            embed.add_field(name=await Functions.translate(interaction, "Current"), value=f"{Functions.safe_int(data['Current Players']):,}", inline=True)
            embed.add_field(name=await Functions.translate(interaction, "24h Peak"), value=f"{Functions.safe_int(data['Peak Players 24h']):,}", inline=True)
            embed.add_field(name=await Functions.translate(interaction, "All-time Peak"), value=f"{Functions.safe_int(data['Peak Players All Time']):,}", inline=True)
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
                program_logger.error(f"Error while getting the playercount. Error Code: {error_code} | Error Message: {error_message}")
                program_logger.warning(f"Error while getting the playercount. Error Code: {error_code} | Error Message: {error_message}")
                await interaction.followup.send(f"Error while getting the playercount. Error Code: {error_code} | Error Message: {error_message}")
                return
            data['update_hour'] = datetime.datetime.now().hour
            with open(buffer_folder+'playercount.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            return data
        await interaction.response.defer()
        if os.path.exists(buffer_folder+'playercount.json'):
            with open(buffer_folder+'playercount.json', 'r', encoding='utf8') as f:
                data = json.load(f)
            if data['update_hour'] == datetime.datetime.now().hour and ((time.time() - os.path.getmtime(buffer_folder+'playercount.json')) / 3600) <= 23:
                await selfembed(data)
                return
        await selfembed(await selfget())

    async def playerstats(interaction: discord.Interaction, steamid):
        await interaction.response.defer(thinking=True)
        try:
            steamid = await SteamApi.link_to_id(steamid)
        except steam.Errors.RateLimit:
            embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
            embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            await interaction.followup.send(embed=embed)
            return
        except ValueError:
            await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
            return
        if steamid is None:
            await interaction.followup.send(await Functions.translate(interaction, "The SteamID is not valid."))
            return
        file_path = os.path.join(stats_folder, os.path.basename(f'player_stats_{steamid}.json'))
        if os.path.exists(f'{stats_folder}player_stats_{steamid}.json') and ((time.time() - os.path.getmtime(f'{stats_folder}player_stats_{steamid}.json')) / 3600) <= 4:
            with open(file_path, 'r', encoding='utf8') as f:
                player_stats = json.load(f)
                ownsDBD = True
        else:
            try:
                ownsDBD = await SteamApi.ownsGame(steamid, DBD_ID)
            except ValueError:
                await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
                return
            except steam.Errors.Private:
                await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f" [here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
                return
            except steam.Errors.RateLimit:
                embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
                embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
                await interaction.followup.send(embed=embed)
                return
        if not ownsDBD:
            await interaction.followup.send(await Functions.translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look")+" [here](https://www.g2a.com/n/dbdstats).")
            return
        else:
            #Get Stats
            if 'player_stats' not in locals(): # This means, that the stats are not loaded from the file.
                try:
                    player_stats = await Functions.check_rate_limit(f'{api_base}playerstats?steamid={steamid}')
                except Exception:
                    removed = await Functions.check_if_removed(steamid)
                    if removed == 2:
                        await interaction.followup.send(await Functions.translate(interaction, "The bot is currently rate limited. Please try again later."), ephemeral=True)
                        return
                    elif removed == 3:
                        embed = discord.Embed(title="Statistics", url=f'https://www.dbd-info.com/player-profile/{steamid}/overview', description=(await Functions.translate(interaction, "It looks like this profile has been banned from displaying on our leaderboard.\nThis probably happened because achievements or statistics were manipulated.\nI can therefore not display any information in an embed.\nIf you still want to see the full statistics, please click on the link.")), color=0xb19325)
                        await interaction.followup.send(embed=embed)
                        return
                    elif removed != 0:
                        await interaction.followup.send(content = removed)
                        return
                with open(file_path, 'w', encoding='utf8') as f:
                    json.dump(player_stats, f, indent=2)
            try:
                steam_data = await SteamApi.get_player_summeries(steamid)
            except ValueError:
                await interaction.followup.send(f'`{steamid}` {await Functions.translate(interaction, "is not a valid SteamID/Link.")}')
                return
            except steam.Errors.RateLimit:
                embed = discord.Embed(title="Fatal Error", description=f"{await Functions.translate(interaction, 'It looks like the bot ran into a rate limit, while querying the SteamAPI. Please join our')} [Support-Server]({str(await Functions.create_support_invite(interaction))}){await Functions.translate(interaction, ') and create a ticket to tell us about this.')}", color=0xff0000)
                embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
                await interaction.followup.send(embed=embed)
                return
            if steam_data == {}:
                await interaction.followup.send(await Functions.translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking") + f" [here](https://steamcommunity.com/my/edit/settings?snr=).", suppress_embeds = True)
                return
            await interaction.followup.send(await Functions.translate(interaction, "Loading stats. This can take a while, if something needs to be translated."))

            event = steam_data['response']['players'][0]
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
            footer = (await Functions.translate(interaction, "Stats are updated every ~4h. | Last update: ")).replace('.|','. | ')+str(await Functions.convert_time(Functions.safe_int(player_stats['updated_at'])))+" UTC"

            for embed in embeds:
                embed.set_thumbnail(url=avatar)
                embed.set_footer(text=footer)

            #Embed1 - Survivor
            await Functions.safe_add_field(embed1, "Bloodpoints Earned", "bloodpoints", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Rank", "survivor_rank", player_stats, interaction)
            embed1.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed1, "Full loadout Games", "survivor_fullloadout", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Perfect Games", "survivor_perfectgames", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Generators repaired", "gensrepaired", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Gens without Perks", "gensrepaired_noperks", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Damaged gens repaired", "damagedgensrepaired", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Successful skill checks", "skillchecks", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Items Depleted", "itemsdepleted", player_stats, interaction, inline=False)
            await Functions.safe_add_field(embed1, "Hex Totems Cleansed", "hextotemscleansed", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Hex Totems Blessed", "hextotemsblessed", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Blessed Boosts", "blessedtotemboosts", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Exit Gates Opened", "exitgatesopened", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Hooks Sabotaged", "hookssabotaged", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Chests Searched", "chestssearched", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Chests Searched in the Basement", "chestssearched_basement", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Mystery boxes opened", "mysteryboxesopened", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Killers aura revealed", "killersaurarevealed", player_stats, interaction)
            await Functions.safe_add_field(embed1, "Screams", "screams", player_stats, interaction)
            # Embed2 - Killer Interactions
            embed2.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed2, "Dodged basic attack or projectiles", "dodgedattack", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Escaped chase after pallet stun", "escapedchase_palletstun", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Escaped chase injured after hit", "escapedchase_healthyinjured", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Escape chase by hiding in locker", "escapedchase_hidinginlocker", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Protection hits for unhooked survivor", "protectionhits_unhooked", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Protectionhits while a survivor is carried", "protectionhits_whilecarried", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Vaults while in chase", "vaultsinchase", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Dodge attack before vaulting", "vaultsinchase_missed", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Wiggled from killers grasp", "wiggledfromkillersgrasp", player_stats, interaction)
            await Functions.safe_add_field(embed2, "Killers blinded with a flashlight", "killerblinded_flashlight", player_stats, interaction)
            # Embed3 - Healing/Saves
            embed3.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed3, "Survivors healed", "survivorshealed", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors healed while injured", "survivorshealed_whileinjured", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors healed while 3 others not healthy", "survivorshealed_threenothealthy", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors healed who found you while injured", "survivorshealed_foundyou", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors healed from dying state to injured", "healeddyingtoinjured", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Obsessions healed", "obsessionshealed", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors healed while in the basement", "survivorshealed_basement", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors saved (from death)", "saved", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Survivors saved during endgame", "saved_endgame", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Killers pallet stunned while carrying a survivor", "killerstunned_palletcarrying", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Killers stunned while holding item", "killerstunned_holdingitem", player_stats, interaction)
            await Functions.safe_add_field(embed3, "Kobed", "unhookedself", player_stats, interaction)
            # Embed4 - Escaped
            embed4.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed4, "While healthy/injured", "escaped", player_stats, interaction)
            await Functions.safe_add_field(embed4, "While crawling", "escaped_ko", player_stats, interaction)
            await Functions.safe_add_field(embed4, "After kobed", "hooked_escape", player_stats, interaction)
            await Functions.safe_add_field(embed4, "Through the hatch", "escaped_hatch", player_stats, interaction)
            await Functions.safe_add_field(embed4, "Through the hatch while crawling", "escaped_hatchcrawling", player_stats, interaction)
            await Functions.safe_add_field(embed4, "Through the hatch with everyone", "escaped_allhatch", player_stats, interaction)
            await Functions.safe_add_field(embed4, "After been downed once", "escaped_downedonce", player_stats, interaction)
            await Functions.safe_add_field(embed4, "After been injured for half of the trial", "escaped_injuredhalfoftrail", player_stats, interaction)
            await Functions.safe_add_field(embed4, "With no bloodloss as obsession", "escaped_nobloodlossobsession", player_stats, interaction)
            await Functions.safe_add_field(embed4, "Last gen last survivor", "escaped_lastgenlastsurvivor", player_stats, interaction)
            await Functions.safe_add_field(embed4, "With new item", "escaped_newitem", player_stats, interaction)
            await Functions.safe_add_field(embed4, "With item from someone else", "escaped_withitemfrom", player_stats, interaction)
            # Embed5 - Repaired second floor generator and escaped
            embed5.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed5, "Disturbed Ward", "secondfloorgen_disturbedward", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Father Campbells Chapel", "secondfloorgen_fathercampbellschapel", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Mothers Dwelling", "secondfloorgen_mothersdwelling", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Temple of Purgation", "secondfloorgen_templeofpurgation", player_stats, interaction)
            await Functions.safe_add_field(embed5, "The Game", "secondfloorgen_game", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Family Residence", "secondfloorgen_familyresidence", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Sanctum of Wrath", "secondfloorgen_sanctumofwrath", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Mount Ormond", "secondfloorgen_mountormondresort", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Lampkin Lane", "secondfloorgen_lampkinlane", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Pale Rose", "secondfloorgen_palerose", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Hawkins", "secondfloorgen_undergroundcomplex", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Treatment Theatre", "secondfloorgen_treatmenttheatre", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Dead Dawg Saloon", "secondfloorgen_deaddawgsaloon", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Midwich", "secondfloorgen_midwichelementaryschool", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Raccoon City", "secondfloorgen_racconcitypolicestation", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Eyrie of Crows", "secondfloorgen_eyrieofcrows", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Garden of Joy", "secondfloorgen_gardenofjoy", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Shattered Square", "secondfloorgen_shatteredsquare", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Shelter Woods", "secondfloorgen_shelterwoods", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Toba Landing", "secondfloorgen_tobalanding", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Nostromo Wreckage", "secondfloorgen_messhall", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Greenville Square", "secondfloorgen_greenvillesquare", player_stats, interaction)
            await Functions.safe_add_field(embed5, "Forgotten Ruins", "secondfloorgen_forgottenruins", player_stats, interaction)
            # Embed6 - Killer Stats
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Rank"), "killer_rank", player_stats, interaction)
            embed6.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Played with full loadout"), "killer_fullloadout", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Perfect Games"), "killer_perfectgames", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Survivors Killed"), "killed", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Survivors Sacrificed"), "sacrificed", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Sacrificed all before last gen"), "sacrificed_allbeforelastgen", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Killed/Sacrificed after last gen"), "killed_sacrificed_afterlastgen", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Killed all 4 with tier 3 Myers"), "killed_allevilwithin", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Obsessions Sacrificed"), "sacrificed_obsessions", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Hatches Closed"), "hatchesclosed", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Gens damaged while 1-4 survivors are hooked"), "gensdamagedwhileonehooked", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Gens damaged while undetectable"), "gensdamagedwhileundetectable", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Grabbed while repairing a gen"), "survivorsgrabbedrepairinggen", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Grabbed while you are hiding in locker"), "survivorsgrabbedfrominsidealocker", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Hit one who dropped a pallet in chase"), "survivorshit_droppingpalletinchase", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Hit while carrying"), "survivorshit_whilecarrying", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Interrupted cleansing"), "survivorsinterruptedcleansingtotem", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Vaults while in chase"), "vaultsinchase_askiller", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Survivors made scream"), "survivorscreams", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Survivors injured while in basement"), "survivorsinjured_basement", player_stats, interaction)
            await Functions.safe_add_field(embed6, await Functions.translate(interaction, "Survivors interupted while vaulting"), "survivorsinterupted_vaulting", player_stats, interaction)
            # Embed7 - Hooked
            embed7.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed7, await Functions.translate(interaction, "Survivors hooked before a generator is repaired"), "survivorshookedbeforegenrepaired", player_stats, interaction)
            await Functions.safe_add_field(embed7, await Functions.translate(interaction, "Survivors hooked during end game collapse"), "survivorshookedendgamecollapse", player_stats, interaction)
            await Functions.safe_add_field(embed7, await Functions.translate(interaction, "Hooked a survivor while 3 other survivors were injured"), "hookedwhilethreeinjured", player_stats, interaction)
            await Functions.safe_add_field(embed7, await Functions.translate(interaction, "3 Survivors hooked in basement"), "survivorsthreehookedbasementsametime", player_stats, interaction)
            embed7.add_field(name="\u200b", value="\u200b")
            await Functions.safe_add_field(embed7, await Functions.translate(interaction, "Survivors hooked in basement"), "survivorshookedinbasement", player_stats, interaction)
            # Embed8 - Powers
            embed8.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Beartrap Catches"), "beartrapcatches", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Uncloak Attacks"), "uncloakattacks", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Chainsaw Hits  (Billy)"), "chainsawhits", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Blink Attacks"), "blinkattacks", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Phantasms Triggered"), "phantasmstriggered", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Hit each survivor after teleporting to phantasm trap"), "survivorshit_afterteleporting", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Evil Within Tier Ups"), "evilwithintierup", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Shock Therapy Hits"), "shocked", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Trials with all survivors in madness tier 3"), "survivorsallmaxmadness", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Hatchets Thrown"), "hatchetsthrown", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Pulled into Dream State"), "dreamstate", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Reverse Bear Traps Placed"), "rbtsplaced", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Cages of Atonement"), "cagesofatonement", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Lethal Rush Hits"), "lethalrushhits", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Lacerations"), "lacerations", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Possessed Chains"), "possessedchains", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Condemned"), "condemned", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Slammed"), "slammedsurvivors", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Damaged while pursued by Guard"), "survivorsdamagedpursuedbyguard", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Tailattacks"), "tailattacks", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Survivor hit 3 sec after scamper"), "survivorshit_scamper", player_stats, interaction)
            await Functions.safe_add_field(embed8, await Functions.translate(interaction, "Hellfire Hits"), "hellfirehits", player_stats, interaction)
            # Embed9 - Survivors downed
            embed9.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed9, await Functions.translate(interaction, "Downed while hindered"), "survivorsdowned_hindered", player_stats, interaction)
            await Functions.safe_add_field(embed9, await Functions.translate(interaction, "Downed while oblivious"), "survivorsdowned_oblivious", player_stats, interaction)
            await Functions.safe_add_field(embed9, await Functions.translate(interaction, "Downed while exposed"), "survivorsdowned_exposed", player_stats, interaction)
            await Functions.safe_add_field(embed9, await Functions.translate(interaction, "Downed near a raised pallet"), "survivorsdowned_nearraisedpallet", player_stats, interaction)
            await Functions.safe_add_field(embed9, await Functions.translate(interaction, "Downed while carrying survivor"), "survivorsdowned_whilecarrying", player_stats, interaction)
            #Embed10 - Survivors downed with power
            embed10.add_field(name="\u200b", value="\u200b", inline=False)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed with a Hatchet (24+ meters)"), "survivorsdowned_hatchets", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed with a Chainsaw (Bubba)"), "survivorsdowned_chainsaw", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while Intoxicated"), "survivorsdowned_intoxicated", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed after Haunting"), "survivorsdowned_haunting", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while in Deep Wound"), "survivorsdowned_deepwound", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while having max sickness"), "survivorsdowned_maxsickness", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while marked (Ghostface)"), "survivorsdowned_marked", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while using Shred"), "survivorsdowned_shred", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while using Blood Fury"), "survivorsdowned_bloodfury", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while Speared"), "survivorsdowned_speared", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while Victor is clinging to them"), "survivorsdowned_victor", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while contaminated"), "survivorsdowned_contaminated", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while using Dire Crows"), "survivorsdowned_direcrows", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed while exposed by Lock On"), "survivorsdowned_lockon", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed during nightfall"), "survivorsdowned_nightfall", player_stats, interaction)
            await Functions.safe_add_field(embed10, await Functions.translate(interaction, "Downed using UVX"), "survivorsdowned_uvx", player_stats, interaction)
            #Send Statistics
            embeds = [embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed8, embed9, embed10]
            await interaction.delete_original_response()
            await interaction.followup.send(embeds=embeds[0:5])
            await interaction.followup.send(embeds=embeds[5:10])

    async def rankreset(interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{api_base}rankreset') as resp:
                data = await resp.json()
        embed = discord.Embed(description=f"{await Functions.translate(interaction, 'The next rank reset will take place on the following date: ')}\n<t:{data['rankreset']}>.", color=0x0400ff)
        await interaction.response.send_message(embed=embed)

    async def shrine(interaction: discord.Interaction = None, channel_id: tuple = ''):
        if channel_id != '':
            channel = await Functions.get_or_fetch('channel', channel_id[1])
            if channel is None:
                program_logger.info(f"Channel <#{channel_id[1]}> not found. Removing from db.")
                c.execute(f"DELETE FROM shrine WHERE channel_id = {channel_id[1]}")
                conn.commit()
                return
            guild: discord.Guild = await Functions.get_or_fetch('guild', channel_id[0])
            if guild is None:
                program_logger.info(f"Guild {channel_id[0]} not found. Removing from db.")
                c.execute(f"DELETE FROM shrine WHERE guild_id = {channel_id[0]}")
                conn.commit()
                return
            data = await Functions.data_load('shrine')
            if data is None:
                return
            embeds = []
            for shrine in data['data']['perks']:
                program_logger.debug(shrine)
                shrine_embed = await SendInfo.perk(shrine['name'], guild.preferred_locale[1][:2], None, shrine=True)
                shrine_embed.set_footer(text=f"Bloodpoints: {Functions.safe_int(shrine['bloodpoints']):,} | Shards: {Functions.safe_int(shrine['shards']):,}\n{await Functions.translate(guild, 'Usage by players')}: {await Functions.translate(guild, shrine['usage_tier'])}")
                embeds.append(shrine_embed)
            try:
                await channel.send(content = f"{await Functions.translate(guild, "This is the current shrine.\nIt started at")} <t:{Functions.convert_to_unix_timestamp(data['data']['start'])}> {await Functions.translate(guild, "and will last until")} <t:{Functions.convert_to_unix_timestamp(data['data']['end'])}>.\n{await Functions.translate(guild, "Updates every 15 minutes.")}", embeds=embeds)
            except discord.errors.Forbidden:
                program_logger.info(f"Missing permissions in {guild.name} ({guild.id})")
                c.execute(f"DELETE FROM shrine WHERE guild_id = {guild.id} AND channel_id = {channel.id}")
                conn.commit()
            return
        else:
            await interaction.response.defer()
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
                program_logger.debug(shrine)
                shrine_perk_name = Functions.find_key_by_name(shrine['name'], perk_data_en)
                shrine_embed = await SendInfo.perk(shrine_perk_name, lang, interaction, True)
                shrine_embed.set_footer(text=f"Bloodpoints: {Functions.safe_int(shrine['bloodpoints']):,} | Shards: {Functions.safe_int(shrine['shards']):,}\n{await Functions.translate(interaction, 'Usage by players')}: {await Functions.translate(interaction, shrine['usage_tier'])}")
                embeds.append(shrine_embed)
            try:
                await interaction.followup.send(content = f"{await Functions.translate(interaction, "This is the current shrine.\nIt started at")} <t:{Functions.convert_to_unix_timestamp(data['data']['start'])}> {await Functions.translate(interaction, "and will last until")} <t:{Functions.convert_to_unix_timestamp(data['data']['end'])}>.\n{await Functions.translate(interaction, "Updates every 15 minutes.")}", embeds=embeds)
            except discord.errors.Forbidden:
                program_logger.info(f"Missing permissions in {guild.name} ({guild.id})")
                c.execute(f"DELETE FROM shrine WHERE guild_id = {guild.id} AND channel_id = {channel.id}")
                conn.commit()

    async def twitch_info(interaction: discord.Interaction):
        await interaction.response.defer()
        if not isTwitchAvailable:
            await interaction.followup.send(await Functions.translate(interaction, "Twitch API is currently not available.\nAsk the owner of this instance to enable it."), ephemeral=True)
            return

        data = await Functions.data_load('twitch')

        embeds = []

        embed = discord.Embed(title=f"Twitch Info - <t:{data['updated_at']}>", url="https://www.twitch.tv/directory/game/Dead%20by%20Daylight", description="Statistics", color=0xff00ff)
        embed.set_thumbnail(url=data['image'])
        embed.set_footer(text=f"Update every 5 minutes.")
        embed.add_field(name="Total Viewers", value=f"{Functions.safe_int(data['viewer_count']):,}", inline=True)
        embed.add_field(name="Total Streams", value=f"{Functions.safe_int(data['stream_count']):,}", inline=True)
        embed.add_field(name="\u00D8 Viewer/Stream", value=f"{Functions.safe_int(data['average_viewer_count']):,}", inline=True)
        embed.add_field(name="Current Rank", value=f"{Functions.safe_int(data['category_rank']):,}", inline=False)
        embeds.append(embed)
        for streamer in data['top_streamers'].values():
            embed = discord.Embed(title=streamer['streamer'], description=streamer['title'], color=0xffb8ff)
            embed.set_thumbnail(url=streamer['thumbnail'])
            embed.add_field(name="Viewer", value=f"{Functions.safe_int(streamer['viewer_count']):,}", inline=True)
            embed.add_field(name="Follower", value=f"{Functions.safe_int(streamer['follower_count']):,}", inline=True)
            embed.add_field(name="\u200b", value=f"[Stream]({streamer['link']})", inline=True)
            embed.add_field(name="Language", value=await Functions.get_language_name(streamer['language']), inline=True)
            embed.set_footer(text=f"Started at: {streamer['started_at']}")
            embeds.append(embed)

        await interaction.followup.send(embeds=embeds)

    async def version(interaction: discord.Interaction):
        await interaction.response.defer()
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
            if i <= 6:
                embed1.add_field(name='\u200b', value=key.capitalize(), inline=True)
                embed1.add_field(name='\u200b', value=data[key]['version'], inline=True)
                embed1.add_field(name='\u200b', value=str(await Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
            if i >= 7:
                embed2.add_field(name='\u200b', value=key.capitalize(), inline=True)
                embed2.add_field(name='\u200b', value=data[key]['version'], inline=True)
                embed2.add_field(name='\u200b', value=str(await Functions.convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
        await interaction.followup.send(embeds=[embed1, embed2])


#Random
class Random():
    async def addon_killer(interaction: discord.Interaction, killer, lang, loadout: bool = False):
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
            embed = await SendInfo.addon(entry['name'], lang, interaction, True)
            embeds.append(embed)
        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral = True)
        return

    async def addon_survivor(interaction: discord.Interaction, parent, lang, loadout: bool = False):
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

            embed = await SendInfo.addon(entry['name'], lang, interaction, True)
            embeds.append(embed)
            selected_keys.append(key)

        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral = True)
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
                return await SendInfo.char(interaction, chars, entry['name'], dlc_data, lang, True), entry['id'], entry['role']
            await SendInfo.char(interaction, chars, entry['name'], dlc_data, lang)
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
            temp = await SendInfo.item(interaction, entry['name'], lang, True)
            return temp[0], temp[1]
        await SendInfo.item(interaction, entry['name'], lang)
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
            addon = await Random.addon_survivor(interaction, item[1], lang, True)
            if addon is not None:
                embeds.extend(addon)
        elif char[2] == 'killer':
            killer_item = await Functions.find_killer_item(char[1], chars)
            killer = await Functions.find_killer_by_item(killer_item, chars)
            addon = await Random.addon_killer(interaction, killer, lang, True)
            if addon is not None:
                embeds.extend(addon)

        perks = await Random.perk(interaction, 4, char[2], lang, True)
        embeds.extend(perks)
        offering = await Random.offering(interaction, char[2], lang, True)
        embeds.append(offering)

        await interaction.followup.send(embeds=embeds)

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
                return await SendInfo.offering(interaction, entry['name'], lang, True)
            await SendInfo.offering(interaction, entry['name'], lang)
            return

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
            program_logger.debug(entry['name'])
            embed = await SendInfo.perk(entry['name'], lang, interaction, False, True)
            embeds.append(embed)
        if not embeds:
            await interaction.followup.send(f"No perks found for {role}.", ephemeral=True)
            return
        if loadout:
            return embeds
        await interaction.followup.send(embeds=embeds, ephemeral=True)


#Owner Commands
class Owner():
    async def activity(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'activity [playing/streaming/listening/watching/competing] [title] (url) - Set the activity of the bot\n'
                                       '```')
        def isURL(string):
            try:
                result = urlparse(string)
                return all([result.scheme, result.netloc])
            except:
                return False

        def remove_and_save(listing):
            if listing and isURL(listing[-1]):
                return listing.pop()
            else:
                return None

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        url = remove_and_save(args[1:])
        title = ' '.join(args[1:])
        program_logger.debug(title)
        program_logger.debug(url)
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
            program_logger.warning(f'Error while reading the changelog file.')
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
            guild = await Functions.get_or_fetch('guild', entry[1])
            if channel is None:
                program_logger.info(f"Channel {entry[2]} not found. Removing from db.")
                c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                published_total += 1
                continue
            if not send_as_file:
                try:
                    # await channel.send(await Functions.translate(guild, text))
                    await channel.send(text)
                    published_success += 1
                    published_total += 1
                except discord.errors.NotFound:
                    program_logger.info(f"Channel {entry[2]} not found. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except discord.errors.Forbidden:
                    program_logger.info(f"Missing permissions in channel {entry[2]}. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except:
                    program_logger.warning(f'Error while publishing the changelog to {entry[2]}.')
                    published_total += 1
            else:
                try:
                    temp_changelog = f'{buffer_folder}changelogTEMP.txt'
                    with open(changelog, 'rb') as f:
                        with open(temp_changelog, 'wb') as f2:
                            f2.write(await Functions.translate(guild, f.read()))
                    await channel.send(file=discord.File(temp_changelog))
                    os.remove(temp_changelog)
                    published_success += 1
                    published_total += 1
                except discord.errors.NotFound:
                    program_logger.info(f"Channel {entry[2]} not found. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except discord.errors.Forbidden:
                    program_logger.info(f"Missing permissions in channel {entry[2]}. Removing from db.")
                    c.execute("DELETE FROM changelogs WHERE channel_id = ?", (entry[2],))
                    published_total += 1
                except:
                    program_logger.warning(f'Error while publishing the changelog to {entry[2]}.')
                    published_total += 1
        os.remove(changelog)
        conn.commit()
        await reply.edit(content = f'Published to `{published_success}/{published_total}` channels.')

    async def clean(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'clean [translation/cache] - Deletes the cache for the selected stuff.\n'
                                       '```')
        if args == []:
            await __wrong_selection()
            return
        if args[0] == 'translation':
            if isDbAvailable:
                await db[DB_NAME].translations.drop()
            translations = f"{buffer_folder}translations.json"
            if os.path.exists(translations):
                os.remove(translations)
            await message.channel.send('Translations deleted.')
        elif args[0] == 'cache':
            if isDbAvailable:
                await db.drop_database(DB_NAME)
            for root, _, files in os.walk(buffer_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
            await Cache.start_cache_update()
            await message.channel.send('All cached files deleted and rebuild.')
        else:
            await __wrong_selection()

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
                if Functions.safe_int(args[0]) < 1:
                    await __wrong_selection()
                    return
                else:
                    lines = Functions.safe_int(args[0])
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

    async def shutdown(message):
        global shutdown
        program_logger.info('Engine powering down...')
        try:
            await message.channel.send('Engine powering down...')
        except:
            await owner.send('Engine powering down...')
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        conn.close()
        await db.close()

        await bot.close()

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
        
    async def broadcast(message):
        already_send = []
        success = 0
        forbidden = 0
        error = 0
        for guild in bot.guilds:
            guild_owner = await Functions.get_or_fetch('user', guild.owner_id)
            if guild_owner.id in already_send:
                continue
            try:
                await guild_owner.send(f'Broadcast from the owner of the bot:\n{message}')
                success += 1
                already_send.append(guild_owner.id)
            except discord.Forbidden:
                forbidden += 1
            except Exception as e:
                error += 1
        await owner.send(f'Broadcast finished.\nSuccess: {success}\nForbidden: {forbidden}\nError: {error}')


#Autocompletion
class AutoComplete:
    def __init__(self) -> None:
        messages = {
        'de': 'Bot startet...',
        'en': 'Bot is starting...',
        'es': 'El bot está empezando...',
        'fr': 'Bot commence...',
        'ja': 'ボットが起動しています...',
        'ko': '봇이 시작됩니다...',
        'pl': 'Bot się uruchamia...',
        'pt-BR': 'O bot está iniciando...',
        'ru': 'Бот запускается...',
        'zh-TW': '机器人正在启动...',
        }
        categories = ["addon", "char", "killer", "dlc", "item", "map", "offering", "perk"]
        for category in categories:
            for lang in api_langs:
                global_var_name = f"{category}_names_{lang}"
                globals()[global_var_name] = [messages[lang]]
        program_logger.debug("Autocompletion initialized.")
        self.returnsize = 25



    async def get_localized_list(self, interaction: discord.Interaction, list_type: Literal['addon', 'char', 'killer', 'dlc', 'item', 'map', 'offering', 'perk']) -> List[str]:
        lang = await Functions.get_language_code(interaction)
        if lang not in api_langs:
            lang = 'en'
        list_name = f'{list_type}_names_{lang}'
        return globals()[list_name]

    async def addons(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        addon_list = await self.get_localized_list(interaction, 'addon')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in addon_list[:self.returnsize]]
        matching_names = [name for name in addon_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def character(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        char_list = await self.get_localized_list(interaction, 'char')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in char_list[:self.returnsize]]
        matching_names = [name for name in char_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def killer(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        killer_list = await self.get_localized_list(interaction, 'killer')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in killer_list[:self.returnsize]]
        matching_names = [name for name in killer_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def dlcs(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        dlc_list = await self.get_localized_list(interaction, 'dlc')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in dlc_list[:self.returnsize]]
        matching_names = [name for name in dlc_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def items(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        item_list = await self.get_localized_list(interaction, 'item')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in item_list[:self.returnsize]]
        matching_names = [name for name in item_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def maps(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        map_list = await self.get_localized_list(interaction, 'map')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in map_list[:self.returnsize]]
        matching_names = [name for name in map_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def offerings(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        offering_list = await self.get_localized_list(interaction, 'offering')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in offering_list[:self.returnsize]]
        matching_names = [name for name in offering_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def perks(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        perk_list = await self.get_localized_list(interaction, 'perk')
        if not current:
            return [discord.app_commands.Choice(name=name, value=name) for name in perk_list[:self.returnsize]]
        matching_names = [name for name in perk_list if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]

    async def patchversions(self, interaction: discord.Interaction, current: str = '') -> List[discord.app_commands.Choice[str]]:
        if not current:
            return [discord.app_commands.Choice(name=version, value=version) for version in patch_versions[:self.returnsize]]
        matching_names = [name for name in patch_versions if current.lower() in name.lower()]
        return [discord.app_commands.Choice(name=name, value=name) for name in matching_names[:self.returnsize]]
autocomplete = AutoComplete()



##Bot Commands (These commands are for the bot itself.)
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
async def ping(interaction: discord.Interaction):
        before = time.monotonic()
        await interaction.response.send_message('Pong!')
        ping = (time.monotonic() - before) * 1000
        await interaction.edit_original_response(content=f'Pong! \nCommand execution time: `{Functions.safe_int(ping)}ms`\nPing to gateway: `{Functions.safe_int(bot.latency * 1000 if interaction.guild is None else bot.shards.get(interaction.guild.shard_id).latency * 1000)}ms`')

#Bot Info
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def botinfo(interaction: discord.Interaction):
        member_count = sum(guild.member_count for guild in bot.guilds)

        embed = discord.Embed(
            title=f"Information about {bot.user.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

        embed.add_field(name="Created at", value=bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), inline=True)
        embed.add_field(name="Version", value=bot_version, inline=True)
        embed.add_field(name="Uptime", value=str(datetime.timedelta(seconds=Functions.safe_int((datetime.datetime.now() - start_time).total_seconds()))), inline=True)

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

        if interaction.user.id == Functions.safe_int(OWNERID):
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
async def subscribe(interaction: discord.Interaction,
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
async def translation_info(interaction: discord.Interaction):
        await interaction.response.defer(thinking = True, ephemeral = True)

        if interaction.guild is None:
            await interaction.response.send_message(await Functions.translate(interaction, 'This command can only be used in a server.'))
            return
        embed = discord.Embed(title = 'Translation', color = 0x00ff00)
        embed.description = await Functions.translate(interaction, 'This bot is translated into the following languages:')
        temp = []
        for lang in api_langs:
            lang = await Functions.get_language_name(lang)
            temp.append(lang)
            embed.description += f'\n• {lang}'
        embed.description += f"\n\n{await Functions.translate(interaction, 'For these languages, the bot uses GoogleTranslate (LibreTranslate as backup), to translate the text, which can be a bit whacky. That is the reason, we only output these languages. For the input, you still have to use english.')}"
        # Merge two lists
        languages = sorted(list(set(libre_languages + google_languages)))
        for lang in languages:
            if lang not in temp:
                embed.description += f'\n• {lang}'
        embed.description += f"\n\n{await Functions.translate(interaction, 'The bot will automatically select the language based on the client who invokes a comand. If you sub to the shrine, he will post it in the language of the server (community). If he can not translate to that language, he will default to english.')}"
        await interaction.followup.send(embed = embed, ephemeral = True)

#Support Invite
@tree.command(name = 'support', description = 'Get invite to our support server.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def support(interaction: discord.Interaction):
        if str(interaction.guild.id) != SUPPORTID:
            await interaction.response.defer(ephemeral = True)
            await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral = True)
        else:
            await interaction.response.send_message('You are already in our support server!', ephemeral = True)


##DBD Commands (these commands are for DeadByDaylight.)
#Buy
@tree.command(name = "buy", description = 'This will post a link to a site where you can buy DeadByDaylight for a few bucks.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
async def buy(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(await Functions.translate(interaction, "This command can only be used in a server."))
    else:
        embed = discord.Embed(title="Buy Dead By Daylight", description=await Functions.translate(interaction, "Click the title, to buy the game for a few bucks."), url="https://www.g2a.com/n/dbdstats", color=0x00ff00)
        await interaction.response.send_message(embed=embed)


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
                               perk = 'Only used if "Perks" is selected. Start writing to search...',
                               patch = 'Only used if "Patchnotes" is selected. Start writing to search...',
                               )
@discord.app_commands.autocomplete(addon=autocomplete.addons,
                                   character=autocomplete.character,
                                   dlc=autocomplete.dlcs,
                                   item=autocomplete.items,
                                   map=autocomplete.maps,
                                   offering=autocomplete.offerings,
                                   perk=autocomplete.perks,
                                   patch=autocomplete.patchversions
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
    discord.app_commands.Choice(name = 'Player-Adept', value = 'adept'),
    discord.app_commands.Choice(name = 'Rankreset', value = 'reset'),
    discord.app_commands.Choice(name = 'Shrine', value = 'shrine'),
    discord.app_commands.Choice(name = 'Twitch', value = 'twitch'),
    discord.app_commands.Choice(name = 'Versions', value = 'version')
    ])
async def info(interaction: discord.Interaction,
               category: str,
               addon: str = None,
               character: str = None,
               dlc: str = None,
               item: str = None,
               map: str = None,
               offering: str = None,
               patch: str = None,
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
                info.timeout = 30
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
                info.timeout = 30
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
            if patch is None:
                await interaction.response.send_message(await Functions.translate(interaction, "You need to specify a patch version."))
            else:
                await Info.patch(interaction, version = patch)

        elif category == 'adept':
            class Input(discord.ui.Modal, title = 'Enter SteamID64. Timeout in 30 seconds.'):
                info.timeout = 30
                answer = discord.ui.TextInput(label = 'ID64 or vanity(url) you want adepts for.', style = discord.TextStyle.short, required = True)
                async def on_submit(self, interaction: discord.Interaction):
                    await Info.adepts(interaction, steamid = self.answer.value.strip())
            await interaction.response.send_modal(Input())

        else:
            await interaction.response.send_message('Invalid category.', ephemeral=True)

#Randomize
@tree.command(name = 'random', description = 'Get a random perk, offering, map, item, char or full loadout.')
@discord.app_commands.checks.cooldown(2, 30, key=lambda i: (i.user.id))
@discord.app_commands.describe(category = 'What do you want to randomize?',
                               item = 'Only used if "Addon" is selected.',
                               killer = 'Only used if "Addon for Killer" is selected. Start writing to search...'
                               )
@discord.app_commands.autocomplete(killer=autocomplete.killer)
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
async def random_func(interaction: discord.Interaction,
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

                    x = Functions.safe_int(x)
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
            await Random.addon_survivor(interaction, item, lang)

        elif category == 'adfk':
            if killer is None:
                await interaction.response.send_message(content='You need to specify a killer.', ephemeral=True)
                return
            lang = await Functions.get_language_code(interaction)
            await Random.addon_killer(interaction, killer, lang)

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
    if not TOKEN:
        error_message = 'Missing token. Please check your .env file.'
        program_logger.critical(error_message)
        sys.exit(error_message)
    else:
        try:
            SignalHandler()
            asyncio.run(Functions.build_lang_lists())
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            error_message = 'Invalid token. Please check your .env file.'
            program_logger.critical(error_message)
            sys.exit(error_message)
        except asyncio.CancelledError:
            if shutdown:
                pass
