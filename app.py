# ============================================================
# app.py — Fun Friday Word-Search Puzzle  🚢  (Strands-style)
# Run:  streamlit run app.py
# ============================================================
import streamlit as st
import streamlit.components.v1 as components
import json, time, random
from datetime import datetime, date, timedelta
import pytz

import database as db
import admin as adm
from config import (
    ADMIN_EMAILS, ADMIN_PASSWORD, PUZZLE_DAY,
    PUZZLE_START_HOUR, PUZZLE_END_HOUR,
    PUZZLE_DURATION_MINUTES, GRID_SIZE, APP_TITLE, ORG_NAME, LOGO_EMOJI,
)
from puzzle_engine import json_to_grid, json_to_placements, real_placements, validate_selection

st.set_page_config(
    page_title=f"{APP_TITLE} | {ORG_NAME}",
    page_icon="🚢", layout="wide",
    initial_sidebar_state="collapsed",
)

IST = pytz.timezone("Asia/Kolkata")
db.init_db()

# ── Global styles (login / leaderboard / panels) ──────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #f0f4ff; color: #1a1a2e; }
section[data-testid="stSidebar"] { background: #fff; }

.header-banner {
    background: linear-gradient(135deg, #1a237e 0%, #1565c0 60%, #0288d1 100%);
    border-radius: 20px; padding: 28px 32px;
    margin-bottom: 20px; text-align: center;
    box-shadow: 0 8px 32px rgba(21,101,192,0.25);
}
.header-banner h1 {
    font-family: 'Nunito', sans-serif;
    font-size: 2.6rem; margin: 0; color: #fff;
    letter-spacing: -0.5px;
}
.header-banner p { color: #bbdefb; margin: 6px 0 0; font-size: 1rem; }

.lb-card {
    background: #fff; border: 1px solid #e0e7ef;
    border-radius: 14px; padding: 14px 20px;
    margin-bottom: 10px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.lb-rank  { font-size: 1.5rem; width: 40px; text-align: center; }
.lb-name  { font-weight: 700; font-size: 1rem; color: #1a1a2e; }
.lb-dept  { font-size: 0.75rem; color: #666; }
.lb-score { margin-left: auto; text-align: right; }
.lb-score .num { font-family: 'Nunito', sans-serif; font-size: 1.15rem; color: #1565c0; font-weight: 800; }
.lb-score .tim { font-size: 0.75rem; color: #555; }

.closed-box {
    background: #fff8e1; border: 1px solid #f9a825;
    border-radius: 14px; padding: 36px; text-align: center; color: #e65100;
}
.winner-box {
    background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
    border: 2px solid #2e7d32; border-radius: 18px;
    padding: 32px; text-align: center; color: #1b5e20;
    animation: glow 2s ease-in-out infinite alternate;
}
@keyframes glow {
    from { box-shadow: 0 0 12px rgba(46,125,50,0.2); }
    to   { box-shadow: 0 0 32px rgba(46,125,50,0.45); }
}
.stButton > button {
    background: #1565c0; color: #fff; border: none;
    border-radius: 10px; padding: 10px 24px;
    font-family: 'Nunito', sans-serif;
    font-size: 1rem; font-weight: 800;
    transition: background 0.2s, transform 0.1s;
}
.stButton > button:hover { background: #1a237e; transform: translateY(-1px); }
.stTextInput > div > div > input {
    background: #fff; color: #1a1a2e;
    border: 1.5px solid #c5cae9; border-radius: 10px;
    font-size: 1rem; padding: 10px 14px;
}
.stMarkdown p, .stMarkdown li { color: #1a1a2e; }
div[data-testid="stForm"] { border: none; padding: 0; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════
def now_ist():
    return datetime.now(IST)

def this_friday_date():
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7
    return today + timedelta(days=days_ahead)

def puzzle_is_open():
    now = now_ist()
    if now.weekday() != PUZZLE_DAY:
        return False
    return PUZZLE_START_HOUR <= now.hour < PUZZLE_END_HOUR

def time_until_next_open():
    now = now_ist()
    days_until = (4 - now.weekday()) % 7
    if days_until == 0 and now.hour >= PUZZLE_END_HOUR:
        days_until = 7
    next_open = now.replace(hour=PUZZLE_START_HOUR, minute=0, second=0, microsecond=0) + timedelta(days=days_until)
    delta = next_open - now
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    return f"{delta.days}d {h%24:02d}h {m:02d}m" if delta.days else f"{h:02d}h {m:02d}m {s:02d}s"

def fmt_time(seconds):
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"

RANK_EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}

def _render_leaderboard(lb):
    if not lb:
        st.info("No submissions yet. Be the first!")
        return
    for i, row in enumerate(lb[:10], 1):
        emoji = RANK_EMOJI.get(i, f"#{i}")
        medal = "🥇" if i == 1 else ""
        st.markdown(f"""
        <div class="lb-card">
          <div class="lb-rank">{emoji}</div>
          <div>
            <div class="lb-name">{medal} {row['player_name']}</div>
            <div class="lb-dept">{row.get('department','')}</div>
          </div>
          <div class="lb-score">
            <div class="num">{row['score']} words</div>
            <div class="tim">⏱ {fmt_time(row['time_taken'])}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Session state
# ═══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "logged_in": False, "player_name": "", "player_email": "",
        "player_dept": "", "game_started": False, "session_id": None,
        "puzzle_data": None, "grid": None, "placements": None,
        "found_words": [], "submitted": False, "admin_mode": False,
        "hints_used": 0, "start_epoch": None,
        "admin_pw_pending": False, "admin_pw_error": "",
        "admin_pw_name": "", "admin_pw_email": "", "admin_pw_dept": "",
        # JS → Python communication
        "js_found_word": None,
        "js_hints_used": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
S = st.session_state


# ═══════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h1>{LOGO_EMOJI} {APP_TITLE}</h1>
  <p>{ORG_NAME} — Every Friday is a Puzzle Friday!</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Sidebar admin
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Admin Panel")
    if S.logged_in and S.player_email in [e.lower() for e in ADMIN_EMAILS]:
        if st.button("🔐 Open Admin Panel"):
            S.admin_mode = True
    else:
        st.info("Admin access for authorised emails only.")

if S.admin_mode and S.logged_in and S.player_email in [e.lower() for e in ADMIN_EMAILS]:
    adm.render_admin(S.player_email)
    st.stop()


# ═══════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════
if not S.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if S.admin_pw_pending:
            st.markdown("### 🔐 Admin Verification")
            st.info(f"**{S.admin_pw_email}** is an admin account. Enter the admin password.")
            pw_input = st.text_input("Admin Password", type="password", placeholder="••••••••••••")
            if S.admin_pw_error:
                st.error(S.admin_pw_error)
            v1, v2 = st.columns(2)
            with v1:
                if st.button("✅ Verify", use_container_width=True):
                    if pw_input == ADMIN_PASSWORD:
                        S.logged_in = True
                        S.player_name = S.admin_pw_name
                        S.player_email = S.admin_pw_email
                        S.player_dept = S.admin_pw_dept
                        S.admin_mode = True
                        S.admin_pw_pending = False
                        S.admin_pw_error = ""
                        st.rerun()
                    else:
                        S.admin_pw_error = "❌ Wrong password."
                        st.rerun()
            with v2:
                if st.button("← Back", use_container_width=True):
                    S.admin_pw_pending = False
                    S.admin_pw_error = ""
                    st.rerun()
        else:
            st.markdown("### 👤 Enter your details to play")
            name  = st.text_input("Your Name *", placeholder="e.g. Utkarsh Kulshrestha")
            email = st.text_input("Work Email *", placeholder="you@matchlog.delivery")
            dept  = st.selectbox("Department", ["Operations","Sales","Finance","Tech","HR","Management","Other"])
            if st.button("🚀 Let's Play!", use_container_width=True):
                name  = name.strip()
                email = email.strip().lower()
                if not name or not email:
                    st.error("Please fill in your name and email.")
                elif "@" not in email:
                    st.error("Enter a valid email address.")
                elif email in [e.lower() for e in ADMIN_EMAILS]:
                    S.admin_pw_pending = True
                    S.admin_pw_name = name
                    S.admin_pw_email = email
                    S.admin_pw_dept = dept
                    S.admin_pw_error = ""
                    st.rerun()
                else:
                    S.logged_in = True
                    S.player_name = name
                    S.player_email = email
                    S.player_dept = dept
                    st.rerun()
    st.stop()


# ═══════════════════════════════════════════════════════════════
# PUZZLE WINDOW CHECK
# ═══════════════════════════════════════════════════════════════
if not puzzle_is_open() and S.player_email not in [e.lower() for e in ADMIN_EMAILS]:
    st.markdown(f"""
    <div class="closed-box">
      <h2>🔒 Puzzle is Closed</h2>
      <p>Fun Friday puzzle opens every <strong>Friday 11:00 AM – 3:00 PM IST</strong>.</p>
      <p style="font-size:1.3rem; margin-top:12px;">
        ⏳ Opens in: <strong>{time_until_next_open()}</strong>
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 🏆 Last Week's Winners")
    all_p = db.get_all_puzzles()
    if all_p:
        lb = db.get_leaderboard(all_p[0]["id"])
        _render_leaderboard(lb) if lb else st.info("No scores yet.")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# Load puzzle
# ═══════════════════════════════════════════════════════════════
friday_str = this_friday_date().isoformat()
puzzle     = db.get_or_create_puzzle(friday_str)

if S.puzzle_data is None or S.puzzle_data["id"] != puzzle["id"]:
    S.puzzle_data = puzzle
    S.grid        = json_to_grid(puzzle["grid"])
    S.placements  = real_placements(json_to_placements(puzzle["placements"]))
    S.found_words = []
    S.hints_used  = 0

if db.already_played(puzzle["id"], S.player_email) and not S.submitted:
    S.submitted = True


# ═══════════════════════════════════════════════════════════════
# Welcome / Start screen
# ═══════════════════════════════════════════════════════════════
if not S.game_started and not S.submitted:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        total_words = len(S.placements)
        st.markdown(f"""
        <div style="background:#fff; border-radius:18px; padding:32px;
                    box-shadow:0 4px 24px rgba(21,101,192,0.12); text-align:center;">
          <div style="font-size:3rem;">🚢</div>
          <h2 style="font-family:'Nunito',sans-serif; color:#1a237e; margin:8px 0;">
            Welcome, {S.player_name}!
          </h2>
          <p style="color:#555; font-size:1rem; margin-bottom:20px;">
            Find all <strong>{total_words} hidden logistics words</strong> in the grid.<br>
            Drag across letters to select. Words go in any direction.
          </p>
          <div style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap; margin-bottom:20px;">
            <div style="background:#e3f2fd; border-radius:12px; padding:12px 20px;">
              ⏱ <strong>{PUZZLE_DURATION_MINUTES} min</strong> timer
            </div>
            <div style="background:#e8f5e9; border-radius:12px; padding:12px 20px;">
              💡 <strong>3 hints</strong> available
            </div>
            <div style="background:#fff8e1; border-radius:12px; padding:12px 20px;">
              🏆 Most words + least time wins
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("⚠️ Timer starts the moment you click Start!")
        if st.button("▶️ Start Puzzle!", use_container_width=True):
            sid = db.create_session(puzzle["id"], S.player_name, S.player_email, S.player_dept)
            S.session_id  = sid
            S.start_epoch = time.time()
            S.game_started = True
            st.rerun()
    st.stop()


# ═══════════════════════════════════════════════════════════════
# SUBMITTED
# ═══════════════════════════════════════════════════════════════
if S.submitted:
    total = len(S.placements)
    st.markdown(f"""
    <div class="winner-box">
      <div style="font-size:3rem;">🎉</div>
      <h2 style="font-family:'Nunito',sans-serif;">Well done, {S.player_name}!</h2>
      <p style="font-size:1.2rem;">You found <strong>{len(S.found_words)}</strong> out of <strong>{total}</strong> words.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 🏆 Live Leaderboard")
    _render_leaderboard(db.get_leaderboard(puzzle["id"]))
    st.stop()


# ═══════════════════════════════════════════════════════════════
# ACTIVE GAME — Timer check
# ═══════════════════════════════════════════════════════════════
elapsed   = int(time.time() - S.start_epoch)
remaining = max(0, PUZZLE_DURATION_MINUTES * 60 - elapsed)

if remaining == 0:
    db.submit_session(S.session_id, S.found_words)
    S.submitted = True
    st.rerun()

# ── Handle word found signal from JS (via query params) ───────
qp = st.query_params
if "found" in qp:
    word = qp["found"]
    if word in S.placements and word not in S.found_words:
        S.found_words.append(word)
        db.update_found_words(S.session_id, S.found_words)
    st.query_params.clear()
    st.rerun()

if "submit" in qp:
    db.submit_session(S.session_id, S.found_words)
    S.submitted = True
    st.query_params.clear()
    st.rerun()

if "hints" in qp:
    try:
        S.hints_used = int(qp["hints"])
    except:
        pass
    st.query_params.clear()

# ═══════════════════════════════════════════════════════════════
# BUILD THE GAME HTML COMPONENT
# ═══════════════════════════════════════════════════════════════
grid_data       = S.grid
placements_data = S.placements
found_words     = S.found_words
total_words     = len(placements_data)
hints_remaining = max(0, 3 - S.hints_used)
GRID_N          = len(grid_data)   # actual grid size (dynamic)

mins, secs = divmod(remaining, 60)

COLORS = [
    "#1565c0","#2e7d32","#6a1b9a","#c62828",
    "#00695c","#e65100","#4527a0","#37474f",
    "#558b2f","#0277bd","#6d4c41","#ad1457",
]

word_color_map = {}
for i, w in enumerate(sorted(placements_data.keys())):
    word_color_map[w] = COLORS[i % len(COLORS)]

placements_js  = json.dumps(placements_data)
found_words_js = json.dumps(found_words)
color_map_js   = json.dumps(word_color_map)
grid_js        = json.dumps(grid_data)

GAME_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; user-select:none; }}
body {{ background:transparent; font-family:'Nunito',sans-serif; }}

#game-wrap {{ display:flex; gap:16px; align-items:flex-start; padding:4px; }}

/* ── Grid panel ── */
#grid-panel {{ position:relative; flex:1; min-width:0; }}
#grid-wrap  {{ position:relative; display:block; width:100%; max-width:480px; }}

/* SVG behind cells — line draws under circles */
#svg-overlay {{
  position:absolute; top:0; left:0;
  width:100%; height:100%;
  pointer-events:none;
  z-index:1;          /* BELOW cells */
  overflow:visible;
}}

#grid {{
  display:grid;
  grid-template-columns: repeat({GRID_N}, 1fr);
  gap:6px;
  padding:12px;
  background:#f8f9ff;
  border-radius:20px;
  box-shadow:0 4px 24px rgba(21,101,192,0.1);
  position:relative;
  z-index:2;          /* ABOVE svg */
}}

/* ── Strands-style circles ── */
.cell {{
  aspect-ratio:1;
  border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-family:'Nunito',sans-serif;
  font-size:clamp(0.6rem, 1.6vw, 0.9rem);
  font-weight:900;
  cursor:pointer;
  background:#ffffff;
  color:#1a237e;
  /* Subtle inset shadow = depth like Strands */
  box-shadow: 0 2px 4px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.8);
  transition:background 0.12s, transform 0.08s, box-shadow 0.12s;
  -webkit-tap-highlight-color:transparent;
  position:relative; z-index:3;  /* ABOVE svg lines */
}}
.cell:hover {{
  background:#e8eaff;
  transform:scale(1.06);
}}

/* Selecting = yellow filled, no border, just shadow glow */
.cell.selecting {{
  background:#f5a623 !important;
  color:#fff !important;
  transform:scale(1.1);
  box-shadow:0 0 0 3px rgba(245,166,35,0.35), 0 3px 8px rgba(245,166,35,0.4) !important;
}}

/* Found = solid color fill, white letter */
.cell.found {{
  color:#fff !important;
  box-shadow:0 2px 6px rgba(0,0,0,0.15) !important;
}}

.cell.shake {{ animation:shake 0.32s ease; }}
@keyframes shake {{
  0%,100% {{ transform:translateX(0); }}
  25%      {{ transform:translateX(-4px); }}
  75%      {{ transform:translateX(4px); }}
}}

/* ── Right panel ── */
#right-panel {{
  width:190px; flex-shrink:0;
  display:flex; flex-direction:column; gap:10px;
}}
.panel-card {{
  background:#fff; border-radius:14px; padding:12px;
  box-shadow:0 2px 10px rgba(21,101,192,0.08); text-align:center;
}}
#timer-display {{
  font-size:2.2rem; font-weight:900; color:#1565c0;
  letter-spacing:2px; line-height:1;
}}
#timer-display.warning {{ color:#e53935; animation:pulse 1s infinite; }}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.5}} }}
.timer-label {{ color:#999; font-size:0.7rem; margin-top:3px; }}

#score-row {{ display:flex; gap:5px; justify-content:center; flex-wrap:wrap; margin-bottom:5px; }}
.score-bubble {{
  width:22px; height:22px; border-radius:50%;
  border:2px solid #c5cae9; background:#f0f4ff;
  transition:all 0.25s;
}}
.score-bubble.done {{ border-color:transparent; transform:scale(1.1); }}
#score-text {{ font-size:0.9rem; font-weight:800; color:#1565c0; }}

.found-word-item {{
  display:flex; align-items:center; gap:6px;
  font-size:0.8rem; font-weight:800;
  padding:4px 10px; border-radius:20px;
  margin-bottom:4px; color:#fff;
  animation:popIn 0.28s cubic-bezier(.175,.885,.32,1.275);
}}
@keyframes popIn {{ from{{transform:scale(0.6);opacity:0}} to{{transform:scale(1);opacity:1}} }}

#hint-btn, #submit-btn {{
  width:100%; padding:9px; border:none; border-radius:12px;
  font-family:'Nunito',sans-serif; font-size:0.9rem; font-weight:900;
  cursor:pointer; transition:all 0.18s;
}}
#hint-btn {{
  background:linear-gradient(135deg,#7c4dff,#651fff);
  color:#fff; box-shadow:0 3px 10px rgba(124,77,255,0.28);
}}
#hint-btn:hover {{ transform:translateY(-2px); }}
#hint-btn:disabled {{ background:#ccc; box-shadow:none; transform:none; cursor:not-allowed; }}
#submit-btn {{
  background:linear-gradient(135deg,#1565c0,#1a237e);
  color:#fff; box-shadow:0 3px 10px rgba(21,101,192,0.28);
}}
#submit-btn:hover {{ transform:translateY(-2px); }}

