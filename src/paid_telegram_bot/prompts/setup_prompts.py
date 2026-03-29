"""MCP Prompts — pre-built prompt templates that guide AI agents through setup flows."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts on the server."""

    @mcp.prompt()
    async def setup_personal_bot() -> str:
        """Guide the user through setting up a personal Telegram bot (Free tier).

        Walk them through: BotFather setup → get token → bot_configure → bot_start → send a test message.
        """
        return (
            "Help the user set up a personal Telegram bot step by step:\n\n"
            "1. **Create a bot with BotFather**: Ask the user to open Telegram, "
            "search for @BotFather, and send /newbot. They'll choose a name and username, "
            "then receive a bot token.\n\n"
            "2. **Configure the bot**: Once they have the token, call the `bot_configure` tool "
            "with their token. Optionally set a custom welcome_message.\n\n"
            "3. **Start the bot**: Call `bot_start` to begin receiving messages.\n\n"
            "4. **Verify it works**: Call `bot_status` to confirm the bot is running, "
            "then ask the user to send a message to their bot in Telegram.\n\n"
            "5. **Check messages**: Call `get_updates` to see the message they sent.\n\n"
            "6. **Send a reply**: Use `send_message` to send a response back to them.\n\n"
            "7. **Set commands**: Optionally use `set_commands` to register commands "
            "like /start and /help in the bot menu.\n\n"
            "The bot is now running and will continue to receive messages in the background. "
            "The user can interact with it through Telegram while you manage it through MCP tools."
        )

    @mcp.prompt()
    async def setup_team_bot() -> str:
        """Guide through setting up a team bot with invites and access control (Pro tier)."""
        return (
            "Help the user set up a team Telegram bot with access control (requires Pro license):\n\n"
            "1. **Basic setup**: Follow the personal bot setup first (bot_configure, bot_start).\n\n"
            "2. **Set access mode**: Call `access_set_mode` with mode='whitelist' or 'approval' "
            "to restrict who can use the bot.\n\n"
            "3. **Create invite links**: Use `deeplink_create_invite` to generate invite links "
            "for team members. Set max_uses and expires_in_days as needed.\n\n"
            "4. **Manage users**: As team members join, use `user_list` to see them. "
            "Use `user_update_tier` to assign roles/plans.\n\n"
            "5. **Set up plans**: Create team-specific plans with `plan_create` that define "
            "message limits per billing period.\n\n"
            "6. **Monitor**: Use `analytics_dashboard` to track usage and `security_log` "
            "for security events.\n\n"
            "7. **Authorize manually**: If needed, use `access_add_user` to manually "
            "authorize specific Telegram users."
        )

    @mcp.prompt()
    async def setup_saas_bot() -> str:
        """Guide through setting up a monetized SaaS bot with payments (Pro tier)."""
        return (
            "Help the user set up a monetized Telegram bot with subscription plans and payments "
            "(requires Pro license):\n\n"
            "1. **Basic setup**: Configure and start the bot (bot_configure, bot_start).\n\n"
            "2. **Create subscription plans**: Use `plan_create` for each tier:\n"
            "   - Free plan (default exists): 0 cost, limited messages\n"
            "   - Basic: e.g. 500 cents ($5), 1000 messages/month\n"
            "   - Pro: e.g. 2000 cents ($20), 5000 messages/month\n"
            "   - Enterprise: e.g. 5000 cents ($50), unlimited\n\n"
            "3. **Configure payments**: Ensure STRIPE_PROVIDER_TOKEN is set for fiat, "
            "or use Telegram Stars for in-app currency.\n\n"
            "4. **Create deep links**: Use `deeplink_create_plan_link` for each plan "
            "to create purchase links. Share these in your marketing.\n\n"
            "5. **Set access mode**: Call `access_set_mode` with mode='open' for public bots.\n\n"
            "6. **Create invite codes**: Use `deeplink_create_invite` with plan assignments "
            "for promotional campaigns.\n\n"
            "7. **Send invoices**: Use `payment_send_invoice` to bill users directly.\n\n"
            "8. **Monitor performance**: Use `analytics_dashboard` for user metrics, "
            "`payment_get_revenue` for financial data.\n\n"
            "9. **Broadcast updates**: Use `broadcast_message` to announce new features.\n\n"
            "10. **Security**: Check `security_log` regularly for suspicious activity."
        )

    @mcp.prompt()
    async def analyze_bot_health() -> str:
        """Analyze bot analytics and suggest improvements (Pro tier)."""
        return (
            "Analyze the health and performance of the user's Telegram bot:\n\n"
            "1. Call `analytics_dashboard` to get the current metrics.\n\n"
            "2. Call `user_list` to review the user base.\n\n"
            "3. Call `payment_get_revenue` for both 'monthly' and 'all_time'.\n\n"
            "4. Call `security_log` to check for any issues.\n\n"
            "5. Call `queue_status` to check infrastructure health.\n\n"
            "Based on the data, provide analysis on:\n"
            "- **User growth**: Is the user base growing? What's the free-to-paid conversion rate?\n"
            "- **Revenue trends**: Is monthly revenue increasing? Average revenue per user?\n"
            "- **Engagement**: Are users active? Identify inactive users.\n"
            "- **Security**: Any concerning events? Blocked users? Rate limit hits?\n"
            "- **Recommendations**: Specific actions to improve metrics."
        )

    @mcp.prompt()
    async def troubleshoot_bot() -> str:
        """Diagnose and fix common bot issues (Free tier)."""
        return (
            "Help diagnose and fix common Telegram bot issues:\n\n"
            "1. **Check status**: Call `bot_status` to see if the bot is running.\n\n"
            "2. **If not running**: Try `bot_start`. If it fails, check the error message.\n"
            "   - 'Invalid token': The TELEGRAM_BOT_TOKEN is wrong. Re-configure with `bot_configure`.\n"
            "   - 'Conflict': Another instance is running. Stop it first or check for duplicate processes.\n\n"
            "3. **Bot running but not receiving messages**:\n"
            "   - Check `get_updates` — if empty, the user might be messaging the wrong bot.\n"
            "   - Verify the bot username matches what they're messaging.\n"
            "   - If in a group, check if group mode is enabled.\n\n"
            "4. **Messages not sending**:\n"
            "   - Check the chat_id is correct.\n"
            "   - The bot must have been started by the user first (/start in DM).\n"
            "   - Check rate limits — free tier is 50 messages/hour.\n\n"
            "5. **Payment issues** (Pro):\n"
            "   - Verify STRIPE_PROVIDER_TOKEN is set correctly.\n"
            "   - Check `payment_list` for failed payments.\n"
            "   - Try sending a test invoice with Stars first.\n\n"
            "6. **General**: Call `get_me` to verify bot capabilities."
        )

    @mcp.prompt()
    async def create_onboarding_flow() -> str:
        """Design a deep link onboarding funnel for the bot (Pro tier)."""
        return (
            "Help design a deep link onboarding funnel for the user's Telegram bot:\n\n"
            "1. **Understand the goal**: Ask the user what they want to achieve:\n"
            "   - Invite team members to a private bot?\n"
            "   - Run a promotional campaign with limited invites?\n"
            "   - Create plan-specific landing links?\n\n"
            "2. **Create the funnel**:\n"
            "   - Use `deeplink_create_plan_link` for each plan to create direct purchase links.\n"
            "   - Use `deeplink_create_invite` with appropriate max_uses and expiry.\n"
            "   - Consider creating different invite codes for different channels "
            "(social media, email, referrals).\n\n"
            "3. **Configure access**: Set `access_set_mode` to match the funnel:\n"
            "   - 'open' for public campaigns\n"
            "   - 'approval' if you want to review users first\n\n"
            "4. **Present the links**: Give the user all generated links with instructions:\n"
            "   - Which link to share where\n"
            "   - How to track which invites are performing best\n\n"
            "5. **Monitor**: Show them how to use `deeplink_list_invites` and "
            "`analytics_dashboard` to track the funnel's performance."
        )
