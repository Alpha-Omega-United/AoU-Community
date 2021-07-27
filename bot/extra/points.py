# point_system.py - Point system for AoU LeaderBoard
# Author: ItsOiK
# Date: 15/07 - 2021


import requests
import ast
import json
import math
import time

from threading import Thread
from loguru import logger


from OAUTH.oauth import ALL_AUTH
CLIENT_ID = ALL_AUTH["CLIENT_ID"]
ACCESS_TOKEN = ALL_AUTH["ACCESS_TOKEN"]


POINT_AMOUNT_LURK = 10
POINT_AMOUNT_HOST = 25
POINT_AMOUNT_RAID = 50

UPDATE_INTERVAL = 600


class PointSystem():
    def __init__(self):
        self.channel_list_to_check = []
        self.json_buffer = {}
        self.last_updated_chatters = int(time.time())
        self.make_chatter_list()
        self.point_system_thread = Thread(target=self.run, daemon=True)
        self.point_system_thread.start()
        self.last_updated_chatters = self.json_buffer["last_updated_chatters"]

    def run(self):
        logger.info("STARTING: Leaderboard Point System")
        time_to_next_update = abs(int(time.time()) - self.last_updated_chatters - UPDATE_INTERVAL)
        logger.warning(f"update in: {math.floor(time_to_next_update / 60)}:{time_to_next_update % 60}")
        while True:
            if abs(int(time.time()) - self.last_updated_chatters) >= UPDATE_INTERVAL:
                logger.info("Updating Point System")
                self.last_updated_chatters = int(time.time())
                self.update()
                time.sleep(UPDATE_INTERVAL)

#! -------------------------------- FILE HANDLING --------------------------------------- #
    def save_json(self):
        with open("bot/data/aou_members.json", "w") as file:
            json.dump(self.json_buffer, file)

    def load_json(self):
        with open("bot/data/aou_members.json") as file:
            content = file.read()
            self.json_buffer = json.loads(content)
            return self.json_buffer

#! ------------------------------- USER MANAGEMENT -------------------------------------- #
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
        self.json_buffer["last_updated_chatters"] = int(time.time())
        self.save_json()
        logger.info(f"Saved file")

    def make_chatter_list(self):
        self.load_json()
        self.channel_list_to_check = []
        for (key, value) in self.json_buffer["users"].items():
            self.channel_list_to_check.append(key)

#! ---------------------------------- TWITCH API ----------------------------------------- #
    def get_chatters_in_channel(self, channel):
        endpoint = f"https://tmi.twitch.tv/group/user/{channel}/chatters"
        response = requests.get(endpoint)
        data = response.json()
        return data

    def check_stream_status(self, twitch_id: list):
        endpoint = "https://api.twitch.tv/helix/streams/" + ",".join(twitch_id)
        headers = {"Client-ID": CLIENT_ID}
        params = {"stream_type": "live"}
        response = requests.get(endpoint, headers=headers, params=params)


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