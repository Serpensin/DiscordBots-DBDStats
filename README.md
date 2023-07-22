# Dead by Daylight Stats Bot [![Discord Bot Invite](https://img.shields.io/badge/Invite-blue)](https://discord.com/oauth2/authorize?client_id=1030163127926542400&permissions=67423232&scope=bot)[![Discord Bots](https://top.gg/api/widget/servers/1030163127926542400.svg)](https://top.gg/bot/1030163127926542400)

This Discord bot allows you to display Dead by Daylight (DBD) player stats and items for Steam users. It supports multiple methods to set up and start the bot, including the Classic Method and Docker Method.
Commands, that only be used by the owner of the bot, can only be used in a DM with the bot. Write `help`, to get a list of available owner commands.

## Features

- Retrieve player statistics for Dead by Daylight
- Display information about in-game items
- Supports multiple installation methods
- Integrates with MongoDB for data storage (optional)

## Setup

### Classic Method

1. Ensure Python 3.9 is installed. This bot was developed using Python 3.9.7. Download it [here](https://www.python.org/downloads/).
2. Clone this repository or download the zip file.
3. Open a terminal in the "DBDStats" folder where you cloned the repository or extracted the zip file.
4. Run `pip install -r requirements.txt` to install the dependencies.
5. Open the file ".env.template" and complete all variables:
   - `TOKEN`: The token of your bot. Obtain it from the [Discord Developer Portal](https://discord.com/developers/applications).
   - `OWNER_ID`: Your Discord ID.
   - `steamAPIkey`: Your Steam API key. Get your key from the [Steam Community API page](https://steamcommunity.com/dev/apikey).
   - `support_server`: The ID of your support server. The bot must be a member of this server to create an invite if someone requires support.
   - `twitch_client_id`: The client ID of your Twitch app. Obtain it from the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
   - `twitch_client_secret`: The client secret of your Twitch app. Obtain it from the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
   - `libretransURL`: The URL of your LibreTranslate instance.
   - `libretransAPIkey`: The API key for the LibreTranslate instance.
   - `MongoDB_host`: The MongoDB host address.
   - `MongoDB_port`: The MongoDB port number.
   - `MongoDB_user`: The MongoDB username.
   - `MongoDB_password`: The MongoDB password.
   - `MongoDB_database`: The MongoDB database name.
   - `MongoDB_collection`: The MongoDB collection name.
6. Rename the file ".env.template" to ".env".
7. Run `python main.py` or `python3 main.py` to start the bot.

### Docker Method

#### Docker Compose Method

If you have cloned the repository, you will find two Docker Compose files in the `DBDStats/Docker-compose` folder. The regular version includes MongoDB (recommended), while the "docker-compose_without_MongoDB" version contains only the bot without MongoDB.

1. Make sure Docker and Docker Compose are installed. Download Docker [here](https://docs.docker.com/get-docker/) and Docker Compose [here](https://docs.docker.com/compose/install/).

2. Navigate to the `DBDStats/Docker-compose` folder where you cloned the repository or extracted the zip file.

##### Regular Version (with MongoDB)

3. Open the `docker-compose.yml` file and update the environment variables as needed (such as `steamAPIkey`, `support_server`, `TOKEN`, `OWNER_ID`, `twitch_client_id`, and `twitch_client_secret`).

4. In the terminal, run the following command from the `DBDStats/Docker-compose` folder to start the bot with MongoDB:
`docker-compose up -d`

##### Version without MongoDB

3. Open the `docker-compose_without_MongoDB.yml` file and update the environment variables as needed (such as `steamAPIkey`, `support_server`, `TOKEN`, `OWNER_ID`, `twitch_client_id`, and `twitch_client_secret`).

4. In the terminal, run the following command from the `DBDStats/Docker-compose` folder to start the bot without MongoDB:
docker-compose -f docker-compose_without_MongoDB.yml up -d

#### Build the image yourself

1. Ensure Docker is installed. Download it from the [Docker website](https://docs.docker.com/get-docker/).
2. Clone this repository or download the zip file.
3. Open a terminal in the "DBDStats" folder where you cloned the repository or extracted the zip file.
4. Run `docker build -t dbdstats .` to build the Docker image.

#### Use the pre-built image

1. Ensure Docker is installed. Download it from the [Docker website](https://docs.docker.com/get-docker/).
2. Open a terminal.
3. Run the bot with the command below:
   - Modify the variables according to your requirements.
   - Set the `steamAPIkey`, `TOKEN`, and `OWNER_ID`.
   - Variables containing 'twitch' are for the Twitch command. Remove them if you don't want to use this command.
   - The `libretransURL` variable is for translating output. Remove it if you don't need it.
   - The `libretransAPIkey` variable is the API key for the LibreTranslate instance set in the `libretransURL` variable.
   - Variables containing 'MongoDB' are for storing the bot's data. Remove them if you don't want to use MongoDB.

#### Run the bot
```bash
docker run -d \
-e steamAPIkey=STEAM_APIKEY \
-e support_server=ID_OF_SUPPORTSERVER \
-e TOKEN=BOT_TOKEN \
-e OWNER_ID=DISCORD_ID_OF_OWNER \
-e twitch_client_id=twitch_client_id \
-e twitch_client_secret=twitch_client_secret \
-e libretransURL=https://YOUR_INSTANCE_OF_LIBRETRANS \
-e libretransAPIkey=APIkey_for_instance_of_libretrans \
-e MongoDB_host=IP_OR_DOMAIN_OF_MONGODB \
-e MongoDB_port=PORT_OF_MONGODB \
-e MongoDB_user=USER_OF_MONGODB \
-e MongoDB_password=PASSWORD_OF_MONGODB \
-e MongoDB_database=DATABASE_OF_MONGODB \
-e MongoDB_collection=COLLECTION_OF_MONGODB \
--name DBDStats \
--restart any \
-v dbdstats_log:/app/DBDStats/Logs \
serpensin/dbdstats
```
