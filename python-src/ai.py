from decimal import Decimal

MAX_AGE = Decimal(80)

def effective_bid(book):
    return book.bids[0].price * (Decimal(1) - book.taker_fee)

def best_bidder(books):
    eligible_books = filter(lambda book:book.age < MAX_AGE, books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.bids) == 0:
            best = book
        elif len(book.bids) > 0 and effective_bid(book) > effective_bid(best):
            best = book

    return best

def effective_ask(book):
    return book.asks[0].price * (Decimal(1) + book.taker_fee)

def best_seller(books):
    eligible_books = filter(lambda book:book.age < MAX_AGE, books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.asks) == 0:
            best = book
        elif len(book.asks) > 0 and effective_ask(book) < effective_ask(best):
            best = book

    return best

def near_crossed(books):
    bidder = best_bidder(books)
    seller = best_seller(books)

    if bidder and seller:
        # Fudge the ask down so we consider nearly actionable crosses ACTIVE for refresh
        if effective_ask(seller) * Decimal(0.999) <= effective_bid(bidder):
            return True

    return False
