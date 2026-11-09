"""Generate the interactive visualization (index.html at the repo root).

Reads the four JSON snapshots from MVP/, embeds the 789 users as JSON,
and writes a self-contained page: canvas ego network with zoom/pan,
list view, search, group filters, stats, and the honest findings
write-up.

Usage:
    python3 make_index.py                          # from the repo root
    python3 make_index.py --anonymize --out FILE   # pseudonymized variant
                                                   # (handles hashed, full
                                                   #  names removed) for
                                                   #  owner review; NOT for
                                                   #  publishing as-is.
"""

import argparse
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.join(HERE, "MVP")

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IGClustering — Namkhang's Instagram ego network, April 2024</title>
<meta name="description" content="One Instagram account, 789 people, April 2024: how separated is everyone in Namkhang's follower network? A star graph with diameter 2 — and an honest account of what the data cannot answer.">
<meta property="og:type" content="website">
<meta property="og:title" content="IGClustering — How close is everyone, really?">
<meta property="og:description" content="Namkhang's Instagram ego network, April 2024 snapshot. 615 followers, 571 following, 397 mutuals — everyone 1 hop from Namkhang, 2 hops from each other.">
<meta property="og:url" content="https://namkhangnle.github.io/IGClustering/">
<meta property="og:image" content="https://namkhangnle.github.io/IGClustering/ego_network.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#bc1888">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='1' x2='1' y2='0'%3E%3Cstop offset='0' stop-color='%23f09433'/%3E%3Cstop offset='.35' stop-color='%23e6683c'/%3E%3Cstop offset='.6' stop-color='%23dc2743'/%3E%3Cstop offset='.8' stop-color='%23cc2366'/%3E%3Cstop offset='1' stop-color='%23bc1888'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='16' fill='url(%23g)'/%3E%3Ccircle cx='32' cy='32' r='13' fill='none' stroke='white' stroke-width='4'/%3E%3Ccircle cx='45' cy='19' r='3' fill='white'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #fafafa; --ink: #141414; --muted: #6b7280; --card: #ffffff;
    --green: #16a34a; --blue: #2563eb; --amber: #d97706; --line: #e7e5e4;
    --ig1: #f09433; --ig2: #e6683c; --ig3: #dc2743; --ig4: #cc2366; --ig5: #bc1888;
    --ig: linear-gradient(45deg, var(--ig1), var(--ig2) 30%, var(--ig3) 55%, var(--ig4) 78%, var(--ig5));
    --shadow: 0 1px 6px rgba(0,0,0,.07);
    --chipbg: #f5f5f4;
  }
  [data-theme="dark"] {
    --bg: #0e0e11; --ink: #f4f4f5; --muted: #9ca3af; --card: #1a1a20;
    --line: #2b2b33; --shadow: 0 1px 8px rgba(0,0,0,.45); --chipbg: #26262e;
    --green: #22c55e; --blue: #60a5fa; --amber: #f59e0b;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.55; }
  .wrap { max-width: 960px; margin: 0 auto; padding: 20px 20px 64px; }
  .topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 22px; }
  .brand { display: flex; align-items: center; gap: 10px; font-family: "Sora", "Inter", sans-serif;
    font-weight: 800; font-size: 19px; letter-spacing: -0.3px; }
  .brand .mark { width: 34px; height: 34px; border-radius: 10px; background: var(--ig);
    display: inline-flex; align-items: center; justify-content: center; flex: none; }
  .brand .mark svg { width: 22px; height: 22px; }
  .brand em { font-style: normal; background: var(--ig); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .themebtn { border: 1px solid var(--line); background: var(--card); color: var(--ink);
    border-radius: 999px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
  h1 { font-family: "Sora", "Inter", sans-serif; font-size: 40px; line-height: 1.08;
    letter-spacing: -1px; margin: 0 0 8px; font-weight: 800; }
  h1 .grad { background: var(--ig); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .sub { color: var(--muted); font-size: 17px; margin: 0 0 18px; max-width: 640px; }
  .banner { border: 1px solid var(--line); border-left: 6px solid transparent;
    border-image: linear-gradient(180deg, var(--ig1), var(--ig3), var(--ig5)) 1;
    background: var(--card); border-radius: 14px; padding: 14px 16px; margin-bottom: 24px;
    font-size: 15px; box-shadow: var(--shadow); }
  .banner b { font-size: 15px; }
  .banner p { margin: 4px 0 0; color: var(--muted); font-size: 14px; }
  .stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 24px; }
  @media (max-width: 640px) { .stats { grid-template-columns: repeat(2, 1fr); } h1 { font-size: 31px; } }
  .stat { background: var(--card); border-radius: 16px; padding: 16px; box-shadow: var(--shadow); }
  .stat b { display: block; font-size: 30px; letter-spacing: -0.8px; font-family: "Sora", "Inter", sans-serif; }
  .stat span { font-size: 13px; color: var(--muted); font-weight: 600; }
  .stat .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }
  .card { background: var(--card); border-radius: 20px; padding: 20px; box-shadow: var(--shadow); margin-bottom: 24px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 10px; }
  .controls input { flex: 1; min-width: 200px; padding: 11px 14px; font-size: 15px;
    border: 1px solid var(--line); border-radius: 12px; background: var(--bg); color: var(--ink); outline: none; }
  .controls input:focus { border-color: var(--ig5); box-shadow: 0 0 0 3px rgba(188,24,136,.18); }
  .seg { display: inline-flex; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
  .seg button { border: none; background: var(--bg); color: var(--ink); padding: 10px 16px;
    font-size: 14px; font-weight: 600; cursor: pointer; }
  .seg button[aria-pressed="true"] { background: var(--ig); color: #fff; }
  .resetbtn { border: 1px solid var(--line); background: var(--card); color: var(--ink);
    border-radius: 12px; padding: 10px 14px; font-size: 14px; font-weight: 600; cursor: pointer; }
  .chiprow { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
  .chip { border: 1px solid var(--line); background: var(--chipbg); border-radius: 999px;
    padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--ink); }
  .chip.off { opacity: .35; }
  .chip .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }
  .status { font-size: 13.5px; color: var(--muted); margin: 0 0 12px; min-height: 20px; }
  .status b { color: var(--ink); }
  .graphwrap { position: relative; border: 1px solid var(--line); border-radius: 16px; overflow: hidden; background: var(--bg); }
  .graphwrap:focus-visible { outline: 3px solid var(--ig5); outline-offset: 2px; }
  #net { width: 100%; height: 560px; display: block; touch-action: none; cursor: grab; }
  #net:active { cursor: grabbing; }
  @media (max-width: 640px) { #net { height: 420px; } }
  .zoomctl { position: absolute; top: 10px; right: 10px; display: flex; flex-direction: column; gap: 6px; z-index: 3; }
  .zoomctl button { width: 38px; height: 38px; border-radius: 10px; border: 1px solid var(--line);
    background: var(--card); color: var(--ink); font-size: 18px; font-weight: 700; cursor: pointer;
    box-shadow: var(--shadow); }
  .zoomctl button.wide { width: auto; padding: 0 10px; font-size: 12px; height: 30px; }
  .hint { font-size: 13px; color: var(--muted); margin: 10px 2px 0; }
  #tooltip { position: absolute; pointer-events: none; background: var(--ink); color: var(--bg);
    padding: 6px 10px; border-radius: 8px; font-size: 13px; display: none; z-index: 5;
    white-space: nowrap; max-width: 92%; overflow: hidden; text-overflow: ellipsis; }
  #detail { margin-top: 14px; border-top: 1px solid var(--line); padding-top: 14px;
    font-size: 15px; min-height: 26px; }
  #detail b { font-size: 16px; }
  #detail .actions { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
  #detail .actions button { border: 1px solid var(--line); background: var(--chipbg); color: var(--ink);
    border-radius: 999px; padding: 6px 12px; font-size: 13px; font-weight: 600; cursor: pointer; }
  #detail .close { float: right; border: none; background: none; color: var(--muted);
    font-size: 20px; cursor: pointer; line-height: 1; padding: 2px 6px; }
  @media (max-width: 640px) {
    #detail.sheet { position: fixed; left: 0; right: 0; bottom: 0; z-index: 50; margin: 0;
      background: var(--card); border-top: 3px solid transparent;
      border-image: linear-gradient(90deg, var(--ig1), var(--ig3), var(--ig5)) 1;
      border-radius: 18px 18px 0 0; padding: 16px 20px 24px; box-shadow: 0 -8px 30px rgba(0,0,0,.25); }
  }
  .listview { max-height: 560px; overflow-y: auto; border: 1px solid var(--line); border-radius: 16px; }
  .listgroup { padding: 10px 14px 4px; font-size: 12px; font-weight: 700; letter-spacing: .06em;
    text-transform: uppercase; color: var(--muted); position: sticky; top: 0; background: var(--card); z-index: 2; }
  .listgroup .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .person { display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
    border: none; border-bottom: 1px solid var(--line); background: var(--card); color: var(--ink);
    padding: 11px 14px; font-size: 15px; cursor: pointer; min-height: 52px; }
  .person:hover, .person:focus-visible { background: var(--chipbg); outline: none; }
  .person:focus-visible { box-shadow: inset 0 0 0 2px var(--ig5); }
  .person .avatar { width: 36px; height: 36px; border-radius: 50%; flex: none; display: inline-flex;
    align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 14px;
    font-family: "Sora", "Inter", sans-serif; }
  .person .who { min-width: 0; }
  .person .who b { display: block; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .person .who span { color: var(--muted); font-size: 13px; }
  .person .tag { margin-left: auto; font-size: 12px; font-weight: 600; color: var(--muted); flex: none; }
  .empty { display: none; text-align: center; padding: 40px 20px; color: var(--muted); }
  .empty b { display: block; color: var(--ink); font-size: 17px; margin-bottom: 6px; font-family: "Sora", "Inter", sans-serif; }
  .empty button { margin-top: 14px; border: none; background: var(--ig); color: #fff; border-radius: 999px;
    padding: 10px 18px; font-size: 14px; font-weight: 700; cursor: pointer; }
  h2 { font-family: "Sora", "Inter", sans-serif; font-size: 22px; letter-spacing: -0.4px; margin: 0 0 10px; }
  .findings li { margin-bottom: 8px; }
  .findings, .method { font-size: 16px; }
  .method code { background: var(--chipbg); padding: 1px 6px; border-radius: 6px; font-size: 14px; }
  .method img { width: 100%; border-radius: 14px; border: 1px solid var(--line); margin-top: 8px; }
  .mutebar { height: 8px; background: var(--line); border-radius: 99px; overflow: hidden; margin: 6px 0 14px; }
  .mutebar i { display: block; height: 100%; background: var(--ig); }
  .fine { font-size: 13px; color: var(--muted); }
  footer { border-top: 1px solid var(--line); padding-top: 16px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <div class="brand"><span class="mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><rect x="2.5" y="2.5" width="19" height="19" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.4" cy="6.6" r="1.1" fill="#fff" stroke="none"/></svg></span>IG<em>Clustering</em></div>
    <button class="themebtn" id="themeBtn" type="button" aria-label="Toggle dark mode">🌙 Dark</button>
  </div>

  <h1>How <span class="grad">close</span> is everyone, really?</h1>
  <p class="sub">Namkhang's Instagram ego network. One account, 789 people, and the honest answer to how separated they all are.</p>

  <div class="banner" role="note">
    <b>📸 April 2024 snapshot — over 2&frac12; years old.</b>
    <p>Every count on this page is from April 2024. Namkhang's follower list today will look different: people followed and unfollowed, accounts renamed or deleted. Read this as a time capsule of one month, not a live profile. No fresher export exists yet; a new scrape would be needed to update it.</p>
  </div>

  <div class="stats">
    <div class="stat"><b>615</b><span>followers</span></div>
    <div class="stat"><b>571</b><span>following</span></div>
    <div class="stat"><b><span class="dot" style="background:var(--green)"></span>397</b><span>mutuals</span></div>
    <div class="stat"><b><span class="dot" style="background:var(--blue)"></span>218</b><span>followers only</span></div>
    <div class="stat"><b><span class="dot" style="background:var(--amber)"></span>174</b><span>following only</span></div>
  </div>

  <div class="card">
    <div class="controls">
      <input id="q" type="search" placeholder="Search a username or name…" autocomplete="off" aria-label="Search usernames or names">
      <div class="seg" role="group" aria-label="View">
        <button id="viewList" type="button" aria-pressed="false">☰ List</button>
        <button id="viewGraph" type="button" aria-pressed="true">◉ Graph</button>
      </div>
      <button class="resetbtn" id="resetBtn" type="button">Reset filters</button>
    </div>
    <div class="chiprow" id="chips">
      <button class="chip" data-g="0" type="button" aria-pressed="true"><span class="dot" style="background:var(--green)"></span>Mutuals · 397</button>
      <button class="chip" data-g="1" type="button" aria-pressed="true"><span class="dot" style="background:var(--blue)"></span>Followers only · 218</button>
      <button class="chip" data-g="2" type="button" aria-pressed="true"><span class="dot" style="background:var(--amber)"></span>Following only · 174</button>
    </div>
    <p class="status" id="status" aria-live="polite"></p>

    <div class="graphwrap" id="graphWrap" tabindex="0" role="application"
         aria-label="Ego network graph. Drag to pan, scroll or pinch to zoom, tap a dot to select it. Arrow keys move between people, Enter selects, plus and minus zoom, 0 resets the view.">
      <canvas id="net"></canvas>
      <div class="zoomctl">
        <button id="zoomIn" type="button" aria-label="Zoom in">+</button>
        <button id="zoomOut" type="button" aria-label="Zoom out">−</button>
        <button id="zoomFit" type="button" class="wide" aria-label="Fit whole network">Fit</button>
      </div>
      <div id="tooltip" role="status"></div>
    </div>
    <p class="hint" id="graphHint">Drag to pan · scroll or pinch to zoom · tap a dot to see who it is · arrow keys move between people, Enter selects. 397 mutuals share one ring, so zoom in to separate them; the list view is the faster way to find someone.</p>

    <div class="listview" id="listView" hidden></div>

    <div class="empty" id="emptyState">
      <b>Nothing to show here.</b>
      <span id="emptyText">Every group is filtered off.</span><br>
      <button id="emptyReset" type="button">Show everyone again</button>
    </div>

    <div id="detail" aria-live="polite">Tap a dot, or pick a name from the list, to see who it is.</div>
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
      <li><b>The non-mutuals split unevenly, and the following-only side is not what it looks like.</b>
      218 people follow Namkhang without a follow-back, versus 174 accounts he follows
      that don't follow him. Only 42 of those 174 (24%) match Georgia Tech / Barstool
      markers in their handle or name, and 101 of 174 (58%) carry an ordinary personal
      full name with no brand or meme marker at all. The data has no category labels,
      so any "mostly brands and meme pages" claim would be a guess, not a finding.</li>
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
    <figure style="margin:16px 0 0"><img src="ego_network.png" alt="Static radial plot of the ego network: Namkhang at the centre, one ring per group" loading="lazy">
    <figcaption class="fine">The static plot from <code>MVP/analyze.py</code> — the same star, drawn once, for the record.</figcaption></figure>
    <p class="fine">Snapshot: April 2024. Usernames shown here are already public in
    this repository's MVP data files. Run <code>python3 MVP/analyze.py</code> to
    reproduce every number on this page.</p>
  </div>

  <footer class="fine">
    IGClustering · April 2024 snapshot of one Instagram account · 789 people · generated by <code>make_index.py</code> from the MVP data files.
    This page lists real usernames and full names from that export; it is published as a data artifact, not a live directory.
  </footer>
</div>

<script>
"use strict";
const USERS = %%USERS_JSON%%;
const GROUPS = [
  { label: "Mutual", plural: "Mutuals", color: "#16a34a", r: 150 },
  { label: "Follower only", plural: "Followers only", color: "#2563eb", r: 260 },
  { label: "Following only", plural: "Following only", color: "#d97706", r: 370 },
];
const CX = 500, CY = 500;
const $ = id => document.getElementById(id);
const canvas = $("net"), wrap = $("graphWrap"), tip = $("tooltip"),
      detail = $("detail"), statusEl = $("status"), listView = $("listView"),
      emptyState = $("emptyState"), emptyText = $("emptyText"), q = $("q");

function hash(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h / 4294967295;
}
const byGroup = [[], [], []];
USERS.forEach(u => byGroup[u.g].push(u));
const nodes = [];
byGroup.forEach((list, g) => {
  const n = list.length;
  list.forEach((u, i) => {
    const a = (i / n) * Math.PI * 2 - Math.PI / 2;
    const jr = (hash(u.u) - 0.5) * 14;
    const ja = (hash(u.u + ":a") - 0.5) * (Math.PI * 2 / n) * 0.7;
    const r = GROUPS[g].r + jr, ang = a + ja;
    nodes.push({ ...u, x: CX + r * Math.cos(ang), y: CY + r * Math.sin(ang), g });
  });
});
const byHandle = new Map(nodes.map(n => [n.u, n]));

// ---------- filter state: one source of truth ----------
// Search and chips never stack into a confusing combined state:
// typing a search turns all groups back on; toggling a chip clears the
// search box. Reset clears both. The status line always states the filter.
const state = { q: "", groups: new Set([0, 1, 2]) };
let visible = nodes.slice();
let selected = null, focused = null;

function groupColor(g) { return GROUPS[g].color; }
function labelOf(nd) { return (nd.n ? nd.n + " · " : "") + "@" + nd.u + " — " + GROUPS[nd.g].label; }

function applyFilters() {
  const s = state.q;
  visible = nodes.filter(nd =>
    state.groups.has(nd.g) &&
    (!s || nd.u.toLowerCase().includes(s) || (nd.n && nd.n.toLowerCase().includes(s))));
  if (selected && !visible.includes(selected)) selected = null;
  if (focused && !visible.includes(focused)) focused = null;
  const parts = [];
  if (s) parts.push('search “' + s + '”');
  const on = [...state.groups].sort().map(g => GROUPS[g].plural);
  parts.push(on.length === 3 ? "all groups" : (on.length ? on.join(" + ") : "no groups"));
  statusEl.innerHTML = "";
  const b = document.createElement("b");
  b.textContent = visible.length + " of 789 shown";
  statusEl.appendChild(b);
  statusEl.appendChild(document.createTextNode(" · " + parts.join(" · ") +
    (visible.length === 789 ? "" : " — use Reset filters to clear")));
  emptyState.style.display = visible.length === 0 ? "block" : "none";
  if (visible.length === 0) {
    emptyText.textContent = s ? ('No one matches "' + s + '". Try a shorter search, or reset.')
      : "Every group is filtered off. Turn a group back on, or reset.";
  }
  renderList();
  draw();
}

// ---------- list view (primary on mobile) ----------
const rowEls = new Map();
(function buildList() {
  byGroup.forEach((list, g) => {
    const h = document.createElement("div");
    h.className = "listgroup"; h.dataset.g = g;
    const dot = document.createElement("span"); dot.className = "dot";
    dot.style.background = groupColor(g); h.appendChild(dot);
    h.appendChild(document.createTextNode(GROUPS[g].plural + " · " + list.length));
    listView.appendChild(h);
    list.forEach(nd => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "person"; b.dataset.u = nd.u; b.dataset.g = g;
      const av = document.createElement("span"); av.className = "avatar";
      av.style.background = groupColor(g);
      av.textContent = (nd.n || nd.u).trim().charAt(0).toUpperCase() || "?";
      const who = document.createElement("span"); who.className = "who";
      const nm = document.createElement("b"); nm.textContent = nd.n || ("@" + nd.u);
      const hd = document.createElement("span"); hd.textContent = "@" + nd.u;
      who.appendChild(nm); who.appendChild(hd);
      const tag = document.createElement("span"); tag.className = "tag";
      tag.textContent = GROUPS[g].label;
      b.appendChild(av); b.appendChild(who); b.appendChild(tag);
      b.addEventListener("click", () => selectNode(nd, { fromList: true }));
      listView.appendChild(b);
      rowEls.set(nd.u, b);
    });
  });
})();
function renderList() {
  const vis = new Set(visible.map(n => n.u));
  rowEls.forEach((el, u) => { el.style.display = vis.has(u) ? "" : "none"; });
  document.querySelectorAll(".listgroup").forEach(h => {
    const g = +h.dataset.g;
    h.style.display = (state.groups.has(g) && visible.some(n => n.g === g)) ? "" : "none";
  });
}

// ---------- canvas graph: zoom / pan / pinch / tap ----------
let dpr = 1, cw = 0, ch = 0, scale = 0.6, tx = 0, ty = 0;
function fitView() {
  scale = Math.min(cw, ch) / 1040; tx = 0; ty = 0; draw();
}
function resize() {
  dpr = window.devicePixelRatio || 1;
  cw = wrap.clientWidth; ch = canvas.clientHeight;
  canvas.width = Math.round(cw * dpr); canvas.height = Math.round(ch * dpr);
  draw();
}
const w2sX = x => (x - CX) * scale + cw / 2 + tx;
const w2sY = y => (y - CY) * scale + ch / 2 + ty;
const s2wX = x => (x - cw / 2 - tx) / scale + CX;
const s2wY = y => (y - ch / 2 - ty) / scale + CY;
function zoomAt(px, py, factor) {
  const ns = Math.min(6, Math.max(0.12, scale * factor));
  const wx = s2wX(px), wy = s2wY(py);
  scale = ns; tx = px - cw / 2 - (wx - CX) * scale; ty = py - ch / 2 - (wy - CY) * scale;
  draw();
}
function theme() {
  return document.documentElement.dataset.theme === "dark"
    ? { ink: "#f4f4f5", muted: "#9ca3af", ring: "rgba(255,255,255,.14)", spoke: "rgba(255,255,255,.05)" }
    : { ink: "#141414", muted: "#6b7280", ring: "rgba(0,0,0,.10)", spoke: "rgba(0,0,0,.05)" };
}
function draw() {
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cw, ch);
  const t = theme();
  ctx.textAlign = "center";
  // ring guides + labels
  ctx.font = "600 12px Inter, sans-serif";
  GROUPS.forEach(g => {
    if (!state.groups.has(GROUPS.indexOf(g))) return;
    ctx.beginPath(); ctx.arc(w2sX(CX), w2sY(CY), g.r * scale, 0, Math.PI * 2);
    ctx.setLineDash([4, 5]); ctx.strokeStyle = t.ring; ctx.lineWidth = 1; ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = t.muted;
    ctx.fillText(g.plural + " · " + byGroup[GROUPS.indexOf(g)].length, w2sX(CX), w2sY(CY - g.r) - 8);
  });
  // spokes
  const visSet = new Set(visible);
  ctx.strokeStyle = t.spoke; ctx.lineWidth = 1;
  ctx.beginPath();
  nodes.forEach(nd => {
    if (!visSet.has(nd)) return;
    ctx.moveTo(w2sX(CX), w2sY(CY)); ctx.lineTo(w2sX(nd.x), w2sY(nd.y));
  });
  ctx.stroke();
  // nodes: fixed world radius, so zooming genuinely separates them
  const visNodes = visible;
  visNodes.forEach(nd => {
    const r = Math.max(2, 4.5 * scale);
    ctx.beginPath(); ctx.arc(w2sX(nd.x), w2sY(nd.y), r, 0, Math.PI * 2);
    ctx.fillStyle = groupColor(nd.g); ctx.globalAlpha = state.q ? 0.95 : 0.8; ctx.fill();
  });
  ctx.globalAlpha = 1;
  if (state.q) { // dim non-matches is replaced by hiding: matches are the visible set
  }
  // centre: Namkhang, labelled on the chart itself
  ctx.beginPath(); ctx.arc(w2sX(CX), w2sY(CY), Math.max(14, 26 * scale), 0, Math.PI * 2);
  ctx.fillStyle = t.ink; ctx.fill();
  ctx.lineWidth = 3; ctx.strokeStyle = theme().ink === "#f4f4f5" ? "#0e0e11" : "#fff"; ctx.stroke();
  ctx.fillStyle = theme().ink === "#f4f4f5" ? "#0e0e11" : "#fff";
  ctx.font = "800 " + Math.max(11, 18 * scale) + "px Sora, Inter, sans-serif";
  ctx.fillText("N", w2sX(CX), w2sY(CY) + Math.max(4, 6 * scale));
  ctx.fillStyle = t.ink;
  ctx.font = "700 13px Sora, Inter, sans-serif";
  ctx.fillText("Namkhang", w2sX(CX), w2sY(CY) + Math.max(14, 26 * scale) + 18);
  // focus ring (keyboard)
  if (focused) {
    ctx.beginPath(); ctx.arc(w2sX(focused.x), w2sY(focused.y), Math.max(8, 10 * scale), 0, Math.PI * 2);
    ctx.setLineDash([3, 3]); ctx.strokeStyle = t.ink; ctx.lineWidth = 1.5; ctx.stroke(); ctx.setLineDash([]);
  }
  // selection ring + label
  if (selected) {
    ctx.beginPath(); ctx.arc(w2sX(selected.x), w2sY(selected.y), Math.max(9, 12 * scale), 0, Math.PI * 2);
    ctx.strokeStyle = "#fff"; ctx.lineWidth = 3; ctx.stroke();
    ctx.beginPath(); ctx.arc(w2sX(selected.x), w2sY(selected.y), Math.max(9, 12 * scale), 0, Math.PI * 2);
    ctx.strokeStyle = groupColor(selected.g); ctx.lineWidth = 2; ctx.stroke();
    ctx.font = "700 13px Inter, sans-serif";
    const lbl = "@" + selected.u;
    const tw = ctx.measureText(lbl).width;
    const lx = Math.min(Math.max(w2sX(selected.x), tw / 2 + 8), cw - tw / 2 - 8);
    const ly = Math.max(16, w2sY(selected.y) - Math.max(12, 14 * scale) - 8);
    ctx.fillStyle = "rgba(20,20,20,.85)";
    ctx.beginPath(); ctx.roundRect(lx - tw / 2 - 7, ly - 11, tw + 14, 20, 6); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.fillText(lbl, lx, ly + 3);
  }
}

