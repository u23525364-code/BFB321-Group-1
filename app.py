from flask import Flask, redirect, render_template, url_for

app = Flask(__name__)

# Sidebar navigation, grouped into sections. base.html renders this on every page.
NAV_SECTIONS = [
    ("Overview", [
        {"endpoint": "home", "label": "Home", "icon": "bi-grid-1x2"},
    ]),
    ("Operations", [
        {"endpoint": "live", "label": "Live deliveries", "icon": "bi-broadcast"},
        {"endpoint": "alerts", "label": "Breach alerts", "icon": "bi-bell", "count": 4},
        {"endpoint": "gatelog", "label": "Gate log", "icon": "bi-upc-scan"},
    ]),
    ("Planning", [
        {"endpoint": "reports", "label": "Reports", "icon": "bi-bar-chart-line"},
        {"endpoint": "capacity", "label": "Capacity", "icon": "bi-sliders"},
    ]),
]


@app.context_processor
def inject_nav():
    return {"nav_sections": NAV_SECTIONS}


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/live")
def live():
    return render_template("live.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/alerts")
def alerts():
    return render_template("alerts.html")


@app.route("/capacity")
def capacity():
    return render_template("capacity.html")


@app.route("/gatelog")
def gatelog():
    return render_template("gatelog.html")


if __name__ == "__main__":
    app.run(debug=True)
