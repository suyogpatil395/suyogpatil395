"""Generate an animated 'snake game' SVG on a contribution-style grid.
Food appears at a new random spot each time, the snake eats and grows, and
when it is long enough it bites its own tail, flashes, and a new round starts.
Several rounds with different food spots play before the loop repeats."""
import random, collections, sys, os

COLS, ROWS, CELL, GAP = 53, 7, 13, 3
STEP = 0.09          # seconds per move
ROUNDS = 3
MAX_LEN = 16
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 2026)
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def neighbors(p):
    for dx, dy in DIRS:
        q = (p[0] + dx, p[1] + dy)
        if 0 <= q[0] < COLS and 0 <= q[1] < ROWS:
            yield q

def bfs(start, goal, blocked):
    prev = {start: None}; dq = collections.deque([start])
    while dq:
        c = dq.popleft()
        if c == goal:
            path = []
            while c != start: path.append(c); c = prev[c]
            return path[::-1]
        for n in neighbors(c):
            if n not in prev and n not in blocked:
                prev[n] = c; dq.append(n)
    return None

def free_space(start, blocked):
    seen = {start}; dq = collections.deque([start])
    while dq:
        c = dq.popleft()
        for n in neighbors(c):
            if n not in seen and n not in blocked: seen.add(n); dq.append(n)
    return len(seen)

frames = []   # each: (snake list head-first, food, state) state: 'play' | 'dead' | 'blank'
for r in range(ROUNDS):
    y = random.randrange(ROWS); x = random.randrange(3, 12)
    snake = [(x, y), (x - 1, y), (x - 2, y)]
    def new_food():
        while True:
            f = (random.randrange(COLS), random.randrange(ROWS))
            if f not in snake and 4 < abs(f[0] - snake[0][0]) + abs(f[1] - snake[0][1]) < 22: return f
    food = new_food()
    for _ in range(4): frames.append((list(snake), food, "play"))
    guard = 0
    while True:
        guard += 1
        head = snake[0]
        if guard > 900: frames.append((list(snake), None, "dead")); break
        if len(snake) >= MAX_LEN:
            # hunt for its own tail: step into a body cell that is not the neck
            body_hits = [n for n in neighbors(head) if n in snake[2:-1]]
            if body_hits:
                snake = [body_hits[0]] + snake[:-1]
                frames.append((list(snake), None, "dead"))
                break
            safe = [n for n in neighbors(head) if n not in snake[:-1]]
            nxt = min(safe, key=lambda n: free_space(n, set(snake[:-1]))) if safe else None  # coil up
            if nxt is None: frames.append((list(snake), None, "dead")); break
            snake = [nxt] + snake[:-1]; frames.append((list(snake), None, "play")); continue
        path = bfs(head, food, set(snake[:-1]))
        if path:
            nxt = path[0]
        else:
            safe = [n for n in neighbors(head) if n not in snake[:-1]]
            if not safe: frames.append((list(snake), None, "dead")); break
            nxt = max(safe, key=lambda n: free_space(n, set(snake)))
        if nxt == food:
            snake = [nxt] + snake
            food = new_food() if len(snake) < MAX_LEN else None
        else:
            snake = [nxt] + snake[:-1]
        frames.append((list(snake), food, "play"))
    last = frames[-1][0]
    for _ in range(7): frames.append((last, None, "dead"))
    for _ in range(4): frames.append(([], None, "blank"))

N = len(frames); DUR = N * STEP
L = max(len(f[0]) for f in frames)
THEMES = {"dark": dict(bg="none", empty="#161b22", head="#22d3ee", body=("#22d3ee", "#a78bfa"), food="#f472b6", dead="#ef4444"),
          "light": dict(bg="none", empty="#ebedf0", head="#0e7490", body=("#0891b2", "#7c3aed"), food="#db2777", dead="#dc2626")}

def lerp(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))

def px(c): return c * (CELL + GAP)

def render(theme):
    T = THEMES[theme]; W = COLS * (CELL + GAP) - GAP; H = ROWS * (CELL + GAP) - GAP
    kt = ";".join(f"{i / N:.5f}" for i in range(N)) + ";1"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + 20}" height="{H + 20}" viewBox="-10 -10 {W + 20} {H + 20}">']
    for x in range(COLS):
        for y in range(ROWS):
            out.append(f'<rect x="{px(x)}" y="{px(y)}" width="{CELL}" height="{CELL}" rx="3" fill="{T["empty"]}"/>')
    # food
    fx = ";".join(str(px(f[1][0]) if f[1] else -40) for f in frames)
    fy = ";".join(str(px(f[1][1]) if f[1] else -40) for f in frames)
    out.append(f'<rect width="{CELL}" height="{CELL}" rx="4" fill="{T["food"]}">'
               f'<animate attributeName="x" values="{fx}" dur="{DUR:.2f}s" calcMode="discrete" repeatCount="indefinite"/>'
               f'<animate attributeName="y" values="{fy}" dur="{DUR:.2f}s" calcMode="discrete" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="1;.35;1" dur=".8s" repeatCount="indefinite"/></rect>')
    # snake segments (tail first so the head draws on top)
    for k in reversed(range(L)):
        t = k / max(L - 1, 1); col = T["head"] if k == 0 else lerp(T["body"][0], T["body"][1], t)
        shrink = min(4, k * 0.18); size = CELL - shrink; off = shrink / 2
        xs, ys, vis, fill = [], [], [], []
        for snake, food, st in frames:
            if k < len(snake):
                xs.append(str(px(snake[k][0]) + off)); ys.append(str(px(snake[k][1]) + off)); vis.append("1")
            else:
                xs.append(xs[-1] if xs else "-40"); ys.append(ys[-1] if ys else "-40"); vis.append("0")
            fill.append(T["dead"] if st == "dead" else col)
        out.append(f'<rect width="{size:.1f}" height="{size:.1f}" rx="{3 + shrink / 3:.1f}">'
                   f'<animate attributeName="x" values="{";".join(xs)}" dur="{DUR:.2f}s" calcMode="discrete" repeatCount="indefinite"/>'
                   f'<animate attributeName="y" values="{";".join(ys)}" dur="{DUR:.2f}s" calcMode="discrete" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="{";".join(vis)}" dur="{DUR:.2f}s" calcMode="discrete" repeatCount="indefinite"/>'
                   f'<animate attributeName="fill" values="{";".join(fill)}" dur="{DUR:.2f}s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    out.append("</svg>")
    return "".join(out)

outdir = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(outdir, exist_ok=True)
for th in THEMES:
    open(os.path.join(outdir, f"snake-{th}.svg"), "w").write(render(th))
print(f"{N} frames, {DUR:.1f}s loop, max length {L}")
