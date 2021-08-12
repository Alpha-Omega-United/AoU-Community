import os

import aiohttp
import discord
from discord.ext import commands
import discord_slash
import dns.resolver
from loguru import logger

from bot import constants

# The reason we need this, is that dns lookup fails with default settings,
# so we need to set the dns severs manually,
# so to stop one dns from ruining our day lets use more than one.

# SOLUTION FROM:
# https://forum.omz-software.com/topic/6751/pymongo-errors-configurationerror-resolver-configuration-could-not-be-read-or-specified-no-nameservers/5

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = constants.DNS_SERVERS

import pymongo  # noqa: E402


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            # to be able to load cogs we need to use commands.Bot,
            # usally commands.bot operats on normal commands.
            # we are going to be using discord_slash we dont need a prefix
            # but since discord.py expects us to they require a prefix anyway
            # so just some spam is a nice work around
            command_prefix="sfsdknfsdoifmsoidoamdoadmoiadjmo",
            intents=discord.Intents.default(),
        )

        self.http_session = aiohttp.ClientSession()

        logger.info("Connecting to DB")
        self.db_client = pymongo.MongoClient(constants.DATABASE_URI)
        self.database = self.db_client[constants.DATABASE_NAME]

    def load_all_extensions(self) -> None:
        for file in constants.Paths.cogs.glob("*.py"):
            dot_path = str(file).replace(os.sep, ".")[:-3]
            self.load_extension(dot_path)

            logger.info(f"Loaded extension: {dot_path}")

    def run(self) -> None:
        super().run(constants.TOKEN)

    async def on_ready(self):
        logger.info("Bot online.")

    async def close(self) -> None:
        """Close http session when bot is shuting down."""
        if self.http_session:
            await self.http_session.close()

        await super().close()


def run() -> None:
    bot = Bot()
    slash = discord_slash.SlashCommand(bot, sync_commands=True)  # noqa: F841
    bot.load_all_extensions()

    logger.info("Starting bot")
    bot.run()
