from pymongo import MongoClient
import sys

print "Old balance: %s" % MongoClient().arbot.targets.find_one({'symbol':sys.argv[1]})['balance']

MongoClient().arbot.targets.update({'symbol':sys.argv[1]}, {'$set':{'balance':sys.argv[2]}})
