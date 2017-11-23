from pymongo import MongoClient

MongoClient().arbot.transfers.update_many({'symbol':sys.argv[1]}, {'$set':{'active':False}})