// pointer: pan, pinch, tap-to-select, hover tooltip (mouse only for hover)
const pointers = new Map();
let downAt = null, moved = 0, pinchD = 0;
canvas.addEventListener("pointerdown", e => {
  canvas.setPointerCapture(e.pointerId);
  pointers.set(e.pointerId, { x: e.offsetX, y: e.offsetY });
  if (pointers.size === 2) {
    const p = [...pointers.values()];
    pinchD = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
  }
  downAt = { x: e.offsetX, y: e.offsetY, t: Date.now() }; moved = 0;
});
canvas.addEventListener("pointermove", e => {
  const prev = pointers.get(e.pointerId);
  if (prev) {
    const dx = e.offsetX - prev.x, dy = e.offsetY - prev.y;
    moved += Math.abs(dx) + Math.abs(dy);
    pointers.set(e.pointerId, { x: e.offsetX, y: e.offsetY });
    if (pointers.size === 2) {
      const p = [...pointers.values()];
      const d = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
      if (pinchD > 0) zoomAt((p[0].x + p[1].x) / 2, (p[0].y + p[1].y) / 2, d / pinchD);
      pinchD = d;
      tx += dx / 2; ty += dy / 2; draw();
    } else if (downAt) { tx += dx; ty += dy; draw(); }
  }
  if (e.pointerType === "mouse" && pointers.size <= 1 && !downAt) {
    const nd = nearestNode(e.offsetX, e.offsetY);
    if (nd) {
      tip.style.display = "block";
      tip.style.left = Math.min(e.offsetX + 12, cw - 180) + "px";
      tip.style.top = (e.offsetY + 12) + "px";
      tip.textContent = labelOf(nd);
    } else tip.style.display = "none";
  }
});
function endPointer(e) {
  pointers.delete(e.pointerId);
  if (pointers.size < 2) pinchD = 0;
  if (downAt && moved < 8 && Date.now() - downAt.t < 500) {
    const nd = nearestNode(downAt.x, downAt.y);
    if (nd) selectNode(nd, { tapX: downAt.x, tapY: downAt.y });
    else if (Math.hypot(s2wX(downAt.x) - CX, s2wY(downAt.y) - CY) < 40) selectCentre();
    else { selected = null; detailClose(); draw(); }
  }
  downAt = null; tip.style.display = "none";
}
canvas.addEventListener("pointerup", endPointer);
canvas.addEventListener("pointercancel", e => { pointers.delete(e.pointerId); downAt = null; });
canvas.addEventListener("pointerleave", () => { tip.style.display = "none"; });
canvas.addEventListener("wheel", e => {
  e.preventDefault();
  zoomAt(e.offsetX, e.offsetY, Math.exp(-e.deltaY * 0.0015));
}, { passive: false });
function nearestNode(px, py) {
  const wx = s2wX(px), wy = s2wY(py), tol = 16 / scale;
  let best = null, bd = Infinity;
  for (const nd of visible) {
    const d = Math.hypot(nd.x - wx, nd.y - wy);
    if (d < bd) { bd = d; best = nd; }
  }
  return bd <= tol ? best : null;
}

