# ============================================================
# app.py — Fun Friday Word-Search Puzzle  🚢
# Run:  streamlit run app.py
# ============================================================
import streamlit as st
import json
import time
import random
from datetime import datetime, date, timedelta
import pytz

import database as db
import admin as adm
from config import (
    ADMIN_EMAILS, ADMIN_PASSWORD, PUZZLE_DAY, PUZZLE_START_HOUR, PUZZLE_END_HOUR,
    PUZZLE_DURATION_MINUTES, GRID_SIZE, APP_TITLE, ORG_NAME, LOGO_EMOJI,
)
from puzzle_engine import json_to_grid, json_to_placements, validate_selection

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_TITLE} | {ORG_NAME}",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── IST timezone ──────────────────────────────────────────────
IST = pytz.timezone("Asia/Kolkata")

# ── DB init ───────────────────────────────────────────────────
db.init_db()

# ── Styles ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Space+Mono:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* White background, dark text everywhere */
.stApp { background: #f5f7fa; color: #1a1a2e; }
section[data-testid="stSidebar"] { background: #ffffff; }

/* ── Header banner ── */
.header-banner {
    background: linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #0d47a1 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(13,71,161,0.25);
}
.header-banner h1 { font-size: 2.4rem; margin: 0; color: #ffffff; }
.header-banner p  { color: #bbdefb; margin: 4px 0 0; font-size: 1rem; }

/* ── Countdown pill ── */
.countdown-pill {
    display: inline-block;
    background: #e53935;
    color: #ffffff;
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    padding: 8px 28px;
    border-radius: 50px;
    letter-spacing: 3px;
    margin: 8px 0;
}

/* ── Grid container ── */
.grid-container {
    display: grid;
    gap: 4px;
    user-select: none;
    width: fit-content;
    margin: 0 auto;
}

/* ── Individual cell ── */
.cell {
    width: 46px; height: 46px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Mono', monospace;
    font-size: 1.05rem; font-weight: 700;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid #cfd8dc;
    background: #ffffff;
    color: #1a1a2e;
    transition: all 0.12s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.cell:hover    { background: #e3f2fd; border-color: #1565c0; color: #0d47a1; transform: scale(1.08); }
.cell.active   { background: #1565c0; border-color: #0d47a1; color: #ffffff; transform: scale(1.1); }
.cell.found    { background: #2e7d32; border-color: #1b5e20; color: #ffffff; }
.cell.found-alt { background: #6a1b9a; border-color: #4a148c; color: #ffffff; }

/* ── Word chips ── */
.word-chip {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem; font-weight: 600;
    margin: 4px;
    letter-spacing: 0.5px;
    border: 1px solid;
}
.chip-found   { background: #e8f5e9; border-color: #2e7d32; color: #1b5e20; }
.chip-pending { background: #f5f5f5; border-color: #bdbdbd; color: #555555; }

/* ── Leaderboard ── */
.lb-card {
    background: #ffffff;
    border: 1px solid #e0e7ef;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 10px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.lb-rank  { font-size: 1.5rem; width: 40px; text-align: center; }
.lb-name  { font-weight: 700; font-size: 1rem; color: #1a1a2e; }
.lb-dept  { font-size: 0.75rem; color: #666666; }
.lb-score { margin-left: auto; text-align: right; }
.lb-score .num { font-family: 'Space Mono', monospace; font-size: 1.1rem; color: #0d47a1; }
.lb-score .tim { font-size: 0.75rem; color: #555555; }

/* ── Status boxes ── */
.closed-box {
    background: #fff8e1; border: 1px solid #f9a825;
    border-radius: 12px; padding: 32px; text-align: center; color: #e65100;
}
.winner-box {
    background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
    border: 2px solid #2e7d32; border-radius: 16px;
    padding: 28px; text-align: center; color: #1b5e20;
    animation: glow 2s ease-in-out infinite alternate;
}
@keyframes glow {
    from { box-shadow: 0 0 10px rgba(46,125,50,0.2); }
    to   { box-shadow: 0 0 28px rgba(46,125,50,0.5); }
}

/* ── Streamlit native element overrides ── */
.stButton > button {
    background: #0d47a1; color: #ffffff; border: none;
    border-radius: 8px; padding: 10px 24px;
    font-weight: 600; transition: background 0.2s;
}
.stButton > button:hover { background: #1565c0; }

/* Input boxes */
.stTextInput > div > div > input {
    background: #ffffff; color: #1a1a2e;
    border: 1px solid #cfd8dc; border-radius: 8px;
}
.stSelectbox > div > div {
    background: #ffffff; color: #1a1a2e;
}

/* Markdown text */
.stMarkdown p, .stMarkdown li { color: #1a1a2e; }

div[data-testid="stForm"] { border: none; padding: 0; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def now_ist() -> datetime:
    return datetime.now(IST)


def this_friday_date() -> date:
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7
    return today + timedelta(days=days_ahead)


def puzzle_is_open() -> bool:
    now = now_ist()
    if now.weekday() != PUZZLE_DAY:
        return False
    return PUZZLE_START_HOUR <= now.hour < PUZZLE_END_HOUR


def time_until_next_open() -> str:
    now = now_ist()
    days_until = (4 - now.weekday()) % 7
    if days_until == 0 and now.hour >= PUZZLE_END_HOUR:
        days_until = 7
    next_open = now.replace(
        hour=PUZZLE_START_HOUR, minute=0, second=0, microsecond=0
    ) + timedelta(days=days_until)
    delta = next_open - now
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s   = divmod(rem, 60)
    return f"{delta.days}d {h % 24:02d}h {m:02d}m" if delta.days else f"{h:02d}h {m:02d}m {s:02d}s"


def fmt_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"


FOUND_COLORS = [
    "found", "found-alt",
]

RANK_EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}


def _render_leaderboard(lb: list[dict]):
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
# Session state bootstrap
# ═══════════════════════════════════════════════════════════════

def init_state():
    defaults = {
        "logged_in":        False,
        "player_name":      "",
        "player_email":     "",
        "player_dept":      "",
        "game_started":     False,
        "session_id":       None,
        "puzzle_data":      None,
        "grid":             None,
        "placements":       None,
        "found_words":      [],
        "selected_cells":   [],
        "cell_colors":      {},
        "start_epoch":      None,
        "submitted":        False,
        "admin_mode":       False,
        "admin_pw_pending": False,   # waiting for admin password
        "admin_pw_error":   "",
        "admin_pw_name":    "",
        "admin_pw_email":   "",
        "admin_pw_dept":    "",
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
# Admin shortcut in sidebar
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ Admin Panel")
    if S.logged_in and S.player_email in ADMIN_EMAILS:
        if st.button("🔐 Open Admin Panel"):
            S.admin_mode = True
    else:
        st.info("Admin access for authorised emails only.")


# ═══════════════════════════════════════════════════════════════
# Admin mode
# ═══════════════════════════════════════════════════════════════

if S.admin_mode and S.logged_in and S.player_email in ADMIN_EMAILS:
    adm.render_admin(S.player_email)
    st.stop()


# ═══════════════════════════════════════════════════════════════
# LOGIN  (password gate for admin emails only)
# ═══════════════════════════════════════════════════════════════

if not S.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:

        # ── STEP 2: Admin password screen ────────────────────
        if S.admin_pw_pending:
            st.markdown("### 🔐 Admin Verification")
            st.info(f"**{S.admin_pw_email}** is an admin account. Enter the admin password to continue.")

            pw_input = st.text_input("Admin Password", type="password", placeholder="••••••••••••")

            if S.admin_pw_error:
                st.error(S.admin_pw_error)

            vcol1, vcol2 = st.columns(2)
            with vcol1:
                if st.button("✅ Verify", use_container_width=True):
                    if pw_input == ADMIN_PASSWORD:
                        S.logged_in         = True
                        S.player_name       = S.admin_pw_name
                        S.player_email      = S.admin_pw_email
                        S.player_dept       = S.admin_pw_dept
                        S.admin_mode        = True
                        S.admin_pw_pending  = False
                        S.admin_pw_error    = ""
                        st.rerun()
                    else:
                        S.admin_pw_error = "❌ Wrong password. Try again."
                        st.rerun()

            with vcol2:
                if st.button("← Back", use_container_width=True):
                    S.admin_pw_pending = False
                    S.admin_pw_error   = ""
                    st.rerun()

        # ── STEP 1: Name / email form ─────────────────────────
        else:
            st.markdown("### 👤 Enter your details to play")
            name  = st.text_input("Your Name *", placeholder="e.g. Utkarsh Kulshrestha")
            email = st.text_input("Work Email *", placeholder="you@matchlog.delivery")
            dept  = st.selectbox("Department", [
                "Operations", "Sales", "Finance", "Tech", "HR", "Management", "Other"
            ])

            if st.button("🚀 Let's Play!", use_container_width=True):
                name  = name.strip()
                email = email.strip().lower()

                if not name or not email:
                    st.error("Please fill in your name and email.")
                elif "@" not in email:
                    st.error("Enter a valid email address.")
                elif email in [e.lower() for e in ADMIN_EMAILS]:
                    # Admin → ask for password first
                    S.admin_pw_pending = True
                    S.admin_pw_name    = name
                    S.admin_pw_email   = email
                    S.admin_pw_dept    = dept
                    S.admin_pw_error   = ""
                    st.rerun()
                else:
                    # Regular user → straight in
                    S.logged_in    = True
                    S.player_name  = name
                    S.player_email = email
                    S.player_dept  = dept
                    S.admin_mode   = False
                    st.rerun()

    st.stop()


# ═══════════════════════════════════════════════════════════════
# PUZZLE WINDOW CHECK
# ═══════════════════════════════════════════════════════════════

is_open = puzzle_is_open()

# Admins can always play / preview
if not is_open and S.player_email not in ADMIN_EMAILS:
    st.markdown(f"""
    <div class="closed-box">
      <h2>🔒 Puzzle is Closed</h2>
      <p>Fun Friday puzzle opens every <strong>Friday 11:00 AM – 3:00 PM IST</strong>.</p>
      <p style="font-size:1.3rem; margin-top:12px;">
        ⏳ Next session opens in: <strong>{time_until_next_open()}</strong>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Show last week's leaderboard
    st.markdown("---")
    st.markdown("## 🏆 Last Week's Winners")
    all_puzzles = db.get_all_puzzles()
    if all_puzzles:
        lb = db.get_leaderboard(all_puzzles[0]["id"])
        _render_leaderboard(lb) if lb else st.info("No scores yet.")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# Load puzzle
# ═══════════════════════════════════════════════════════════════

friday_str = this_friday_date().isoformat()
puzzle     = db.get_or_create_puzzle(friday_str)

if S.puzzle_data is None or S.puzzle_data["id"] != puzzle["id"]:
    S.puzzle_data  = puzzle
    S.grid         = json_to_grid(puzzle["grid"])
    S.placements   = json_to_placements(puzzle["placements"])
    S.found_words  = []
    S.selected_cells = []
    S.cell_colors  = {}


# ═══════════════════════════════════════════════════════════════
# Already submitted?
# ═══════════════════════════════════════════════════════════════

if db.already_played(puzzle["id"], S.player_email) and not S.submitted:
    S.submitted = True


# ═══════════════════════════════════════════════════════════════
# Game not started yet
# ═══════════════════════════════════════════════════════════════

if not S.game_started and not S.submitted:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"### 👋 Welcome, **{S.player_name}**!")
        st.markdown(f"""
        **How to play:**
        - Find hidden logistics words in the grid
        - Click letters to select — words can be horizontal, vertical, or diagonal
        - You have **{PUZZLE_DURATION_MINUTES} minutes**
        - Most words + least time = 🏆 Winner!
        """)
        st.warning("⚠️ Once you click Start, your timer begins immediately!")
        if st.button("▶️ Start Puzzle!", use_container_width=True):
            sid = db.create_session(
                puzzle["id"], S.player_name, S.player_email, S.player_dept
            )
            S.session_id  = sid
            S.start_epoch = time.time()
            S.game_started = True
            st.rerun()
    st.stop()


# ═══════════════════════════════════════════════════════════════
# SUBMITTED VIEW
# ═══════════════════════════════════════════════════════════════

if S.submitted:
    st.markdown(f"""
    <div class="winner-box">
      <h2>🎉 Well done, {S.player_name}!</h2>
      <p>You found <strong>{len(S.found_words)}</strong> words out of {len(S.placements)}.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🏆 Live Leaderboard")
    lb = db.get_leaderboard(puzzle["id"])
    _render_leaderboard(lb)
    st.stop()


# ═══════════════════════════════════════════════════════════════
# ACTIVE GAME
# ═══════════════════════════════════════════════════════════════

# ── Timer check ───────────────────────────────────────────────
elapsed     = int(time.time() - S.start_epoch)
remaining   = max(0, PUZZLE_DURATION_MINUTES * 60 - elapsed)

if remaining == 0:
    db.submit_session(S.session_id, S.found_words)
    S.submitted = True
    st.rerun()

# ── Layout: puzzle left | info right ──────────────────────────
left, right = st.columns([3, 1.4], gap="large")

# ────────────────────────────────────────────────────────────
# RIGHT PANEL
# ────────────────────────────────────────────────────────────
with right:

    # Countdown
    mins, secs = divmod(remaining, 60)
    color = "#e53935" if remaining < 120 else "#0d47a1"
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:16px;">
      <div class="countdown-pill" style="background:{color};">
        {mins:02d}:{secs:02d}
      </div>
      <div style="color:#555555; font-size:0.8rem;">time remaining</div>
    </div>
    """, unsafe_allow_html=True)

    # Score
    total = len(json.loads(puzzle["words"]))
    st.markdown(f"""
    <div style="text-align:center; background:#e3f2fd; border:1px solid #90caf9;
                border-radius:12px; padding:14px; margin-bottom:16px;">
      <div style="font-size:2rem; font-weight:700; color:#0d47a1;">{len(S.found_words)}</div>
      <div style="color:#555555; font-size:0.8rem;">of {total} words found</div>
    </div>
    """, unsafe_allow_html=True)

    # Word list
    st.markdown("**📋 Words to Find:**")
    words_html = ""
    for w in json.loads(puzzle["words"]):
        if w in S.found_words:
            words_html += f'<span class="word-chip chip-found">✓ {w}</span>'
        else:
            words_html += f'<span class="word-chip chip-pending">{w}</span>'
    st.markdown(words_html, unsafe_allow_html=True)

    st.markdown("---")

    # Submit early
    if st.button("✅ Submit Now", use_container_width=True):
        db.submit_session(S.session_id, S.found_words)
        S.submitted = True
        st.rerun()

    st.markdown("---")
    st.markdown("## 🏆 Leaderboard")
    lb = db.get_leaderboard(puzzle["id"])
    _render_leaderboard(lb)


# ────────────────────────────────────────────────────────────
# LEFT PANEL — Interactive Grid
# ────────────────────────────────────────────────────────────
with left:
    st.markdown(f"#### 🔍 Find the hidden words — {S.player_name}")

    # ── Build the interactive grid with buttons ───────────────
    # We use a session-state click mechanism:
    # Each cell is a small button labelled with the letter.
    # Selected cells are tracked in S.selected_cells.

    grid      = S.grid
    n         = len(grid)
    cell_cols = st.columns(n, gap="small")

    for c in range(n):
        with cell_cols[c]:
            for r in range(n):
                letter  = grid[r][c]
                cell_id = (r, c)
                css     = S.cell_colors.get(cell_id, "")

                # Style override for selection
                if cell_id in S.selected_cells:
                    btn_style = "background:#1565c0; color:#fff; border:2px solid #42a5f5;"
                elif css == "found":
                    btn_style = "background:#1b5e20; color:#a5d6a7; border:2px solid #66bb6a;"
                elif css == "found-alt":
                    btn_style = "background:#4a148c; color:#e1bee7; border:2px solid #ab47bc;"
                else:
                    btn_style = ""

                if st.button(
                    letter,
                    key=f"cell_{r}_{c}",
                    help=f"Row {r+1}, Col {c+1}",
                ):
                    # ── Click logic ───────────────────────────
                    if cell_id not in S.selected_cells:
                        S.selected_cells.append(cell_id)
                    else:
                        # Deselect if clicked again
                        S.selected_cells.remove(cell_id)

                    # Try to match a word whenever ≥2 cells selected
                    if len(S.selected_cells) >= 2:
                        matched = validate_selection(S.selected_cells, S.placements)
                        if matched and matched not in S.found_words:
                            S.found_words.append(matched)
                            db.update_found_words(S.session_id, S.found_words)
                            # Colour all cells of the found word
                            color_cls = FOUND_COLORS[len(S.found_words) % 2]
                            for cell in S.placements[matched]:
                                S.cell_colors[tuple(cell)] = color_cls
                            S.selected_cells = []
                            st.balloons()
                        elif len(S.selected_cells) > GRID_SIZE:
                            # Too many selected without match — reset
                            S.selected_cells = []

                    st.rerun()

    # ── Helper message ────────────────────────────────────────
    if S.selected_cells:
        sel_letters = "".join(grid[r][c] for r, c in S.selected_cells)
        st.markdown(
            f"**Selected:** `{sel_letters}` — "
            f"click the last letter again to deselect, or keep selecting to form a word.",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "_Click letters in order to spell a word. "
            "Words can go in any direction!_"
        )

    # Auto-refresh every second for the countdown
    time.sleep(1)
    st.rerun()