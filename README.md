# 🔍 tg-intersect

> **Find members shared between Telegram groups — fast, from your terminal.**

`tg-intersect` is a Python CLI tool that connects to Telegram via your own account and finds users who are members of **two or more groups simultaneously**. Results are displayed in a rich, colour-coded table and can be exported to CSV, JSON, or plain text in one keystroke.

---

## ✨ Features

- **Multi-group comparison** — compare 2, 3, or more groups at once; finds members common to *all* of them
- **Live progress bars** — real-time fetch status per group with elapsed time
- **Rich terminal output** — styled table with public/private account labels, sorted alphabetically
- **Export results** — save to `.csv`, `.json`, or `.txt` with a timestamped filename
- **Bot filtering** — bots are automatically excluded from results
- **Session reuse** — logs in once, saves a session file, never asks for OTP again

---

## 📋 Requirements

- Python 3.8+
- A Telegram account
- Telegram API credentials (free) → [my.telegram.org](https://my.telegram.org)
- Admin or member access to the groups you want to scan

---

## ⚙️ Installation

```bash
# 1. Clone the repo
git clone https://github.com/asmpro7/tg-intersect.git
cd tg-intersect

# 2. Install dependencies
pip install kurigram tgcrypto rich
```

---

## 🔑 Configuration

Open `tg-intersect.py` and fill in the two lines near the top:

```python
API_ID   = 0000      
API_HASH = "0000"   
```

**How to get your API credentials:**

1. Go to [my.telegram.org](https://my.telegram.org) and log in
2. Click **API development tools**
3. Create an app (any name/platform is fine)
4. Copy the `App api_id` and `App api_hash`

---

## 🚀 Usage

```bash
python tg-intersect.py
```

You'll be guided through the steps interactively:

```
  Group 1 (required): -1001234567890
  Group 2 (required): @somegroup
  Group 3 (or leave blank to start):
```

Group IDs can be either a **numeric ID** (e.g. `-1001234567890`) or a **public username** (e.g. `@groupname`).

### Finding a group's numeric ID

The easiest way is to forward any message from the group to [@userinfobot](https://t.me/userinfobot) — it will reply with the chat ID.

---

## 📊 Output

After fetching, you'll see a summary panel and a full results table:

```
╭─────────────────── Summary ───────────────────╮
│                                               │
│  Group Alpha: 4,821 human members fetched     │
│  Group Beta:  2,190 human members fetched     │
│                                               │
│  Common members found: 38                     │
│  Completed in 14.2s                           │
│                                               │
╰───────────────────────────────────────────────╯

         Common Members  31 public  7 private
╭────┬──────────────────────────┬──────────────────────┬───────────────┬─────────╮
│  # │ Name                     │ Handle               │ User ID       │ Type    │
├────┼──────────────────────────┼──────────────────────┼───────────────┼─────────┤
│  1 │ Ahmed                    │ @ahmedh              │ 123456789     │ Public  │
│  2 │ Sara                     │ ID: 987654321        │ 987654321     │ Private │
│ …  │ …                        │ …                    │ …             │ …       │
╰────┴──────────────────────────┴──────────────────────┴───────────────┴─────────╯
```

Then you'll be prompted to export:

```
Export results? [y/n]: y
Format (csv, txt, json) [csv]: json
✓ Saved to common_members_20260218_143022.json
```

---

## 📁 Export Formats

| Format | Contents |
|--------|----------|
| `csv`  | `#`, Full Name, Username, User ID, Type, Profile URL |
| `txt`  | Human-readable numbered list |
| `json` | Full structured data including group metadata |

---

## ⚠️ Notes & Limits

- **Admin rights not required** for public groups; for private groups your account must be a member
- **Large groups (100k+ members)** will take longer due to Telegram's rate limiting — the progress bar will show you live status
- **Session file** (`my_session.session`) is saved locally after first login — keep it private, it grants access to your account
- This tool uses your **personal account**, not a bot — Telegram's Terms of Service apply

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

Built with [kurigram](https://github.com/KurimuzonAkuma/kurigram) and [Rich](https://github.com/Textualize/rich).
