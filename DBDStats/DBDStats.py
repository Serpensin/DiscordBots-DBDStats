#Import
from distutils.sysconfig import PREFIX
import discord
from discord.ext import commands
import requests as r
import time
from pretty_help import PrettyHelp, DefaultMenu
import logging
import logging.handlers
import os
import mysql.connector as sql
import Tables
from zipfile import ZIP_LZMA, ZipFile
from sys import exit





#Set vars
steamAPIkey = '71F4FABB9E88701D00565E39870CD51E' #https://steamcommunity.com/dev/apikey
#myID64 = '76561198889439823'
TOKEN = 'MTAzMDE2MzEyNzkyNjU0MjQwMA.GMhudd.FmTF0CUHnlkUWJtxt3S9WhJIas-Pkm5oIoshsg'
activity = discord.Game(name='DBD Stats for Steam', url='https://www.twitch.tv/deadbydaylight')
ownerID = '863687441809801246'
default_prefix = '<'
channel_for_print = '1031306769093382154'
support = 'https://discord.gg/Rwz9CvR35t'
tricky_base = 'https://dbd.tricky.lol/api/'
tricky_base_perks = 'https://dbd.tricky.lol/dbdassets/perks/'
db_host = 'localhost'
db_database = 'discord_dbdstats'
db_user = 'DBDStats'
db_password = 'NXJkJF@rZyr9^ypCDJD5cZaG%S&K^Hu$bVjU75XgFgYpbvu*stMUWFAirh%B#EqsBqe2iDes'

















#Init
print('------')
print('Initialization...')
if not os.path.exists('Logs'):
    os.mkdir('Logs')
    log_folder = 'Logs'
else:
    if not os.access('Logs', os.R_OK | os.W_OK | os.X_OK):
        if not os.path.exists('DBDStats - Logs'):
            os.mkdir('DBDStats - Logs')
            log_folder = 'DBDStats - Logs'
        else:
            log_folder = 'DBDStats - Logs'
    else:
        log_folder = 'Logs'
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename = log_folder+'\\DBDStats.log',
    encoding = 'utf-8',
    maxBytes = 8 * 1024 * 1024, 
    backupCount = 5,            
    mode='w')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
menu = DefaultMenu(delete_after_timeout=True)
#Connect to DB
try:
    connection = sql.connect(host = db_host,
                             database = db_database,
                             user = db_user,
                             password = db_password)
    if connection.is_connected():
        cursor = connection.cursor(buffered=True)
        try:
            for table_name in Tables.TABLES:
                table_description = Tables.TABLES[table_name]
                try:
                    cursor.execute(table_description)
                except sql.Error as err:
                    if err.errno != 1050:
                        print(err)
        except sql.Error as err:
            print(err)
except sql.Error as err:
    print(err)
    exit()

def get_prefix(bot, message):
    cursor = connection.cursor(buffered=True)
    query = "SELECT guild_id, prefix FROM guild"
    cursor.execute(query)
    for (guild_id, prefix) in cursor:
        if str(message.guild.id) == guild_id:
            return prefix
    return '<@1030163127926542400>'

bot = commands.AutoShardedBot(command_prefix = (get_prefix),
                              strip_after_prefix = True,
                              owner_id = ownerID,
                              intents = intents,
                              activity = activity,
                              help_command = PrettyHelp(menu = menu,
                                                      sort_commands = True,
                                                      show_index = False
                                                      )
                              )










