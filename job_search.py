"""
job_search.py
Multi-source remote job search engine.
Searches WeWorkRemotely, Remote.co, Jobicy, and LinkedIn public pages.
Scores results by keyword fit, filters by recency, and sends an email digest.

Usage:
    python job_search.py              # run search + send email
    import job_search; job_search.run_search()   # call from app.py
"""

import urllib.request
import urllib.parse
import json
import smtplib
import ssl
import os
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Config (edit these or set via environment variables) ─────────────────────
# Set GMAIL_SENDER and GMAIL_RECIPIENT in config.json, or override with env vars
CONFIG_FILE  = Path("config.json")
RESULTS_FILE = Path("data/search_results.json")
RESULTS_FILE.parent.mkdir(exist_ok=True)

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

config       = load_config()
SENDER       = os.environ.get("GMAIL_SENDER",    config.get("email_sender",    "you@gmail.com"))
RECIPIENT    = os.environ.get("GMAIL_RECIPIENT", config.get("email_recipient", "you@gmail.com"))
APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Search queries ─────────────────────────────────────────────────────────────
# Customize these to match your target roles
QUERIES = config.get("search_queries", [
    "Director of Operations remote",
    "Head of Operations remote",
    "VP Operations remote",
    "Director Operations process improvement",
    "Director Continuous Improvement",
    "General Manager Operations remote",
])

# ── Scoring keywords ──────────────────────────────────────────────────────────
# Edit these lists in config.json to match your background and target roles
POSITIVE = config.get("positive_keywords", [
    "kpi", "sop", "vendor management", "field service", "distributed",
    "remote operations", "scale", "process improvement", "operational excellence",
    "deployment", "continuous improvement", "integration", "logistics",
    "startup", "growth stage", "director", "head of operations",
])

NEGATIVE = config.get("negative_keywords", [
    "revenue operations", "revops", "salesforce admin",
    "oil and gas", "mining", "autocad", "forklift",
])

