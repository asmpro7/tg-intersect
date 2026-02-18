"""
Telegram Common Members Finder — Rich CLI
Uses Pyrogram (Kurigram) + Rich for a beautiful terminal experience.

Extra features:
  • Export results to CSV, TXT, or JSON
  • Compare more than 2 groups (finds members common to ALL of them)
  • Show account type: public (@username) vs private (ID only)
  • Show member counts per group before and after
  • Elapsed time display
"""

import asyncio
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from pyrogram import Client
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table

# ── Configuration ──────────────────────────────────────────────────────────────
API_ID = 0000
API_HASH = "0000"
SESSION = "my_session"
# ──────────────────────────────────────────────────────────────────────────────

console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_user(user):
    """Return (full_name, handle, type_label)."""
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip(
    ) or "Unknown"
    if user.username:
        handle = f"@{user.username}"
        kind = "[green]Public[/green]"
    else:
        handle = f"ID: {user.id}"
        kind = "[yellow]Private[/yellow]"
    return full_name, handle, kind


# ── Async Telegram logic ───────────────────────────────────────────────────────

async def fetch_group_info(client, group_id):
    try:
        chat = await client.get_chat(group_id)
        return chat.title or str(group_id), chat.members_count
    except Exception:
        return str(group_id), None


async def fetch_members(client, group_id, progress, task):
    members = {}
    async for member in client.get_chat_members(group_id):
        user = member.user
        if user and not user.is_bot:
            members[user.id] = user
        progress.advance(task)
    return members


async def run(group_ids: list):
    start_time = time.time()

    async with Client(SESSION, api_id=API_ID, api_hash=API_HASH) as app:

        # ── Fetch group titles ────────────────────────────────────────────────
        console.rule("[bold cyan]Groups[/bold cyan]")
        group_meta = {}
        for gid in group_ids:
            title, count = await fetch_group_info(app, gid)
            group_meta[gid] = {"title": title, "count": count}
            count_str = f"{count:,}" if count else "unknown"
            console.print(
                f"  [cyan]•[/cyan] [bold]{title}[/bold]  —  {count_str} total members")

        console.print()

        # ── Fetch members with live progress bars ────────────────────────────
        all_members = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            for gid in group_ids:
                title = group_meta[gid]["title"]
                task = progress.add_task(
                    f"[cyan]Fetching[/cyan] {title}…", total=None)
                members = await fetch_members(app, gid, progress, task)
                progress.update(
                    task,
                    total=len(members), completed=len(members),
                    description=f"[green]✓[/green] {title}",
                )
                group_meta[gid]["members"] = members
                all_members.append(members)

        # ── Intersection ──────────────────────────────────────────────────────
        common_ids = set(all_members[0].keys())
        for m in all_members[1:]:
            common_ids &= set(m.keys())

        ref = all_members[0]
        common_users = sorted(
            [ref[uid] for uid in common_ids],
            key=lambda u: (u.first_name or "").lower(),
        )

        elapsed = time.time() - start_time

        # ── Summary panel ─────────────────────────────────────────────────────
        lines = []
        for gid in group_ids:
            m = group_meta[gid]
            lines.append(
                f"[bold]{m['title']}[/bold]: [cyan]{len(m['members']):,}[/cyan] human members fetched"
            )
        lines.append("")
        lines.append(
            f"[bold green]Common members found: {len(common_users):,}[/bold green]")
        lines.append(f"[dim]Completed in {elapsed:.1f}s[/dim]")

        console.print(Panel(
            "\n".join(lines),
            title="[bold cyan]Summary[/bold cyan]",
            border_style="cyan",
            padding=(1, 4),
        ))

        if not common_users:
            console.print("\n[yellow]No common members found.[/yellow]\n")
            return

        # ── Results table ─────────────────────────────────────────────────────
        pub = sum(1 for u in common_users if u.username)
        priv = len(common_users) - pub

        table = Table(
            box=box.ROUNDED,
            border_style="bright_black",
            header_style="bold cyan",
            show_lines=True,
            title=f"[bold white]Common Members[/bold white]  "
                  f"[green]{pub} public[/green]  [yellow]{priv} private[/yellow]",
            caption=f"[dim]Sorted alphabetically · {len(common_users)} total[/dim]",
        )
        table.add_column("#",       style="dim",
                         width=5,   justify="right")
        table.add_column("Name",    style="bold white", min_width=24)
        table.add_column("Handle",  style="cyan",       min_width=22)
        table.add_column("User ID", style="dim",        min_width=14)
        table.add_column("Type",    justify="center",   min_width=10)

        for i, user in enumerate(common_users, 1):
            name, handle, kind = fmt_user(user)
            table.add_row(str(i), name, handle, str(user.id), kind)

        console.print()
        console.print(table)

        # ── Export ────────────────────────────────────────────────────────────
        console.print()
        if Confirm.ask("[bold]Export results?[/bold]", default=False):
            fmt = Prompt.ask("Format", choices=[
                             "csv", "txt", "json"], default="csv")
            export(common_users, group_meta, group_ids, fmt)


