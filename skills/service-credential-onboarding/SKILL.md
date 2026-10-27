---
name: service-credential-onboarding
description: "Use when saving credentials to log into a website."
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [vault, credentials, browser, cron, automation, login]
---

# Service credential onboarding

## When to Use

Use when the user hands over credentials (or offers them) for an external
website the agent must reach: scheduled report pulls, logins for a dashboard,
"saya berikan username dan password adminnya", or wiring a site into cron jobs.
Goal: the credential lives encrypted in the vault, bound to its exact origin,
and the agent never sees or repeats its value.

## Procedure

1. **Never accept a password in chat.** The only intake is a masked prompt
   (`browser_vault_save_login`), `hermes vault add`, or the Desktop
   Settings → Passwords & Logins UI. If the user pastes a password anyway,
   ask them to change it at the source, and never echo it back.
2. **Store per PROFILE, not globally.** The vault is scoped to a profile
   (`$HERMES_HOME/vault/`), and jobs run under a specific profile. When adding
   from a terminal, always pass the profile flag:
   `hermes -p <profile> vault add` — a bare `hermes vault add` writes the
   ACTIVE profile's vault and the consumer profile will then report
   `Vault is empty`. If a login lands in the wrong profile, move it by copying
   both `vault.json.enc` and `vault.key` (chmod 600) to the target profile's
   `vault/` dir — the key travels with the ciphertext, both stay encrypted.
3. **Prompt fields (order observed):** `Kind (login/payment/address) [login]` →
   Enter; `Label`; `Site origin` (exact URL, e.g.
   `https://host.example/path`); `Identifier type [email]` → **must be a valid
   enum** (`email` / `phone` / `username`) — typing an identifier value here
   makes the prompt loop forever; `Identifier` (the username);
   `Password` (hidden).
4. **Headless sessions cannot prompt.** `browser_vault_save_login` in a
   Telegram/cron/API session returns `prompt_unavailable` with a hint to run
   `hermes vault add` or use Desktop → Settings → Passwords & Logins. Tell the
   user exactly which of the two to use; do not retry the prompt tool.
5. **Prove the login before scheduling anything:** open the site in the
   supervised browser, type the identifier myself (`fill_input`), call
   `browser_vault_fill` with the handle, submit, and assert the landing URL
   changed past the login form. The vault list entry alone (`available: true`)
   proves storage, NOT that the password works or that the origin matches.
   Report the handle + identifier, never the secret.
6. **Only then wire the automation:** cron jobs call `browser_vault_list` for
   the origin first; if no item exists, the job must STOP and ask the user to
   save a login (never type a password, never fake a report). Verify one
   manual fire (`cronjob_manage action='run'`) to watch the full
   login → act → deliver path before trusting the schedule.

## Pitfalls

- **The prompt's identifier type field is an enum, not a value field.**
  Entering the username/email there repeats the same prompt; only
  `email`/`phone`/`username` are accepted.
- **Two different credentials for one site are two different problems.** A
  working login does not mean the automated path works: the cron session,
  vault scope, and browser origin binding must all line up — verify each
  separately (storage → login → job fire) instead of assuming one covers the
  rest.
- **Origin binding is exact.** A login saved for `https://host.example/` is
  not filled on `https://host.example/subpath` or over http — save the origin
  the job will actually load, or the fill is refused.
- **Schedule only what you have seen run once.** A cron job created against an
  unverified credential reports failure at the scheduled hour instead of
  working; prove the path manually first, then leave the schedule armed.
- **SPA login forms can wipe the field before you submit.** Control-panel
  logins (cPanel Evolution, Vue/React SPAs) re-render the password input
  between `browser_vault_fill` and a follow-up submit, so by the time
  `click_at_xy` runs the field reads empty again even though the fill
  reported success. Fix: **before** calling `browser_vault_fill`, arm a
  `document`-level capture-phase hook that auto-submits the moment a value
  appears, so fill and submit run as one uninterrupted chain:
  ```js
  document.addEventListener('input', e => {
    if (e.target && e.target.id === 'password' && e.target.value.length > 0 && !window.__done) {
      window.__done = true;
      setTimeout(() => {
        const b = [...document.querySelectorAll('button')]
          .find(x => /sign in/i.test(x.innerText || ''));
        if (b) b.click();   // NOT form.requestSubmit() — SPAs often have no real <form>
      }, 30);
    }
  }, true);  // capture phase survives re-renders; element listeners do not
  ```
  Three details that make it work: capture-phase listener on `document` (an
  element listener dies when the SPA re-mounts the node); dispatch the actual
  `<button>` click, not `form.requestSubmit()` (SPAs often render inputs
  without a `<form>`, making requestSubmit a silent no-op); arm the hook
  **before** the vault fill, never after, or the input event is missed.
- **cPanel Evolution login: id `username` is DUPLICATED (DIV + input).** `getElementById('username')`/selector `#username` can grab the DIV (no `.value`), so `fill_input` errors "element not found" and JS reads return `undefined`/`{}`. Always target **`input#username`** explicitly (and `input#password` for consistency). Also `js()` needs a real IIFE `(() => {...})()` — an uncalled arrow returns the function itself (reads as `{}`), and `String(u.value)` on a missing element reads `'undefined'` (string, not null).
- **SPA re-renders can blank fields between calls; keep the whole fill→submit chain in ONE `browser_exec` call.** The browser tab also resets to `about:blank` between separate calls — call `ensure_real_tab()`/re-navigate at the start of a fresh call.
- **Remote SSH login with vault credentials (authorized ops only).** For
  infrastructure tasks explicitly authorized by the owner, an interactive SSH
  password can be supplied without putting the secret in argv or output by
  resolving the active-profile vault secret in-process and passing it to
  OpenSSH through a one-shot `SSH_ASKPASS` helper backed by an environment
  variable. Keep the helper mode 700 and remove it after the call; never print
  the secret or put it in a command argument. Use a purpose-built wrapper
  (see `cpanel-shared-hosting-deploy/scripts/ssh_vault.py`) rather than
  decrypting vault files manually. If the helper cannot resolve the vault
  record, stop and fix profile/handle selection; do not copy vault ciphertext
  or key into ad hoc scripts.
- **Re-verify side effects against the live list, never a success toast.** A
  "created successfully" modal is optimistic UI, not proof — re-open the
  target list page (database list, table index, settings page) and count
  entries before reporting success. Reporting a create as done off the toast
  alone, when the object is absent from the list, is the mistake that makes
  the user re-check everything you claim.
- **When the user demands the secret BACK — printed in chat, sent as a file,
  or uploaded to a Drive link — refuse the same way every time AND offer a
  path that removes the need for the secret.** Refusal alone reads as an
  obstacle and invites escalating rephrasings ("I don't mind if it's visible",
  "just send the file", "upload it and give me the link"); pair every refusal
  with a working self-serve alternative: the exact file path plus the command
  they run themselves, or — when a temporary gate is what blocks them — remove
  that gate so no secret is needed at all while the app's real login stays as
  the protection. Never upload a secret to cloud storage: a shared link leaks
  the credential permanently and to anyone who finds it, which is worse than
  a chat message, not better. Keep the refusal brief and move straight to the
  alternative; re-arguing the rule is what turns one request into four.