from flask import Flask, request, redirect, url_for, flash, jsonify, render_template_string, render_template, session
import mysql.connector
import bcrypt
import re
from books_filters import filter_books
from datetime import datetime, timedelta
import requests
import razorpay
import os, hmac, hashlib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "your-secret-key"
# Initialize Razorpay client using keys from .env
razorpay_client = razorpay.Client(auth=(
    os.getenv("RAZOR_KEY_ID"),
    os.getenv("RAZOR_KEY_SECRET")
))

# MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Abh@y2005",
        database="bookstore"
    )


@app.route("/")
def animation():
    return render_template("animation.html")

# Embedded HTML Template with local background image and updated styles
template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>eBooks Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body, html {
      height: 100%;
      margin: 0;
      font-family: 'Segoe UI', sans-serif;
      overflow: hidden;
    }

    .bg-image {
      background: url('/static/background.jpg') no-repeat center center/cover;
      position: fixed;
      top: 0;
      left: 0;
      height: 100vh;
      width: 100vw;
      filter: brightness(0.6);
      z-index: -1;
    }

    .login-box {
      background: rgba(255, 255, 255, 0.6); /* More visible white transparent */
      border: 1px solid rgba(255, 255, 255, 0.5);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: #000; /* Dark text for readability */
      max-width: 400px;
      width: 100%;
      border-radius: 15px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .form-control {
      background-color: rgba(255, 255, 255, 0.85);
      border: none;
      color: #000;
    }

    .form-control::placeholder {
      color: #666;
    }

    .form-control:focus {
      background-color: rgba(255, 255, 255, 0.95);
      border: none;
      box-shadow: none;
      color: #000;
    }

    .alert {
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
    }

    @media (max-width: 480px) {
      .login-box {
        padding: 20px !important;
      }
    }
  </style>
</head>
<body>
  <div class="bg-image"></div>

  <div class="container d-flex justify-content-center align-items-center min-vh-100">
    <div class="login-box p-4 shadow-lg">
      <h2 class="text-center mb-3">Welcome Back</h2>
      <p class="text-center text-muted mb-4">Sign in to your eBooks account</p>

      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, message in messages %}
            <div class="alert alert-{{ category }} text-center" role="alert">
              {{ message }}
            </div>
          {% endfor %}
        {% endif %}
      {% endwith %}

      <form method="POST">
        <div class="mb-3">
          <label for="email" class="form-label">Email address</label>
          <input type="email" class="form-control" id="email" name="email" placeholder="you@example.com" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input type="password" class="form-control" id="password" name="password" placeholder="••••••••" required>
        </div>
        <div class="d-flex justify-content-between mb-3">
          <a href="#" class="text-primary text-decoration-none">Forgot password?</a>
        </div>
        <button type="submit" class="btn btn-primary w-100">Sign In</button>
        <div class="text-center mt-3">
           Don't have an account? <a href="{{ url_for('register') }}" class="text-primary">Register</a>
        </div>
      </form>
    </div>
  </div>
