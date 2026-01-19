from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import shutil

app = Flask(__name__)
app.secret_key = "oncf-secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE_DIR, "uploads")

# Création des dossiers principaux
for section in ["catenaire", "sousstation"]:
    os.makedirs(os.path.join(UPLOADS, section), exist_ok=True)
from werkzeug.security import generate_password_hash

print(generate_password_hash("admin123"))

USERS = {
    "admin": "admin123",
    "pro": "pro123"
}

def list_dir(base, subpath=""):
    path = os.path.join(base, subpath)
    items = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        items.append({
            "name": name,
            "is_dir": os.path.isdir(full)
        })
    return items

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        role = request.form["role"]
        password = request.form["password"]

        if role in USERS and USERS[role] == password:
            session["role"] = role
            return redirect("/")

    return render_template("index.html", role=session.get("role"))

@app.route("/browse/<section>/", defaults={"path": ""})
@app.route("/browse/<section>/<path:path>")
def browse(section, path):
    if section not in ["catenaire", "sousstation"]:
        return redirect("/")

    base = os.path.join(UPLOADS, section)
    current = os.path.join(base, path)

    if not os.path.exists(current):
        return redirect("/")

    items = list_dir(base, path)
    parent = "/".join(path.split("/")[:-1]) if path else ""

    return render_template(
        "section.html",
        role=session.get("role"),
        section=section,
        items=items,
        path=path,
        parent=parent
    )

@app.route("/create-folder", methods=["POST"])
def create_folder():
    if session.get("role") != "admin":
        return redirect("/")

    section = request.form["section"]
    path = request.form.get("path", "")
    name = request.form["name"]

    base = os.path.join(UPLOADS, section, path)
    os.makedirs(os.path.join(base, name), exist_ok=True)
    return redirect(request.referrer)

@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "admin":
        return redirect("/")

    section = request.form["section"]
    path = request.form.get("path", "")
    file = request.files["file"]

    if file:
        dest = os.path.join(UPLOADS, section, path)
        file.save(os.path.join(dest, file.filename))

    return redirect(request.referrer)

@app.route("/delete", methods=["POST"])
def delete():
    if session.get("role") != "admin":
        return redirect("/")

    section = request.form["section"]
    path = request.form.get("path", "")
    name = request.form["name"]

    target = os.path.join(UPLOADS, section, path, name)

    if os.path.isdir(target):
        shutil.rmtree(target)
    elif os.path.isfile(target):
        os.remove(target)

    return redirect(request.referrer)

@app.route("/files/<section>/<path:path>")
def files(section, path):
    return send_from_directory(os.path.join(UPLOADS, section), path)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
import zipfile
from io import BytesIO
from flask import send_file

@app.route("/download-zip/<section>/<path:path>")
def download_zip(section, path):
    base = os.path.join(UPLOADS, section, path)
    memory = BytesIO()

    with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(base):
            for f in files:
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, base)
                z.write(full_path, arcname)

    memory.seek(0)
    return send_file(memory, download_name=f"{path}.zip", as_attachment=True)


if __name__ == "__main__":
   app.run(host="0.0.0.0", port=1000)

