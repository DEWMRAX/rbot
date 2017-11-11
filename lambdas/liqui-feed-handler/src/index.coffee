request = require 'request'

AWS = require 'aws-sdk'
AWS.config.update
  region: "us-east-1"

docClient = new AWS.DynamoDB.DocumentClient()

LIMIT=50

format_quote = (quote) ->
  price: quote[0].toString()
  quantity: quote[1].toString()

format_quotes = (quotes) ->
  format_quote quote for quote in quotes[0..LIMIT]

pair_name = (token, currency) ->
  "#{token.toLowerCase()}_#{currency.toLowerCase()}"

exports.handler = (event, context, callback) ->
  token = process.env.TOKEN
  currency = process.env.CURRENCY
  exchange = process.env.EXCHANGE
  pair = "#{token}_#{currency}"

  request "https://api.liqui.io/api/3/ticker/#{pair_name token, currency}?limit=#{LIMIT}", (err, response, body) ->
    if err
      return callback err

    try
      book = JSON.parse body[pair_name token,currency]

      params =
        TableName: 'orderbooks'
        Item:
          pair: pair
          exchange: exchange
          asks: book.asks
          bids: book.bids
          timestamp: Date.now()

      await docClient.put params, defer err
      if err
        console.log "Unable to insert quote", exchange, pair, ". Error JSON:", (JSON.stringify err, null, 2)
        return callback err

      console.log "Quote insert succeeded", exchange, pair, "."
      return callback null, 'OK'

    console.log "Unable to parse book", exchange, pair, ". Body:", body
    return callback body