#toast {{
  position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
  background:#1a237e; color:#fff;
  padding:9px 26px; border-radius:50px;
  font-size:1rem; font-weight:800;
  opacity:0; pointer-events:none; transition:opacity 0.25s;
  z-index:999; box-shadow:0 6px 20px rgba(26,35,126,0.3);
}}
#toast.show {{ opacity:1; }}
</style>
</head>
<body>
<div id="game-wrap">

  <div id="grid-panel">
    <div id="grid-wrap">
      <div id="grid"></div>
      <svg id="svg-overlay"></svg>
    </div>
  </div>

  <div id="right-panel">
    <div class="panel-card">
      <div id="timer-display">{mins:02d}:{secs:02d}</div>
      <div class="timer-label">time remaining</div>
    </div>

    <div class="panel-card">
      <div id="score-row"></div>
      <div id="score-text">0 / {total_words} found</div>
    </div>

    <button id="hint-btn">💡 Hint ({hints_remaining} left)</button>

    <div class="panel-card" style="text-align:left;">
      <div style="font-size:0.65rem;color:#999;margin-bottom:8px;font-weight:900;letter-spacing:1px;text-transform:uppercase;">Found</div>
      <div id="found-words-container"></div>
    </div>

    <button id="submit-btn">✅ Submit</button>
  </div>
