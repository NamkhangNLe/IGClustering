"""Generate the interactive visualization (index.html at the repo root).

Reads the four JSON snapshots from MVP/, embeds the 789 users as JSON,
and writes a self-contained page: radial ego network, search, group
filters, stats, and the honest findings write-up. No build step, no CDN.

Usage:
    python3 make_index.py         # from the repo root checkout
"""

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.join(HERE, "MVP")


def load(filename, key):
    with open(os.path.join(MVP, filename), encoding="utf-8") as f:
        return json.load(f)[key]


def main():
    followers = load("Namkhang-Followers.json", "followers")
    following = load("Namkhang-Following.json", "followings")
    f_set = {u["username"]: u["full_name"] for u in followers}
    g_set = {u["username"]: u["full_name"] for u in following}

    mutual = sorted(set(f_set) & set(g_set))
    f_only = sorted(set(f_set) - set(g_set))
    g_only = sorted(set(g_set) - set(f_set))

    def group_of(u):
        if u in f_set and u in g_set:
            return 0
        if u in f_set:
            return 1
        return 2

    users = []
    for u in sorted(set(f_set) | set(g_set)):
        name = (f_set.get(u) or g_set.get(u) or "").strip()
        users.append({"u": u, "n": name, "g": group_of(u)})

    data_json = json.dumps(users, ensure_ascii=False, separators=(",", ":"))

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IGClustering — Namkhang's Instagram ego network</title>
<style>
  :root {{
    --paper: #FAF8F5; --ink: #191919; --muted: #6b6560; --card: #ffffff;
    --green: #16a34a; --blue: #2563eb; --amber: #d97706; --line: #e8e2da;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--paper); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.55; }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 40px 20px 64px; }}
  h1 {{ font-size: 34px; letter-spacing: -0.8px; margin: 0 0 6px; font-weight: 800; }}
  .sub {{ color: var(--muted); font-size: 17px; margin: 0 0 28px; max-width: 640px; }}
  .stats {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 28px; }}
  @media (max-width: 640px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
  .stat {{ background: var(--card); border-radius: 16px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
  .stat b {{ display: block; font-size: 30px; letter-spacing: -0.8px; }}
  .stat span {{ font-size: 13px; color: var(--muted); font-weight: 600; }}
  .stat .dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }}
  .card {{ background: var(--card); border-radius: 20px; padding: 20px; box-shadow: 0 1px 6px rgba(0,0,0,.07); margin-bottom: 28px; }}
  .controls {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; }}
  .controls input {{ flex: 1; min-width: 200px; padding: 11px 14px; font-size: 15px;
    border: 1px solid var(--line); border-radius: 12px; background: var(--paper); color: var(--ink); outline: none; }}
  .controls input:focus {{ border-color: var(--ink); }}
  .chip {{ border: 1px solid var(--line); background: var(--paper); border-radius: 999px;
    padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--ink); }}
  .chip.off {{ opacity: .35; }}
  .chip .dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }}
  #net {{ width: 100%; height: auto; display: block; touch-action: manipulation; }}
  #net circle.node {{ cursor: pointer; transition: opacity .15s; }}
  #net circle.node:hover {{ stroke: var(--ink); stroke-width: 1.5; }}
  #net circle.node.dim {{ opacity: .08; }}
  #net circle.node.match {{ stroke: var(--ink); stroke-width: 1.5; }}
  #net line.spoke {{ stroke-opacity: .07; }}
  #net line.spoke.dim {{ opacity: .05; }}
  #tooltip {{ position: absolute; pointer-events: none; background: var(--ink); color: #fff;
    padding: 6px 10px; border-radius: 8px; font-size: 13px; display: none; z-index: 5; white-space: nowrap; }}
  #detail {{ margin-top: 12px; font-size: 15px; min-height: 24px; }}
  #detail b {{ font-size: 16px; }}
  #matches {{ font-size: 14px; color: var(--muted); margin-top: 8px; min-height: 20px; }}
  #matches button {{ border: none; background: none; color: var(--blue); font-size: 14px;
    cursor: pointer; padding: 2px 4px; text-decoration: underline; }}
  h2 {{ font-size: 22px; letter-spacing: -0.4px; margin: 0 0 10px; }}
  .findings li {{ margin-bottom: 8px; }}
  .findings, .method {{ font-size: 16px; }}
  .method code {{ background: #f0ebe4; padding: 1px 6px; border-radius: 6px; font-size: 14px; }}
  .mutebar {{ height: 8px; background: #eee9e2; border-radius: 99px; overflow: hidden; margin: 6px 0 14px; }}
  .mutebar i {{ display: block; height: 100%; background: var(--green); }}
  .fine {{ font-size: 13px; color: var(--muted); }}
</style>
</head>
<body>
<div class="wrap">
  <h1>How close is everyone, really?</h1>
  <p class="sub">Namkhang's Instagram ego network, April 2024 snapshot. One account, 789 people,
  and the honest answer to how separated they all are.</p>

  <div class="stats">
    <div class="stat"><b>615</b><span>followers</span></div>
    <div class="stat"><b>571</b><span>following</span></div>
    <div class="stat"><b><span class="dot" style="background:var(--green)"></span>397</b><span>mutuals</span></div>
    <div class="stat"><b><span class="dot" style="background:var(--blue)"></span>218</b><span>followers only</span></div>
    <div class="stat"><b><span class="dot" style="background:var(--amber)"></span>174</b><span>following only</span></div>
  </div>

  <div class="card">
    <div class="controls">
      <input id="q" type="search" placeholder="Search a username or name…" autocomplete="off">
      <button class="chip" data-g="0"><span class="dot" style="background:var(--green)"></span>Mutuals</button>
      <button class="chip" data-g="1"><span class="dot" style="background:var(--blue)"></span>Followers only</button>
      <button class="chip" data-g="2"><span class="dot" style="background:var(--amber)"></span>Following only</button>
    </div>
    <div style="position:relative">
      <svg id="net" viewBox="0 0 1000 1000" role="img" aria-label="Radial ego network"></svg>
      <div id="tooltip"></div>
    </div>
    <div id="detail">Hover a dot to see who it is. Click to pin it here.</div>
    <div id="matches"></div>
  </div>

  <div class="card findings">
    <h2>Findings</h2>
    <ul>
      <li><b>Everyone is 1 hop from Namkhang, 2 hops from everyone else.</b> The data is
      1-hop only, so the graph is a star: 790 nodes, 789 edges, diameter 2, average
      shortest path 1.9975, clustering coefficient 0. Any two people in this network
      are connected through exactly one intermediate, Namkhang.</li>
      <li><b>69.5% of the people Namkhang follows follow him back</b> (397 of 571).
      64.6% of his followers are people he follows back (397 of 615).</li>
      <li><b>The non-mutuals split unevenly.</b> 218 people follow Namkhang without a
      follow-back, versus 174 accounts he follows that don't follow him. The
      following-only side is mostly brands, meme pages, and GT accounts.</li>
      <li><b>Mutuality, of following:</b> 69.5%
        <div class="mutebar"><i style="width:69.5%"></i></div></li>
      <li><b>Mutuality, of followers:</b> 64.6%
        <div class="mutebar"><i style="width:64.6%"></i></div></li>
    </ul>
    <h2>What this does not answer</h2>
    <p>The original question, Ivy League vs Georgia Tech separation, <b>cannot be
    answered from this dataset</b>. The scrape collected username and full name only;
    there is no school affiliation anywhere in the data, and no second-hop edges
    (we never collected who anyone else follows). To answer it for real you would
    need, per person, a school label and at least one more hop of follow edges.
    Instagram no longer exposes that data through the endpoints this scraper used,
    so the honest finish is the ego-network analysis above, not an invented
    school clustering.</p>
  </div>

  <div class="card method">
    <h2>How it was done</h2>
    <p><code>MVP/scrape.js</code> ran in the browser console against Instagram's old
    GraphQL endpoints and dumped followers / following as JSON (April 2024).
    <code>MVP/merge.py</code> joins the two lists into <code>Merged.csv</code> (the
    397 mutuals). <code>MVP/analyze.py</code> validates the derived lists against the
    computed sets, computes the graph statistics, and writes
    <code>MVP/results.json</code> plus a static plot (<code>ego_network.png</code>).
    <code>MVP/graphing.py</code> re-renders that plot. This page is generated from
    the same JSON by <code>make_index.py</code>.</p>
    <p class="fine">Snapshot: April 2024. Usernames shown here are already public in
    this repository's MVP data files. Run <code>python3 MVP/analyze.py</code> to
    reproduce every number on this page.</p>
  </div>
</div>

<script>
const USERS = {data_json};
const GROUPS = [
  {{ label: "Mutual", color: "#16a34a", r: 150 }},
  {{ label: "Follower only", color: "#2563eb", r: 260 }},
  {{ label: "Following only", color: "#d97706", r: 370 }},
];
const CX = 500, CY = 500;
const svg = document.getElementById("net");
const NS = "http://www.w3.org/2000/svg";
const tip = document.getElementById("tooltip");
const detail = document.getElementById("detail");
const matchesEl = document.getElementById("matches");

function hash(s) {{
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h / 4294967295;
}}

// deterministic layout: sorted within group, even angles, tiny hash jitter
const byGroup = [[], [], []];
USERS.forEach(u => byGroup[u.g].push(u));
const nodes = [];
byGroup.forEach((list, g) => {{
  const n = list.length;
  list.forEach((u, i) => {{
    const a = (i / n) * Math.PI * 2 - Math.PI / 2;
    const jr = (hash(u.u) - 0.5) * 14;
    const ja = (hash(u.u + ":a") - 0.5) * (Math.PI * 2 / n) * 0.7;
    const r = GROUPS[g].r + jr;
    const ang = a + ja;
    nodes.push({{ ...u, x: CX + r * Math.cos(ang), y: CY + r * Math.sin(ang), g }});
  }});
}});

const spokes = document.createElementNS(NS, "g");
const dots = document.createElementNS(NS, "g");
nodes.forEach(nd => {{
  const ln = document.createElementNS(NS, "line");
  ln.setAttribute("x1", CX); ln.setAttribute("y1", CY);
  ln.setAttribute("x2", nd.x); ln.setAttribute("y2", nd.y);
  ln.setAttribute("stroke", GROUPS[nd.g].color);
  ln.setAttribute("class", "spoke");
  ln.dataset.g = nd.g;
  spokes.appendChild(ln);
  const c = document.createElementNS(NS, "circle");
  c.setAttribute("cx", nd.x); c.setAttribute("cy", nd.y); c.setAttribute("r", 3.2);
  c.setAttribute("fill", GROUPS[nd.g].color);
  c.setAttribute("class", "node");
  c.dataset.g = nd.g; c.dataset.u = nd.u;
  c.addEventListener("mousemove", e => {{
    tip.style.display = "block";
    tip.style.left = (e.clientX + 12) + "px";
    tip.style.top = (e.clientY + 12) + "px";
    tip.textContent = (nd.n ? nd.n + " · " : "") + "@" + nd.u + " — " + GROUPS[nd.g].label;
  }});
  c.addEventListener("mouseleave", () => tip.style.display = "none");
  c.addEventListener("click", () => {{
    detail.innerHTML = "<b>" + (nd.n ? nd.n + " " : "") + "@" + nd.u + "</b> — " +
      GROUPS[nd.g].label + ". 1 hop from Namkhang, 2 hops from everyone else in this graph.";
  }});
  dots.appendChild(c);
}});

// centre
const cc = document.createElementNS(NS, "circle");
cc.setAttribute("cx", CX); cc.setAttribute("cy", CY); cc.setAttribute("r", 26);
cc.setAttribute("fill", "#191919"); cc.setAttribute("stroke", "#fff"); cc.setAttribute("stroke-width", 3);
const ct = document.createElementNS(NS, "text");
ct.setAttribute("x", CX); ct.setAttribute("y", CY + 6);
ct.setAttribute("text-anchor", "middle"); ct.setAttribute("fill", "#fff");
ct.setAttribute("font-size", "18"); ct.setAttribute("font-weight", "800");
ct.textContent = "N";
svg.appendChild(spokes); svg.appendChild(dots); svg.appendChild(cc); svg.appendChild(ct);

// group filter chips
document.querySelectorAll(".chip").forEach(chip => {{
  chip.addEventListener("click", () => {{
    chip.classList.toggle("off");
    const g = chip.dataset.g;
    document.querySelectorAll('[data-g="' + g + '"]').forEach(el => {{
      el.style.display = chip.classList.contains("off") ? "none" : "";
    }});
  }});
}});

// search
const q = document.getElementById("q");
q.addEventListener("input", () => {{
  const s = q.value.trim().toLowerCase();
  const all = document.querySelectorAll("circle.node");
  if (!s) {{
    all.forEach(c => c.classList.remove("dim", "match"));
    matchesEl.textContent = "";
    return;
  }}
  const hits = nodes.filter(nd =>
    nd.u.toLowerCase().includes(s) || (nd.n && nd.n.toLowerCase().includes(s)));
  all.forEach(c => {{
    const hit = hits.some(h => h.u === c.dataset.u);
    c.classList.toggle("match", hit);
    c.classList.toggle("dim", !hit);
  }});
  matchesEl.innerHTML = hits.length + " match" + (hits.length === 1 ? "" : "es") + ": " +
    hits.slice(0, 8).map(h =>
      '<button data-u="' + h.u + '">@' + h.u + "</button>").join(" ");
  matchesEl.querySelectorAll("button").forEach(b => b.addEventListener("click", () => {{
    const nd = nodes.find(n => n.u === b.dataset.u);
    detail.innerHTML = "<b>" + (nd.n ? nd.n + " " : "") + "@" + nd.u + "</b> — " +
      GROUPS[nd.g].label + ". 1 hop from Namkhang, 2 hops from everyone else in this graph.";
  }}));
}});
</script>
</body>
</html>
"""

    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote index.html ({len(html)/1024:.1f} KB, {len(users)} users embedded)")


if __name__ == "__main__":
    main()
