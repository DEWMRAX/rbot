request = require 'request'

LIMIT=15
MIN_BOOK_DATA = 5

format_quote = (quote) ->
  [quote.price, quote.amount]

format_quotes = (quotes) ->
  format_quote quote for quote in quotes[0..LIMIT]

symbol_to_gemini = (symbol) ->
  symbol

pair_name = (token, currency) ->
  "#{symbol_to_gemini token.toLowerCase()}#{symbol_to_gemini currency.toLowerCase()}"

sanity_check = (book) ->
  (book?.asks and book.asks.length > MIN_BOOK_DATA and book?.bids and book.bids.length > MIN_BOOK_DATA)

exports.get_book = (token, currency, error_cb, success_cb) ->
  request_details =
    url: "https://api.gemini.com/v1/book/#{pair_name token, currency}"
    headers:
      'User-Agent': 'nodejs:request'

  request request_details, (err, response, body) ->
    if err
      return error_cb err

    try
      body = JSON.parse body
    catch
      console.log 'Unable to parse body:', body
      return error_cb body

    book = body
    if not sanity_check book
      console.log 'Insufficient book data:', (JSON.stringify book, null, 2)
      return error_cb body

    return success_cb
      asks: format_quotes book.asks
      bids: format_quotes book.bids
