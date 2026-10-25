"""Render an animated contribution heatmap + weekly trend as SVG (dark and light).
Runs in GitHub Actions; reads the public contribution calendar through the GraphQL API."""
import json, os, sys, urllib.request

USER = os.environ.get("GH_USER", "suyogpatil395")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"
q = {"query": "query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}", "variables": {"u": USER}}
req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps(q).encode(), headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
dates = [w["contributionDays"][0]["date"] for w in cal["weeks"]]
total = cal["totalContributions"]
mx = max([c for w in weeks for c in w] + [1])

THEMES = {
    "dark": dict(bg="#0b1020", stroke="#1e293b", ink="#e2e8f0", mut="#94a3b8", empty="#161b2e", lv=["#0e4f5c", "#0e7490", "#22d3ee", "#a5f3fc"], line="#a78bfa", dot="#34d399"),
    "light": dict(bg="#ffffff", stroke="#e2e8f0", ink="#0f172a", mut="#64748b", empty="#eef2f7", lv=["#a5f3fc", "#22d3ee", "#0891b2", "#155e75"], line="#7c3aed", dot="#059669"),
}
FONT = "'Segoe UI',-apple-system,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,monospace"

def level(c):
    if c == 0: return -1
    r = c / mx
    return 0 if r <= .25 else 1 if r <= .5 else 2 if r <= .75 else 3

def render(t):
    T = THEMES[t]; W, H = 1000, 300; cell, gap = 13, 3; x0 = (W - len(weeks) * (cell + gap) + gap) // 2; y0 = 70
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="{T["bg"]}" stroke="{T["stroke"]}"/>',
           f'<text x="40" y="44" fill="{T["ink"]}" font-family="{FONT}" font-size="18" font-weight="700">{total} contributions in the last year</text>',
           f'<text x="{W-40}" y="44" text-anchor="end" fill="{T["mut"]}" font-family="{MONO}" font-size="12">@{USER} · auto-updated</text>']
    for wi, w in enumerate(weeks):
        for di, c in enumerate(w):
            lv = level(c); col = T["empty"] if lv < 0 else T["lv"][lv]
            x = x0 + wi * (cell + gap); y = y0 + di * (cell + gap); d = wi * 0.035
            out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{col}" opacity="0"><title>{c} on week of {dates[wi]}</title>'
                       f'<animate attributeName="opacity" from="0" to="1" begin="{d:.2f}s" dur=".4s" fill="freeze"/></rect>')
    # weekly trend line under the grid
    tot = [sum(w) for w in weeks]; tm = max(tot + [1]); base = 270; hh = 55
    pts = " ".join(f"{x0 + i*(cell+gap) + cell/2:.1f},{base - v/tm*hh:.1f}" for i, v in enumerate(tot))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{T["line"]}" stroke-width="2" stroke-linejoin="round" stroke-dasharray="2000" stroke-dashoffset="2000">'
               f'<animate attributeName="stroke-dashoffset" from="2000" to="0" begin=".6s" dur="2.5s" fill="freeze"/></polyline>')
    path = "M" + " L".join(pts.split())
    out.append(f'<circle r="4" fill="{T["dot"]}"><animateMotion path="{path}" dur="6s" begin="3s" repeatCount="indefinite"/></circle>')
    out.append(f'<text x="{x0}" y="{base+22}" fill="{T["mut"]}" font-family="{MONO}" font-size="11">weekly trend</text>')
    for i, c in enumerate(["Less"] + T["lv"] + ["More"]):
        if c in ("Less", "More"):
            out.append(f'<text x="{W-40-130 if c == "Less" else W-40}" y="{base+22}" text-anchor="{"end" if c == "Less" else "end"}" fill="{T["mut"]}" font-family="{FONT}" font-size="11">{c}</text>')
        else:
            out.append(f'<rect x="{W-40-122 + (i-1)*18}" y="{base+11}" width="13" height="13" rx="3" fill="{c}"/>')
    out.append("</svg>")
    return "\n".join(out)

os.makedirs(OUT, exist_ok=True)
for t in THEMES:
    open(os.path.join(OUT, f"activity-{t}.svg"), "w").write(render(t))
print("total", total)
