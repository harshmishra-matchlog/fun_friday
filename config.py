# ============================================================
# config.py — Fun Friday Puzzle Configuration
# ============================================================

ADMIN_EMAILS = [
    "kulshresthauk71@gmail.com",
    "harsh.mishra@matchlog.delivery",
]

# ── Admin password — change this anytime, just restart the app ──
ADMIN_PASSWORD = "automationpaglu"

# Puzzle window: Friday 11 AM to 3 PM (IST)
PUZZLE_DAY = 7          # Monday=0 … Friday=4
PUZZLE_START_HOUR = 0  # 11:00 AM
PUZZLE_END_HOUR   = 23  # 03:00 PM
PUZZLE_DURATION_MINUTES = 15   # per-player timer

GRID_SIZE = 12          # 12×12 grid

# ── Weekly word pool (admin can override via DB) ─────────────
# Each week's words are drawn from this master list.
# Admin can upload a custom list through the admin panel.

MASTER_WORD_POOL = [
    # Containers & Equipment
    "CONTAINER", "TEUS", "FEUS", "REEFER", "FLATRACK", "OPENTOP",
    "TANKTAINER", "ISOCONTAINER", "FLEXIBAG",
    # Documents
    "BILLOFLADING", "SEAWAY", "AIRWAY", "MANIFEST", "INVOICE",
    "PACKINGLIST", "COO", "CERTIFICATE", "PACKING",
    # Ports & Locations
    "NHAVASHEVA", "MUNDRA", "PIPAVAV", "HAZIRA", "CHENNAI",
    "KOLKATA", "COCHIN", "VIZAG", "TUTICORIN",
    # Shipping Lines
    "MAERSK", "MSC", "COSCO", "HAPAG", "EVERGREEN",
    "YANGMING", "OOCL", "ZIMS", "SEALAND",
    # Logistics Terms
    "FREIGHT", "DEMURRAGE", "DETENTION", "FORWARDER", "BROKER",
    "CUSTOMS", "CLEARANCE", "BONDED", "WAREHOUSE", "FUMIGATION",
    # Trade Terms
    "EXPORT", "IMPORT", "INCOTERMS", "EXWORKS", "CIFPORT",
    "FOBPORT", "DDPTERM", "CFRTERM", "LCLETTEROFCREDIT",
    # Operations
    "STUFFING", "DESTUFFING", "TRANSSHIPMENT", "CONSOLIDATION",
    "DECONSOLIDATION", "FCLTRUCK", "LCLTRUCK", "SURVEY",
    # Ports & Terminals
    "TERMINAL", "BERTH", "VESSEL", "VOYAGE", "PORTOFLOADING",
    "PORTOFDISCHARGE", "TRANSHIPMENT", "GATEWAY", "FEEDER",
    # Regulatory
    "SOLAS", "IMDG", "HAZMAT", "DANGEROUS", "PHYTOSANITARY",
    "QUARANTINE", "INSPECTION", "ANTIDUMPING",
    # Finance & Insurance
    "INSURANCE", "PREMIUM", "SURVEY", "CLAUSES", "AVERAGE",
    "SUBROGATION", "DEDUCTIBLE",
    # Short codes
    "CFS", "ICD", "CY", "POL", "POD", "ETA", "ETD",
    "FCL", "LCL", "MTO", "NVOCC", "BL", "DO", "NOC",
    "VGM", "SOC", "COC", "IGM", "EGM",
]

# Words selected each week (admin sets this; default = auto-pick 20)
DEFAULT_WORDS_PER_PUZZLE = 20

# SQLite DB path (relative to app.py)
DB_PATH = "fun_friday.db"

APP_TITLE  = "🚢 Fun Friday Puzzle"
ORG_NAME   = "Matchlog"
LOGO_EMOJI = "⚓"
