from flask import Flask, render_template, request, session
from books_filters import filter_books
import mysql.connector

app = Flask(__name__)
app.secret_key = "your_secret_key"   # Needed for session


# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # your MySQL username
        password="Abh@y2005",  # your MySQL password
        database="bookstore"      # your DB name
    )

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/book/<category>/<book_id>")
def book_details(category, book_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if category == "computer":
        cursor.execute("SELECT * FROM computer_books WHERE book_id=%s", (book_id,))
    elif category == "electronics":
        cursor.execute("SELECT * FROM electronics_books WHERE book_id=%s", (book_id,))
    elif category == "mechanical":
        cursor.execute("SELECT * FROM mechanical_books WHERE book_id=%s", (book_id,))
    elif category == "it":
        cursor.execute("SELECT * FROM it_books WHERE book_id=%s", (book_id,))
    else:
        return "Invalid category", 404

    book = cursor.fetchone()
    cursor.close()
    conn.close()

    if not book:
        return "Book not found", 404

    return render_template("book_details.html", book=book)



@app.route("/computer", methods=['GET', 'POST'])
def computer():
    # Step 1: fetch all books from database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM computer_books")
    books = cursor.fetchall()
    cursor.close()
    conn.close()

    if "filters" not in session:
        session["filters"] = {}

    # Step 3: if form is submitted, update filters in session
    if request.method == 'POST':
        session["filters"] = request.form.to_dict(flat=False)
        filtered_books = filter_books(books)
    else:
        filtered_books = filter_books(books) if session.get("filters") else books

    # Step 4: pass filters to template
    return render_template("computer.html", books=filtered_books, filters=session["filters"])


@app.route("/electronics", methods=['GET', 'POST'])
def electronics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM electronics_books")
    books = cursor.fetchall()
    cursor.close()
    conn.close()

    if "filters" not in session:
        session["filters"] = {}

    # Step 3: if form is submitted, update filters in session
    if request.method == 'POST':
        session["filters"] = request.form.to_dict(flat=False)
        filtered_books = filter_books(books)
    else:
        filtered_books = filter_books(books) if session.get("filters") else books

    # Step 4: pass filters to template
    return render_template("electronics.html", books=filtered_books, filters=session["filters"])

@app.route("/mechanical", methods=['GET', 'POST'])
def mechanical():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mechanical_books")
    books = cursor.fetchall()
    cursor.close()
    conn.close()

    if "filters" not in session:
        session["filters"] = {}

    # Step 3: if form is submitted, update filters in session
    if request.method == 'POST':
        session["filters"] = request.form.to_dict(flat=False)
        filtered_books = filter_books(books)
    else:
        filtered_books = filter_books(books) if session.get("filters") else books

    # Step 4: pass filters to template
    return render_template("mechanical.html", books=filtered_books, filters=session["filters"])

@app.route("/it", methods=['GET', 'POST'])
def it():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM it_books")
    books = cursor.fetchall()
    cursor.close()
    conn.close()

    if "filters" not in session:
        session["filters"] = {}

    # Step 3: if form is submitted, update filters in session
    if request.method == 'POST':
        session["filters"] = request.form.to_dict(flat=False)
        filtered_books = filter_books(books)
    else:
        filtered_books = filter_books(books) if session.get("filters") else books

    return render_template("it.html", books=filtered_books, filters=session["filters"])

 

@app.route("/telecommunication")
def telecommunication():
    return render_template("telecommunication.html")

@app.route("/civil")
def civil():
    return render_template("civil.html")


@app.route("/about")
def about():
    return render_template("aboutus.html")

@app.route("/faqs")
def faqs():
    return render_template("faqs.html")

@app.route("/account")
def account():
    return render_template("account.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")


if __name__ == "__main__":
    app.run(debug=True)
