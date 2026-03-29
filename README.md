# Paid Telegram Bot MCP Server

**Enterprise Telegram bot management for any AI agent** — users, payments, analytics, and 40+ tools.

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![MCP Marketplace](https://img.shields.io/badge/MCP_Marketplace-Listed-purple)](https://mcp-marketplace.io/servers/paid-telegram-bot)

Unlike basic Telegram MCP servers that only send and receive messages, this server provides **production-grade infrastructure**: built-in SQLite database, token bucket rate limiting, priority message queue, Stripe + Telegram Stars payments, multi-user subscription management, deep link onboarding, analytics dashboards, and security event logging — all accessible through 40+ MCP tools.

## Quick Start

### 1. Install

```bash
pip install paid-telegram-bot
```

### 2. Get a Telegram Bot Token

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the token you receive

### 3. Add to Your MCP Client

**Claude Desktop / Cursor / Windsurf** — add to your MCP config:

```json
{
  "mcpServers": {
    "paid-telegram-bot": {
      "command": "paid-telegram-bot",
      "env": {
        "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN_HERE"
      }
    }
  }
}
```

**With Pro license** (unlocks all 40+ tools):

```json
{
  "mcpServers": {
    "paid-telegram-bot": {
      "command": "paid-telegram-bot",
      "env": {
        "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
        "MCP_LICENSE_KEY": "mcp_live_YOUR_KEY_HERE",
        "STRIPE_PROVIDER_TOKEN": "YOUR_STRIPE_TOKEN"
      }
    }
  }
}
```

### 4. Start Using

Tell your AI agent:

> "Set up my Telegram bot and send a test message"

The agent will use the `setup-personal-bot` prompt to guide you through the process.

## Features

### Free Tier (12 tools, no license required)

| Tool | Description |
|------|-------------|
| `bot_configure` | Set bot token and basic settings |
| `bot_start` | Start the Telegram bot (long-polling) |
| `bot_stop` | Stop the bot |
| `bot_status` | Get bot running status, username, uptime |
| `send_message` | Send a text message to a chat |
| `send_photo` | Send a photo to a chat |
| `send_document` | Send a file/document to a chat |
| `get_updates` | Get recent incoming messages |
| `get_chat_info` | Get info about a chat/group |
| `set_commands` | Register bot commands with Telegram |
| `reply_to_message` | Reply to a specific message |
| `get_me` | Get bot info (username, name, etc.) |

**Free tier limits**: 1 bot, 50 outbound messages/hour, no multi-user management.

### Pro Tier (40+ tools, license required)

#### User & Access Management
`user_list` · `user_get` · `user_block` · `user_unblock` · `user_update_tier` · `access_set_mode` · `access_add_user` · `access_remove_user`

#### Subscription Plans
`plan_list` · `plan_create` · `plan_update` · `plan_delete`

#### Payments (Stripe + Telegram Stars)
`payment_send_invoice` · `payment_list` · `payment_get_revenue`

#### Analytics & Admin
`analytics_dashboard` · `analytics_usage` · `broadcast_message` · `security_log` · `security_get_events`

#### Deep Links & Onboarding
`deeplink_create_invite` · `deeplink_create_plan_link` · `deeplink_revoke_invite` · `deeplink_list_invites`

#### Message Infrastructure
`queue_status` · `queue_set_priority` · `send_inline_keyboard` · `send_poll` · `get_poll_results`

#### File & Media
`file_send` (smart media routing) · `file_download` · `file_list_received`

#### Group Mode
`group_configure` · `group_list`

#### Event Subscriptions & History
`subscribe_events` · `get_event_queue` · `history_search` · `history_export`

### MCP Resources

| Resource | Description | Tier |
|----------|-------------|------|
| `telegram://bot/status` | Bot status and config | Free |
| `telegram://messages/recent` | Last 50 messages | Free |
| `telegram://users` | All bot users | Pro |
| `telegram://plans` | Subscription plans | Pro |
| `telegram://analytics` | Analytics dashboard | Pro |
| `telegram://security/events` | Security events | Pro |
| `telegram://invites` | Active invite codes | Pro |

### MCP Prompts

| Prompt | Description | Tier |
|--------|-------------|------|
| `setup-personal-bot` | Guide through personal bot setup | Free |
| `setup-team-bot` | Team bot with invites and access control | Pro |
| `setup-saas-bot` | Monetized bot with plans and payments | Pro |
| `analyze-bot-health` | Analyze analytics, suggest improvements | Pro |
| `troubleshoot-bot` | Diagnose common issues | Free |
| `create-onboarding-flow` | Design a deep link onboarding funnel | Pro |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `MCP_LICENSE_KEY` | No | Pro license key from [MCP Marketplace](https://mcp-marketplace.io/servers/paid-telegram-bot) |
| `STRIPE_PROVIDER_TOKEN` | No | Stripe token for fiat payments (from @BotFather → Payments) |
| `TELEGRAM_OWNER_CHAT_ID` | No | Your Telegram user ID for owner notifications |
| `PAID_TELEGRAM_BOT_DATA_DIR` | No | Custom data directory (default: `~/.paid-telegram-bot`) |

## Architecture

The server runs as a **persistent local process** alongside your MCP client:

- **Database**: SQLite stored at `~/.paid-telegram-bot/data.db`
- **Bot**: `python-telegram-bot` long-polling in a background asyncio task
- **Rate limiter**: Token bucket (30 msg/s Telegram cap, per-chat spacing)
- **Message queue**: Priority-based (high/normal/low) with stale message cleanup
- **Files**: Stored at `~/.paid-telegram-bot/files/`
- **Config**: JSON at `~/.paid-telegram-bot/config.json` + environment variables

## Pricing

| Plan | Price | What You Get |
|------|-------|-------------|
| **Free** | $0 | 12 basic tools, 1 bot, 50 msg/hr |
| **Personal** | $9/month | All 40+ tools, 1 bot, unlimited messages |
| **Team** | $29/month | All tools, 3 bots, priority support |
| **Enterprise** | $79/month | Unlimited bots, SSE daemon mode, webhook support |

[Get a license →](https://mcp-marketplace.io/servers/paid-telegram-bot)

## Development

```bash
# Clone the repository
git clone https://github.com/netflypsb/paid-telegram-bot-mcp.git
cd paid-telegram-bot-mcp

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install in development mode
pip install -e .

# Run the server
paid-telegram-bot
# or
python -m paid_telegram_bot
```

## Compatibility

Works with any MCP-compatible AI client:

- Claude Desktop
- Cursor
- Windsurf
- Claude Code
- OpenClaw
- Any custom MCP client

## License

[MIT](LICENSE) — the server code is open source. Pro features require a license key from MCP Marketplace.

## Links

- [MCP Marketplace listing](https://mcp-marketplace.io/servers/paid-telegram-bot)
- [GitHub repository](https://github.com/netflypsb/paid-telegram-bot-mcp)
- [Changelog](CHANGELOG.md)
- [MCP Protocol](https://modelcontextprotocol.io)
