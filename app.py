from flask import Flask, request, redirect, session
import cloudinary
import cloudinary.uploader
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Cloudinary
cloudinary.config(
    cloud_name="dkbc4mvcm",
    api_key="655223884414587",
    api_secret="9lzc7StgLJtNnUP69bqBmgpPsII"
)

# Database
conn = sqlite3.connect("final.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (mobile TEXT PRIMARY KEY, password TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, public_id TEXT)")
conn.commit()

# SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (mobile, password))
        conn.commit()
        return redirect("/")
    return '''
    <h2>Signup</h2>
    <form method="post">
        <input name="mobile" placeholder="Mobile"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button>Signup</button>
    </form>
    '''

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM users WHERE mobile=? AND password=?", (mobile, password))
        user = cursor.fetchone()
        if user:
            session["user"] = mobile
            return redirect("/dashboard")
    return '''
    <h2>Login</h2>
    <form method="post">
        <input name="mobile" placeholder="Mobile"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button>Login</button>
    </form>
    <a href="/signup">Signup</a><br>
    <a href="/forgot">Forgot Password</a>
    '''

# FORGOT PASSWORD
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        mobile = request.form["mobile"]
        newpass = request.form["password"]
        cursor.execute("UPDATE users SET password=? WHERE mobile=?", (newpass, mobile))
        conn.commit()
        return redirect("/")
    return '''
    <h2>Reset Password</h2>
    <form method="post">
        <input name="mobile" placeholder="Mobile"><br><br>
        <input name="password" placeholder="New Password"><br><br>
        <button>Reset</button>
    </form>
    '''

# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        file = request.files["file"]
        if file:
            result = cloudinary.uploader.upload(file)
            url = result["secure_url"]
            public_id = result["public_id"]

            cursor.execute("INSERT INTO photos (url, public_id) VALUES (?,?)", (url, public_id))
            conn.commit()

    cursor.execute("SELECT * FROM photos")
    data = cursor.fetchall()

    html = "<h2>Secret Vault 🔐</h2>"
    html += '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <button>Upload</button>
    </form>
    <h3>Your Photos:</h3>
    <a href="/logout">Logout</a><br><br>
    '''

    for row in data:
        html += f"""
        <div>
            <img src='{row[1]}' width='150'><br>
            <a href='/delete/{row[0]}'>Delete ❌</a>
        </div><br>
        """

    return html

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("SELECT public_id FROM photos WHERE id=?", (id,))
    result = cursor.fetchone()

    if result:
        public_id = result[0]
        cloudinary.uploader.destroy(public_id)
        cursor.execute("DELETE FROM photos WHERE id=?", (id,))
        conn.commit()

    return redirect("/dashboard")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# RUN (LIVE READY)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)