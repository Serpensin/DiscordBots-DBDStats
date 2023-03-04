# Info

This Bot can show informations about DBD Player stats and items.
Currently this only works for Steam.

### Setup

#### Classic
      1. Make sure you have Python 3.9 installed. I used 3.9.7 to develop this bot. (https://www.python.org/downloads/)
      2. Clone this repo, or download the zip file.
      3. Open a terminal inside "DBDStats" in the folder where you cloned the repo, or extracted the zip file.
      4. Run `pip install -r requirements.txt` to install the dependencies.
      5. Open the file ".env" and fill out all variables.
          5.1. TOKEN is the token of your bot. (https://discord.com/developers/applications)
          5.2. OWNER_ID is your DiscordID.
          5.3. steamAPIkey is your SteamAPI key. You can get your key at https://steamcommunity.com/dev/apikey.
          5.4. support_server is the ID of your support server. The bot needs to be part of this so he can  
               create an invite if someone needs support.
          5.5. twitch_client_id is the client id of your twitch app. (https://dev.twitch.tv/console/apps)
          5.6. twitch_client_secret is the client secret of your twitch app. (https://dev.twitch.tv/console/apps)
      6. Run `python main.py` or `python3 main.py` to start the bot.

#### Docker
##### Create the image yourself
      1. Make sure you have Docker installed. (https://docs.docker.com/get-docker/)
      2. Clone this repo, or download the zip file.
      3. Open a terminal inside "WebhookCreator" in the folder where you cloned the repo, or extracted the zip file.
      4. Run `docker build -t webhookcreator .` to build the docker image.
      5. Run `docker run -v log:/app/DBDStats/Logs --name DBDStats --health-interval 1m30s --health-retries 1m30s --health-cmd CMD --health-cmd curl --health-cmd -f --health-cmd http://localhost --restart any -e steamAPIkey=STEAM_APIKEY -e support_server=ID_OF_SUPPORTSERVER -e TOKEN=BOT_TOKEN -e OWNER_ID=DISCORD_ID_OF_OWNER -e twitch_client_id -e twitch_client_secret serpensin/dbdstats` to start the bot.
##### Use my pre-build image
      1. Make sure you have Docker installed. (https://docs.docker.com/get-docker/)
      2. Open a terminal.
      3. Run `docker run -v log:/app/DBDStats/Logs --name DBDStats --health-interval 1m30s --health-retries 1m30s --health-cmd CMD --health-cmd curl --health-cmd -f --health-cmd http://localhost --restart any -e steamAPIkey=STEAM_APIKEY -e support_server=ID_OF_SUPPORTSERVER -e TOKEN=BOT_TOKEN -e OWNER_ID=DISCORD_ID_OF_OWNER -e twitch_client_id -e twitch_client_secret serpensin/dbdstats` to start the bot.

You can also [invite](https://discord.com/api/oauth2/authorize?client_id=1030163127926542400&permissions=137506506753&scope=bot%20applications.commands) the bot I host to your server.

