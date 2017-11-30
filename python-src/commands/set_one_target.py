from pymongo import MongoClient
import sys

MongoClient().arbot.targets.update({'symbol':sys.argv[1]}, {'$set':{'balance':sys.argv[2]}})
