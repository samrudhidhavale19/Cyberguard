from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect('cyberguard.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # ✅ DO NOT DROP TABLE (IMPORTANT FIX)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS check_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    return app.send_static_file(path)

# ---------------- SAVE REPORT ----------------
@app.route('/api/reports', methods=['POST'])
def save_report():
    data = request.get_json()

    name = data.get('name')
    contact = data.get('contact')
    description = data.get('description')

    print("🔥 RECEIVED:", name, contact, description)

    if not name or not contact or not description:
        return jsonify({"status": "error", "msg": "Missing data"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO reports (name, contact, description) VALUES (?, ?, ?)",
        (name, contact, description)
    )

    conn.commit()
    conn.close()

    print("✅ SAVED TO DATABASE")

    return jsonify({"status": "success"})

# ---------------- CHECK SCAM ----------------
@app.route('/api/check', methods=['POST'])
def check_scam():
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({"result": "unknown", "confidence": 0, "reasons": []}), 400

    normalized = message.lower()
    score = 0
    reasons = []

    if 'http' in normalized or 'www' in normalized:
        score += 3
        reasons.append("Contains suspicious link")

    suspicious_words = ['urgent', 'password', 'otp', 'winner', 'lottery', 'bank', 'account', 'verify']
    for word in suspicious_words:
        if word in normalized:
            score += 2
            reasons.append(f"Suspicious word: {word}")

    if score >= 5:
        result = "scam"
        confidence = min(score * 10, 100)
    elif score >= 2:
        result = "suspicious"
        confidence = score * 10
    else:
        result = "safe"
        confidence = 100 - score * 5

    return jsonify({"result": result, "confidence": confidence, "reasons": reasons})

# ---------------- SAVE CHECK RESULT ----------------
@app.route('/api/check_results', methods=['POST'])
def save_check_result():
    data = request.get_json()

    message = data.get('message')
    result = data.get('result')

    if not message or not result:
        return jsonify({"status": "error", "msg": "Missing data"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO check_results (message, result) VALUES (?, ?)",
        (message, result)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

# ---------------- GET REPORTS ----------------
@app.route('/api/reports', methods=['GET'])
def get_reports():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports ORDER BY id DESC")
    rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({
            "id": row["id"],
            "name": row["name"],
            "contact": row["contact"],
            "description": row["description"]
        })

    conn.close()
    return jsonify(data)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)