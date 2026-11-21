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


def live():
    return render_template("live.html")


@app.route("/alerts")
def alerts():
    return render_template("alerts.html")


@app.route("/gatelog")
def gatelog():
    return render_template("gatelog.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/capacity")
def capacity():
    return render_template("capacity.html")


@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)

    @app.route("/live")

