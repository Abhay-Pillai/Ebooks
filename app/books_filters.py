from flask import request

def filter_books(books):
    # Get filter values from the form
    search = request.form.get('search', '').lower().strip()
    author_search = request.form.get('author', '').lower().strip()
    subject = request.form.get('subject', 'All')
    price_min = int(request.form.get('price_min', 0))
    price_max = int(request.form.get('price_max', 100000))
    sales_selected = [s.lower() for s in request.form.getlist('sales')]  # lowercase for case-insensitive match
    rating_selected = request.form.get('rating')

    filtered = []
    for book in books:
        # Normalize book fields for comparison
        book_title = book['title'].lower()
        book_author = book['author'].lower()
        book_sales = str(book['sales']).lower()  # in case sales is text like 'Medium'

        # Match title and author
        title_match = search in book_title if search else True
        author_match = author_search in book_author if author_search else True
        if not (title_match and author_match):
            continue

        # Match subject
        if subject != 'All' and book['subject'] != subject:
            continue

        # Match price
        if not (price_min <= book['price'] <= price_max):
            continue

        # Match sales (multiple checkboxes, case-insensitive)
        if sales_selected and book_sales not in sales_selected:
            continue

        # Match rating (radio button)
        if rating_selected and book['rating'] != int(rating_selected):
            continue

        # Passed all filters
        filtered.append(book)

    return filtered