</body>
</html>
"""
# ------------------ SIGNIN ------------------
@app.route("/signin", methods=["POST", "GET"])
def signin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM accounts WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and bcrypt.checkpw(password.encode("utf-8"), result[0].encode("utf-8")):
            session.clear()  # ✅ clear previous session
            session["user_email"] = email
            return redirect(url_for("home"))
        else:
            return "Invalid credentials", 401
    return redirect(url_for("login"))

# ------------------ REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data
        full_name = request.form['name'].strip()
        gender = request.form['gender']
        email = request.form['email'].strip()
        dob = request.form['dob']
        phone = request.form['phone'].strip()
        password = request.form['password']
        city = request.form.get('city', '').strip()
        country = request.form.get('country', '').strip()
        address = request.form.get('address', '').strip()

        # Server-side validation
        email_regex = r'^[^\s@]+@[^\s@]+\.com$'
        phone_regex = r'^[0-9]{10}$'
        password_regex = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{10,}$'

        if not re.match(email_regex, email):
            flash("Invalid email format", "danger")
            return render_template("register.html")

        if not re.match(phone_regex, phone):
            flash("Phone number must be 10 digits", "danger")
            return render_template("register.html")

        if not re.match(password_regex, password):
            flash("Password must be at least 10 characters, include letters, numbers, and 1 special character", "danger")
            return render_template("register.html")

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert into MySQL
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounts (full_name, gender, email, dob, phone, password_hash, city, country, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (full_name, gender, email, dob, phone, hashed_password, city, country, address))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Account registered successfully!", "success")
            return redirect(url_for("login"))

        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                flash("Email or phone already registered", "danger")
            else:
                flash(f"Database error: {err}", "danger")
            return render_template("register.html")

    # GET request
    return render_template("register.html")

# ------------------ LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM accounts WHERE email=%s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            session["user_email"] = email
            return redirect(url_for("home"))

        else:
            flash("Invalid email or password", "danger")
            return render_template_string(template)

    # GET request → just render login page
    return render_template_string(template)

@app.route("/home")
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
    elif category == "aerospace":
        cursor.execute("SELECT * FROM aerospace_books WHERE book_id=%s", (book_id,))
    elif category == "civil":
        cursor.execute("SELECT * FROM civil_books WHERE book_id=%s", (book_id,))
    elif category == "automobile":
        cursor.execute("SELECT * FROM automobile_books WHERE book_id=%s", (book_id,))
    elif category == "chemical":
        cursor.execute("SELECT * FROM chemical_books WHERE book_id=%s", (book_id,))
    elif category == "biomedical":
        cursor.execute("SELECT * FROM biomedical_books WHERE book_id=%s", (book_id,))
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


@app.route("/aerospace", methods=['GET', 'POST'])
def aerospace():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM aerospace_books")
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

    return render_template("aerospace.html", books=filtered_books, filters=session["filters"])

@app.route("/civil", methods=['GET', 'POST'])
def civil():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM civil_books")
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

    return render_template("civil.html", books=filtered_books, filters=session["filters"])

@app.route("/automobile", methods=['GET', 'POST'])
def automobile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM automobile_books")
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

    return render_template("automobile.html", books=filtered_books, filters=session["filters"])

@app.route("/chemical", methods=['GET', 'POST'])
def chemical():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chemical_books")
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

    return render_template("chemical.html", books=filtered_books, filters=session["filters"])

@app.route("/biomedical", methods=['GET', 'POST'])
def biomedical():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM biomedical_books")
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

    return render_template("biomedical.html", books=filtered_books, filters=session["filters"])

# ------------------ SEARCH SUGGESTIONS ------------------
@app.route("/search_suggestions")
def search_suggestions():
    query = request.args.get("query", "").strip().lower()
    mode = request.args.get("mode", "ajax")
    results = []
    suggestions = []

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # ✅ ensures results are dict-like

    all_tables = [
        "computer_books", "electronics_books", "mechanical_books",
        "it_books", "civil_books", "aerospace_books",
        "chemical_books", "automobile_books", "biomedical_books"
    ]

    for table in all_tables:
        try:
            # ✅ Try selecting consistent columns
            cursor.execute(f"""
                SELECT 
                    title,
                    author,
                    subject,
                    price,
                    sales,
                    rating,
                    edition,
                    image_url
                FROM {table}
                WHERE LOWER(title) LIKE %s
                LIMIT 5
            """, (f"%{query}%",))
            
            rows = cursor.fetchall()
            for row in rows:
                results.append(row)
                suggestions.append(row["title"])
                
        except Exception as e:
            print(f"⚠️ Error fetching from {table}: {e}")

    cursor.close()
    conn.close()

    # ✅ If user clicked suggestion or pressed Enter → render HTML
    if mode == "page":
        return render_template("search_results.html", results=results, query=query)

    # ✅ Else → return JSON suggestions
    return jsonify(suggestions)

@app.route("/about")
def about():
    return render_template("aboutus.html")

@app.route("/faqs")
def faqs():
    return render_template("faqs.html")

# ------------------ FEEDBACK ------------------
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user_email" not in session:
        flash("Please log in first to give feedback.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        email = session["user_email"]
        rating = request.form.get("rating")  # ✅ safe now
        content = request.form.get("content")
        ui = request.form.get("ui")
        suggestion = request.form.get("suggestion")

        # ✅ Check missing fields
        if not rating:
            flash("Please select a star rating before submitting.", "danger")
            return redirect(url_for("feedback"))

        # 🟢 Process or store feedback
        print("Feedback received:", name, email, rating, content, ui, suggestion)
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("home"))

    return render_template("feedback.html", session_email=session["user_email"])

# ------------------ ACCOUNT MAIN PAGE ------------------
@app.route("/account")
def account():
    if "user_email" not in session:
        return redirect(url_for("login"))
    return render_template("account.html", active_tab="profile")

# ------------------ PROFILE ------------------
@app.route("/profile")
def profile():
    if "user_email" not in session:
        return redirect(url_for("login"))
    email = session["user_email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT full_name, gender, email, dob, phone, city, country, address 
        FROM accounts 
        WHERE email=%s
    """, (email,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("account.html", active_tab="profile", row=row)

# ------------------ UPDATE PROFILE ------------------
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]

    full_name = request.form.get("full_name")
    gender = request.form.get("gender")
    dob = request.form.get("dob")
    phone = request.form.get("phone")
    city = request.form.get("city")
    country = request.form.get("country")
    address = request.form.get("address")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE accounts
        SET full_name=%s, gender=%s, dob=%s, phone=%s, city=%s, country=%s, address=%s
        WHERE email=%s
    """, (full_name, gender, dob, phone, city, country, address, email))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile", active_tab="profile"))

# ------------------ DASHBOARD SECTION ------------------
@app.route("/dashboard")
def dashboard():
    return render_template("account.html", active_tab="dashboard")

@app.route("/dashboard-data")
def dashboard_data():
    if "user_email" not in session:
        return jsonify({"error": "not_logged_in"}), 401

    email = session["user_email"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # ✅ Total Orders
        cursor.execute("SELECT COUNT(*) AS total_orders FROM orders WHERE user_email = %s", (email,))
        total_orders = (cursor.fetchone() or {}).get("total_orders", 0)

        # ✅ Total Cart Items
        cursor.execute("SELECT COUNT(*) AS total_cart_items FROM cart WHERE user_email = %s", (email,))
        total_cart_items = (cursor.fetchone() or {}).get("total_cart_items", 0)

        # ✅ Total Wishlist Items
        cursor.execute("SELECT COUNT(*) AS total_wishlist_items FROM wishlist WHERE user_email = %s", (email,))
        total_wishlist_items = (cursor.fetchone() or {}).get("total_wishlist_items", 0)

        # ✅ Cash Orders
        cursor.execute("SELECT COUNT(*) AS total_cod_orders FROM orders WHERE user_email = %s AND payment_mode = 'Cash'", (email,))
        total_cod_orders = (cursor.fetchone() or {}).get("total_cod_orders", 0)

        # ✅ Online Orders
        cursor.execute("SELECT COUNT(*) AS total_online_orders FROM orders WHERE user_email = %s AND payment_mode = 'Online'", (email,))
        total_online_orders = (cursor.fetchone() or {}).get("total_online_orders", 0)

        # ✅ Fetch all book_ids for category calculation
        cursor.execute("SELECT book_id FROM orders WHERE user_email = %s", (email,))
        orders = cursor.fetchall()

        # ✅ Category mapping logic
        category_counts = {
            "computer": 0,
            "electronics": 0,
            "mechanical": 0,
            "civil": 0,
            "chemical": 0,
            "biomedical": 0,
            "it": 0,
            "aerospace": 0,
            "automobile": 0
        }

        for row in orders:
            book_id = (row["book_id"] or "").upper().strip()

            if book_id.startswith("IBCS") or book_id.startswith("CS"):
                category_counts["computer"] += 1
            elif book_id.startswith("IBEC") or book_id.startswith("EC"):
                category_counts["electronics"] += 1
            elif book_id.startswith("IBME") or book_id.startswith("ME"):
                category_counts["mechanical"] += 1
            elif book_id.startswith("IBCL") or book_id.startswith("CL"):
                category_counts["civil"] += 1
            elif book_id.startswith("IBCH") or book_id.startswith("CH"):
                category_counts["chemical"] += 1
            elif book_id.startswith("IBBM") or book_id.startswith("IBBO") or book_id.startswith("BM"):
                category_counts["biomedical"] += 1
            elif book_id.startswith("IBIT") or book_id.startswith("IT"):
                category_counts["it"] += 1
            elif book_id.startswith("IBAE") or book_id.startswith("IBAS") or book_id.startswith("AE") or book_id.startswith("AS"):
                category_counts["aerospace"] += 1
            elif book_id.startswith("IBAU") or book_id.startswith("IBAT") or book_id.startswith("AU") or book_id.startswith("AT"):
                category_counts["automobile"] += 1

        # ✅ Filter only categories that have at least 1 book
        categories = [cat.capitalize() for cat, count in category_counts.items() if count > 0]
        totals = [count for count in category_counts.values() if count > 0]

        cursor.close()
        conn.close()

        # ✅ Return clean JSON data
        return jsonify({
            "total_orders": total_orders,
            "total_cart_items": total_cart_items,
            "total_wishlist_items": total_wishlist_items,
            "total_cod_orders": total_cod_orders,
            "total_online_orders": total_online_orders,
            "categories": categories,
            "totals": totals
        })

    except Exception as e:
        print("Dashboard data error:", e)
        return jsonify({"error": str(e)}), 500

# ------------------ WISHLIST ------------------
@app.route("/wishlist")
def wishlist():
    if "user_email" not in session:
        return redirect("/login")

    email = session["user_email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Fetch  all books in the logged-in user's wishlist
    cursor.execute("SELECT * FROM wishlist WHERE user_email = %s", (email,))
    wishlist_items = cursor.fetchall()

    cursor.close()
    conn.close()

    # ✅ Render account.html with wishlist tab active
    return render_template("account.html", active_tab="wishlist", wishlist_items=wishlist_items)

# ------------------ ADD TO WISHLIST ------------------
@app.route("/add_to_wishlist", methods=["POST"])
def add_to_wishlist():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Please log in first"})

    data = request.get_json() or {}
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({"success": False, "message": "Missing book_id"})

    email = session["user_email"]

    # ✅ Detect category from book_id prefix/substring
    if "CS" in book_id:
        category = "computer"
        table_name = "computer_books"
    elif "EC" in book_id:
        category = "electronics"
        table_name = "electronics_books"
    elif "ME" in book_id:
        category = "mechanical"
        table_name = "mechanical_books"
    elif "CL" in book_id:
        category = "civil"
        table_name = "civil_books"
    elif "CH" in book_id:
        category = "chemical"
        table_name = "chemical_books"
    elif "BO" in book_id:
        category = "biomedical"
        table_name = "biomedical_books"
    elif "IT" in book_id:
        category = "it"
        table_name = "it_books"
    elif "AS" in book_id:
        category = "aerospace"
        table_name = "aerospace_books"
    elif "AT" in book_id:
        category = "automobile"
        table_name = "automobile_books"
    else:
        return jsonify({"success": False, "message": "Unknown category for this book_id"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # ✅ fetch book details from detected table
        query = f"""
            SELECT book_id, image_url, title, author, subject, price
            FROM {table_name}
            WHERE book_id = %s
        """
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()

        if not book:
            return jsonify({"success": False, "message": "Book not found"})

        # ✅ check for duplicates in wishlist
        cursor.execute(
            "SELECT * FROM wishlist WHERE book_id = %s AND user_email = %s",
            (book_id, email)
        )
        existing = cursor.fetchone()
        if existing:
            return jsonify({"success": True, "message": f"{book['title']} already in wishlist!"})

        # ✅ insert into wishlist (correct column mapping)
        cursor.execute("""
            INSERT INTO wishlist 
            (book_id, image_url, book_title, author, category, subject, price, added_date, user_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE(), %s)
        """, (
            book["book_id"],
            book["image_url"],
            book["title"],       # ✅ map books.title → wishlist.book_title
            book["author"],
            category,
            book["subject"],
            book["price"],
            email
        ))
        conn.commit()

        return jsonify({"success": True, "message": f"{book['title']} added to wishlist!"})

    except Exception as e:
        conn.rollback()
        print("Wishlist Error:", str(e))   # ✅ log the actual DB error
        return jsonify({"success": False, "message": "Server error while adding to wishlist"})
    finally:
        cursor.close()
        conn.close()
        
# ------------------ DELETE FROM WISHLIST ------------------
@app.route("/delete_from_wishlist", methods=["POST"])
def delete_from_wishlist():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Please log in first"})

    data = request.get_json() or {}
    book_id = data.get("book_id")
    email = session["user_email"]

    if not book_id:
        return jsonify({"success": False, "message": "Missing book_id"})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Delete specific record for the logged-in user
        cursor.execute("DELETE FROM wishlist WHERE user_email = %s AND book_id = %s", (email, book_id))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"success": True, "message": "Book removed from wishlist"})
        else:
            return jsonify({"success": False, "message": "Book not found in wishlist"})

    except Exception as e:
        conn.rollback()
        print("Wishlist Delete Error:", e)
        return jsonify({"success": False, "message": "Error deleting item from wishlist"})
    finally:
        cursor.close()
        conn.close()
        
# ------------------ ORDERS ------------------
@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Please log in first"})

    email = session["user_email"]
    data = request.get_json()
    cart_items = data.get("cart_items", [])
    payment_mode = data.get("payment_mode", "Online")
    discounted_total = data.get("discounted_total")  # ✅ total after discount from frontend

    # ✅ Step 1: Fetch cart from DB if frontend didn't send
    if not cart_items:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT book_id, title, price, quantity FROM cart WHERE user_email=%s", (email,))
        cart_items = cursor.fetchall()
        cursor.close()
        conn.close()

    if not cart_items:
        return jsonify({"success": False, "message": "Cart is empty"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ Step 2: Get address for order
        cursor.execute("SELECT address FROM accounts WHERE email=%s", (email,))
        acc = cursor.fetchone()
        address = acc["address"] if acc else "Not Provided"

        order_date = datetime.now().date()
        shipping_date = (datetime.now() + timedelta(days=3)).date()
        placed_order_ids = []

        SHIPPING_COST = 100  # ✅ Flat shipping per order
        DISCOUNT_RATE = 0.30  # ✅ 30% discount

        # ✅ Step 3: Calculate total & insert orders
        for item in cart_items:
            price = float(item["price"])
            quantity = int(item["quantity"])

            # ✅ Apply 30% discount per item (if applicable)
            discounted_price = round(price * (1 - DISCOUNT_RATE), 2)
            subtotal = discounted_price * quantity
            total_price = subtotal + SHIPPING_COST  # ✅ include shipping

            # ✅ If total discount already calculated in frontend, adjust proportionally
            if discounted_total:
                total_price = discounted_total / len(cart_items)

            # ✅ Determine payment status
            if payment_mode == "Cash":
                payment_status = "Pending"
                payment_mode_str = "Cash"
            else:
                payment_status = "Paid"
                payment_mode_str = "Online"

            # ✅ Insert into database
            cursor.execute("""
                INSERT INTO orders 
                (user_email, book_id, title, quantity, order_date, shipping_date, 
                 order_amount, shipping_address, payment_status, payment_mode, order_status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                email,
                item["book_id"], item["title"], quantity,
                order_date, shipping_date, total_price,
                address, payment_status, payment_mode_str, "Shipped"
            ))
            placed_order_ids.append(cursor.lastrowid)

        # ✅ Step 4: Clear cart & commit
        session["last_order_ids"] = placed_order_ids
        cursor.execute("DELETE FROM cart WHERE user_email=%s", (email,))
        conn.commit()

        return jsonify({"success": True, "message": "Order placed successfully with 30% discount!"})

    except Exception as e:
        conn.rollback()
        print("❌ Error in place_order:", e)
        return jsonify({"success": False, "message": "Error placing order"})
    finally:
        cursor.close()
        conn.close()


