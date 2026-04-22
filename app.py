import joblib
import random
from flask import Flask, render_template, request, jsonify, redirect, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

model = joblib.load("model.pkl")

USER_FILE = "users.json"
HISTORY_FILE = "history.json"

# ---------- SAFE JSON ----------
def safe_load(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def safe_save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ---------- USERS ----------
def load_users():
    return safe_load(USER_FILE)

def save_users(users):
    safe_save(USER_FILE, users)

# ---------- HISTORY ----------
def load_history():
    return safe_load(HISTORY_FILE)

def save_history(data):
    safe_save(HISTORY_FILE, data)

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials ❌")

    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return render_template("signup.html", error="User already exists ❌")

        users[username] = password
        save_users(users)
        return redirect("/")

    return render_template("signup.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ---------- AI INSIGHT ----------
def generate_ai_insight(glucose, hours, activity, insulin, slope):
    reasons = []

    if glucose < 80:
        reasons.append(f"Glucose is very low ({glucose} mg/dL)")

    if hours > 4:
        reasons.append(f"Long time since last meal ({hours} hours)")

    if activity == 2 and glucose < 110:
        reasons.append("High physical activity with moderate glucose")

    if insulin < 2 and glucose < 120:
        reasons.append("Recent insulin dose may be lowering glucose")

    if slope < -15:
        reasons.append("Glucose level is dropping rapidly")

    if not reasons:
        reasons.append("All readings are within safe range")

    return reasons

# ---------- PREDICT ----------
@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    glucose = int(data["glucose"])
    hours = int(data["hours"])
    insulin = int(data["insulin"])
    activity = {"low": 0, "medium": 1, "high": 2}[data["activity"]]

    prev = glucose + random.randint(-20, 20)
    slope = glucose - prev

    features = [[glucose, hours, activity, insulin, slope]]

    # ---- MODEL PREDICTION ----
    risk_class = model.predict(features)[0]
    probs = model.predict_proba(features)[0]

    # ✅ TRUE AI CONFIDENCE
    confidence = round(probs[risk_class] * 100, 2)
    score = int(confidence)

    # ---- RESULT TEXT ----
    if risk_class == 2:
        result = "HIGH RISK 🚨"
        suggestion = "Take sugar immediately"
        food = "Drink fruit juice or glucose tablets"

    elif risk_class == 1:
        result = "MEDIUM RISK ⚠️"
        suggestion = "Eat something soon"
        food = "Have biscuits or a banana"

    else:
        result = "LOW RISK ✅"
        suggestion = "You're safe"
        food = "Maintain normal diet"

    # ---- AI INSIGHT ----
    insight = generate_ai_insight(glucose, hours, activity, insulin, slope)

    # ---------- SAVE 30 DAYS HISTORY ----------
    history = load_history()
    user = session["user"]

    if user not in history:
        history[user] = []

    history[user].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "glucose": glucose,
        "score": score,
        "result": result,
        "insight": insight
    })

    history[user] = history[user][-300:]
    save_history(history)

    return jsonify({
        "result": result,
        "score": score,
        "confidence": confidence,
        "suggestion": suggestion,
        "food": food,
        "insight": insight,
        "history": history[user]
    })

# ---------- FETCH HISTORY ----------
@app.route("/history")
def get_history():
    if "user" not in session:
        return jsonify([])
    history = load_history()
    return jsonify(history.get(session["user"], []))

# ---------- HISTORY PAGE ----------
@app.route("/history-page")
def history_page():
    if "user" not in session:
        return redirect("/")
    return render_template("history.html")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
