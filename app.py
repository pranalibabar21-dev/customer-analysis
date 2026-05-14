from flask import Flask, render_template, request, redirect, session
import pandas as pd
import sqlite3
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from reportlab.pdfgen import canvas

# ----------------------------------------------------
# FLASK APP
# ----------------------------------------------------
app = Flask(__name__)

app.secret_key = "secret123"

# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------
conn = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

cursor = conn.cursor()

# ----------------------------------------------------
# CREATE TABLE
# ----------------------------------------------------
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        password TEXT,

        role TEXT
    )
    '''
)

conn.commit()

# ----------------------------------------------------
# DEFAULT ADMIN
# ----------------------------------------------------
cursor.execute(
    "SELECT * FROM users WHERE username=?",
    ("admin",)
)

admin = cursor.fetchone()

if not admin:

    cursor.execute(

        "INSERT INTO users(username, password, role) VALUES(?, ?, ?)",

        ("admin", "admin123", "admin")
    )

    conn.commit()

# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
sales_data = pd.read_csv(
    "sales_data.csv"
)

customer_data = pd.read_csv(
    "customer_data.csv"
)

# ----------------------------------------------------
# DATE
# ----------------------------------------------------
sales_data['Date'] = pd.to_datetime(
    sales_data['Date']
)

# ----------------------------------------------------
# KPI
# ----------------------------------------------------
total_sales = round(

    sales_data['Total_Sales'].sum(),

    2
)

total_customers = sales_data[
    'Customer_ID'
].nunique()

top_product = sales_data.groupby(
    'Product'
)['Total_Sales'].sum().idxmax()

# ----------------------------------------------------
# ML MODEL
# ----------------------------------------------------
X = sales_data[['Quantity', 'Price']]

y = sales_data['Total_Sales']

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.2,
    random_state=42
)

model = LinearRegression()

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

accuracy = round(
    r2_score(y_test, y_pred),
    2
)

# ----------------------------------------------------
# PRODUCT SALES CHART
# ----------------------------------------------------
product_sales = sales_data.groupby(
    'Product'
)['Total_Sales'].sum()

plt.figure(figsize=(8,5))

product_sales.plot(kind='bar')

plt.title("Product Sales")

plt.xlabel("Product")

plt.ylabel("Sales")

plt.tight_layout()

plt.savefig("static/chart.png")

plt.close()

# ----------------------------------------------------
# MONTHLY SALES
# ----------------------------------------------------
sales_data['Month'] = sales_data[
    'Date'
].dt.month

monthly_sales = sales_data.groupby(
    'Month'
)['Total_Sales'].sum()

plt.figure(figsize=(8,5))

plt.plot(
    monthly_sales.index,
    monthly_sales.values,
    marker='o'
)

plt.title("Monthly Sales Trend")

plt.xlabel("Month")

plt.ylabel("Sales")

plt.tight_layout()

plt.savefig(
    "static/monthly_chart.png"
)

plt.close()

# ----------------------------------------------------
# REGION SALES
# ----------------------------------------------------
region_sales = sales_data.groupby(
    'Region'
)['Total_Sales'].sum()

plt.figure(figsize=(7,5))

region_sales.plot(
    kind='bar',
    color='orange'
)

plt.title("Region-wise Sales")

plt.xlabel("Region")

plt.ylabel("Sales")

plt.tight_layout()

plt.savefig(
    "static/region_chart.png"
)

plt.close()

# ----------------------------------------------------
# TOP PRODUCTS
# ----------------------------------------------------
top_products = sales_data.groupby(
    'Product'
)['Total_Sales'].sum().sort_values(
    ascending=False
).head(5)

# ----------------------------------------------------
# CHURN DATA
# ----------------------------------------------------
churn = customer_data[
    'Churn'
].value_counts()

# ----------------------------------------------------
# CHURN DONUT CHART
# ----------------------------------------------------
plt.figure(figsize=(5,5))

plt.pie(

    churn,

    labels=churn.index,

    autopct='%1.1f%%'
)

centre_circle = plt.Circle(

    (0,0),

    0.70,

    fc='white'
)

fig = plt.gcf()

fig.gca().add_artist(
    centre_circle
)

plt.title(
    "Customer Churn Analysis"
)

plt.tight_layout()

plt.savefig(
    "static/churn_chart.png"
)

plt.close()

# ----------------------------------------------------
# HOME
# ----------------------------------------------------
@app.route("/")

def home():

    return redirect("/dashboard")

# ----------------------------------------------------
# DASHBOARD
# ----------------------------------------------------
@app.route("/dashboard")

def dashboard():

    if 'user' not in session:

        return render_template(
            "dashboard.html"
        )

    search = request.args.get("search")

    filtered_data = sales_data

    if search:

        filtered_data = sales_data[
            sales_data['Product'].str.contains(
                search,
                case=False
            )
        ]

    sales_table = filtered_data.head(20).to_html(
        classes="table table-bordered",
        index=False
    )

    return render_template(

        "dashboard.html",

        total_sales=total_sales,

        total_customers=total_customers,

        top_product=top_product,

        accuracy=accuracy,

        chart="chart.png",

        monthly_chart="monthly_chart.png",

        churn_chart="churn_chart.png",

        region_chart="region_chart.png",

        top_products=top_products,

        sales_table=sales_table
    )

# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
@app.route("/login", methods=["POST"])

def login():

    username = request.form["username"]

    password = request.form["password"]

    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM users WHERE username=? AND password=?",

        (username, password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        session['user'] = user[1]

        session['role'] = user[3]

        return redirect("/dashboard")

    return redirect("/dashboard")

# ----------------------------------------------------
# REGISTER
# ----------------------------------------------------
@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        conn = sqlite3.connect("users.db")

        cursor = conn.cursor()

        cursor.execute(

            "INSERT INTO users(username, password, role) VALUES(?, ?, ?)",

            (username, password, "user")
        )

        conn.commit()

        conn.close()

        return redirect("/dashboard")

    return render_template(
        "register.html"
    )

# ----------------------------------------------------
# PROFILE
# ----------------------------------------------------
@app.route("/profile")

def profile():

    if 'user' not in session:

        return redirect("/dashboard")

    return render_template(
        "profile.html"
    )

# ----------------------------------------------------
# PREDICTION
# ----------------------------------------------------
@app.route("/prediction", methods=["GET", "POST"])

def prediction():

    if 'user' not in session:

        return redirect("/dashboard")

    prediction = None

    if request.method == "POST":

        quantity = int(
            request.form["quantity"]
        )

        price = int(
            request.form["price"]
        )

        prediction = model.predict(
            [[quantity, price]]
        )[0]

    plt.figure(figsize=(6,4))

    plt.scatter(y_test, y_pred)

    plt.xlabel("Actual")

    plt.ylabel("Predicted")

    plt.title("Sales Prediction")

    plt.tight_layout()

    plt.savefig(
        "static/prediction_chart.png"
    )

    plt.close()

    return render_template(

        "prediction.html",

        prediction=prediction,

        prediction_chart="prediction_chart.png"
    )

# ----------------------------------------------------
# ADMIN
# ----------------------------------------------------
@app.route("/admin")

def admin():

    if 'user' not in session:

        return redirect("/dashboard")

    if session.get('role') != 'admin':

        return "Access Denied"

    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    conn.close()

    return render_template(

        "admin.html",

        users=users
    )

# ----------------------------------------------------
# UPLOAD
# ----------------------------------------------------
@app.route("/upload", methods=["POST"])

def upload():

    if 'file' not in request.files:

        return redirect("/dashboard")

    file = request.files['file']

    if file.filename == '':

        return redirect("/dashboard")

    file.save(file.filename)

    return redirect("/dashboard")

# ----------------------------------------------------
# DOWNLOAD CSV
# ----------------------------------------------------
@app.route("/download")

def download():

    return sales_data.to_csv(index=False)

# ----------------------------------------------------
# PDF REPORT
# ----------------------------------------------------
@app.route("/pdf")

def pdf():

    pdf_path = "sales_report.pdf"

    c = canvas.Canvas(pdf_path)

    c.drawString(
        100,
        800,
        "Customer Sales Analysis Report"
    )

    c.drawString(
        100,
        760,
        f"Total Sales: {total_sales}"
    )

    c.drawString(
        100,
        740,
        f"Total Customers: {total_customers}"
    )

    c.save()

    return redirect("/dashboard")

# ----------------------------------------------------
# LOGOUT
# ----------------------------------------------------
@app.route("/logout")

def logout():

    session.clear()

    return redirect("/dashboard")

# ----------------------------------------------------
# RUN APP
# ----------------------------------------------------
if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False
    )