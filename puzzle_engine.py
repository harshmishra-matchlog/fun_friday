# ============================================================
# puzzle_engine.py — Word-Search Grid Generator
# ============================================================
import random
import json
from config import GRID_SIZE


DIRECTIONS = [
    ( 0,  1),   # right
    ( 0, -1),   # left
    ( 1,  0),   # down
    (-1,  0),   # up
    ( 1,  1),   # down-right
    ( 1, -1),   # down-left
    (-1,  1),   # up-right
    (-1, -1),   # up-left
]

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_grid(words: list[str], size: int = GRID_SIZE):
    """
    Place words in a size×size grid.
    Returns:
        grid        — 2-D list of characters
        placements  — dict  {word: [(r,c), ...]}  cells each word occupies
    """
    words = [w.upper().replace(" ", "") for w in words]
    words.sort(key=len, reverse=True)   # place longest words first

    grid = [["" for _ in range(size)] for _ in range(size)]
    placements: dict[str, list[tuple[int, int]]] = {}

    for word in words:
        placed = False
        attempts = 0
        shuffled_dirs = DIRECTIONS.copy()
        random.shuffle(shuffled_dirs)

        while not placed and attempts < 500:
            attempts += 1
            dr, dc = random.choice(shuffled_dirs)
            r = random.randint(0, size - 1)
            c = random.randint(0, size - 1)

            end_r = r + dr * (len(word) - 1)
            end_c = c + dc * (len(word) - 1)

            if not (0 <= end_r < size and 0 <= end_c < size):
                continue

            # Check if cells are free or have same letter
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

        if not placed:
            # If we couldn't place it, skip (admin word list might be too large)
            pass

    # Fill remaining empty cells with random letters
    for r in range(size):
        for c in range(size):
            if grid[r][c] == "":
                grid[r][c] = random.choice(ALPHABET)

    return grid, placements


def grid_to_json(grid) -> str:
    return json.dumps(grid)


def placements_to_json(placements) -> str:
    # Convert tuple keys to list for JSON serialisation
    serialisable = {word: cells for word, cells in placements.items()}
    return json.dumps(serialisable)


def json_to_grid(s: str):
    return json.loads(s)


def json_to_placements(s: str) -> dict[str, list[list[int]]]:
    return json.loads(s)


def validate_selection(selected_cells: list[tuple[int, int]],
                       placements: dict[str, list]) -> str | None:
    """
    Check whether selected_cells match any word's placement.
    Returns the matched word or None.
    selected_cells can be in forward or reverse order.
    """
    sel = [list(c) for c in selected_cells]
    sel_rev = sel[::-1]
    for word, cells in placements.items():
        if sel == cells or sel_rev == cells:
            return word
    return None
