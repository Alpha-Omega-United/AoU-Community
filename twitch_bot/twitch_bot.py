# bot.py - Twitch Chat bot (TwitchIO)
# Author: ItsOiK
# Date: 15/07 - 2021

import socket
import asyncio
import requests
import re
import time
import datetime as dt
import json
import threading
import ctypes

from loguru import logger
from twitchio.ext import commands
from random import choice
from random import randint

from .command_aliases import com_aliases
from twitch_bot.extra.points import PointSystem
from OAUTH.oauth import ALL_AUTH
from aou_database.aou_database import AouDatabase


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
        self.aouDb = AouDatabase()
        self.restart_timer = None
        self.now = dt.datetime.now().strftime("%H%M%S")
        logger.info("STARTING: AoU Community bot")
        self.JSON_BUFFER = {}
        self.CHANNELS = []
        self.MODERATORS = []
        self.load_channels_to_join()
        self.prefix = "!"
        self.ignore_commands = ["test"]
        self.point_system = PointSystem(self.aouDb)
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(token=TMI, prefix='!', initial_channels=self.CHANNELS)

# #! -------------------------------- CHATBOT STARTING -------------------------------------- #
    async def event_ready(self, event):
        print(event)
        # Called once the bot goes online
        logger.info(f"STARTED: {BOT_NICK}")
        ws = self._ws  # this is only needed to send messages within event_ready
        # for index, channel in enumerate(self.CHANNELS):
        #     logger.debug(f"AoU-bot joined #{index + 1}/{len(self.CHANNELS)}: {channel}")
        await ws.send_privmsg(BOT_NICK, f"/me bot has landed!")
        # # await ws.send_privmsg("itsoik", f"/me bot has landed!")

#! --------------------------------- CHATBOT EVENT --------------------------------------- #
    # async def event_message(self, ctx):
    #     self.now = dt.datetime.now()
    #     time_of_chat_msg = self.now.strftime("%H%M%S")
    #     # runs every time a message is sent in chat.
    #     # make sure the bot ignores itself and the streamer
    #     try:
    #         if ctx.author.name.lower() == BOT_NICK.lower():
    #             return
    #     except Exception as e:
    #         logger.error(e)
    #         logger.error("something went wrong.....")
    #         logger.debug(ctx)
    #     # await self.handle_commands(ctx)
    #     # logger.error(ctx)
    #     # logger.error(ctx.author)
    #     # logger.error(ctx.content)
    #     # await ctx.channel.send(ctx.content) #! REPLIES TO ALL CHAT MESSAGES SENT WITH MESSAGE SENT

    #! ERROR HANDLING THINGY!
    # async def event_command_error(self, ctx, error):
    #     logger.error(f"event_command_error: Channel: {ctx.channel}; Command {error}")


# ! ------------------------------------ ON-LOAD ------------------------------------------- #
    def load_channels_to_join(self):
        member_data = self.aouDb.collection.find({})
        members_channels = []
        for list_user in member_data:
            members_channels.append(list_user["twitch_name"])
        self.CHANNELS = members_channels
        self.CHANNELS.append("alphaomegaunited")
        logger.warning(f"joined {len(self.CHANNELS)} channels")


# ! --------------------------------------------------------------------------------------- #
# *                                       COMMANDS                                          #
# ! ------------------------------------ REGULAR ------------------------------------------ #
    @commands.command(aliases=com_aliases["test_aliases"])
    async def test(self, ctx: commands.Context):
        # if ctx.author.name in self.CHANNELS:
        await ctx.send("tested")

    @commands.command(aliases=com_aliases["aou_discord_aliases"])
    async def aou_discord(self, ctx: commands.Context):
        # if ctx.author.name in self.CHANNELS:
        await ctx.send("""Alpha Omega United is a Twitch/Discord Community.
        We have community nights, game nights, tournaments and have some cool extra
        features to come in the near future, wether you are a gamer, streamer or
        anywhere in between this is a great place to meet likeminded people and
        share some LUL 's :D Discord: https://discord.gg/P5qnher4kV - Website: https://alpha-omega-united.github.io/""")

    @commands.command(aliases=com_aliases["signup_aliases"])
    async def signup(self, ctx: commands.Context):
        user = ctx.author.name
        if not self.check_if_user_in_buffer(user):
            logger.debug(f"{user} to add")
            self.add_user_to_buffer_and_save(user)
            await ctx.send(f"{user}, Added to Watchlist, if you have custom bot name, type !bot followed by the name of your bot, example: !bot AoU_bot")
            await self.restart_bot()
        else:
            await ctx.send(f"{user}, Already in watchlist, did you want to register your bot instead? type !bot followed by the name of your bot, example: !bot AoU_bot")
        await ctx.send(f"{user}, It may take up to 30minutes before the bot joins your channel.")

    @commands.command(aliases=com_aliases["bot_aliases"])
    async def bot(self, ctx: commands.Context):
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

    @commands.command(aliases=com_aliases["remove_aliases"])
    async def remove(self, ctx: commands.Context):
        if ctx.author.name in self.MODERATORS:
            user_to_remove = ctx.content.split(" ")[1]
            removed_user = self.JSON_BUFFER["users"].pop(user_to_remove, None)
            if removed_user is None:
                user_to_remove = removed_user
            await ctx.send(f"{user_to_remove} was removed from the watchlist")
            # //TODO SOMETNiHG
            # self.save_json(AOU_MEMBERS)
        else:
            await ctx.send("You dont have permission to do that, contact a moderator on discord")

    @commands.command(aliases=com_aliases["restart_aliases"])
    async def restart(self, ctx: commands.Context):
        if ctx.author.name in self.MODERATORS:
            await ctx.send("Restarting in now")
            await self.restart_bot(True)

#! ------------------------------- CHATBOT #HELP LIST ------------------------------------- #
    @ commands.command()
    async def help(self, ctx: commands.Context):
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

    def add_user_to_buffer_and_save(self, user, twitch_id: int = 0):
        """add user to buffer and saves"""
        logger.info(f"{user} added to file")
        new_data = {"twitch_id": twitch_id,
                    "points": 0}
        self.JSON_BUFFER["users"][user.lower()] = new_data
        # TODO SOMETHING
        # self.save_json(AOU_MEMBERS_)

    def add_bot_to_buffer_and_save(self, user, bot):
        logger.info(f"{user} added {bot} to file")
        self.JSON_BUFFER["bots"].append(bot.lower())
        # TODO SOMETHING
        # self.save_json(AOU_MEMBERS_)

    async def restart_bot(self, now=False):
        if not now:
            await asyncio.sleep(300)
        logger.warning("bot restarting")
        await self.get_api_call("restart_bot")


#! --------------------------------------------------------------------------------------- #
#*                                      RESTART                                            #
#! ----------------------------------- SOMETHING ----------------------------------------- #
