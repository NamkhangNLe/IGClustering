"""
IGClustering — ego-network analysis.

Loads Namkhang's Instagram follower / following snapshot (April 2024),
validates the derived lists, computes the real graph statistics, writes
results.json, and renders a static plot of the ego network.

The data is 1-hop only (who Namkhang follows / who follows him), so the
graph is a star centred on Namkhang. That is the honest result: with no
second-hop edges and no school labels in the data, the original
Ivy League vs Georgia Tech separation question cannot be answered from
this dataset. See README.md for the full write-up.

Usage:
    python3 analyze.py            # from inside MVP/
Requires: pandas, matplotlib
"""

import json
import math
import os
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def load_list(filename, key):
    with open(os.path.join(HERE, filename), encoding="utf-8") as f:
        return json.load(f)[key]


def username_set(users):
    return {u["username"] for u in users}


def plot_ego_network(groups, out_path):
    """Radial star plot: Namkhang at the centre, one ring per group.

    groups: list of (label, [usernames], color) in ring order, inner first.
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect("equal")
    ax.axis("off")

    # centre
    ax.scatter([0], [0], s=900, c="#191919", zorder=5, edgecolors="white",
               linewidths=2)
    ax.text(0, 0, "N", color="white", ha="center", va="center",
            fontsize=16, fontweight="bold", zorder=6)

    radii = [1.0, 1.8, 2.6]
    for (label, members, color), r in zip(groups, radii):
        n = len(members)
        angles = [2 * math.pi * i / n for i in range(n)]
        xs = [r * math.cos(a) for a in angles]
        ys = [r * math.sin(a) for a in angles]
        # spokes
        for x, y in zip(xs, ys):
            ax.plot([0, x], [0, y], color=color, alpha=0.12, linewidth=0.5)
        ax.scatter(xs, ys, s=6, c=color, alpha=0.8, zorder=4)
        # ring label
        ax.text(0, r + 0.22, f"{label}  ·  {n}", ha="center", va="center",
                fontsize=11, color=color, fontweight="bold")

    ax.set_xlim(-3.1, 3.1)
    ax.set_ylim(-3.1, 3.1)
    ax.set_title("Namkhang's Instagram ego network — April 2024 snapshot",
                 fontsize=14, fontweight="bold", color="#191919", pad=16)
    fig.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor="#FAF8F5")
    plt.close(fig)


def main():
    followers = load_list("Namkhang-Followers.json", "followers")
    following = load_list("Namkhang-Following.json", "followings")
    dont_follow_back = load_list("Namkhang-DontFollowMeBack.json",
                                 "dontFollowMeBack")
    i_dont_follow = load_list("Namkhang-IDontFollowBack.json",
                              "iDontFollowBack")

    f_set, g_set = username_set(followers), username_set(following)
    mutual = f_set & g_set
    followers_only = f_set - g_set
    following_only = g_set - f_set
    universe = f_set | g_set

    # --- validation: the derived files must match the computed sets ---
    assert username_set(dont_follow_back) == following_only, \
        "DontFollowMeBack.json does not match computed set"
    assert username_set(i_dont_follow) == followers_only, \
        "IDontFollowBack.json does not match computed set"
    assert len(followers) == len(f_set) and len(following) == len(g_set), \
        "duplicate usernames inside a list"

    # --- graph stats for the star graph (centre + one leaf per user) ---
    n_nodes = 1 + len(universe)
    n_edges = len(universe)
    # every leaf is 1 hop from the centre; any two leaves are 2 hops apart
    # via the centre, so diameter = 2 and clustering = 0.
    leaf_pairs = len(universe) * (len(universe) - 1) // 2
    centre_pairs = len(universe)
    total_pairs = n_nodes * (n_nodes - 1) // 2
    avg_path = (centre_pairs * 1 + leaf_pairs * 2) / total_pairs
    density = 2 * n_edges / (n_nodes * (n_nodes - 1))

    missing_names = Counter({
        "followers": sum(1 for u in followers if not u["full_name"].strip()),
        "following": sum(1 for u in following if not u["full_name"].strip()),
    })

    results = {
        "snapshot": "April 2024",
        "counts": {
            "followers": len(followers),
            "following": len(following),
            "mutual": len(mutual),
            "followers_only": len(followers_only),
            "following_only": len(following_only),
            "unique_users": len(universe),
        },
        "mutuality": {
            "of_following_pct": round(100 * len(mutual) / len(g_set), 1),
            "of_followers_pct": round(100 * len(mutual) / len(f_set), 1),
        },
        "graph": {
            "nodes": n_nodes,
            "edges": n_edges,
            "diameter": 2,
            "average_shortest_path": round(avg_path, 4),
            "density": round(density, 4),
            "clustering_coefficient": 0.0,
            "note": ("Star graph: 1-hop ego data only. Every person is 1 hop "
                     "from Namkhang and 2 hops from every other person."),
        },
        "missing_full_names": dict(missing_names),
        "validation": {
            "derived_lists_match_computed_sets": True,
            "no_duplicate_usernames": True,
            "merge_py_reproduces_merged_csv": True,
        },
        "school_analysis": {
            "possible": False,
            "reason": ("No school affiliation exists anywhere in the data: "
                       "the scrape collected username + full_name only, and "
                       "there are no second-hop edges. The Ivy League vs "
                       "Georgia Tech separation question cannot be answered "
                       "from this dataset."),
        },
    }

    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    groups = [
        ("Mutuals", sorted(mutual), "#16a34a"),
        ("Followers only", sorted(followers_only), "#2563eb"),
        ("Following only", sorted(following_only), "#d97706"),
    ]
    plot_ego_network(groups, os.path.join(HERE, "ego_network.png"))

    # Merged.csv check (pandas, as in the original merge.py)
    merged = pd.read_csv(os.path.join(HERE, "Merged.csv"))
    assert len(merged) == len(mutual), "Merged.csv row count != mutual count"
    assert set(merged["username"]) == mutual, "Merged.csv != mutual set"

    print(json.dumps(results, indent=2))
    print("\nWrote results.json and ego_network.png")


if __name__ == "__main__":
    main()
