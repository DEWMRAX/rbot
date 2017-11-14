import boto3

with open('../markets.csv') as f:
    markets = [line.strip('\n') for line in f]

l=boto3.client('lambda')

for market in markets:
    (exchange, token, currency) = market.split(',')
    l.invoke(InvocationType='Event', FunctionName="%s-%s-%s" % (exchange, token, currency))

# db=boto3.resource('dynamodb')
#
# books = db.Table('orderbooks').scan()
#
# for book in books['Items']:
#     print book['pair']
#     print book['exchange']
#     print book['timestamp']
#     print
