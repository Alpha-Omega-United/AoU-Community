# aou_database.py - MongoDB databsae for AoU
# Author: ItsOiK
# Date: 23/08 - 2021

from loguru import logger

from pymongo import MongoClient
import pymongo

from OAUTH.oauth import ALL_AUTH
MONGO_DB_CONNECTION_URL = ALL_AUTH["MONGO_DB_CONNECTION_URL"]


# TODO : grab list of members
# TODO : loop every 5 min:
# TODO : check each member's chatlist
# TODO : reward members in other members chatlist
# TODO :


def query_database(callbackQuery):
    response = ""
    try:
        client = MongoClient(MONGO_DB_CONNECTION_URL)
        client.connect()
        databate = client.db("aou_members_list")
        collection = databate.collection("members")
        if callbackQuery["queryType"] == "find":
            response = collection.find()
            # pass
        elif callbackQuery["queryType"] == "edit":
            response = collection.edit()
            # pass
        elif callbackQuery["queryType"] == "delete":
            response = collection.delete()
            # pass
        elif callbackQuery["queryType"] == "update_many":
            response = collection.update_many()
            # pass
    except Exception as e:
        logger.error(e)
    finally:
        # Close the connection for good meassure
        client.close()
        return response