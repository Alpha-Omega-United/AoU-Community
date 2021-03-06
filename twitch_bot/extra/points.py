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


from aou_database.aou_database import AouDatabase
from OAUTH.oauth import ALL_AUTH


CLIENT_ID = ALL_AUTH["CLIENT_ID"]
APP_ACCESS_TOKEN = ALL_AUTH["APP_ACCESS_TOKEN"]
CLIENT_ID = ALL_AUTH["CLIENT_ID"]
CLIENT_SECRET = ALL_AUTH["CLIENT_SECRET"]
APP_ACCESS_TOKEN_ENDPOINT = ALL_AUTH["APP_ACCESS_TOKEN_ENDPOINT"]


#! CONSTS:
POINT_AMOUNT_LURK = 5  # ! every x minutes
# POINT_AMOUNT_HOST = 25
# POINT_AMOUNT_RAID = 50
UPDATE_INTERVAL = POINT_AMOUNT_LURK * 60
MAX_CHANNEL_REWARDS = 2

UPDATED_USERS = {"default": None}


class PointSystem:
    def __init__(self, aouDb) -> None:
        self.json_buffer = self.load_json()
        self.last_updated_chatters = int(
            self.json_buffer["last_updated_chatters"])
        self.number_of_registered_members = int(
            self.json_buffer["number_of_registered_members"]
        )
        logger.warning(
            f"there are {self.number_of_registered_members} registered members"
        )
        self.aouDb = aouDb
        self.channel_list_to_check = self.populate_channel_list()
        self.currently_live = []
        self.point_system_thread = Thread(target=self.run, daemon=True)
        self.point_system_thread.start()
        self.users_to_give_points = {}
        self.ignorelist = ["alphaomegaunited"]
        self.not_supported_sites = ["youtube", "trovo"]
        # self.get_app_access_token()

    def get_app_access_token(self):
        params = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        response = requests.post(APP_ACCESS_TOKEN_ENDPOINT, params=params)
        # logger.debug(f'response: {response.json()} ')

    def load_json(self) -> dict:
        """handles loading last updated timestamp from cache.json"""
        with open("twitch_bot/extra/cache/cache.json") as file:
            content = json.loads(file.read())
            return content

    def save_json(self, reset_last_updated=False) -> None:
        """handles saving last updated timestamp from cache.json"""
        data_to_save = {
            "last_updated_chatters": self.last_updated_chatters,
            "number_of_registered_members": len(self.channel_list_to_check),
        }
        if reset_last_updated:
            data_to_save["last_updated_chatters"] = 0
        with open("twitch_bot/extra/cache/cache.json", "w") as file:
            json.dump(data_to_save, file)

    def populate_channel_list(self) -> list:
        """Grabs all users from database and returns a list of only twitch_name's"""
        response = self.aouDb.collection.find({})
        result = [user["twitch_name"] for user in response]
        return result

    def run(self) -> None:
        """handles timing of updateinterval and last updated timer"""
        logger.info("STARTING: Leaderboard Point System")
        time_to_next_update = abs(
            int(time.time()) - self.last_updated_chatters - UPDATE_INTERVAL
        )
        logger.warning(
            f"update in: {math.floor(time_to_next_update / 60)}:{time_to_next_update % 60}"
        )
        while True:
            if abs(int(time.time()) - self.last_updated_chatters) >= UPDATE_INTERVAL:
                logger.info("Updating Point System")
                self.last_updated_chatters = int(time.time())
                self.update()
                time.sleep(UPDATE_INTERVAL)

    def update(self) -> None:
        """Triggers everything related to getting users and updating points."""
        self.channel_list_to_check = self.populate_channel_list()
        if len(self.channel_list_to_check) != self.number_of_registered_members:
            self.save_json(True)
            self.restart_bot()
            #!REstart
            pass
        live_data = self.check_live()
        if "error" in live_data[0].keys():
            logger.error("SOMETHING WENT WRONG RESTARTING")
            self.restart_bot()
        self.currently_live = self.parse_live_users(live_data)
        self.set_as_live_in_db(self.currently_live)
        self.users_to_give_points = self.update_chatter(self.currently_live)
        self.update_points(self.users_to_give_points)
        self.save_json()

    def restart_bot(self):
        logger.warning(
            f"registered members: {self.number_of_registered_members} ")
        logger.warning(f"channels joined: {len(self.channel_list_to_check)}")
        logger.warning("Restarting bot in 30sec to update channel-list")
        from time import sleep

        sleep(30)
        AOU_API = "http://192.168.31.54:8888/api"
        endpoint = f"{AOU_API}/bot_get/restart_bot"
        logger.warning("RESTARTING NOW")
        response = requests.get(endpoint, headers={"password": "123"})
        logger.debug(response.text)

    def check_live(self) -> list:
        """check twitch if users in 'channel_list_to_check' are live."""
        endpoint = "https://api.twitch.tv/helix/streams"
        headers = {"client-id": CLIENT_ID,
                   "Authorization": f"Bearer {APP_ACCESS_TOKEN}"}
        user_query = "&user_login=" + \
            "&user_login=".join(self.channel_list_to_check)
        result = requests.get(endpoint + "?" + user_query, headers=headers)
        result_json = result.json()
        if "error" in result_json.keys():
            logger.error(f"result_json: {result_json} ")
            return [{"error": True}]
        return result_json["data"]

    def set_as_live_in_db(self, user_list: list) -> None:
        """takes a list of users, sets EVERY user to stream = None,
        then sets currently live users stream data"""
        #! this will fuck with youtube and other streamersites
        #! currently supported sites: Twitch.tv
        result = self.aouDb.collection.update_many(
            {"stream.live_where": "twitch"},
            # {},
            {"$set": {"stream": None}},
        )
        logger.warning(f"live now: {user_list}")
        if len(user_list) == 0:
            user_list = 0
        else:
            for user in user_list:
                logger.error(user)
                result = self.aouDb.collection.update_one(
                    {"twitch_name": user},
                    {
                        "$set": {
                            "stream": {
                                "live_url": f"https://twitch.tv/{user}",
                                "live_where": "twitch",
                            }
                        }
                    },
                )
                if int(result.modified_count) == 1:
                    logger.debug(f"set as live: {user}")
                else:
                    logger.debug("no user changed")
                    logger.warning(f"something may have gone wrong")

    def parse_live_users(self, data: list) -> list:
        """receives data from twitch and parses data we want"""
        temp_list = []
        for user_object in data:
            if user_object["user_login"] in self.channel_list_to_check:
                temp_list.append(user_object["user_login"])
        return temp_list

    def update_chatter(self, live_users: list) -> dict:
        """update chatter list of live members"""
        temp_dict = {}
        for user in live_users:
            chatter_users = self.get_chatters_in_channel(user)
            for user in chatter_users:
                if user in temp_dict and user != "alphaomegaunited":
                    if temp_dict[user]["count"] < MAX_CHANNEL_REWARDS:
                        temp_dict[user]["count"] += 1
                    else:
                        continue
                else:
                    temp_dict[user] = {"count": 1}
        return temp_dict

    def get_chatters_in_channel(self, channel: str) -> list:
        endpoint = f"https://tmi.twitch.tv/group/user/{channel}/chatters"
        response = requests.get(endpoint)
        data = response.json()
        return self.parse_chatter_data(data["chatters"])

    def parse_chatter_data(self, data: dict) -> list:
        """gets lists of chatters from a channel and returns one list with all chatters"""
        temp_list = []
        for user in data["vips"]:
            temp_list.append(user)
        for user in data["moderators"]:
            temp_list.append(user)
        for user in data["viewers"]:
            temp_list.append(user)
        return temp_list

    def update_points(self, users_to_update: dict) -> None:
        """updates points on chatters in channel"""
        cursor = self.aouDb.collection.find()
        for doc in enumerate(cursor):
            user_to_update = doc[1]["twitch_name"].lower()
            if user_to_update in users_to_update:
                points_to_update = (
                    users_to_update[user_to_update]["count"] *
                    POINT_AMOUNT_LURK
                )
                result = self.aouDb.collection.update_one(
                    {"twitch_name": user_to_update},
                    {"$inc": {"points": points_to_update}},
                )
                if result.matched_count == 1:
                    logger.debug(
                        f"{user_to_update} was given {points_to_update}points")
                else:
                    logger.warning(
                        f"something might have gone wrong when giving {points_to_update}points to {user_to_update}"
                    )
