# =========================================
# IMPORTS
# =========================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_file
)

import pandas as pd
import sqlite3
import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import r2_score

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from reportlab.pdfgen import canvas
from datetime import datetime
# =========================================
# APP CONFIG
# =========================================

app = Flask(__name__)

app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create upload folder if not exists
if not os.path.exists(UPLOAD_FOLDER):

    os.makedirs(UPLOAD_FOLDER)

# Create static folder if not exists
if not os.path.exists("static"):

    os.makedirs("static")
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE,

    password TEXT,

    role TEXT
)
""")

conn.commit()

cursor.execute(
    "SELECT * FROM users WHERE username=?",
    ("admin",)
)

admin = cursor.fetchone()

if not admin:

    cursor.execute(
        """
        INSERT INTO users
        (username,password,role)
        VALUES(?,?,?)
        """,
        (
            "admin",
            generate_password_hash(
                "admin123"
            ),
            "admin"
        )
    )

    conn.commit()

conn.close()
# =========================================
# DATABASE CONNECTION
# =========================================

conn = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

cursor = conn.cursor()

# =========================================
# USERS TABLE
# =========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE,

    password TEXT,

    role TEXT
)
""")

conn.commit()
# =========================================
# ACTIVITY LOG TABLE
# =========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS activity_logs(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    activity TEXT,

    timestamp TEXT
)
""")

conn.commit()

# =========================================
# DEFAULT ADMIN ACCOUNT
# =========================================

cursor.execute(
"""
SELECT * FROM users
WHERE username=?
""",
("admin",)
)

admin = cursor.fetchone()

if not admin:

    cursor.execute(
        """
        INSERT INTO users(
            username,
            password,
            role
        )
        VALUES (?, ?, ?)
        """,
        (
            "admin",
            generate_password_hash(
                "admin123"
            ),
            "admin"
        )
    )

    conn.commit()
# =========================================
# dataset_exist
# =========================================

def dataset_exists():

    return (
        os.path.exists("uploads/sales_data.csv")
        and
        os.path.exists("uploads/customer_data.csv")
    )
# =========================================
# HELPER FUNCTION
# LOAD DATASET AFTER UPLOAD
# =========================================

def load_data():

    try:

        sales_data = pd.read_csv(
            "uploads/sales_data.csv",
            encoding="utf-8"
        )

    except:

        sales_data = pd.read_csv(
            "uploads/sales_data.csv",
            encoding="latin1"
        )

    try:

        customer_data = pd.read_csv(
            "uploads/customer_data.csv",
            encoding="utf-8"
        )

    except:

        customer_data = pd.read_csv(
            "uploads/customer_data.csv",
            encoding="latin1"
        )

    return sales_data, customer_data



# =========================================
# ACTIVITY LOG FUNCTION
# =========================================

def add_log(username, activity):

    timestamp = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO activity_logs(
            username,
            activity,
            timestamp
        )
        VALUES (?, ?, ?)
        """,
        (
            username,
            activity,
            timestamp
        )
    )

    conn.commit()

    conn.close()


# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )

def login_required():

    return "user" in session
# =========================================
# CONTACT
# =========================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )
# =========================================
# ABOUT 
# =========================================
@app.route("/about")
def about():

    return render_template(
        "about.html"
    )

# =========================================
# LOGIN PAGE
# =========================================
@app.route("/login_page")
def login_page():

    return render_template(
        "login.html"
    )