</div>
<div id="toast"></div>

<script>
const GRID       = {grid_js};
const PLACEMENTS = {placements_js};
const COLOR_MAP  = {color_map_js};
const GRID_N     = {GRID_N};
const TOTAL      = {total_words};
const MAX_HINTS  = 3;

let foundWords    = {found_words_js};
let hintsUsed     = {S.hints_used};
let isSelecting   = false;
let selectedCells = [];
let hintActive    = false;
let timerSecs     = {remaining};

// ── Build grid ───────────────────────────────────────────────
const gridEl = document.getElementById('grid');
for (let r=0; r<GRID_N; r++) {{
  for (let c=0; c<GRID_N; c++) {{
    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.textContent = GRID[r][c];
    cell.dataset.r = r; cell.dataset.c = c;
    cell.id = `cell-${{r}}-${{c}}`;
    gridEl.appendChild(cell);
  }}
}}

// ── SVG connecting line ──────────────────────────────────────
const svg = document.getElementById('svg-overlay');

function cellCenter(el) {{
  const wrap = document.getElementById('grid-wrap');
  const wRect = wrap.getBoundingClientRect();
  const eRect = el.getBoundingClientRect();
  return {{
    x: eRect.left - wRect.left + eRect.width / 2,
    y: eRect.top  - wRect.top  + eRect.height / 2,
    r: eRect.width / 2
  }};
}}

