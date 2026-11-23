#Lecture Slides Class 5 pg 44: Edits = import "services" instead of "models"and changed the name of the file to servic es.py instead of models.py as claude pointed out that the folder is already named models,
#names of the html templates were changed to match the names of the html templates in the templates folder,

import logging
import os
from flask import (Flask, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)


import db
import services
import api
from config import CONFIGS

app = Flask(__name__)
app_env = os.getenv("APP_ENV", "development")
app.config.from_object(CONFIGS.get(app_env, CONFIGS["development"]))
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(os.path.join(LOG_DIR, "app.log")),
              logging.StreamHandler()],
)
log = logging.getLogger("hpc")

db.init_app(app)
app.register_blueprint(api.bp)

@app.after_request
def log_failed_requests(response):
    """Record every request that ended in an error (status 400 or higher)."""
    if response.status_code >= 400:
        log.warning("%s %s -> %s", request.method, request.full_path,
                    response.status_code)
    return response

def _is_api_request():
    """True for URLs under /api/: those callers expect JSON, not a web page."""
    return request.path.startswith("/api/")


@app.errorhandler(404)
def not_found(error):
    """Unknown URL or record: JSON for the API, a friendly page otherwise."""
    if _is_api_request():
        return jsonify(error="Not found."), 404
    return render_template("error.html", code=404,
                           message="That page does not exist."), 404


@app.errorhandler(400)
def bad_request(error):
    """Invalid input that reached Flask's own checks (e.g. broken JSON)."""
    if _is_api_request():
        return jsonify(error="Bad request: check the data you sent."), 400
    return render_template("error.html", code=400,
                           message="Something in your request was not valid."), 400


@app.errorhandler(500)
def server_error(error):
    """Unexpected crash: undo half-finished database work, log it, hide the details."""
    if "db" in g:
        g.db.rollback()
    log.exception("Unhandled error on %s %s", request.method, request.path)
    if _is_api_request():
        return jsonify(error="Internal server error."), 500
    return render_template("error.html", code=500,
                           message="Something went wrong on our side."), 500


@app.route("/")
def index():
    stats = services.dashboard_stats()
    return render_template("home.html", stats=stats)

@app.route("/live")
def live():
    search = request.args.get("q", "").strip()
    carrier_id = request.args.get("carrier", type=int)
    return render_template("live.html",
                           deliveries=services.list_deliveries(search, carrier_id),
                           carriers=services.list_carriers(),
                           stats=services.dashboard_stats(),
                           search=search, carrier_id=carrier_id)

@app.context_processor
def inject_alert_count():
    """Number of breaches still waiting for a reason, for the sidebar badge."""
    return dict(alert_count=len(services.breach_alerts()["new"]))


@app.route("/alerts")
def alerts():
    return render_template("alerts.html", alerts=services.breach_alerts(),
                           reasons=services.REASON_CODES)


@app.route("/deliveries/<int:delivery_id>/exception", methods=["POST"])
def delivery_exception(delivery_id):
    """Update flow (Class 5 slides 53-56): save a reason code on a breached delivery."""
    if services.get_delivery(delivery_id) is None:
        flash("Delivery not found.", "error")
        return redirect(url_for("alerts"))
    ok, message = services.update_delivery_note(delivery_id, request.form.get("reason"))
    flash(message, "success" if ok else "error")
    return redirect(url_for("alerts"))

@app.route("/gatelog")
def gatelog():
    return render_template("gatelog.html", events=services.list_scan_events(),
                           trucks=services.list_trucks(),
                           locations=services.SCAN_LOCATIONS)

@app.route("/scans", methods=["POST"])
def scan_create():
    """Create flow (Class 5 slides 63-66): record one RFID gate scan."""
    ok, message, delivery_id = services.record_scan(
        request.form.get("truck_code"),
        request.form.get("location"),
        request.form.get("reader_id"))
    flash(message, "success" if ok else "error")
    return redirect(url_for("gatelog"))

@app.route("/reports")
def reports():
    return render_template("reports.html",
                           by_carrier=services.compliance_by("carrier"),
                           by_truck=services.compliance_by("truck"),
                           summary=services.report_summary(),
                           days=services.compliance_by_day())

@app.route("/capacity")
def capacity():
    """BYD capacity scenario: read the form (GET), validate, run models/capacity.py."""
    values, errors = services.read_capacity_inputs(request.args)
    result = services.run_capacity_scenario(values)
    return render_template("capacity.html", values=values, result=result,
                           errors=errors)

@app.before_request
def require_login():
    """Every page needs a signed-in user, except the login page, static files and the API."""
    if request.endpoint in ("login", "static") or request.path.startswith("/api/"):
        return None
    if not session.get("user"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if (username == app.config["DEMO_USER"]
                and password == app.config["DEMO_PASSWORD"]):
            session.clear()
            session["user"] = username
            flash(f"Signed in as {username}.", "success")
            return redirect(url_for("index"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))

#Lecture Slides Class 4 pg 7
if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])