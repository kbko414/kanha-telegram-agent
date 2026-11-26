# Kanha Telegram Agent

A single-owner Telegram agent bot with shell, file, and web tools, powered by the
[FreeModel.in](https://freemodel.in) API. Send it a message, it thinks, uses
tools when needed, and answers. One command sets it up on Ubuntu.

> **Owner-only.** The bot answers a single Telegram user ID and ignores
> everyone else. It can run shell commands on the host, so never point it at
> a shared server or share its token.

## Quick install (Ubuntu 24.04 / 26.04)

```bash
curl -fsSL https://raw.githubusercontent.com/kbko414/kanha-telegram-agent/main/setup_tgagent.sh | sudo bash
```

The installer will:

1. Install Python 3, venv, pip, curl
2. Create the app in `/opt/tgagent` (`memory/`, `work/`)
3. Create a Python venv and install dependencies
4. Ask for your Telegram bot token, FreeModel.in API key, your Telegram user
   ID, and the model ID — then write `/opt/tgagent/.env` (mode `600`)
5. Create a non-root `tgagent` system user and a systemd service
6. Start the service and verify it stays up

Then open Telegram and send `/start` to your bot.

## What you need before installing

| Item | Where to get it |
| --- | --- |
| Telegram bot token | [@BotFather](https://t.me/BotFather) → `/newbot` |
| FreeModel.in API key | [freemodel.in](https://freemodel.in) dashboard (starts with `fm_`) |
| Your Telegram user ID | [@userinfobot](https://t.me/userinfobot) on Telegram |
| Model ID | Default `gpt-6-luna`; any model your FreeModel key can use |

## Commands

| Command | What it does |
| --- | --- |
| `/start` | Show status (model, backend) and reset memory |
| `/reset` | Wipe conversation memory |
| `/memory` | Show the last few exchanges |
| `/temp <n>` | Get / set sampling temperature (default `0.8`) |
| `/ping` | Liveness check |

Any other text message is handled by the agent. It can run shell commands,
read and write files under `work/`, list directories, and fetch URLs.

## Manual install

```bash
git clone https://github.com/kbko414/kanha-telegram-agent.git
cd kanha-telegram-agent
cp .env.example .env   # then fill in TG_TOKEN, API_KEY, OWNER_ID
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python bot.py
```

## Configuration

All settings live in `.env` (see `.env.example`):

| Variable | Default | Meaning |
| --- | --- | --- |
| `TG_TOKEN` | — | Telegram bot token (required) |
| `API_BASE` | `https://freemodel.in/v1` | OpenAI-compatible API base URL |
| `API_KEY` | — | FreeModel.in API key (required) |
| `MODEL` | `gpt-6-luna` | Model ID |
| `OWNER_ID` | `0` | Your Telegram user ID (required, must be numeric) |

Tuning constants in `config.py`: `HISTORY_LIMIT = 40` messages kept per
chat, `MAX_TOOL_ROUNDS = 8` tool calls per reply, `SHELL_TIMEOUT = 60` s.

## Managing the service

```bash
sudo systemctl status tgagent      # status
sudo journalctl -u tgagent -f      # live logs
sudo systemctl restart tgagent     # restart
sudo nano /opt/tgagent/.env        # edit config, then restart
```

## Project structure

```
setup_tgagent.sh   # one-command installer (writes everything below to /opt/tgagent)
bot.py             # Telegram bot: owner guard, commands, message loop
agent.py           # FreeModel.in chat loop with tool calling
tools.py           # shell, read_file, write_file, list_dir, web_fetch
config.py          # env loading, paths, limits, system prompt
requirements.txt   # python-telegram-bot, aiohttp, python-dotenv, requests
.env.example       # config template (copy to .env, never commit a real one)
systemd/
  tgagent.service  # systemd unit used by the installer
memory/            # per-chat history JSON (gitignored)
work/              # agent working directory for files it reads/writes
```

## Security notes

- The bot only replies to `OWNER_ID`. Everyone else gets `not authorized.`
- The agent's shell tool runs as the `tgagent` system user (no login shell),
  with its working directory confined to `work/`.
- `.env` holds secrets — it is created with mode `600` and is gitignored.
- The installer reads tokens with hidden input so they don't show on screen.
- Keep the bot token and API key private. If either leaks, revoke it and
  update `/opt/tgagent/.env`.

## License

MIT — see [LICENSE](LICENSE).
