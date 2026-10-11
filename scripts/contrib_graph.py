import os, re, sys, datetime, urllib.request

USER = os.environ.get("GH_USER", "urjitupadhya")
OUT = os.environ.get("OUT", "assets/contrib.svg")
COLORS = ["#161B22", "#0E4F63", "#0F7C99", "#00A8CC", "#00D4FF"]

def fetch_days():
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    return parse(html)

def parse(html):
    days = {}
    for tag in re.findall(r"<td[^>]*data-date=[^>]*>", html):
        d = re.search(r'data-date="([\d-]+)"', tag)
        l = re.search(r'data-level="(\d)"', tag)
        if d and l:
            days[d.group(1)] = int(l.group(1))
    return days

def render(days):
    if not days:
        sys.exit("No contribution data found")
    dates = sorted(days)
    first = datetime.date.fromisoformat(dates[0])
    cell, gap, left, top = 11, 3, 40, 40
    weeks = ((datetime.date.fromisoformat(dates[-1]) - first).days + (first.weekday() + 1) % 7) // 7 + 1
    w = left + weeks * (cell + gap) + 20
    h = top + 7 * (cell + gap) + 30
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<rect width="{w}" height="{h}" rx="10" fill="#0D1117"/>',
           f'<text x="{left}" y="24" fill="#00D4FF" font-family="monospace" font-size="14" font-weight="bold">Contribution Graph: {USER}</text>']
    offset = (first.weekday() + 1) % 7  # Sunday = 0
    for i, d in enumerate(dates):
        idx = i + offset
        x = left + (idx // 7) * (cell + gap)
        y = top + (idx % 7) * (cell + gap)
        out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{COLORS[days[d]]}"><title>{d}</title></rect>')
    out.append("</svg>")
    return "\n".join(out)

if __name__ == "__main__":
    svg = render(fetch_days())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(svg)
    print("Wrote", OUT)
