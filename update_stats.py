"""
update_stats.py

Fetches Codeforces stats for a given handle and updates the
STATS table in README.md between the <!-- STATS_START --> and
<!-- STATS_END --> markers.

Usage:
    python update_stats.py

Set your handle either by editing HANDLE below, or by setting
the CF_HANDLE environment variable (useful in CI).
"""

import os
import re
import sys
import requests

HANDLE = os.environ.get("CF_HANDLE", "f220b")
README_PATH = "README.md"


def fetch_json(url: str) -> dict:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise RuntimeError(f"Codeforces API error for {url}: {data.get('comment')}")
    return data


def get_rating(handle: str):
    data = fetch_json(f"https://codeforces.com/api/user.info?handles={handle}")
    user = data["result"][0]
    return user.get("rating", "Unrated"), user.get("maxRating", "Unrated"), user.get("rank", "unrated")


def get_solve_stats(handle: str):
    data = fetch_json(f"https://codeforces.com/api/user.status?handle={handle}")
    submissions = data["result"]

    solved = set()
    contests = set()

    for s in submissions:
        problem = s["problem"]
        contest_id = problem.get("contestId")
        if contest_id is not None:
            contests.add(contest_id)
        if s.get("verdict") == "OK":
            pid = f'{contest_id}{problem.get("index")}'
            solved.add(pid)

    return len(solved), len(contests)


def build_stats_table(handle: str) -> str:
    rating, max_rating, rank = get_rating(handle)
    solved_count, contest_count = get_solve_stats(handle)

    return (
        "| Metric | Count |\n"
        "|---|---|\n"
        f"| Problems Solved | {solved_count} |\n"
        f"| Contests Participated | {contest_count} |\n"
        f"| Current Rating | {rating} ({rank}) |\n"
        f"| Max Rating | {max_rating} |\n"
    )


def update_readme(stats_table: str, readme_path: str = README_PATH):
    if not os.path.exists(readme_path):
        print(f"ERROR: {readme_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"<!-- STATS_START -->.*?<!-- STATS_END -->", re.DOTALL
    )
    replacement = f"<!-- STATS_START -->\n{stats_table}<!-- STATS_END -->"

    if not pattern.search(content):
        print(
            "ERROR: STATS_START / STATS_END markers not found in README.md. "
            "Add them around your stats table first.",
            file=sys.stderr,
        )
        sys.exit(1)

    new_content = pattern.sub(replacement, content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md stats updated successfully.")


if __name__ == "__main__":
    if HANDLE == "your_handle":
        print(
            "WARNING: Using placeholder handle 'your_handle'. "
            "Set CF_HANDLE env var or edit HANDLE in this script.",
            file=sys.stderr,
        )
    table = build_stats_table(HANDLE)
    update_readme(table)