# =========================================
# LOGIN 
# =========================================
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]

    password = request.form["password"]

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT *
        FROM users
        WHERE username=?
        """,

        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        stored_password = user[2]

        if check_password_hash(
            stored_password,
            password
        ):

            session["user"] = username

            session["role"] = user[3]

            add_log(
                username,
                "Logged In"
            )

            # ADMIN LOGIN

            if user[3] == "admin":

                return redirect(
                    "/admin"
                )

            # USER LOGIN

            if dataset_exists():

                return redirect(
                    "/dashboard"
                )

            return redirect(
                "/upload"
            )

    return """

    <h2>

    Invalid Username or Password

    </h2>

    <br>

    <a href='/login_page'>

    Back To Login

    </a>

    """
# =========================================
# FORGOT PASSWORD
# =========================================

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form["username"]

        new_password = request.form["new_password"]

        conn = sqlite3.connect("users.db")

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = cursor.fetchone()

        if user:

            cursor.execute(
                """
                UPDATE users
                SET password=?
                WHERE username=?
                """,
                (
                    generate_password_hash(
                        new_password
                    ),
                    username
                )
            )

            conn.commit()

            conn.close()

            return """
            Password Updated Successfully
            <br><br>
            <a href='/login_page'>Login</a>
            """

        conn.close()

        return "Username Not Found"

    return render_template(
        "forgot_password.html"
    )

# =========================================
# REGISTER
# =========================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form[
            "username"
        ]

        password = request.form[
            "password"
        ]

        hashed_password = generate_password_hash(
            password
        )

        conn = sqlite3.connect(
            "users.db"
        )

        cursor = conn.cursor()

        try:

            cursor.execute(

                """
                INSERT INTO users(
                    username,
                    password,
                    role
                )

                VALUES (?, ?, ?)
                """,

                (
                    username,
                    hashed_password,
                    "user"
                )
            )

            conn.commit()

            add_log(
                username,
                "Registered"
            )

            conn.close()

            return redirect("/login_page")

        except:

            conn.close()

            return """

            <h2>
            Username Already Exists
            </h2>

            <a href='/register'>
            Try Again
            </a>

            """

    return render_template(
        "register.html"
    )


# =========================================
# PROFILE
# =========================================

@app.route("/profile")
def profile():

    if "user" not in session:

        return redirect("/")

    return render_template(
        "profile.html"
    )


# =========================================
# CHANGE PASSWORD
# =========================================

@app.route(
    "/change_password",
    methods=["GET", "POST"]
)
def change_password():

    if "user" not in session:

        return redirect("/")

    if request.method == "POST":

        new_password = request.form[
            "password"
        ]

        hashed_password = generate_password_hash(
            new_password
        )

        conn = sqlite3.connect(
            "users.db"
        )

        cursor = conn.cursor()

        cursor.execute(

            """
            UPDATE users
            SET password=?
            WHERE username=?
            """,

            (
                hashed_password,
                session["user"]
            )
        )

        conn.commit()

        conn.close()

        add_log(
            session["user"],
            "Changed Password"
        )

        return """

        <h2>
        Password Changed Successfully
        </h2>

        <a href='/profile'>
        Back to Profile
        </a>

        """

    return """

    <h2>Change Password</h2>

    <form method='POST'>

        <input
        type='password'
        name='password'
        placeholder='New Password'
        required>

        <br><br>

        <button type='submit'>

            Change Password

        </button>

    </form>

    """


# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    if "user" in session:

        add_log(
            session["user"],
            "Logged Out"
        )

    session.clear()

    return redirect("/")


# =========================================
# SESSION CHECK
# =========================================

def login_required():

    if "user" not in session:

        return False

    return True
# =========================================
# UPLOAD DATASET
# =========================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    if "user" not in session:

        return redirect(
            "/login_page"
        )

    sales_exists = os.path.exists(
        "uploads/sales_data.csv"
    )

    customer_exists = os.path.exists(
        "uploads/customer_data.csv"
    )

    if request.method == "POST":

        sales_file = request.files[
            "sales_file"
        ]

        customer_file = request.files[
            "customer_file"
        ]

        # ==========================
        # CSV VALIDATION
        # ==========================

        if not sales_file.filename.lower().endswith(
            ".csv"
        ):

            return """

            <script>

            alert(
            'Please upload Sales Dataset in CSV format only'
            );

            window.location.href='/upload';

            </script>

            """

        if not customer_file.filename.lower().endswith(
            ".csv"
        ):

            return """

            <script>

            alert(
            'Please upload Customer Dataset in CSV format only'
            );

            window.location.href='/upload';

            </script>

            """

        # ==========================
        # CREATE UPLOAD FOLDER
        # ==========================

        os.makedirs(
            "uploads",
            exist_ok=True
        )

        # ==========================
        # SAVE FILES
        # ==========================

        sales_file.save(
            "uploads/sales_data.csv"
        )

        customer_file.save(
            "uploads/customer_data.csv"
        )

        # ==========================
        # GENERATE CHARTS
        # ==========================

        try:

            generate_charts()

        except Exception as e:

            print(
                "Chart Error:",
                e
            )

        # ==========================
        # ACTIVITY LOG
        # ==========================

        try:

            add_log(

                session["user"],

                "Uploaded Dataset"
            )

        except:

            pass

        # ==========================
        # SUCCESS MESSAGE
        # ==========================

        return """

        <script>

        alert(
        'Dataset Uploaded Successfully'
        );

        window.location.href='/dashboard';

        </script>

        """

    return render_template(

        "upload.html",

        sales_exists=sales_exists,

        customer_exists=customer_exists
    )
# =========================================
# CHECK DATASET
# =========================================

def dataset_exists():

    sales_file = os.path.join(
        "uploads",
        "sales_data.csv"
    )

    customer_file = os.path.join(
        "uploads",
        "customer_data.csv"
    )

    return (

        os.path.exists(
            sales_file
        )

        and

        os.path.exists(
            customer_file
        )

    )


# =========================================
# DASHBOARD
# =========================================

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect("/login_page")

    if not dataset_exists():
        return redirect("/upload")

    sales_data, customer_data = load_data()

    if sales_data is None:
        return redirect("/upload")

    # ==========================
    # DATASET INFORMATION
    # ==========================

    sales_records = len(
        sales_data
    )

    customer_records = len(
        customer_data
    )

    total_products = sales_data[
        "Product"
    ].nunique()

    total_regions = sales_data[
        "Region"
    ].nunique()

    try:
        generate_charts()

    except Exception as e:

        print(
            "Chart Generation Error:",
            e
        )

    # KPI

    total_sales = 0

    if "Total_Sales" in sales_data.columns:

        total_sales = round(
            sales_data["Total_Sales"].sum(),
            2
        )

    total_customers = 0

    if "Customer_ID" in sales_data.columns:

        total_customers = sales_data[
            "Customer_ID"
        ].nunique()

    top_product = "N/A"

    if (
        "Product" in sales_data.columns
        and
        "Total_Sales" in sales_data.columns
    ):

        top_product = sales_data.groupby(
            "Product"
        )["Total_Sales"].sum().idxmax()

    # ML Accuracy

    try:

        model, accuracy = train_model()

    except:

        accuracy = 0

    # SEARCH

    search = request.args.get(
        "search",
        ""
    )

    region = request.args.get(
        "region",
        "All"
    )

    filtered_data = sales_data.copy()

    if search and "Product" in filtered_data.columns:

        filtered_data = filtered_data[
            filtered_data["Product"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    if (
        region != "All"
        and
        "Region" in filtered_data.columns
    ):

        filtered_data = filtered_data[
            filtered_data["Region"]
            == region
        ]

    # TABLE

    sales_table = filtered_data.head(
        20
    ).to_html(
        classes=
        "table table-bordered table-striped",
        index=False
    )

    # REGIONS

    regions = []

    if "Region" in sales_data.columns:

        regions = sorted(
            sales_data["Region"]
            .dropna()
            .unique()
        )

    # INSIGHTS

    insights = [

        f"Highest Sales Product : {top_product}",

        f"Total Customers : {total_customers}",

        f"Total Sales : ₹{total_sales}",

        f"Model Accuracy : {accuracy}%"

    ]

    # LOG

    try:

        add_log(
            session["user"],
            "Viewed Dashboard"
        )

    except:

        pass

    return render_template(

        "dashboard.html",

        total_sales=total_sales,

        total_customers=total_customers,

        top_product=top_product,

        accuracy=accuracy,

        sales_table=sales_table,

        insights=insights,

        regions=regions,

        sales_records=sales_records,

        customer_records=customer_records,

        total_products=total_products,

        total_regions=total_regions,

        chart="chart.png",

        monthly_chart="monthly_chart.png",

        region_chart="region_chart.png",

        churn_chart="churn_chart.png"
    )
def generate_charts():

    import pandas as pd
    import matplotlib.pyplot as plt

    sales_file = "uploads/sales_data.csv"

    if not os.path.exists(sales_file):

        print("sales_data.csv not found")

        return

    os.makedirs(
        "static",
        exist_ok=True
    )

    sales_data = pd.read_csv(
        sales_file
    )

    print(
        "CSV Columns:",
        list(sales_data.columns)
    )

    # ==================================
    # PRODUCT SALES CHART
    # ==================================

    try:

        if (
            "Product" in sales_data.columns
            and
            "Total_Sales" in sales_data.columns
        ):

            plt.figure(figsize=(8,5))

            product_sales = sales_data.groupby(
                "Product"
            )["Total_Sales"].sum()

            product_sales.plot(
                kind="bar"
            )

            plt.title(
                "Product Sales Analysis"
            )

            plt.ylabel(
                "Total Sales"
            )

            plt.tight_layout()

            plt.savefig(
                "static/chart.png"
            )

            plt.close()

    except Exception as e:

        print(
            "Product Chart Error:",
            e
        )

    # ==================================
    # MONTHLY SALES TREND
    # ==================================

    try:

        if (
            "Date" in sales_data.columns
            and
            "Total_Sales" in sales_data.columns
        ):

            sales_data["Date"] = pd.to_datetime(
                sales_data["Date"]
            )

            monthly_sales = sales_data.groupby(
                sales_data["Date"].dt.month
            )["Total_Sales"].sum()

            plt.figure(figsize=(8,5))

            monthly_sales.plot(
                kind="line",
                marker="o"
            )

            plt.title(
                "Monthly Sales Trend"
            )

            plt.ylabel(
                "Total Sales"
            )

            plt.tight_layout()

            plt.savefig(
                "static/monthly_chart.png"
            )

            plt.close()

    except Exception as e:

        print(
            "Monthly Chart Error:",
            e
        )

    # ==================================
    # REGION SALES CHART
    # ==================================

    try:

        if (
            "Region" in sales_data.columns
            and
            "Total_Sales" in sales_data.columns
        ):

            plt.figure(figsize=(8,5))

            region_sales = sales_data.groupby(
                "Region"
            )["Total_Sales"].sum()

            region_sales.plot(
                kind="bar"
            )

            plt.title(
                "Region Wise Sales"
            )

            plt.ylabel(
                "Total Sales"
            )

            plt.tight_layout()

            plt.savefig(
                "static/region_chart.png"
            )

            plt.close()

    except Exception as e:

        print(
            "Region Chart Error:",
            e
        )

# ==================================
# CUSTOMER CHURN CHART
# ==================================

try:

    customer_file = "uploads/customer_data.csv"

    if os.path.exists(customer_file):

        customer_data = pd.read_csv(
            customer_file
        )

        print(
            "Customer Columns:",
            list(customer_data.columns)
        )

        if "Churn" in customer_data.columns:

            plt.figure(figsize=(6,6))

            churn_data = customer_data[
                "Churn"
            ].value_counts()

            churn_data.plot(
                kind="pie",
                autopct="%1.1f%%"
            )

            plt.ylabel("")

            plt.title(
                "Customer Churn Analysis"
            )

            plt.tight_layout()

            plt.savefig(
                "static/churn_chart.png"
            )

            plt.close()

            print(
                "Churn Chart Generated"
            )

except Exception as e:

    print(
        "Churn Chart Error:",
        e
    )
# =========================================
# DATASET STATUS
# =========================================

@app.route("/dataset_status")
def dataset_status():

    if dataset_exists():

        return """

        <h2>
        Dataset Uploaded
        </h2>

        """

    return """

    <h2>
    Dataset Not Uploaded
    </h2>

    <a href='/upload'>
    Upload Dataset
    </a>

    """
# =========================================
# TRAIN MACHINE LEARNING MODEL
# =========================================

def train_model():

    sales_data, customer_data = load_data()

    if sales_data is None:

        return None, 0

    required_columns = [

        "Quantity",
        "Price",
        "Total_Sales"
    ]

    for col in required_columns:

        if col not in sales_data.columns:

            return None, 0

    X = sales_data[
        ["Quantity", "Price"]
    ]

    y = sales_data[
        "Total_Sales"
    ]

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.2,

        random_state=42
    )

    model = RandomForestRegressor(

        n_estimators=100,

        random_state=42
    )

    model.fit(

        X_train,

        y_train
    )

    y_pred = model.predict(
        X_test
    )

    accuracy = round(

        r2_score(
            y_test,
            y_pred
        ) * 100,

        2
    )

    return model, accuracy


# =========================================
# PREDICTION MODULE
# =========================================

@app.route(
    "/prediction",
    methods=["GET", "POST"]
)
def prediction():

    if not login_required():

        return redirect("/")

    if not dataset_exists():

        return redirect(
            "/upload"
        )

    prediction_result = None

    accuracy = 0

    model, accuracy = train_model()

    if request.method == "POST":

        quantity = int(

            request.form[
                "quantity"
            ]
        )

        price = float(

            request.form[
                "price"
            ]
        )

        prediction_result = round(

            model.predict(

                [[quantity, price]]

            )[0],

            2
        )

        add_log(

            session["user"],

            "Generated Prediction"
        )

    return render_template(

        "prediction.html",

        prediction=
        prediction_result,

        accuracy=
        accuracy
    )


# =========================================
# SALES FORECAST FUNCTION
# =========================================

def forecast_sales():

    sales_data, customer_data = load_data()

    if sales_data is None:

        return 0

    avg_sales = round(

        sales_data[
            "Total_Sales"
        ].mean(),

        2
    )

    return avg_sales


# =========================================
# MODEL INFORMATION
# =========================================

@app.route("/model_info")
def model_info():

    if not login_required():

        return redirect("/")

    model, accuracy = train_model()

    return f"""

    <h2>
    Machine Learning Model
    </h2>

    <hr>

    <h3>
    Algorithm :
    Random Forest Regressor
    </h3>

    <h3>
    Accuracy :
    {accuracy} %
    </h3>

    <h3>
    Features :
    Quantity, Price
    </h3>

    <h3>
    Output :
    Total Sales
    </h3>

    """


# =========================================
# SALES FORECAST PAGE
# =========================================

@app.route("/forecast")
def forecast():

    if not login_required():

        return redirect("/")

    future_sales = forecast_sales()

    add_log(

        session["user"],

        "Viewed Forecast"
    )

    return f"""

    <h2>
    Sales Forecast
    </h2>

    <hr>

    <h3>
    Expected Average Sales :
    ₹ {future_sales}
    </h3>

    """
# =========================================
# CUSTOMER SEGMENTATION
# =========================================

def generate_segmentation():

    sales_data, customer_data = load_data()

    if sales_data is None:

        return None

    required_columns = [

        "Quantity",
        "Total_Sales"

    ]

    for col in required_columns:

        if col not in sales_data.columns:

            return None

    segment_data = sales_data[
        [
            "Quantity",
            "Total_Sales"
        ]
    ]

    kmeans = KMeans(

        n_clusters=3,

        random_state=42,

        n_init=10
    )

    sales_data["Segment"] = kmeans.fit_predict(
        segment_data
    )

    # =====================================
    # SEGMENTATION CHART
    # =====================================

    plt.figure(figsize=(8,5))

    plt.scatter(

        sales_data["Quantity"],

        sales_data["Total_Sales"],

        c=sales_data["Segment"]

    )

    plt.xlabel(
        "Quantity"
    )

    plt.ylabel(
        "Total Sales"
    )

    plt.title(
        "Customer Segmentation"
    )

    plt.tight_layout()

    plt.savefig(
        "static/segmentation_chart.png"
    )

    plt.close()

    return sales_data


# =========================================
# SEGMENT ANALYTICS
# =========================================

def get_segment_summary():

    sales_data = generate_segmentation()

    if sales_data is None:

        return {

            "high": 0,

            "medium": 0,

            "low": 0
        }

    segment_counts = sales_data[
        "Segment"
    ].value_counts()

    high = 0
    medium = 0
    low = 0

    if len(segment_counts) >= 1:

        high = segment_counts.iloc[0]

    if len(segment_counts) >= 2:

        medium = segment_counts.iloc[1]

    if len(segment_counts) >= 3:

        low = segment_counts.iloc[2]

    return {

        "high": high,

        "medium": medium,

        "low": low
    }


# =========================================
# SEGMENTATION PAGE
# =========================================

@app.route("/segmentation")
def segmentation():

    if not login_required():

        return redirect("/")

    if not dataset_exists():

        return redirect(
            "/upload"
        )

    generate_segmentation()

    summary = get_segment_summary()

    add_log(

        session["user"],

        "Viewed Segmentation"
    )

    return render_template(

        "segmentation.html",

        high=summary["high"],

        medium=summary["medium"],

        low=summary["low"]
    )


# =========================================
# SEGMENT DETAILS
# =========================================

@app.route("/segment_details")
def segment_details():

    if not login_required():

        return redirect("/")

    sales_data = generate_segmentation()

    if sales_data is None:

        return redirect(
            "/upload"
        )

    table = sales_data.head(
        50
    ).to_html(

        classes=
        "table table-bordered",

        index=False
    )

    return f"""

    <html>

    <head>

    <title>

    Segment Details

    </title>

    </head>

    <body>

    <h2>

    Customer Segmentation Data

    </h2>

    {table}

    </body>

    </html>

    """


# =========================================
# CUSTOMER RETENTION INSIGHTS
# =========================================

@app.route("/retention")
def retention():

    if not login_required():

        return redirect("/")

    return """

    <h2>

    Customer Retention Suggestions

    </h2>

    <hr>

    <ul>

        <li>
        Offer discounts to
        low-value customers.
        </li>

        <li>
        Reward high-value
        customers with loyalty
        programs.
        </li>

        <li>
        Provide personalized
        marketing campaigns.
        </li>

        <li>
        Improve customer support
        engagement.
        </li>

    </ul>

    """
# =========================================
# ADMIN PANEL
# =========================================

@app.route("/admin")
def admin():

    if session.get("role") != "admin":

        return "Access Denied"

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    # SEARCH

    search = request.args.get(
        "search",
        ""
    )

    if search:

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username LIKE ?
            """,
            (
                "%" + search + "%",
            )
        )

    else:

        cursor.execute(
            "SELECT * FROM users"
        )

    users = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM activity_logs
        ORDER BY id DESC
        LIMIT 20
        """
    )

    logs = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        logs=logs
    )
# =========================================
# ADD USER
# =========================================

@app.route("/add_user", methods=["GET", "POST"])
def add_user():

    if session.get("role") != "admin":

        return "Access Denied"

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        hashed_password = generate_password_hash(
            password
        )

        conn = sqlite3.connect("users.db")

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users(
                username,
                password,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                hashed_password,
                role
            )
        )

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template(
        "add_user.html"
    )

# =========================================
# EDIT USER
# =========================================

@app.route(
    "/edit_user/<int:user_id>",
    methods=["GET", "POST"]
)
def edit_user(user_id):

    if session.get("role") != "admin":

        return "Access Denied"

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    if user and user[1] == "admin":

        conn.close()

        return "Admin account cannot be edited."

    if request.method == "POST":

        username = request.form["username"]

        role = request.form["role"]

        cursor.execute(
            """
            UPDATE users
            SET username=?,
                role=?
            WHERE id=?
            """,
            (
                username,
                role,
                user_id
            )
        )

        conn.commit()

        conn.close()

        return redirect("/admin")

    conn.close()

    return render_template(
        "edit_user.html",
        user=user
    )
# =========================================
# DELETE USER
# =========================================

@app.route(
    "/delete_user/<int:user_id>"
)
def delete_user(user_id):

    if session.get("role") != "admin":

        return "Access Denied"

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    if user and user[0] == "admin":

        conn.close()

        return "Admin account cannot be deleted."

    cursor.execute(
        """
        DELETE FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    conn.commit()

    conn.close()

    return redirect("/admin")