// ---------- selection + detail / bottom sheet ----------
function detailClose() {
  detail.classList.remove("sheet");
  detail.innerHTML = "";
  detail.textContent = "Tap a dot, or pick a name from the list, to see who it is.";
}
function selectNode(nd, opts) {
  opts = opts || {};
  selected = nd; focused = nd;
  detail.innerHTML = "";
  const close = document.createElement("button");
  close.className = "close"; close.type = "button"; close.setAttribute("aria-label", "Close details");
  close.textContent = "×";
  close.addEventListener("click", () => { selected = null; detailClose(); draw(); });
  detail.appendChild(close);
  const b = document.createElement("b");
  b.textContent = (nd.n ? nd.n + " " : "") + "@" + nd.u;
  detail.appendChild(b);
  detail.appendChild(document.createTextNode(" — " + GROUPS[nd.g].label +
    ". 1 hop from Namkhang, 2 hops from everyone else in this graph."));
  const acts = document.createElement("div"); acts.className = "actions";
  if (opts.fromList) {
    const loc = document.createElement("button"); loc.type = "button";
    loc.textContent = "Locate on graph";
    loc.addEventListener("click", () => { setView("graph"); zoomTo(nd); });
    acts.appendChild(loc);
  }
  const clear = document.createElement("button"); clear.type = "button";
  clear.textContent = "Clear selection";
  clear.addEventListener("click", () => { selected = null; detailClose(); draw(); });
  acts.appendChild(clear);
  detail.appendChild(acts);
  if (opts.tapX !== undefined) {
    tip.style.display = "block";
    tip.style.left = Math.min(opts.tapX + 12, cw - 180) + "px";
    tip.style.top = (opts.tapY + 12) + "px";
    tip.textContent = labelOf(nd);
    setTimeout(() => { tip.style.display = "none"; }, 2500);
  }
  if (window.innerWidth <= 640 && currentView === "graph") detail.classList.add("sheet");
  draw();
}
function selectCentre() {
  selected = null;
  detail.innerHTML = "";
  const b = document.createElement("b"); b.textContent = "Namkhang — @namkhangnle";
  detail.appendChild(b);
  detail.appendChild(document.createTextNode(
    " The centre of this graph. Every person here is 1 hop from him; any two people connect through him in 2 hops."));
  if (window.innerWidth <= 640 && currentView === "graph") detail.classList.add("sheet");
  draw();
}
function zoomTo(nd) {
  scale = Math.min(2.2, Math.max(1.1, scale));
  tx = cw / 2 - (nd.x - CX) * scale; ty = ch / 2 - (nd.y - CY) * scale;
  selectNode(nd); draw();
}