# ------------------ ORDERS LIST ------------------
@app.route("/orders")
def orders():
    if "user_email" not in session:
        return redirect(url_for("signin"))

    email = session["user_email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT order_id, book_id, title, quantity, order_date, shipping_date, 
               order_amount, shipping_address, payment_status, 
               payment_mode, order_status
        FROM orders
        WHERE user_email = %s
        ORDER BY order_date DESC, order_id DESC
    """, (email,))
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("account.html", active_tab="orders", orders=orders)

# ------------------ CHANGE PASSWORD ------------------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_email" not in session:
        return redirect(url_for("login"))

    # GET → show change password tab
    if request.method == "GET":
        return render_template("account.html", active_tab="change_password")

    # POST handling (form or JSON)
    is_json = request.is_json
    if is_json:
        data = request.get_json() or {}
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = new_password  # client JS already checks confirm
    else:
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        confirm_password = request.form.get("confirm-password")

    # 1. Validate input
    if not old_password or not new_password:
        msg = "Missing old or new password"
        return (jsonify({"success": False, "message": msg}), 400) if is_json else (flash(msg, "danger"), redirect(url_for("change_password")))

    if new_password != confirm_password:
        msg = "New password and confirm password do not match!"
        return (jsonify({"success": False, "message": msg}), 400) if is_json else (flash(msg, "danger"), redirect(url_for("change_password")))

    # 2. Fetch stored hash
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password_hash FROM accounts WHERE email=%s", (session["user_email"],))
    user = cursor.fetchone()

    if not user or not user["password_hash"]:
        cursor.close()
        conn.close()
        msg = "No password found for this account. Please reset password."
        return (jsonify({"success": False, "message": msg}), 400) if is_json else (flash(msg, "danger"), redirect(url_for("change_password")))

    stored_hash = user["password_hash"]
    if isinstance(stored_hash, (bytes, bytearray)):
        stored_hash = stored_hash.decode("utf-8")

    # 3. Verify old password
    if not bcrypt.checkpw(old_password.encode("utf-8"), stored_hash.encode("utf-8")):
        cursor.close()
        conn.close()
        msg = "Old password is incorrect!"
        return (jsonify({"success": False, "message": msg}), 401) if is_json else (flash(msg, "danger"), redirect(url_for("change_password")))

    # 4. Save new password (string)
    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor.execute("UPDATE accounts SET password_hash=%s WHERE email=%s", (new_hash, session["user_email"]))
    conn.commit()
    cursor.close()
    conn.close()

    msg = "Password changed successfully!"
    return jsonify({"success": True, "message": msg}) if is_json else (flash(msg, "success"), redirect(url_for("change_password")))


# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------ CART ------------------
@app.route("/cart")
def cart():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cart WHERE user_email = %s", (email,))
    cart_items = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("cart.html", cart_items=cart_items, session_email=email)

# ------------------ ADD TO CART ------------------
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Please log in first"})

    data = request.get_json() or {}
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({"success": False, "message": "Missing book_id"})

    email = session["user_email"]

    # ✅ Detect category from book_id prefix/substring
    if "CS" in book_id:
        category = "computer"
        table_name = "computer_books"
    elif "EC" in book_id:
        category = "electronics"
        table_name = "electronics_books"
    elif "ME" in book_id:
        category = "mechanical"
        table_name = "mechanical_books"
    elif "CL" in book_id:
        category = "civil"
        table_name = "civil_books"
    elif "CH" in book_id:
        category = "chemical"
        table_name = "chemical_books"
    elif "BO" in book_id:
        category = "biomedical"
        table_name = "biomedical_books"
    elif "IT" in book_id:
        category = "it"
        table_name = "it_books"
    elif "AS" in book_id:
        category = "aerospace"
        table_name = "aerospace_books"
    elif "AT" in book_id:
        category = "automobile"
        table_name = "automobile_books"
    else:
        return jsonify({"success": False, "message": "Unknown category for this book_id"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # ✅ fetch book details from detected table
        query = f"""
            SELECT book_id, image_url, title, author, subject, price
            FROM {table_name}
            WHERE book_id = %s
        """
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()

        if not book:
            return jsonify({"success": False, "message": "Book not found"})

        # ✅ check for duplicates
        cursor.execute("SELECT * FROM cart WHERE user_email = %s AND book_id = %s", (email, book_id))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"success": True, "message": f"{book['title']} already in cart!"})

        # ✅ insert into cart
        cursor.execute("""
            INSERT INTO cart (user_email, book_id, image_url, title, author, category, subject, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            email,
            book["book_id"],
            book["image_url"],
            book["title"],
            book["author"],
            category,   # detected from book_id
            book["subject"],
            book["price"]
        ))
        conn.commit()

        return jsonify({"success": True, "message": f"{book['title']} added to cart!"})
    except Exception as e:
        conn.rollback()
        # print(e)  # log error in server console if needed
        return jsonify({"success": False, "message": "Server error while adding to cart"})
    finally:
        cursor.close()
        conn.close()

