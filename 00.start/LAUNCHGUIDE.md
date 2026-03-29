# Paid Telegram Bot

## Tagline
Enterprise Telegram bot management for any AI agent — users, payments, analytics, and more.

## Description
Paid Telegram Bot is a production-grade MCP server that gives any AI agent full enterprise Telegram bot management capabilities. Unlike basic Telegram MCP servers that only send and receive messages, this server includes a built-in SQLite database, token bucket rate limiting, priority message queue, Stripe + Telegram Stars payment processing, multi-user subscription management, deep link onboarding, analytics dashboards, and security event logging — all accessible through 40+ MCP tools.

**How it works**: The server runs as a persistent local process alongside your MCP client. It manages a Telegram bot via long-polling, stores user data and payment records in a local SQLite database, enforces rate limits against Telegram's API caps, and exposes everything as MCP tools your AI agent can call.

**Who it's for**: Developers, indie hackers, agencies, and businesses who want their AI agent (Claude, Cursor, Windsurf, Claude Code, or any MCP-compatible client) to manage a Telegram bot with enterprise features — from personal assistants to monetized SaaS bots serving thousands of users.

**Free tier** includes 12 basic tools for personal bot setup and messaging. **Pro tier** (license required) unlocks 40+ tools including user management, subscription plans, payment processing, analytics, deep links, group mode, event subscriptions, and chat history search.

## Setup Requirements
- `TELEGRAM_BOT_TOKEN` (required): Your Telegram bot token from @BotFather. Open Telegram, message @BotFather, send /newbot, and follow the prompts. https://core.telegram.org/bots#botfather
- `MCP_LICENSE_KEY` (optional): License key for Pro features. Free tier works without a key. Purchase at https://mcp-marketplace.io/servers/paid-telegram-bot
- `STRIPE_PROVIDER_TOKEN` (optional): Stripe payment provider token for accepting fiat payments from your bot's users. Get it from @BotFather → Payments → Stripe. https://stripe.com

## Category
Communication

## Use Cases
Telegram Bot Management, AI-Powered Customer Support, SaaS Bot Monetization, Team Communication, Group Chat Automation, Telegram Channel Management, Payment Processing, User Onboarding, Community Management, Bot Analytics, Multi-User Bot Deployment, Deep Link Marketing, Subscription Management, Broadcast Messaging, File Delivery Automation

## Features
- 40+ MCP tools for complete Telegram bot lifecycle management
- Built-in SQLite database for persistent user, payment, and analytics data
- Multi-user bot with role-based access (owner, subscriber, free, blocked)
- Three access control modes: Whitelist, Open, and Approval
- Subscription plans with customizable pricing and message limits (Free/Basic/Pro/Enterprise)
- Dual payment support: Stripe (fiat currency) and Telegram Stars
- Credit purchase system for pay-per-use models
- Token bucket rate limiter respecting Telegram's 30 msg/s API limit
- Priority message queue (high/normal/low) with retry and 429 backoff
- AI request concurrency queue with user position notifications
- Deep link onboarding: plan links, invite codes with expiry/revocation, referral tracking
- Smart file delivery with auto-routing (photos, videos, audio, documents)
- Batch file delivery with automatic ZIP compression
- Analytics dashboard: total/active/paying users, revenue, messages by day
- Security event logging with severity levels and query filters
- Owner notifications for new users, suspicious activity, and security events
- Broadcast messaging to all bot users
- Group mode with mention/command activation and per-user limits
- Typing indicator and emoji reaction lifecycle (received → thinking → working → done)
- Subscription lifecycle management: expiry warnings, auto-downgrade, renewal reminders
- Inactive user detection and auto-suspension
- Chat history search with keyword and date filters
- Event subscription system: subscribe to new messages, new users, keyword matches
- MCP Resources for read-only access to bot status, users, plans, and analytics
- MCP Prompts for guided setup flows (personal bot, team bot, SaaS bot)
- Freemium model: 12 free tools for personal use, Pro license unlocks everything
- Works with Claude Desktop, Cursor, Windsurf, Claude Code, and any MCP-compatible agent

## Getting Started
- "Set up a personal Telegram bot for me" — The agent uses the setup-personal-bot prompt to guide you through BotFather setup, token configuration, and bot launch
- "Start my Telegram bot and show me its status" — Uses bot_start and bot_status tools
- "Send 'Hello World' to chat 123456" — Uses send_message tool
- "List all my bot users and show analytics" — Uses user_list and analytics_dashboard tools (Pro)
- "Create a Pro plan at $20/month with 2000 messages" — Uses plan_create tool (Pro)
- "Generate an invite link for 50 users on the Basic plan" — Uses deeplink_create_invite tool (Pro)
- "Show me revenue for this month" — Uses payment_get_revenue tool (Pro)
- "Broadcast a message to all users about the new feature" — Uses broadcast_message tool (Pro)
- Tool: bot_configure — Set bot token and basic settings
- Tool: bot_start — Start the Telegram bot with long-polling
- Tool: send_message — Send a text message to any chat
- Tool: user_list — List all bot users with filters (Pro)
- Tool: plan_create — Create subscription plans with pricing (Pro)
- Tool: payment_send_invoice — Send Stripe or Stars payment invoice (Pro)
- Tool: analytics_dashboard — Full analytics with users, revenue, trends (Pro)
- Tool: deeplink_create_invite — Generate invite links with expiry and limits (Pro)

## Tags
telegram, bot, mcp, ai-agent, enterprise, payments, stripe, telegram-stars, subscriptions, user-management, analytics, rate-limiting, message-queue, deep-links, onboarding, saas, monetization, group-chat, file-delivery, security, broadcasting, bot-management, communication, automation, multi-user, freemium

## Documentation URL
https://github.com/netflypsb/paid-telegram-bot-mcp#readme

## Health Check URL
N/A (local stdio server)