// ---------- keyboard access on the graph ----------
wrap.addEventListener("keydown", e => {
  if (!visible.length) return;
  if (e.key === "ArrowRight" || e.key === "ArrowDown") {
    e.preventDefault();
    const i = focused ? visible.indexOf(focused) : -1;
    focused = visible[(i + 1) % visible.length]; selected = null; detailClose(); draw();
    announceFocus();
  } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
    e.preventDefault();
    const i = focused ? visible.indexOf(focused) : 0;
    focused = visible[(i - 1 + visible.length) % visible.length]; selected = null; detailClose(); draw();
    announceFocus();
  } else if ((e.key === "Enter" || e.key === " ") && focused) {
    e.preventDefault(); selectNode(focused);
  } else if (e.key === "+" || e.key === "=") { e.preventDefault(); zoomAt(cw / 2, ch / 2, 1.25); }
  else if (e.key === "-") { e.preventDefault(); zoomAt(cw / 2, ch / 2, 0.8); }
  else if (e.key === "0") { e.preventDefault(); fitView(); }
});
function announceFocus() {
  if (!focused) return;
  statusEl.textContent = "Focused: " + labelOf(focused) + " — press Enter to select.";
}
$("zoomIn").addEventListener("click", () => zoomAt(cw / 2, ch / 2, 1.35));
$("zoomOut").addEventListener("click", () => zoomAt(cw / 2, ch / 2, 1 / 1.35));
$("zoomFit").addEventListener("click", fitView);