# =========================================
# ACTIVITY LOGS
# =========================================

@app.route("/activity_logs")
def activity_logs():

    if session.get("role") != "admin":

        return "Access Denied"

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT *
        FROM activity_logs
        ORDER BY id DESC
        """
    )

    logs = cursor.fetchall()

    conn.close()

    return render_template(

        "activity_logs.html",

        logs=logs
    )


# =========================================
# SYSTEM STATISTICS
# =========================================

@app.route("/system_stats")
def system_stats():

    if session.get("role") != "admin":

        return "Access Denied"

    conn = sqlite3.connect(
        "users.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM activity_logs"
    )

    total_logs = cursor.fetchone()[0]

    conn.close()

    return f"""

    <h2>

    System Statistics

    </h2>

    <hr>

    <h3>

    Total Users :
    {total_users}

    </h3>

    <h3>

    Total Activities :
    {total_logs}

    </h3>

    """
# =========================================
# PDF REPORT GENERATION
# =========================================

@app.route("/report")
def report():

    if not login_required():

        return redirect("/")

    sales_data, customer_data = load_data()

    if sales_data is None:

        return redirect("/upload")

    pdf_path = "static/report.pdf"

    total_sales = round(
        sales_data["Total_Sales"].sum(),
        2
    )

    total_customers = sales_data[
        "Customer_ID"
    ].nunique()

    top_product = sales_data.groupby(
        "Product"
    )["Total_Sales"].sum().idxmax()

    c = canvas.Canvas(pdf_path)
    c.setFont(
        "Helvetica-Bold",
        16
    )

    c.drawString(
        150,
        800,
        "Customer Sales Report"
    )

    c.setFont(
        "Helvetica",
        12
    )

    c.drawString(
        50,
        750,
        f"Total Sales : ₹ {total_sales}"
    )

    c.drawString(
        50,
        720,
        f"Total Customers : {total_customers}"
    )

    c.drawString(
        50,
        690,
        f"Top Product : {top_product}"
    )

    c.drawString(
        50,
        660,
        f"Generated By : {session['user']}"
    )

    c.save()

    add_log(
        session["user"],
        "Generated PDF Report"
    )

    return send_file(
        pdf_path,
        as_attachment=True
    )


# =========================================
# EXPORT EXCEL REPORT
# =========================================

@app.route("/export_excel")
def export_excel():

    if not login_required():

        return redirect("/")

    sales_data, customer_data = load_data()

    if sales_data is None:

        return redirect("/upload")

    excel_path = "static/sales_report.xlsx"

    sales_data.to_excel(

        excel_path,

        index=False
    )

    add_log(

        session["user"],

        "Exported Excel Report"
    )

    return send_file(

        excel_path,

        as_attachment=True
    )


# =========================================
# BUSINESS INSIGHTS
# =========================================

@app.route("/insights")
def insights():

    if not login_required():

        return redirect("/")

    insights_data = generate_insights()

    html = """

    <h2>

    AI Business Insights

    </h2>

    <hr>

    """

    for item in insights_data:

        html += f"<h4>{item}</h4>"

    return html

# =========================================
# ERROR HANDLER
# =========================================

@app.errorhandler(404)
def not_found(error):

    return """

    <h2>

    Page Not Found

    </h2>

    <a href='/dashboard'>

    Dashboard

    </a>

    """, 404


# =========================================
# ERROR HANDLER 500
# =========================================

##def internal_error(error):

    return """
    <h2>

      Internal Server Error

     </h2>


    Please check uploaded dataset
    and application logs.

    """, 500
# =========================================
# RUN APPLICATION
# =========================================
if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=True
)