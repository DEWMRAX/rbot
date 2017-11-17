from flask import Flask
import boto3

app = Flask(__name__)

table = boto3.resource('dynamodb', region_name='us-east-1').Table('orderbooks')

def book_to_string(item, depth):
    ret += "%s %s<br>" % (item['exchange'], item['pair'])

    for i in xrange(depth, 0, -1):
        if i-1 < len(item['asks']):
            quote = item['asks'][i-1]
            ret += "%0.8f x %0.8f<br>" % (quote[0], quote[1])

    ret += "==============================<br>"

    for i in xrange(0, depth):
        if i < len(item['bids']):
            quote = item['bids'][i]
            ret += "%0.8f x %0.8f<br>" % (quote[0], quote[1])

    return ret

@app.route('/<pair>')
def show_books(pair):
    fil = boto3.dynamodb.conditions.Key('pair').eq(pair)

    return "<br><br>".join(map(lambda item:book_to_string(item, 5), table.scan(FilterExpression=fil)['Items']))

if __name__ == '__main__':
  app.run()