// ---------- view toggle: list is primary on mobile ----------
let currentView = "graph";
function setView(v) {
  currentView = v;
  $("viewList").setAttribute("aria-pressed", String(v === "list"));
  $("viewGraph").setAttribute("aria-pressed", String(v === "graph"));
  listView.hidden = v !== "list";
  wrap.hidden = v !== "graph";
  $("graphHint").style.display = v === "graph" ? "" : "none";
  if (v === "graph") { resize(); fitView(); }
}
$("viewList").addEventListener("click", () => setView("list"));
$("viewGraph").addEventListener("click", () => setView("graph"));

// ---------- search + chips + reset (coherent: they reset each other) ----------
q.addEventListener("input", () => {
  state.q = q.value.trim().toLowerCase();
  if (state.q) { // a search searches everyone: groups back on
    state.groups = new Set([0, 1, 2]);
    syncChips();
  }
  applyFilters();
});
document.querySelectorAll("#chips .chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const g = +chip.dataset.g;
    if (state.q) { q.value = ""; state.q = ""; } // a chip choice clears the search
    if (state.groups.has(g)) state.groups.delete(g); else state.groups.add(g);
    syncChips();
    applyFilters();
  });
});
function syncChips() {
  document.querySelectorAll("#chips .chip").forEach(chip => {
    const g = +chip.dataset.g;
    chip.classList.toggle("off", !state.groups.has(g));
    chip.setAttribute("aria-pressed", String(state.groups.has(g)));
  });
}
function resetAll() {
  state.q = ""; q.value = "";
  state.groups = new Set([0, 1, 2]);
  selected = null; focused = null; detailClose();
  syncChips(); applyFilters(); fitView();
}
$("resetBtn").addEventListener("click", resetAll);
$("emptyReset").addEventListener("click", resetAll);

