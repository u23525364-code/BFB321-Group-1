# BFB321-Semester-Project

HPC delivery takt-time dashboard (Flask + Bootstrap 5.3).

## Running the dashboard

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 (redirects to the login page).

## Page formatting

Every page in `templates/` extends `base.html` and uses the Halfway theme
(`static/css/halfway-theme.css`) plus the shared components in `static/css/style.css`.
The rules are in `.claude/skills/halfway-dashboard/SKILL.md`.
