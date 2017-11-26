from pymongo import MongoClient
import sys

MongoClient().arbot.transfers.update_many({'symbol':sys.argv[1]}, {'$set':{'active':False}})
