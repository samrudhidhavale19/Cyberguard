from flask import Flask, request, jsonify # pyright: ignore[reportMissingImports]
from flask_cors import CORS # pyright: ignore[reportMissingModuleSource]
import sqlite3

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

# ---------------- SQLITE CONNECTION ----------------
db = sqlite3.connect('cyberguard.db', check_same_thread=False)
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Create tables if not exist
cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    description TEXT NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS check_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    result TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)''')

db.commit()

# ---------------- SCAM MODEL ----------------
from sklearn.feature_extraction.text import CountVectorizer # pyright: ignore[reportMissingModuleSource]
from sklearn.naive_bayes import MultinomialNB # pyright: ignore[reportMissingModuleSource]

texts = [
    "you won lottery", "free money now", "urgent click link",
    "bank password needed", "claim your prize",
    "hello friend", "let's meet tomorrow", "how are you"
]

labels = [1,1,1,1,1,0,0,0]

vectorizer = CountVectorizer()
X = vectorizer.fit_transform(texts)

model = MultinomialNB()
model.fit(X, labels)

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    return app.send_static_file(path)

# ---------------- CHECK API ----------------
@app.route('/api/check', methods=['POST'])
def check():
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({"error": "Message required"}), 400

    msg = data['message'].strip()

    if msg == "":
        return jsonify({"error": "Empty message"}), 400

    X_test = vectorizer.transform([msg])
    pred = model.predict(X_test)[0]

    return jsonify({
        "result": "scam" if pred == 1 else "safe"
    })

# ---------------- REPORT API ----------------
@app.route('/api/reports', methods=['POST'])
def report():
    data = request.get_json()

    name = data.get('name', '').strip()
    contact = data.get('contact', '').strip()
    description = data.get('description', '').strip()

    if not name or not contact or not description:
        return jsonify({"error": "All fields required"}), 400

    sql = "INSERT INTO reports (name, contact, description) VALUES (?, ?, ?)"
    values = (name, contact, description)

    cursor.execute(sql, values)
    db.commit()

    return jsonify({"status": "saved"})

@app.route('/api/reports', methods=['GET'])
def get_reports():
    cursor.execute("SELECT * FROM reports")
    data = cursor.fetchall()
    return jsonify([dict(row) for row in data])

# ---------------- SAVE CHECK RESULT ----------------
@app.route('/api/save', methods=['POST'])
def save_check():
    data = request.get_json()

    message = data.get('message', '').strip()
    result = data.get('result', '').strip()

    if not message or not result:
        return jsonify({"error": "Message and result required"}), 400

    sql = "INSERT INTO check_results (message, result) VALUES (?, ?)"
    values = (message, result)

    cursor.execute(sql, values)
    db.commit()

    return jsonify({"status": "saved"})

# ---------------- LOGIN SYSTEM ----------------
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Required fields missing"}), 400

    try:
        sql = "INSERT INTO users (username, password) VALUES (?,?)"
        cursor.execute(sql, (username, password))
        db.commit()
        return jsonify({"status": "created"})

    except sqlite3.IntegrityError:
        return jsonify({"status": "user exists"}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    sql = "SELECT * FROM users WHERE username=? AND password=?"
    cursor.execute(sql, (username, password))
    user = cursor.fetchone()

    if user:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"}), 401

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
