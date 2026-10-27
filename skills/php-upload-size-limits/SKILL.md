---
name: php-upload-size-limits
description: Use when PHP rejects uploads under the stated limit.
version: 1.0.0
author: office
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [php, upload, php-ini, debugging]
    related_skills: [systematic-debugging, php-panel-verification-evidence]
---

# PHP Upload Size Limits

Use when a user reports "berkas melebihi batas" / "file exceeds size limit" for a
file that is clearly under the limit the form advertises.

## When to Use

- An upload is rejected with a size message while the file is smaller than the advertised maximum.
- The form hint says "max 3 MB" but files around 2 MB fail.
- A user reports the same upload failing on one machine/server but not another.

## Root Cause Pattern

The application limit is a constant (e.g. 3 MB) while PHP's own limits are lower
(`upload_max_filesize=2M`). PHP discards the file before any application code
runs and sets `UPLOAD_ERR_INI_SIZE (1)`. Nothing in the app logic is wrong — the
disabled promise is.

Check the real limits first, in the SAPI that actually serves traffic (not your
shell):

```bash
php -r 'printf("upload=%s post=%s\n", ini_get("upload_max_filesize"), ini_get("post_max_size"));'
```

For `php -S` the CLI ini applies; for FPM/Apache it is `/etc/php/<v>/fpm/php.ini`
or the vhost. A dev script that starts the server can pass `-d upload_max_filesize=8M
-d post_max_size=12M` so the documented limit holds locally.

## Fix

1. Derive the effective limit instead of hardcoding it: `min(app_limit,
upload_max_filesize, post_max_size)`. Parse ini shorthand (`2M`, `8M`, `512K`,
`-1` = unlimited) yourself; `ini_get` returns the string, not bytes.
2. Render every upload hint from that value, so the UI never promises more than
the server accepts. Grep the whole repo for the literal (`maksimal 3 MB`) — the
same text is usually duplicated across controllers and views.
3. Put the real numbers in the error: file size and effective limit, not a
generic "server limit".
4. Handle `post_max_size` overflow: PHP empties `$_POST` and `$_FILES`, so CSRF
validates an empty token and the user sees "sesi kedaluwarsa", which is a lie.
Compare `$_SERVER['CONTENT_LENGTH']` against `post_max_size` in the front
controller and answer `413` with a size message.

## Verify End-to-End, Not by Reading Code

Generate a real file just over the reported size with GD noise (`imagepng($im,$f,0)`
of ~1200×760 random pixels ≈ 2,6 MB; random pixels do not compress) and POST it
through the actual form with a real session and CSRF token. Then:

- run once with `upload_max_filesize=2M` — expect rejection whose message names 2 MB and a hint that says 2 MB;
- run once with the raised limit — expect `302` and the DB column updated;
- restore the DB column and delete the uploaded file afterwards.

## Pitfalls

- `php -r` with nested quotes inside a shell string fails with `unexpected EOF`.
  Write a temp script file instead of fighting quoting.
- Silently exiting `255` with no output is a swallowed fatal, and
  `-d display_errors=stderr` often still prints nothing because the project's own
  error handler replaces display_errors. Bisect instead: query one thing at a
  time and confirm the table/column/key exists (`SHOW TABLES`, `SHOW COLUMNS`,
  list the settings keys) — a query against a nonexistent table or against a name
  that actually lives in a JSON settings row is the usual cause. Re-run with the
  `-d` flags only to confirm it is not a parse error.
- Killing a throwaway server with `pkill -f "<pattern>"` also kills the calling
  shell; verify the port separately afterwards.
- Do not print credential files to the terminal during diagnosis. If a password
  is exposed, rotate it (dedicated rotate script) and say so plainly.
- Add a regression assertion that the effective limit never exceeds the ini
  values and that hints contain no hardcoded size, otherwise the same drift
  returns on the next refactor.
