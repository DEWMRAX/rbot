request = require 'request'

AWS = require 'aws-sdk'
AWS.config.update
  region: "us-east-1"

docClient = new AWS.DynamoDB.DocumentClient()

LIMIT=50

format_quote = (quote) ->
  [quote[0].toString(), quote[1].toString()]

format_quotes = (quotes) ->
  format_quote quote for quote in quotes[0..LIMIT]

pair_name = (token, currency) ->
  "#{token.toLowerCase()}_#{currency.toLowerCase()}"

exports.handler = (event, context, callback) ->
  token = process.env.TOKEN
  currency = process.env.CURRENCY
  exchange = process.env.EXCHANGE
  pair = "#{token}_#{currency}"

  console.log "Looking up #{pair} on #{exchange}"

  request "https://api.liqui.io/api/3/depth/#{pair_name token, currency}?limit=#{LIMIT}", (err, response, body) ->
    if err
      return callback err

    try
      body = JSON.parse body
    catch
      console.log "Unable to parse body", exchange, pair, ". Body:", body
      return callback body

    book = body[pair_name token,currency]
    # sanity and quality check on orderbook data we are trusting
    if not (book?.asks and book.asks.length > 5 and book?.bids and book.bids.length > 5)
      console.log "Insufficient book data", exchange, pair, ". Body:", (JSON.stringify body, null, 2)
      return callback body

    params =
      TableName: 'orderbooks'
      Item:
        pair: pair
        exchange: exchange
        asks: format_quotes body[pair_name token,currency].asks
        bids: format_quotes body[pair_name token,currency].bids
        timestamp: Date.now()

    await docClient.put params, defer err
    if err
      console.log "Unable to insert quote", exchange, pair, ". Error JSON:", (JSON.stringify err, null, 2)
      return callback err
    else
      console.log "Quote insert succeeded", exchange, pair, "."
      return callback null, 'OK'
