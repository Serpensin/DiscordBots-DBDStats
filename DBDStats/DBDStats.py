#Import
import discord
#from discord.ext import commands
import requests as r
import time
import logging
import logging.handlers
import os
from zipfile import ZIP_LZMA, ZipFile
#from sys import exit
import json
from random import randrange
from datetime import timedelta, datetime
from googletrans import Translator
from bs4 import BeautifulSoup


#Set vars
api_base = 'https://dbd.tricky.lol/api/'                                
perks_base = 'https://dbd.tricky.lol/dbdassets/perks/'
map_portraits = 'https://cdn.bloodygang.com/botfiles/mapportraits/'
char_portraits = 'https://cdn.bloodygang.com/botfiles/charportraits/'   
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
log_folder = 'DBDStats//Logs'
buffer_folder = 'DBDStats//Buffer'
stats_folder = 'DBDStats//Buffer//Stats//'
logger = logging.getLogger('discord')
manlogger = logging.getLogger('Program')
logger.setLevel(logging.INFO)
manlogger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename = log_folder+'//DBDStats.log',
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
with open('settings.json') as f:
    data = json.load(f)
    steamAPIkey = data['steamAPIkey']
    TOKEN = data['TOKEN']
    ownerID = data['owner_id']
    channel_for_print = data['channel_for_print']
    support_id = data['support_id']
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
translator = Translator()

def get_activity():
    with open('settings.json') as f:
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
    with open('settings.json') as f:
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


class aclient(discord.AutoShardedClient):
    def __init__(self):
        super().__init__(owner_id = ownerID,
                              intents = intents,
                              activity = get_activity(),
                              status = get_status()
                        )
        self.synced = False
    async def on_ready(self):
        if not self.synced:
            await tree.sync(guild = discord.Object(id = 1030227106279477268))
            self.synced = True
        logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        global owner, print_channel
        owner = await bot.fetch_user(ownerID)
        print_channel = await bot.fetch_channel(channel_for_print)
        manlogger.info('Initialization completed...')
        manlogger.info('------')
        print('READY')
bot = aclient()
tree = discord.app_commands.CommandTree(bot)


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
            await channel.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup to get help with the initial setup.')
            return
    await guild.owner.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup to get help with the initial setup.')

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(translate(interaction, 'This comand is on cooldown.\nTime left: `')+seconds_to_minutes(error.retry_after)+'`.', ephemeral = True)
        manlogger.warning(str(error)+' '+interaction.user.name+' | '+str(interaction.user.id))
    else:
        await interaction.response.send_message(error, ephemeral = True)
        manlogger.warning(str(error)+' '+interaction.user.name+' | '+str(interaction.user.id))


#Functions
def CheckForDBD(id, steamAPIkey):
    if len(id) != 17:
        return(1)
    try:
        int(id)
    except:
        return(1)
    try:
        resp = r.get('http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='+steamAPIkey+'&steamid='+id+'&format=json')
        data = resp.json()
        if resp.status_code == 400:
            return(2)
        if data['response'] == {}:
            return(3)
        for event in data['response']['games']:
            if event['appid'] == 381210:
                return(0)
            else:
                continue
        return(4)
    except:
        return(5)

def convert_time(timestamp):
    return(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp)))

def convert_time_dateonly(timestamp):
    return(time.strftime('%Y-%m-%d', time.gmtime(timestamp)))

def convert_number(number):
    return(f'{number:,}')

async def check_429(path):
    resp = r.get(path)
    if resp.status_code == 429:               
        manlogger.warning(str(resp.status_code)+' while accessing '+path)
        await print_channel.send(str(resp.status_code)+' while accessing '+path)
        return(1)
    return(resp.json())

