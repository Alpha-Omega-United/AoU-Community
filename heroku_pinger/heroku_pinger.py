# heroku_pinger.py - Keeps heroku app from idling
# Author: ItsOiK
# Date: 31/08-2021

import datetime as dt
import time
import requests
import math
from loguru import logger
from random import randint
from threading import Thread

AOU_HEROKU_ENDPOINT = "https://aou-website-backend.herokuapp.com/"


timespan = (10, 25)


class HerokuPinger():
    def __init__(self) -> None:
        """
        init
        """
        self.heroku_thread = Thread(target=self.run, daemon=True)

    def ping_heroku(self) -> None:
        """
        handles pinging heroku to keep alive
        """
        logger.info("INIT: heroku_pinger")
        logger.warning("Pinging heroku")
        response = requests.get(AOU_HEROKU_ENDPOINT)
        if response.status_code == 200:
            result = response.json()
            result_status = result["status"]
            logger.debug(f"Heroku ping status: {result_status}")
        else:
            logger.warning(f"Heroku ping status: unsuccessfull")

    def run(self) -> None:
        """
        runs loop for the pinger - use start to start thread

        will ping heroku between "timespan" minutes
        """
        logger.info("STARTED: heroku_pinger")
        while True:
            self.ping_heroku()
            next_ping = randint(timespan[0], timespan[1]) * 60
            logger.debug(
                f"Next ping in: {int(next_ping/60)} mintues")
            time.sleep(next_ping)

    def start(self) -> None:
        """
        starts the thread for the pinger
        """
        self.heroku_thread.start()
