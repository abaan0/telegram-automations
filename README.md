<a id="readme-top"></a>

<div align="center">

# Telegram Automations

**A modular Python Telegram bot for Bitcoin monitoring, free-game discovery, and automated notifications.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Issues](https://img.shields.io/github/issues/abaan0/telegram-automations)](https://github.com/abaan0/telegram-automations/issues)
[![Stars](https://img.shields.io/github/stars/abaan0/telegram-automations)](https://github.com/abaan0/telegram-automations/stargazers)

[Repository](https://github.com/abaan0/telegram-automations) · [Report a bug](https://github.com/abaan0/telegram-automations/issues/new) · [Request a feature](https://github.com/abaan0/telegram-automations/issues/new)

</div>

## Overview

Telegram Automations combines on-demand bot commands with scheduled GitHub Actions checks. The Telegram bot supports polling during local development and webhooks when deployed to Render.

**Main capabilities**

- Check Bitcoin's current USD price and 24-hour change with `/btcprice`.
- Receive Bitcoin alerts when the absolute 24-hour change reaches the configured threshold.
- Discover Epic Games and Steam free-game promotions, on demand or through scheduled notifications.
- Retrieve the daily Wordle answer with `/wordleanswer`.
- Keep a SQLite user registry and allow admins to inspect it with `/users`.
- Extend commands through a decorator-based registry in `commands/`.

A historical-events and Gemini-powered `/today` command is **still present in the repository**, although it is considered legacy and was previously marked for removal. See [Known limitations](#known-limitations).

## Telegram commands

| Command | What it does |
| --- | --- |
| `/btcprice` | Returns Bitcoin's USD price and 24-hour percentage change from CoinGecko. |
| `/epicgames` | Lists Epic Games titles with active free promotions and claim links. |
| `/steamgames` | Lists 100%-discounted Steam games and their claim links. |
| `/wordleanswer` | Returns the current Wordle answer. |
| `/users` | Lists recorded bot users; restricted to `ADMIN_ID`. |
| `/today` (legacy) | Uses historical-event sources and Gemini to select events and draft social-media posts; still registered in the current code. |

## Scheduled alerts

Scheduled checks run independently of the Render web service, using GitHub Actions.

| Workflow | Schedule (UTC) | Behavior |
| --- | --- | --- |
| [BTC Price Alert](.github/workflows/btc-alert.yml) | Every 15 minutes | Alerts if the absolute 24-hour BTC price change reaches **3%** and the 24-hour cooldown has elapsed. |
| [Epic Games Free Alert](.github/workflows/epic-alert.yml) | Daily at 00:00 UTC (05:30 IST) | Checks for changes to the set of currently free Epic Games titles. |
| [Steam Free Game Alert](.github/workflows/steam-alert.yml) | Every 6 hours | Looks for newly detected 100%-discounted Steam games. |

All three workflows also support manual triggering through the **Actions** tab. A manual run sends a test confirmation message and performs the regular check; it does not bypass the BTC cooldown for price alerts.

### Bitcoin alert persistence

The BTC workflow uses `scripts/config.py` for its threshold (`BTC_ALERT_THRESHOLD = 3.0`). Its behavior is:

1. Check the CoinGecko 24-hour percentage change every 15 minutes.
2. Send a price alert only when the threshold has been crossed **and** at least 24 hours have passed since the previous successful price alert.
3. Record the successful alert timestamp in `state/btc_alert_state.json`.
4. Commit the updated state to the repository using GitHub Actions, so the timestamp survives subsequent workflow runs.
5. Use workflow concurrency to avoid overlapping BTC checks.

The timestamp is written after Telegram accepts the alert request. Repository write permission is needed for the automatic state commit. If the commit fails, subsequent checks may not have the latest cooldown state, so review failed workflow runs.

### Free-game alerts and expiry dates

- **Epic Games:** The scheduled script compares the current game titles with `state/epic_alert_state.json`, then sends a notification when the list changes. Its latest code is intended to display the promotion's **expiry date and time in IST**, when Epic provides an end date.
- **Steam:** The workflow checks for new free-to-keep games using Steam app IDs, and includes the original price and game link when available. It saves its state through GitHub Actions cache.

**Important:** The current GitHub repository does not contain the shared `scripts/epic_games.py` module imported by the updated Epic alert script and its tests. Until that module is added, the Epic scheduled workflow will fail. The `/epicgames` bot command still uses the older parser and does not yet show expiry dates. See [Known limitations](#known-limitations).

## Tech stack

- **Python 3.12**, `python-telegram-bot`, `httpx`, `python-dotenv`
- **Starlette and Uvicorn** for webhook mode
- **SQLite and aiosqlite** for user tracking
- **GitHub Actions** for scheduled monitoring
- **Render** for bot hosting
- **CoinGecko, Epic Games Store, and Steam** as external data sources
- **Google Gemini and additional event APIs** for the legacy `/today` feature

## Getting started

### Requirements

- Python 3.12 recommended
- Git
- A Telegram bot created using [@BotFather](https://t.me/BotFather)
- The bot token and your Telegram user ID

### Install on Windows (PowerShell)

```powershell
git clone https://github.com/abaan0/telegram-automations.git
cd telegram-automations
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your own credentials. **For local polling, remove or comment out `RENDER=true` from the copied `.env` file.** The program selects webhook mode whenever `RENDER` has a nonempty value.

Start the bot:

```powershell
python bot.py
```

Do not run polling and the deployed webhook bot with the same token simultaneously, since they can interfere with each other's Telegram update handling.

### Configuration

| Variable | Used for | Notes |
| --- | --- | --- |
| `BOT_TOKEN` | Bot and alerts | Telegram token from BotFather; required. |
| `ADMIN_ID` | Bot | Telegram user ID authorized to run `/users`; required. |
| `RENDER` | Bot | Set to `true` to enable webhook mode; **unset** for local polling. |
| `WEBHOOK_BASE_URL` | Webhook | Public HTTPS base URL, without a trailing slash. |
| `WEBHOOK_SECRET` | Webhook | Set a strong random secret so webhook requests can be checked. |
| `PORT` | Webhook | Defaults to `10000`. |
| `TELEGRAM_CHAT_ID` | BTC alert | Destination chat ID for the price alert. |
| `COINGECKO_API_KEY` | BTC alert | Required by the current `scripts/config.py` for scheduled checks. |
| `EPIC_GAMES_CHAT_IDS` | Epic alert | Comma-separated destination chat IDs. |
| `STEAM_GAMES_CHAT_IDS` | Steam alert | Comma-separated destination chat IDs. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Legacy `/today` | Needed for Gemini-powered event ranking/content. |
| `SPORTSDB_API_KEY`, `TMDB_API_TOKEN`, `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET`, `TIMEZONE` | Legacy `/today` | Optional event-source and timezone settings. |

Use [.env.example](.env.example) as a starting point. Never commit `.env`, access tokens, API keys, or service-account credentials.

## Deployment

### Render: Telegram bot

The repository includes [`render.yaml`](render.yaml) for a free-plan web service.

1. Connect the repository to Render and create a web service using `render.yaml`.
2. Configure `BOT_TOKEN`, `ADMIN_ID`, `RENDER=true`, `WEBHOOK_BASE_URL`, and `WEBHOOK_SECRET` in the Render environment. Set any other keys required by the commands you use.
3. Deploy and verify that `https://YOUR-SERVICE.onrender.com/health` returns `OK`.
4. Use a **secret** webhook token and treat the bot token as private. The current implementation includes the bot token in its webhook URL and startup logging, so limit log access.

The `/health` route supports monitoring. External monitors such as cron-job.org can periodically check it, but uptime on a free hosting plan is not guaranteed.

### GitHub Actions: scheduled alerts

1. Open **Repository → Settings → Secrets and variables → Actions**.
2. Add the appropriate repository secrets: `BOT_TOKEN`, `COINGECKO_API_KEY`, `TELEGRAM_CHAT_ID`, `EPIC_GAMES_CHAT_IDS`, and `STEAM_GAMES_CHAT_IDS`.
3. Open **Settings → Actions → General → Workflow permissions** and enable **Read and write permissions** (subject to repository policy). The BTC and Epic workflows need `contents: write` to commit updated state.
4. Open **Actions** and manually run a workflow to check its output. A manual run sends a test confirmation to the configured recipient(s).

Schedules use **UTC**, and GitHub Actions may start scheduled runs later than the nominal cron time.

## Project structure

```text
telegram-automations/
├── .github/workflows/
│   ├── btc-alert.yml          # BTC checks and Git state commits
│   ├── epic-alert.yml         # Epic Games scheduled checks
│   └── steam-alert.yml        # Steam scheduled checks
├── commands/
│   ├── __init__.py            # Command registration and discovery
│   ├── btcprice.py
│   ├── epicgames.py
│   ├── steamgames.py
│   ├── today.py               # Legacy command, still present
│   ├── users.py
│   └── wordleanswer.py
├── scripts/
│   ├── btc_alert.py
│   ├── config.py              # BTC threshold and shared settings
│   ├── epic_alert.py
│   └── steam_alert.py
├── services/                  # AI, historical events and Sheets helpers
├── state/
│   ├── btc_alert_state.json
│   ├── epic_alert_state.json
│   └── steam_alert_state.json
├── tests/
│   └── test_epic_games.py
├── bot.py                      # Polling / webhook entry point
├── notify.py
├── users.py                   # SQLite user tracking
├── users.db
├── .env.example
├── render.yaml
├── requirements.txt
└── README.md
```

The expected shared file `scripts/epic_games.py` is **missing from the current GitHub tree**. It is required for the intended Epic expiry feature.

## Testing

Run the existing unit tests from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The Epic expiry tests will not import successfully until `scripts/epic_games.py` is added. No live Telegram messages should be sent by these unit tests.

## Known limitations

- **Epic expiry feature is not fully integrated:** `scripts/epic_alert.py` and `tests/test_epic_games.py` import a missing `scripts/epic_games.py` helper. The current `/epicgames` command still shows links without expiry times.
- **Legacy `/today` code remains:** Both `commands/today.py` and its callback registration in `bot.py` still exist. Remove both when retiring that feature.
- **Steam alert state uses Actions cache:** Unlike BTC state, it is not committed to the repository and can be lost or restored inconsistently.
- **BTC state commits depend on Actions permissions:** A failed push can leave the stored cooldown timestamp out of date.
- **Webhook security can be strengthened:** `WEBHOOK_SECRET` is optional in the current code, and the bot token is included in the webhook path and startup log. Configure the secret and restrict access to logs.

## Roadmap

- [x] Telegram commands for BTC, Epic Games, Steam and Wordle
- [x] Scheduled BTC monitoring with a 24-hour alert cooldown
- [x] BTC state commits and non-overlapping BTC workflow runs
- [x] Scheduled Epic Games and Steam checks
- [x] SQLite-backed user tracking with an admin command
- [x] Render webhook deployment and `/health` endpoint
- [x] Initial unit tests for Epic promotion parsing (currently blocked by a missing module)
- [ ] Restore the Epic expiry helper and use it in both the workflow and `/epicgames`
- [ ] Remove the deprecated `/today` feature if no longer wanted
- [ ] Make Steam state persistence more reliable
- [ ] Add integration tests and improve workflow error handling
- [ ] Add optional per-user notification preferences

## Contributing

Suggestions and pull requests are welcome. Open an [issue](https://github.com/abaan0/telegram-automations/issues) for bugs or ideas. For a code contribution, create a feature branch, make changes, test them, then open a pull request against `main`.

## License

No license file is currently present in this repository. A license must be added before claiming that the project is MIT-licensed or otherwise openly licensed for reuse.

## Links

- [GitHub repository](https://github.com/abaan0/telegram-automations)
- [Issue tracker](https://github.com/abaan0/telegram-automations/issues)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [CoinGecko](https://www.coingecko.com/)
- [Epic Games Store](https://store.epicgames.com/en-US/free-games)
- [Steam](https://store.steampowered.com/)

<p align="right">(<a href="#readme-top">Back to top</a>)</p>
