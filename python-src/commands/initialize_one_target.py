from pymongo import MongoClient
import sys

MongoClient().arbot.targets.insert({'symbol':sys.argv[1], 'balance':sys.argv[2]})
