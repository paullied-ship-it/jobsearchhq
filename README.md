# Job Search HQ

A local Streamlit app for managing your job search — daily routine tracker, application pipeline, and automated multi-source job search with email digests.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

### 📋 Daily Routine
- Checkboxes for each step in your daily job search routine
- Step 3 (verification) highlighted as a reminder to confirm roles are still live
- Auto-rotating search string — changes daily to keep searches fresh
- Verification checklist and quick links to all major job boards

### 📝 Application Tracker
- Track applications with company, role, URL, status, compensation, and notes
- Filter and search your pipeline
- Update status inline (Watching → Applied → Interview → Offer / Rejected)
- Summary metrics dashboard
- Data saved locally to `data/applications.json`

### 🔍 Job Search
- Searches WeWorkRemotely, Remote.co, Jobicy, and LinkedIn simultaneously
- Scores each role 0–100 based on keyword fit against your target profile
- Filters out roles older than 14 days automatically
- One-click "Track it" button adds any role to your Application Tracker
- Optional email digest via Gmail App Password

### ⏳ Countdown Timer
- Configurable target date pill in the header — set your own job search deadline

---

## Setup

### Requirements
- Python 3.9+
- pip

### Install
```bash
git clone https://github.com/yourusername/jobsearchhq.git
cd jobsearchhq
pip install -r requirements.txt
```

### Configure
Edit `config.json` to personalize the app:

```json
{
  "user_name": "Your Name",
  "target_date": "2026-12-31",
  "target_date_label": "My Deadline",
  "email_sender": "you@gmail.com",
  "email_recipient": "you@gmail.com",
  "search_queries": [
    "Director of Operations remote",
    "Head of Operations remote"
  ],
  "positive_keywords": ["kpi", "sop", "vendor management"],
  "negative_keywords": ["oil and gas", "mining"]
}
```

| Field | Description |
|---|---|
| `user_name` | Displayed in the app header |
| `target_date` | Countdown target (YYYY-MM-DD) |
| `target_date_label` | Label shown above the timer |
| `email_sender` | Gmail address to send from |
| `email_recipient` | Email address to receive digests |
| `search_queries` | Job search strings (customize to your target roles) |
| `positive_keywords` | Keywords that raise a job's fit score |
| `negative_keywords` | Keywords that lower a job's fit score |

### Run
```bash
streamlit run app.py
```

Opens automatically at `http://localhost:8501`

---

## Email Digests (optional)

The app can email you a daily digest of top matches using Gmail.

**Step 1 — Enable 2-Step Verification**
Go to [myaccount.google.com/security](https://myaccount.google.com/security)

**Step 2 — Create a Gmail App Password**
Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), create a password for "Mail"

**Step 3 — Set the environment variable**

Mac/Linux:
```bash
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

Windows:
```cmd
setx GMAIL_APP_PASSWORD "xxxx xxxx xxxx xxxx"
```

**Step 4 — Restart the app**

The app will detect the password and enable the email button automatically.

---

## Scheduled Daily Search (Windows)

To run the search automatically every morning:

1. Download `setup_scheduler.bat`
2. Edit the path inside to match where you saved the project
3. Right-click → **Run as administrator**

This registers a Windows Task Scheduler job that runs `job_search.py` at 9AM daily and sends the email digest — whether the Streamlit app is open or not.

---

## Desktop Shortcut (Windows)

Create a `.bat` file:
```bat
@echo off
cd /d "C:\path\to\jobsearchhq"
start "" "http://localhost:8501"
python -m streamlit run app.py
pause
```

Right-click → **Send to → Desktop (create shortcut)**

---

## Data & Privacy

- All application data is stored locally in `data/applications.json`
- `data/` is in `.gitignore` — your personal pipeline data will never be committed
- No external services, no accounts, no telemetry beyond Streamlit's built-in analytics

---

## Customizing the Job Search

The scoring system in `job_search.py` is fully configurable via `config.json`:

- **positive_keywords** — terms that increase a job's fit score (+5 each)
- **negative_keywords** — terms that decrease a job's fit score (-15 each)
- **search_queries** — the queries sent to each source

Tune these to your background and target roles for better signal-to-noise.

---

## Contributing

PRs welcome. Ideas for improvement:
- Additional job board RSS sources
- Better LinkedIn scraping
- Slack/Teams notification support
- Resume keyword matching
- Interview prep tracker

---

## License

MIT — see [LICENSE](LICENSE)
