# bot.py - Twitch Chat bot (TwitchIO)
# Author: ItsOiK
# Date: 15/07 - 2021

from .command_aliases import *
import socket
import asyncio
import requests
import re
import time
import datetime as dt
import json

from random import randint
import threading
from loguru import logger
from twitchio.ext import commands
from random import choice

import ctypes

from OAUTH.oauth import ALL_AUTH
from bot.extra.points import PointSystem


CLIENT_ID = ALL_AUTH["CLIENT_ID"]
CLIENT_SECRET = ALL_AUTH["CLIENT_SECRET"]
ACCESS_TOKEN = ALL_AUTH["ACCESS_TOKEN"]
TMI = ALL_AUTH["TMI"]
BOT_NICK = ALL_AUTH["BOT_NICK"]
AOU_API = "http://192.168.31.54:8888/api"


def time_now():
    return dt.datetime.now().strftime("%H:%M:%S")


class Bot(commands.Bot):
    def __init__(self):
        self.restart_timer = None
        self.now = dt.datetime.now().strftime("%H%M%S")
        logger.info("STARTING: AoU Community bot")
        self.JSON_BUFFER = {}
        self.CHANNELS = []
        self.MODERATORS = []
        self.load_channels_to_join()
        self.prefix = "!"
        self.ignore_commands = ["test"]
        self.point_system = PointSystem()
        super().__init__(
            irc_token=TMI,
            client_id=CLIENT_ID,
            nick=BOT_NICK,
            prefix=self.prefix,
            initial_channels=self.CHANNELS
        )

#! -------------------------------- CHATBOT STARTING -------------------------------------- #
    async def event_ready(self):
        # Called once the bot goes online
        logger.info(f"STARTED: {BOT_NICK}")
        ws = self._ws  # this is only needed to send messages within event_ready
        for index, channel in enumerate(self.CHANNELS):
            logger.debug(f"AoU-bot joined #{index + 1}/{len(self.CHANNELS)}: {channel}")
        await ws.send_privmsg("alphaomegaunited", f"/me bot has landed!")
        # await ws.send_privmsg("itsoik", f"/me bot has landed!")

    async def join_more_channels(self, channels):
        await self._ws.join_channels(channels)

#! --------------------------------- CHATBOT EVENT --------------------------------------- #
    async def event_message(self, ctx):
        self.now = dt.datetime.now()
        time_of_chat_msg = self.now.strftime("%H%M%S")
        # runs every time a message is sent in chat.
        # make sure the bot ignores itself and the streamer
        if ctx.author.name.lower() == BOT_NICK.lower():
            return
        await self.handle_commands(ctx)

        # await ctx.channel.send(ctx.content) #! REPLIES TO ALL CHAT MESSAGES SENT WITH MESSAGE SENT

    #! ERROR HANDLING THINGY!
    # async def event_command_error(self, ctx, error):
    #     logger.error(f"event_command_error: Channel: {ctx.channel}; Command {error}")

#! --------------------------------------------------------------------------------------- #
#*                                    FILE HANDLER                                         #
#! ------------------------------------ LOADING ------------------------------------------ #
    def load_json(self, file_name):
        with open(file_name) as file:
            content = file.read()
            self.JSON_BUFFER = json.loads(content)
            self.MODERATORS = self.JSON_BUFFER["MODERATORS"]
            return self.JSON_BUFFER

#! ------------------------------------ SAVING ------------------------------------------- #
    def save_json(self, file_name):
        with open(file_name, "w") as file:
            json.dump(self.JSON_BUFFER, file)

#! ------------------------------------ ON-LOAD ------------------------------------------- #
    def load_channels_to_join(self):
        member_data = self.load_json("bot/data/aou_members.json")
        members_channels = []
        for (key, value) in member_data["users"].items():
            members_channels.append(key)
        self.CHANNELS = members_channels

    def load_bots_to_watch(self):
        pass

