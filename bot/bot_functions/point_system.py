# point_system.py - Point system for AoU LeaderBoard
# Author: ItsOiK
# Date: 15/07 - 2021

import datetime as dt
import requests
import ast
import json

from threading import Thread
from loguru import logger


def time_now():
    return int(dt.datetime.now().strftime("%H%M%S"))


POINT_AMOUNT_LURK = 5
POINT_AMOUNT_HOST = 5
POINT_AMOUNT_RAID = 15

UPDATE_INTERVAL = 300


class PointSystem():
    def __init__(self):
        self.channel_list_to_check = []
        self.json_buffer = {}
        self.make_chatter_list()
        self.point_system_thread = Thread(target=self.run, daemon=True)
        self.last_updated_chatters = time_now()-295
        self.point_system_thread.start()

    def run(self):
        logger.info("STARTING: Leaderboard Point System")
        while True:
            # try:
            if abs(self.last_updated_chatters - time_now()) > UPDATE_INTERVAL:
                self.last_updated_chatters = time_now()
                self.update_file_with_points()
            # except Exception as e:
            #     logger.error(e)

    def get_chatters_in_channel(self, channel):
        endpoint = f"https://tmi.twitch.tv/group/user/{channel}/chatters"
        response = requests.get(endpoint)
        data = response.json()
        return data

    def update_file_with_points(self):
        for channel in self.channel_list_to_check:
            if channel != "MODERATORS":
                result = self.get_chatters_in_channel(channel)
                for viewer in result["chatters"]["viewers"]:
                    if viewer in self.json_buffer.keys():
                        if viewer != "MODERATORS":
                            logger.warning(f"update points on: {viewer}")
                            self.json_buffer = self.load_json()
                            self.json_buffer[viewer]["points"] += POINT_AMOUNT_LURK
                            self.save_json()

    def make_chatter_list(self):
        self.load_json()
        self.channel_list_to_check = []
        for (key, value) in self.json_buffer.items():
            self.channel_list_to_check.append(key)

    def load_json(self):
        with open("bot/data/aou_members.json") as file:
            content = file.read()
            self.json_buffer = json.loads(content)
            return self.json_buffer

#! ------------------------------------ SAVING ------------------------------------------- #
    def save_json(self):
        with open("bot/data/aou_members.json", "w") as file:
            json.dump(self.json_buffer, file)
