from pymongo import MongoClient

MongoClient().arbot.targets.update({'symbol':sys.argv[1]}, {'$set':{'balance':sys.argv[2]}})