#Events
@bot.event
async def on_ready():
    print('------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    global owner, print_channel
    owner = await bot.fetch_user(ownerID)
    print_channel = await bot.fetch_channel(channel_for_print)
    await bot.add_cog(Bot(bot))
    await bot.add_cog(DBD(bot))
    await bot.add_cog(zBotOwner(bot))
    print('Initialization completed...')
    print('------')

    
    
    

@bot.event
async def on_guild_remove(guild):
    print(f'I got kicked from {guild}. (ID: {guild.id})')



@bot.event
async def on_guild_join(guild):
    await owner.send('Dam')
    print(f'I joined {guild}. (ID: {guild.id})')
    






#Functions

#Check if player has DBD
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








#Owner Commands
class zBotOwner(commands.Cog):
    @commands.command(brief='Shutdown', help='This will shutdown the bot.')
    async def shutdown(self, ctx: commands.Context):
        if ctx.author.id == int(ownerID):
            await bot.close()


    @commands.command(brief='Get prefix of guild', help='With this command you can get the custom prefix of a specific guild.', usage='You have to provide the guildID you are looking for.')
    async def get_prefix(self, ctx: commands.Context, guildID=None):
        if guildID == None:
            return
        if ctx.author.id == int(ownerID):    
            cursor = connection.cursor(buffered=True)
            query = "SELECT guild_id, prefix FROM guild WHERE guild_id='"+guildID+"'"
            cursor.execute(query)
            for (guild_id, prefix) in cursor:
                if guild_id == str(guildID):
                    await ctx.send(f'The prefix for `{guild_id}` is `{prefix}`.')


    @commands.command(brief='Get the log.', help='Get the current, or all logfiles.', usage='<folder> | If you enter "folder", you will get the current log, as well as the last 5.')
    async def getlog(self, ctx: commands.Context, folder=None):
        if ctx.author.id == int(ownerID):
            if folder == None:
                try:
                    await ctx.send(file=discord.File(r''+log_folder+'\\DBDStats.log'))
                except discord.HTTPException as err:
                    if err.status == 413:
                        await message.edit(embed=discord.Embed(title="Log", description="The log is too big. Compressing...", color=0x0000ff))
                        with ZipFile(log_folder+'\\DBDStats.zip', mode='w', compression=ZIP_LZMA, allowZip64=True) as f:
                            f.write(log_folder+'\\DBDStats.log')
                        await message.edit(embed=discord.Embed(title="Log", description="I'm uploading the compressed log...", color=0x0000ff))
                        try:
                            await ctx.send(file=discord.File(r''+log_folder+'\\DBDStats.zip'))
                        except discord.HTTPException as err:
                            if err.status == 413:
                                await message.edit(embed=discord.Embed(title="Log", description="The log is still too big to be send directly.\nYou have to look at the log in your server(VPS),\noronly ask for the last few lines.", color=0xff0000))
                                await message.delete(10)
            elif folder == 'folder':
                if os.path.exists(log_folder+'\\DBDStats.zip'):
                    os.remove(log_folder+'\\DBDStats.zip')
                message = await ctx.send(embed=discord.Embed(title="Log", description="Compressing logs...", color=0x0000ff))
                with ZipFile(log_folder+'\\DBDStats.zip', mode='w', compression=ZIP_LZMA, allowZip64=True) as f:
                    if os.path.exists(log_folder+'\\DBDStats.log'):
                        f.write(log_folder+'\\DBDStats.log')
                    if os.path.exists(log_folder+'\\DBDStats.log.1'):
                        f.write(log_folder+'\\DBDStats.log.1')
                    if os.path.exists(log_folder+'\\DBDStats.log.2'):    
                        f.write(log_folder+'\\DBDStats.log.2')
                    if os.path.exists(log_folder+'\\DBDStats.log.3'):    
                        f.write(log_folder+'\\DBDStats.log.3')
                    if os.path.exists(log_folder+'\\DBDStats.log.4'):    
                        f.write(log_folder+'\\DBDStats.log.4')
                    if os.path.exists(log_folder+'\\DBDStats.log.5'):    
                        f.write(log_folder+'\\DBDStats.log.5')
                await message.edit(embed=discord.Embed(title="Log", description="Uploading logs...", color=0x0000ff))
                await ctx.send(file=discord.File(r''+log_folder+'\\DBDStats.zip'))
                await message.delete()
                os.remove(log_folder+'\\DBDStats.zip')
            else:
                await ctx.message.delete()




            







#Bot Commands
class Bot(commands.Cog):
    @commands.command(brief='Test Response', help='Test, if the bot is responding.')
    async def ping(self, ctx: commands.Context):
        before = time.monotonic()
        message = await ctx.send('Pong!')
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f'Pong! `{int(ping)}ms`')

    @commands.command(brief='Change prefix', help='Here you can change the prefix for this guild.', usage='[prefix]', pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx: commands.Context, prefix_input=None):
        if not prefix_input:
            cursor = connection.cursor(buffered=True)
            query = "SELECT guild_id, prefix FROM guild WHERE guild_id='"+str(ctx.guild.id)+"'"
            cursor.execute(query)
            for (guild_id, prefix) in cursor:
                if guild_id == str(ctx.guild.id):
                    await ctx.send(f'The current prefix for this guild is `{prefix}`.')
                else:
                    await ctx.send('The current prefix for this guild is `!`.')
        else:
            cursor = connection.cursor(buffered=True)
            query = "SELECT guild_id, prefix FROM guild WHERE guild_id='"+str(ctx.guild.id)+"'"
            cursor.execute(query)
            for (guild_id, prefix) in cursor:
                if prefix == prefix_input:
                    await ctx.send("The prefix didn't need to be updated.")
                    return
                else:
                    #Update existing
                    query = "UPDATE guild SET prefix='"+prefix_input+"' WHERE guild_id='"+str(ctx.guild.id)+"'"
                    cursor.execute(query)
                    connection.commit()
                    cursor.close()
                    await ctx.send(f'Your new custom prefix is now `{prefix_input}`.')
                    return
            #Adding new
            query = "INSERT INTO `guild` (`guild_id`, `prefix`) VALUES ('"+str(ctx.guild.id)+"', '"+prefix_input+"')"
            cursor.execute(query)
            connection.commit()
            cursor.close()
            await ctx.send(f'Your custom prefix is now `{prefix_input}`.')
    #Permission missmatch
    @prefix.error
    async def prefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.author.send('You are not allowed to use this command.\nYou need the "Manage Guild" permission to use it.')









