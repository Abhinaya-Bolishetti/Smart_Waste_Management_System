import json
import os
import sqlite3
import uuid
from functools import wraps
from math import atan2, cos, radians, sin, sqrt

import numpy as np
import tensorflow as tf
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "MOBILENET.h5")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "wastewise-dev-secret")

app.config["DATABASE"] = os.path.join(BASE_DIR, "waste_centers.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY", "")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

WASTE_CATEGORIES = ['battery', 'biological', 'cardboard', 'clothes', 'glass', 'metal', 'paper', 'plastic', 'shoes', 'trash']

try:
    MODEL = tf.keras.models.load_model(MODEL_PATH)
except Exception:
    MODEL = None


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_connection(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS waste_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            center_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            category TEXT NOT NULL,
            price_per_kg REAL NOT NULL
        );
        """
    )

    admin = cursor.execute("SELECT * FROM admin WHERE username = ?", ("admin",)).fetchone()
    if admin is None:
        cursor.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", generate_password_hash("admin")),
        )
    elif not is_hashed_password(admin["password"]):
        cursor.execute(
            "UPDATE admin SET password = ? WHERE id = ?",
            (generate_password_hash(admin["password"]), admin["id"]),
        )

    db.commit()


def is_hashed_password(raw_value):
    return isinstance(raw_value, str) and raw_value.startswith(("pbkdf2:", "scrypt:"))


def verify_password(stored_password, entered_password):
    if is_hashed_password(stored_password):
        return check_password_hash(stored_password, entered_password)
    return stored_password == entered_password


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def admin_required(route_func):
    @wraps(route_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in as admin to continue.", "warning")
            return redirect(url_for("admin_login"))
        return route_func(*args, **kwargs)

    return wrapper


def user_required(route_func):
    @wraps(route_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("user_login"))
        return route_func(*args, **kwargs)

    return wrapper


def predict_waste_category(img_path):
    if MODEL is None:
        raise RuntimeError("Model file MOBILENET.h5 is missing or failed to load.")

    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = MODEL.predict(img_array, verbose=0)
    class_idx = int(np.argmax(preds[0]))
    return WASTE_CATEGORIES[class_idx]

def haversine(lat1, lon1, lat2, lon2):
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


@app.route("/")
def index():
    return render_template("index.html", categories=WASTE_CATEGORIES)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = get_db().execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
        if admin and verify_password(admin["password"], password):
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Admin login successful.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin username or password.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    centers = get_db().execute(
        "SELECT * FROM waste_centers ORDER BY category, center_name"
    ).fetchall()
    return render_template("admin_dashboard.html", centers=centers)


@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def add_center():
    if request.method == "POST":
        name = request.form.get("center_name", "").strip()
        category = request.form.get("category", "")

        try:
            latitude = float(request.form.get("latitude", ""))
            longitude = float(request.form.get("longitude", ""))
            price_per_kg = float(request.form.get("price_per_kg", ""))
        except ValueError:
            flash("Please enter valid numeric values for latitude, longitude, and price.", "danger")
            return render_template("add_center.html", categories=WASTE_CATEGORIES)

        if not name:
            flash("Center name is required.", "danger")
            return render_template("add_center.html", categories=WASTE_CATEGORIES)

        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            flash("Latitude must be between -90 and 90, and longitude must be between -180 and 180.", "danger")
            return render_template("add_center.html", categories=WASTE_CATEGORIES)

        if price_per_kg < 0:
            flash("Price per kg cannot be negative.", "danger")
            return render_template("add_center.html", categories=WASTE_CATEGORIES)

        if category not in WASTE_CATEGORIES:
            flash("Please choose a valid waste category.", "danger")
            return render_template("add_center.html", categories=WASTE_CATEGORIES)

        get_db().execute(
            """
            INSERT INTO waste_centers (center_name, latitude, longitude, category, price_per_kg)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, latitude, longitude, category, price_per_kg),
        )
        get_db().commit()
        flash("Waste center added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_center.html", categories=WASTE_CATEGORIES)


