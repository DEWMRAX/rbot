from pymongo import MongoClient

MongoClient().arbot.prices.insert({'symbol':sys.argv[1], 'price':float(sys.argv[2])})