function drawLine(pts, color, cls) {{
  if (pts.length < 2) return;
  // Stroke width = cell diameter so line fills the gap between circles
  const strokeW = pts[0].r * 1.55;
  for (let i = 1; i < pts.length; i++) {{
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1', pts[i-1].x); line.setAttribute('y1', pts[i-1].y);
    line.setAttribute('x2', pts[i].x);   line.setAttribute('y2', pts[i].y);
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-width', strokeW);
    line.setAttribute('stroke-linecap','round');
    line.setAttribute('opacity', cls === 'sel-line' ? '0.7' : '0.85');
    line.classList.add(cls);
    svg.appendChild(line);
  }}
}}

function drawSelectionLine(cells) {{
  svg.querySelectorAll('.sel-line').forEach(e => e.remove());
  if (cells.length < 2) return;
  drawLine(cells.map(cellCenter), '#f5a623', 'sel-line');
}}

function drawFoundLine(cells, color) {{
  const pts = cells.map(([r,c]) => {{
    const el = document.getElementById(`cell-${{r}}-${{c}}`);
    return el ? cellCenter(el) : null;
  }}).filter(Boolean);
  drawLine(pts, color, 'found-line');
}}

function redrawAllFoundLines() {{
  svg.querySelectorAll('.found-line').forEach(e => e.remove());
  foundWords.forEach(w => {{
    const cells = PLACEMENTS[w];
    if (cells) drawFoundLine(cells, COLOR_MAP[w] || '#1565c0');
  }});
}}

