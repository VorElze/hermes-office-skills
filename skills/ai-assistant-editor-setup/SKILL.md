---
name: ai-assistant-editor-setup
description: 'Use when setting up an AI assistant extension in VS Code.'
version: 1.0.0
author: codi
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [editor, vscode, cline, ai-assistant, setup]
---

# AI assistant setup in a desktop editor

## When to Use

User asks to install, enable, or configure an AI coding assistant inside
VS Code or a derivative (Cursor, Windsurf, VSCodium) — first-time provider
setup (e.g. Cline), or "it doesn't open / doesn't respond".

## Procedure

1. Open the assistant from ITS OWN activity-bar icon (or its command in the
   Command Palette). Never start from the editor's built-in Chat panel —
   that is a *different* assistant and will answer setup instructions
   confidently while the target one stays unconfigured.
2. Gear icon in the assistant's panel → API Provider. Choose managed
   account/subscription, or BYOK when the user already has a proxy or API
   key (usually cheapest for a user who pays for a proxy).
3. BYOK endpoint styles:
   - Anthropic-style proxy: provider `Anthropic`, Base URL = the proxy
     endpoint, paste key.
   - OpenAI-style: provider `OpenAI Compatible`, Base URL ends in `/v1`
     with NO trailing slash, paste key, type the exact Model ID (custom
     endpoints do not auto-populate model lists).
4. Fill the collapsible **Model Configuration**: context window, max output
   tokens, price (display only), and **tool/computer-use mode ON** — with it
   off the assistant is chat-only and file/terminal actions silently no-op.
5. Verify → send a trivial test message and confirm it can read a workspace
   file before declaring the setup done.

## Pitfalls

- **Two variants of the same assistant installed** (stable + nightly/preview)
  split its commands: palette entries return "No matching results". Keep one
  variant (prefer the stable marketplace build), uninstall the other, fully
  restart the editor (File → Exit, not reload window).
- **The activity bar can be moved or hidden** — the tell is explorer icons
  on the RIGHT edge of the window. There is no "Show Activity Bar" command
  (searching it returns "No matching results" and looks like the feature is
  gone); use `View: Move Activity Bar to Side`, then right-click the bar and
  re-enable the assistant's icon.
- **UI field names move between versions** — check the vendor docs (Cline:
  docs.cline.bot) for current labels instead of asserting them from memory.