@app.route("/admin/edit/<int:center_id>", methods=["GET", "POST"])
@admin_required
def edit_center(center_id):
    db = get_db()
    center = db.execute("SELECT * FROM waste_centers WHERE id = ?", (center_id,)).fetchone()
    if center is None:
        flash("Waste center not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        name = request.form.get("center_name", "").strip()
        category = request.form.get("category", "")

        try:
            latitude = float(request.form.get("latitude", ""))
            longitude = float(request.form.get("longitude", ""))
            price_per_kg = float(request.form.get("price_per_kg", ""))
        except ValueError:
            flash("Please enter valid numeric values for latitude, longitude, and price.", "danger")
            return render_template(
                "edit_center.html", center=center, categories=WASTE_CATEGORIES
            )

        if not name:
            flash("Center name is required.", "danger")
            return render_template("edit_center.html", center=center, categories=WASTE_CATEGORIES)

        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            flash("Latitude must be between -90 and 90, and longitude must be between -180 and 180.", "danger")
            return render_template("edit_center.html", center=center, categories=WASTE_CATEGORIES)

        if price_per_kg < 0:
            flash("Price per kg cannot be negative.", "danger")
            return render_template("edit_center.html", center=center, categories=WASTE_CATEGORIES)

        if category not in WASTE_CATEGORIES:
            flash("Please choose a valid waste category.", "danger")
            return render_template("edit_center.html", center=center, categories=WASTE_CATEGORIES)

        db.execute(
            """
            UPDATE waste_centers
            SET center_name = ?, latitude = ?, longitude = ?, category = ?, price_per_kg = ?
            WHERE id = ?
            """,
            (name, latitude, longitude, category, price_per_kg, center_id),
        )
        db.commit()
        flash("Waste center updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_center.html", center=center, categories=WASTE_CATEGORIES)


@app.route("/admin/delete/<int:center_id>", methods=["POST"])
@admin_required
def delete_center(center_id):
    db = get_db()
    db.execute("DELETE FROM waste_centers WHERE id = ?", (center_id,))
    db.commit()
    flash("Waste center deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("user_register.html")

        if len(password) < 4:
            flash("Password must be at least 4 characters long.", "danger")
            return render_template("user_register.html")

        if password != confirm_password:
            flash("Password and confirm password do not match.", "danger")
            return render_template("user_register.html")

        try:
            get_db().execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), email),
            )
            get_db().commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("user_login"))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose a different one.", "danger")

    return render_template("user_register.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and verify_password(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back, {}.".format(user["username"]), "success")
            return redirect(url_for("user_upload"))

        flash("Invalid username or password.", "danger")

    return render_template("user_login.html")


@app.route("/user/upload", methods=["GET", "POST"])
@user_required
def user_upload():
    if request.method == "POST":
        file = request.files.get("file")

        if file is None or file.filename == "":
            flash("Please choose an image to upload.", "warning")
            return render_template("user_upload.html")

        if not allowed_file(file.filename):
            flash("Invalid file type. Allowed: png, jpg, jpeg", "danger")
            return render_template("user_upload.html")

        filename = "{}-{}".format(uuid.uuid4().hex[:10], secure_filename(file.filename))
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            predicted_category = predict_waste_category(filepath)
        except RuntimeError as ex:
            flash(str(ex), "danger")
            return render_template("user_upload.html")

        session["predicted_category"] = predicted_category
        session["uploaded_image"] = filename
        flash(
            "Image classified as {}. Next, allow location access to find nearby centers.".format(
                predicted_category
            ),
            "success",
        )
        return redirect(url_for("results"))

    return render_template("user_upload.html")


@app.route("/results")
@user_required
def results():
    predicted_category = session.get("predicted_category", "")
    if not predicted_category:
        flash("Please upload a waste image first.", "warning")
        return redirect(url_for("user_upload"))

    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    error_param = request.args.get("error", "")
    uploaded_image = session.get("uploaded_image")

    if error_param:
        error_messages = {
            "permission_denied": "Location access denied. Please enable location services in your browser.",
            "unavailable": "Location information is unavailable right now.",
            "timeout": "Location request timed out. Please try again.",
            "unsupported": "Geolocation is not supported in this browser.",
            "location": "Could not detect your location.",
        }
        flash(error_messages.get(error_param, "Could not detect your location."), "warning")

    centers_with_dist = []
    location_pending = user_lat is None or user_lng is None
    if not location_pending:
        centers = get_db().execute(
            "SELECT * FROM waste_centers WHERE lower(category) = lower(?)",
            (predicted_category,),
        ).fetchall()
        for center in centers:
            distance_km = haversine(user_lat, user_lng, center["latitude"], center["longitude"])
            centers_with_dist.append(
                {
                    "id": center["id"],
                    "center_name": center["center_name"],
                    "latitude": center["latitude"],
                    "longitude": center["longitude"],
                    "category": center["category"],
                    "price_per_kg": center["price_per_kg"],
                    "distance": round(distance_km, 2),
                }
            )
        centers_with_dist.sort(key=lambda item: item["distance"])

    if not location_pending and not centers_with_dist:
        flash(
            "No nearby centers found for {}. Try another image or ask admin to add centers for this category.".format(
                predicted_category
            ),
            "info",
        )

    uploaded_image_url = (
        url_for("static", filename="uploads/{}".format(uploaded_image)) if uploaded_image else ""
    )

    return render_template(
        "results.html",
        category=predicted_category,
        centers=centers_with_dist,
        user_lat=user_lat,
        user_lng=user_lng,
        location_pending=location_pending,
        uploaded_image_url=uploaded_image_url,
        google_maps_api_key=app.config["GOOGLE_MAPS_API_KEY"],
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out successfully.", "info")
    return redirect(url_for("index"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)