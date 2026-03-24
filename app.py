from flask import Flask, request, redirect, session
import sqlite3
import time

app = Flask(__name__)
app.secret_key = "secret"

# 🔐 PIN + RESET
PIN = "1234"
ANSWER = "mydog"

# DB
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS photos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT,
hidden INTEGER DEFAULT 0
)
""")
conn.commit()

# ⏱️ AUTO LOCK
def check_login():
    if session.get("ok") and time.time() - session.get("time",0) < 60:
        return True
    session.clear()
    return False

# 🔐 LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["pin"] == PIN:
            session["ok"] = True
            session["time"] = time.time()
            return redirect("/vault")
        else:
            return "❌ Wrong PIN"

    return '''
    <h2>🔐 Enter PIN</h2>
    <form method="post">
    <input name="pin"><br><br>
    <button>Enter</button>
    </form>
    <br><a href="/reset">Reset PIN</a>
    '''

# 📸 VAULT
@app.route("/vault", methods=["GET","POST"])
def vault():
    if not check_login():
        return redirect("/")

    session["time"] = time.time()

    if request.method == "POST":
        url = request.form["url"]
        cursor.execute("INSERT INTO photos (url,hidden) VALUES (?,0)", (url,))
        conn.commit()

    cursor.execute("SELECT * FROM photos")
    data = cursor.fetchall()

    html = "<h2>📸 Vault</h2>"
    html += '''
    <form method="post">
    <input name="url" placeholder="Image URL"><br><br>
    <button>Add</button>
    </form>
    <a href="/hidden">🔐 Hidden Files</a><br>
    <a href="/logout">Logout</a><br><br>
    '''

    for row in data:
        if row[2] == 0:
            html += f"""
            <img src="{row[1]}" width="120"><br>
            <a href="/hide/{row[0]}">Hide</a><br><br>
            """

    return html

# 🙈 HIDE
@app.route("/hide/<int:id>")
def hide(id):
    if not check_login():
        return redirect("/")
    cursor.execute("UPDATE photos SET hidden=1 WHERE id=?", (id,))
    conn.commit()
    return redirect("/vault")

# 🔐 HIDDEN PAGE
@app.route("/hidden")
def hidden():
    if not check_login():
        return redirect("/")

    cursor.execute("SELECT * FROM photos WHERE hidden=1")
    data = cursor.fetchall()

    html = "<h2>🔐 Hidden Files</h2>"
    html += '<a href="/vault">⬅ Back</a><br><br>'

    for row in data:
        html += f"""
        <img src="{row[1]}" width="120"><br>
        <a href="/unhide/{row[0]}">🔓 Unhide</a> |
        <a href="/delete/{row[0]}">🗑 Delete</a><br><br>
        """

    return html

# 🔓 UNHIDE
@app.route("/unhide/<int:id>")
def unhide(id):
    if not check_login():
        return redirect("/")
    cursor.execute("UPDATE photos SET hidden=0 WHERE id=?", (id,))
    conn.commit()
    return redirect("/hidden")

# 🗑 DELETE
@app.route("/delete/<int:id>")
def delete(id):
    if not check_login():
        return redirect("/")
    cursor.execute("DELETE FROM photos WHERE id=?", (id,))
    conn.commit()
    return redirect("/hidden")

# 🔁 RESET PIN (OLD PIN + ANSWER)
@app.route("/reset", methods=["GET","POST"])
def reset():
    global PIN
    if request.method == "POST":
        if request.form["old"] == PIN and request.form["ans"] == ANSWER:
            PIN = request.form["new"]
            session.clear()
            return "✅ PIN Changed"
        else:
            return "❌ Wrong"

    return '''
    <h2>Reset PIN</h2>
    <form method="post">
    <input name="old" placeholder="Old PIN"><br><br>
    <input name="ans" placeholder="Answer"><br><br>
    <input name="new" placeholder="New PIN"><br><br>
    <button>Reset</button>
    </form>
    '''

# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ▶️ RUN
app.run(host="0.0.0.0", port=10000)
