# point_system.py - Point system for AoU LeaderBoard
# Author: ItsOiK
# Date: 15/07 - 2021

import datetime as dt
import requests
import ast
import json
import math
import time

from threading import Thread
from loguru import logger


def time_now():
    return int(dt.datetime.now().strftime("%H%M%S"))


POINT_AMOUNT_LURK = 5
POINT_AMOUNT_HOST = 25
POINT_AMOUNT_RAID = 50

UPDATE_INTERVAL = 300


class PointSystem():
    def __init__(self):
        self.channel_list_to_check = []
        self.json_buffer = {}
        self.last_updated_chatters = time_now()-295
        self.make_chatter_list()
        self.point_system_thread = Thread(target=self.run, daemon=True)
        self.point_system_thread.start()

    def run(self):
        logger.info("STARTING: Leaderboard Point System")
        try:
            self.last_updated_chatters = self.json_buffer["last_updated_chatters"]
        except KeyError as e:
            logger.error(e)
        time_to_update = abs(abs(self.last_updated_chatters - time_now()) - UPDATE_INTERVAL)
        logger.info(f"UPDATE in {math.floor(time_to_update / 60)}:{time_to_update % 60}")
        while True:
            if self.last_updated_chatters - time_now() <= UPDATE_INTERVAL:
                logger.info("Updating Point System")
                self.last_updated_chatters = time_now()
                self.update()
                time.sleep(UPDATE_INTERVAL)

    def get_chatters_in_channel(self, channel):
        endpoint = f"https://tmi.twitch.tv/group/user/{channel}/chatters"
        response = requests.get(endpoint)
        data = response.json()
        return data

    def update(self):
        for index, channel in enumerate(self.channel_list_to_check):
            viewers_on_channel = []
            if channel != "alphaomegaunited":
                logger.info(f"checking channel #{index + 1}/{len(self.channel_list_to_check)}: {channel}")
                result = self.get_chatters_in_channel(channel)
                for (key, value) in result["chatters"].items():
                    if key != "broadcaster":
                        for viewer in value:
                            if viewer in self.json_buffer["users"].keys() and viewer != "alphaomegaunited":
                                viewers_on_channel.append(viewer)
                                self.json_buffer = self.load_json()
                                self.json_buffer["users"][viewer]["points"] += POINT_AMOUNT_LURK
                if len(viewers_on_channel) > 0:
                    logger.debug(f"updated points on: {viewers_on_channel} in {channel}")
        self.json_buffer["last_updated_chatters"] = time_now()
        self.save_json()
        logger.info(f"Saved file")

    def make_chatter_list(self):
        self.load_json()
        self.channel_list_to_check = []
        for (key, value) in self.json_buffer["users"].items():
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


# a = {
# 	'_links': {
# 	},
# 	'chatter_count': 18,
# 	'chatters': {
# 		'broadcaster': [
# 			'calviz_gaming'
# 		],
# 		'vips': [
# 			'deliriouszendera',
# 			'nexxerd'
# 		],
# 		'moderators': [
# 			'nightbot',
# 			'streamelements'
# 		],
# 		'staff': [
# 		],
# 		'admins': [
# 		],
# 		'global_mods': [
# 		],
# 		'viewers': [
# 			'2020',
# 			'academyimpossible',
# 			'alphaomegaunited',
# 			'ankaplaysgames',
# 			'anotherttvviewer',
# 			'calviz_root',
# 			'commanderroot',
# 			'dcserverforsmallstreamers',
# 			'irishvikingr',
# 			'luffydstream',
# 			'mslenity',
# 			'sniperxpgamer',
# 			'stormpostor'
# 		]
# 	}
