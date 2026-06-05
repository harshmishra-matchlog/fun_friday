# ============================================================
# admin.py — Admin Panel for Fun Friday Puzzle
# ============================================================
import streamlit as st
import json
import io
from datetime import date, timedelta

import database as db
from config import MASTER_WORD_POOL, GRID_SIZE, DEFAULT_WORDS_PER_PUZZLE


def _next_fridays(n=4):
    """Return the next n Friday dates including today if Friday."""
    fridays = []
    d = date.today()
    while len(fridays) < n:
        if d.weekday() == 4:
            fridays.append(d)
        d += timedelta(days=1)
        if len(fridays) == 0 and d.weekday() > 4:
            d += timedelta(days=(7 - d.weekday() + 4))
    return fridays


def render_admin(admin_email: str):
    st.markdown("## 🔐 Admin Panel")
    st.info(f"Logged in as **{admin_email}**")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Manage Words",
        "🔄 Regenerate Puzzle",
        "📊 Results & Export",
        "🏆 All-Time Stats",
    ])

    # ─── TAB 1: Manage Words ──────────────────────────────────
    with tab1:
        st.markdown("### Upload Words for a Specific Friday")

        fridays = _next_fridays(4)
        friday_options = {f.strftime("%d %b %Y (%A)"): f.isoformat() for f in fridays}
        chosen_label = st.selectbox("Select Friday", list(friday_options.keys()))
        chosen_date  = friday_options[chosen_label]

        st.markdown("---")
        st.markdown("#### Option A — Pick from Master Word Pool")
        selected_from_pool = st.multiselect(
            "Select words (max 25, each ≤12 chars for 12×12 grid)",
            options=[w for w in MASTER_WORD_POOL if len(w) <= GRID_SIZE],
            max_selections=25,
        )

        st.markdown("#### Option B — Paste Custom Words")
        st.caption("One word per line, no spaces, max 12 characters each")
        custom_text = st.text_area("Custom words", height=180,
                                    placeholder="VESSEL\nFREIGHT\nMAERSK\nCONTAINER")

        if st.button("💾 Save Word List", use_container_width=True):
            words = list(selected_from_pool)
            for w in custom_text.strip().splitlines():
                w = w.strip().upper().replace(" ", "")
                if w and len(w) <= GRID_SIZE and w not in words:
                    words.append(w)
            if len(words) < 5:
                st.error("Please provide at least 5 words.")
            else:
                db.save_admin_word_list(chosen_date, words, admin_email)
                st.success(f"✅ Saved {len(words)} words for {chosen_label}.")
                st.json(words)

    # ─── TAB 2: Regenerate Puzzle ─────────────────────────────
    with tab2:
        st.markdown("### Regenerate Puzzle Grid")
        st.warning(
            "⚠️ Regenerating will delete the current puzzle for that week "
            "and create a new grid. Existing player sessions will be preserved "
            "but may show incorrect placements."
        )

        fridays       = _next_fridays(4)
        friday_opts2  = {f.strftime("%d %b %Y (%A)"): f.isoformat() for f in fridays}
        chosen2_label = st.selectbox("Select Friday ", list(friday_opts2.keys()))
        chosen2_date  = friday_opts2[chosen2_label]

        if st.button("🔄 Regenerate Now", use_container_width=True):
            puzzle = db.regenerate_puzzle(chosen2_date, admin_email)
            words  = json.loads(puzzle["words"])
            st.success(f"✅ New puzzle generated for {chosen2_label} with {len(words)} words.")
            st.markdown("**Words in this puzzle:**")
            st.write(" | ".join(words))

        st.markdown("---")
        st.markdown("### Preview Current Puzzle")
        all_puzzles = db.get_all_puzzles()
        if all_puzzles:
            p = all_puzzles[0]
            st.markdown(f"**Date:** {p['week_date']}")
            words = json.loads(p["words"])
            st.markdown("**Words:** " + " · ".join(words))

            grid = json.loads(p["grid"])
            # Display grid as text
            grid_str = ""
            for row in grid:
                grid_str += "  ".join(row) + "\n"
            st.code(grid_str, language=None)

    # ─── TAB 3: Results & Export ──────────────────────────────
    with tab3:
        st.markdown("### Player Results")

        all_puzzles = db.get_all_puzzles()
        if not all_puzzles:
            st.info("No puzzles created yet.")
        else:
            puzzle_opts = {p["week_date"]: p["id"] for p in all_puzzles}
            chosen_week = st.selectbox("Select Week", list(puzzle_opts.keys()))
            pid         = puzzle_opts[chosen_week]

            lb = db.get_leaderboard(pid)
            if not lb:
                st.info("No submissions for this week yet.")
            else:
                st.markdown(f"**{len(lb)} submissions**")

                # Table
                import pandas as pd
                df = pd.DataFrame(lb)
                df["time_fmt"] = df["time_taken"].apply(
                    lambda s: f"{s//60}m {s%60:02d}s"
                )
                df = df.rename(columns={
                    "player_name": "Name",
                    "player_email": "Email",
                    "department": "Dept",
                    "score": "Words Found",
                    "time_fmt": "Time Taken",
                })
                st.dataframe(
                    df[["Name", "Email", "Dept", "Words Found", "Time Taken"]],
                    use_container_width=True,
                    hide_index=True,
                )

                # Export to Excel
                try:
                    import openpyxl
                    buf = io.BytesIO()
                    df[["Name", "Email", "Dept", "Words Found", "Time Taken"]].to_excel(
                        buf, index=False, engine="openpyxl"
                    )
                    st.download_button(
                        "📥 Download Excel",
                        data=buf.getvalue(),
                        file_name=f"fun_friday_{chosen_week}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except ImportError:
                    st.info("Install `openpyxl` for Excel export: `pip install openpyxl`")

                # Declare winner
                if lb:
                    winner = lb[0]
                    st.markdown("---")
                    st.markdown(f"""
                    <div style="background:#1b2a00;border:2px solid #76c442;
                                border-radius:12px;padding:20px;text-align:center;">
                      <h3>🥇 This Week's Winner</h3>
                      <h2>{winner['player_name']}</h2>
                      <p>{winner['score']} words · ⏱ {winner['time_taken']//60}m {winner['time_taken']%60:02d}s</p>
                    </div>
                    """, unsafe_allow_html=True)

    # ─── TAB 4: All-time Stats ────────────────────────────────
    with tab4:
        st.markdown("### 🏆 All-Time Hall of Fame")
        all_puzzles = db.get_all_puzzles()
        if not all_puzzles:
            st.info("No data yet.")
            return

        import pandas as pd
        all_rows = []
        for p in all_puzzles:
            lb = db.get_leaderboard(p["id"])
            for i, r in enumerate(lb):
                r["week"] = p["week_date"]
                r["rank"] = i + 1
                all_rows.append(r)

        if not all_rows:
            st.info("No submissions yet across any week.")
            return

        df_all = pd.DataFrame(all_rows)

        # Most wins
        winners = df_all[df_all["rank"] == 1].groupby("player_name").size().reset_index()
        winners.columns = ["Player", "Wins"]
        winners = winners.sort_values("Wins", ascending=False)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Most Wins**")
            st.dataframe(winners, hide_index=True, use_container_width=True)

        with col2:
            st.markdown("**Participation Count**")
            part = df_all.groupby("player_name").size().reset_index()
            part.columns = ["Player", "Sessions"]
            part = part.sort_values("Sessions", ascending=False)
            st.dataframe(part, hide_index=True, use_container_width=True)

    if st.button("← Back to Game", use_container_width=True):
        st.session_state.admin_mode = False
        st.rerun()
