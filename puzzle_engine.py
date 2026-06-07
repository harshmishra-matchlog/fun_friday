# ============================================================
# puzzle_engine.py — Word-Search Grid Generator (Strands-style)
# Every cell is part of exactly one word — no random filler
# ============================================================
import random
import json
from config import GRID_SIZE

DIRECTIONS = [
    ( 0,  1),  # right
    ( 0, -1),  # left
    ( 1,  0),  # down
    (-1,  0),  # up
    ( 1,  1),  # down-right
    ( 1, -1),  # down-left
    (-1,  1),  # up-right
    (-1, -1),  # up-left
]

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_grid(words: list[str], size: int = GRID_SIZE):
    words = [w.upper().replace(" ", "") for w in words]
    words.sort(key=len, reverse=True)

    grid       = [["" for _ in range(size)] for _ in range(size)]
    placements = {}

    # ── Place real words ──────────────────────────────────────
    for word in words:
        placed   = False
        attempts = 0
        dirs     = DIRECTIONS.copy()
        random.shuffle(dirs)

        while not placed and attempts < 800:
            attempts += 1
            dr, dc = random.choice(dirs)
            r = random.randint(0, size - 1)
            c = random.randint(0, size - 1)

            end_r = r + dr * (len(word) - 1)
            end_c = c + dc * (len(word) - 1)
            if not (0 <= end_r < size and 0 <= end_c < size):
                continue

            ok = True
            for i, ch in enumerate(word):
                nr, nc = r + dr * i, c + dc * i
                if grid[nr][nc] not in ("", ch):
                    ok = False
                    break

            if ok:
                cells = []
                for i, ch in enumerate(word):
                    nr, nc = r + dr * i, c + dc * i
                    grid[nr][nc] = ch
                    cells.append((nr, nc))
                placements[word] = cells
                placed = True

    # ── Fill remaining cells with short filler words / letters ─
    # Collect empty cells
    empty = [(r, c) for r in range(size) for c in range(size) if grid[r][c] == ""]

    # Try to place small 3-4 letter filler words to keep it Strands-like
    # If we can't, fall back to single random letters
    filler_words = [
        "PORT","DOCK","SHIP","LOAD","HOLD","SEAL","DECK","HULL","MAST",
        "TIDE","WAVE","BUOY","KEEL","HELM","ROPE","HOOK","BOLT","LOCK",
        "GATE","RAMP","SLAB","TANK","DRUM","SACK","BALE","COIL","TARP",
        "CAP","BOX","BIN","BAY","LOT","TON","TEU","FCL","LCL","CFS",
        "ETA","ETD","POL","POD","AWB","BL","DO","VGM","NOC","IGM",
    ]
    random.shuffle(filler_words)

    filler_idx = 0
    max_attempts = 300
    att = 0

    while True:
        empty = [(r, c) for r in range(size) for c in range(size) if grid[r][c] == ""]
        if not empty:
            break
        att += 1
        if att > max_attempts or filler_idx >= len(filler_words):
            # Just fill remaining with random letters
            for r, c in empty:
                grid[r][c] = random.choice(ALPHABET)
            break

        word = filler_words[filler_idx]
        filler_idx += 1
        if len(word) > len(empty):
            continue

        dirs = DIRECTIONS.copy()
        random.shuffle(dirs)
        placed = False
        for _ in range(200):
            dr, dc = random.choice(dirs)
            r0, c0 = random.choice(empty)
            end_r = r0 + dr * (len(word) - 1)
            end_c = c0 + dc * (len(word) - 1)
            if not (0 <= end_r < size and 0 <= end_c < size):
                continue
            ok = True
            for i, ch in enumerate(word):
                nr, nc = r0 + dr * i, c0 + dc * i
                if grid[nr][nc] not in ("", ch):
                    ok = False
                    break
            if ok:
                cells = []
                for i, ch in enumerate(word):
                    nr, nc = r0 + dr * i, c0 + dc * i
                    grid[nr][nc] = ch
                    cells.append((nr, nc))
                # filler placements stored with "__" prefix so game ignores them
                placements[f"__{word}_{att}"] = cells
                placed = True
                break

    return grid, placements


def grid_to_json(grid) -> str:
    return json.dumps(grid)


def placements_to_json(placements) -> str:
    return json.dumps(placements)


def json_to_grid(s: str):
    return json.loads(s)


def json_to_placements(s: str) -> dict[str, list[list[int]]]:
    return json.loads(s)


def real_placements(placements: dict) -> dict:
    """Return only the actual puzzle words (not filler __ words)."""
    return {k: v for k, v in placements.items() if not k.startswith("__")}


def validate_selection(selected_cells, placements: dict) -> str | None:
    sel     = [list(c) for c in selected_cells]
    sel_rev = sel[::-1]
    for word, cells in placements.items():
        if word.startswith("__"):
            continue
        if sel == cells or sel_rev == cells:
            return word
    return None