OPS_TERMS = [
    "operat", "director", "head of", "vp ", "vice president", "general manager",
    "lean", "process", "logistics", "infrastructure", "vendor", "field service",
    "deployment", "continuous improvement", "kpi", "quality",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def score_job(job):
    text = (job.get("title","") + " " + job.get("snippet","") + " " + job.get("company","")).lower()
    score = 50
    for kw in POSITIVE:
        if kw in text: score += 5
    for kw in NEGATIVE:
        if kw in text: score -= 15
    for term in ["director", "head of", "vp ", "vice president"]:
        if term in job.get("title","").lower():
            score += 10; break
    if "remote" in text: score += 8
    return min(max(score, 0), 100)

def clean(text):
    text = re.sub(r"<[^>]+>", " ", text)
    for ent, rep in [("&amp;","&"),("&lt;","<"),("&gt;",">"),
                     ("&#39;","'"),("&quot;",'"'),("&nbsp;"," "),("\n"," ")]:
        text = text.replace(ent, rep)
    return re.sub(r"\s+", " ", text).strip()

def fetch_url(url, extra_headers=None):
    h = dict(HEADERS)
    if extra_headers: h.update(extra_headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=12) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def parse_rss_items(content):
    items = content.split("<item>")[1:]
    results = []
    for item in items:
        def tag(t):
            m = re.search(
                r"<" + t + r"[^>]*><!\[CDATA\[(.*?)\]\]></" + t + r">|"
                r"<" + t + r"[^>]*>(.*?)</" + t + r">", item, re.DOTALL)
            if m: return clean(m.group(1) or m.group(2) or "")
            return ""
        results.append({
            "title":   tag("title"),
            "link":    tag("link") or tag("guid"),
            "company": tag("author") or tag("dc:creator") or "",
            "snippet": tag("description")[:300],
            "date":    tag("pubDate"),
        })
    return results

def is_recent(date_str, days=14):
    if not date_str: return True
    try:
        from email.utils import parsedate_to_datetime
        pub   = parsedate_to_datetime(date_str)
        delta = datetime.now(pub.tzinfo) - pub
        return delta.days <= days
    except Exception:
        return True

def is_relevant(job):
    text = (job.get("title","") + " " + job.get("snippet","")).lower()
    return any(t in text for t in OPS_TERMS)

# ── Sources ───────────────────────────────────────────────────────────────────
def search_wwr(max_results=15):
    """We Work Remotely — management/finance RSS"""
    jobs = []
    try:
        content = fetch_url("https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss")
        for item in parse_rss_items(content)[:max_results]:
            if ":" in item["title"]:
                parts = item["title"].split(":", 1)
                item["company"] = parts[0].strip()
                item["title"]   = parts[1].strip()
            item["source"] = "WeWorkRemotely"
            if item["title"] and item["link"]:
                jobs.append(item)
    except Exception as e:
        print("  WeWorkRemotely error: " + str(e))
    return jobs

def search_remoteco(max_results=15):
    """Remote.co RSS feed"""
    jobs = []
    try:
        content = fetch_url("https://remote.co/remote-jobs/feed/")
        for item in parse_rss_items(content)[:max_results]:
            item["source"] = "Remote.co"
            if item["title"] and item["link"]:
                jobs.append(item)
    except Exception as e:
        print("  Remote.co error: " + str(e))
    return jobs

def search_jobicy(max_results=15):
    """Jobicy remote operations RSS"""
    jobs = []
    try:
        url = "https://jobicy.com/feed/remote-jobs?count=" + str(max_results) + "&tag=operations"
        content = fetch_url(url)
        for item in parse_rss_items(content)[:max_results]:
            item["source"] = "Jobicy"
            if item["title"] and item["link"]:
                jobs.append(item)
    except Exception as e:
        print("  Jobicy error: " + str(e))
    return jobs

def search_linkedin(query, max_results=5):
    """LinkedIn public job search page scrape (best effort)"""
    jobs = []
    try:
        encoded = urllib.parse.quote(query)
        url = ("https://www.linkedin.com/jobs/search?keywords=" + encoded
               + "&location=Remote&f_WT=2&f_TPR=r604800")
        content = fetch_url(url)
        cards = re.findall(
            r'<a[^>]+href="(https://www\.linkedin\.com/jobs/view/[^"]+)"[^>]*>'
            r'.*?<h3[^>]*class="[^"]*base-search-card__title[^"]*"[^>]*>(.*?)</h3>'
            r'.*?<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>(.*?)</h4>',
            content, re.DOTALL
        )
        for link, title, company in cards[:max_results]:
            jobs.append({
                "title":   clean(title),
                "company": clean(company),
                "link":    link.split("?")[0],
                "snippet": "",
                "source":  "LinkedIn",
                "date":    "",
            })
    except Exception as e:
        print("  LinkedIn error: " + str(e))
    return jobs

# ── Main runner ───────────────────────────────────────────────────────────────
def run_search():
    print("[Job Search] Starting — " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    all_jobs, seen = [], set()

    print("  Fetching LinkedIn...")
    for q in QUERIES[:3]:
        for job in search_linkedin(q):
            if job["link"] not in seen:
                all_jobs.append(job); seen.add(job["link"])

    print("  Fetching WeWorkRemotely...")
    for job in search_wwr():
        if job["link"] not in seen and is_recent(job.get("date","")):
            all_jobs.append(job); seen.add(job["link"])

    print("  Fetching Remote.co...")
    for job in search_remoteco():
        if job["link"] not in seen and is_recent(job.get("date","")):
            all_jobs.append(job); seen.add(job["link"])

    print("  Fetching Jobicy...")
    for job in search_jobicy():
        if job["link"] not in seen and is_recent(job.get("date","")):
            all_jobs.append(job); seen.add(job["link"])

    for job in all_jobs:
        job["score"]      = score_job(job)
        job["fetched_at"] = datetime.now().isoformat()

    filtered = [j for j in all_jobs if is_relevant(j)]
    filtered.sort(key=lambda x: x["score"], reverse=True)

    print("[Job Search] Found " + str(len(filtered)) + " relevant roles from "
          + str(len(all_jobs)) + " total fetched.")

    with open(RESULTS_FILE, "w") as f:
        json.dump(filtered, f, indent=2)

    return filtered

# ── Email digest ──────────────────────────────────────────────────────────────
def build_email_html(jobs):
    date_str   = datetime.now().strftime("%A, %B %d, %Y")
    top_jobs   = [j for j in jobs if j["score"] >= 60][:10]
    other_jobs = [j for j in jobs if j["score"] < 60][:5]

    def color(s):
        return "#4ade80" if s >= 75 else "#fbbf24" if s >= 60 else "#9ca3af"

    def row(job):
        c = color(job["score"])
        return (
            "<tr style='border-bottom:1px solid #2d3148'>"
            "<td style='padding:12px 8px;vertical-align:top;width:60%'>"
            "<a href='" + job["link"] + "' style='color:#60a5fa;font-weight:600;"
            "font-size:14px;text-decoration:none'>" + job["title"] + "</a><br>"
            "<span style='color:#9ca3af;font-size:12px'>" + job["company"]
            + " &nbsp;·&nbsp; " + job["source"] + "</span><br>"
            "<span style='color:#6b7280;font-size:12px'>" + job.get("snippet","")[:180] + "</span>"
            "</td>"
            "<td style='padding:12px 8px;text-align:center;width:15%'>"
            "<span style='background:#1c1f2e;color:" + c + ";padding:3px 10px;"
            "border-radius:999px;font-size:12px;font-weight:600'>" + str(job["score"]) + "</span></td>"
            "<td style='padding:12px 8px;text-align:center;width:25%'>"
            "<a href='" + job["link"] + "' style='background:#2d3148;color:#f0f2f6;"
            "padding:6px 14px;border-radius:6px;font-size:12px;text-decoration:none'>View</a></td></tr>"
        )

    top_rows   = "".join(row(j) for j in top_jobs)
    other_rows = "".join(row(j) for j in other_jobs)
    other_sec  = (
        "<h3 style='color:#9ca3af;font-size:13px;margin:24px 0 8px;"
        "text-transform:uppercase;letter-spacing:0.08em'>Also worth a look</h3>"
        "<table style='width:100%;border-collapse:collapse'>" + other_rows + "</table>"
    ) if other_rows else ""

    return (
        "<!DOCTYPE html><html><body style='background:#0f1117;color:#f0f2f6;"
        "font-family:Arial,sans-serif;padding:32px;max-width:700px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#1a1d2e,#2a1f3d);border:1px solid #6b46c1;"
        "border-radius:12px;padding:20px 28px;margin-bottom:28px'>"
        "<div style='font-size:22px;font-weight:700'>Job Search HQ — Daily Digest</div>"
        "<div style='font-size:13px;color:#9ca3af;margin-top:4px'>"
        + date_str + " &nbsp;·&nbsp; " + str(len(jobs)) + " roles found</div></div>"
        "<h3 style='color:#c084fc;font-size:13px;margin:0 0 8px;"
        "text-transform:uppercase;letter-spacing:0.08em'>Top matches (score 60+)</h3>"
        + ("<p style='color:#9ca3af;font-size:13px'>No strong matches today.</p>"
           if not top_jobs else
           "<table style='width:100%;border-collapse:collapse'>" + top_rows + "</table>")
        + other_sec
        + "<div style='margin-top:32px;padding:16px 20px;background:#1c1f2e;"
        "border-radius:8px;border-left:3px solid #f59e0b'>"
        "<div style='font-size:13px;color:#fbbf24;font-weight:600;margin-bottom:6px'>"
        "Verification reminder</div>"
        "<div style='font-size:12px;color:#9ca3af;line-height:1.7'>"
        "Confirm posting date &lt; 30 days · verify on company careers page directly · "
        "never rely solely on aggregators.</div></div>"
        "<div style='margin-top:24px;text-align:center;font-size:11px;color:#4b5563'>"
        "Job Search HQ · github.com/yourusername/jobsearchhq</div>"
        "</body></html>"
    )

def send_email(jobs):
    if not APP_PASSWORD:
        print("[Email] GMAIL_APP_PASSWORD not set — skipping email.")
        print("[Email] Set it with: setx GMAIL_APP_PASSWORD \"your app password\"")
        return False
    subject = (
        "Job Search Digest — " + datetime.now().strftime("%b %d")
        + " — " + str(len([j for j in jobs if j["score"] >= 60])) + " strong matches"
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText(build_email_html(jobs), "html"))
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(SENDER, APP_PASSWORD)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())
        print("[Email] Sent to " + RECIPIENT)
        return True
    except Exception as e:
        print("[Email] Failed: " + str(e))
        return False

if __name__ == "__main__":
    jobs = run_search()
    if jobs:
        send_email(jobs)
    else:
        print("[Job Search] No results returned.")
