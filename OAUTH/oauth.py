# bot.py - Twitch Chat bot (TwitchIO)
# Author: ItsOiK
# Date: 15/07 - 2021

from decouple import config


CLIENT_ID = config("CLIENT_ID")
CLIENT_SECRET = config("CLIENT_SECRET")
ACCESS_TOKEN = config("ACCESS_TOKEN")
TMI = config("TMI")

BOT_NICK = "alphaomegaunited"


ALL_AUTH = {
    "CLIENT_ID": CLIENT_ID,
    "CLIENT_SECRET": CLIENT_SECRET,
    "ACCESS_TOKEN": ACCESS_TOKEN,
    "TMI": TMI,
    "BOT_NICK": BOT_NICK,
}
