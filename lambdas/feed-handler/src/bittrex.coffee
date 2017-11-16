request = require 'request'

LIMIT=50
MIN_BOOK_DATA = 5

format_quote = (quote) ->
  [quote['Rate'], quote['Quantity']]

format_quotes = (quotes) ->
  format_quote quote for quote in quotes[0..LIMIT]

pair_name = (token, currency) ->
  "#{currency.toLowerCase()}-#{token.toLowerCase()}"

sanity_check = (book) ->
  (book?.buy and book.buy.length > MIN_BOOK_DATA and book?.sell and book.sell.length > MIN_BOOK_DATA)

exports.get_book = (token, currency, error_cb, success_cb) ->
  request "https://bittrex.com/api/v1.1/public/getorderbook?type=both&market=#{pair_name token, currency}", (err, response, body) ->
    if err
      return error_cb err

    try
      body = JSON.parse body
      book = body.result
    catch
      console.log 'Unable to parse body:', body
      return error_cb body

    if not sanity_check book
      console.log 'Insufficient book data:', (JSON.stringify book, null, 2)
      return error_cb book

    return success_cb
      asks: format_quotes book.sell
      bids: format_quotes book.buy
