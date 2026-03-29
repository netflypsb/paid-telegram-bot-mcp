# Changelog

All notable changes to the Paid Telegram Bot MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-29

### Added
- Initial release with 40+ MCP tools
- **Free tier** (12 tools, no license required):
  - `bot_configure`, `bot_start`, `bot_stop`, `bot_status`
  - `send_message`, `send_photo`, `send_document`, `reply_to_message`
  - `get_updates`, `get_chat_info`, `get_me`, `set_commands`
  - Free tier rate limit: 50 outbound messages/hour
- **Pro tier** (license required):
  - User management: `user_list`, `user_get`, `user_block`, `user_unblock`, `user_update_tier`
  - Access control: `access_set_mode`, `access_add_user`, `access_remove_user`
  - Plan management: `plan_list`, `plan_create`, `plan_update`, `plan_delete`
  - Payments: `payment_send_invoice` (Stripe + Stars), `payment_list`, `payment_get_revenue`
  - Analytics: `analytics_dashboard`, `analytics_usage`
  - Admin: `broadcast_message`, `security_log`, `security_get_events`
  - Deep links: `deeplink_create_invite`, `deeplink_create_plan_link`, `deeplink_revoke_invite`, `deeplink_list_invites`
  - Message infra: `queue_status`, `queue_set_priority`, `send_inline_keyboard`, `send_poll`, `get_poll_results`
  - File/media: `file_send` (smart routing), `file_download`, `file_list_received`
  - Group mode: `group_configure`, `group_list`
  - Events: `subscribe_events`, `get_event_queue`, `history_search`, `history_export`
- **MCP Resources**: `telegram://bot/status`, `telegram://messages/recent`, `telegram://users`, `telegram://plans`, `telegram://analytics`, `telegram://security/events`, `telegram://invites`
- **MCP Prompts**: `setup-personal-bot`, `setup-team-bot`, `setup-saas-bot`, `analyze-bot-health`, `troubleshoot-bot`, `create-onboarding-flow`
- SQLite database with full schema (users, plans, payments, usage logs, security events, invite codes, messages with FTS5)
- Token bucket rate limiter
- Priority message queue (high/normal/low)
- AI request concurrency queue
- Typing indicator and emoji reaction lifecycle
- License key verification via `mcp-marketplace-license` SDK
- Freemium model: free tools work without a key, Pro tools require `MCP_LICENSE_KEY`