def check_if_removed(id):
    resp = r.get(api_base+'playerstats?steamid='+id)
    if resp.status_code == 404:
        manlogger.warning('SteamID '+id+' got removed from the leaderboard or no stats available yet.')
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


    
##Owner Commands----------------------------------------
#Shutdown
@tree.command(name = 'shutdown', description = 'Savely shut down the bot.', guild = discord.Object(id = 1030227106279477268))
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        manlogger.info('Engine powering down...')
        await interaction.response.send_message(translate(interaction, 'Engine powering down...'), ephemeral = True)
        await bot.close()
    else:
        await interaction.response.send_message(translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
#Get Logs
@tree.command(name = 'get_logs', description = 'Get the current, or all logfiles.', guild = discord.Object(id = 1030227106279477268))
async def self(interaction: discord.Interaction):
    class LogButton(discord.ui.View):
        def __init__(self):
            super().__init__()
        @discord.ui.button(label = translate(interaction, 'Current Log'), style = discord.ButtonStyle.grey)
        async def current(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            try:
                await interaction.response.send_message(file=discord.File(r''+log_folder+'//DBDStats.log'), ephemeral=True)
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(buffer_folder+'//DBDStats.zip', mode='w', compression=ZIP_LZMA, allowZip64=True) as f:
                        f.write(log_folder+'//DBDStats.log')
                    await interaction.response.edit_original_response(embed=discord.Embed(title="Log", description="I'm uploading the compressed log...", color=0x0000ff))
                    try:
                        await interaction.response.send_message(file=discord.File(r''+buffer_folder+'//DBDStats.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await interaction.response.send_message(translate(interaction, "The log is too big to be send directly.\nYou have to look at the log in your server(VPS)."), color=0xff0000)
        @discord.ui.button(label = translate(interaction, 'Whole Folder'), style = discord.ButtonStyle.grey)
        async def whole(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            if os.path.exists(buffer_folder+'//DBDStats.zip'):
                os.remove(buffer_folder+'//DBDStats.zip')
            with ZipFile(buffer_folder+'//DBDStats.zip', mode='w', compression=ZIP_LZMA, allowZip64=True) as f:
                if os.path.exists(log_folder+'//DBDStats.log'):
                    f.write(log_folder+'//DBDStats.log')
                if os.path.exists(log_folder+'//DBDStats.log.1'):
                    f.write(log_folder+'//DBDStats.log.1')
                if os.path.exists(log_folder+'//DBDStats.log.2'):    
                    f.write(log_folder+'//DBDStats.log.2')
                if os.path.exists(log_folder+'//DBDStats.log.3'):    
                    f.write(log_folder+'//DBDStats.log.3')
                if os.path.exists(log_folder+'//DBDStats.log.4'):    
                    f.write(log_folder+'//DBDStats.log.4')
                if os.path.exists(log_folder+'//DBDStats.log.5'):    
                    f.write(log_folder+'//DBDStats.log.5')
            await interaction.response.send_message(file=discord.File(r''+buffer_folder+'//DBDStats.zip'), ephemeral=True)
            os.remove(buffer_folder+'//DBDStats.zip')
    if interaction.user.id != int(ownerID):
        await interaction.response.send_message(translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
        return
    else:
        await interaction.response.send_message(translate(interaction, 'Send only the current Log, or the whole folder?'), view = LogButton(), ephemeral = True)
#Clear Buffer        
@tree.command(name = 'clear_buffer', description = 'Delete all files in buffer that are older than 4h.', guild = discord.Object(id = 1030227106279477268))
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
    await interaction.response.send_message(content=translate(interaction, f'I deleted {i} files.'), ephemeral=True)
#Change Activity
@tree.command(name = 'activity', description = 'Change my activity.', guild = discord.Object(id = 1030227106279477268))
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
        with open('settings.json') as f:
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
        with open('settings.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = get_activity(), status = get_status())
        await interaction.followup.send(translate(interaction, 'Activity changed!'), ephemeral = True)
    else:
        await interaction.followup.send(translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
#Change Status
@tree.command(name = 'status', description = 'Change my status.', guild = discord.Object(id = 1030227106279477268))
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
        with open('settings.json') as f:
            data = json.load(f)
        data['status'] = status
        with open('settings.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = get_activity(), status = get_status())
        await interaction.followup.send(translate(interaction, 'Status changed!'), ephemeral = True)
    else:
        await interaction.followup.send(translate(interaction, 'Only the BotOwner can use this command!'), ephemeral = True)
        
    
##Bot Commands----------------------------------------
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.', guild = discord.Object(id = 1030227106279477268))
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! `{int(ping)}ms`')
#Change Nickname
@tree.command(name = 'change_nickname', description = 'Change the nickname of the bot.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_nicknames = True)
@discord.app_commands.describe(nick='New nickname for me.')
async def self(interaction: discord.Interaction, nick: str):
    await interaction.guild.me.edit(nick=nick)
    await interaction.response.send_message(translate(interaction, f'My new nickname is now **{nick}**.'), ephemeral=True)
#Support Invite
@tree.command(name = 'support', description = 'Get invite to our support server.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
async def self(interaction: discord.Interaction):
    #await interaction.response.send_message(await create_support_invite(interaction))
    await interaction.response.send_message(translate(interaction, 'This command is disabled during testing.'))
#Setup
@tree.command(name = 'setup', description = 'Get help to setup the bot.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id))
@discord.app_commands.describe(option='Please use the \'Help\' option first, because it explains the other options.')
@discord.app_commands.choices(option=[
    discord.app_commands.Choice(name='Help', value='1'),

    ])
async def self(interaction: discord.Interaction, option: str):
    if option == '1':
        language = discord.Embed(title="Setup - Language", description=translate(interaction, "Most outputs will be translated using Google Translator. However the default will be English. Every user can have there own language the bot will use on reply. To use this feature, you must have roles that are named **exactly** like following. Because there are 107 Languages/Roles, you have to setup the roles you need on your own.")+"\n\nAfrikaans, Albanian, Amharic, Arabic, Armenian, Azerbaijani, Basque, Belarusian, Bengali, Bosnian, Bulgarian, Catalan, Cebuano, Chichewa, Chinese (Simplified), Chinese (Traditional), Corsican, Croatian, Czech, Danish, Dutch, Esperanto, Estonian, Filipino, Finnish, French, Frisian, Galician, Georgian, German, Greek, Gujarati, Haitian Creole, Hausa, Hawaiian, Hebrew, Hebrew, Hindi, Hmong, Hungarian, Icelandic, Igbo, Indonesian, Irish, Italian, Japanese, Javanese, Kannada, Kazakh, Khmer, Korean, Kurdish (Kurmanji), Kyrgyz, Lao, Latin, Latvian, Lithuanian, Luxembourgish, Macedonian, Malagasy, Malay, Malayalam, Maltese, Maori, Marathi, Mongolian, Myanmar (Burmese), Nepali, Norwegian, Odia, Pashto, Persian, Polish, Portuguese, Punjabi, Romanian, Russian, Samoan, Scots Gaelic, Serbian, Sesotho, Shona, Sindhi, Sinhala, Slovak, Slovenian, Somali, Spanish, Sundanese, Swahili, Swedish, Tajik, Tamil, Telugu, Thai, Turkish, Ukrainian, Urdu, Uyghur, Uzbek, Vietnamese, Welsh, Xhosa, Yiddish, Yoruba, Zulu", color=0x004cff)
        await interaction.response.send_message(embeds=[language])
    
        

##DBD Commands----------------------------------------
#Stats
@tree.command(name = 'stats', description = 'Get stats for DBD.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
@discord.app_commands.describe(steamid64='SteamID64 of the player you want to get stats for.')
async def self(interaction: discord.Interaction, steamid64: str):
    if interaction.guild is None:
        await interaction.response.send_message('This command can only be used inside a server.')
        return
    check = CheckForDBD(steamid64, steamAPIkey)
    if check == 1:
        await interaction.response.send_message(translate(interaction, f'The SteamID64 has to be 17 chars long and only containing numbers.'), ephemeral=True)   
    elif check == 2:
        await interaction.response.send_message(translate(interaction, f'This SteamID64 is NOT in use.'), ephemeral=True)
    elif check == 3:
        await interaction.response.send_message(translate(interaction, "It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking").replace('.','. ')+"\n[here](https://steamcommunity.com/profiles/"+id+"/edit/settings).", ephemeral=True)
    elif check == 4:
        await interaction.response.send_message(translate(interaction, "I'm sorry, but this profile doesn't own DBD. But if you want to buy it, you can take a look").replace('.','. ')+" [here](https://www.g2a.com/n/dbdstats).")
    elif check == 5:
        embed1=discord.Embed(title="Fatal Error", description=translate(interaction, "It looks like there was an error querying the SteamAPI (probably a rate limit).\nPlease join our").replace('.','. ')+" [Support-Server]("+str(await create_support_invite(interaction))+translate(interaction, ") and create a ticket to tell us about this."), color=0xff0000)
        embed1.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
        await interaction.response.send_message(embed=embed1, ephemeral=True)
    elif check == 0:
        await interaction.response.defer(thinking=True)
        for filename in os.scandir(stats_folder):
            if filename.is_file() and ((time.time() - os.path.getmtime(filename)) / 3600) >= 24:
                os.remove(filename)
        #Get Stats from https://dbd.tricky.lol/
        if check_if_removed(steamid64) == 1:
            embed1 = discord.Embed(title="Statistics", url=alt_playerstats+steamid64, description=translate(interaction, "It looks like this profile has been banned from displaying on our leaderboard.\nThis probably happened because achievements or statistics were manipulated.\nI can therefore not display any information in an embed.\nIf you still want to see the full statistics, please click on the link.\n\nThis message also appears if the stats for this profile hasn't been captured yet. In that case you can try again in a few minutes.").replace('.','. '), color=0xb19325)
            await interaction.followup.send(embed=embed1)
            return
        if os.path.exists(stats_folder+'//player_stats_'+str(steamid64)+'.json') and ((time.time() - os.path.getmtime(buffer_folder+'//player_stats_'+str(steamid64)+'.json')) / 3600) <= 4:
            player_file = open(stats_folder+'//player_stats_'+str(steamid64)+'.json', 'r', encoding='utf8')
            player_stats = json.loads(player_file.read())
        else:
            if await check_429(api_base+'playerstats?steamid='+steamid64) != 1:
                with open(stats_folder+'//player_stats_'+str(steamid64)+'.json', 'w', encoding='utf8') as f:
                    json.dump(r.get(api_base+'playerstats?steamid='+steamid64).json(), f, indent=2)
            else:
                await interaction.followup.send(translate(interaction, "The stats got loaded in the last 3h but I don't have a local copy. Try again in ~3-4h.").replace('.','. '), ephemeral=True)
                return
            player_file = open(stats_folder+'//player_stats_'+str(steamid64)+'.json', 'r', encoding='utf8')
            player_stats = json.loads(player_file.read())
        steam_data = await check_429('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='+steamAPIkey+'&steamids='+steamid64)
        if steam_data == 1 or player_stats == 1:
            await interaction.followup.send(translate(interaction, "The bot got ratelimited. Please try again later. (This error can also appear if the same profile got querried multiple times in a 3h window.)").replace('.','. '), ephemeral=True)
            return
        for event in steam_data['response']['players']:
            personaname = event['personaname']
            profileurl = event['profileurl']
            avatar = event['avatarfull']
        #Set embed headers
        embed1 = discord.Embed(title=translate(interaction, "Statistics (1/10) - Survivor Stats"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed2 = discord.Embed(title=translate(interaction, "Statistics (2/10) - Killer Interactions"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed3 = discord.Embed(title=translate(interaction, "Statistics (3/10) - Healing/Saved"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed4 = discord.Embed(title=translate(interaction, "Statistics (4/10) - Escaped"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed5 = discord.Embed(title=translate(interaction, "Statistics (5/10) - Repaired second floor generator and escaped"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed6 = discord.Embed(title=translate(interaction, "Statistics (6/10) - Killer Stats"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed7 = discord.Embed(title=translate(interaction, "Statistics (7/10) - Hooked"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed8 = discord.Embed(title=translate(interaction, "Statistics (8/10) - Powers"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed9 = discord.Embed(title=translate(interaction, "Statistics (9/10) - Survivors downed"), description=personaname+'\n'+profileurl, color=0xb19325)
        embed10 = discord.Embed(title=translate(interaction, "Statistics (10/10) - Survivors downed with power"), description=personaname+'\n'+profileurl, color=0xb19325)
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
        footer = translate(interaction, "Stats are updated every ~4h. | Last update: ").replace('.|','. | ')+str(convert_time(int(player_stats['updated_at'])))+" UTC"
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
        embed1.add_field(name=translate(interaction, "Bloodpoints Earned"), value=convert_number(player_stats['bloodpoints']), inline=True)
        embed1.add_field(name=translate(interaction, "Rank"), value=player_stats['survivor_rank'], inline=True)
        embed1.add_field(name="\u200b", value="\u200b", inline=False)
        embed1.add_field(name=translate(interaction, "Full loadout Games"), value=convert_number(player_stats['survivor_fullloadout']), inline=True)
        embed1.add_field(name=translate(interaction, "Perfect Games"), value=convert_number(player_stats['survivor_perfectgames']), inline=True)
        embed1.add_field(name=translate(interaction, "Generators repaired"), value=convert_number(player_stats['gensrepaired']), inline=True)
        embed1.add_field(name=translate(interaction, "Gens without Perks"), value=convert_number(player_stats['gensrepaired_noperks']), inline=True)
        embed1.add_field(name=translate(interaction, "Damaged gens repaired"), value=convert_number(player_stats['damagedgensrepaired']), inline=True)
        embed1.add_field(name=translate(interaction, "Successful skill checks"), value=convert_number(player_stats['skillchecks']), inline=True)
        embed1.add_field(name=translate(interaction, "Items Depleted"), value=convert_number(player_stats['itemsdepleted']), inline=False)
        embed1.add_field(name=translate(interaction, "Hex Totems Cleansed"), value=convert_number(player_stats['hextotemscleansed']), inline=True)
        embed1.add_field(name=translate(interaction, "Hex Totems Blessed"), value=convert_number(player_stats['hextotemsblessed']), inline=True)
        embed1.add_field(name=translate(interaction, "Exit Gates Opened"), value=convert_number(player_stats['blessedtotemboosts']), inline=True)
        embed1.add_field(name=translate(interaction, "Hooks Sabotaged"), value=convert_number(player_stats['hookssabotaged']), inline=True)
        embed1.add_field(name=translate(interaction, "Chests Searched"), value=convert_number(player_stats['chestssearched']), inline=True)
        embed1.add_field(name=translate(interaction, "Chests Searched in the Basement"), value=convert_number(player_stats['chestssearched_basement']), inline=True)
        embed1.add_field(name=translate(interaction, "Mystery boxes opened"), value=convert_number(player_stats['mysteryboxesopened']), inline=True)
        #Embed2 - Killer Interactions
        embed2.add_field(name="\u200b", value="\u200b", inline=False)
        embed2.add_field(name=translate(interaction, "Dodged basic attack or projectiles"), value=convert_number(player_stats['dodgedattack']), inline=True)
        embed2.add_field(name=translate(interaction, "Escaped chase after pallet stun"), value=convert_number(player_stats['escapedchase_palletstun']), inline=True)
        embed2.add_field(name=translate(interaction, "Escaped chase injured after hit"), value=convert_number(player_stats['escapedchase_healthyinjured']), inline=True)
        embed2.add_field(name=translate(interaction, "Escape chase by hiding in locker"), value=convert_number(player_stats['escapedchase_hidinginlocker']), inline=True)
        embed2.add_field(name=translate(interaction, "Protection hits for unhooked survivor"), value=convert_number(player_stats['protectionhits_unhooked']), inline=True)
        embed2.add_field(name=translate(interaction, "Protectionhits while a survivor is carried"), value=convert_number(player_stats['protectionhits_whilecarried']), inline=True)
        embed2.add_field(name=translate(interaction, "Vaults while in chase"), value=convert_number(player_stats['vaultsinchase']), inline=True)
        embed2.add_field(name=translate(interaction, "Dodge attack before vaulting"), value=convert_number(player_stats['vaultsinchase_missed']), inline=True)
        embed2.add_field(name=translate(interaction, "Wiggled from killers grasp"), value=convert_number(player_stats['wiggledfromkillersgrasp']), inline=True)
        #Embed3 - Healing/Saves
        embed3.add_field(name="\u200b", value="\u200b", inline=False)
        embed3.add_field(name=translate(interaction, "Survivors healed"), value=convert_number(player_stats['survivorshealed']), inline=True)
        embed3.add_field(name=translate(interaction, "Survivors healed while injured"), value=convert_number(player_stats['survivorshealed_whileinjured']), inline=True)
        embed3.add_field(name=translate(interaction, "Survivors healed while 3 others not healthy"), value=convert_number(player_stats['survivorshealed_threenothealthy']), inline=True)
        embed3.add_field(name=translate(interaction, "Survivors healed who found you while injured"), value=convert_number(player_stats['survivorshealed_foundyou']), inline=True)
        embed3.add_field(name=translate(interaction, "Survivors healed from dying state to injured"), value=convert_number(player_stats['healeddyingtoinjured']), inline=True)
        embed3.add_field(name=translate(interaction, "Obsessions healed"), value=convert_number(player_stats['obsessionshealed']), inline=True)
        embed3.add_field(name=translate(interaction, "Survivors saved (from death)"), value=convert_number(player_stats['saved']), inline=True)
        embed3.add_field(name=translate(interaction, "Survivors saved during endgame"), value=convert_number(player_stats['saved_endgame']), inline=True)
        embed3.add_field(name=translate(interaction, "Killers pallet stunned while carrying a survivor"), value=convert_number(player_stats['killerstunnedpalletcarrying']), inline=True)
        embed3.add_field(name="Kobed", value=convert_number(player_stats['unhookedself']), inline=True)
        #Embed5 - Escaped
        embed4.add_field(name="\u200b", value="\u200b", inline=False)
        embed4.add_field(name=translate(interaction, "While healthy/injured"), value=convert_number(player_stats['escaped']), inline=True)
        embed4.add_field(name=translate(interaction, "While crawling"), value=convert_number(player_stats['escaped_ko']), inline=True)
        embed4.add_field(name=translate(interaction, "After kobed"), value=convert_number(player_stats['hooked_escape']), inline=True)
        embed4.add_field(name=translate(interaction, "Through the hatch"), value=convert_number(player_stats['escaped_hatch']), inline=True)
        embed4.add_field(name=translate(interaction, "Through the hatch while crawling"), value=convert_number(player_stats['escaped_hatchcrawling']), inline=True)
        embed4.add_field(name=translate(interaction, "Through the hatch with everyone"), value=convert_number(player_stats['escaped_allhatch']), inline=True)
        embed4.add_field(name=translate(interaction, "After been downed once"), value=convert_number(player_stats['escaped_downedonce']), inline=True)
        embed4.add_field(name=translate(interaction, "After been injured for half of the trial"), value=convert_number(player_stats['escaped_injuredhalfoftrail']), inline=True)
        embed4.add_field(name=translate(interaction, "With no bloodloss as obsession"), value=convert_number(player_stats['escaped_nobloodlossobsession']), inline=True)
        embed4.add_field(name=translate(interaction, "Last gen last survivor"), value=convert_number(player_stats['escaped_lastgenlastsurvivor']), inline=True)
        embed4.add_field(name=translate(interaction, "With new item"), value=convert_number(player_stats['escaped_newitem']), inline=True)
        embed4.add_field(name=translate(interaction, "With item from someone else"), value=convert_number(player_stats['escaped_withitemfrom']), inline=True)
        #Embed6 - Repaired second floor generator and escaped
        embed5.add_field(name="\u200b", value="\u200b", inline=False)
        embed5.add_field(name="Disturbed Ward", value=convert_number(player_stats['secondfloorgen_disturbedward']), inline=True)
        embed5.add_field(name="Father Campbells Chapel", value=convert_number(player_stats['secondfloorgen_fathercampbellschapel']), inline=True)
        embed5.add_field(name="Mothers Dwelling", value=convert_number(player_stats['secondfloorgen_mothersdwelling']), inline=True)
        embed5.add_field(name="Temple of Purgation", value=convert_number(player_stats['secondfloorgen_templeofpurgation']), inline=True)
        embed5.add_field(name="The Game", value=convert_number(player_stats['secondfloorgen_game']), inline=True)
        embed5.add_field(name="Family Residence", value=convert_number(player_stats['secondfloorgen_familyresidence']), inline=True)
        embed5.add_field(name="Sanctum of Wrath", value=convert_number(player_stats['secondfloorgen_sanctumofwrath']), inline=True)
        embed5.add_field(name="Mount Ormond", value=convert_number(player_stats['secondfloorgen_mountormondresort']), inline=True)
        embed5.add_field(name="Lampkin Lane", value=convert_number(player_stats['secondfloorgen_lampkinlane']), inline=True)
        embed5.add_field(name="Pale Rose", value=convert_number(player_stats['secondfloorgen_palerose']), inline=True)
        embed5.add_field(name="Hawkins", value=convert_number(player_stats['secondfloorgen_undergroundcomplex']), inline=True)
        embed5.add_field(name="Treatment Theatre", value=convert_number(player_stats['secondfloorgen_treatmenttheatre']), inline=True)
        embed5.add_field(name="Dead Dawg Saloon", value=convert_number(player_stats['secondfloorgen_deaddawgsaloon']), inline=True)
        embed5.add_field(name="Midwich", value=convert_number(player_stats['secondfloorgen_midwichelementaryschool']), inline=True)
        embed5.add_field(name="Raccoon City", value=convert_number(player_stats['secondfloorgen_racconcitypolicestation']), inline=True)
        embed5.add_field(name="Eyrie of Crows", value=convert_number(player_stats['secondfloorgen_eyrieofcrows']), inline=True)
        embed5.add_field(name="Garden of Joy", value=convert_number(player_stats['secondfloorgen_gardenofjoy']), inline=True)
        embed5.add_field(name="\u200b", value="\u200b", inline=True)
        #Embed7 - Killer Stats
        embed6.add_field(name=translate(interaction, "Rank"), value=player_stats['killer_rank'], inline=True)
        embed6.add_field(name="\u200b", value="\u200b", inline=False)
        embed6.add_field(name=translate(interaction, "Played with full loadout"), value=convert_number(player_stats['killer_fullloadout']), inline=True)
        embed6.add_field(name=translate(interaction, "Perfect Games"), value=convert_number(player_stats['killer_perfectgames']), inline=True)
        embed6.add_field(name=translate(interaction, "Survivors Killed"), value=convert_number(player_stats['killed']), inline=True)
        embed6.add_field(name=translate(interaction, "Survivors Sacrificed"), value=convert_number(player_stats['sacrificed']), inline=True)
        embed6.add_field(name=translate(interaction, "Sacrificed all before last gen"), value=convert_number(player_stats['sacrificed_allbeforelastgen']), inline=True)
        embed6.add_field(name=translate(interaction, "Killed/Sacrificed after last gen"), value=convert_number(player_stats['killed_sacrificed_afterlastgen']), inline=True)
        embed6.add_field(name=translate(interaction, "Killed all 4 with tier 3 Myers"), value=convert_number(player_stats['killed_allevilwithin']), inline=True)
        embed6.add_field(name=translate(interaction, "Obsessions Sacrificed"), value=convert_number(player_stats['sacrificed_obsessions']), inline=True)
        embed6.add_field(name=translate(interaction, "Hatches Closed"), value=convert_number(player_stats['hatchesclosed']), inline=True)
        embed6.add_field(name=translate(interaction, "Gens damaged while 1-4 survivors are hooked"), value=convert_number(player_stats['gensdamagedwhileonehooked']), inline=True)
        embed6.add_field(name=translate(interaction, "Gens damaged while undetectable"), value=convert_number(player_stats['gensdamagedwhileundetectable']), inline=True)
        embed6.add_field(name=translate(interaction, "Grabbed while repairing a gen"), value=convert_number(player_stats['survivorsgrabbedrepairinggen']), inline=True)
        embed6.add_field(name=translate(interaction, "Grabbed while you are hiding in locker"), value=convert_number(player_stats['survivorsgrabbedfrominsidealocker']), inline=True)
        embed6.add_field(name=translate(interaction, "Hit one who dropped a pallet in chase"), value=convert_number(player_stats['survivorshitdroppingpalletinchase']), inline=True)
        embed6.add_field(name=translate(interaction, "Hit while carrying"), value=convert_number(player_stats['survivorshitwhilecarrying']), inline=True)
        embed6.add_field(name=translate(interaction, "Interrupted cleansing"), value=convert_number(player_stats['survivorsinterruptedcleansingtotem']), inline=True)
        embed6.add_field(name="\u200b", value="\u200b", inline=True)
        embed6.add_field(name=translate(interaction, "Vaults while in chase"), value=convert_number(player_stats['vaultsinchase_askiller']), inline=True)
        #Embed8 - Hooked
        embed7.add_field(name="\u200b", value="\u200b", inline=False)
        embed7.add_field(name=translate(interaction, "Suvivors hooked before a generator is repaired"), value=convert_number(player_stats['survivorshookedbeforegenrepaired']), inline=True)
        embed7.add_field(name=translate(interaction, "Survivors hooked during end game collapse"), value=convert_number(player_stats['survivorshookedendgamecollapse']), inline=True)
        embed7.add_field(name=translate(interaction, "Hooked a survivor while 3 other survivors were injured"), value=convert_number(player_stats['hookedwhilethreeinjured']), inline=True)
        embed7.add_field(name=translate(interaction, "3 Survivors hooked in basement"), value=convert_number(player_stats['survivorsthreehookedbasementsametime']), inline=True)
        embed7.add_field(name="\u200b", value="\u200b", inline=True)
        embed7.add_field(name=translate(interaction, "Survivors hooked in basement"), value=convert_number(player_stats['survivorshookedinbasement']), inline=True)
        #Embed9 - Powers
        embed8.add_field(name="\u200b", value="\u200b", inline=False)
        embed8.add_field(name=translate(interaction, "Beartrap Catches"), value=convert_number(player_stats['beartrapcatches']), inline=True)
        embed8.add_field(name=translate(interaction, "Uncloak Attacks"), value=convert_number(player_stats['uncloakattacks']), inline=True)
        embed8.add_field(name=translate(interaction, "Chainsaw Hits  (Billy)"), value=convert_number(player_stats['chainsawhits']), inline=True)
        embed8.add_field(name=translate(interaction, "Blink Attacks"), value=convert_number(player_stats['blinkattacks']), inline=True)
        embed8.add_field(name=translate(interaction, "Phantasms Triggered"), value=convert_number(player_stats['phantasmstriggered']), inline=True)
        embed8.add_field(name=translate(interaction, "Hit each survivor after teleporting to phantasm trap"), value=convert_number(player_stats['survivorshiteachafterteleporting']), inline=True)
        embed8.add_field(name=translate(interaction, "Evil Within Tier Ups"), value=convert_number(player_stats['evilwithintierup']), inline=True)
        embed8.add_field(name=translate(interaction, "Shock Therapy Hits"), value=convert_number(player_stats['shocked']), inline=True)
        embed8.add_field(name=translate(interaction, "Trials with all survivors in madness tier 3"), value=convert_number(player_stats['survivorsallmaxmadness']), inline=True)
        embed8.add_field(name=translate(interaction, "Hatchets Thrown"), value=convert_number(player_stats['hatchetsthrown']), inline=True)
        embed8.add_field(name=translate(interaction, "Pulled into Dream State"), value=convert_number(player_stats['dreamstate']), inline=True)
        embed8.add_field(name=translate(interaction, "Reverse Bear Traps Placed"), value=convert_number(player_stats['rbtsplaced']), inline=True)
        embed8.add_field(name=translate(interaction, "Cages of Atonement"), value=convert_number(player_stats['cagesofatonement']), inline=True)
        embed8.add_field(name=translate(interaction, "Lethal Rush Hits"), value=convert_number(player_stats['lethalrushhits']), inline=True)
        embed8.add_field(name=translate(interaction, "Lacerations"), value=convert_number(player_stats['lacerations']), inline=True)
        embed8.add_field(name=translate(interaction, "Possessed Chains"), value=convert_number(player_stats['possessedchains']), inline=True)
        embed8.add_field(name=translate(interaction, "Condemned"), value=convert_number(player_stats['condemned']), inline=True)
        embed8.add_field(name=translate(interaction, "Slammed"), value=convert_number(player_stats['slammedsurvivors']), inline=True)
        #Embed10 - Survivors downed
        embed9.add_field(name="\u200b", value="\u200b", inline=False)
        embed9.add_field(name=translate(interaction, "Downed while suffering from oblivious"), value=convert_number(player_stats['survivorsdowned_oblivious']), inline=True)
        embed9.add_field(name=translate(interaction, "Downed while Exposed"), value=convert_number(player_stats['survivorsdowned_exposed']), inline=True)
        embed9.add_field(name=translate(interaction, "Downed while carrying a survivor"), value=convert_number(player_stats['survivorsdownedwhilecarrying']), inline=True)
        embed9.add_field(name=translate(interaction, "Downed near a raised pallet"), value=convert_number(player_stats['survivorsdownednearraisedpallet']), inline=True)
        #Embed11 - Survivors downed with power
        embed10.add_field(name="\u200b", value="\u200b", inline=False)
        embed10.add_field(name=translate(interaction, "Downed with a Hatchet (24+ meters)"), value=convert_number(player_stats['survivorsdowned_hatchets']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed with a Chainsaw (Bubba)"), value=convert_number(player_stats['survivorsdowned_chainsaw']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while Intoxicated"), value=convert_number(player_stats['survivorsdowned_intoxicated']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed after Haunting"), value=convert_number(player_stats['survivorsdowned_haunting']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while in Deep Wound"), value=convert_number(player_stats['survivorsdowned_deepwound']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while having max sickness"), value=convert_number(player_stats['survivorsdowned_maxsickness']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while marked (Ghostface)"), value=convert_number(player_stats['survivorsdowned_marked']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while using Shred"), value=convert_number(player_stats['survivorsdowned_shred']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while using Blood Fury"), value=convert_number(player_stats['survivorsdowned_bloodfury']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while Speared"), value=convert_number(player_stats['survivorsdowned_speared']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while Victor is clinging to them"), value=convert_number(player_stats['survivorsdowned_victor']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while contaminated"), value=convert_number(player_stats['survivorsdowned_contaminated']), inline=True)
        embed10.add_field(name=translate(interaction, "Downed while using Dire Crows"), value=convert_number(player_stats['survivorsdowned_direcrows']), inline=True)
        embed10.add_field(name="\u200b", value="\u200b", inline=True)
        embed10.add_field(name=translate(interaction, "Downed during nightfall"), value=convert_number(player_stats['survivorsdowned_nightfall']), inline=True)
        #Send Statistics
        player_file.close()
        await interaction.edit_original_response(embeds=[embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed8, embed9, embed10])
#Buy
@tree.command(name = "buy", description = 'This will post a link to a site where you can buy DeadByDaylight for a few bucks.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))        
async def self(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(translate(interaction, "This command can only be used in a server."))
    else:
        embed = discord.Embed(title="Buy Dead By Daylight", description=translate(interaction, "Click the title, to buy the game for a few bucks."), url="https://www.g2a.com/n/dbdstats", color=0x00ff00)
        await interaction.response.send_message(embed=embed)
#Rankreset
@tree.command(name = "rankreset", description = 'This will show how long it takes until the next rankreset.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
async def self(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(translate(interaction, "This command can only be used in a server."))
    else:
        resp = r.get(api_base+'rankreset')
        data = resp.json()
        embed = discord.Embed(description=translate(interaction, 'The next rank reset will take place on the following date: ')+' <t:'+str(data['rankreset'])+'>.', color=0x0400ff)
        await interaction.response.send_message(embed=embed)
#Get current Event
@tree.command(name = 'event', description='Get status of a currently or upcomming events.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
async def self(interaction: discord.Interaction):
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
                embed = discord.Embed(title="Event", description=translate(interaction, "Currently there is a event in DeadByDaylight.")+" <a:hyperWOW:1032389458319913023>", color=0x922f2f)
                embed.add_field(name=translate(interaction, "Name"), value=event['name'], inline=True)
                embed.add_field(name=translate(interaction, "Bloodpoint Multiplier"), value=event['multiplier'], inline=False)
                embed.add_field(name=translate(interaction, "Beginning"), value=str(convert_time(event['start'])+' UTC'), inline=True)
                embed.add_field(name=translate(interaction, "Ending"), value=str(convert_time(event['end'])+' UTC'), inline=True)
                await interaction.followup.send(embed=embed)
                return
            elif int(event['start']) <= int(time.time()) <= int(event['end']):
                embed = discord.Embed(title="Event", description=translate(interaction, "There is a upcomming event in DeadByDaylight.")+" <a:SmugDance:1032349729167790090>", color=0x922f2f)
                embed.add_field(name="Name", value=event['name'], inline=True)
                embed.add_field(name="Bloodpoint Multiplier", value=event['multiplier'], inline=False)
                embed.add_field(name="Beginning", value=str(convert_time(event['start'])+' UTC'), inline=True)
                embed.add_field(name="Ending", value=str(convert_time(event['end'])+' UTC'), inline=True)
                await interaction.followup.send(embed=embed)
                return
        embed = discord.Embed(title="Event", description=translate(interaction, "Currently there is no event in DeadByDaylight.")+" <:pepe_sad:1032389746284056646>", color=0x922f2f)
        await interaction.followup.send(embed=embed)
#Get DB Versions
@tree.command(name = 'version', description='Get versions of the databases this bot uses.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
async def self(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    if interaction.guild is None:
        await interaction.response.send_message("This command can only be used in a server.")
    else:
        data = await check_429(api_base+'versions')
        if data == 1:
            await interaction.followup.send(translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '), ephemeral=True)
            return
        embed = discord.Embed(title='DB Version (1/2)', color=0x42a32e)
        embed.add_field(name=translate(interaction, 'Name'), value='\u200b', inline=True)
        embed.add_field(name=translate(interaction, 'Version'), value='\u200b', inline=True)
        embed.add_field(name=translate(interaction, 'Last Update'), value='\u200b', inline=True)
        embed2 = discord.Embed(title='DB Version (2/2)', color=0x42a32e)
        embed2.add_field(name=translate(interaction, 'Name'), value='\u200b', inline=True)
        embed2.add_field(name=translate(interaction, 'Version'), value='\u200b', inline=True)
        embed2.add_field(name=translate(interaction, 'Last Update'), value='\u200b', inline=True)
        resp = r.get(api_base+'versions')
        data = resp.json()
        i = 0
        for key in data.keys():
            i += 1
            if i <= 5:
                embed.add_field(name='\u200b', value=key.capitalize(), inline=True)
                embed.add_field(name='\u200b', value=data[key]['version'], inline=True)
                embed.add_field(name='\u200b', value=str(convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
            if i >= 6:
                embed2.add_field(name='\u200b', value=key.capitalize(), inline=True)
                embed2.add_field(name='\u200b', value=data[key]['version'], inline=True)
                embed2.add_field(name='\u200b', value=str(convert_time(data[key]['lastupdate'])+' UTC'), inline=True)
        await interaction.followup.send(embeds=[embed, embed2])
#Character Info
@tree.command(name = 'character', description='Get information about a character.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
@discord.app_commands.describe(character='Enter the exact name, or ID of the char. Leave empty, to get a list of all chars.')
async def self(interaction: discord.Interaction, character: str=''):
    await interaction.response.defer(thinking = True)
    if interaction.guild is None:
        await interaction.followup.send("This command can only be used in a server.")
    if os.path.exists(buffer_folder+'//character_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'//character_info.json')) / 3600) <= 4:
        character_info = open(buffer_folder+'//character_info.json', 'r', encoding='utf8')
    else:
        data = await check_429(api_base+'characters?includeperks=1')
        if data == 1:
            await interaction.followup.send(translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
            return
        with open(buffer_folder+'//character_info.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        character_info = open(buffer_folder+'//character_info.json', 'r', encoding='utf8')   
    if os.path.exists(buffer_folder+'//dlc.json') and ((time.time() - os.path.getmtime(buffer_folder+'//dlc.json')) / 3600) <= 4:
        dlc_info = open(buffer_folder+'//dlc.json', 'r', encoding='utf8')
    else:
        data = await check_429(api_base+'dlc')
        if data == 1:
            await interaction.followup.send(translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
            return
        with open(buffer_folder+'//dlc.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        dlc_info = open(buffer_folder+'//dlc.json', 'r', encoding='utf8')
    data = json.loads(character_info.read())
    dlc_data = json.loads(dlc_info.read())
    if character == '' and os.path.exists(buffer_folder+'//characters_survivor.txt') and os.path.exists(buffer_folder+'//characters_killer.txt') and ((time.time() - os.path.getmtime(buffer_folder+'//characters_survivor.txt')) / 3600) <= 4:
        await interaction.followup.send(files=[discord.File(buffer_folder+'//characters_survivor.txt'), discord.File(buffer_folder+'//characters_killer.txt')])
    elif character == '':
        survivor = open(buffer_folder+'//characters_survivor.txt', 'w', encoding='utf8')
        killer = open(buffer_folder+'//characters_killer.txt', 'w', encoding='utf8')
        for key in data.keys():
            if data[key]['role'] == 'survivor':
                survivor.write('ID: '+data[key]['id']+' \u0009 Name: '+data[key]['name']+'\n')
            elif data[key]['role'] == 'killer':
                killer.write('ID: '+data[key]['id']+' \u0009 Name: '+data[key]['name']+'\n')
            else:
                manlogger.info('Unknown role: '+data[key]['role'])
                await interaction.followup.send("Unknown role: "+data[key]['role'])
        survivor.close()
        killer.close()
        await interaction.followup.send(content=translate(interaction, "Here are the characters:"), files=[discord.File(buffer_folder+'//characters_survivor.txt'), discord.File(buffer_folder+'//characters_killer.txt')])
    else:
        for key in data.keys():
            if str(data[key]['id']).lower() == character.lower().replace('the ', '') or str(data[key]['name']).lower().replace('the ', '') == character.lower():
                embed = discord.Embed(title=translate(interaction, "Character Info"), description=str(data[key]['name']), color=0xb19325)
                embed.set_thumbnail(url=char_portraits+str(data[key]['id'])+'.png')
                embed.add_field(name=translate(interaction, "Role"), value=str(data[key]['role']).capitalize(), inline=True)
                embed.add_field(name=translate(interaction, "Gender"), value=str(data[key]['gender']).capitalize(), inline=True)
                for dlc_key in dlc_data.keys():
                    if dlc_key == data[key]['dlc']:
                        embed.add_field(name="DLC", value='['+str(dlc_data[dlc_key]['name']).capitalize().replace(' chapter', '')+']('+steamStore+str(dlc_data[dlc_key]['steamid'])+')', inline=True)
                if data[key]['difficulty'] != 'none':
                    embed.add_field(name=translate(interaction, "Difficulty"), value=str(data[key]['difficulty']).capitalize(), inline=True)
                if str(data[key]['role']) == 'killer':
                    embed.add_field(name=translate(interaction, "Walkspeed"), value=str(int(data[key]['tunables']['maxwalkspeed']) / 100)+'m/s', inline=True)
                    embed.add_field(name=translate(interaction, "Terror Radius"), value=str(int(data[key]['tunables']['terrorradius']) / 100)+'m', inline=True)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                embed.add_field(name="Bio", value=translate(interaction, str(data[key]['bio']).replace('<br><br>', '').replace('<b>', '**').replace('</b>', '**').replace('&nbsp;', ' ').replace('.', '. ')), inline=False)
                if len(data[key]['story']) > 4096:
                    story = buffer_folder+'//character_story.txt'
                    if os.path.exists(story):
                        story = buffer_folder+'//character_story'+str(randrange(1, 999))+'.txt'
                    with open(story, 'w', encoding='utf8') as f:
                        f.write(translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('. ', '.\n').replace('\n ', '\n').replace('&nbsp;', ' ').replace('S.\nT.\nA.\nR.\nS.\n', 'S.T.A.R.S.')).replace('.', '. '))
                    await interaction.followup.send('Story', file=discord.File(r''+story))
                    os.remove(story)
                elif 1024 < len(data[key]['story']) < 4096:
                    embed2 = discord.Embed(title='Story', description=translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('&nbsp;', ' ')).replace('.', '. '), color=0xb19325)
                    character_info.close()
                    dlc_info.close()
                    await interaction.followup.send(embeds=[embed, embed2])
                    return
                else:
                    embed.add_field(name="Story", value=translate(interaction, str(data[key]['story']).replace('<br><br>', '').replace('&nbsp;', ' ')).replace('.', '. '), inline=False)
                character_info.close()
                dlc_info.close()
                await interaction.followup.send(embed=embed)
                return
        embed = discord.Embed(title=translate(interaction, "Character Info"), description=translate(interaction, f"I couldn't find a character named {character}."), color=0xb19325)
        await interaction.followup.send(embed=embed)
        character_info.close()
        dlc_info.close()
#Get DLCs
@tree.command(name='dlc', description='Get information about the DLCs.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
@discord.app_commands.describe(name='Enter the exact name of the DLC to get the description. Leave empty to get a list of all DLCs.')
async def self(interaction: discord.Interaction, name: str=''):
    await interaction.response.defer(thinking=True)
    if os.path.exists(buffer_folder+'//dlc.json') and ((time.time() - os.path.getmtime(buffer_folder+'//dlc.json')) / 3600) <= 4:
        dlc_info = open(buffer_folder+'//dlc.json', 'r', encoding='utf8')
    else:
        data = await check_429(api_base+'dlc')
        if data == 1:
            await interaction.followup.send(translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '), ephemeral=True)
            return
        with open(buffer_folder+'//dlc.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
            dlc_info = open(buffer_folder+'//dlc.json', 'r', encoding='utf8')
    data = json.loads(dlc_info.read())
    if name == '':
        embed = discord.Embed(title="DLC Info (1/2)",  description=translate(interaction, "Here is a list of all DLCs. Click the link to go to the steam storepage.").replace('.','. '), color=0xb19325)
        embed2 = discord.Embed(title="DLC Info (2/2)", description=translate(interaction, "Here is a list of all DLCs. Click the link to go to the steam storepage.").replace('.','. '), color=0xb19325)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed2.add_field(name='\u200b', value='\u200b', inline=False)
        i = 0
        for key in data.keys():
            if data[key]['steamid'] == 0:
                continue
            if i <= 25:
                embed.add_field(name=str(data[key]['name']), value='['+convert_time_dateonly(data[key]['time'])+']('+steamStore+str(data[key]['steamid'])+')')
                i += 1
            if i > 25:
                embed2.add_field(name=str(data[key]['name']), value='['+convert_time_dateonly(data[key]['time'])+']('+steamStore+str(data[key]['steamid'])+')')
        await interaction.followup.send(embeds=[embed, embed2])
        dlc_info.close()
    else:
        for key in data.keys():
            if data[key]['name'].lower() == name.lower():
                embed = discord.Embed(title="DLC description for '"+data[key]['name']+"'", description=translate(interaction, str(data[key]['description']).replace('<br><br>', ' ')), color=0xb19325)
                dlc_info.close()
                await interaction.followup.send(embed=embed)
#Maps
@tree.command(name='map', description='Get information about the maps.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
@discord.app_commands.describe(name='Enter the exact name of the map to get the description. Leave empty to get a list of all maps.')
async def self(interaction: discord.Interaction, name: str=''):
    await interaction.response.defer(thinking=True)
    if interaction.guild is None:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return
    if os.path.exists(buffer_folder+'//maps_info.json') and ((time.time() - os.path.getmtime(buffer_folder+'//maps_info.json')) / 3600) >= 4 or not os.path.exists(buffer_folder+'//maps_info.json'):
        data = await check_429(api_base+'maps')
        if data == 1:
            await interaction.followup.send(translate(interaction, "The bot got ratelimited. Please try again later.").replace('.','. '))
        with open(buffer_folder+'//maps_info.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
    if name == '' and os.path.exists(buffer_folder+'//maps.txt') and ((time.time() - os.path.getmtime(buffer_folder+'//maps.txt')) / 3600) <= 4:
            await interaction.followup.send(file=discord.File(r''+buffer_folder+'//maps.txt'))
            return
    elif name == '':
        map_info = open(buffer_folder+'//maps_info.json', 'r', encoding='utf8')
        map_data = json.loads(map_info.read())
        with open(buffer_folder+'//maps.txt', 'w', encoding='utf8') as f:
            for key in map_data.keys():
                if key == 'Swp_Mound':
                    continue
                f.write('Name: '+map_data[key]['name']+'\n')
        await interaction.followup.send(file=discord.File(r''+buffer_folder+'//maps.txt'))
    else:
        map_info = open(buffer_folder+'//maps_info.json', 'r', encoding='utf8')
        map_data = json.loads(map_info.read())
        for key in map_data.keys():
            if map_data[key]['name'] == 'Swp_Mound':
                continue
            if map_data[key]['name'].lower() == name.lower():
                embed = discord.Embed(title="Map description for '"+map_data[key]['name']+"'", description=translate(interaction, str(map_data[key]['description']).replace('<br><br>', ' ')).replace('.','. '), color=0xb19325)
                embed.set_thumbnail(url=map_portraits+key+'.png')
                await interaction.followup.send(embed=embed)
                return
        await interaction.followup.send(f"No map with name **{name}** found.")
#Playercount
@tree.command(name='playercount', description='Get the current playercount.', guild = discord.Object(id = 1030227106279477268))
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    async def selfembed(data):
        embed = discord.Embed(title=translate(interaction, "Playercount"), color=0xb19325)
        embed.set_thumbnail(url="https://cdn.bloodygang.com/botfiles/dbd.png")
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name=translate(interaction, "Current"), value=convert_number(int(data['Current Players'])), inline=True)
        embed.add_field(name=translate(interaction, "24h Peak"), value=convert_number(int(data['Peak Players 24h'])), inline=True)
        embed.add_field(name=translate(interaction, "All-time Peak"), value=convert_number(int(data['Peak Players All Time'])), inline=True)
        embed.set_footer(text=translate(interaction, "This will be updated every full hour."))
        await interaction.followup.send(embed = embed)
    async def selfget():
        url = 'https://steamcharts.com/app/381210'
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26'}
        page = r.get(url, headers = header)
        if page.status_code != 200:
            await interaction.followup.send(translate(interaction, "Error while fetching the playercount.").replace('.','. '))
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
        with open(buffer_folder+'//playercount.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        return data
    await interaction.response.defer(thinking = True)
    if os.path.exists(buffer_folder+'//playercount.json'):
        with open(buffer_folder+'//playercount.json', 'r', encoding='utf8') as f:
            data = json.load(f)
        if data['update_hour'] == datetime.now().hour:
            await selfembed(data)
            return
    await selfembed(await selfget())


    
        


    
        

        

    
    


    






















bot.run(TOKEN, log_handler=None)
