# aou_database.py - MongoDB databsae for AoU
# Author: ItsOiK
# Date: 23/08 - 2021

from loguru import logger
from pprint import pprint

from pymongo import MongoClient
import pymongo

from OAUTH.oauth import ALL_AUTH
MONGO_DB_CONNECTION_URL = ALL_AUTH["MONGO_DB_CONNECTION_URL"]
MONGO_DB_NAME = ALL_AUTH["MONGO_DB_NAME"]
MONGO_DB_COLLECTION = ALL_AUTH["MONGO_DB_COLLECTION"]


class AouDatabase():
    def __init__(self) -> None:
        logger.info("AoUDatabase: INIT")
        self.client = MongoClient(MONGO_DB_CONNECTION_URL)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db[MONGO_DB_COLLECTION]

    def query_database(self, callbackQuery):
        response = ""
        try:
            if callbackQuery["queryType"] == "find":
                result = self.collection.find(callbackQuery["data"])
                response = [object for object in result]
            elif callbackQuery["queryType"] == "edit":
                response = self.collection.edit(callbackQuery["data"])
            elif callbackQuery["queryType"] == "delete":
                response = self.collection.delete(callbackQuery["data"])
            elif callbackQuery["queryType"] == "update_many":
                response = self.collection.update_many(callbackQuery["data"])
        except Exception as e:
            logger.error(e)
        finally:
            # logger.error(response)
            return response