// ---------- dark mode ----------
const themeBtn = $("themeBtn");
function setTheme(mode) {
  document.documentElement.dataset.theme = mode;
  try { localStorage.setItem("igc-theme", mode); } catch (err) {}
  themeBtn.textContent = mode === "dark" ? "☀️ Light" : "🌙 Dark";
  draw();
}
themeBtn.addEventListener("click", () => {
  setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
});
(function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem("igc-theme"); } catch (err) {}
  setTheme(saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
})();

// ---------- boot ----------
window.addEventListener("resize", resize);
setView(window.innerWidth <= 640 ? "list" : "graph");
syncChips();
applyFilters();
resize();
fitView();
</script>
</body>
</html>
"""


def load(filename, key):
    with open(os.path.join(MVP, filename), encoding="utf-8") as f:
        return json.load(f)[key]


def build_users(anonymize=False):
    followers = load("Namkhang-Followers.json", "followers")
    following = load("Namkhang-Following.json", "followings")
    f_set = {u["username"]: u["full_name"] for u in followers}
    g_set = {u["username"]: u["full_name"] for u in following}

    def group_of(u):
        if u in f_set and u in g_set:
            return 0
        if u in f_set:
            return 1
        return 2

    users = []
    for u in sorted(set(f_set) | set(g_set)):
        name = (f_set.get(u) or g_set.get(u) or "").strip()
        if anonymize:
            digest = hashlib.sha256(u.encode("utf-8")).hexdigest()[:8]
            users.append({"u": "user_" + digest, "n": "", "g": group_of(u)})
        else:
            users.append({"u": u, "n": name, "g": group_of(u)})
    return users


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anonymize", action="store_true",
                    help="hash handles, drop full names (owner-review variant)")
    ap.add_argument("--out", default=None, help="output path (default index.html)")
    args = ap.parse_args()

    users = build_users(anonymize=args.anonymize)
    data_json = json.dumps(users, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.replace("%%USERS_JSON%%", data_json)
    if args.anonymize:
        html = html.replace(
            "Every count on this page is from April 2024.",
            "ANONYMIZED REVIEW COPY — handles are one-way hashes, full names removed. "
            "Every count on this page is from April 2024.")
        html = html.replace(
            'src="ego_network.png"', 'src="ego_network.png" data-anonymized="true"')
    out = args.out or os.path.join(HERE, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {out} ({len(html)/1024:.1f} KB, {len(users)} users embedded"
          + (", ANONYMIZED" if args.anonymize else "") + ")")


if __name__ == "__main__":
    main()