#DBD Commands
class DBD(commands.Cog):
    @commands.command(brief='Get Stats', help='Get Stats from DBD about a specific SteamID64.')
    async def stats(self, ctx: commands.Context, id=None):
        if ctx.guild is None:
            await ctx.send(f'This command can only be used inside a server.')
            return
        await ctx.message.delete()
        if id == None:
            return
        check = CheckForDBD(id, steamAPIkey)
        if check == 1:
            message = await ctx.send(f'The SteamID64 has to be 17 chars long and only containing numbers.')
            await message.delete(delay=5)
        elif check == 2:
            message = await ctx.send(f'This SteamID64 is NOT in use.')
            await message.delete(delay=5)
        elif check == 3:
            embed = discord.Embed(description="It looks like this profile is private.\nHowever, in order for this bot to work, you must set your profile (including the game details) to public.\nYou can do so, by clicking [here](https://steamcommunity.com/profiles/"+id+"/edit/settings).", color=0xff0000)
            message = await ctx.send(embed=embed)
            await message.delete(delay=15)
        elif check == 4:
            embed = discord.Embed(description="I'm sorry, but this profile doesn't own DBD. But if you want to buy it,\nyou can take a look [here](https://www.g2a.com/n/dbdstats).", color=0x0400ff)
            message = await ctx.send(embed=embed)
            await message.delete(delay=15)
        elif check == 5:
            embed=discord.Embed(title="Fatal Error", description="It looks like there was an error querying the SteamAPI (probably a rate limit).\nThis will only affect the 'stats' and the 'leaderboard' command.\nPlease join our [Support-Server]("+support+") and create a ticket to tell us about this.", color=0xff0000)
            embed.set_author(name="./Serpensin.sh", icon_url="https://cdn.discordapp.com/avatars/863687441809801246/a_64d8edd03839fac2f861e055fc261d4a.gif")
            message = await ctx.send(embed=embed)
            await message.delete(delay=15)
        elif check == 0:
            #Get Stats from https://dbd.tricky.lol/
            resp = r.get(tricky_base+'playerstats?steamid='+id)
            data = resp.json()
            print(data)
        
    
    
    
    
    @commands.command(brief='Buy DBD', help='This will post a link to a site where you can buy DeadByDaylight for a few bucks.')
    async def buy(self, ctx: commands.Context):
        await ctx.message.delete()
        embed = discord.Embed(description='[Here](https://www.g2a.com/n/dbdstats) you can buy DeadByDaylight for a few bucks.', color=0x00ff11)
        message = await ctx.send(embed=embed)
        await message.delete(delay=30)
        
    
    
    @commands.command(brief='Rankreset timer', help='This will show how long it takes until the next rankreset.')
    async def reset(self, ctx: commands.Context):
        await ctx.message.delete()
        resp = r.get(tricky_base+'rankreset')
        data = resp.json()
        embed = discord.Embed(description='The next rank reset will take place on <t:'+str(data['rankreset'])+'>.', color=0x0400ff)
        message = await ctx.send(embed=embed)
        await message.delete(delay=15)
    
    
    





























#bot.run(TOKEN)
bot.run(TOKEN, log_handler=None)