# ------------------ DELETE FROM CART ------------------
@app.route("/delete_from_cart", methods=["POST"])
def delete_from_cart():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Please log in first"})

    data = request.get_json() or {}
    book_id = data.get("book_id")
    email = session["user_email"]

    if not book_id:
        return jsonify({"success": False, "message": "Missing book_id"})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM cart WHERE user_email=%s AND book_id=%s", (email, book_id))
        conn.commit()
        return jsonify({"success": True, "message": "Book removed from cart"})
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"success": False, "message": "Error deleting item"})
    finally:
        cursor.close()
        conn.close()

# -------------------- Create Razorpay order -----------------------------
@app.route("/create-order", methods=["POST"])
def create_order():
    data = request.get_json()
    amount = int(float(data.get("amount", 0)) * 100)
    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    print("DEBUG Created Order:", order)   
    return jsonify(order)

# --------------------------Verify payment signature--------------------------------
@app.route("/verify-payment", methods=["POST"])
def verify_payment():
    data = request.get_json() or {}
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")

    env = os.getenv("RAZOR_ENV", "live").lower()
    secret = os.getenv("RAZOR_KEY_SECRET")

    # ✅ In TEST mode: bypass verification
    if env == "test":
        print("⚠️ TEST MODE: Simulating payment success")
        return jsonify({"ok": True, "message": "Payment verified (simulated in test mode)"})

    # ✅ In LIVE mode: do proper HMAC verification
    if not secret:
        return jsonify({"ok": False, "message": "Secret key not loaded"}), 500

    generated_signature = hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    if generated_signature == signature:
        return jsonify({"ok": True, "message": "Payment verified"})
    else:
        return jsonify({"ok": False, "message": "Invalid signature"}), 400

