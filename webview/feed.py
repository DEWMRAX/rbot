from flask import Flask
import boto3

app = Flask(__name__)

table = boto3.resource('dynamodb', region_name='us-east-1').Table('orderbooks')

@app.route('/<pair>')
def xxhello_world(pair):
    fil = boto3.dynamodb.conditions.Key('pair').eq(pair)
    return str(table.scan(FilterExpression=fil))

if __name__ == '__main__':
  app.run()