function redrawAllFoundLines() {{
  svg.querySelectorAll('.found-line').forEach(e=>e.remove());
  foundWords.forEach(w => {{
    const cells = PLACEMENTS[w];
    if (cells) drawFoundLine(cells, COLOR_MAP[w]||'#1565c0');
  }});
}}

// ── Colour found cells ───────────────────────────────────────
function colourFound() {{
  document.querySelectorAll('.cell').forEach(el => {{
    el.classList.remove('found');
    el.style.background='';
  }});
  foundWords.forEach(w => {{
    const cells = PLACEMENTS[w];
    if (!cells) return;
    const col = COLOR_MAP[w]||'#1565c0';
    cells.forEach(([r,c]) => {{
      const el = document.getElementById(`cell-${{r}}-${{c}}`);
      if (el) {{ el.classList.add('found'); el.style.background=col; }}
    }});
  }});
}}

// ── Score ────────────────────────────────────────────────────
function updateScore() {{
  const row = document.getElementById('score-row');
  row.innerHTML='';
  for (let i=0;i<TOTAL;i++) {{
    const b=document.createElement('div');
    b.className='score-bubble'+(i<foundWords.length?' done':'');
    if (i<foundWords.length) b.style.background=COLOR_MAP[foundWords[i]]||'#1565c0';
    row.appendChild(b);
  }}
  document.getElementById('score-text').textContent=`${{foundWords.length}} / ${{TOTAL}} found`;
}}