def export(users, group_meta, group_ids, fmt: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(f"common_members_{ts}.{fmt}")

    if fmt == "csv":
        with open(filename, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["#", "Full Name", "Username",
                       "User ID", "Type", "Profile URL"])
            for i, user in enumerate(users, 1):
                name, handle, _ = fmt_user(user)
                kind = "Public" if user.username else "Private"
                url = (f"https://t.me/{user.username}" if user.username
                       else f"tg://user?id={user.id}")
                w.writerow([i, name, handle, user.id, kind, url])

    elif fmt == "txt":
        with open(filename, "w", encoding="utf-8") as f:
            groups_str = " ∩ ".join(group_meta[g]["title"] for g in group_ids)
            f.write(f"Common members: {groups_str}\n")
            f.write(
                f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total     : {len(users)}\n")
            f.write("=" * 60 + "\n")
            for i, user in enumerate(users, 1):
                name, handle, _ = fmt_user(user)
                f.write(f"{i:4}. {name:<30} {handle}\n")

    elif fmt == "json":
        data = {
            "generated": datetime.now().isoformat(),
            "groups": [
                {
                    "id":           str(g),
                    "title":        group_meta[g]["title"],
                    "members_fetched": len(group_meta[g]["members"]),
                }
                for g in group_ids
            ],
            "common_count": len(users),
            "members": [
                {
                    "id":         user.id,
                    "first_name": user.first_name,
                    "last_name":  user.last_name,
                    "username":   user.username,
                    "type":       "public" if user.username else "private",
                    "url":        (f"https://t.me/{user.username}" if user.username
                                   else f"tg://user?id={user.id}"),
                }
                for user in users
            ],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    console.print(
        f"\n[green]✓[/green] Saved to [bold cyan]{filename}[/bold cyan]")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    console.print(Panel.fit(
        "[bold cyan]tg-intersect[/bold cyan]\n"
        "[dim]By Ahmed Abdelmageed[/dim]",
        border_style="cyan",
        padding=(1, 6),
    ))

    if API_ID == 0 or not API_HASH:
        console.print(
            "[red]⚠  Please set API_ID and API_HASH inside the script.[/red]")
        sys.exit(1)

    console.print(
        "\n[dim]Enter group IDs or @usernames one by one.\n"
        "You can compare [bold]more than 2 groups[/bold] — "
        "result = members present in ALL groups.\n"
        "Leave blank when done (min 2 required).[/dim]\n"
    )

    group_ids = []
    idx = 1
    while True:
        label = "required" if idx <= 2 else "or leave blank to start"
        raw = Prompt.ask(
            f"  Group [cyan]{idx}[/cyan] [dim]({label})[/dim]"
        ).strip()

        if not raw:
            if idx <= 2:
                console.print("[red]  At least 2 groups are required.[/red]")
                continue
            break

        try:
            group_ids.append(int(raw))
        except ValueError:
            group_ids.append(raw)
        idx += 1

    console.print()
    asyncio.run(run(group_ids))
    console.print()


if __name__ == "__main__":
    main()

