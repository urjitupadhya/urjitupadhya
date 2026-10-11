"""
contrib_graph.py
Fetches the past year of contribution data via GitHub GraphQL API
and writes assets/contrib.svg.

Requires env vars:
  GH_TOKEN  – a GitHub personal access token (read:user scope is enough)
  GH_USER   – GitHub username (default: urjitupadhya)
  OUT       – output path   (default: assets/contrib.svg)
"""

import os, sys, json, datetime, urllib.request, urllib.error

USER   = os.environ.get("GH_USER",  "urjitupadhya")
OUT    = os.environ.get("OUT",       "assets/contrib.svg")
TOKEN  = os.environ.get("GH_TOKEN", "")

# Black-and-gold palette (0 = empty, 1-4 = contribution levels)
COLORS = ["#161B22", "#3B2A0E", "#7A5520", "#C9A96E", "#E8D3A2"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVEL_MAP = {
    "NONE":           0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE":2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE":4,
}

def fetch_weeks():
    if not TOKEN:
        sys.exit("Error: GH_TOKEN environment variable is not set.")
    payload = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type":  "application/json",
            "User-Agent":    "contrib-graph-action/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code}: {e.read().decode()}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def render(weeks):
    cell, gap, left, top = 11, 3, 6, 32

    # build flat list of (date, level) in week-column order
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append((day["date"], LEVEL_MAP.get(day["contributionLevel"], 0)))

    num_weeks = len(weeks)
    w = left + num_weeks * (cell + gap) + 6
    h = top + 7 * (cell + gap) + 6

    # month labels
    month_labels = []
    prev_month = None
    for wi, week in enumerate(weeks):
        first_day = week["contributionDays"][0]["date"]
        month = datetime.date.fromisoformat(first_day).strftime("%b")
        if month != prev_month:
            x = left + wi * (cell + gap)
            month_labels.append(f'<text x="{x}" y="20" fill="#8A8A8A" font-family="monospace" font-size="10">{month}</text>')
            prev_month = month

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="GitHub contribution graph for {USER}">',
        f'  <rect width="{w}" height="{h}" rx="8" fill="#0D1117"/>',
    ]
    out.extend(f"  {lbl}" for lbl in month_labels)

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            level = LEVEL_MAP.get(day["contributionLevel"], 0)
            x = left + wi * (cell + gap)
            y = top  + di * (cell + gap)
            color = COLORS[level]
            out.append(
                f'  <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}">'
                f'<title>{day["date"]}</title></rect>'
            )

    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    weeks = fetch_weeks()
    svg   = render(weeks)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT}  ({len(svg)} bytes)")
