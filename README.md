# 🚢 Fun Friday Puzzle — Setup Guide

**A weekly word-search game for Matchlog employees. Every Friday, 11AM–3PM.**

---

## 📁 Project Structure

```
fun_friday_puzzle/
├── app.py              ← Main Streamlit app (run this)
├── admin.py            ← Admin panel module
├── database.py         ← SQLite database layer
├── puzzle_engine.py    ← Word-search grid generator
├── config.py           ← All settings (edit this!)
├── requirements.txt    ← Python dependencies
└── fun_friday.db       ← Auto-created SQLite database
```

---

## ⚡ Quick Start (Local / VS Code)

### 1. Prerequisites
- Python 3.10 or higher
- VS Code with Python extension

### 2. Clone / copy the folder
Put the `fun_friday_puzzle/` folder anywhere on your machine.

### 3. Create a virtual environment (recommended)
```bash
cd fun_friday_puzzle
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the app
```bash
streamlit run app.py
```
App opens at **http://localhost:8501**

---

## 🔧 Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `ADMIN_EMAILS` | kulshresthauk71@gmail.com, harsh.mishra@matchlog.delivery | Users with admin access |
| `PUZZLE_DAY` | 4 (Friday) | 0=Monday, 4=Friday |
| `PUZZLE_START_HOUR` | 11 | 11:00 AM IST |
| `PUZZLE_END_HOUR` | 15 | 3:00 PM IST |
| `PUZZLE_DURATION_MINUTES` | 15 | Per-player countdown |
| `GRID_SIZE` | 12 | 12×12 grid |
| `DEFAULT_WORDS_PER_PUZZLE` | 20 | Words auto-selected each week |

---

## 🎮 How the Game Works

1. **Employee opens the app** during Friday 11AM–3PM IST
2. **Enters name + email + department** → starts their personal 15-min timer
3. **Clicks letters** in the grid to form words (any direction)
4. **Words turn green** when found; score updates live
5. **Submits early** or auto-submits when time runs out
6. **Live leaderboard** ranks: most words found → tie-break by least time

---

## 🔐 Admin Panel

Admins (`kulshresthauk71@gmail.com` or `harsh.mishra@matchlog.delivery`) see a **"Open Admin Panel"** button in the sidebar after logging in.

### Admin can:
- **Upload custom word list** for any upcoming Friday
- **Regenerate the puzzle grid** (new random layout, same words)
- **View all player submissions** with scores
- **Download results as Excel**
- **See the weekly winner** declared automatically
- **All-time stats** — most wins, most participation

---

## 🌐 Deploy on Streamlit Cloud (Free)

1. Push your folder to a **GitHub repository** (private is fine)
2. Go to **[share.streamlit.io](https://share.streamlit.io)**
3. Click "New app" → Connect your GitHub repo
4. Set main file path: `fun_friday_puzzle/app.py`
5. Click Deploy

> **Note:** On Streamlit Cloud, the SQLite DB resets on each redeploy.  
> For persistent data, swap SQLite for **Supabase (free tier)** — just replace  
> `database.py` connection logic. Ask your dev to help with that migration.

---

## 🚀 Deploy on Internal Server (Recommended for Production)

```bash
# On your server / VPS
pip install -r requirements.txt
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

Access at `http://YOUR_SERVER_IP:8501`

For SSL/domain, put Nginx in front as a reverse proxy.

---

## 📅 Weekly Workflow for Admins

**Every Wednesday or Thursday:**
1. Open the app → Admin Panel → "Manage Words" tab
2. Select the upcoming Friday
3. Pick words from the master pool OR paste custom words
4. Click Save → Puzzle auto-generates

**Friday during the event:**
- Monitor real-time leaderboard in Results tab
- Download Excel at 3PM for records

---

## 🛠 Customisation Tips

**Change word bank:** Edit `MASTER_WORD_POOL` in `config.py`

**Change timing:** Edit `PUZZLE_START_HOUR` / `PUZZLE_END_HOUR` in `config.py`

**Change grid size:** Edit `GRID_SIZE` in `config.py` (max recommended: 15)

**Add your logo:** Replace the emoji in `APP_TITLE` / `LOGO_EMOJI` in `config.py`

**Test outside Friday:** 
```python
# In config.py, temporarily change PUZZLE_DAY to today's weekday:
PUZZLE_DAY = 0   # Monday
PUZZLE_START_HOUR = 0
PUZZLE_END_HOUR = 23
```

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` |
| Puzzle closed outside Friday | Expected! Change `PUZZLE_DAY` in config.py for testing |
| "already played" showing incorrectly | Clear `fun_friday.db` file to reset all data |
| Grid words don't fit | Shorten words to ≤12 chars or increase `GRID_SIZE` |

---

Built with ❤️ for Matchlog Fun Fridays 🚢