# ------------------ ORDER CONFIRMATION ------------------
@app.route("/order_confirmation")
def order_confirmation():
    if "user_email" not in session:
        return redirect(url_for("login"))

    last_order_ids = session.get("last_order_ids", [])

    if not last_order_ids:
        return render_template("order_confirmation.html", orders=[])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    format_strings = ",".join(["%s"] * len(last_order_ids))
    cursor.execute(f"""
        SELECT order_id, book_id, title, quantity, order_date, shipping_date, 
               order_amount, shipping_address, payment_status, 
               payment_mode, order_status
        FROM orders
        WHERE order_id IN ({format_strings})
        ORDER BY order_date DESC
    """, tuple(last_order_ids))
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("order_confirmation.html", orders=orders)

# ------------------ MOVE FROM WISHLIST TO CART ------------------
@app.route("/move_to_cart", methods=["POST"])
def move_to_cart():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Please log in first"})

    data = request.get_json() or {}
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({"success": False, "message": "Missing book_id"})

    email = session["user_email"]

    # ✅ Detect category from book_id prefix/substring
    if "CS" in book_id:
        category = "computer"
        table_name = "computer_books"
    elif "EC" in book_id:
        category = "electronics"
        table_name = "electronics_books"
    elif "ME" in book_id:
        category = "mechanical"
        table_name = "mechanical_books"
    elif "CL" in book_id:
        category = "civil"
        table_name = "civil_books"
    elif "CH" in book_id:
        category = "chemical"
        table_name = "chemical_books"
    elif "BO" in book_id:
        category = "biomedical"
        table_name = "biomedical_books"
    elif "IT" in book_id:
        category = "it"
        table_name = "it_books"
    elif "AS" in book_id:
        category = "aerospace"
        table_name = "aerospace_books"
    elif "AT" in book_id:
        category = "automobile"
        table_name = "automobile_books"
    else:
        return jsonify({"success": False, "message": "Unknown category for this book_id"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ Step 1: Check if already in cart
        cursor.execute("SELECT * FROM cart WHERE user_email = %s AND book_id = %s", (email, book_id))
        existing_cart = cursor.fetchone()
        if existing_cart:
            return jsonify({"success": False, "message": "Book already in cart!"})

        # ✅ Step 2: Fetch book details from its category table
        query = f"""
            SELECT book_id, image_url, title, author, subject, price
            FROM {table_name}
            WHERE book_id = %s
        """
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()

        if not book:
            return jsonify({"success": False, "message": "Book not found"})

        # ✅ Step 3: Insert into cart
        cursor.execute("""
            INSERT INTO cart (user_email, book_id, image_url, title, author, category, subject, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            email,
            book["book_id"],
            book["image_url"],
            book["title"],
            book["author"],
            category,
            book["subject"],
            book["price"]
        ))

        # ✅ Step 4: Delete from wishlist
        cursor.execute("DELETE FROM wishlist WHERE user_email = %s AND book_id = %s", (email, book_id))
        conn.commit()

        return jsonify({"success": True, "message": f"{book['title']} moved to cart and removed from wishlist!"})

    except Exception as e:
        conn.rollback()
        print("Move to Cart Error:", e)
        return jsonify({"success": False, "message": "Server error while moving book to cart"})
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)