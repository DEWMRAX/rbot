request = require 'request'

LIMIT=15
MIN_BOOK_DATA = 5

format_quote = (quote) ->
  [quote[0].toString(), quote[1].toString()]

format_quotes = (quotes) ->
  format_quote quote for quote in quotes[0..LIMIT]

symbol_to_kraken = (symbol) ->
  switch symbol
    when 'BTC' then 'XBT'
    when 'BCC' then 'BCH'
    else symbol

pair_name = (token, currency) ->
  "#{symbol_to_kraken token}#{symbol_to_kraken currency}"

sanity_check = (book) ->
  (book?.asks and book.asks.length > MIN_BOOK_DATA and book?.bids and book.bids.length > MIN_BOOK_DATA)

exports.get_book = (token, currency, error_cb, success_cb) ->
  request "https://api.kraken.com/0/public/Depth?count=#{LIMIT}&pair=#{pair_name token, currency}", (err, response, body) ->
    if err
      return error_cb err

    try
      body = JSON.parse body
      for pair of body.result # there's only ever one entry
        book = body.result[pair]
    catch
      console.log 'Unable to parse body:', body
      return error_cb body

    if not sanity_check book
      console.log 'Insufficient book data:', (JSON.stringify book, null, 2)
      return error_cb body

    return success_cb
      asks: format_quotes book.asks
      bids: format_quotes book.bids
