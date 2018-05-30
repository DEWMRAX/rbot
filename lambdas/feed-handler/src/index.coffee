liqui = require './liqui'
binance = require './binance'
bittrex = require './bittrex'
poloniex = require './poloniex'
kraken = require './kraken'
gdax = require './gdax'
itbit = require './itbit'
bitflyer = require './bitflyer'

AWS = require 'aws-sdk'
AWS.config.update
  region: "us-east-1"

docClient = new AWS.DynamoDB.DocumentClient()

exports.handler = (event, context, callback) ->
  token = event.token
  currency = event.currency
  exchange = event.exchange
  pair = "#{token}-#{currency}"

  console.log "Looking up #{pair} on #{exchange}"

  feed_handler = switch exchange
    when 'LIQUI' then liqui
    when 'BINANCE' then binance
    when 'BITTREX' then bittrex
    when 'POLO' then poloniex
    when 'KRAKEN' then kraken
    when 'GDAX' then gdax
    when 'ITBIT' then itbit
    when 'BITFLYER' then bitflyer

  await feed_handler.get_book token, currency, callback, defer book

  params =
    TableName: 'orderbooks-test'
    Item:
      pair: pair
      exchange: exchange
      asks: book.asks
      bids: book.bids
      timestamp: Date.now()

  await docClient.put params, defer err
  if err
    console.log 'Unable to insert quote', exchange, pair, '. Error JSON:', (JSON.stringify err, null, 2)
    return callback err
  else
    console.log 'Quote insert succeeded', exchange, pair, '.'
    return callback null, 'OK'
