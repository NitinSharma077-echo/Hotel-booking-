"""
AI Hotel Booking Agent — Streamlit UI
Run:  streamlit run streamlit_app.py
"""
import sys, os, json, time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import streamlit as st

# ── page config (must be first) ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Hotel Booking",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, html, body { font-family:'Inter',sans-serif; box-sizing:border-box; }
[data-testid="stAppViewContainer"] { background:#0a0c14; }
[data-testid="stSidebar"]          { display:none; }
[data-testid="stHeader"]           { background:transparent; }
[data-testid="stToolbar"]          { display:none; }

/* hero */
.hero {
    background: linear-gradient(135deg,#0d1f35 0%,#0a1628 60%,#0c1e32 100%);
    border:1px solid #1c3a58; border-radius:20px;
    padding:44px 48px 36px; margin-bottom:28px; position:relative; overflow:hidden;
}
.hero::after {
    content:''; position:absolute; bottom:-80px; right:-40px;
    width:300px; height:300px;
    background:radial-gradient(circle,rgba(79,195,247,.07) 0%,transparent 65%);
    border-radius:50%; pointer-events:none;
}
.hero h1 { color:#e4f1fb; font-size:2.3rem; font-weight:800; margin:0 0 6px; }
.hero p  { color:#6a9ec0; font-size:1rem; margin:0; }
.hero .tag {
    display:inline-block; background:rgba(79,195,247,.1); color:#4fc3f7;
    border:1px solid rgba(79,195,247,.25); border-radius:20px;
    padding:2px 12px; font-size:.75rem; font-weight:600; margin-top:14px;
}

/* section label */
.slabel {
    font-size:.7rem; font-weight:700; letter-spacing:.14em; color:#2d4a6b;
    text-transform:uppercase; margin:26px 0 10px;
    display:flex; align-items:center; gap:8px;
}
.slabel::after { content:''; flex:1; height:1px; background:#131c2e; }

/* profile saved pill */
.profile-pill {
    display:inline-flex; align-items:center; gap:6px;
    background:#071f14; border:1px solid #1a5c35; border-radius:30px;
    padding:4px 14px; font-size:.78rem; color:#4caf82; font-weight:600;
}

/* api key warning */
.api-warn {
    background:#1a1000; border:1px solid #7a4a00; border-radius:12px;
    padding:16px 20px; margin-bottom:20px;
}
.api-warn b { color:#f5a623; }
.api-warn p { color:#b07030; font-size:.88rem; margin:6px 0 0; }
.api-warn code { background:#0d0800; color:#f5a623; padding:2px 6px; border-radius:4px; font-size:.82rem; }

/* input cards */
.icard {
    background:#0f1421; border:1px solid #18243a; border-radius:14px;
    padding:24px 28px; margin-bottom:16px;
}

/* stat boxes */
.stat {
    background:#0a0e1a; border:1px solid #16213a; border-radius:12px;
    padding:18px 14px; text-align:center;
}
.stat .v { color:#4fc3f7; font-size:1.5rem; font-weight:700; line-height:1; }
.stat .l { color:#2d4a6b; font-size:.68rem; text-transform:uppercase;
           letter-spacing:.1em; margin-top:6px; }

/* badge */
.badge {
    display:inline-block; background:#0d1e30; color:#4fc3f7;
    border:1px solid #1a3a55; border-radius:30px;
    padding:3px 12px; font-size:.76rem; font-weight:500; margin:2px 3px 2px 0;
}

/* booking table */
.btable { width:100%; border-collapse:collapse; }
.btable tr:last-child td { border-bottom:none; }
.btable td {
    padding:11px 6px; border-bottom:1px solid #111827;
    font-size:.9rem; vertical-align:top;
}
.btable td:first-child { color:#2d4a6b; width:44%; font-weight:500; }
.btable td:last-child  { color:#c8dff0; font-weight:600; }

/* success / error banners */
.ok-banner {
    background:linear-gradient(120deg,#061612,#081f16);
    border:1px solid #124d2a; border-radius:16px;
    padding:22px 28px; margin-bottom:22px;
    display:flex; align-items:center; gap:16px;
}
.ok-banner .ico { font-size:2.2rem; }
.ok-banner h3 { color:#3dba74; margin:0 0 4px; font-size:1.15rem; }
.ok-banner p  { color:#5cad82; margin:0; font-size:.86rem; }

.err-banner {
    background:linear-gradient(120deg,#170505,#130404);
    border:1px solid #4d1010; border-radius:18px;
    padding:44px 32px; text-align:center; margin:24px 0;
}
.err-banner .ico { font-size:3.5rem; margin-bottom:14px; }
.err-banner h2 { color:#e85252; font-size:1.8rem; margin:0 0 10px; }
.err-banner p  { color:#b06060; font-size:.96rem; max-width:500px; margin:0 auto; }

/* gallery */
.gcap { text-align:center; color:#2d4a6b; font-size:.7rem; margin-top:4px; }

/* step progress */
.step-row { display:flex; align-items:center; gap:10px; margin:5px 0; }
.sdot { width:8px;height:8px;border-radius:50%;flex-shrink:0; }
.sdot.done   { background:#3dba74; }
.sdot.active { background:#4fc3f7; box-shadow:0 0 8px #4fc3f7bb; }
.sdot.wait   { background:#1c2d44; }
.stxt { font-size:.86rem; }
.stxt.done   { color:#3dba74; }
.stxt.active { color:#4fc3f7; font-weight:600; }
.stxt.wait   { color:#2d4060; }

/* buttons */
div[data-testid="stButton"]>button[kind="primary"] {
    background:linear-gradient(135deg,#1565c0,#0d47a1) !important;
    border:none!important; border-radius:12px!important;
    font-size:1rem!important; font-weight:700!important; padding:13px 0!important;
    letter-spacing:.04em!important; color:#fff!important;
    box-shadow:0 4px 18px rgba(21,101,192,.45)!important;
}
div[data-testid="stButton"]>button[kind="secondary"] {
    background:#0a0e1a!important; border:1px solid #18243a!important;
    border-radius:10px!important; color:#6a9ec0!important;
}
</style>
""", unsafe_allow_html=True)

# ── session state ─────────────────────────────────────────────────────────────
for k, v in {
    "page":    "form",
    "result":  None,
    "form":    {},
    "user":    {},
    "history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── persistence ───────────────────────────────────────────────────────────────
PROFILE_FILE    = ROOT / "user_profile.json"
SCREENSHOTS_DIR = ROOT / "app" / "screenshots"

def load_profile() -> dict:
    if PROFILE_FILE.exists():
        try: return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return {}

def save_profile(p: dict):
    PROFILE_FILE.write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")

# load once on startup
if not st.session_state["user"]:
    st.session_state["user"] = load_profile()

# ── helpers ───────────────────────────────────────────────────────────────────
def run_orchestrator(data: dict, automate: bool) -> dict:
    try:
        from app.orchestrator.orchestrator import Orchestrator
        return Orchestrator().run(data, automate_browser=automate)
    except Exception as exc:
        return {"status": "error", "message": str(exc),
                "hotel": None, "options": None, "screenshots": [], "session_id": ""}

def nights_count(ci: str, co: str) -> int:
    try: return max(1, (date.fromisoformat(co) - date.fromisoformat(ci)).days)
    except Exception: return 1

def get_all_screenshots() -> list:
    if not SCREENSHOTS_DIR.exists(): return []
    return sorted(SCREENSHOTS_DIR.rglob("*.png"),
                  key=lambda p: p.stat().st_mtime, reverse=True)

def render_gallery(paths: list):
    if not paths:
        st.info("No screenshots yet.")
        return
    for i in range(0, len(paths), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(paths):
                p = paths[i + j]
                with col:
                    st.image(str(p), use_container_width=True)
                    st.markdown(f'<p class="gcap">{p.name}</p>',
                                unsafe_allow_html=True)

def rapidapi_key_set() -> bool:
    from dotenv import load_dotenv
    load_dotenv()
    return bool(os.getenv("RAPIDAPI_KEY", "").strip())

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — BOOKING FORM
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["page"] == "form":

    u = st.session_state["user"]
    f = st.session_state["form"]

    # ── hero ──────────────────────────────────────────────────────────────────
    is_returning = bool(u.get("full_name"))
    greeting = f"Welcome back, {u['full_name'].split()[0]}! 👋" if is_returning else "🏨 AI Hotel Booking Agent"

    st.markdown(f"""
    <div class="hero">
      <h1>{greeting}</h1>
      <p>Smart multi-agent search · Real Booking.com data · Live browser automation</p>
      {"" if not is_returning else '<span class="tag">✓ Profile loaded — your details are pre-filled</span>'}
    </div>
    """, unsafe_allow_html=True)

    # ── API key check ─────────────────────────────────────────────────────────
    if not rapidapi_key_set():
        st.markdown("""
        <div class="api-warn">
          <b>⚠️ RapidAPI Key Required for Real Hotel Data</b>
          <p>
            1. Go to <b>https://rapidapi.com/tipsters/api/booking-com</b><br>
            2. Sign up free → Subscribe to <b>Basic plan (500 req/month free)</b><br>
            3. Copy your <code>X-RapidAPI-Key</code> from the dashboard<br>
            4. Open <code>.env</code> in this folder → set <code>RAPIDAPI_KEY=your_key_here</code><br>
            5. Restart the app
          </p>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1 — PERSONAL DETAILS  (auto-filled from saved profile)
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown('<p class="slabel">👤 Personal Details</p>', unsafe_allow_html=True)
    st.caption("Saved automatically — you won't need to re-enter these next time.")

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        full_name = st.text_input("Full Name *",
            value=u.get("full_name", ""), placeholder="Arjun Sharma")
    with r1c2:
        email = st.text_input("Email Address",
            value=u.get("email", ""), placeholder="arjun@email.com")
    with r1c3:
        phone = st.text_input("Phone Number",
            value=u.get("phone", ""), placeholder="+91 98765 43210")

    # ── Booking.com credentials ────────────────────────────────────────────
    st.markdown('<p class="slabel">🔐 Booking.com Account  <span style="color:#1c3a58;font-size:.7rem;font-weight:400;">(for auto-login during browser automation)</span></p>', unsafe_allow_html=True)
    st.caption("Stored locally on your machine. Used only to log into Booking.com automatically.")

    cr1, cr2, cr3 = st.columns([2, 2, 1])
    with cr1:
        booking_email = st.text_input("Booking.com Email",
            value=u.get("booking_email", u.get("email", "")),
            placeholder="your@booking.com account")
    with cr2:
        booking_password = st.text_input("Booking.com Password",
            value=u.get("booking_password", ""),
            placeholder="••••••••••",
            type="password")
    with cr3:
        st.markdown("<br>", unsafe_allow_html=True)
        auth_exists = (ROOT / "auth.json").exists()
        if auth_exists:
            st.markdown('<div class="profile-pill">✓ Session saved</div>',
                        unsafe_allow_html=True)
            if st.button("Clear session", type="secondary"):
                (ROOT / "auth.json").unlink(missing_ok=True)
                st.success("Session cleared.")
                st.rerun()
        else:
            st.caption("No saved session yet")

    # ── Payment Details ────────────────────────────────────────────────────
    st.markdown(
        '<p class="slabel">💳 Payment Details  '
        '<span style="color:#1c3a58;font-size:.7rem;font-weight:400;">'
        '(optional — used if Booking.com has no saved card)</span></p>',
        unsafe_allow_html=True)
    st.caption("Stored locally. Leave blank to use a card already saved in your Booking.com account.")

    pay1, pay2, pay3 = st.columns([3, 1, 1])
    with pay1:
        card_number = st.text_input("Card Number",
            value=u.get("card_number", ""),
            placeholder="4111 1111 1111 1111",
            max_chars=19)
    with pay2:
        expiry_month = st.text_input("MM",
            value=u.get("expiry_month", ""),
            placeholder="MM", max_chars=2)
    with pay3:
        expiry_year = st.text_input("YY",
            value=u.get("expiry_year", ""),
            placeholder="YY", max_chars=2)

    pay4, pay5 = st.columns([1, 3])
    with pay4:
        cvv = st.text_input("CVV",
            value=u.get("cvv", ""),
            placeholder="123", max_chars=4, type="password")
    with pay5:
        name_on_card = st.text_input("Name on Card",
            value=u.get("name_on_card", ""),
            placeholder="ARJUN SHARMA")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2 — BOOKING DETAILS
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown('<p class="slabel">🔍 Booking Details</p>', unsafe_allow_html=True)

    b1, b2, b3 = st.columns([2, 1, 1])
    with b1:
        city = st.text_input("City / Destination *",
            value=f.get("city", ""), placeholder="Goa, Mumbai, Jaipur, Delhi, Bangkok…")
    with b2:
        checkin = st.date_input("Check-in *",
            value=date.fromisoformat(f["checkin"]) if f.get("checkin") else date.today() + timedelta(days=7))
    with b3:
        checkout = st.date_input("Check-out *",
            value=date.fromisoformat(f["checkout"]) if f.get("checkout") else date.today() + timedelta(days=10))

    d1, d2, d3 = st.columns(3)
    with d1:
        guests = st.number_input("Guests", min_value=1, max_value=12,
            value=int(f.get("guests", 2)))
    with d2:
        budget = st.number_input("Max Budget ₹/night", min_value=500, max_value=200000,
            value=int(f.get("budget", 5000)), step=500)
    with d3:
        min_rating = st.select_slider("Min Rating",
            options=[1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0],
            value=float(f.get("min_rating", 4.0)),
            format_func=lambda x: f"⭐ {x}")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3 — PREFERENCES
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown('<p class="slabel">✨ Preferences</p>', unsafe_allow_html=True)

    p1, p2 = st.columns([3, 2])
    with p1:
        amenities = st.multiselect("Required Amenities",
            ["wifi", "pool", "gym", "spa", "breakfast", "free_cancellation", "parking", "bar"],
            default=f.get("amenities", []),
            placeholder="Any amenities you need…")
    with p2:
        room_type = st.selectbox("Room Type",
            ["Any", "Standard", "Deluxe", "Suite", "Family Room"],
            index=["Any","Standard","Deluxe","Suite","Family Room"].index(f.get("room_type","Any")))
        purpose   = st.selectbox("Trip Purpose",
            ["Leisure","Business","Family","Honeymoon"],
            index=["Leisure","Business","Family","Honeymoon"].index(f.get("purpose","Leisure")))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4 — AUTOMATION
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown('<p class="slabel">⚙️ Browser Automation</p>', unsafe_allow_html=True)

    at1, at2 = st.columns([1, 2])
    with at1:
        automate = st.toggle("Open Booking.com in browser",
            value=f.get("automate", True),
            help="Opens a real Chrome window, logs in, searches and navigates the booking flow.")
        auto_confirm = st.toggle("Auto-confirm booking",
            value=f.get("auto_confirm", False),
            disabled=not automate,
            help="⚠️ Charges real money — clicks the final Confirm/Pay button automatically.")
    with at2:
        if automate:
            if booking_email and booking_password:
                st.success("✓ Credentials found — browser will log in automatically")
            else:
                st.warning("Add your Booking.com email & password above for auto-login")
            if auto_confirm:
                st.error("⚠️ Auto-confirm is ON — the agent will click Pay and charge your card!")
            else:
                st.info("Auto-confirm is OFF — the browser will stop at the payment page so you can review before paying.")
        else:
            auto_confirm = False
            st.caption("Browser automation off — agents will search & rank hotels only.")

    os.environ["HEADLESS"] = "false"

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # BOOK BUTTON
    # ─────────────────────────────────────────────────────────────────────────
    book_btn = st.button("🚀  Book Hotel Now", type="primary", use_container_width=True)

    if book_btn:
        errs = []
        if not full_name.strip():     errs.append("Full name is required.")
        if not city.strip():          errs.append("Please enter a destination city.")
        if checkout <= checkin:       errs.append("Check-out must be after check-in.")
        if not rapidapi_key_set():    errs.append("RAPIDAPI_KEY is not set in .env — real hotel data cannot be fetched.")

        if errs:
            for e in errs: st.error(e)
        else:
            # ── save profile (with credentials + payment) ─────────────────
            profile = {
                "full_name":        full_name.strip(),
                "email":            email.strip(),
                "phone":            phone.strip(),
                "booking_email":    booking_email.strip(),
                "booking_password": booking_password,   # stored locally
                "card_number":      card_number.strip(),
                "expiry_month":     expiry_month.strip(),
                "expiry_year":      expiry_year.strip(),
                "cvv":              cvv.strip(),
                "name_on_card":     name_on_card.strip(),
            }
            st.session_state["user"] = profile
            save_profile(profile)

            form_vals = {
                "city": city.strip(), "checkin": checkin.isoformat(),
                "checkout": checkout.isoformat(), "guests": int(guests),
                "budget": float(budget), "min_rating": float(min_rating),
                "amenities": amenities, "room_type": room_type,
                "purpose": purpose, "automate": automate,
                "auto_confirm": auto_confirm,
            }
            st.session_state["form"] = form_vals

            # ── live process window ───────────────────────────────────────
            st.markdown("""
            <div style="background:#080e1c;border:1px solid #1a2e4a;border-radius:14px;
                        padding:22px 26px;margin:16px 0 20px;">
              <div style="color:#4fc3f7;font-size:1rem;font-weight:700;margin-bottom:14px;">
                ⚡ Booking Process — Live
              </div>
            """, unsafe_allow_html=True)

            prog = st.progress(0)
            status_line = st.empty()
            step_log    = st.empty()
            st.markdown("</div>", unsafe_allow_html=True)

            agent_steps = [
                (0.10, "🔍", "Calling Booking.com API to fetch real hotels…"),
                (0.25, "🎯", f"Filtering: budget ≤ ₹{int(budget):,}  |  rating ≥ {min_rating}⭐"),
                (0.38, "🔁", "Retry logic — relaxing constraints if no match found…"),
                (0.52, "⚖️", "Ranking hotels with AI scoring algorithm…"),
                (0.66, "🤖", "AI decision engine selecting best hotel…"),
                (0.78, "📋", "Preparing booking payload…"),
                (0.88, "🌐", "Opening Chrome → navigating Booking.com…" if automate else "✅ Booking prepared (automation off)"),
                (0.96, "💾", "Saving session to memory…"),
            ]

            log_lines = []
            def draw_log():
                html = "".join(
                    f'<div class="step-row">'
                    f'<div class="sdot {"done" if i < len(log_lines)-1 else "active"}"></div>'
                    f'<span class="stxt {"done" if i < len(log_lines)-1 else "active"}">{ln}</span>'
                    f'</div>'
                    for i, ln in enumerate(log_lines)
                )
                step_log.markdown(html, unsafe_allow_html=True)

            for pct, icon, label in agent_steps[:-3]:
                prog.progress(pct)
                status_line.markdown(
                    f'<p style="color:#4fc3f7;font-size:.88rem;margin:0">{icon} {label}</p>',
                    unsafe_allow_html=True)
                log_lines.append(f"{icon} {label}")
                draw_log()
                time.sleep(0.3)

            # ── run orchestrator (browser opens here if automate=True) ────
            name_parts = full_name.strip().split(None, 1)
            data = {
                "location":    city.strip(),
                "checkin":     checkin.isoformat(),
                "checkout":    checkout.isoformat(),
                "guests":      int(guests),
                "budget":      float(budget),
                "min_rating":  float(min_rating),
                "amenities":   amenities,
                "auto_mode":   True,
                "user_name":   full_name.strip(),
                "user_email":  email.strip(),
                "room_type":   room_type,
                "purpose":     purpose,
                "auto_confirm": auto_confirm,
                "guest": {
                    "first_name": name_parts[0] if name_parts else "",
                    "last_name":  name_parts[1] if len(name_parts) > 1 else "",
                    "email":      email.strip(),
                    "phone":      phone.strip(),
                },
                "payment": {
                    "card_number":  card_number.strip(),
                    "expiry_month": expiry_month.strip(),
                    "expiry_year":  expiry_year.strip(),
                    "cvv":          cvv.strip(),
                    "name_on_card": name_on_card.strip(),
                },
            }

            if automate:
                prog.progress(0.88)
                status_line.markdown(
                    '<p style="color:#f5a623;font-size:.88rem;margin:0">'
                    '🌐 Chrome is open — completing booking on Booking.com…'
                    '</p>', unsafe_allow_html=True)
                log_lines.append("🌐 Chrome opened — browser automation running…")
                draw_log()

            result = run_orchestrator(data, automate=automate)

            # ── finish ────────────────────────────────────────────────────
            prog.progress(1.0)
            status_line.markdown(
                '<p style="color:#3dba74;font-size:.88rem;margin:0">✅ All done!</p>',
                unsafe_allow_html=True)
            log_lines.append("💾 Results saved.")
            draw_log()
            time.sleep(0.6)
            prog.empty()
            status_line.empty()
            step_log.empty()

            st.session_state["result"] = result
            if result.get("status") == "success":
                st.session_state["history"].insert(0, {
                    **result,
                    "booked_at": time.strftime("%Y-%m-%d %H:%M"),
                    "city":  city.strip(),
                    "guest": full_name.strip(),
                })

            st.session_state["page"] = "result"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — RESULT
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "result":

    result = st.session_state.get("result", {})
    status = result.get("status", "")
    f      = st.session_state.get("form", {})
    u      = st.session_state.get("user", {})

    # nav row
    n1, _, n2 = st.columns([1, 6, 1])
    with n1:
        if st.button("← New Search", type="secondary"):
            st.session_state.update({"page": "form", "result": None})
            st.rerun()
    with n2:
        if st.button("📸 Gallery", type="secondary"):
            st.session_state["page"] = "gallery"
            st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # NO HOTEL FOUND
    # ─────────────────────────────────────────────────────────────────────────
    if status in ("no_results", "error"):
        # Distinguish API key error from budget error
        msg = result.get("message", "")
        is_key_error = "RAPIDAPI_KEY" in msg or "X-RapidAPI-Key" in msg

        if is_key_error:
            st.markdown(f"""
            <div class="err-banner">
              <div class="ico">🔑</div>
              <h2>API Key Not Configured</h2>
              <p>{msg}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="err-banner">
              <div class="ico">🚫</div>
              <h2>No Hotel Found in This Budget</h2>
              <p>{msg or "No hotels matched your criteria even after relaxing the budget and rating."}</p>
            </div>
            """, unsafe_allow_html=True)

            t1, t2, t3 = st.columns(3)
            for col, icon, title, hint in [
                (t1,"💰","Increase Budget","Try ₹2,000–5,000 more per night"),
                (t2,"⭐","Lower Rating","Drop minimum star rating by 0.5"),
                (t3,"📍","Try Another City","Search a different destination"),
            ]:
                col.markdown(f"""<div class="icard">
                  <b style="color:#4fc3f7">{icon} {title}</b><br>
                  <span style="color:#2d4a6b;font-size:.84rem;">{hint}</span>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Try Again", type="primary", use_container_width=True):
            st.session_state.update({"page": "form", "result": None})
            st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # SUCCESS
    # ─────────────────────────────────────────────────────────────────────────
    elif status == "success":
        hotel   = result.get("hotel", {})
        booking = result.get("booking", {})
        shots   = result.get("screenshots", [])
        n       = nights_count(f.get("checkin",""), f.get("checkout",""))
        price   = hotel.get("price", 0)
        total   = price * n

        # ── success banner ─────────────────────────────────────────────────
        st.markdown(f"""
        <div class="ok-banner">
          <div class="ico">✅</div>
          <div>
            <h3>Hotel Found &amp; Booking Process Completed!</h3>
            <p>Booking.com was opened, searched, and navigated.
               {len(shots)} screenshot(s) saved to gallery.</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── hotel card ─────────────────────────────────────────────────────
        photo = hotel.get("photo", "")
        stars = hotel.get("stars", 0)
        stars_html = "⭐" * int(stars) if stars else ""
        amenity_badges = "".join(
            f'<span class="badge">{a}</span>' for a in hotel.get("amenities", []))
        review_word = hotel.get("review_word", "")

        if photo:
            ph1, ph2 = st.columns([1, 2])
            with ph1:
                st.image(photo, use_container_width=True,
                         caption=hotel.get("hotel_name",""))
            with ph2:
                st.markdown(f"""
                <div style="padding:8px 0">
                  <div style="color:#4fc3f7;font-size:1.65rem;font-weight:800;margin-bottom:4px;">
                    {hotel.get("hotel_name","—")}
                  </div>
                  <div style="color:#2d4a6b;font-size:.9rem;margin-bottom:8px;">
                    📍 {hotel.get("location","—")} &nbsp;
                    {stars_html} &nbsp;
                    <span style="color:#3dba74;font-size:.85rem;">{review_word}</span>
                  </div>
                  <div style="margin-bottom:14px;">{amenity_badges}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="icard">
              <div style="color:#4fc3f7;font-size:1.65rem;font-weight:800;margin-bottom:4px;">
                {hotel.get("hotel_name","—")}
              </div>
              <div style="color:#2d4a6b;font-size:.9rem;margin-bottom:10px;">
                📍 {hotel.get("location","—")} &nbsp; {stars_html} &nbsp;
                <span style="color:#3dba74">{review_word}</span>
              </div>
              {amenity_badges}
            </div>
            """, unsafe_allow_html=True)

        # ── stat boxes ─────────────────────────────────────────────────────
        s1,s2,s3,s4,s5 = st.columns(5)
        for col, val, lbl in [
            (s1, f"₹{price:,.0f}",   "Per Night"),
            (s2, f"{n} night{'s' if n>1 else ''}", "Stay"),
            (s3, f"₹{total:,.0f}",   "Subtotal"),
            (s4, f"₹{total*1.12:,.0f}","Total+Tax"),
            (s5, f"⭐ {hotel.get('rating',0)}", "Rating /5"),
        ]:
            col.markdown(f"""<div class="stat">
              <div class="v">{val}</div><div class="l">{lbl}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── booking summary + price breakdown ──────────────────────────────
        left, right = st.columns(2)
        with left:
            st.markdown('<p class="slabel">📋 Booking Summary</p>', unsafe_allow_html=True)
            rc = hotel.get("review_count", 0)
            st.markdown(f"""<table class="btable">
              <tr><td>Guest Name</td>    <td>{u.get("full_name","—")}</td></tr>
              <tr><td>Email</td>         <td>{u.get("email","—")}</td></tr>
              <tr><td>Phone</td>         <td>{u.get("phone","—")}</td></tr>
              <tr><td>Destination</td>   <td>{f.get("city","—")}</td></tr>
              <tr><td>Check-in</td>      <td>{f.get("checkin","—")}</td></tr>
              <tr><td>Check-out</td>     <td>{f.get("checkout","—")}</td></tr>
              <tr><td>Guests</td>        <td>{f.get("guests","—")}</td></tr>
              <tr><td>Room Type</td>     <td>{f.get("room_type","Any")}</td></tr>
              <tr><td>Purpose</td>       <td>{f.get("purpose","—")}</td></tr>
              <tr><td>Reviews</td>       <td>{rc:,} reviews</td></tr>
              <tr><td>Session</td>       <td style="font-family:monospace;font-size:.78rem;">{result.get("session_id","")[:20]}…</td></tr>
            </table>""", unsafe_allow_html=True)

        with right:
            st.markdown('<p class="slabel">💰 Price Breakdown</p>', unsafe_allow_html=True)
            st.markdown(f"""<table class="btable">
              <tr><td>Rate per night</td>      <td>₹{price:,.0f}</td></tr>
              <tr><td>Nights</td>              <td>{n}</td></tr>
              <tr><td>Guests</td>              <td>{f.get("guests","—")}</td></tr>
              <tr><td>Room subtotal</td>        <td>₹{total:,.0f}</td></tr>
              <tr><td>Taxes &amp; fees (12%)</td><td>₹{total*0.12:,.0f}</td></tr>
              <tr><td style="color:#4fc3f7"><b>Grand Total</b></td>
                  <td style="color:#4fc3f7"><b>₹{total*1.12:,.0f}</b></td></tr>
            </table>""", unsafe_allow_html=True)

            if result.get("message"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.info(f"🤖 {result['message']}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── action buttons ─────────────────────────────────────────────────
        ab1, ab2, ab3 = st.columns(3)
        with ab1:
            if st.button("📸  View Screenshots Gallery",
                         type="primary", use_container_width=True):
                st.session_state["page"] = "gallery"
                st.rerun()
        with ab2:
            if st.button("🔁  Book Another Hotel",
                         type="secondary", use_container_width=True):
                st.session_state.update({"page": "form", "result": None})
                st.rerun()
        with ab3:
            link = hotel.get("link", "")
            if link and link.startswith("http"):
                st.link_button("🌐  Open on Booking.com", link,
                               use_container_width=True)

        # ── inline screenshots ─────────────────────────────────────────────
        if shots:
            st.markdown('<p class="slabel">📸 Booking Screenshots</p>',
                        unsafe_allow_html=True)
            render_gallery([Path(p) for p in shots])

    # ─────────────────────────────────────────────────────────────────────────
    # OPTIONS (top-3 interactive)
    # ─────────────────────────────────────────────────────────────────────────
    elif status == "options":
        st.markdown("### 🏆 Top Hotels Found — Pick One")
        for i, h in enumerate(result.get("options", []), 1):
            badges = "".join(f'<span class="badge">{a}</span>'
                             for a in h.get("amenities",[]))
            with st.expander(
                f"#{i}  {h.get('hotel_name','')}  ·  "
                f"₹{h.get('price',0):,.0f}/night  ·  ⭐{h.get('rating',0)}"
            ):
                if h.get("photo"):
                    st.image(h["photo"], width=300)
                st.markdown(badges, unsafe_allow_html=True)
                st.caption(f"📍 {h.get('location','')}  |  AI score: {h.get('score',0):.3f}")
                if st.button("Book This", key=f"opt{i}", type="primary"):
                    st.session_state["result"] = {
                        "status": "success", "hotel": h,
                        "booking": {"checkin": f.get("checkin"),
                                    "checkout": f.get("checkout"),
                                    "guests": f.get("guests")},
                        "screenshots": [], "session_id": result.get("session_id",""),
                        "message": f"You selected {h['hotel_name']}",
                    }
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SCREENSHOT GALLERY
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["page"] == "gallery":

    g1, _, g2 = st.columns([1, 5, 2])
    with g1:
        if st.button("← Back", type="secondary"):
            st.session_state["page"] = "result"
            st.rerun()
    with g2:
        if st.button("🏠  New Booking", type="secondary"):
            st.session_state.update({"page": "form", "result": None})
            st.rerun()

    st.markdown("""
    <div class="hero" style="padding:28px 36px 22px;">
      <h1 style="font-size:1.75rem;">📸 Screenshot Gallery</h1>
      <p>All screenshots captured during browser automation — every session</p>
    </div>
    """, unsafe_allow_html=True)

    all_shots = get_all_screenshots()

    if not all_shots:
        st.markdown("""
        <div class="err-banner" style="padding:36px;">
          <div class="ico">📂</div>
          <h2 style="font-size:1.4rem;">Gallery is Empty</h2>
          <p>Enable browser automation and run a booking to capture screenshots.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        sessions = sorted({p.parent.name for p in all_shots})
        fc1, fc2 = st.columns([3,1])
        with fc1:
            chosen = st.selectbox("Filter by session",
                                  ["All sessions"] + sessions)
        with fc2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption(f"{len(all_shots)} total screenshots")

        filtered = (all_shots if chosen == "All sessions"
                    else [p for p in all_shots if p.parent.name == chosen])

        render_gallery(filtered)

        st.markdown("---")
        if st.button("🗑️  Clear Screenshots", type="secondary"):
            for fp in filtered:
                try: fp.unlink()
                except Exception: pass
            st.rerun()

    # history accordion
    history = st.session_state.get("history", [])
    if history:
        st.markdown('<p class="slabel">📋 Booking History</p>',
                    unsafe_allow_html=True)
        for entry in history:
            h = entry.get("hotel") or {}
            label = (f"✅  {h.get('hotel_name','?')}  ·  "
                     f"{entry.get('city','')}  ·  {entry.get('booked_at','')}")
            with st.expander(label):
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Price/night", f"₹{h.get('price',0):,.0f}")
                c2.metric("Rating", f"⭐ {h.get('rating',0)}")
                c3.metric("Stars", f"{'⭐'*int(h.get('stars',0)) or '—'}")
                c4.metric("Screenshots", len(entry.get("screenshots",[])))
                if h.get("photo"):
                    st.image(h["photo"], width=260)
