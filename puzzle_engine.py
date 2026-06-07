# ============================================================
# puzzle_engine.py — NYT Strands-style snake placement
# ============================================================
import random, json, math

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def neighbours(r, c, size):
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr==0 and dc==0: continue
            nr,nc = r+dr, c+dc
            if 0<=nr<size and 0<=nc<size:
                yield nr,nc

def _place_word_snake(word, grid, occupied, size, attempts=800):
    for _ in range(attempts):
        r = random.randint(0, size-1)
        c = random.randint(0, size-1)
        if occupied[r][c] and grid[r][c] != word[0]:
            continue
        path    = [(r,c)]
        visited = {(r,c)}
        failed  = False
        for ch in word[1:]:
            nbrs = list(neighbours(path[-1][0], path[-1][1], size))
            random.shuffle(nbrs)
            placed = False
            for nr,nc in nbrs:
                if (nr,nc) in visited: continue
                if occupied[nr][nc] and grid[nr][nc] != ch: continue
                path.append((nr,nc))
                visited.add((nr,nc))
                placed = True
                break
            if not placed:
                failed = True
                break
        if not failed:
            return path
    return None

def optimal_grid_size(words):
    total_letters = sum(len(w) for w in words)
    size = math.ceil(math.sqrt(total_letters * 1.4))
    return max(size, 8)   # minimum 8x8

def generate_grid(words, size=None):
    words = [w.upper().replace(" ","") for w in words]
    words.sort(key=len, reverse=True)

    if size is None:
        size = optimal_grid_size(words)

    grid     = [["" for _ in range(size)] for _ in range(size)]
    occupied = [[False]*size for _ in range(size)]
    placements = {}

    for word in words:
        path = _place_word_snake(word, grid, occupied, size)
        if path:
            for i,(r,c) in enumerate(path):
                grid[r][c] = word[i]
                occupied[r][c] = True
            placements[word] = path

    # Fill empties with filler snakes
    filler_pool = [
        "PORT","DOCK","SHIP","LOAD","HOLD","SEAL","DECK","HULL",
        "TIDE","WAVE","BUOY","KEEL","HELM","ROPE","HOOK","BOLT",
        "GATE","RAMP","TANK","DRUM","SACK","BALE","COIL",
        "BOX","BIN","BAY","TON","TEU","FCL","LCL","CFS",
        "ETA","ETD","POL","POD","BL","DO","VGM","NOC","IGM",
        "CAP","LOT","AWB","COD","SKU","PKG","MTO","CTO","DG",
    ]
    random.shuffle(filler_pool)

    for attempt in range(1000):
        empty = [(r,c) for r in range(size) for c in range(size) if not occupied[r][c]]
        if not empty: break
        if not filler_pool: break
        word = filler_pool.pop()
        if len(word) > len(empty): continue
        path = _place_word_snake(word, grid, occupied, size, attempts=300)
        if path:
            for i,(r,c) in enumerate(path):
                grid[r][c] = word[i]
                occupied[r][c] = True
            placements[f"__{word}_{attempt}"] = path

    # Remaining single cells
    for r in range(size):
        for c in range(size):
            if not occupied[r][c]:
                grid[r][c] = random.choice(ALPHABET)

    return grid, placements, size   # return size too

def real_placements(placements):
    return {k:v for k,v in placements.items() if not k.startswith("__")}

def grid_to_json(grid):    return json.dumps(grid)
def placements_to_json(p): return json.dumps(p)
def json_to_grid(s):       return json.loads(s)
def json_to_placements(s): return json.loads(s)

def validate_selection(selected_cells, placements):
    sel     = [list(c) for c in selected_cells]
    sel_rev = sel[::-1]
    for word,cells in placements.items():
        if word.startswith("__"): continue
        if sel==cells or sel_rev==cells: return word
    return None
