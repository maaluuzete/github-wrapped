import argparse
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from collections import Counter

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
API_BASE = "https://api.github.com"

def error(msg):
    console.print(Panel(msg, style="bold red"))
    sys.exit(1)

def validate_days(value):
    try:
        days = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Days must be an integer.")
    if days <= 0:
        raise argparse.ArgumentTypeError("Days must be a positive integer.")
    return days

def parse_args():
    parser = argparse.ArgumentParser(description="GitHub Wrapped - Activity summary dashboard")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--days", required=True, type=validate_days, help="Time window in days")
    return parser.parse_args()

def github_request(url, token, params=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.exceptions.RequestException as e:
        error(f"Network error: {e}")

    if r.status_code == 404:
        error(f"User not found.")
    elif r.status_code in (401, 403):
        error("Authentication failed or API rate limit exceeded.")
    elif r.status_code >= 500:
        error("GitHub server error. Try again later.")

    return r.json()

def fetch_events(username, token, days):
    events = []
    page = 1
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with console.status(f"[bold green]Fetching events for {username}...", spinner="dots"):
        while True:
            url = f"{API_BASE}/users/{username}/events"
            data = github_request(url, token, {"per_page": 100, "page": page})

            if not data or not isinstance(data, list):
                break

            last_event_date = datetime.strptime(
                data[-1]["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)

            events.extend(data)

            if last_event_date < cutoff or len(data) < 100:
                break
            
            page += 1

    filtered = [
        ev for ev in events 
        if datetime.strptime(ev["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) >= cutoff
    ]
    return filtered

def fetch_repos(username, token):
    repos = []
    page=1
    with console.status("[bold blue]Fetching repositories...", spinner="dots"):
        while True:
            url = f"{API_BASE}/users/{username}/repos"
            data = github_request(url, token, {"per_page": 100, "page": page})
            
            if not data or not isinstance(data, list):
                break
                
            repos.extend(data)
            
            if len(data) < 100:
                break
            page+=1
    return repos

def analyze_events(events):
    stats = {
        "total_events": len(events),
        "commits": 0,
        "prs_opened": 0,
        "prs_merged": 0,
        "issues": 0,
        "repo_counter": Counter(),
        "day_counter": Counter(),
    }

    for ev in events:
        typ = ev["type"]
        repo = ev["repo"]["name"]
        stats["repo_counter"][repo] += 1
        day = ev["created_at"][:10]
        stats["day_counter"][day] += 1

        if typ == "PushEvent":
            stats["commits"] += ev["payload"].get("size", 0)
        elif typ == "PullRequestEvent":
            payload = ev["payload"]
            action = payload.get("action")
            if action == "opened":
                stats["prs_opened"] += 1
            elif action == "closed" and payload.get("pull_request", {}).get("merged"):
                stats["prs_merged"] += 1
        elif typ == "IssuesEvent" and ev["payload"].get("action") == "opened":
            stats["issues"] += 1

    return stats

def analyze_languages(repos):
    return Counter(r["language"] for r in repos if r.get("language"))

def render_dashboard(username, days, stats, lang_stats):
    console.rule(f"[bold cyan]GitHub Activity Report[/bold cyan]")
    
    header = Text(f"{username} — last {days} days", style="bold magenta")
    console.print(header, justify="center")

    if stats["total_events"] == 0:
        console.print(Panel(
            "No activity found in this period.\n[dim]Note: GitHub API only provides public events from the last 90 days.[/dim]", 
            style="yellow", 
            title="Empty History"
        ))
        return


    summary = Table.grid(padding=1)
    summary.add_column(justify="left", style="cyan")
    summary.add_column(justify="right", style="bold white")
    summary.add_row("Total Commits", str(stats["commits"]))
    summary.add_row("PRs Opened", str(stats["prs_opened"]))
    summary.add_row("PRs Merged", str(stats["prs_merged"]))
    summary.add_row("Issues Opened", str(stats["issues"]))

    if stats["day_counter"]:
        busiest_day, count = stats["day_counter"].most_common(1)[0]
        summary.add_row("Busiest Day", f"{busiest_day} ({count} events)")

    console.print(Panel(summary, title="Activity Summary", border_style="green"))


    if stats["repo_counter"]:
        repo_table = Table(title="Top 5 Repositories", header_style="bold blue", expand=True)
        repo_table.add_column("#", justify="center", width=4)
        repo_table.add_column("Repository")
        repo_table.add_column("Events", justify="right")
        for i, (name, count) in enumerate(stats["repo_counter"].most_common(5), 1):
            repo_table.add_row(str(i), name, str(count))
        console.print(repo_table)

    if lang_stats:
        lang_table = Table(title="Language Usage (All Repos)", header_style="bold yellow")
        lang_table.add_column("Language")
        lang_table.add_column("Repos Count", justify="right")
        for lang, count in lang_stats.most_common(10):
            lang_table.add_row(lang, str(count))
        console.print(lang_table)
    if days > 90:
        console.print("\n[dim]* GitHub only stores public events for 90 days. Results for older periods may be incomplete.[/dim]")

def main():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        error("Missing GITHUB_TOKEN in .env file.")

    args = parse_args()
    
    events = fetch_events(args.username, token, args.days)
    repos = fetch_repos(args.username, token)
    
    stats = analyze_events(events)
    lang_stats = analyze_languages(repos)

    render_dashboard(args.username, args.days, stats, lang_stats)

if __name__ == "__main__":
    main()