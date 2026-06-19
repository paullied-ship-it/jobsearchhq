import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="Job Search HQ",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FILE = Path("data/applications.json")
DATA_FILE.parent.mkdir(exist_ok=True)

# ── Load config ───────────────────────────────────────────────────────────────
CONFIG_FILE = Path("config.json")
def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {
        "target_date": "2026-12-31",
        "target_date_label": "My Target Date",
        "user_name": "Job Seeker",
        "target_titles": [
            "Director of Operations",
            "Head of Operations",
            "VP of Operations",
            "General Manager",
        ]
    }

config = load_config()

def load_apps():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return []

def save_apps(apps):
    with open(DATA_FILE, "w") as f:
        json.dump(apps, f, indent=2)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4 { color: #f0f2f6; }
p, label, .stMarkdown { color: #c9cdd4; }
.timer-pill {
    display: inline-flex; align-items: center;
    background: linear-gradient(135deg, #1a1d2e, #2a1f3d);
    border: 1px solid #6b46c1; border-radius: 999px;
    padding: 10px 24px; font-family: 'Courier New', monospace;
    font-size: 15px; font-weight: 600; color: #c084fc;
    letter-spacing: 0.05em; box-shadow: 0 0 20px rgba(107,70,193,0.3);
}
.timer-label {
    font-size: 11px; color: #9ca3af; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 4px; font-family: Arial, sans-serif;
}
.step-tile {
    background: #1c1f2e; border: 1px solid #2d3148;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 10px;
}
.step-tile.verify { border-left: 3px solid #f59e0b; }
.step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%;
    background: #2d3148; color: #9ca3af;
    font-size: 12px; font-weight: 600; margin-right: 10px;
}
.step-num.verify { background: #2d1f00; color: #f59e0b; }
.step-title { font-size: 15px; font-weight: 600; color: #f0f2f6; display: inline; }
.step-detail { font-size: 13px; color: #9ca3af; margin-top: 6px; line-height: 1.5; }
.step-time {
    float: right; font-size: 11px; background: #2d3148;
    color: #9ca3af; padding: 3px 8px; border-radius: 999px; margin-top: 2px;
}
.card {
    background: #1c1f2e; border: 1px solid #2d3148;
    border-radius: 12px; padding: 20px 22px; margin-bottom: 16px;
}
.badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.badge-applied   { background: #1e3a5f; color: #60a5fa; }
.badge-interview { background: #1a3320; color: #4ade80; }
.badge-offer     { background: #2d1f00; color: #fbbf24; }
.badge-rejected  { background: #2d1010; color: #f87171; }
.badge-watching  { background: #2a1f3d; color: #c084fc; }
.section-header {
    font-size: 11px; font-weight: 600; color: #6b7280;
    text-transform: uppercase; letter-spacing: 0.1em; margin: 1.5rem 0 0.75rem;
}
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #1c1f2e; border-radius: 8px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: #9ca3af; background: transparent; border-radius: 6px; padding: 8px 18px; font-size: 13px; }
.stTabs [aria-selected="true"] { background: #2d3148 !important; color: #f0f2f6 !important; }
.stButton > button { background: #2d3148; color: #f0f2f6; border: 1px solid #3d4268; border-radius: 8px; font-size: 13px; padding: 6px 16px; }
.stButton > button:hover { background: #3d4268; border-color: #6b46c1; color: white; }
hr { border-color: #2d3148; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Timer ─────────────────────────────────────────────────────────────────────
def render_timer():
    target_date  = config.get("target_date", "2026-12-31")
    target_label = config.get("target_date_label", "Target Date")
    components.html(f"""
    <style>
      body {{ margin:0; padding:0; background:transparent; }}
      .timer-label {{ font-size:11px; color:#9ca3af; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:4px; font-family:Arial,sans-serif; }}
      .timer-pill {{ display:inline-flex; align-items:center;
                     background:linear-gradient(135deg,#1a1d2e,#2a1f3d);
                     border:1px solid #6b46c1; border-radius:999px; padding:10px 24px;
                     font-family:'Courier New',monospace; font-size:15px; font-weight:600;
                     color:#c084fc; letter-spacing:0.05em;
                     box-shadow:0 0 20px rgba(107,70,193,0.3); }}
    </style>
    <div class="timer-label">Time until {target_label}</div>
    <div class="timer-pill" id="cd">loading...</div>
    <script>
      var target = new Date("{target_date}T00:00:00");
      function tick() {{
        var now  = new Date();
        var diff = target - now;
        if (diff <= 0) {{ document.getElementById("cd").innerHTML = "Target date reached!"; return; }}
        var d = Math.floor(diff / 86400000);
        var h = Math.floor((diff % 86400000) / 3600000);
        var m = Math.floor((diff % 3600000)  / 60000);
        var s = Math.floor((diff % 60000)    / 1000);
        document.getElementById("cd").innerHTML =
          d + "d &nbsp; " + String(h).padStart(2,"0") + "h &nbsp; " +
          String(m).padStart(2,"0") + "m &nbsp; " + String(s).padStart(2,"0") + "s";
      }}
      tick(); setInterval(tick, 1000);
    </script>
    """, height=75)

# ── Constants ─────────────────────────────────────────────────────────────────
STEPS = [
    {"num": "1", "title": "Run fresh searches",
     "detail": "Job boards + 1 rotated search string · Indeed + Glassdoor alerts · Google Jobs · Wellfound",
     "time": "15 min", "verify": False},
    {"num": "2", "title": "Build your shortlist — 3 to 5 roles",
     "detail": "Skim for title, comp, and fit. Flag anything worth verifying before going deeper.",
     "time": "5 min", "verify": False},
    {"num": "3", "title": "Verify each role is still live",
     "detail": "Check posting date (< 30 days) · Go direct to company careers page · Aggregators cache stale listings.",
     "time": "5-10 min", "verify": True},
    {"num": "4", "title": "Apply to confirmed live roles",
     "detail": "Tailor your cover letter to each role · 2-3 max per day · Quality over volume.",
     "time": "variable", "verify": False},
    {"num": "5", "title": "Daily outreach",
     "detail": "One warm message to someone at a target company. Compounds over time.",
     "time": "5 min", "verify": False},
]

SEARCH_STRINGS = [
    '"Director of Operations" remote',
    '"Head of Operations" startup',
    '"VP of Operations" fintech OR logistics OR SaaS',
    '"Chief of Staff" operations OR COO',
    '"Director of Continuous Improvement" OR "Lean Six Sigma"',
    '"General Manager" operations remote',
    '"Director" "KPI" "process improvement" "scale"',
]

STATUS_OPTIONS = ["Watching", "Applied", "Interview", "Offer", "Rejected"]
STATUS_BADGE = {
    "Watching":  "badge-watching",
    "Applied":   "badge-applied",
    "Interview": "badge-interview",
    "Offer":     "badge-offer",
    "Rejected":  "badge-rejected",
}

# ── Header ────────────────────────────────────────────────────────────────────
col_head, col_timer = st.columns([3, 2])
with col_head:
    st.markdown("## 🎯 &nbsp; Job Search HQ")
    st.caption("Welcome back, " + config.get("user_name", "Job Seeker"))
with col_timer:
    st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
    render_timer()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📋 &nbsp; Daily Routine", "📝 &nbsp; Application Tracker", "🔍 &nbsp; Job Search"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Daily Routine
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_steps, col_search = st.columns([3, 2])

    with col_steps:
        st.markdown('<div class="section-header">Today\'s checklist</div>', unsafe_allow_html=True)
        if "completed" not in st.session_state:
            st.session_state.completed = {str(i): False for i in range(1, 6)}
        if all(st.session_state.completed.values()):
            st.success("All steps complete for today — great work!")
        for i, step in enumerate(STEPS):
            key        = str(i + 1)
            tile_class = "step-tile verify" if step["verify"] else "step-tile"
            num_class  = "step-num verify"  if step["verify"] else "step-num"
            opacity    = "0.45" if st.session_state.completed.get(key) else "1"
            col_check, col_tile = st.columns([0.08, 0.92])
            with col_check:
                checked = st.checkbox(
                    label=step["title"], value=st.session_state.completed.get(key, False),
                    key="step_" + key, label_visibility="collapsed"
                )
                st.session_state.completed[key] = checked
            with col_tile:
                st.markdown(
                    '<div class="' + tile_class + '" style="opacity:' + opacity + '">'
                    '<span class="' + num_class + '">' + step["num"] + '</span>'
                    '<span class="step-title">' + step["title"] + '</span>'
                    '<span class="step-time">' + step["time"] + '</span>'
                    '<div class="step-detail">' + step["detail"] + '</div>'
                    '</div>', unsafe_allow_html=True
                )
        if st.button("Reset checklist"):
            for k in st.session_state.completed:
                st.session_state.completed[k] = False
            st.rerun()

    with col_search:
        st.markdown('<div class="section-header">Today\'s search string</div>', unsafe_allow_html=True)
        day_idx = datetime.now().weekday() % len(SEARCH_STRINGS)
        st.code(SEARCH_STRINGS[day_idx], language=None)
        st.caption("Rotates daily. Copy and use across all platforms.")

        st.markdown('<div class="section-header">Verification checklist</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div style="font-size:13px; line-height:1.9; color:#c9cdd4">
            Posted within 30 days?<br>
            Role on company careers page?<br>
            Verified original source (not just aggregator)?<br>
            ATS link live? (Greenhouse / Lever / Ashby)
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">Quick links</div>', unsafe_allow_html=True)
        links = {
            "LinkedIn Jobs":  "https://www.linkedin.com/jobs/",
            "Indeed":         "https://www.indeed.com",
            "Wellfound":      "https://wellfound.com/jobs",
            "Google Jobs":    "https://www.google.com/search?q=Director+of+Operations+remote+jobs",
            "Glassdoor":      "https://www.glassdoor.com/Job/remote-director-operations-jobs-SRCH_IL.0,6_IS11047_KO7,26.htm",
            "Google Alerts":  "https://www.google.com/alerts",
        }
        cols = st.columns(2)
        for i, (name, url) in enumerate(links.items()):
            with cols[i % 2]:
                st.link_button(name, url, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Application Tracker
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    apps = load_apps()
    col_form, col_list = st.columns([2, 3])

    with col_form:
        st.markdown('<div class="section-header">Add application</div>', unsafe_allow_html=True)
        with st.form("add_app", clear_on_submit=True):
            company  = st.text_input("Company *")
            role     = st.text_input("Role / Title *")
            url      = st.text_input("Job URL")
            status   = st.selectbox("Status", STATUS_OPTIONS)
            comp     = st.text_input("Compensation (est.)")
            notes    = st.text_area("Notes", height=100,
                                    placeholder="Requirements, contacts, follow-up dates...")
            submitted = st.form_submit_button("Add Application", use_container_width=True)
            if submitted:
                if company and role:
                    apps.append({
                        "id":      datetime.now().isoformat(),
                        "company": company,
                        "role":    role,
                        "url":     url,
                        "status":  status,
                        "comp":    comp,
                        "notes":   notes,
                        "date":    datetime.now().strftime("%b %d, %Y"),
                    })
                    save_apps(apps)
                    st.success("Added " + company)
                    st.rerun()
                else:
                    st.error("Company and role are required.")

        st.markdown("---")
        st.markdown('<div class="section-header">Summary</div>', unsafe_allow_html=True)
        if apps:
            cols = st.columns(len(STATUS_OPTIONS))
            for i, s in enumerate(STATUS_OPTIONS):
                with cols[i]:
                    st.metric(s, sum(1 for a in apps if a["status"] == s))
        else:
            st.caption("No applications yet.")

    with col_list:
        st.markdown('<div class="section-header">Your applications</div>', unsafe_allow_html=True)
        if not apps:
            st.info("No applications tracked yet. Add your first one!")
        else:
            filter_status = st.multiselect(
                "Filter", STATUS_OPTIONS, default=STATUS_OPTIONS, label_visibility="collapsed"
            )
            search_term = st.text_input(
                "Search", label_visibility="collapsed", placeholder="Search company or role..."
            )
            filtered = [
                a for a in apps
                if a["status"] in filter_status
                and (search_term.lower() in a["company"].lower()
                     or search_term.lower() in a["role"].lower())
            ]
            filtered.sort(key=lambda x: x["id"], reverse=True)
            for app in filtered:
                badge_class = STATUS_BADGE.get(app["status"], "badge-watching")
                with st.expander(app["company"] + " — " + app["role"], expanded=False):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            '<span class="badge ' + badge_class + '">' + app["status"] + '</span>',
                            unsafe_allow_html=True
                        )
                        if app.get("comp"):    st.caption("Comp: " + app["comp"])
                        if app.get("url"):     st.markdown("[View posting](" + app["url"] + ")")
                        st.caption("Added: " + app.get("date", "N/A"))
                        if app.get("notes"):
                            st.markdown("**Notes:**")
                            st.markdown(
                                "<div style='font-size:13px;color:#9ca3af'>" + app["notes"] + "</div>",
                                unsafe_allow_html=True
                            )
                    with c2:
                        new_status = st.selectbox(
                            "Status", STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(app["status"]),
                            key="status_" + app["id"]
                        )
                        if new_status != app["status"]:
                            for a in apps:
                                if a["id"] == app["id"]:
                                    a["status"] = new_status
                            save_apps(apps)
                            st.rerun()
                        if st.button("Delete", key="del_" + app["id"]):
                            apps = [a for a in apps if a["id"] != app["id"]]
                            save_apps(apps)
                            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Job Search
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    import importlib.util

    SEARCH_SCRIPT = Path("job_search.py")
    RESULTS_FILE  = Path("data/search_results.json")

    def load_results():
        if RESULTS_FILE.exists():
            with open(RESULTS_FILE) as f:
                return json.load(f)
        return []

    def run_job_search():
        spec = importlib.util.spec_from_file_location("job_search", SEARCH_SCRIPT)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.run_search(), mod

    col_left, col_right = st.columns([2, 3])

    with col_left:
        st.markdown('<div class="section-header">Search controls</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div style="font-size:13px;color:#c9cdd4;line-height:1.8">
            Searches multiple remote job boards simultaneously.<br><br>
            Scores each role 0–100 based on keyword fit.<br><br>
            Filters out roles older than 14 days automatically.
            </div>
        </div>
        """, unsafe_allow_html=True)

        run_btn   = st.button("Run Job Search Now", use_container_width=True, type="primary")
        email_btn = st.button("Re-send Last Digest Email", use_container_width=True)

        results = load_results()
        if results:
            last_run = results[0].get("fetched_at", "")
            if last_run:
                try:
                    dt = datetime.fromisoformat(last_run)
                    st.caption("Last run: " + dt.strftime("%b %d at %I:%M %p"))
                except Exception:
                    pass
            st.metric("Roles found", len(results))
            st.metric("Strong matches (60+)", sum(1 for r in results if r["score"] >= 60))

        st.markdown('<div class="section-header">Email setup</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:12px;color:#9ca3af;line-height:1.8">
        To enable email digests, set your Gmail App Password:<br>
        <code style="background:#161824;padding:2px 6px;border-radius:4px;color:#c084fc">
        setx GMAIL_APP_PASSWORD "xxxx xxxx xxxx xxxx"</code><br>
        Then restart the app. See README for full setup instructions.
        </div>
        """, unsafe_allow_html=True)

        app_pw_set = bool(os.environ.get("GMAIL_APP_PASSWORD", ""))
        if app_pw_set:
            st.success("Gmail App Password detected")
        else:
            st.warning("Gmail App Password not set")

    with col_right:
        st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)

        if run_btn:
            if not SEARCH_SCRIPT.exists():
                st.error("job_search.py not found. Make sure it is in the same folder as app.py.")
            else:
                with st.spinner("Searching for fresh roles..."):
                    try:
                        results, mod = run_job_search()
                        st.success("Found " + str(len(results)) + " fresh roles!")
                        if app_pw_set:
                            mod.send_email(results)
                    except Exception as e:
                        st.error("Search error: " + str(e))
                st.rerun()

        if email_btn and not run_btn:
            results = load_results()
            if results:
                if not SEARCH_SCRIPT.exists():
                    st.error("job_search.py not found.")
                else:
                    spec = importlib.util.spec_from_file_location("job_search", SEARCH_SCRIPT)
                    mod  = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    sent = mod.send_email(results)
                    if sent:
                        st.success("Digest re-sent successfully!")
            else:
                st.info("No results to send. Run a search first.")

        results = load_results()
        if not results:
            st.markdown("""
            <div style="padding:3rem 2rem;text-align:center;color:#4b5563;
                        border:1px dashed #2d3148;border-radius:12px">
                <div style="font-size:32px;margin-bottom:12px">🔍</div>
                <div style="font-size:14px">Click <b style="color:#c084fc">Run Job Search Now</b>
                to fetch today's fresh roles.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            score_filter = st.slider("Minimum fit score", 0, 100, 50, step=5)
            filtered     = [r for r in results if r["score"] >= score_filter]
            st.caption(str(len(filtered)) + " roles at " + str(score_filter) + "+ fit score")

            for idx, job in enumerate(filtered):
                score = job["score"]
                if score >= 75:   score_color, tier = "#4ade80", "Strong fit"
                elif score >= 60: score_color, tier = "#fbbf24", "Good fit"
                else:             score_color, tier = "#9ca3af", "Possible"

                with st.expander(job["title"] + " — " + job["company"], expanded=False):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            '<span class="badge" style="background:#1c1f2e;color:' + score_color + '">'
                            + tier + " · " + str(score) + "/100</span>",
                            unsafe_allow_html=True
                        )
                        st.markdown("[View posting](" + job["link"] + ")")
                        st.caption("Source: " + job["source"] + " · " + job.get("search_label", ""))
                        if job.get("snippet"):
                            st.markdown(
                                "<div style='font-size:13px;color:#9ca3af;margin-top:6px'>"
                                + job["snippet"] + "</div>", unsafe_allow_html=True
                            )
                    with c2:
                        if st.button("Track it", key="track_" + str(idx)):
                            apps = load_apps()
                            apps.append({
                                "id":      datetime.now().isoformat(),
                                "company": job["company"],
                                "role":    job["title"],
                                "url":     job["link"],
                                "status":  "Watching",
                                "comp":    "",
                                "notes":   "Added from job search. Score: " + str(score) + "/100",
                                "date":    datetime.now().strftime("%b %d, %Y"),
                            })
                            save_apps(apps)
                            st.success("Added to tracker!")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:12px;color:#4b5563'>"
    "Job Search HQ · Built with Streamlit · Data saved locally in data/applications.json"
    "</div>",
    unsafe_allow_html=True
)
