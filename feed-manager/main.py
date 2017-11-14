from logger import record_event
from collections import defaultdict
import boto3
import time

STALE_TIMEOUT = 60
INVOKE_THROTTLE = 20
REFRESH_RATE = 2

# lambda-name => timestamp of last update
last_updated = defaultdict(lambda: 0)
last_invoked = defaultdict(lambda: 0)
def process_data(response):
    for item in response['Items']:
        name = "%s-%s" % (item['exchange'], item['pair'])
        last_updated[name] = item['timestamp'] / 1000 # ms to s

with open('../markets.csv') as f:
    markets = [line.strip('\n') for line in f]

lambda_client = boto3.client('lambda')
table = boto3.resource('dynamodb').Table('orderbooks')

while True:
    response = table.scan()
    process_data(response)
    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        process_data(response)

    for market in markets:
        name = market.replace(',', '-')
        if time.time() > last_updated[name] + STALE_TIMEOUT and \
           time.time() > last_invoked[name] + INVOKE_THROTTLE:
            last_invoked[name] = time.time()
            record_event("INVOKING,%s" % name)
            lambda_client.invoke(InvocationType='Event', FunctionName=name)

    record_event("SLEEPING,%s" % REFRESH_RATE)
    time.sleep(REFRESH_RATE)
