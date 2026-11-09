"""Draw the ego network (replaces the old plt.show() version).

Loads the follower / following snapshot, rebuilds the three groups, and
saves a static radial plot to ego_network.png (Agg backend, no display
needed). For the numbers behind the picture, run analyze.py.

Usage:
    python3 graphing.py           # from inside MVP/
"""

import os

from analyze import load_list, plot_ego_network, username_set

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    followers = load_list("Namkhang-Followers.json", "followers")
    following = load_list("Namkhang-Following.json", "followings")
    f_set, g_set = username_set(followers), username_set(following)

    groups = [
        ("Mutuals", sorted(f_set & g_set), "#16a34a"),
        ("Followers only", sorted(f_set - g_set), "#2563eb"),
        ("Following only", sorted(g_set - f_set), "#d97706"),
    ]
    out = os.path.join(HERE, "ego_network.png")
    plot_ego_network(groups, out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
