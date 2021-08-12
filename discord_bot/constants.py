import os
import pathlib
from typing import NamedTuple

import dotenv


dotenv.load_dotenv()

# The reason we need this, is that dns lookup fails with default settings,
# so we need to set the dns severs manually,
# so to stop one dns from ruining our day lets use more than one.

# SOLUTION FROM:
# https://forum.omz-software.com/topic/6751/pymongo-errors-configurationerror-resolver-configuration-could-not-be-read-or-specified-no-nameservers/5

DNS_SERVERS = [
    # Google
    "8.8.8.8",
    "8.8.4.4",
    # Cloudflare
    "1.1.1.1",
]


def load_required(key: str) -> str:
    value = os.getenv(key, None)
    if value is None:
        raise EnvironmentError(f"Missing envioroment varible {key!r}")
    return value


TOKEN = load_required("DISCORD_TOKEN")

DATABASE_URI = load_required("DATABASE_URI")
DATABASE_NAME = load_required("DATABASE_NAME")

# Testing unhides all messages.
# WARNING: DO NOT ENABLE IN PROD
TESTING = bool(os.getenv("TESTING", False))
HIDE_MESSAGES = not TESTING

# Default to real server
GUILD_ID = int(os.getenv("GUILD_ID", 797571990176661504))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", 797573934848802817))


class Paths(NamedTuple):
    src = pathlib.Path("bot")
    cogs = src / "cogs"
    resources = src / "resources"