#! --------------------------------------------------------------------------------------- #
#*                                       COMMANDS                                          #
#! ------------------------------------ REGULAR ------------------------------------------ #
    @commands.command(name="test", aliases=test_aliases)
    async def test(self, ctx):
        if ctx.author.name in self.CHANNELS:
            await ctx.send("tested")

    @commands.command(name="signup", aliases=signup_aliases)
    async def signup(self, ctx):
        user = ctx.author.name
        if not self.check_if_user_in_buffer(user):
            self.add_user_to_buffer_and_save(user)
            await ctx.send(f"{user}, Added to Watchlist, if you have custom bot name, type !bot followed by the name of your bot, example: !bot AoU_bot")
            await self.restart_bot()
        else:
            await ctx.send(f"{user}, Already in watchlist, did you want to register your bot instead? type !bot followed by the name of your bot, example: !bot AoU_bot")
        await ctx.send(f"{user}, It may take up to 30minutes before the bot joins your channel.")

    @commands.command(name="bot", aliases=["bots"])
    async def bot(self, ctx):
        if "!bots" in ctx.content:
            bots = ", ".join(self.JSON_BUFFER["bots"])
            await ctx.send(f"You have registered these bots: {bots}")
            return
        user = ctx.author.name
        bot = ctx.content.split(" ")[1]
        if self.check_if_bot_in_buffer(user, bot):
            await ctx.send(f"{bot} Already added, you can add more bots if you have multiple, just repeat the command again, do '!bots' to see all the bots you have registered")
        else:
            self.add_bot_to_buffer_and_save(ctx.author.name, bot)
            await ctx.send(f"{bot} Successfully added, you can add more bots if you have multiple, just repeat the command again, do '!bots' to see all the bots you have registered")

    @commands.command(name="remove", aliases=test_aliases)
    async def remove(self, ctx):
        if ctx.author.name in self.MODERATORS:
            user_to_remove = ctx.content.split(" ")[1]
            removed_user = self.JSON_BUFFER["users"].pop(user_to_remove, None)
            if removed_user is None:
                user_to_remove = removed_user
            await ctx.send(f"{user_to_remove} was removed from the watchlist")
            self.save_json("bot/data/aou_members.json")
        else:
            await ctx.send("You dont have permission to do that, contact a moderator on discord")

    @commands.command(name="restart", aliases=test_aliases)
    async def restart(self, ctx):
        if ctx.author.name in self.MODERATORS:
            await ctx.send("Restarting in now")
            await self.restart_bot(True)

#! ------------------------------- CHATBOT #HELP LIST ------------------------------------- #
    @ commands.command(name="help")
    async def help(self, ctx):
        """grabs all commands from the magic carpet
        and sends a msg with a formatted string"""
        command_names = [command for command in self.commands]
        add_prefix = [f"{self.prefix}{word}, " for word in command_names if word not in self.ignore_commands]
        message = ""
        for command in add_prefix:
            message += command
        await ctx.send(f"Available commands are: {message}")

#! --------------------------------------------------------------------------------------- #
#*                                        API                                              #
#! ----------------------------------- RECEIVING ----------------------------------------- #
    async def send_msg_to_chat_as_bot(self, msg):
        await self._ws.send_privmsg(self.CHANNELS, f"{msg}")

#! --------------------------------------------------------------------------------------- #
#*                                        API                                              #
#! ------------------------------------ SENDING ------------------------------------------ #
    async def get_api_call(self, path):
        headers = {"password": "123"}
        endpoint = f"{AOU_API}/bot_get/{path}"
        response = requests.get(endpoint, headers=headers)
        logger.debug(response.text)

    async def post_api_call(self, path, params):
        response = requests.post()

#! --------------------------------------------------------------------------------------- #
#*                                     FUNCTIONS                                           #
#! ----------------------------------- SOMETHING ----------------------------------------- #
    def check_if_bot_in_buffer(self, user, bot):
        if self.check_if_user_in_buffer(user):
            for bot_in_buffer in self.JSON_BUFFER["bots"]:
                if bot == bot_in_buffer:
                    return True
        return False

    def check_if_user_in_buffer(self, user):
        if user in self.JSON_BUFFER["users"].keys():
            return True
        return False

    def add_user_to_buffer_and_save(self, user):
        """add user to buffer and saves"""
        logger.info(f"{user} added to file")
        new_data = {"bots": ["alphaomegaunited", "streamelements", "streamlabs", "nightbot", "moobot", "deepbot", "wizebot"],
                    "points": 0}
        self.JSON_BUFFER["users"][user.lower()] = new_data
        self.save_json("bot/data/aou_members.json")

    def add_bot_to_buffer_and_save(self, user, bot):
        logger.info(f"{user} added {bot} to file")
        self.JSON_BUFFER["bots"].append(bot.lower())
        self.save_json("bot/data/aou_members.json")

    async def restart_bot(self, now=False):
        if not now:
            await asyncio.sleep(300)
        logger.warning("bot restarting")
        await self.get_api_call("restart_bot")


#! --------------------------------------------------------------------------------------- #
#*                                      RESTART                                            #
#! ----------------------------------- SOMETHING ----------------------------------------- #
