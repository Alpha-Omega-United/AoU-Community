#!/usr/bin/python3

# Main.py - Entrypoint for app
# Author: ItsOiK
# Date: 14/07-2021


import multiprocessing
import requests
import os
import sys
import time
import datetime as dt

from typing import Iterable
from sanic import Sanic
from sanic.response import json, text
from loguru import logger
from threading import Thread
from decouple import config

from twitch_bot.twitch_bot import Bot as TwitchBotImport
# from discord_bot.discord_bot import Bot as DiscordBotImport


AOU_API = "http://192.168.31.54:8888/api"

AUTH = "123"
#! ------------------------------------------------------------------- #
#*                             LOGGER                                  #
#! ------------------------- SOMETHING ------------------------------- #


def should_rotate(message, file) -> bool:
    """When should the bot rotate : Once in 1 week or if the size is greater than 5 MB."""
    filepath = os.path.abspath(file.name)
    creation = os.path.getmtime(filepath)
    now = message.record["time"].timestamp()
    max_time = 1 * 24 * 60 * 60  # 1 day in seconds
    if file.tell() + len(message) > 5 * (2 ** 20):  # if greater than size 5 MB
        return True
    if now - creation > max_time:
        return True
    return False


logger.remove()
logger.add(
    sys.stdout, format="<g>{time:HH:mm:ss}</> | <lvl>{level: <2}</> | <c>{name}</>:<c>{function}</>:<c>{line}</>\t<lvl>{message}</lvl>")

logger.add("log/log.txt", rotation=should_rotate)
logger.info("STARTING: Logging Process")


def time_now():
    return int(dt.datetime.now().strftime("%H%M%S"))



#! --------------------------------------------------------------------------------------- #
#*                                    THREADING                                            #
#! ----------------------------------- SOMETHING ----------------------------------------- #
class TwitchBot():
    def __init__(self):
        self.twitch_bot_module = TwitchBotImport()
        self.twitch_bot_process = multiprocessing.Process(target=self.twitch_bot_module.run, daemon=True)
        self.start_twitch_bot()

    def start_twitch_bot(self):
        if self.twitch_bot_process.is_alive():
            logger.error("is alive")
            logger.error(self.twitch_bot_process)
            self.twitch_bot_process.terminate()
        self.twitch_bot_process = multiprocessing.Process(target=self.twitch_bot_module.run, daemon=True)
        logger.info("STARTING: Bot Thread")
        self.twitch_bot_process.start()

    def restart_twitch_bot(self):
        logger.warning("KILLING: Bot Thread")
        self.twitch_bot_process.terminate()
        logger.info("Bot Thread Re-Starting")
        self.start_bot()


#! --------------------------------------------------------------------------------------- #
#*                                        API                                              #
#! ----------------------------------- SOMETHING ----------------------------------------- #
async def bot_post(path, params, body):
    if path == "":
        pass
    else:
        logger.error("NO SUCH PATH")
        return text("NO SUCH PATH")


async def bot_get(path, params, body):
    logger.debug(path)
    logger.debug(params)
    logger.debug(body)
    if path == "restart_bot":
        import sys
        try:
            sys.exit(1)
        except Exception as e:
            logger.error(e)
        # try:
        #     twitch_bot.restart_bot()
        # except Exception as e:
        #     logger.error(e)
        # return text("Bot restarted")
    if path == "get_channel_chatters":
        result = await twitch_bot.twitch_bot_module.get_channel_chatters()
        logger.warning(result)
        logger.warning("updated channel chatters")
        return json(result)
    else:
        logger.error("NO SUCH PATH")
        return text("NO SUCH PATH")

#! --------------------------------------------------------------------------------------- #
#*                                        API                                              #
#! ----------------------------------- SOMETHING ----------------------------------------- #
endpoints = {
    "bot_post": bot_post,
    "bot_get": bot_get
}

app = Sanic("AoU Community Bot")


@app.route('/api/<endpoint>/<path>')
async def get_requests(request, endpoint, path):
    params = request.args
    body = request.json
    # logger.debug(f"MAIN API GET: received params: {params}")
    # logger.debug(f"MAIN API GET: received body: {body}")
    if check_password(request):
        response = endpoints.get(endpoint)
        if response:
            result = await response(path, params, body)
            return result
        else:
            logger.error("no such endpoint")
            return text("no such endpoint")
    else:
        logger.error("Wrong Password: Unathorized")
        return text("Wrong Password: Unathorized")


@app.post('/api/<endpoint>/<path>')
async def post_requests(request, endpoint, path):
    params = request.args
    body = request.json
    # logger.warning(f" MAIN API POST: received params: {params}")
    # logger.warning(f" MAIN API POST: received body: {body}")
    if check_password(request):
        response = endpoints.get(endpoint)
        if response:
            result = await response(path, params, body)
            return result
        else:
            logger.error("no such endpoint")
            return text("no such endpoint")
    else:
        logger.error("Wrong Password: Unathorized")
        return text("Wrong Password: Unathorized")


def check_password(request):
    logger.debug(f"Checking password")
    # logger.warning(request.headers)
    password = request.headers.get("password")
    if password is None:
        logger.warning("Password was None")
        password = request.json["password"]
    if str(password) != AUTH:
        return False
    else:
        return True


if __name__ == '__main__':
    logger.info("STARTING: Threaded Modules")
    twitch_bot = TwitchBot()
    # discord_bot = DiscordBot()
    logger.info("STARTING: API server Loop")
    app.run(host="0.0.0.0", port="8888")
