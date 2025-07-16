import json
import os
import threading
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "ton_secret"

USERS_FILE = "users.json"

# Variables Timelapse (à adapter ou rendre dynamiques)
CAM_IP = "192.168.20.20"
USER = "timelapse"
PASS = "time1234"
CODE = "GotoPreset"
ARG1 = 0.1
ARG2 = -0.04
ARG3 = 0
SAVE_DIR = os.path.expanduser("~/Bureau/timelapse-chantier-MAS")

timelapse_thread = None
timelapse_running = False

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_user(username, password, role):
    users = load_users()
    if username in users:
        return False, "Utilisateur déjà existant"
    users[username] = {"password": password, "role": role}
    save_users(users)
    return True, None

def delete_user(username):
    users = load_users()
    if username not in users:
        return False, "Utilisateur non trouvé"
    del users[username]
    save_users(users)
    return True, None

def verify_user(username, password):
    users = load_users()
    user = users.get(username)
    if user and user["password"] == password:
        return True
    return False

def get_user_role(username):
    users = load_users()
    user = users.get(username)
    if user:
        return user["role"]
    return None

def timelapse_loop():
    global timelapse_running
    import datetime
    import subprocess

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    while timelapse_running:
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        if 6 <= hour <= 20 and minute == 0:
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(SAVE_DIR, f"{timestamp}.jpg")

            # Commande web PTZ
            ptz_url = f"http://{USER}:{PASS}@{CAM_IP}/cgi-bin/ptz.cgi?action=moveAbsolutely&channel=1&code={CODE}&arg1={ARG1}&arg2={ARG2}&arg3={ARG3}"
            try:
                requests.get(ptz_url, timeout=5)
                time.sleep(10)  # attente 10 secondes
                snapshot_url = f"http://{USER}:{PASS}@{CAM_IP}/cgi-bin/snapshot.cgi"
                r = requests.get(snapshot_url, timeout=10)
                if r.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(r.content)
                    print(f"Image sauvegardée: {filename}")
                else:
                    print(f"Erreur lors de la capture: HTTP {r.status_code}")
            except Exception as e:
                print(f"Erreur lors de la capture: {e}")

            time.sleep(60)  # éviter doublons
        else:
            time.sleep(30)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if verify_user(username, password):
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect"
    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    role = get_user_role(username)
    return render_template("dashboard.html", user={"username": username, "get_role": lambda: role})

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    role = get_user_role(username)
    if role != "admin":
        return "Accès refusé", 403

    users = load_users()
    message = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            uname = request.form.get("username")
            pwd = request.form.get("password")
            role_new = request.form.get("role")
            success, msg = add_user(uname, pwd, role_new)
            message = msg if not success else f"Utilisateur {uname} ajouté."
        elif action == "delete":
            uname = request.form.get("username")
            success, msg = delete_user(uname)
            message = msg if not success else f"Utilisateur {uname} supprimé."
        users = load_users()

    return render_template("admin.html", users=users, message=message)

@app.route("/control", methods=["POST"])
def control():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    role = get_user_role(username)

    if role not in ["plus", "admin"]:
        return "Accès refusé", 403

    global timelapse_running, timelapse_thread

    action = request.form.get("action")
    if action == "start":
        if not timelapse_running:
            timelapse_running = True
            timelapse_thread = threading.Thread(target=timelapse_loop, daemon=True)
            timelapse_thread.start()
    elif action == "stop":
        timelapse_running = False
        if timelapse_thread is not None:
            timelapse_thread.join(timeout=2)
            timelapse_thread = None

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