function updateFoundList() {{
  const c=document.getElementById('found-words-container');
  c.innerHTML='';
  foundWords.forEach(w=>{{
    const d=document.createElement('div');
    d.className='found-word-item';
    d.style.background=COLOR_MAP[w]||'#1565c0';
    d.innerHTML=`<span>✓</span><span>${{w}}</span>`;
    c.appendChild(d);
  }});
}}

function showToast(msg,duration=2000) {{
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),duration);
}}

// ── Drag ─────────────────────────────────────────────────────
function getCellAt(x,y) {{
  const el=document.elementFromPoint(x,y);
  return el&&el.classList.contains('cell')?el:null;
}}
function clearSelection() {{
  selectedCells.forEach(el=>el.classList.remove('selecting'));
  selectedCells=[];
  svg.querySelectorAll('.sel-line,.sel-dot').forEach(e=>e.remove());
}}
function isAdjacent(a,b) {{
  return Math.abs(+a.dataset.r-+b.dataset.r)<=1 &&
         Math.abs(+a.dataset.c-+b.dataset.c)<=1;
}}
function tryMatch() {{
  const sel=selectedCells.map(el=>[+el.dataset.r,+el.dataset.c]);
  const selR=[...sel].reverse();
  for (const [word,cells] of Object.entries(PLACEMENTS)) {{
    if (foundWords.includes(word)) continue;
    if (JSON.stringify(sel)===JSON.stringify(cells)||
        JSON.stringify(selR)===JSON.stringify(cells)) {{
      foundWords.push(word);
      colourFound();
      setTimeout(redrawAllFoundLines, 50);
      updateScore(); updateFoundList();
      showToast(`✓ ${{word}}!`);
      const url=new URL(window.location.href);
      url.searchParams.set('found',word);
      window.parent.location.href=url.toString();
      return true;
    }}
  }}
  selectedCells.forEach(el=>{{
    el.classList.add('shake');
    setTimeout(()=>el.classList.remove('shake'),400);
  }});
  return false;
}}

