"""
github_stats_agent.py — JARVIS GitHub Stats & Voice Git Control
================================================================
Fetches Raj's live GitHub stats and allows voice-controlled git operations.
Uses the public GitHub API — no OAuth required for public data.

Features:
  - Live contribution stats (commits today, total repos, stars)
  - Recent commit activity
  - Open issues and PRs across repos
  - Voice git commands: push, pull, status, commit
  - Repo overview

Voice commands:
  - "show my GitHub stats"
  - "how many commits today"
  - "my GitHub activity"
  - "open issues on GitHub"
  - "JARVIS push my changes"
  - "git status"
  - "git commit saying [message]"
"""

import os
import re
import subprocess
import datetime
import requests

GITHUB_USERNAME = "RAJ-15012006"
GITHUB_API_BASE = "https://api.github.com"

GITHUB_TRIGGERS = [
    "github stats", "my github", "github activity", "commits today",
    "my repos", "my repositories", "stars on github", "github profile",
    "open issues", "pull requests", "github push", "git push", "git pull",
    "git status", "git commit", "push my changes", "push to github",
    "commit and push", "show my github",
]

def is_github_command(command: str) -> bool:
    cmd = command.lower()
    return any(t in cmd for t in GITHUB_TRIGGERS)


def _github_get(endpoint: str) -> dict:
    """Make a GitHub API GET request."""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        resp = requests.get(f"{GITHUB_API_BASE}{endpoint}", headers=headers, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_profile_stats() -> str:
    """Get Raj's GitHub profile statistics."""
    data = _github_get(f"/users/{GITHUB_USERNAME}")
    if "error" in data:
        return f"Raj, couldn't fetch GitHub profile: {data['error']}"

    repos = _github_get(f"/users/{GITHUB_USERNAME}/repos?per_page=100&sort=updated")
    total_stars = 0
    total_forks = 0
    languages = {}
    recent_repos = []

    if isinstance(repos, list):
        for repo in repos:
            total_stars += repo.get("stargazers_count", 0)
            total_forks += repo.get("forks_count", 0)
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        recent_repos = [r["name"] for r in repos[:5]]

    top_lang = max(languages, key=languages.get) if languages else "Python"
    public_repos = data.get("public_repos", 0)
    followers = data.get("followers", 0)
    following = data.get("following", 0)

    return (
        f"📊 GitHub Stats for @{GITHUB_USERNAME}:\n\n"
        f"🗂️  Public Repos: {public_repos}\n"
        f"⭐ Total Stars: {total_stars}\n"
        f"🍴 Total Forks: {total_forks}\n"
        f"👥 Followers: {followers} | Following: {following}\n"
        f"💻 Top Language: {top_lang}\n"
        f"🕒 Recent Repos: {', '.join(recent_repos[:3])}"
    )


def get_recent_activity() -> str:
    """Get recent GitHub push/commit activity."""
    events = _github_get(f"/users/{GITHUB_USERNAME}/events/public?per_page=20")
    if isinstance(events, dict) and "error" in events:
        return f"Couldn't fetch activity: {events['error']}"

    if not events:
        return "No recent GitHub activity found, Sir."

    # Filter push events
    push_events = [e for e in events if e.get("type") == "PushEvent"]
    if not push_events:
        return "No recent push events found, Sir."

    lines = ["⚡ Recent GitHub Activity:\n"]
    seen_repos = set()
    for event in push_events[:5]:
        repo = event.get("repo", {}).get("name", "Unknown")
        if repo in seen_repos:
            continue
        seen_repos.add(repo)

        commits = event.get("payload", {}).get("commits", [])
        commit_msg = commits[0].get("message", "No message") if commits else "No commits"
        created_at = event.get("created_at", "")
        try:
            dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            ist = dt + datetime.timedelta(hours=5, minutes=30)
            time_str = ist.strftime("%d %b, %I:%M %p")
        except Exception:
            time_str = created_at[:10]

        lines.append(f"• [{repo.split('/')[-1]}] {commit_msg[:60]} — {time_str}")

    return "\n".join(lines)


def get_open_issues() -> str:
    """Get open issues across Raj's repos."""
    repos = _github_get(f"/users/{GITHUB_USERNAME}/repos?per_page=50")
    if isinstance(repos, dict) and "error" in repos:
        return f"Couldn't fetch repos: {repos['error']}"

    all_issues = []
    for repo in repos[:10]:  # Check top 10 repos
        repo_name = repo.get("name", "")
        if repo.get("open_issues_count", 0) > 0:
            issues = _github_get(f"/repos/{GITHUB_USERNAME}/{repo_name}/issues?state=open&per_page=3")
            if isinstance(issues, list):
                for issue in issues:
                    all_issues.append(f"• [{repo_name}] #{issue['number']}: {issue['title']}")

    if not all_issues:
        return "No open issues found across your repositories, Sir. Clean slate! 🎉"

    return f"🔴 Open Issues ({len(all_issues)}):\n\n" + "\n".join(all_issues[:10])


# ── Voice Git Commands ────────────────────────────────────────────────────────

def _run_git(args: list, cwd: str = None) -> str:
    """Run a git command and return output."""
    try:
        # Default cwd: try Desktop/jarvis_main
        if not cwd:
            home = os.path.expanduser("~")
            for candidate in [
                os.path.join(home, "Desktop", "jarvis_main"),
                os.path.join(home, "projects"),
                home,
            ]:
                if os.path.exists(os.path.join(candidate, ".git")):
                    cwd = candidate
                    break

        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else "Done."
    except subprocess.TimeoutExpired:
        return "Git command timed out, Sir."
    except Exception as e:
        return f"Git command failed: {str(e)}"


def git_status() -> str:
    """Run git status."""
    output = _run_git(["status", "--short"])
    if not output or output == "Done.":
        return "✅ Working tree is clean, Sir. Nothing to commit."
    return f"📋 Git Status:\n{output}"


def git_push(message: str = "JARVIS auto-commit") -> str:
    """Stage all, commit with message, and push."""
    # Add all
    add_out = _run_git(["add", "-A"])
    # Commit
    commit_out = _run_git(["commit", "-m", message])
    if "nothing to commit" in commit_out.lower():
        return "Nothing to commit, Sir. Working tree is clean."
    # Push
    push_out = _run_git(["push"])
    if "error" in push_out.lower() or "fatal" in push_out.lower():
        return f"❌ Push failed, Sir:\n{push_out}"
    return f"✅ Committed and pushed to GitHub:\n📝 Message: '{message}'"


def git_pull() -> str:
    """Pull latest changes."""
    output = _run_git(["pull"])
    return f"📥 Git Pull:\n{output}"


def handle_github_command(command: str) -> str:
    """Main dispatcher for GitHub/git voice commands."""
    cmd = command.lower().strip()

    if any(w in cmd for w in ["push", "commit and push", "push my changes"]):
        # Extract commit message
        msg = "JARVIS voice commit"
        for kw in ["saying", "message", "with message", "commit message"]:
            if kw in cmd:
                parts = cmd.split(kw)
                if len(parts) > 1:
                    msg = parts[-1].strip()
                    break
        # Default descriptive message
        if msg == "JARVIS voice commit":
            msg = f"feat: JARVIS voice commit — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return git_push(msg)

    if "pull" in cmd:
        return git_pull()

    if "status" in cmd:
        return git_status()

    if "issues" in cmd:
        return get_open_issues()

    if any(w in cmd for w in ["activity", "recent", "commits today"]):
        return get_recent_activity()

    # Default: full stats
    return get_profile_stats()
