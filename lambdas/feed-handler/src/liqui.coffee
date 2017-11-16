request = require 'request'

LIMIT=50
MIN_BOOK_DATA = 5

format_quote = (quote) ->
  [quote[0].toString(), quote[1].toString()]

format_quotes = (quotes) ->
  format_quote quote for quote in quotes[0..LIMIT]

pair_name = (token, currency) ->
  "#{token.toLowerCase()}_#{currency.toLowerCase()}"

sanity_check = (book) ->
  (book?.asks and book.asks.length > MIN_BOOK_DATA and book?.bids and book.bids.length > MIN_BOOK_DATA)

exports.get_book = (token, currency, error_cb, success_cb) ->
  request "https://api.liqui.io/api/3/depth/#{pair_name token, currency}?limit=#{LIMIT}", (err, response, body) ->
    if err
      return error_cb err

    try
      body = JSON.parse body
    catch
      console.log 'Unable to parse body:', body
      return error_cb body

    book = body[pair_name token,currency]
    if not sanity_check book
      console.log 'Insufficient book data:', (JSON.stringify book, null, 2)
      return error_cb body

    return success_cb
      asks: format_quotes book.asks
      bids: format_quotes book.bids
