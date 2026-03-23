# Discord Server Setup Guide

## Goal

Set up a welcoming and sustainable Discord community for NeuroBridge contributors and users.

## 1) Create the Server

1. Open Discord and click Add a Server.
2. Choose Create My Own.
3. Name it: NeuroBridge Community.
4. Upload project icon and add a short description.

## 2) Create Channels

Create these channels in order:

- #announcements (read-only)
- #introductions
- #general
- #dev-chat
- #profile-research
- #show-and-tell
- #bugs
- #ideas

Recommended categories:

- Start Here: #announcements, #introductions
- Community: #general, #show-and-tell
- Build: #dev-chat, #profile-research, #bugs, #ideas

## 3) Configure #announcements as Read-only

1. Open channel settings for #announcements.
2. For @everyone, disable Send Messages.
3. For Core Team role, enable Send Messages.
4. Keep Reply in Threads enabled for contributors if desired.

## 4) Create Roles

Create these roles:

- @Core-Team
- @Profile-Researcher
- @Contributor

Permissions guidance:

- @Core-Team: moderation + announcements + webhook management.
- @Profile-Researcher: elevated posting in #profile-research.
- @Contributor: standard community permissions after first merged PR.

## 5) Auto-Welcome Message

Use a bot (e.g., Carl-bot or MEE6) to post this when users join:

"Welcome to NeuroBridge Community. Start in #introductions, read #announcements, and check CONTRIBUTING.md to get your first issue."

Include links:

- GitHub repo
- CONTRIBUTING.md
- Good first issues label
- SECURITY.md reporting path

## 6) Connect GitHub to Discord

1. In Discord channel #announcements, use Server Integrations to add GitHub app.
2. Subscribe to:
   - New releases
   - New issues
3. Filter noise by repository and event type.
4. Test by creating a draft issue and confirming message delivery.

## 7) Moderation and Safety Defaults

- Enable AutoMod for slurs, threats, and spam links.
- Require verified email for posting.
- Enable slow mode for #announcements replies during launch windows.
- Pin community conduct links in #announcements and #general.

## 8) Launch Checklist

- Channel order and permissions verified
- Role colors and hierarchy verified
- Welcome bot tested
- GitHub integration tested
- Moderation settings enabled
