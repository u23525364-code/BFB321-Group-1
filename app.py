#Lecture Slides Class 5 pg 44: Edits = import "services" instead of "models"and changed the name of the file to servic es.py instead of models.py as claude pointed out that the folder is already named models,
#names of the html templates were changed to match the names of the html templates in the templates folder,

import os
from flask import (Flask, flash, redirect, render_template,
                   request, url_for)

import db
import services

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY",
                                     "dev-only-change-me")

db.init_app(app)

@app.route("/")
def index():
    stats = services.dashboard_stats()
    return render_template("home.html", stats=stats)

@app.route("/live")
def live():
    return render_template("live.html")

@app.route("/alerts")
def alerts():
    return render_template("alerts.html")

@app.route("/gatelog")
def gatelog():
    return render_template("gatelog.html", events=services.list_scan_events())

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/capacity")
def capacity():
    return render_template("capacity.html")

@app.route("/login")
def login():
    return render_template("login.html")

#Lecture Slides Class 4 pg 7
if __name__ == "__main__":
    app.run(debug=True)