gridEl.addEventListener('pointerdown',e=>{{
  const cell=getCellAt(e.clientX,e.clientY);
  if (!cell||cell.classList.contains('found')) return;
  e.preventDefault();
  isSelecting=true; clearSelection();
  cell.classList.add('selecting');
  selectedCells=[cell];
  gridEl.setPointerCapture(e.pointerId);
}});

gridEl.addEventListener('pointermove',e=>{{
  if (!isSelecting) return;
  const cell=getCellAt(e.clientX,e.clientY);
  if (!cell||cell.classList.contains('found')) return;
  if (selectedCells.length>1&&cell===selectedCells[selectedCells.length-2]) {{
    selectedCells[selectedCells.length-1].classList.remove('selecting');
    selectedCells.pop();
    drawSelectionLine(selectedCells);
    return;
  }}
  if (selectedCells.includes(cell)) return;
  if (!isAdjacent(selectedCells[selectedCells.length-1],cell)) return;
  cell.classList.add('selecting');
  selectedCells.push(cell);
  drawSelectionLine(selectedCells);
}});

gridEl.addEventListener('pointerup',e=>{{
  if (!isSelecting) return;
  isSelecting=false;
  if (selectedCells.length>=2) {{
    const matched=tryMatch();
    if (!matched) setTimeout(clearSelection,400);
    else clearSelection();
  }} else clearSelection();
}});

// ── Hint ─────────────────────────────────────────────────────
document.getElementById('hint-btn').addEventListener('click',()=>{{
  if (hintsUsed>=MAX_HINTS||hintActive) return;
  const rem=Object.keys(PLACEMENTS).filter(w=>!foundWords.includes(w));
  if (!rem.length) return;
  const word=rem[Math.floor(Math.random()*rem.length)];
  const cells=PLACEMENTS[word];
  const col=COLOR_MAP[word]||'#7c4dff';
  hintsUsed++; hintActive=true;
  const left=MAX_HINTS-hintsUsed;
  const btn=document.getElementById('hint-btn');
  btn.textContent=`💡 Hint (${{left}} left)`;
  if (hintsUsed>=MAX_HINTS) btn.disabled=true;
  cells.forEach(([r,c])=>{{
    const el=document.getElementById(`cell-${{r}}-${{c}}`);
    if (!el) return;
    const orig=el.style.background;
    el.style.background=col; el.style.opacity='0.75';
    setTimeout(()=>{{el.style.background=orig;el.style.opacity='1';}},1800);
  }});
  showToast(`💡 ${{word.length}}-letter word`,2500);
  setTimeout(()=>{{hintActive=false;}},2000);
  const url=new URL(window.location.href);
  url.searchParams.set('hints',hintsUsed);
  window.parent.location.href=url.toString();
}});

// ── Submit ────────────────────────────────────────────────────
document.getElementById('submit-btn').addEventListener('click',()=>{{
  if (!confirm('Submit your answers now?')) return;
  const url=new URL(window.location.href);
  url.searchParams.set('submit','1');
  window.parent.location.href=url.toString();
}});

// ── Timer ─────────────────────────────────────────────────────
function updateTimer() {{
  if (timerSecs<=0) return;
  timerSecs--;
  const m=Math.floor(timerSecs/60).toString().padStart(2,'0');
  const s=(timerSecs%60).toString().padStart(2,'0');
  const el=document.getElementById('timer-display');
  el.textContent=`${{m}}:${{s}}`;
  if(timerSecs<120) el.classList.add('warning');
  else el.classList.remove('warning');
}}
setInterval(updateTimer,1000);

// ── Init ──────────────────────────────────────────────────────
window.addEventListener('load',()=>{{
  colourFound();
  setTimeout(redrawAllFoundLines, 100);
  updateScore();
  updateFoundList();
}});
</script>
</body>
</html>"""

components.html(GAME_HTML, height=680, scrolling=False)
